"""
Announcement and notification system for ACB Link Desktop.

Provides a robust system for:
- Publishing and managing announcements (admin)
- Displaying announcements to users (widget, dialogs, native notifications)
- Tracking read/unread status
- Priority-based alerting (critical announcements trigger dialogs)
- Historical announcement viewing
- Native OS notifications (Windows/macOS)
"""

import json
import logging
import platform
import threading
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
import wx

logger = logging.getLogger(__name__)


class AnnouncementPriority(IntEnum):
    """Priority levels for announcements."""
    
    INFO = 0  # General information, lowest priority
    LOW = 1  # Minor updates, tips
    NORMAL = 2  # Standard announcements
    HIGH = 3  # Important announcements
    CRITICAL = 4  # Critical - triggers popup dialog and native notification


class AnnouncementCategory(IntEnum):
    """Categories for announcements."""
    
    GENERAL = 0  # General announcements
    UPDATE = 1  # Application updates/releases
    FEATURE = 2  # New feature announcements
    MAINTENANCE = 3  # Scheduled maintenance
    INFRASTRUCTURE = 4  # Infrastructure issues/changes
    SECURITY = 5  # Security advisories
    CONTENT = 6  # New content available
    EVENT = 7  # Upcoming events
    TIP = 8  # Tips and tricks
    COMMUNITY = 9  # Community news


PRIORITY_LABELS = {
    AnnouncementPriority.INFO: "Info",
    AnnouncementPriority.LOW: "Low",
    AnnouncementPriority.NORMAL: "Normal",
    AnnouncementPriority.HIGH: "High",
    AnnouncementPriority.CRITICAL: "Critical",
}

CATEGORY_LABELS = {
    AnnouncementCategory.GENERAL: "General",
    AnnouncementCategory.UPDATE: "Update",
    AnnouncementCategory.FEATURE: "New Feature",
    AnnouncementCategory.MAINTENANCE: "Maintenance",
    AnnouncementCategory.INFRASTRUCTURE: "Infrastructure",
    AnnouncementCategory.SECURITY: "Security",
    AnnouncementCategory.CONTENT: "New Content",
    AnnouncementCategory.EVENT: "Event",
    AnnouncementCategory.TIP: "Tip",
    AnnouncementCategory.COMMUNITY: "Community",
}

CATEGORY_ICONS = {
    AnnouncementCategory.GENERAL: "📢",
    AnnouncementCategory.UPDATE: "🔄",
    AnnouncementCategory.FEATURE: "✨",
    AnnouncementCategory.MAINTENANCE: "🔧",
    AnnouncementCategory.INFRASTRUCTURE: "🏗️",
    AnnouncementCategory.SECURITY: "🔒",
    AnnouncementCategory.CONTENT: "📚",
    AnnouncementCategory.EVENT: "📅",
    AnnouncementCategory.TIP: "💡",
    AnnouncementCategory.COMMUNITY: "👥",
}


@dataclass
class Announcement:
    """Represents a single announcement."""
    
    id: str  # Unique identifier
    title: str  # Announcement title
    summary: str  # Brief summary (shown in widget)
    content: str  # Full content (Markdown supported)
    priority: AnnouncementPriority = AnnouncementPriority.NORMAL
    category: AnnouncementCategory = AnnouncementCategory.GENERAL
    
    # Timestamps
    published_at: str = ""  # ISO format
    expires_at: Optional[str] = None  # ISO format, None = never expires
    
    # Metadata
    author: str = "ACB Link Team"
    version: Optional[str] = None  # Associated app version (for updates)
    link_url: Optional[str] = None  # Optional link for more info
    link_text: Optional[str] = None  # Text for the link
    
    # Display options
    dismissible: bool = True  # Can user dismiss/mark as read?
    requires_acknowledgment: bool = False  # Must user explicitly acknowledge?
    show_in_widget: bool = True  # Show in home widget?
    
    # Targeting (for future use)
    target_versions: Optional[List[str]] = None  # Only show to these versions
    target_platforms: Optional[List[str]] = None  # Only show on these platforms
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if not self.published_at:
            self.published_at = datetime.now().isoformat()
    
    @property
    def is_expired(self) -> bool:
        """Check if announcement has expired."""
        if not self.expires_at:
            return False
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.now() > expires
        except ValueError:
            return False
    
    @property
    def published_date(self) -> datetime:
        """Get published date as datetime object."""
        try:
            return datetime.fromisoformat(self.published_at)
        except ValueError:
            return datetime.now()
    
    @property
    def age_display(self) -> str:
        """Get human-readable age string."""
        age = datetime.now() - self.published_date
        if age.days > 365:
            years = age.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif age.days > 30:
            months = age.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif age.days > 0:
            return f"{age.days} day{'s' if age.days > 1 else ''} ago"
        elif age.seconds > 3600:
            hours = age.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif age.seconds > 60:
            minutes = age.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    @property
    def priority_label(self) -> str:
        """Get human-readable priority label."""
        return PRIORITY_LABELS.get(self.priority, "Normal")
    
    @property
    def category_label(self) -> str:
        """Get human-readable category label."""
        return CATEGORY_LABELS.get(self.category, "General")
    
    @property
    def category_icon(self) -> str:
        """Get emoji icon for category."""
        return CATEGORY_ICONS.get(self.category, "📢")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["priority"] = int(self.priority)
        data["category"] = int(self.category)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Announcement":
        """Create from dictionary."""
        data = data.copy()
        data["priority"] = AnnouncementPriority(data.get("priority", 2))
        data["category"] = AnnouncementCategory(data.get("category", 0))
        return cls(**data)


