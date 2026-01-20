"""
ACB Link Desktop - Configuration Management

Centralized configuration for application defaults, live data URLs,
offline data paths, and user preferences. All configuration is stored
in JSON files for easy modification and deployment.

This module provides:
- Default application configuration
- Live data source URLs (streams, podcasts, affiliates, etc.)
- Offline data paths and cache management
- User preference storage
- Configuration file management
"""

import json
import logging
import os
import platform
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Default Configuration
# =============================================================================


@dataclass
class DataSourceConfig:
    """Configuration for a single data source with live and offline URLs."""

    name: str
    description: str
    live_url: str
    offline_path: str
    cache_duration_hours: int = 24
    last_sync: Optional[str] = None
    enabled: bool = True


@dataclass
class LiveDataConfig:
    """Configuration for all live data sources."""

    # Base URL for ACB Link data
    base_url: str = "https://link.acb.org"

    # Individual data sources
    streams: DataSourceConfig = field(
        default_factory=lambda: DataSourceConfig(
            name="streams",
            description="ACB Media streaming stations",
            live_url="https://link.acb.org/streams.xml",
            offline_path="data/s3/streams.xml",
            cache_duration_hours=168,  # 1 week
        )
    )

    podcasts: DataSourceConfig = field(
        default_factory=lambda: DataSourceConfig(
            name="podcasts",
            description="ACB podcast feeds (OPML)",
            live_url="https://link.acb.org/link.opml",
            offline_path="data/s3/link.opml",
            cache_duration_hours=24,
        )
    )

    state_affiliates: DataSourceConfig = field(
        default_factory=lambda: DataSourceConfig(
            name="state_affiliates",
            description="State affiliate organizations",
            live_url="https://link.acb.org/states.xml",
            offline_path="data/s3/states.xml",
            cache_duration_hours=168,
        )
    )

    special_interest_groups: DataSourceConfig = field(
        default_factory=lambda: DataSourceConfig(
            name="special_interest_groups",
            description="Special interest group affiliates",
            live_url="https://link.acb.org/sigs.xml",
            offline_path="data/s3/sigs.xml",
            cache_duration_hours=168,
        )
    )

    publications: DataSourceConfig = field(
        default_factory=lambda: DataSourceConfig(
            name="publications",
            description="ACB publications and resources",
            live_url="https://link.acb.org/publications.xml",
            offline_path="data/s3/publications.xml",
            cache_duration_hours=168,
        )
    )

    categories: DataSourceConfig = field(
        default_factory=lambda: DataSourceConfig(
            name="categories",
            description="Content categories",
            live_url="https://link.acb.org/categories.xml",
            offline_path="data/s3/categories.xml",
            cache_duration_hours=168,
        )
    )

    # ACB websites and resources
    acb_sites: DataSourceConfig = field(
        default_factory=lambda: DataSourceConfig(
            name="acb_sites",
            description="ACB website directory",
            live_url="https://link.acb.org/acbsites.xml",
            offline_path="data/s3/acbsites.xml",
            cache_duration_hours=168,
        )
    )


@dataclass
class UpdateConfig:
    """Configuration for automatic updates."""

    enabled: bool = True
    check_on_startup: bool = True
    check_interval_hours: int = 24
    github_repo: str = "acbnational/acb_link_desktop"
    github_api_url: str = (
        "https://api.github.com/repos/acbnational/acb_link_desktop/releases/latest"
    )
    download_url_template: str = (
        "https://github.com/acbnational/acb_link_desktop/releases/download/v{version}/{filename}"
    )
    last_check: Optional[str] = None
    skipped_version: Optional[str] = None


@dataclass
class NetworkConfig:
    """Network-related configuration."""

    timeout_seconds: int = 30
    retry_count: int = 3
    retry_delay_seconds: int = 5
    user_agent: str = "ACBLinkDesktop/1.0"
    proxy_enabled: bool = False
    proxy_url: Optional[str] = None


