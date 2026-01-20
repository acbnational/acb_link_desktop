"""
ACB Link Desktop - App Enhancements for 1.0 Release
Performance monitoring, status indicators, quick actions, and UX improvements.
WCAG 2.2 AA compliant.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

import psutil
import wx
import wx.adv

from .accessibility import announce, make_accessible, make_button_accessible

logger = logging.getLogger(__name__)


# =============================================================================
# Performance Monitoring
# =============================================================================


@dataclass
class PerformanceMetrics:
    """Current performance metrics."""

    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    thread_count: int = 0
    response_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """Monitors application performance metrics."""

    def __init__(self, update_interval: float = 2.0):
        """
        Initialize performance monitor.

        Args:
            update_interval: Seconds between metric updates
        """
        self._interval = update_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._metrics = PerformanceMetrics()
        self._callbacks: List[Callable[[PerformanceMetrics], None]] = []
        self._process = psutil.Process()

    def start(self):
        """Start monitoring."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.debug("Performance monitor started")

    def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.debug("Performance monitor stopped")

    def add_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """Add callback for metric updates."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """Remove callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_metrics(self) -> PerformanceMetrics:
        """Get current metrics."""
        return self._metrics

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                # Get CPU usage
                cpu = self._process.cpu_percent(interval=0.1)

                # Get memory usage
                mem_info = self._process.memory_info()
                mem_mb = mem_info.rss / (1024 * 1024)
                mem_percent = self._process.memory_percent()

                # Get thread count
                threads = self._process.num_threads()

                # Update metrics
                self._metrics = PerformanceMetrics(
                    cpu_percent=cpu,
                    memory_mb=mem_mb,
                    memory_percent=mem_percent,
                    thread_count=threads,
                    timestamp=datetime.now(),
                )

                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        wx.CallAfter(callback, self._metrics)
                    except Exception:
                        pass

            except Exception as e:
                logger.debug(f"Performance monitoring error: {e}")

            time.sleep(self._interval)


# =============================================================================
# Status Indicator System
# =============================================================================


class StatusLevel(Enum):
    """Status severity levels."""

    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()
    PROGRESS = auto()


@dataclass
class StatusMessage:
    """A status message with level and optional details."""

    text: str
    level: StatusLevel = StatusLevel.INFO
    details: Optional[str] = None
    timeout_seconds: Optional[float] = 5.0
    progress: Optional[int] = None  # 0-100 for progress level
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def icon(self) -> str:
        """Get icon for status level."""
        icons = {
            StatusLevel.INFO: "ℹ️",
            StatusLevel.SUCCESS: "✓",
            StatusLevel.WARNING: "⚠️",
            StatusLevel.ERROR: "✗",
            StatusLevel.PROGRESS: "⏳",
        }
        return icons.get(self.level, "")