@dataclass
class AnnouncementSettings:
    """Settings for the announcement system."""
    
    # Checking behavior
    check_on_startup: bool = True
    check_interval_minutes: int = 60  # How often to check (0 = manual only)
    
    # Notification preferences
    show_native_notifications: bool = True
    show_critical_dialogs: bool = True  # Always show dialog for critical
    notification_sound: bool = True
    
    # Widget preferences
    show_widget: bool = True
    widget_max_items: int = 5
    
    # Filtering
    min_priority_for_notification: AnnouncementPriority = AnnouncementPriority.HIGH
    enabled_categories: List[int] = field(default_factory=lambda: list(range(10)))
    
    # History
    keep_history_days: int = 90  # How long to keep read announcements
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "check_on_startup": self.check_on_startup,
            "check_interval_minutes": self.check_interval_minutes,
            "show_native_notifications": self.show_native_notifications,
            "show_critical_dialogs": self.show_critical_dialogs,
            "notification_sound": self.notification_sound,
            "show_widget": self.show_widget,
            "widget_max_items": self.widget_max_items,
            "min_priority_for_notification": int(self.min_priority_for_notification),
            "enabled_categories": self.enabled_categories,
            "keep_history_days": self.keep_history_days,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnnouncementSettings":
        """Create from dictionary."""
        if not data:
            return cls()
        return cls(
            check_on_startup=data.get("check_on_startup", True),
            check_interval_minutes=data.get("check_interval_minutes", 60),
            show_native_notifications=data.get("show_native_notifications", True),
            show_critical_dialogs=data.get("show_critical_dialogs", True),
            notification_sound=data.get("notification_sound", True),
            show_widget=data.get("show_widget", True),
            widget_max_items=data.get("widget_max_items", 5),
            min_priority_for_notification=AnnouncementPriority(
                data.get("min_priority_for_notification", 3)
            ),
            enabled_categories=data.get("enabled_categories", list(range(10))),
            keep_history_days=data.get("keep_history_days", 90),
        )