@dataclass
class PathConfig:
    """File and directory paths configuration."""

    # Base directories
    app_data_dir: str = ""
    cache_dir: str = ""
    logs_dir: str = ""

    # User content directories
    downloads_dir: str = ""
    recordings_dir: str = ""

    # Data files
    settings_file: str = ""
    favorites_file: str = ""
    playlists_file: str = ""
    history_file: str = ""

    def __post_init__(self):
        """Initialize default paths based on platform."""
        home = Path.home()

        if platform.system() == "Windows":
            app_data = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
            self.app_data_dir = str(app_data / "ACB Link")
        elif platform.system() == "Darwin":
            self.app_data_dir = str(home / "Library" / "Application Support" / "ACB Link")
        else:
            self.app_data_dir = str(home / ".acb_link")

        self.cache_dir = str(Path(self.app_data_dir) / "cache")
        self.logs_dir = str(Path(self.app_data_dir) / "logs")
        self.downloads_dir = str(home / "Documents" / "ACB Link" / "Podcasts")
        self.recordings_dir = str(home / "Documents" / "ACB Link" / "Recordings")

        self.settings_file = str(Path(self.app_data_dir) / "settings.json")
        self.favorites_file = str(Path(self.app_data_dir) / "favorites.json")
        self.playlists_file = str(Path(self.app_data_dir) / "playlists.json")
        self.history_file = str(Path(self.app_data_dir) / "history.json")

    def ensure_directories(self):
        """Create all necessary directories if they don't exist."""
        for dir_path in [
            self.app_data_dir,
            self.cache_dir,
            self.logs_dir,
            self.downloads_dir,
            self.recordings_dir,
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


@dataclass
class DefaultsConfig:
    """Default application values."""

    # Audio
    default_volume: int = 80
    default_playback_speed: float = 1.0
    default_skip_forward: int = 30
    default_skip_backward: int = 10

    # UI
    default_tab: str = "home"
    default_theme: str = "system"
    default_font_size: int = 12
    default_font_family: str = "Segoe UI"

    # Behavior
    start_minimized: bool = False
    minimize_to_tray: bool = True
    close_to_tray: bool = False
    remember_window_position: bool = True

    # Recording
    default_recording_format: str = "mp3"
    default_recording_bitrate: int = 128

    # Sync
    auto_sync_on_startup: bool = True
    sync_interval_hours: int = 24


# =============================================================================
# Application Configuration Class
# =============================================================================


@dataclass
class AppConfig:
    """
    Main application configuration container.

    This class holds all configuration data and provides methods for
    loading, saving, and managing configuration files.
    """

    version: str = "1.0.0"
    live_data: LiveDataConfig = field(default_factory=LiveDataConfig)
    updates: UpdateConfig = field(default_factory=UpdateConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)

    # Metadata
    first_run: bool = True
    install_date: Optional[str] = None
    last_run: Optional[str] = None

    def __post_init__(self):
        """Initialize configuration after creation."""
        if self.install_date is None:
            self.install_date = datetime.now().isoformat()

    @staticmethod
    def get_config_path() -> Path:
        """Get the path to the main configuration file."""
        if platform.system() == "Windows":
            app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            return app_data / "ACB Link" / "config.json"
        elif platform.system() == "Darwin":
            return Path.home() / "Library" / "Application Support" / "ACB Link" / "config.json"
        else:
            return Path.home() / ".acb_link" / "config.json"

    @staticmethod
    def get_bundled_data_path() -> Path:
        """Get the path to bundled offline data."""
        # Check if running from frozen executable or source
        if getattr(sys, "frozen", False):
            # Running as compiled
            return Path(sys._MEIPASS) / "data" / "s3"  # type: ignore[attr-defined]
        else:
            # Running from source
            return Path(__file__).parent.parent / "data" / "s3"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "live_data": {
                "base_url": self.live_data.base_url,
                "streams": asdict(self.live_data.streams),
                "podcasts": asdict(self.live_data.podcasts),
                "state_affiliates": asdict(self.live_data.state_affiliates),
                "special_interest_groups": asdict(self.live_data.special_interest_groups),
                "publications": asdict(self.live_data.publications),
                "categories": asdict(self.live_data.categories),
                "acb_sites": asdict(self.live_data.acb_sites),
            },
            "updates": asdict(self.updates),
            "network": asdict(self.network),
            "paths": asdict(self.paths),
            "defaults": asdict(self.defaults),
            "first_run": self.first_run,
            "install_date": self.install_date,
            "last_run": self.last_run,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """Create configuration from dictionary."""
        config = cls()

        if "version" in data:
            config.version = data["version"]

        if "live_data" in data:
            ld = data["live_data"]
            config.live_data.base_url = ld.get("base_url", config.live_data.base_url)

            for source_name in [
                "streams",
                "podcasts",
                "state_affiliates",
                "special_interest_groups",
                "publications",
                "categories",
                "acb_sites",
            ]:
                if source_name in ld:
                    source_config = getattr(config.live_data, source_name)
                    for key, value in ld[source_name].items():
                        if hasattr(source_config, key):
                            setattr(source_config, key, value)

        if "updates" in data:
            for key, value in data["updates"].items():
                if hasattr(config.updates, key):
                    setattr(config.updates, key, value)

        if "network" in data:
            for key, value in data["network"].items():
                if hasattr(config.network, key):
                    setattr(config.network, key, value)

        if "paths" in data:
            for key, value in data["paths"].items():
                if hasattr(config.paths, key) and value:
                    setattr(config.paths, key, value)

        if "defaults" in data:
            for key, value in data["defaults"].items():
                if hasattr(config.defaults, key):
                    setattr(config.defaults, key, value)

        config.first_run = data.get("first_run", True)
        config.install_date = data.get("install_date")
        config.last_run = data.get("last_run")

        return config

    def save(self, filepath: Optional[Path] = None) -> bool:
        """
        Save configuration to JSON file.

        Args:
            filepath: Optional path to save to. Uses default if not specified.

        Returns:
            True if save was successful, False otherwise.
        """
        if filepath is None:
            filepath = self.get_config_path()

        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    @classmethod
    def load(cls, filepath: Optional[Path] = None) -> "AppConfig":
        """
        Load configuration from JSON file.

        Args:
            filepath: Optional path to load from. Uses default if not specified.

        Returns:
            AppConfig instance (default if file doesn't exist or is invalid).
        """
        if filepath is None:
            filepath = cls.get_config_path()

        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                config = cls.from_dict(data)
                logger.info(f"Configuration loaded from {filepath}")
                return config

            except Exception as e:
                logger.warning(f"Failed to load configuration: {e}. Using defaults.")

        return cls()

    def get_data_sources(self) -> List[DataSourceConfig]:
        """Get a list of all data source configurations."""
        return [
            self.live_data.streams,
            self.live_data.podcasts,
            self.live_data.state_affiliates,
            self.live_data.special_interest_groups,
            self.live_data.publications,
            self.live_data.categories,
            self.live_data.acb_sites,
        ]

    def mark_as_run(self):
        """Mark the application as having been run."""
        self.first_run = False
        self.last_run = datetime.now().isoformat()


# =============================================================================
# Singleton Configuration Instance
# =============================================================================

_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get the global configuration instance.

    Returns:
        The singleton AppConfig instance.
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = AppConfig.load()
        _config_instance.paths.ensure_directories()

    return _config_instance


def reload_config() -> AppConfig:
    """
    Reload configuration from disk.

    Returns:
        The reloaded AppConfig instance.
    """
    global _config_instance
    _config_instance = AppConfig.load()
    _config_instance.paths.ensure_directories()
    return _config_instance


def save_config() -> bool:
    """
    Save the current configuration to disk.

    Returns:
        True if save was successful.
    """
    config = get_config()
    return config.save()


# Import sys for frozen check
import sys  # noqa: E402
