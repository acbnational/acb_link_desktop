"""
ACB Link Desktop - GitHub-Based Admin Authentication

This module provides admin authentication using GitHub's free infrastructure:
- Admin roles determined by GitHub repository permissions
- Authentication via GitHub Personal Access Tokens (PATs)
- Organization config stored in a GitHub repository
- Completely free, no custom server needed

Role Mapping:
- SUPER_ADMIN: GitHub Organization owners
- CONFIG_ADMIN: Repository admin permission (can change settings, manage access)
- AFFILIATE_ADMIN: Repository write/maintain permission (can push)
- USER: Read-only or no access

Security:
- PATs are validated against GitHub API
- Tokens stored in memory only (never written to disk)
- All admin actions logged locally
- Config files are signed commits in the repository
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# GitHub API base URL
GITHUB_API = "https://api.github.com"

# Default repository for organization config
# This should be a repository in the ACB organization
DEFAULT_CONFIG_REPO = "acbnational/acb_link_config"
DEFAULT_CONFIG_BRANCH = "main"
DEFAULT_CONFIG_FILE = "org_config.json"

# Cache settings
CONFIG_CACHE_FILE = "github_org_config.json"
CONFIG_CACHE_DURATION_HOURS = 1  # Re-check frequently since it's free

# Token settings
TOKEN_CACHE_DURATION_HOURS = 8  # How long to cache permission checks


# =============================================================================
# Enums
# =============================================================================

class AdminRole(Enum):
    """Administrator role levels mapped to GitHub permissions."""
    USER = 0           # No special access
    AFFILIATE_ADMIN = 1  # Write/push access to config repo
    CONFIG_ADMIN = 2     # Admin access to config repo
    SUPER_ADMIN = 3      # Organization owner
    
    def __ge__(self, other):
        if isinstance(other, AdminRole):
            return self.value >= other.value
        return NotImplemented
    
    def __gt__(self, other):
        if isinstance(other, AdminRole):
            return self.value > other.value
        return NotImplemented
    
    def __le__(self, other):
        if isinstance(other, AdminRole):
            return self.value <= other.value
        return NotImplemented
    
    def __lt__(self, other):
        if isinstance(other, AdminRole):
            return self.value < other.value
        return NotImplemented


class AdminPermission(Enum):
    """Specific admin permissions."""
    VIEW_ADMIN_PANEL = "view_admin_panel"
    REVIEW_CORRECTIONS = "review_corrections"
    APPROVE_CORRECTIONS = "approve_corrections"
    MODIFY_DATA_SOURCES = "modify_data_sources"
    MODIFY_NETWORK = "modify_network"
    MODIFY_DEFAULTS = "modify_defaults"
    MANAGE_ADMINS = "manage_admins"


# Permission mapping by role
ROLE_PERMISSIONS: Dict[AdminRole, List[AdminPermission]] = {
    AdminRole.USER: [],
    AdminRole.AFFILIATE_ADMIN: [
        AdminPermission.VIEW_ADMIN_PANEL,
        AdminPermission.REVIEW_CORRECTIONS,
        AdminPermission.APPROVE_CORRECTIONS,
    ],
    AdminRole.CONFIG_ADMIN: [
        AdminPermission.VIEW_ADMIN_PANEL,
        AdminPermission.REVIEW_CORRECTIONS,
        AdminPermission.APPROVE_CORRECTIONS,
        AdminPermission.MODIFY_DATA_SOURCES,
        AdminPermission.MODIFY_NETWORK,
        AdminPermission.MODIFY_DEFAULTS,
    ],
    AdminRole.SUPER_ADMIN: [perm for perm in AdminPermission],  # All permissions
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class GitHubUser:
    """GitHub user information."""
    username: str
    display_name: str
    email: Optional[str]
    avatar_url: Optional[str]


@dataclass
class AdminSession:
    """Active admin session with GitHub authentication."""
    user: GitHubUser
    role: AdminRole
    permissions: List[AdminPermission]
    github_token: str  # The PAT (kept in memory only)
    authenticated_at: datetime
    expires_at: datetime
    org_name: Optional[str] = None
    repo_name: Optional[str] = None
    
    @property
    def username(self) -> str:
        return self.user.username
    
    @property
    def display_name(self) -> str:
        return self.user.display_name
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now() > self.expires_at
    
    def has_permission(self, permission: AdminPermission) -> bool:
        """Check if session has a specific permission."""
        if self.role == AdminRole.SUPER_ADMIN:
            return True
        return permission in self.permissions
    
    def has_role(self, required_role: AdminRole) -> bool:
        """Check if session has at least the required role level."""
        return self.role >= required_role


@dataclass
class AuditEntry:
    """Audit log entry for admin actions."""
    timestamp: str
    action: str
    username: str
    role: str
    target: str
    details: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None


# =============================================================================
# GitHub API Client
# =============================================================================

class GitHubClient:
    """Simple GitHub API client using only standard library."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
    
    def _request(self, endpoint: str, method: str = "GET", 
                 data: Optional[Dict] = None) -> Tuple[bool, Any]:
        """Make a GitHub API request."""
        url = f"{GITHUB_API}{endpoint}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ACBLinkDesktop/1.1"
        }
        
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        
        try:
            body = json.dumps(data).encode() if data else None
            req = Request(url, data=body, headers=headers, method=method)
            
            with urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode())
                return True, response_data
                
        except HTTPError as e:
            try:
                error_body = json.loads(e.read().decode())
                return False, {"status": e.code, "message": error_body.get("message", str(e))}
            except Exception:
                return False, {"status": e.code, "message": str(e)}
        except URLError as e:
            return False, {"status": 0, "message": f"Network error: {e.reason}"}
        except Exception as e:
            return False, {"status": 0, "message": str(e)}
    
    def get_authenticated_user(self) -> Tuple[bool, Any]:
        """Get the authenticated user's information."""
        return self._request("/user")
    
    def get_repo_permission(self, owner: str, repo: str, 
                           username: str) -> Tuple[bool, Any]:
        """Get a user's permission level on a repository."""
        return self._request(f"/repos/{owner}/{repo}/collaborators/{username}/permission")
    
    def is_org_owner(self, org: str, username: str) -> Tuple[bool, bool]:
        """Check if user is an organization owner."""
        success, data = self._request(f"/orgs/{org}/memberships/{username}")
        if success and data.get("role") == "admin":
            return True, True
        return success, False
    
    def get_file_contents(self, owner: str, repo: str, path: str,
                         ref: str = "main") -> Tuple[bool, Any]:
        """Get a file's contents from a repository."""
        return self._request(f"/repos/{owner}/{repo}/contents/{path}?ref={ref}")
    
    def update_file(self, owner: str, repo: str, path: str,
                   content: str, message: str, sha: str,
                   branch: str = "main") -> Tuple[bool, Any]:
        """Update a file in a repository."""
        import base64
        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "sha": sha,
            "branch": branch
        }
        return self._request(f"/repos/{owner}/{repo}/contents/{path}", 
                            method="PUT", data=data)


