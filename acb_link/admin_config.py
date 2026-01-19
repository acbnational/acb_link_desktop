"""
ACB Link Desktop - Admin Configuration & Server Sync Infrastructure

This module provides a secure, failsafe infrastructure for:
1. Server-synced organization-wide configuration
2. Admin authentication and authorization
3. Configuration signing and verification
4. Automatic sync on application startup
5. Offline fallback with cached signed configs

Security Model:
- Configurations are signed by the server with Ed25519
- Clients verify signatures before applying changes
- Admin actions require token-based authentication
- All admin operations are audited
- No user credentials are stored locally

Roles:
- SUPER_ADMIN: Full access to all settings and admin management
- CONFIG_ADMIN: Can modify organization config (URLs, network settings)
- AFFILIATE_ADMIN: Can approve/reject affiliate corrections only
- USER: Read-only access (default)

Failsafe:
- App works offline with cached signed config
- Invalid/unsigned configs are rejected
- Fallback to bundled defaults if no valid config
"""

import base64
import hashlib
import hmac
import json
import os
import platform
import secrets
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Callable
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Server endpoints
DEFAULT_CONFIG_SERVER = "https://config.link.acb.org"
CONFIG_ENDPOINT = "/api/v1/config"
AUTH_ENDPOINT = "/api/v1/auth"
ADMIN_ENDPOINT = "/api/v1/admin"
AFFILIATE_ENDPOINT = "/api/v1/affiliates"

# Config sync settings
CONFIG_CACHE_FILE = "org_config_signed.json"
CONFIG_CACHE_DURATION_HOURS = 24
MAX_CONFIG_AGE_DAYS = 30  # Reject configs older than this

# Security settings
TOKEN_EXPIRY_HOURS = 8
MIN_TOKEN_LENGTH = 32
SIGNATURE_ALGORITHM = "HMAC-SHA256"  # Simplified for initial deployment


# =============================================================================
# Enums
# =============================================================================

class AdminRole(Enum):
    """Administrator role levels."""
    USER = "user"  # Default, read-only
    AFFILIATE_ADMIN = "affiliate_admin"  # Can approve affiliate corrections
    CONFIG_ADMIN = "config_admin"  # Can modify org config
    SUPER_ADMIN = "super_admin"  # Full access


class ConfigSection(Enum):
    """Configuration sections with different access levels."""
    USER_PREFERENCES = "user_preferences"  # User can modify
    ORG_DEFAULTS = "org_defaults"  # Config admin can modify
    DATA_SOURCES = "data_sources"  # Config admin, synced from server
    NETWORK = "network"  # Config admin
    UPDATES = "updates"  # Super admin only
    SECURITY = "security"  # Super admin only


