"""
ACB Link - Utility Functions
Helper functions and utilities for the application.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Configure logging
def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Set up application logging."""
    log_dir = Path.home() / ".acb_link" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"acb_link_{datetime.now().strftime('%Y%m%d')}.log"

    logger = logging.getLogger("acb_link")
    logger.setLevel(log_level)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_app_data_dir() -> Path:
    """Get the application data directory."""
    app_dir = Path.home() / ".acb_link"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_cache_dir() -> Path:
    """Get the cache directory."""
    cache_dir = get_app_data_dir() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_downloads_dir() -> Path:
    """Get the downloads directory."""
    downloads_dir = get_app_data_dir() / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    return downloads_dir


def get_recordings_dir() -> Path:
    """Get the recordings directory."""
    recordings_dir = get_app_data_dir() / "recordings"
    recordings_dir.mkdir(parents=True, exist_ok=True)
    return recordings_dir


def format_duration(seconds: float) -> str:
    """Format duration in seconds to HH:MM:SS or MM:SS."""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def format_file_size(bytes_size: int) -> str:
    """Format file size in bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(bytes_size) < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    # Also remove leading/trailing dots and spaces
    filename = filename.strip(". ")
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def generate_unique_filename(base_name: str, extension: str, directory: Path) -> Path:
    """Generate a unique filename in the given directory."""
    sanitized = sanitize_filename(base_name)
    filename = f"{sanitized}.{extension}"
    filepath = directory / filename

    counter = 1
    while filepath.exists():
        filename = f"{sanitized}_{counter}.{extension}"
        filepath = directory / filename
        counter += 1

    return filepath


class RecentItemsManager:
    """Manages recently played items."""

    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self.items: List[Dict[str, Any]] = []
        self._load()

    @property
    def _file_path(self) -> Path:
        return get_app_data_dir() / "recent_items.json"

    def _load(self):
        """Load recent items from file."""
        if self._file_path.exists():
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    self.items = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.items = []

    def _save(self):
        """Save recent items to file."""
        try:
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(self.items, f, indent=2)
        except IOError:
            pass

    def add_item(self, item_type: str, name: str, **kwargs):
        """Add an item to recent history."""
        item = {"type": item_type, "name": name, "timestamp": datetime.now().isoformat(), **kwargs}

        # Remove duplicate if exists
        self.items = [i for i in self.items if not (i["type"] == item_type and i["name"] == name)]

        # Add to front
        self.items.insert(0, item)

        # Trim to max
        self.items = self.items[: self.max_items]

        self._save()

    def get_items(self, item_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent items, optionally filtered by type."""
        if item_type:
            filtered = [i for i in self.items if i["type"] == item_type]
        else:
            filtered = self.items
        return filtered[:limit]

    def clear(self):
        """Clear all recent items."""
        self.items = []
        self._save()


class PlaybackPositionManager:
    """Manages playback positions for podcast episodes."""

    def __init__(self):
        self.positions: Dict[str, float] = {}
        self._load()

    @property
    def _file_path(self) -> Path:
        return get_app_data_dir() / "playback_positions.json"

    def _load(self):
        """Load positions from file."""
        if self._file_path.exists():
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    self.positions = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.positions = {}

    def _save(self):
        """Save positions to file."""
        try:
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(self.positions, f, indent=2)
        except IOError:
            pass

    def get_position(self, episode_id: str) -> float:
        """Get saved position for an episode."""
        return self.positions.get(episode_id, 0.0)

    def save_position(self, episode_id: str, position: float):
        """Save playback position for an episode."""
        self.positions[episode_id] = position
        self._save()

    def clear_position(self, episode_id: str):
        """Clear saved position for an episode."""
        if episode_id in self.positions:
            del self.positions[episode_id]
            self._save()


class CacheManager:
    """Manages application cache."""

    def __init__(self, max_size_mb: int = 500):
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.cache_dir = get_cache_dir()

    def get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total = 0
        for file in self.cache_dir.rglob("*"):
            if file.is_file():
                total += file.stat().st_size
        return total

    def clear_cache(self):
        """Clear all cached files."""
        import shutil

        for item in self.cache_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    def enforce_size_limit(self):
        """Remove oldest files to stay under size limit."""
        while self.get_cache_size() > self.max_size:
            files = []
            for file in self.cache_dir.rglob("*"):
                if file.is_file():
                    files.append((file, file.stat().st_mtime))

            if not files:
                break

            # Sort by modification time, oldest first
            files.sort(key=lambda x: x[1])

            # Remove oldest file
            oldest_file, _ = files[0]
            oldest_file.unlink()


def check_internet_connection() -> bool:
    """Check if there's an active internet connection."""
    import socket

    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


def get_system_info() -> Dict[str, str]:
    """Get system information for debugging."""
    import platform

    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
        "architecture": platform.machine(),
    }


# Accessibility helpers


def announce_to_screen_reader(message: str):
    """
    Announce a message to the screen reader.
    Uses accessible_output2 if available, falls back to wx.
    """
    try:
        import accessible_output2.outputs.auto as ao

        speaker = ao.Auto()
        speaker.speak(message)
    except ImportError:
        # Fall back to logging if accessible_output2 not available
        logger = logging.getLogger("acb_link")
        logger.info(f"Screen reader announcement: {message}")


def is_screen_reader_active() -> bool:
    """Check if a screen reader is currently running."""
    if sys.platform == "win32":
        import ctypes

        try:
            # Check for JAWS
            _jaws = ctypes.windll.LoadLibrary("jfwapi.dll")  # noqa: F841
            return True
        except OSError:
            pass

        try:
            # Check for NVDA
            import ctypes.wintypes

            user32 = ctypes.windll.user32
            # Check if NVDA is running by looking for its window
            nvda_window = user32.FindWindowW("wxWindowClassNR", "NVDA")
            if nvda_window:
                return True
        except Exception:
            pass

    return False
