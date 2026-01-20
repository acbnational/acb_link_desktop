"""
ACB Link - Application Updater
GitHub-based update system for checking and applying updates.
Cross-platform support for Windows and macOS.
"""

import hashlib
import json
import platform
import subprocess
import tempfile
import threading
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import wx

    HAS_WX = True
except ImportError:
    HAS_WX = False


# GitHub repository information
GITHUB_OWNER = "acbnational"
GITHUB_REPO = "acb_link_desktop"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RELEASES_URL = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"


@dataclass
class ReleaseAsset:
    """Represents a downloadable asset from a GitHub release."""

    name: str
    download_url: str
    size: int
    content_type: str

    @property
    def is_windows_installer(self) -> bool:
        """Check if this is a Windows installer."""
        return self.name.endswith(".exe") or self.name.endswith(".msi")

    @property
    def is_mac_installer(self) -> bool:
        """Check if this is a macOS installer."""
        return self.name.endswith(".dmg") or self.name.endswith(".pkg")

    @property
    def is_portable(self) -> bool:
        """Check if this is a portable ZIP."""
        return self.name.endswith(".zip")

    @property
    def is_checksum(self) -> bool:
        """Check if this is a checksum file."""
        return "sha256" in self.name.lower() or "checksum" in self.name.lower()


@dataclass
class Release:
    """Represents a GitHub release."""

    tag_name: str
    name: str
    body: str
    published_at: str
    html_url: str
    prerelease: bool
    draft: bool
    assets: List[ReleaseAsset]

    @property
    def version(self) -> str:
        """Extract version number from tag (removes 'v' prefix)."""
        return self.tag_name.lstrip("v")

    @property
    def version_tuple(self) -> Tuple[int, ...]:
        """Parse version as tuple for comparison."""
        try:
            return tuple(int(x) for x in self.version.split("."))
        except ValueError:
            return (0, 0, 0)

    def get_asset_for_platform(self) -> Optional[ReleaseAsset]:
        """Get the appropriate installer for the current platform."""
        system = platform.system().lower()

        for asset in self.assets:
            if asset.is_checksum:
                continue

            if system == "windows" and asset.is_windows_installer:
                return asset
            elif system == "darwin" and asset.is_mac_installer:
                return asset

        # Fall back to portable ZIP
        for asset in self.assets:
            if asset.is_portable:
                return asset

        return None


class UpdateChecker:
    """
    Checks for application updates using GitHub releases.

    This provides a free, reliable update mechanism using GitHub's
    release infrastructure. No additional server infrastructure required.
    """

    def __init__(self, current_version: str):
        """
        Initialize the update checker.

        Args:
            current_version: Current application version (e.g., "2.0.0")
        """
        self.current_version = current_version
        self.current_version_tuple = self._parse_version(current_version)
        self._latest_release: Optional[Release] = None
        self._check_in_progress = False
        # Expose API URL for testing and configuration
        self.api_url = GITHUB_RELEASES_URL
        self.repo_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"

    def _parse_version(self, version: str) -> Tuple[int, ...]:
        """Parse version string to tuple for comparison."""
        try:
            clean = version.lstrip("v")
            return tuple(int(x) for x in clean.split("."))
        except ValueError:
            return (0, 0, 0)

    def check_for_updates(
        self,
        include_prereleases: bool = False,
        callback: Optional[Callable[[Optional[Release], Optional[str]], None]] = None,
    ) -> Optional[Release]:
        """
        Check GitHub for new releases.

        Args:
            include_prereleases: Whether to include pre-release versions
            callback: Optional callback for async operation (release, error)

        Returns:
            Release object if update available, None otherwise
        """
        if not HAS_REQUESTS:
            error = "requests library not available"
            if callback:
                callback(None, error)
            return None

        if callback:
            # Run async
            thread = threading.Thread(
                target=self._check_async, args=(include_prereleases, callback)
            )
            thread.daemon = True
            thread.start()
            return None
        else:
            # Run sync
            return self._do_check(include_prereleases)

    def _check_async(
        self,
        include_prereleases: bool,
        callback: Callable[[Optional[Release], Optional[str]], None],
    ):
        """Async version of update check."""
        try:
            release = self._do_check(include_prereleases)
            callback(release, None)
        except Exception as e:
            callback(None, str(e))

    def _do_check(self, include_prereleases: bool) -> Optional[Release]:
        """Perform the actual update check."""
        try:
            # Fetch latest releases
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": f"ACBLink/{self.current_version}",
            }

            response = requests.get(GITHUB_RELEASES_URL, headers=headers, timeout=10)
            response.raise_for_status()

            releases_data = response.json()

            # Find the latest applicable release
            for release_data in releases_data:
                if release_data.get("draft", False):
                    continue

                if not include_prereleases and release_data.get("prerelease", False):
                    continue

                # Parse release
                release = self._parse_release(release_data)

                # Check if newer
                if release.version_tuple > self.current_version_tuple:
                    self._latest_release = release
                    return release

            return None

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to check for updates: {e}")

    def _parse_release(self, data: dict) -> Release:
        """Parse GitHub release JSON to Release object."""
        assets = []
        for asset_data in data.get("assets", []):
            assets.append(
                ReleaseAsset(
                    name=asset_data["name"],
                    download_url=asset_data["browser_download_url"],
                    size=asset_data["size"],
                    content_type=asset_data["content_type"],
                )
            )

        return Release(
            tag_name=data["tag_name"],
            name=data["name"],
            body=data.get("body", ""),
            published_at=data["published_at"],
            html_url=data["html_url"],
            prerelease=data.get("prerelease", False),
            draft=data.get("draft", False),
            assets=assets,
        )

    @property
    def latest_release(self) -> Optional[Release]:
        """Get the last fetched release."""
        return self._latest_release