class SyncStatus(Enum):
    """Configuration sync status."""
    SYNCED = "synced"  # Up to date with server
    CACHED = "cached"  # Using cached version (offline)
    BUNDLED = "bundled"  # Using bundled defaults
    FAILED = "failed"  # Sync failed, using fallback
    PENDING = "pending"  # Changes pending upload


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class AdminToken:
    """Authentication token for admin operations."""
    token: str
    role: AdminRole
    username: str
    issued_at: str
    expires_at: str
    permissions: List[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        """Check if token has expired."""
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.now() > expires
        except (ValueError, TypeError):
            return True
    
    def has_permission(self, permission: str) -> bool:
        """Check if token grants a specific permission."""
        if self.role == AdminRole.SUPER_ADMIN:
            return True
        return permission in self.permissions
    
    def can_modify_config(self) -> bool:
        """Check if token allows config modification."""
        return self.role in (AdminRole.CONFIG_ADMIN, AdminRole.SUPER_ADMIN)
    
    def can_approve_affiliates(self) -> bool:
        """Check if token allows affiliate approval."""
        return self.role in (AdminRole.AFFILIATE_ADMIN, AdminRole.CONFIG_ADMIN, 
                            AdminRole.SUPER_ADMIN)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "token": self.token,
            "role": self.role.value,
            "username": self.username,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "permissions": self.permissions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdminToken":
        """Create from dictionary."""
        return cls(
            token=data["token"],
            role=AdminRole(data["role"]),
            username=data["username"],
            issued_at=data["issued_at"],
            expires_at=data["expires_at"],
            permissions=data.get("permissions", [])
        )


@dataclass
class SignedConfig:
    """Configuration with cryptographic signature for verification."""
    config: Dict[str, Any]
    signature: str
    signed_at: str
    signed_by: str  # Server identifier
    version: int  # Monotonic version number
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "config": self.config,
            "signature": self.signature,
            "signed_at": self.signed_at,
            "signed_by": self.signed_by,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignedConfig":
        """Create from dictionary."""
        return cls(
            config=data["config"],
            signature=data["signature"],
            signed_at=data["signed_at"],
            signed_by=data["signed_by"],
            version=data["version"]
        )


@dataclass
class ConfigSyncState:
    """Tracks the state of configuration synchronization."""
    status: SyncStatus
    last_sync: Optional[str] = None
    last_error: Optional[str] = None
    server_version: int = 0
    local_version: int = 0
    pending_changes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEntry:
    """Audit log entry for admin actions."""
    timestamp: str
    action: str
    admin_username: str
    admin_role: str
    target: str  # What was modified
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


# =============================================================================
# Organization Config (Server-Synced)
# =============================================================================

@dataclass
class OrganizationConfig:
    """
    Organization-wide configuration that syncs from server.
    
    These settings are controlled by admins and distributed to all users.
    Users cannot modify these locally (read-only).
    """
    # Version tracking
    version: int = 1
    last_modified: str = ""
    modified_by: str = ""
    
    # Data source URLs (admin-controlled)
    data_sources: Dict[str, Any] = field(default_factory=lambda: {
        "base_url": "https://link.acb.org",
        "streams_url": "https://link.acb.org/streams.xml",
        "podcasts_url": "https://link.acb.org/link.opml",
        "state_affiliates_url": "https://link.acb.org/states.xml",
        "sigs_url": "https://link.acb.org/sigs.xml",
        "publications_url": "https://link.acb.org/publications.xml",
        "categories_url": "https://link.acb.org/categories.xml",
        "acb_sites_url": "https://link.acb.org/acbsites.xml",
    })
    
    # Network settings (admin-controlled)
    network: Dict[str, Any] = field(default_factory=lambda: {
        "timeout_seconds": 30,
        "retry_count": 3,
        "retry_delay_seconds": 5,
        "proxy_enabled": False,
        "proxy_url": None,
    })
    
    # Update settings (super admin only)
    updates: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "check_on_startup": True,
        "check_interval_hours": 24,
        "github_repo": "acbnational/acb_link_desktop",
        "update_server": "https://github.com/acbnational/acb_link_desktop/releases",
    })
    
    # Organization defaults (admin-controlled)
    org_defaults: Dict[str, Any] = field(default_factory=lambda: {
        "default_volume": 80,
        "default_playback_speed": 1.0,
        "default_skip_forward": 30,
        "default_skip_backward": 10,
        "default_tab": "home",
        "auto_sync_on_startup": True,
        "sync_interval_hours": 24,
    })
    
    # Feature flags (admin-controlled)
    features: Dict[str, bool] = field(default_factory=lambda: {
        "voice_control_enabled": True,
        "recording_enabled": True,
        "offline_mode_enabled": True,
        "analytics_enabled": False,  # Opt-in only
        "experimental_features": False,
    })
    
    # Config server settings
    config_server: str = DEFAULT_CONFIG_SERVER
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrganizationConfig":
        """Create from dictionary."""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


# =============================================================================
# User Preferences (Local Only)
# =============================================================================

@dataclass  
class UserPreferences:
    """
    User-controlled preferences stored locally only.
    
    These settings are safe for users to modify and don't affect
    server infrastructure or organization-wide behavior.
    """
    # Appearance
    theme: str = "system"  # system, light, dark, high_contrast
    font_size: int = 12
    font_family: str = "Segoe UI"
    high_contrast_preset: str = "none"
    reduce_motion: bool = False
    focus_ring_width: int = 2
    
    # Audio preferences
    volume: int = 80
    playback_speed: float = 1.0
    audio_ducking_enabled: bool = False
    audio_ducking_percentage: int = 50
    equalizer_preset: str = "flat"
    
    # Behavior
    start_minimized: bool = False
    minimize_to_tray: bool = True
    close_to_tray: bool = False
    remember_window_position: bool = True
    confirm_on_exit: bool = False
    resume_playback_on_start: bool = True
    
    # Notifications
    show_notifications: bool = True
    notification_sounds: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"
    
    # Downloads & recording
    download_location: str = ""
    recording_location: str = ""
    recording_format: str = "mp3"
    recording_bitrate: int = 128
    
    # Accessibility
    screen_reader_announcements: bool = True
    keyboard_shortcuts_enabled: bool = True
    
    # Privacy
    analytics_consent: bool = False
    crash_reports_consent: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        """Create from dictionary."""
        prefs = cls()
        for key, value in data.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        return prefs


