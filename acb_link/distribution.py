"""
ACB Link Desktop - Store Distribution Support

Support for Microsoft Store and Mac App Store distribution,
including delta updates for efficient patch downloads.
"""

import json
import hashlib
import platform
import logging
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from enum import Enum

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logger = logging.getLogger(__name__)


# =============================================================================
# Distribution Channel Detection
# =============================================================================

class DistributionChannel(Enum):
    """Application distribution channel."""
    GITHUB = "github"  # GitHub Releases (default)
    MICROSOFT_STORE = "microsoft_store"
    MAC_APP_STORE = "mac_app_store"
    PORTABLE = "portable"  # ZIP/standalone
    DEVELOPMENT = "development"


def detect_distribution_channel() -> DistributionChannel:
    """Detect how the application was installed."""
    system = platform.system().lower()
    
    if system == "windows":
        # Check for Microsoft Store installation
        # Store apps are installed under WindowsApps
        try:
            import sys
            exe_path = Path(sys.executable).resolve()
            if "WindowsApps" in str(exe_path):
                return DistributionChannel.MICROSOFT_STORE
        except Exception:
            pass
        
        # Check for portable mode (no installer registry)
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\ACB\ACB Link Desktop"
            )
            winreg.CloseKey(key)
            return DistributionChannel.GITHUB  # Installed via GitHub installer
        except FileNotFoundError:
            # Check if running from source
            if Path(__file__).parent.parent.name == "acb_link":
                return DistributionChannel.DEVELOPMENT
            return DistributionChannel.PORTABLE
        except Exception:
            pass
    
    elif system == "darwin":
        # Check for Mac App Store installation
        try:
            import subprocess
            result = subprocess.run(
                ["codesign", "-d", "--entitlements", ":-", str(Path(__file__).parent)],
                capture_output=True,
                text=True
            )
            if "com.apple.application-identifier" in result.stdout:
                # Has App Store entitlements
                return DistributionChannel.MAC_APP_STORE
        except Exception:
            pass
        
        # Check if in /Applications
        try:
            import sys
            exe_path = Path(sys.executable).resolve()
            if "/Applications/" in str(exe_path):
                return DistributionChannel.GITHUB
        except Exception:
            pass
        
        return DistributionChannel.DEVELOPMENT
    
    return DistributionChannel.GITHUB


# =============================================================================
# Delta Update Support
# =============================================================================

@dataclass
class FileManifest:
    """Manifest of files and their hashes for delta updates."""
    path: str
    size: int
    sha256: str
    modified: str


@dataclass
class DeltaUpdateInfo:
    """Information about an available delta update."""
    from_version: str
    to_version: str
    files_changed: List[FileManifest]
    files_added: List[FileManifest]
    files_removed: List[str]
    delta_size: int  # Total size of delta download
    full_size: int  # Size of full installer for comparison
    delta_url: str
    checksum: str
    
    @property
    def savings_percent(self) -> float:
        """Calculate bandwidth savings vs full download."""
        if self.full_size == 0:
            return 0.0
        return (1 - (self.delta_size / self.full_size)) * 100