class StatusBar(wx.Panel):
    """Enhanced status bar with multiple zones and progress indicator."""

    def __init__(self, parent):
        super().__init__(parent)

        self._current_message: Optional[StatusMessage] = None
        self._timer = wx.Timer(self)
        self._progress_timer = wx.Timer(self)

        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        """Build status bar UI."""
        self.SetMinSize((-1, 28))

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Status icon and text
        self.status_icon = wx.StaticText(self, label="", size=(24, -1))
        sizer.Add(self.status_icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        self.status_text = wx.StaticText(self, label="Ready")
        make_accessible(self.status_text, "Status", "Current application status")
        sizer.Add(self.status_text, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        # Progress gauge (hidden by default)
        self.progress = wx.Gauge(self, range=100, size=(150, 16))
        self.progress.Hide()
        make_accessible(self.progress, "Progress", "Operation progress indicator")
        sizer.Add(self.progress, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        # Separator
        sizer.Add(wx.StaticLine(self, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 4)

        # Performance indicator (optional)
        self.perf_text = wx.StaticText(self, label="", size=(100, -1))
        self.perf_text.SetForegroundColour(wx.Colour(100, 100, 100))
        make_accessible(self.perf_text, "Performance", "Memory and CPU usage")
        sizer.Add(self.perf_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 10)

        # Connection status
        self.connection_icon = wx.StaticText(self, label="●", size=(20, -1))
        self.connection_icon.SetForegroundColour(wx.Colour(0, 180, 0))
        make_accessible(self.connection_icon, "Connection status", "Online")
        sizer.Add(self.connection_icon, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        self.SetSizer(sizer)

    def _bind_events(self):
        """Bind event handlers."""
        self.Bind(wx.EVT_TIMER, self._on_timer, self._timer)
        self.Bind(wx.EVT_TIMER, self._on_progress_timer, self._progress_timer)

    def set_status(self, message: StatusMessage):
        """Set status message."""
        self._current_message = message

        # Update UI
        self.status_icon.SetLabel(message.icon)
        self.status_text.SetLabel(message.text)

        # Set color based on level
        colors = {
            StatusLevel.INFO: wx.Colour(50, 50, 50),
            StatusLevel.SUCCESS: wx.Colour(0, 128, 0),
            StatusLevel.WARNING: wx.Colour(200, 150, 0),
            StatusLevel.ERROR: wx.Colour(200, 0, 0),
            StatusLevel.PROGRESS: wx.Colour(0, 100, 200),
        }
        self.status_text.SetForegroundColour(colors.get(message.level, wx.BLACK))

        # Handle progress
        if message.level == StatusLevel.PROGRESS and message.progress is not None:
            self.progress.SetValue(message.progress)
            self.progress.Show()
        else:
            self.progress.Hide()

        self.Layout()

        # Set timeout
        if message.timeout_seconds:
            self._timer.Start(int(message.timeout_seconds * 1000), oneShot=True)

        # Announce for screen readers
        if message.level in (StatusLevel.WARNING, StatusLevel.ERROR):
            announce(message.text)

    def set_status_text(
        self, text: str, level: StatusLevel = StatusLevel.INFO, timeout: float = 5.0
    ):
        """Convenience method to set status."""
        self.set_status(StatusMessage(text=text, level=level, timeout_seconds=timeout))

    def show_progress(self, text: str, progress: int):
        """Show progress status."""
        self.set_status(
            StatusMessage(
                text=text, level=StatusLevel.PROGRESS, progress=progress, timeout_seconds=None
            )
        )

    def hide_progress(self):
        """Hide progress indicator."""
        self.progress.Hide()
        self.Layout()

    def set_connection_status(self, online: bool):
        """Set connection status indicator."""
        if online:
            self.connection_icon.SetLabel("●")
            self.connection_icon.SetForegroundColour(wx.Colour(0, 180, 0))
            self.connection_icon.SetToolTip("Online - Connected to ACB servers")
        else:
            self.connection_icon.SetLabel("○")
            self.connection_icon.SetForegroundColour(wx.Colour(200, 0, 0))
            self.connection_icon.SetToolTip("Offline - No internet connection")

    def update_performance(self, metrics: PerformanceMetrics):
        """Update performance display."""
        text = f"Mem: {metrics.memory_mb:.0f}MB"
        self.perf_text.SetLabel(text)

    def _on_timer(self, event):
        """Handle status timeout."""
        self.status_icon.SetLabel("")
        self.status_text.SetLabel("Ready")
        self.status_text.SetForegroundColour(wx.Colour(50, 50, 50))

    def _on_progress_timer(self, event):
        """Handle progress animation."""
        pass


# =============================================================================
# Quick Actions Panel
# =============================================================================


class QuickAction:
    """Represents a quick action."""

    def __init__(
        self,
        id: str,
        label: str,
        description: str,
        icon: str,
        shortcut: Optional[str],
        callback: Callable,
    ):
        self.id = id
        self.label = label
        self.description = description
        self.icon = icon
        self.shortcut = shortcut
        self.callback = callback


class QuickActionsPanel(wx.Panel):
    """Panel showing common quick actions."""

    def __init__(self, parent, actions: List[QuickAction]):
        super().__init__(parent)

        self.actions = actions
        self._build_ui()

    def _build_ui(self):
        """Build quick actions UI."""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header = wx.StaticText(self, label="Quick Actions")
        header_font = header.GetFont()
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        sizer.Add(header, 0, wx.ALL, 5)

        # Action buttons
        btn_sizer = wx.WrapSizer(wx.HORIZONTAL)

        for action in self.actions:
            btn = wx.Button(self, label=f"{action.icon} {action.label}")
            btn.SetMinSize((120, 40))

            tooltip = action.description
            if action.shortcut:
                tooltip += f"\nShortcut: {action.shortcut}"
            btn.SetToolTip(tooltip)

            make_button_accessible(btn, action.label, action.description)
            btn.Bind(wx.EVT_BUTTON, lambda e, a=action: a.callback())

            btn_sizer.Add(btn, 0, wx.ALL, 3)

        sizer.Add(btn_sizer, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)


# =============================================================================
# Startup Optimization
# =============================================================================


class StartupOptimizer:
    """Optimizes application startup time."""

    def __init__(self):
        self._startup_time = time.time()
        self._milestones: Dict[str, float] = {}
        self._deferred_tasks: List[Callable] = []

    def mark_milestone(self, name: str):
        """Mark a startup milestone."""
        elapsed = (time.time() - self._startup_time) * 1000
        self._milestones[name] = elapsed
        logger.debug(f"Startup milestone '{name}': {elapsed:.0f}ms")

    def defer_task(self, task: Callable, delay_ms: int = 500):
        """Defer a task to run after startup."""
        self._deferred_tasks.append(task)

        def run_deferred():
            time.sleep(delay_ms / 1000)
            for t in self._deferred_tasks:
                try:
                    wx.CallAfter(t)
                except Exception as e:
                    logger.error(f"Deferred task error: {e}")
            self._deferred_tasks.clear()

        threading.Thread(target=run_deferred, daemon=True).start()

    def get_startup_report(self) -> str:
        """Get startup performance report."""
        total = (time.time() - self._startup_time) * 1000
        lines = ["Startup Performance Report:", f"Total: {total:.0f}ms"]

        sorted_milestones = sorted(self._milestones.items(), key=lambda x: x[1])
        for name, time_ms in sorted_milestones:
            lines.append(f"  {name}: {time_ms:.0f}ms")

        return "\n".join(lines)


# =============================================================================
# Lazy Loading Manager
# =============================================================================


class LazyLoader:
    """Manages lazy loading of heavy components."""

    def __init__(self):
        self._loaded: Dict[str, Any] = {}
        self._loaders: Dict[str, Callable] = {}

    def register(self, key: str, loader: Callable):
        """Register a lazy loader."""
        self._loaders[key] = loader

    def get(self, key: str) -> Any:
        """Get or load component."""
        if key not in self._loaded:
            if key not in self._loaders:
                raise KeyError(f"No loader registered for '{key}'")

            logger.debug(f"Lazy loading: {key}")
            self._loaded[key] = self._loaders[key]()

        return self._loaded[key]

    def preload(self, key: str):
        """Preload component in background."""

        def _preload():
            self.get(key)

        threading.Thread(target=_preload, daemon=True).start()

    def is_loaded(self, key: str) -> bool:
        """Check if component is loaded."""
        return key in self._loaded

    def unload(self, key: str):
        """Unload component to free memory."""
        if key in self._loaded:
            del self._loaded[key]
            logger.debug(f"Unloaded: {key}")


# =============================================================================
# Notification Center
# =============================================================================


class NotificationType(Enum):
    """Types of notifications."""

    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()
    PLAYBACK = auto()
    DOWNLOAD = auto()
    UPDATE = auto()


@dataclass
class Notification:
    """A notification message."""

    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    action_label: Optional[str] = None
    action_callback: Optional[Callable] = None
    timeout_seconds: float = 5.0
    timestamp: datetime = field(default_factory=datetime.now)


class NotificationCenter:
    """Manages application notifications."""

    _instance: Optional["NotificationCenter"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._notifications: List[Notification] = []
        self._callbacks: List[Callable[[Notification], None]] = []
        self._enabled = True
        self._initialized = True

    def notify(self, notification: Notification):
        """Send a notification."""
        if not self._enabled:
            return

        self._notifications.append(notification)

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Notification callback error: {e}")

        # Announce for accessibility
        if notification.type in (NotificationType.WARNING, NotificationType.ERROR):
            announce(f"{notification.title}: {notification.message}")

        logger.info(f"Notification: {notification.title} - {notification.message}")

    def notify_simple(
        self, title: str, message: str, type: NotificationType = NotificationType.INFO
    ):
        """Send a simple notification."""
        self.notify(Notification(title=title, message=message, type=type))

    def add_listener(self, callback: Callable[[Notification], None]):
        """Add notification listener."""
        self._callbacks.append(callback)

    def remove_listener(self, callback: Callable[[Notification], None]):
        """Remove notification listener."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def set_enabled(self, enabled: bool):
        """Enable or disable notifications."""
        self._enabled = enabled

    def get_recent(self, count: int = 10) -> List[Notification]:
        """Get recent notifications."""
        return self._notifications[-count:]

    def clear(self):
        """Clear notification history."""
        self._notifications.clear()


def get_notification_center() -> NotificationCenter:
    """Get the notification center singleton."""
    return NotificationCenter()


# =============================================================================
# Session Manager
# =============================================================================


@dataclass
class SessionInfo:
    """Information about the current session."""

    start_time: datetime = field(default_factory=datetime.now)
    streams_played: int = 0
    podcasts_played: int = 0
    total_listen_time_seconds: float = 0.0
    downloads_completed: int = 0
    searches_performed: int = 0


class SessionManager:
    """Manages session state and statistics."""

    _instance: Optional["SessionManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._session = SessionInfo()
        self._initialized = True

    @property
    def session(self) -> SessionInfo:
        """Get current session info."""
        return self._session

    def track_stream_play(self):
        """Track stream playback."""
        self._session.streams_played += 1

    def track_podcast_play(self):
        """Track podcast playback."""
        self._session.podcasts_played += 1

    def track_listen_time(self, seconds: float):
        """Track listening time."""
        self._session.total_listen_time_seconds += seconds

    def track_download(self):
        """Track completed download."""
        self._session.downloads_completed += 1

    def track_search(self):
        """Track search performed."""
        self._session.searches_performed += 1

    def get_session_duration(self) -> timedelta:
        """Get session duration."""
        return datetime.now() - self._session.start_time

    def get_session_summary(self) -> str:
        """Get session summary string."""
        duration = self.get_session_duration()
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        listen_mins = int(self._session.total_listen_time_seconds / 60)

        return (
            f"Session: {hours}h {minutes}m\n"
            f"Streams played: {self._session.streams_played}\n"
            f"Podcasts played: {self._session.podcasts_played}\n"
            f"Listen time: {listen_mins} minutes\n"
            f"Downloads: {self._session.downloads_completed}"
        )


def get_session_manager() -> SessionManager:
    """Get the session manager singleton."""
    return SessionManager()


# =============================================================================
# Keyboard Navigation Enhancement
# =============================================================================


class FocusTracker:
    """Tracks focus for enhanced keyboard navigation."""

    def __init__(self, parent: wx.Window):
        self._parent = parent
        self._focus_history: List[wx.Window] = []
        self._max_history = 20

    def track_focus(self, window: wx.Window):
        """Track focus change."""
        if window and window not in self._focus_history[-1:]:
            self._focus_history.append(window)
            if len(self._focus_history) > self._max_history:
                self._focus_history.pop(0)

    def go_back(self) -> bool:
        """Return focus to previous control."""
        if len(self._focus_history) > 1:
            self._focus_history.pop()  # Remove current
            prev = self._focus_history[-1]
            if prev.IsShown() and prev.IsEnabled():
                prev.SetFocus()
                return True
        return False

    def get_focusable_children(self, parent: wx.Window) -> List[wx.Window]:
        """Get all focusable children of a window."""
        focusable = []

        for child in parent.GetChildren():
            if self._is_focusable(child):
                focusable.append(child)
            focusable.extend(self.get_focusable_children(child))

        return focusable

    def _is_focusable(self, window: wx.Window) -> bool:
        """Check if window is focusable."""
        if not window.IsShown() or not window.IsEnabled():
            return False

        # Check for common focusable control types
        focusable_types = (
            wx.Button,
            wx.TextCtrl,
            wx.ComboBox,
            wx.Choice,
            wx.ListBox,
            wx.ListCtrl,
            wx.TreeCtrl,
            wx.CheckBox,
            wx.RadioButton,
            wx.Slider,
            wx.SpinCtrl,
            wx.Notebook,
        )

        return isinstance(window, focusable_types)


# =============================================================================
# App State Manager
# =============================================================================


class AppState(Enum):
    """Application states."""

    STARTING = auto()
    READY = auto()
    PLAYING = auto()
    RECORDING = auto()
    SYNCING = auto()
    UPDATING = auto()
    ERROR = auto()
    CLOSING = auto()


class AppStateManager:
    """Manages application state transitions."""

    _instance: Optional["AppStateManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._state = AppState.STARTING
        self._callbacks: List[Callable[[AppState, AppState], None]] = []
        self._initialized = True

    @property
    def state(self) -> AppState:
        """Get current state."""
        return self._state

    def set_state(self, new_state: AppState):
        """Set application state."""
        if new_state != self._state:
            old_state = self._state
            self._state = new_state

            # Notify listeners
            for callback in self._callbacks:
                try:
                    callback(old_state, new_state)
                except Exception as e:
                    logger.error(f"State callback error: {e}")

            logger.debug(f"App state: {old_state.name} -> {new_state.name}")

    def add_listener(self, callback: Callable[[AppState, AppState], None]):
        """Add state change listener."""
        self._callbacks.append(callback)

    def is_busy(self) -> bool:
        """Check if app is busy."""
        return self._state in (AppState.SYNCING, AppState.UPDATING, AppState.RECORDING)


def get_app_state_manager() -> AppStateManager:
    """Get the app state manager singleton."""
    return AppStateManager()


# =============================================================================
# Welcome/Onboarding Dialog
# =============================================================================


class WelcomeDialog(wx.Dialog):
    """Welcome dialog for first-time users."""

    def __init__(self, parent, version: str):
        super().__init__(
            parent,
            title=f"Welcome to ACB Link Desktop {version}",
            size=(600, 500),
            style=wx.DEFAULT_DIALOG_STYLE,
        )

        self.version = version
        self._build_ui()
        self.Centre()

    def _build_ui(self):
        """Build welcome dialog UI."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Logo/Title area
        title_sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="ACB Link Desktop")
        title_font = title.GetFont()
        title_font.SetPointSize(24)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title_sizer.Add(title, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        subtitle = wx.StaticText(panel, label=f"Version {self.version} - Your Gateway to ACB Media")
        subtitle_font = subtitle.GetFont()
        subtitle_font.SetPointSize(12)
        subtitle.SetFont(subtitle_font)
        subtitle.SetForegroundColour(wx.Colour(100, 100, 100))
        title_sizer.Add(subtitle, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        sizer.Add(title_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Features highlight
        features_box = wx.StaticBox(panel, label="What's New in Version 1.0")
        features_sizer = wx.StaticBoxSizer(features_box, wx.VERTICAL)

        features = [
            "🎵 10 live streaming channels with instant shortcuts",
            "🎧 Over 35 podcasts with download & offline playback",
            "📅 Calendar integration with event reminders",
            "🏠 Customizable home page with widgets",
            "⌨️ Full keyboard navigation and screen reader support",
            "🎤 Optional voice control for hands-free operation",
            "⏰ Sleep timer and scheduled recordings",
            "🔄 Automatic updates and data sync",
        ]

        for feature in features:
            feat_text = wx.StaticText(panel, label=feature)
            features_sizer.Add(feat_text, 0, wx.ALL, 3)

        sizer.Add(features_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Quick start tip
        tip_box = wx.StaticBox(panel, label="Quick Start")
        tip_sizer = wx.StaticBoxSizer(tip_box, wx.VERTICAL)

        tips = wx.StaticText(
            panel,
            label=(
                "• Press Alt+1 through Alt+0 to quickly play any stream\n"
                "• Press Ctrl+1 through Ctrl+9 to navigate tabs\n"
                "• Press F1 for help at any time\n"
                "• Press Ctrl+, to open Settings"
            ),
        )
        tip_sizer.Add(tips, 0, wx.ALL, 5)

        sizer.Add(tip_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Don't show again
        self.chk_dont_show = wx.CheckBox(panel, label="Don't show this again")
        make_accessible(
            self.chk_dont_show, "Don't show this again", "Skip this welcome screen on next startup"
        )
        sizer.Add(self.chk_dont_show, 0, wx.LEFT | wx.BOTTOM, 15)

        # Get started button
        btn_start = wx.Button(panel, wx.ID_OK, "Get Started!")
        btn_start.SetDefault()
        make_button_accessible(
            btn_start, "Get Started", "Close this dialog and start using ACB Link"
        )

        btn_font = btn_start.GetFont()
        btn_font.SetPointSize(12)
        btn_start.SetFont(btn_font)
        btn_start.SetMinSize((150, 40))

        sizer.Add(btn_start, 0, wx.ALIGN_CENTER | wx.ALL, 15)

        panel.SetSizer(sizer)

        announce("Welcome to ACB Link Desktop. Press Enter to get started.")

    def should_show_again(self) -> bool:
        """Check if welcome should show again."""
        return not self.chk_dont_show.GetValue()


# =============================================================================
# Memory Optimization
# =============================================================================


class MemoryOptimizer:
    """Optimizes memory usage."""

    def __init__(self, threshold_mb: float = 500):
        """
        Initialize memory optimizer.

        Args:
            threshold_mb: Memory threshold to trigger cleanup
        """
        self._threshold_mb = threshold_mb
        self._last_cleanup = time.time()
        self._cleanup_interval = 60  # seconds

    def check_and_cleanup(self) -> bool:
        """Check memory and cleanup if needed."""
        import gc

        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return False

        try:
            process = psutil.Process()
            mem_mb = process.memory_info().rss / (1024 * 1024)

            if mem_mb > self._threshold_mb:
                logger.info(f"Memory cleanup triggered at {mem_mb:.0f}MB")

                # Force garbage collection
                gc.collect()

                # Clear caches
                self._clear_caches()

                # Log result
                new_mem_mb = process.memory_info().rss / (1024 * 1024)
                freed = mem_mb - new_mem_mb
                logger.info(f"Memory cleanup freed {freed:.0f}MB")

                self._last_cleanup = current_time
                return True

        except Exception as e:
            logger.debug(f"Memory check error: {e}")

        return False

    def _clear_caches(self):
        """Clear various caches."""
        # This would clear application-specific caches
        pass

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            return psutil.Process().memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0