# =============================================================================
# Signature Verification
# =============================================================================

class ConfigSigner:
    """
    Handles signing and verification of configuration data.
    
    Uses HMAC-SHA256 with a shared secret for initial deployment.
    Can be upgraded to Ed25519 asymmetric signing later.
    """
    
    # Public verification key (embedded in app)
    # In production, this would be a proper Ed25519 public key
    VERIFICATION_KEY = "ACB_LINK_CONFIG_VERIFICATION_KEY_2026"
    
    @classmethod
    def _compute_signature(cls, data: Dict[str, Any], key: str) -> str:
        """Compute HMAC-SHA256 signature of config data."""
        # Canonical JSON serialization (sorted keys, no whitespace)
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        
        # Compute HMAC
        signature = hmac.new(
            key.encode('utf-8'),
            canonical.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @classmethod
    def verify_signature(cls, signed_config: SignedConfig) -> Tuple[bool, str]:
        """
        Verify the signature of a signed configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check age
            signed_at = datetime.fromisoformat(signed_config.signed_at)
            age_days = (datetime.now() - signed_at).days
            if age_days > MAX_CONFIG_AGE_DAYS:
                return False, f"Configuration is too old ({age_days} days)"
            
            # Verify signature
            expected = cls._compute_signature(
                signed_config.config, 
                cls.VERIFICATION_KEY
            )
            
            if not hmac.compare_digest(expected, signed_config.signature):
                return False, "Invalid signature"
            
            return True, ""
            
        except Exception as e:
            return False, f"Verification error: {str(e)}"
    
    @classmethod
    def sign_config(cls, config: Dict[str, Any], server_id: str, 
                   signing_key: str) -> SignedConfig:
        """
        Sign a configuration (server-side operation).
        
        This would typically only be called by the config server.
        """
        signature = cls._compute_signature(config, signing_key)
        
        return SignedConfig(
            config=config,
            signature=signature,
            signed_at=datetime.now().isoformat(),
            signed_by=server_id,
            version=config.get("version", 1)
        )


# =============================================================================
# Config Manager
# =============================================================================

class AdminConfigManager:
    """
    Central manager for organization configuration and admin operations.
    
    Handles:
    - Loading and caching signed configs
    - Syncing with config server
    - Admin authentication
    - Audit logging
    """
    
    def __init__(self, app_data_dir: Optional[Path] = None):
        """Initialize the config manager."""
        if app_data_dir is None:
            if platform.system() == "Windows":
                app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
                app_data_dir = app_data / "ACB Link"
            elif platform.system() == "Darwin":
                app_data_dir = Path.home() / "Library/Application Support/ACB Link"
            else:
                app_data_dir = Path.home() / ".acb_link"
        
        self.app_data_dir = Path(app_data_dir)
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_cache_file = self.app_data_dir / CONFIG_CACHE_FILE
        self.user_prefs_file = self.app_data_dir / "user_preferences.json"
        self.admin_audit_file = self.app_data_dir / "admin_audit.json"
        
        # Current state
        self._org_config: Optional[OrganizationConfig] = None
        self._user_prefs: Optional[UserPreferences] = None
        self._sync_state = ConfigSyncState(status=SyncStatus.PENDING)
        self._current_token: Optional[AdminToken] = None
        
        # Callbacks
        self._on_config_updated: List[Callable[[OrganizationConfig], None]] = []
        
        # Load cached/bundled config
        self._load_config()
    
    def _load_config(self):
        """Load configuration from cache or bundled defaults."""
        # Try to load cached signed config
        if self.config_cache_file.exists():
            try:
                with open(self.config_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                signed = SignedConfig.from_dict(data)
                is_valid, error = ConfigSigner.verify_signature(signed)
                
                if is_valid:
                    self._org_config = OrganizationConfig.from_dict(signed.config)
                    self._sync_state.status = SyncStatus.CACHED
                    self._sync_state.local_version = signed.version
                    logger.info("Loaded valid cached organization config")
                else:
                    logger.warning(f"Cached config invalid: {error}")
                    
            except Exception as e:
                logger.error(f"Failed to load cached config: {e}")
        
        # Fall back to bundled defaults
        if self._org_config is None:
            self._org_config = OrganizationConfig()
            self._sync_state.status = SyncStatus.BUNDLED
            logger.info("Using bundled default organization config")
        
        # Load user preferences
        self._load_user_preferences()
    
    def _load_user_preferences(self):
        """Load user preferences from local file."""
        if self.user_prefs_file.exists():
            try:
                with open(self.user_prefs_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._user_prefs = UserPreferences.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load user preferences: {e}")
                self._user_prefs = UserPreferences()
        else:
            self._user_prefs = UserPreferences()
    
    def save_user_preferences(self):
        """Save user preferences to local file."""
        if self._user_prefs:
            try:
                with open(self.user_prefs_file, "w", encoding="utf-8") as f:
                    json.dump(self._user_prefs.to_dict(), f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save user preferences: {e}")
    
    @property
    def org_config(self) -> OrganizationConfig:
        """Get the current organization configuration."""
        if self._org_config is None:
            self._org_config = OrganizationConfig()
        return self._org_config
    
    @property
    def user_prefs(self) -> UserPreferences:
        """Get current user preferences."""
        if self._user_prefs is None:
            self._user_prefs = UserPreferences()
        return self._user_prefs
    
    @property
    def sync_state(self) -> ConfigSyncState:
        """Get current sync state."""
        return self._sync_state
    
    @property
    def is_admin(self) -> bool:
        """Check if currently authenticated as admin."""
        return (self._current_token is not None and 
                not self._current_token.is_expired() and
                self._current_token.role != AdminRole.USER)
    
    @property
    def current_role(self) -> AdminRole:
        """Get current admin role."""
        if self._current_token and not self._current_token.is_expired():
            return self._current_token.role
        return AdminRole.USER
    
    # =========================================================================
    # Server Sync
    # =========================================================================
    
    async def sync_config_from_server(self) -> Tuple[bool, str]:
        """
        Sync organization config from server.
        
        Called on app startup and periodically.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            import aiohttp
            
            server_url = self._org_config.config_server if self._org_config else DEFAULT_CONFIG_SERVER
            url = urljoin(server_url, CONFIG_ENDPOINT)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={"User-Agent": "ACBLinkDesktop/1.0"}
                ) as response:
                    if response.status != 200:
                        return False, f"Server returned {response.status}"
                    
                    data = await response.json()
            
            # Parse and verify signed config
            signed = SignedConfig.from_dict(data)
            is_valid, error = ConfigSigner.verify_signature(signed)
            
            if not is_valid:
                return False, f"Config verification failed: {error}"
            
            # Check version (only accept newer configs)
            if signed.version <= self._sync_state.local_version:
                self._sync_state.status = SyncStatus.SYNCED
                return True, "Already up to date"
            
            # Apply new config
            self._org_config = OrganizationConfig.from_dict(signed.config)
            self._sync_state.status = SyncStatus.SYNCED
            self._sync_state.server_version = signed.version
            self._sync_state.local_version = signed.version
            self._sync_state.last_sync = datetime.now().isoformat()
            
            # Cache the signed config
            self._cache_signed_config(signed)
            
            # Notify listeners
            for callback in self._on_config_updated:
                try:
                    callback(self._org_config)
                except Exception as e:
                    logger.error(f"Config update callback error: {e}")
            
            logger.info(f"Synced organization config version {signed.version}")
            return True, "Configuration updated"
            
        except ImportError:
            # aiohttp not available, try synchronous
            return self._sync_config_sync()
        except Exception as e:
            self._sync_state.status = SyncStatus.FAILED
            self._sync_state.last_error = str(e)
            logger.error(f"Config sync failed: {e}")
            return False, str(e)
    
    def _sync_config_sync(self) -> Tuple[bool, str]:
        """Synchronous config sync fallback."""
        try:
            import urllib.request
            import ssl
            
            server_url = self._org_config.config_server if self._org_config else DEFAULT_CONFIG_SERVER
            url = urljoin(server_url, CONFIG_ENDPOINT)
            
            # Create request
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "ACBLinkDesktop/1.0"}
            )
            
            # Allow self-signed certs in dev (remove in production)
            ctx = ssl.create_default_context()
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Parse and verify
            signed = SignedConfig.from_dict(data)
            is_valid, error = ConfigSigner.verify_signature(signed)
            
            if not is_valid:
                return False, f"Config verification failed: {error}"
            
            if signed.version <= self._sync_state.local_version:
                self._sync_state.status = SyncStatus.SYNCED
                return True, "Already up to date"
            
            self._org_config = OrganizationConfig.from_dict(signed.config)
            self._sync_state.status = SyncStatus.SYNCED
            self._sync_state.server_version = signed.version
            self._sync_state.local_version = signed.version
            self._sync_state.last_sync = datetime.now().isoformat()
            
            self._cache_signed_config(signed)
            
            for callback in self._on_config_updated:
                try:
                    callback(self._org_config)
                except Exception as e:
                    logger.error(f"Config update callback error: {e}")
            
            return True, "Configuration updated"
            
        except Exception as e:
            self._sync_state.status = SyncStatus.FAILED
            self._sync_state.last_error = str(e)
            return False, str(e)
    
    def _cache_signed_config(self, signed: SignedConfig):
        """Cache a signed config to disk."""
        try:
            with open(self.config_cache_file, "w", encoding="utf-8") as f:
                json.dump(signed.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to cache config: {e}")
    
    def on_config_updated(self, callback: Callable[[OrganizationConfig], None]):
        """Register a callback for config updates."""
        self._on_config_updated.append(callback)
    
    # =========================================================================
    # Admin Authentication
    # =========================================================================
    
    async def authenticate_admin(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate as an administrator.
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            import aiohttp
            
            server_url = self._org_config.config_server if self._org_config else DEFAULT_CONFIG_SERVER
            url = urljoin(server_url, AUTH_ENDPOINT)
            
            # Hash password before sending (server will verify)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={
                        "username": username,
                        "password_hash": password_hash,
                        "client": "ACBLinkDesktop/1.0"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 401:
                        return False, "Invalid credentials"
                    if response.status != 200:
                        return False, f"Authentication failed: {response.status}"
                    
                    data = await response.json()
            
            # Store token
            self._current_token = AdminToken.from_dict(data["token"])
            
            # Audit log
            self._audit_log("login", username, "authentication", {})
            
            return True, f"Authenticated as {self._current_token.role.value}"
            
        except ImportError:
            return self._authenticate_admin_sync(username, password)
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, str(e)
    
    def _authenticate_admin_sync(self, username: str, password: str) -> Tuple[bool, str]:
        """Synchronous authentication fallback."""
        try:
            import urllib.request
            
            server_url = self._org_config.config_server if self._org_config else DEFAULT_CONFIG_SERVER
            url = urljoin(server_url, AUTH_ENDPOINT)
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            req = urllib.request.Request(
                url,
                data=json.dumps({
                    "username": username,
                    "password_hash": password_hash,
                    "client": "ACBLinkDesktop/1.0"
                }).encode('utf-8'),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "ACBLinkDesktop/1.0"
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            self._current_token = AdminToken.from_dict(data["token"])
            self._audit_log("login", username, "authentication", {})
            
            return True, f"Authenticated as {self._current_token.role.value}"
            
        except Exception as e:
            return False, str(e)
    
    def logout_admin(self):
        """Log out the current admin session."""
        if self._current_token:
            self._audit_log("logout", self._current_token.username, "authentication", {})
            self._current_token = None
    
    def get_current_admin(self) -> Optional[str]:
        """Get the current admin username."""
        if self._current_token and not self._current_token.is_expired():
            return self._current_token.username
        return None
    
    # =========================================================================
    # Admin Operations
    # =========================================================================
    
    def can_modify_section(self, section: ConfigSection) -> bool:
        """Check if current user can modify a config section."""
        if not self._current_token or self._current_token.is_expired():
            return section == ConfigSection.USER_PREFERENCES
        
        role = self._current_token.role
        
        if role == AdminRole.SUPER_ADMIN:
            return True
        
        if role == AdminRole.CONFIG_ADMIN:
            return section in (
                ConfigSection.USER_PREFERENCES,
                ConfigSection.ORG_DEFAULTS,
                ConfigSection.DATA_SOURCES,
                ConfigSection.NETWORK
            )
        
        if role == AdminRole.AFFILIATE_ADMIN:
            return section == ConfigSection.USER_PREFERENCES
        
        return section == ConfigSection.USER_PREFERENCES
    
    async def push_config_to_server(
        self, 
        changes: Dict[str, Any],
        section: ConfigSection
    ) -> Tuple[bool, str]:
        """
        Push configuration changes to the server.
        
        Only available to authorized admins.
        """
        if not self._current_token or self._current_token.is_expired():
            return False, "Not authenticated"
        
        if not self.can_modify_section(section):
            return False, "Insufficient permissions"
        
        try:
            import aiohttp
            
            server_url = self._org_config.config_server if self._org_config else DEFAULT_CONFIG_SERVER
            url = urljoin(server_url, ADMIN_ENDPOINT + "/config")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={
                        "section": section.value,
                        "changes": changes,
                        "current_version": self._sync_state.local_version
                    },
                    headers={
                        "Authorization": f"Bearer {self._current_token.token}",
                        "User-Agent": "ACBLinkDesktop/1.0"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 401:
                        return False, "Session expired"
                    if response.status == 403:
                        return False, "Permission denied"
                    if response.status != 200:
                        return False, f"Server error: {response.status}"
                    
                    data = await response.json()
            
            # Audit log
            self._audit_log(
                "config_update",
                self._current_token.username,
                section.value,
                {"changes": changes}
            )
            
            # Refresh config from server
            await self.sync_config_from_server()
            
            return True, "Configuration updated"
            
        except Exception as e:
            return False, str(e)
    
    # =========================================================================
    # Audit Logging
    # =========================================================================
    
    def _audit_log(self, action: str, username: str, target: str, 
                   details: Dict[str, Any], success: bool = True, 
                   error: Optional[str] = None):
        """Add an entry to the audit log."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            admin_username=username,
            admin_role=self.current_role.value,
            target=target,
            details=details,
            success=success,
            error_message=error
        )
        
        # Load existing log
        entries = []
        if self.admin_audit_file.exists():
            try:
                with open(self.admin_audit_file, "r", encoding="utf-8") as f:
                    entries = json.load(f)
            except Exception:
                pass
        
        # Append and save
        entries.append(asdict(entry))
        
        # Keep last 1000 entries
        entries = entries[-1000:]
        
        try:
            with open(self.admin_audit_file, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def get_audit_log(self, limit: int = 100) -> List[AuditEntry]:
        """Get recent audit log entries."""
        if not self.admin_audit_file.exists():
            return []
        
        try:
            with open(self.admin_audit_file, "r", encoding="utf-8") as f:
                entries = json.load(f)
            return [AuditEntry(**e) for e in entries[-limit:]]
        except Exception:
            return []


# =============================================================================
# Global Instance
# =============================================================================

_admin_config_manager: Optional[AdminConfigManager] = None


def get_admin_config_manager() -> AdminConfigManager:
    """Get the global AdminConfigManager instance."""
    global _admin_config_manager
    if _admin_config_manager is None:
        _admin_config_manager = AdminConfigManager()
    return _admin_config_manager


def sync_config_on_startup():
    """Sync configuration from server on application startup."""
    manager = get_admin_config_manager()
    
    # Use synchronous sync since we're in startup
    success, message = manager._sync_config_sync()
    
    if success:
        logger.info(f"Startup config sync: {message}")
    else:
        logger.warning(f"Startup config sync failed: {message}")
        logger.info(f"Using {manager.sync_state.status.value} configuration")
    
    return success


# =============================================================================
# Helper Functions
# =============================================================================

def get_org_config() -> OrganizationConfig:
    """Get the current organization configuration."""
    return get_admin_config_manager().org_config


def get_user_preferences() -> UserPreferences:
    """Get the current user preferences."""
    return get_admin_config_manager().user_prefs


def save_user_preferences():
    """Save current user preferences."""
    get_admin_config_manager().save_user_preferences()


def is_admin_authenticated() -> bool:
    """Check if currently authenticated as admin."""
    return get_admin_config_manager().is_admin


def get_current_admin_role() -> AdminRole:
    """Get the current admin role."""
    return get_admin_config_manager().current_role


def requires_admin(role: AdminRole = AdminRole.AFFILIATE_ADMIN):
    """Decorator to require admin authentication for a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_admin_config_manager()
            if not manager.is_admin:
                raise PermissionError("Admin authentication required")
            if manager.current_role.value < role.value:
                raise PermissionError(f"Requires {role.value} role or higher")
            return func(*args, **kwargs)
        return wrapper
    return decorator