# =============================================================================
# GitHub Admin Manager
# =============================================================================

class GitHubAdminManager:
    """
    Manages admin authentication and configuration using GitHub.
    
    This replaces the need for a custom server - everything is free!
    """
    
    def __init__(self, 
                 config_repo: str = DEFAULT_CONFIG_REPO,
                 config_branch: str = DEFAULT_CONFIG_BRANCH,
                 config_file: str = DEFAULT_CONFIG_FILE,
                 data_dir: Optional[Path] = None):
        """
        Initialize the GitHub admin manager.
        
        Args:
            config_repo: GitHub repo for org config (owner/repo format)
            config_branch: Branch to use for config
            config_file: Path to config file in repo
            data_dir: Local directory for caching
        """
        self.config_repo = config_repo
        self.config_branch = config_branch
        self.config_file = config_file
        
        # Parse owner/repo
        parts = config_repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid repo format: {config_repo}. Expected 'owner/repo'")
        self.repo_owner = parts[0]
        self.repo_name = parts[1]
        
        # Set up data directory
        if data_dir is None:
            data_dir = Path.home() / ".acb_link"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session (in memory only)
        self._session: Optional[AdminSession] = None
        
        # Audit log
        self._audit_log: List[AuditEntry] = []
        self._load_audit_log()
    
    @property
    def is_authenticated(self) -> bool:
        """Check if there's an active admin session."""
        return self._session is not None and not self._session.is_expired()
    
    @property
    def current_session(self) -> Optional[AdminSession]:
        """Get the current admin session."""
        if self._session and self._session.is_expired():
            self._session = None
        return self._session
    
    def authenticate(self, github_token: str) -> Tuple[bool, str, Optional[AdminSession]]:
        """
        Authenticate using a GitHub Personal Access Token.
        
        The token needs at least 'read:org' scope to check org membership,
        and 'repo' scope if you need to update config.
        
        Args:
            github_token: GitHub Personal Access Token
            
        Returns:
            (success, message, session)
        """
        client = GitHubClient(github_token)
        
        # Step 1: Validate token and get user info
        success, user_data = client.get_authenticated_user()
        if not success:
            return False, f"Invalid token: {user_data.get('message', 'Unknown error')}", None
        
        username = user_data.get("login", "")
        display_name = user_data.get("name") or username
        email = user_data.get("email")
        avatar = user_data.get("avatar_url")
        
        user = GitHubUser(
            username=username,
            display_name=display_name,
            email=email,
            avatar_url=avatar
        )
        
        # Step 2: Determine role based on GitHub permissions
        role = AdminRole.USER
        
        # Check if user is org owner (SUPER_ADMIN)
        success, is_owner = client.is_org_owner(self.repo_owner, username)
        if is_owner:
            role = AdminRole.SUPER_ADMIN
            logger.info(f"User {username} is org owner -> SUPER_ADMIN")
        else:
            # Check repository permission
            success, perm_data = client.get_repo_permission(
                self.repo_owner, self.repo_name, username
            )
            
            if success:
                permission = perm_data.get("permission", "none")
                logger.info(f"User {username} has repo permission: {permission}")
                
                if permission == "admin":
                    role = AdminRole.CONFIG_ADMIN
                elif permission in ("write", "maintain"):
                    role = AdminRole.AFFILIATE_ADMIN
                # "read" or "none" stays as USER
        
        # Step 3: Create session
        now = datetime.now()
        session = AdminSession(
            user=user,
            role=role,
            permissions=ROLE_PERMISSIONS.get(role, []),
            github_token=github_token,
            authenticated_at=now,
            expires_at=now + timedelta(hours=TOKEN_CACHE_DURATION_HOURS),
            org_name=self.repo_owner,
            repo_name=self.repo_name
        )
        
        self._session = session
        
        # Log authentication
        self._log_action(
            "authenticate",
            username,
            role.name,
            "session",
            {"role": role.name, "permissions": [p.value for p in session.permissions]}
        )
        
        role_desc = {
            AdminRole.USER: "regular user (no admin access)",
            AdminRole.AFFILIATE_ADMIN: "Affiliate Admin (can review corrections)",
            AdminRole.CONFIG_ADMIN: "Config Admin (can modify settings)",
            AdminRole.SUPER_ADMIN: "Super Admin (full access)"
        }
        
        return True, f"Authenticated as {display_name} - {role_desc[role]}", session
    
    def logout(self):
        """Clear the current session."""
        if self._session:
            self._log_action(
                "logout",
                self._session.username,
                self._session.role.name,
                "session",
                {}
            )
        self._session = None
    
    def require_role(self, required_role: AdminRole) -> Tuple[bool, str]:
        """
        Check if current session has at least the required role.
        
        Returns:
            (has_role, message)
        """
        if not self.is_authenticated or self._session is None:
            return False, "Not authenticated. Please log in with your GitHub token."
        
        if self._session.has_role(required_role):
            return True, "Access granted"
        
        return False, f"Insufficient permissions. Required: {required_role.name}, Have: {self._session.role.name}"
    
    def require_permission(self, permission: AdminPermission) -> Tuple[bool, str]:
        """
        Check if current session has a specific permission.
        
        Returns:
            (has_permission, message)
        """
        if not self.is_authenticated or self._session is None:
            return False, "Not authenticated. Please log in with your GitHub token."
        
        if self._session.has_permission(permission):
            return True, "Access granted"
        
        return False, f"Missing permission: {permission.value}"
    
    def fetch_org_config(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Fetch organization config from GitHub repository.
        
        This works without authentication for public repos.
        With authentication, it also works for private repos.
        
        Returns:
            (success, message, config_dict)
        """
        token = self._session.github_token if self._session else None
        client = GitHubClient(token)
        
        # Try to get config file
        success, data = client.get_file_contents(
            self.repo_owner, 
            self.repo_name,
            self.config_file,
            self.config_branch
        )
        
        if not success:
            # Try loading cached version
            cached = self._load_cached_config()
            if cached:
                return True, "Using cached config (GitHub unavailable)", cached
            return False, f"Failed to fetch config: {data.get('message', 'Unknown error')}", None
        
        # Decode content (base64 encoded by GitHub)
        import base64
        try:
            content = base64.b64decode(data["content"]).decode("utf-8")
            config = json.loads(content)
            
            # Cache it locally
            self._save_cached_config(config, data.get("sha", ""))
            
            return True, "Config loaded from GitHub", config
            
        except Exception as e:
            logger.error(f"Error parsing config: {e}")
            cached = self._load_cached_config()
            if cached:
                return True, "Using cached config (parse error)", cached
            return False, f"Error parsing config: {e}", None
    
    def update_org_config(self, config: Dict[str, Any], 
                         commit_message: str) -> Tuple[bool, str]:
        """
        Update organization config in GitHub repository.
        
        Requires CONFIG_ADMIN or SUPER_ADMIN role.
        
        Args:
            config: New config dictionary
            commit_message: Git commit message
            
        Returns:
            (success, message)
        """
        # Check permissions
        has_role, msg = self.require_role(AdminRole.CONFIG_ADMIN)
        if not has_role or self._session is None:
            return False, msg
        
        client = GitHubClient(self._session.github_token)
        
        # Get current file SHA (required for update)
        success, data = client.get_file_contents(
            self.repo_owner,
            self.repo_name, 
            self.config_file,
            self.config_branch
        )
        
        if not success:
            return False, f"Failed to get current config: {data.get('message')}"
        
        current_sha = data.get("sha", "")
        
        # Update file
        config_json = json.dumps(config, indent=2)
        success, result = client.update_file(
            self.repo_owner,
            self.repo_name,
            self.config_file,
            config_json,
            commit_message,
            current_sha,
            self.config_branch
        )
        
        if success:
            self._log_action(
                "update_config",
                self._session.username,
                self._session.role.name,
                "org_config",
                {"commit_message": commit_message}
            )
            return True, "Config updated successfully"
        else:
            return False, f"Failed to update config: {result.get('message')}"
    
    def _load_cached_config(self) -> Optional[Dict[str, Any]]:
        """Load cached config from disk."""
        cache_path = self.data_dir / CONFIG_CACHE_FILE
        try:
            if cache_path.exists():
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Check age
                    cached_at = data.get("_cached_at", "")
                    if cached_at:
                        cached_time = datetime.fromisoformat(cached_at)
                        age_hours = (datetime.now() - cached_time).total_seconds() / 3600
                        if age_hours < CONFIG_CACHE_DURATION_HOURS * 24:  # Allow 24x cache time
                            return data.get("config", data)
            return None
        except Exception as e:
            logger.warning(f"Error loading cached config: {e}")
            return None
    
    def _save_cached_config(self, config: Dict[str, Any], sha: str):
        """Save config to cache."""
        cache_path = self.data_dir / CONFIG_CACHE_FILE
        try:
            cache_data = {
                "config": config,
                "_cached_at": datetime.now().isoformat(),
                "_sha": sha
            }
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving config cache: {e}")
    
    def _log_action(self, action: str, username: str, role: str,
                   target: str, details: Dict[str, Any],
                   success: bool = True, error: Optional[str] = None):
        """Add an entry to the audit log."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            username=username,
            role=role,
            target=target,
            details=details,
            success=success,
            error=error
        )
        self._audit_log.append(entry)
        self._save_audit_log()
    
    def _load_audit_log(self):
        """Load audit log from disk."""
        log_path = self.data_dir / "admin_audit.json"
        try:
            if log_path.exists():
                with open(log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._audit_log = [
                        AuditEntry(**entry) for entry in data
                    ]
        except Exception as e:
            logger.warning(f"Error loading audit log: {e}")
            self._audit_log = []
    
    def _save_audit_log(self):
        """Save audit log to disk."""
        log_path = self.data_dir / "admin_audit.json"
        try:
            # Keep last 1000 entries
            entries = self._audit_log[-1000:]
            data = [
                {
                    "timestamp": e.timestamp,
                    "action": e.action,
                    "username": e.username,
                    "role": e.role,
                    "target": e.target,
                    "details": e.details,
                    "success": e.success,
                    "error": e.error
                }
                for e in entries
            ]
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving audit log: {e}")
    
    def get_audit_log(self, limit: int = 100) -> List[AuditEntry]:
        """Get recent audit log entries."""
        return self._audit_log[-limit:]


# =============================================================================
# Singleton Instance
# =============================================================================

_github_admin_manager: Optional[GitHubAdminManager] = None


def get_github_admin_manager() -> GitHubAdminManager:
    """Get or create the singleton GitHubAdminManager instance."""
    global _github_admin_manager
    if _github_admin_manager is None:
        _github_admin_manager = GitHubAdminManager()
    return _github_admin_manager


def configure_github_admin(config_repo: str = DEFAULT_CONFIG_REPO,
                          config_branch: str = DEFAULT_CONFIG_BRANCH,
                          config_file: str = DEFAULT_CONFIG_FILE,
                          data_dir: Optional[Path] = None) -> GitHubAdminManager:
    """Configure and return the GitHub admin manager."""
    global _github_admin_manager
    _github_admin_manager = GitHubAdminManager(
        config_repo=config_repo,
        config_branch=config_branch,
        config_file=config_file,
        data_dir=data_dir
    )
    return _github_admin_manager