class DeltaUpdateManager:
    """
    Manages delta (patch-only) updates for efficient bandwidth usage.
    
    Instead of downloading the full installer, only changed files
    are downloaded and applied.
    """
    
    MANIFEST_FILENAME = "manifest.json"
    DELTA_API_BASE = "https://api.github.com/repos/acb-bits/acb-link-desktop"
    
    def __init__(self, current_version: str, install_path: Optional[Path] = None):
        self.current_version = current_version
        self.install_path = install_path or self._detect_install_path()
        self._current_manifest: Optional[Dict[str, FileManifest]] = None
    
    def _detect_install_path(self) -> Path:
        """Detect the application installation path."""
        import sys
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        return Path(__file__).parent.parent
    
    def generate_manifest(self) -> Dict[str, FileManifest]:
        """Generate manifest of current installation."""
        manifest = {}
        
        for file_path in self.install_path.rglob("*"):
            if file_path.is_file():
                # Skip certain files
                if any(skip in str(file_path) for skip in [
                    "__pycache__", ".pyc", ".log", "cache"
                ]):
                    continue
                
                try:
                    rel_path = file_path.relative_to(self.install_path)
                    file_hash = self._hash_file(file_path)
                    
                    manifest[str(rel_path)] = FileManifest(
                        path=str(rel_path),
                        size=file_path.stat().st_size,
                        sha256=file_hash,
                        modified=datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                    )
                except Exception as e:
                    logger.debug(f"Skipping {file_path}: {e}")
        
        self._current_manifest = manifest
        return manifest
    
    def check_for_delta_update(
        self,
        target_version: str,
        callback: Optional[Callable[[Optional[DeltaUpdateInfo], Optional[str]], None]] = None
    ) -> Optional[DeltaUpdateInfo]:
        """
        Check if a delta update is available from current to target version.
        
        Returns DeltaUpdateInfo if delta available, None if full download needed.
        """
        if not HAS_REQUESTS:
            if callback:
                callback(None, "Network library not available")
            return None
        
        if callback:
            thread = threading.Thread(
                target=self._check_delta_async,
                args=(target_version, callback),
                daemon=True
            )
            thread.start()
            return None
        else:
            return self._do_check_delta(target_version)
    
    def _check_delta_async(
        self,
        target_version: str,
        callback: Callable[[Optional[DeltaUpdateInfo], Optional[str]], None]
    ):
        try:
            result = self._do_check_delta(target_version)
            callback(result, None)
        except Exception as e:
            callback(None, str(e))
    
    def _do_check_delta(self, target_version: str) -> Optional[DeltaUpdateInfo]:
        """Perform delta update check."""
        try:
            # Check if delta manifest exists for this version pair
            delta_url = (
                f"{self.DELTA_API_BASE}/releases/download/"
                f"v{target_version}/delta-{self.current_version}-to-{target_version}.json"
            )
            
            response = requests.get(delta_url, timeout=10)
            
            if response.status_code == 404:
                # No delta available, need full download
                logger.info(f"No delta update available from {self.current_version} to {target_version}")
                return None
            
            response.raise_for_status()
            delta_data = response.json()
            
            return DeltaUpdateInfo(
                from_version=delta_data["from_version"],
                to_version=delta_data["to_version"],
                files_changed=[FileManifest(**f) for f in delta_data.get("changed", [])],
                files_added=[FileManifest(**f) for f in delta_data.get("added", [])],
                files_removed=delta_data.get("removed", []),
                delta_size=delta_data["delta_size"],
                full_size=delta_data["full_size"],
                delta_url=delta_data["delta_url"],
                checksum=delta_data["checksum"],
            )
            
        except requests.RequestException as e:
            logger.warning(f"Delta check failed: {e}")
            return None
    
    def apply_delta_update(
        self,
        delta_info: DeltaUpdateInfo,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> bool:
        """
        Download and apply a delta update.
        
        Args:
            delta_info: Delta update information
            progress_callback: Called with (current, total, status_message)
            
        Returns:
            True if update applied successfully
        """
        if not HAS_REQUESTS:
            return False
        
        try:
            # Download delta package
            if progress_callback:
                progress_callback(0, 100, "Downloading delta update...")
            
            response = requests.get(delta_info.delta_url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Save to temp file
            import tempfile
            import zipfile
            
            temp_dir = Path(tempfile.mkdtemp(prefix="acblink_delta_"))
            delta_file = temp_dir / "delta.zip"
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(delta_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = int((downloaded / total_size) * 50)
                            progress_callback(percent, 100, "Downloading...")
            
            # Verify checksum
            if progress_callback:
                progress_callback(50, 100, "Verifying download...")
            
            file_hash = self._hash_file(delta_file)
            if file_hash != delta_info.checksum:
                logger.error("Delta update checksum mismatch")
                return False
            
            # Extract and apply
            if progress_callback:
                progress_callback(60, 100, "Applying update...")
            
            extract_dir = temp_dir / "extracted"
            with zipfile.ZipFile(delta_file, 'r') as zf:
                zf.extractall(extract_dir)
            
            # Apply changes (simplified - real implementation would be more robust)
            total_files = (
                len(delta_info.files_changed) +
                len(delta_info.files_added) +
                len(delta_info.files_removed)
            )
            processed = 0
            
            # Remove deleted files
            for rel_path in delta_info.files_removed:
                target = self.install_path / rel_path
                if target.exists():
                    target.unlink()
                processed += 1
                if progress_callback:
                    percent = 60 + int((processed / total_files) * 40)
                    progress_callback(percent, 100, f"Removing {rel_path}")
            
            # Copy changed and added files
            for file_info in delta_info.files_changed + delta_info.files_added:
                source = extract_dir / file_info.path
                target = self.install_path / file_info.path
                
                if source.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(source, target)
                
                processed += 1
                if progress_callback:
                    percent = 60 + int((processed / total_files) * 40)
                    progress_callback(percent, 100, f"Updating {file_info.path}")
            
            if progress_callback:
                progress_callback(100, 100, "Update complete!")
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Delta update failed: {e}")
            return False
    
    @staticmethod
    def _hash_file(filepath: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()


# =============================================================================
# Store-Specific Update Handlers
# =============================================================================

class MicrosoftStoreUpdater:
    """
    Handles updates for Microsoft Store distribution.
    
    When installed from the Microsoft Store, updates are managed
    by the Store itself. This class provides integration hooks.
    """
    
    @staticmethod
    def is_store_version() -> bool:
        """Check if running as Microsoft Store app."""
        return detect_distribution_channel() == DistributionChannel.MICROSOFT_STORE
    
    @staticmethod
    def check_for_update() -> bool:
        """
        Check for Store updates.
        
        For Store apps, this triggers the Store's update check.
        """
        if not MicrosoftStoreUpdater.is_store_version():
            return False
        
        try:
            # Use Windows Runtime to check for updates
            # This requires the app to have Store capabilities
            import subprocess
            subprocess.run(
                ["start", "ms-windows-store://updates"],
                shell=True,
                check=False
            )
            return True
        except Exception as e:
            logger.warning(f"Store update check failed: {e}")
            return False
    
    @staticmethod
    def get_store_link() -> str:
        """Get Microsoft Store link for the app."""
        # This would be the actual Store ID when published
        return "ms-windows-store://pdp/?ProductId=9XXXXXXXXX"


class MacAppStoreUpdater:
    """
    Handles updates for Mac App Store distribution.
    
    When installed from the Mac App Store, updates are managed
    by the App Store itself. This class provides integration hooks.
    """
    
    @staticmethod
    def is_store_version() -> bool:
        """Check if running as Mac App Store app."""
        return detect_distribution_channel() == DistributionChannel.MAC_APP_STORE
    
    @staticmethod
    def check_for_update() -> bool:
        """
        Check for App Store updates.
        
        For App Store apps, this opens the App Store updates page.
        """
        if not MacAppStoreUpdater.is_store_version():
            return False
        
        try:
            import subprocess
            subprocess.run(
                ["open", "macappstore://showUpdatesPage"],
                check=False
            )
            return True
        except Exception as e:
            logger.warning(f"App Store update check failed: {e}")
            return False
    
    @staticmethod
    def get_store_link() -> str:
        """Get Mac App Store link for the app."""
        # This would be the actual App Store ID when published
        return "macappstore://apps.apple.com/app/idXXXXXXXXXX"


# =============================================================================
# Unified Distribution Manager
# =============================================================================

class DistributionManager:
    """
    Unified manager for all distribution channels.
    
    Automatically detects distribution channel and provides
    appropriate update mechanisms.
    """
    
    def __init__(self, current_version: str):
        self.current_version = current_version
        self.channel = detect_distribution_channel()
        self.delta_manager = DeltaUpdateManager(current_version)
        
        logger.info(f"Distribution channel: {self.channel.value}")
    
    def get_update_mechanism(self) -> str:
        """Get description of how updates are handled."""
        if self.channel == DistributionChannel.MICROSOFT_STORE:
            return "Updates are managed through the Microsoft Store"
        elif self.channel == DistributionChannel.MAC_APP_STORE:
            return "Updates are managed through the Mac App Store"
        elif self.channel == DistributionChannel.GITHUB:
            return "Updates are downloaded from GitHub Releases"
        elif self.channel == DistributionChannel.PORTABLE:
            return "Please download new versions manually from GitHub"
        else:
            return "Running in development mode"
    
    def check_for_updates(
        self,
        callback: Optional[Callable[[bool, str], None]] = None
    ):
        """
        Check for updates using the appropriate mechanism.
        
        Args:
            callback: Called with (update_available, message)
        """
        if self.channel == DistributionChannel.MICROSOFT_STORE:
            success = MicrosoftStoreUpdater.check_for_update()
            if callback:
                callback(success, "Opening Microsoft Store...")
        
        elif self.channel == DistributionChannel.MAC_APP_STORE:
            success = MacAppStoreUpdater.check_for_update()
            if callback:
                callback(success, "Opening App Store...")
        
        elif self.channel == DistributionChannel.GITHUB:
            # Use existing GitHub update mechanism
            from .updater import check_for_updates_manual
            check_for_updates_manual(self.current_version)
            if callback:
                callback(True, "Checking GitHub releases...")
        
        else:
            if callback:
                callback(False, self.get_update_mechanism())
    
    def supports_delta_updates(self) -> bool:
        """Check if delta updates are supported for this channel."""
        return self.channel == DistributionChannel.GITHUB
    
    def get_store_link(self) -> Optional[str]:
        """Get app store link if applicable."""
        if self.channel == DistributionChannel.MICROSOFT_STORE:
            return MicrosoftStoreUpdater.get_store_link()
        elif self.channel == DistributionChannel.MAC_APP_STORE:
            return MacAppStoreUpdater.get_store_link()
        return None


# =============================================================================
# Convenience Functions
# =============================================================================

def get_distribution_channel() -> DistributionChannel:
    """Get the current distribution channel."""
    return detect_distribution_channel()


def get_distribution_manager(version: str) -> DistributionManager:
    """Get a distribution manager instance."""
    return DistributionManager(version)