class NativeNotifier:
    """Cross-platform native notification support."""
    
    def __init__(self):
        """Initialize the native notifier."""
        self.system = platform.system()
        self._initialized = False
        self._init_platform()
    
    def _init_platform(self):
        """Initialize platform-specific notification support."""
        try:
            if self.system == "Windows":
                self._init_windows()
            elif self.system == "Darwin":
                self._init_macos()
            else:
                logger.info("Native notifications not supported on this platform")
        except Exception as e:
            logger.warning(f"Failed to initialize native notifications: {e}")
    
    def _init_windows(self):
        """Initialize Windows notification support."""
        try:
            # Try Windows 10+ toast notifications
            from win10toast import ToastNotifier
            self._toaster = ToastNotifier()
            self._initialized = True
            logger.info("Windows toast notifications initialized")
        except ImportError:
            # Fallback: try plyer
            try:
                from plyer import notification
                self._plyer = notification
                self._initialized = True
                logger.info("Windows notifications via plyer initialized")
            except ImportError:
                logger.warning("No Windows notification library available")
    
    def _init_macos(self):
        """Initialize macOS notification support."""
        try:
            # Try native macOS notifications via pyobjc
            from Foundation import NSUserNotification, NSUserNotificationCenter  # type: ignore
            self._ns_notification = NSUserNotification
            self._ns_center = NSUserNotificationCenter
            self._initialized = True
            logger.info("macOS native notifications initialized")
        except ImportError:
            # Fallback: try plyer
            try:
                from plyer import notification
                self._plyer = notification
                self._initialized = True
                logger.info("macOS notifications via plyer initialized")
            except ImportError:
                # Last resort: osascript
                self._use_osascript = True
                self._initialized = True
                logger.info("macOS notifications via osascript")
    
    def notify(
        self,
        title: str,
        message: str,
        priority: AnnouncementPriority = AnnouncementPriority.NORMAL,
        timeout: int = 10,
        callback: Optional[Callable] = None,
    ) -> bool:
        """
        Show a native notification.
        
        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (affects sound/urgency)
            timeout: How long to show (seconds)
            callback: Optional callback when notification clicked
            
        Returns:
            True if notification was shown successfully
        """
        if not self._initialized:
            logger.debug("Native notifications not available")
            return False
        
        try:
            if self.system == "Windows":
                return self._notify_windows(title, message, priority, timeout)
            elif self.system == "Darwin":
                return self._notify_macos(title, message, priority, timeout)
        except Exception as e:
            logger.warning(f"Failed to show native notification: {e}")
            return False
        
        return False
    
    def _notify_windows(
        self,
        title: str,
        message: str,
        priority: AnnouncementPriority,
        timeout: int,
    ) -> bool:
        """Show Windows notification."""
        try:
            if hasattr(self, "_toaster"):
                # Use win10toast
                icon_path = None  # Could add app icon path here
                self._toaster.show_toast(
                    title,
                    message,
                    icon_path=icon_path,
                    duration=timeout,
                    threaded=True,
                )
                return True
            elif hasattr(self, "_plyer"):
                # Use plyer
                self._plyer.notify(
                    title=title,
                    message=message,
                    timeout=timeout,
                    app_name="ACB Link Desktop",
                )
                return True
        except Exception as e:
            logger.warning(f"Windows notification failed: {e}")
        return False
    
    def _notify_macos(
        self,
        title: str,
        message: str,
        priority: AnnouncementPriority,
        timeout: int,
    ) -> bool:
        """Show macOS notification."""
        try:
            if hasattr(self, "_ns_notification"):
                # Use native NSUserNotification
                notification = self._ns_notification.alloc().init()
                notification.setTitle_(title)
                notification.setInformativeText_(message)
                if priority >= AnnouncementPriority.HIGH:
                    notification.setSoundName_("default")
                center = self._ns_center.defaultUserNotificationCenter()
                center.deliverNotification_(notification)
                return True
            elif hasattr(self, "_plyer"):
                # Use plyer
                self._plyer.notify(
                    title=title,
                    message=message,
                    timeout=timeout,
                    app_name="ACB Link Desktop",
                )
                return True
            elif hasattr(self, "_use_osascript"):
                # Use osascript as fallback
                import subprocess
                script = f'''
                display notification "{message}" with title "{title}" sound name "default"
                '''
                subprocess.run(["osascript", "-e", script], capture_output=True)
                return True
        except Exception as e:
            logger.warning(f"macOS notification failed: {e}")
        return False