class UpdateDownloader:
    """Downloads and verifies update packages."""

    def __init__(self):
        self._download_path: Optional[Path] = None
        self._progress_callback: Optional[Callable[[int, int], None]] = None

    def download_release(
        self, release: Release, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[Path]:
        """
        Download the release installer for the current platform.

        Args:
            release: Release to download
            progress_callback: Called with (bytes_downloaded, total_bytes)

        Returns:
            Path to downloaded file, or None on failure
        """
        asset = release.get_asset_for_platform()
        if not asset:
            raise RuntimeError("No compatible installer found for this platform")

        self._progress_callback = progress_callback

        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp(prefix="acblink_update_"))
        download_path = temp_dir / asset.name

        try:
            response = requests.get(asset.download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if self._progress_callback:
                            self._progress_callback(downloaded, total_size)

            self._download_path = download_path
            return download_path

        except Exception as e:
            # Clean up on failure
            if download_path.exists():
                download_path.unlink()
            raise RuntimeError(f"Download failed: {e}")

    def verify_checksum(self, file_path: Path, expected_sha256: str) -> bool:
        """Verify file SHA256 checksum."""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest().lower() == expected_sha256.lower()


class UpdateInstaller:
    """Installs downloaded updates."""

    @staticmethod
    def install_update(installer_path: Path, silent: bool = False) -> bool:
        """
        Launch the installer and exit the application.

        Args:
            installer_path: Path to the installer
            silent: Run installer silently (Windows only)

        Returns:
            True if installer launched successfully
        """
        system = platform.system().lower()

        try:
            if system == "windows":
                return UpdateInstaller._install_windows(installer_path, silent)
            elif system == "darwin":
                return UpdateInstaller._install_macos(installer_path)
            else:
                raise RuntimeError(f"Unsupported platform: {system}")
        except Exception as e:
            raise RuntimeError(f"Failed to launch installer: {e}")

    @staticmethod
    def _install_windows(installer_path: Path, silent: bool) -> bool:
        """Install on Windows."""
        if installer_path.suffix.lower() == ".msi":
            args = ["msiexec", "/i", str(installer_path)]
            if silent:
                args.extend(["/qn", "/norestart"])
        else:
            args = [str(installer_path)]
            if silent:
                args.append("/S")  # NSIS silent flag

        # Launch installer
        subprocess.Popen(args, shell=True)
        return True

    @staticmethod
    def _install_macos(installer_path: Path) -> bool:
        """Install on macOS."""
        if installer_path.suffix.lower() == ".dmg":
            # Mount DMG and open
            subprocess.Popen(["open", str(installer_path)])
        elif installer_path.suffix.lower() == ".pkg":
            # Launch pkg installer
            subprocess.Popen(["open", str(installer_path)])
        return True


class UpdateDialog:
    """
    wxPython dialog for update notifications and installation.

    This is a standalone dialog that can be used with the update system.
    """

    @staticmethod
    def show_update_available(
        parent,
        release: Release,
        on_download: Callable[[], None],
        on_skip: Callable[[], None],
        on_remind: Callable[[], None],
    ):
        """
        Show update available dialog.

        Args:
            parent: Parent window
            release: The available release
            on_download: Callback when user chooses to download
            on_skip: Callback when user skips this version
            on_remind: Callback when user wants reminder later
        """
        if not HAS_WX:
            return

        message = f"""A new version of ACB Link Desktop is available!

Current version: {release.version}
New version: {release.tag_name}

Release notes:
{release.body[:500]}{'...' if len(release.body) > 500 else ''}

Would you like to download and install the update?"""

        dialog = wx.Dialog(
            parent,
            title="Update Available",
            size=(500, 400),  # type: ignore[arg-type]
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Message
        msg_text = wx.TextCtrl(
            dialog, value=message, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
        )
        sizer.Add(msg_text, 1, wx.EXPAND | wx.ALL, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_download = wx.Button(dialog, label="Download && Install")
        btn_download.SetDefault()
        btn_sizer.Add(btn_download, 0, wx.RIGHT, 5)

        btn_release_notes = wx.Button(dialog, label="View Release Notes")
        btn_sizer.Add(btn_release_notes, 0, wx.RIGHT, 5)

        btn_skip = wx.Button(dialog, label="Skip This Version")
        btn_sizer.Add(btn_skip, 0, wx.RIGHT, 5)

        btn_remind = wx.Button(dialog, label="Remind Me Later")
        btn_sizer.Add(btn_remind, 0)

        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        dialog.SetSizer(sizer)

        # Bind events
        def on_download_click(event):
            dialog.EndModal(wx.ID_OK)
            on_download()

        def on_skip_click(event):
            dialog.EndModal(wx.ID_CANCEL)
            on_skip()

        def on_remind_click(event):
            dialog.EndModal(wx.ID_CANCEL)
            on_remind()

        def on_release_notes_click(event):
            webbrowser.open(release.html_url)

        btn_download.Bind(wx.EVT_BUTTON, on_download_click)
        btn_skip.Bind(wx.EVT_BUTTON, on_skip_click)
        btn_remind.Bind(wx.EVT_BUTTON, on_remind_click)
        btn_release_notes.Bind(wx.EVT_BUTTON, on_release_notes_click)

        dialog.ShowModal()
        dialog.Destroy()

    @staticmethod
    def show_no_updates(parent):
        """Show dialog when no updates are available."""
        if not HAS_WX:
            return

        wx.MessageBox(
            "You are running the latest version of ACB Link Desktop.",
            "No Updates Available",
            wx.OK | wx.ICON_INFORMATION,
            parent,
        )

    @staticmethod
    def show_check_failed(parent, error: str):
        """Show dialog when update check fails."""
        if not HAS_WX:
            return

        wx.MessageBox(
            f"Unable to check for updates:\n\n{error}\n\nPlease check your internet connection and try again.",
            "Update Check Failed",
            wx.OK | wx.ICON_WARNING,
            parent,
        )


class AutoUpdateManager:
    """
    Manages automatic update checking with settings persistence.
    """

    def __init__(self, current_version: str, settings_path: Optional[Path] = None):
        """
        Initialize the auto-update manager.

        Args:
            current_version: Current application version
            settings_path: Path to settings file (default: ~/.acb_link/update_settings.json)
        """
        self.checker = UpdateChecker(current_version)
        self.downloader = UpdateDownloader()

        if settings_path is None:
            settings_path = Path.home() / ".acb_link" / "update_settings.json"
        self.settings_path = settings_path

        self._settings = self._load_settings()

    def _load_settings(self) -> dict:
        """Load update settings from file."""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "check_automatically": True,
            "include_prereleases": False,
            "skipped_versions": [],
            "last_check": None,
            "remind_later_until": None,
        }

    def _save_settings(self):
        """Save update settings to file."""
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, "w") as f:
            json.dump(self._settings, f, indent=2)

    @property
    def check_automatically(self) -> bool:
        """Whether to check for updates automatically on startup."""
        return self._settings.get("check_automatically", True)

    @check_automatically.setter
    def check_automatically(self, value: bool):
        self._settings["check_automatically"] = value
        self._save_settings()

    def skip_version(self, version: str):
        """Skip a specific version."""
        skipped = self._settings.get("skipped_versions", [])
        if version not in skipped:
            skipped.append(version)
            self._settings["skipped_versions"] = skipped
            self._save_settings()

    def is_version_skipped(self, version: str) -> bool:
        """Check if a version was skipped."""
        return version in self._settings.get("skipped_versions", [])

    def remind_later(self, hours: int = 24):
        """Set reminder for later."""
        remind_time = datetime.now().timestamp() + (hours * 3600)
        self._settings["remind_later_until"] = remind_time
        self._save_settings()

    def should_remind(self) -> bool:
        """Check if reminder period has passed."""
        remind_until = self._settings.get("remind_later_until")
        if remind_until is None:
            return True
        return datetime.now().timestamp() > remind_until

    def check_and_notify(self, parent=None, silent_if_none: bool = True):
        """
        Check for updates and show notification if available.

        Args:
            parent: Parent window for dialogs
            silent_if_none: Don't show dialog if no updates
        """

        def on_result(release: Optional[Release], error: Optional[str]):
            if error:
                if not silent_if_none:
                    UpdateDialog.show_check_failed(parent, error)
                return

            if release is None:
                if not silent_if_none:
                    UpdateDialog.show_no_updates(parent)
                return

            # Check if skipped or reminded
            if self.is_version_skipped(release.version):
                return

            if not self.should_remind():
                return

            # Show update dialog
            UpdateDialog.show_update_available(
                parent,
                release,
                on_download=lambda: self._do_download_and_install(release, parent),
                on_skip=lambda: self.skip_version(release.version),
                on_remind=lambda: self.remind_later(24),
            )

        self.checker.check_for_updates(
            include_prereleases=self._settings.get("include_prereleases", False), callback=on_result
        )

    def _do_download_and_install(self, release: Release, parent):
        """Download and install the update."""
        if not HAS_WX:
            return

        # Show progress dialog
        progress = wx.ProgressDialog(
            "Downloading Update",
            f"Downloading {release.name}...",
            maximum=100,
            parent=parent,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT,
        )

        def on_progress(downloaded, total):
            if total > 0:
                percent = int((downloaded / total) * 100)
                wx.CallAfter(
                    progress.Update,
                    percent,
                    f"Downloaded {downloaded // 1024} KB of {total // 1024} KB",
                )

        try:
            installer_path = self.downloader.download_release(
                release, progress_callback=on_progress
            )

            progress.Destroy()

            if installer_path:
                # Confirm installation
                result = wx.MessageBox(
                    "Download complete. Install now?\n\nThe application will close to install the update.",
                    "Install Update",
                    wx.YES_NO | wx.ICON_QUESTION,
                    parent,
                )

                if result == wx.YES:
                    UpdateInstaller.install_update(installer_path)
                    # Exit application
                    wx.GetApp().ExitMainLoop()

        except Exception as e:
            progress.Destroy()
            wx.MessageBox(
                f"Download failed:\n\n{e}", "Download Error", wx.OK | wx.ICON_ERROR, parent
            )


# Global singleton for AutoUpdateManager
_update_manager_instance: Optional[AutoUpdateManager] = None


# Convenience functions for integration
def get_update_manager(current_version: str) -> AutoUpdateManager:
    """Get or create the global update manager instance (singleton)."""
    global _update_manager_instance
    if _update_manager_instance is None:
        _update_manager_instance = AutoUpdateManager(current_version)
    return _update_manager_instance


def check_for_updates_on_startup(current_version: str, parent=None):
    """Convenience function for startup update check."""
    manager = get_update_manager(current_version)
    if manager.check_automatically:
        manager.check_and_notify(parent, silent_if_none=True)


def check_for_updates_manual(current_version: str, parent=None):
    """Convenience function for manual update check (from menu)."""
    manager = get_update_manager(current_version)
    manager.check_and_notify(parent, silent_if_none=False)