class AnnouncementManager:
    """
    Manages announcements for ACB Link Desktop.
    
    Responsibilities:
    - Fetching announcements from server
    - Caching announcements locally
    - Tracking read/unread status
    - Triggering notifications for new announcements
    - Managing announcement history
    """
    
    # Default announcements file URL (would be hosted on ACB server)
    DEFAULT_ANNOUNCEMENTS_URL = "https://acblink.org/announcements.json"
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the announcement manager.
        
        Args:
            data_dir: Directory for storing announcement data
        """
        if data_dir is None:
            data_dir = Path.home() / ".acb_link"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._announcements_file = self.data_dir / "announcements.json"
        self._read_status_file = self.data_dir / "announcements_read.json"
        self._settings_file = self.data_dir / "announcement_settings.json"
        
        # In-memory state
        self._announcements: List[Announcement] = []
        self._read_ids: Set[str] = set()
        self._acknowledged_ids: Set[str] = set()  # For critical announcements
        self._settings = AnnouncementSettings()
        
        # Notification support
        self._notifier = NativeNotifier()
        
        # Callbacks
        self._on_new_announcements: List[Callable[[List[Announcement]], None]] = []
        self._on_critical_announcement: List[Callable[[Announcement], None]] = []
        
        # Background checking
        self._check_thread: Optional[threading.Thread] = None
        self._stop_checking = threading.Event()
        
        # Load cached data
        self._load_data()
    
    def _load_data(self):
        """Load cached announcements and read status."""
        # Load announcements
        if self._announcements_file.exists():
            try:
                with open(self._announcements_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._announcements = [
                        Announcement.from_dict(a) for a in data.get("announcements", [])
                    ]
                    logger.info(f"Loaded {len(self._announcements)} cached announcements")
            except Exception as e:
                logger.warning(f"Failed to load cached announcements: {e}")
        
        # Load read status
        if self._read_status_file.exists():
            try:
                with open(self._read_status_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._read_ids = set(data.get("read", []))
                    self._acknowledged_ids = set(data.get("acknowledged", []))
                    logger.info(f"Loaded read status for {len(self._read_ids)} announcements")
            except Exception as e:
                logger.warning(f"Failed to load read status: {e}")
        
        # Load settings
        if self._settings_file.exists():
            try:
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._settings = AnnouncementSettings.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load announcement settings: {e}")
    
    def _save_announcements(self):
        """Save announcements to cache."""
        try:
            with open(self._announcements_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "announcements": [a.to_dict() for a in self._announcements],
                        "last_updated": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Failed to save announcements: {e}")
    
    def _save_read_status(self):
        """Save read status to file."""
        try:
            with open(self._read_status_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "read": list(self._read_ids),
                        "acknowledged": list(self._acknowledged_ids),
                        "last_updated": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Failed to save read status: {e}")
    
    def save_settings(self):
        """Save announcement settings."""
        try:
            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(self._settings.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save announcement settings: {e}")
    
    @property
    def settings(self) -> AnnouncementSettings:
        """Get current announcement settings."""
        return self._settings
    
    @settings.setter
    def settings(self, value: AnnouncementSettings):
        """Set announcement settings."""
        self._settings = value
        self.save_settings()
    
    def add_new_announcements_callback(
        self, callback: Callable[[List[Announcement]], None]
    ):
        """Add callback for when new announcements are received."""
        self._on_new_announcements.append(callback)
    
    def add_critical_announcement_callback(
        self, callback: Callable[[Announcement], None]
    ):
        """Add callback for critical announcements."""
        self._on_critical_announcement.append(callback)
    
    def get_all_announcements(
        self,
        include_expired: bool = False,
        include_read: bool = True,
    ) -> List[Announcement]:
        """
        Get all announcements.
        
        Args:
            include_expired: Include expired announcements
            include_read: Include already-read announcements
            
        Returns:
            List of announcements sorted by priority and date
        """
        announcements = []
        for a in self._announcements:
            if not include_expired and a.is_expired:
                continue
            if not include_read and a.id in self._read_ids:
                continue
            # Check category filter
            if a.category not in self._settings.enabled_categories:
                continue
            announcements.append(a)
        
        # Sort by priority (descending) then date (descending)
        announcements.sort(
            key=lambda x: (x.priority, x.published_date),
            reverse=True,
        )
        return announcements
    
    def get_unread_announcements(self) -> List[Announcement]:
        """Get all unread, non-expired announcements."""
        return self.get_all_announcements(include_expired=False, include_read=False)
    
    def get_unread_count(self) -> int:
        """Get count of unread announcements."""
        return len(self.get_unread_announcements())
    
    def get_critical_unacknowledged(self) -> List[Announcement]:
        """Get critical announcements that haven't been acknowledged."""
        critical = []
        for a in self._announcements:
            if a.is_expired:
                continue
            if a.priority == AnnouncementPriority.CRITICAL:
                if a.id not in self._acknowledged_ids:
                    critical.append(a)
        return critical
    
    def is_read(self, announcement_id: str) -> bool:
        """Check if an announcement has been read."""
        return announcement_id in self._read_ids
    
    def mark_as_read(self, announcement_id: str):
        """Mark an announcement as read."""
        self._read_ids.add(announcement_id)
        self._save_read_status()
        logger.debug(f"Marked announcement {announcement_id} as read")
    
    def mark_as_unread(self, announcement_id: str):
        """Mark an announcement as unread."""
        self._read_ids.discard(announcement_id)
        self._save_read_status()
    
    def mark_all_as_read(self):
        """Mark all announcements as read."""
        for a in self._announcements:
            self._read_ids.add(a.id)
        self._save_read_status()
        logger.info("Marked all announcements as read")
    
    def acknowledge_critical(self, announcement_id: str):
        """Acknowledge a critical announcement (won't show popup again)."""
        self._acknowledged_ids.add(announcement_id)
        self._read_ids.add(announcement_id)
        self._save_read_status()
        logger.info(f"Acknowledged critical announcement {announcement_id}")
    
    def get_announcement_by_id(self, announcement_id: str) -> Optional[Announcement]:
        """Get a specific announcement by ID."""
        for a in self._announcements:
            if a.id == announcement_id:
                return a
        return None
    
    def fetch_announcements(
        self,
        url: Optional[str] = None,
        callback: Optional[Callable[[bool, str], None]] = None,
    ):
        """
        Fetch announcements from server.
        
        Args:
            url: URL to fetch from (uses default if None)
            callback: Called with (success, message) when complete
        """
        def _fetch():
            try:
                import urllib.request
                import ssl
                
                fetch_url = url or self.DEFAULT_ANNOUNCEMENTS_URL
                
                # Create SSL context
                context = ssl.create_default_context()
                
                # Fetch announcements
                request = urllib.request.Request(
                    fetch_url,
                    headers={"User-Agent": "ACB Link Desktop/1.0"},
                )
                
                with urllib.request.urlopen(request, context=context, timeout=30) as response:
                    data = json.loads(response.read().decode("utf-8"))
                
                new_announcements = [
                    Announcement.from_dict(a) for a in data.get("announcements", [])
                ]
                
                # Find truly new announcements
                existing_ids = {a.id for a in self._announcements}
                new_items = [a for a in new_announcements if a.id not in existing_ids]
                
                # Update announcements list
                self._announcements = new_announcements
                self._save_announcements()
                
                # Process new announcements
                if new_items:
                    self._process_new_announcements(new_items)
                
                # Clean up old read status
                self._cleanup_old_status()
                
                if callback:
                    wx.CallAfter(
                        callback,
                        True,
                        f"Fetched {len(new_announcements)} announcements "
                        f"({len(new_items)} new)",
                    )
                
                logger.info(
                    f"Fetched {len(new_announcements)} announcements "
                    f"({len(new_items)} new)"
                )
                
            except Exception as e:
                logger.error(f"Failed to fetch announcements: {e}")
                if callback:
                    wx.CallAfter(callback, False, str(e))
        
        thread = threading.Thread(target=_fetch, daemon=True)
        thread.start()
    
    def _process_new_announcements(self, new_announcements: List[Announcement]):
        """Process newly received announcements."""
        # Sort by priority
        new_announcements.sort(key=lambda x: x.priority, reverse=True)
        
        # Notify callbacks
        for callback in self._on_new_announcements:
            try:
                wx.CallAfter(callback, new_announcements)
            except Exception as e:
                logger.error(f"New announcement callback failed: {e}")
        
        # Handle critical announcements
        critical = [
            a for a in new_announcements
            if a.priority == AnnouncementPriority.CRITICAL
        ]
        
        for announcement in critical:
            if self._settings.show_critical_dialogs:
                for callback in self._on_critical_announcement:
                    try:
                        wx.CallAfter(callback, announcement)
                    except Exception as e:
                        logger.error(f"Critical announcement callback failed: {e}")
        
        # Show native notifications
        if self._settings.show_native_notifications:
            for announcement in new_announcements:
                if announcement.priority >= self._settings.min_priority_for_notification:
                    self._show_native_notification(announcement)
    
    def _show_native_notification(self, announcement: Announcement):
        """Show a native OS notification for an announcement."""
        title = f"{announcement.category_icon} {announcement.title}"
        message = announcement.summary[:200]
        if len(announcement.summary) > 200:
            message += "..."
        
        self._notifier.notify(
            title=title,
            message=message,
            priority=announcement.priority,
            timeout=10 if announcement.priority < AnnouncementPriority.CRITICAL else 30,
        )
    
    def _cleanup_old_status(self):
        """Remove read status for announcements older than retention period."""
        cutoff = datetime.now() - timedelta(days=self._settings.keep_history_days)
        current_ids = {a.id for a in self._announcements}
        
        # Also keep status for announcements published within retention period
        valid_ids = set()
        for a in self._announcements:
            if a.published_date > cutoff:
                valid_ids.add(a.id)
        
        # Clean up read IDs
        self._read_ids = self._read_ids.intersection(current_ids | valid_ids)
        self._acknowledged_ids = self._acknowledged_ids.intersection(current_ids | valid_ids)
        self._save_read_status()
    
    def start_background_checking(self):
        """Start background checking for new announcements."""
        if self._check_thread is not None:
            return
        
        if self._settings.check_interval_minutes <= 0:
            logger.info("Background announcement checking disabled")
            return
        
        self._stop_checking.clear()
        self._check_thread = threading.Thread(
            target=self._background_check_loop,
            daemon=True,
        )
        self._check_thread.start()
        logger.info(
            f"Started background announcement checking "
            f"(interval: {self._settings.check_interval_minutes} min)"
        )
    
    def stop_background_checking(self):
        """Stop background checking."""
        if self._check_thread is None:
            return
        
        self._stop_checking.set()
        self._check_thread = None
        logger.info("Stopped background announcement checking")
    
    def _background_check_loop(self):
        """Background loop for checking announcements."""
        interval_seconds = self._settings.check_interval_minutes * 60
        
        while not self._stop_checking.wait(timeout=interval_seconds):
            if self._stop_checking.is_set():
                break
            
            logger.debug("Background check for new announcements")
            self.fetch_announcements()
    
    # Admin functions for publishing announcements
    
    def create_announcement(
        self,
        title: str,
        summary: str,
        content: str,
        priority: AnnouncementPriority = AnnouncementPriority.NORMAL,
        category: AnnouncementCategory = AnnouncementCategory.GENERAL,
        **kwargs,
    ) -> Announcement:
        """
        Create a new announcement (admin function).
        
        Args:
            title: Announcement title
            summary: Brief summary
            content: Full content (Markdown)
            priority: Priority level
            category: Category
            **kwargs: Additional announcement fields
            
        Returns:
            The created announcement
        """
        announcement = Announcement(
            id=str(uuid.uuid4()),
            title=title,
            summary=summary,
            content=content,
            priority=priority,
            category=category,
            published_at=datetime.now().isoformat(),
            **kwargs,
        )
        return announcement
    
    def publish_announcement(self, announcement: Announcement) -> bool:
        """
        Publish an announcement locally (for testing/admin).
        
        In production, announcements would be published to the server.
        This method adds it locally for immediate effect.
        
        Args:
            announcement: The announcement to publish
            
        Returns:
            True if published successfully
        """
        # Check if already exists
        for i, existing in enumerate(self._announcements):
            if existing.id == announcement.id:
                self._announcements[i] = announcement
                self._save_announcements()
                logger.info(f"Updated announcement: {announcement.title}")
                return True
        
        # Add new
        self._announcements.insert(0, announcement)
        self._save_announcements()
        
        # Process as new
        self._process_new_announcements([announcement])
        
        logger.info(f"Published announcement: {announcement.title}")
        return True
    
    def delete_announcement(self, announcement_id: str) -> bool:
        """
        Delete an announcement (admin function).
        
        Args:
            announcement_id: ID of announcement to delete
            
        Returns:
            True if deleted successfully
        """
        for i, a in enumerate(self._announcements):
            if a.id == announcement_id:
                del self._announcements[i]
                self._save_announcements()
                
                # Clean up read status
                self._read_ids.discard(announcement_id)
                self._acknowledged_ids.discard(announcement_id)
                self._save_read_status()
                
                logger.info(f"Deleted announcement: {announcement_id}")
                return True
        
        return False
    
    def export_announcements_json(self) -> str:
        """
        Export announcements as JSON (for server upload).
        
        Returns:
            JSON string of all announcements
        """
        return json.dumps(
            {
                "announcements": [a.to_dict() for a in self._announcements],
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
            },
            indent=2,
        )
    
    def import_announcements_json(self, json_str: str) -> int:
        """
        Import announcements from JSON.
        
        Args:
            json_str: JSON string containing announcements
            
        Returns:
            Number of announcements imported
        """
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        announcements = [
            Announcement.from_dict(a) for a in data.get("announcements", [])
        ]
        self._announcements = announcements
        self._save_announcements()
        return len(announcements)


# Global instance
_announcement_manager: Optional[AnnouncementManager] = None


def get_announcement_manager() -> AnnouncementManager:
    """Get the global announcement manager instance."""
    global _announcement_manager
    if _announcement_manager is None:
        _announcement_manager = AnnouncementManager()
    return _announcement_manager


def initialize_announcement_manager(data_dir: Optional[Path] = None) -> AnnouncementManager:
    """Initialize the global announcement manager."""
    global _announcement_manager
    _announcement_manager = AnnouncementManager(data_dir)
    return _announcement_manager
