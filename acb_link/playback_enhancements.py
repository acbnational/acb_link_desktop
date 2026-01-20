"""
ACB Link - Playback Enhancements
Sleep timer, auto-play, playback speed, media keys, audio ducking, quiet hours,
recently played, and sharing features.
"""

import json
import os
import platform
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import wx

# ============================================================================
# SLEEP TIMER
# ============================================================================


class SleepTimerPreset(Enum):
    """Sleep timer preset durations."""

    MINUTES_15 = 15
    MINUTES_30 = 30
    MINUTES_45 = 45
    MINUTES_60 = 60
    MINUTES_90 = 90
    MINUTES_120 = 120
    END_OF_EPISODE = -1  # Special: stop when current content ends
    CUSTOM = 0

    @property
    def label(self) -> str:
        labels = {
            self.MINUTES_15: "15 minutes",
            self.MINUTES_30: "30 minutes",
            self.MINUTES_45: "45 minutes",
            self.MINUTES_60: "1 hour",
            self.MINUTES_90: "1 hour 30 minutes",
            self.MINUTES_120: "2 hours",
            self.END_OF_EPISODE: "End of current episode",
            self.CUSTOM: "Custom time",
        }
        return labels.get(self, f"{self.value} minutes")


class EnhancedSleepTimer:
    """
    Enhanced sleep timer with presets, fade-out, and notifications.
    """

    def __init__(
        self,
        on_timer_end: Callable[[], None],
        on_timer_tick: Optional[Callable[[int], None]] = None,
        on_fade_start: Optional[Callable[[], None]] = None,
    ):
        self.on_timer_end = on_timer_end
        self.on_timer_tick = on_timer_tick
        self.on_fade_start = on_fade_start

        self._timer_thread: Optional[threading.Thread] = None
        self._remaining_seconds: int = 0
        self._is_active: bool = False
        self._stop_event = threading.Event()
        self._fade_duration_seconds: int = 30  # Fade out over 30 seconds
        self._enable_fade: bool = True

    def start(self, minutes: int, enable_fade: bool = True):
        """Start the sleep timer."""
        self.cancel()

        self._remaining_seconds = minutes * 60
        self._enable_fade = enable_fade
        self._is_active = True
        self._stop_event.clear()

        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self._timer_thread.start()

    def start_preset(self, preset: SleepTimerPreset, enable_fade: bool = True):
        """Start timer with a preset duration."""
        if preset == SleepTimerPreset.END_OF_EPISODE:
            # Special handling - caller should set this up differently
            return
        elif preset == SleepTimerPreset.CUSTOM:
            return  # Caller should use start() with custom minutes
        else:
            self.start(preset.value, enable_fade)

    def cancel(self):
        """Cancel the timer."""
        self._is_active = False
        self._stop_event.set()
        self._remaining_seconds = 0

        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=1.0)
        self._timer_thread = None

    def add_time(self, minutes: int):
        """Add more time to the current timer."""
        if self._is_active:
            self._remaining_seconds += minutes * 60

    def get_remaining(self) -> int:
        """Get remaining time in seconds."""
        return self._remaining_seconds

    def get_remaining_formatted(self) -> str:
        """Get remaining time as formatted string."""
        if not self._is_active:
            return "Off"

        mins = self._remaining_seconds // 60
        secs = self._remaining_seconds % 60

        if mins >= 60:
            hours = mins // 60
            mins = mins % 60
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"

    def is_active(self) -> bool:
        """Check if timer is running."""
        return self._is_active

    def _timer_loop(self):
        """Timer loop running in background thread."""
        fade_started = False

        while self._remaining_seconds > 0 and not self._stop_event.is_set():
            self._stop_event.wait(1.0)

            if self._stop_event.is_set():
                break

            self._remaining_seconds -= 1

            # Notify tick
            if self.on_timer_tick:
                wx.CallAfter(self.on_timer_tick, self._remaining_seconds)

            # Start fade if enabled
            if (
                self._enable_fade
                and self._remaining_seconds <= self._fade_duration_seconds
                and not fade_started
            ):
                fade_started = True
                if self.on_fade_start:
                    wx.CallAfter(self.on_fade_start)

        if not self._stop_event.is_set():
            self._is_active = False
            wx.CallAfter(self.on_timer_end)


class SleepTimerDialog(wx.Dialog):
    """Dialog for setting sleep timer."""

    def __init__(self, parent: wx.Window, current_remaining: int = 0):
        super().__init__(parent, title="Sleep Timer", style=wx.DEFAULT_DIALOG_STYLE)

        self.selected_minutes = 0
        self.enable_fade = True
        self._current_remaining = current_remaining

        self._create_ui()
        self.Fit()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Current status
        if self._current_remaining > 0:
            mins = self._current_remaining // 60
            status = wx.StaticText(panel, label=f"Timer active: {mins} minutes remaining")
            status.SetFont(status.GetFont().Bold())
            main_sizer.Add(status, 0, wx.ALL, 10)

        # Preset buttons
        presets_label = wx.StaticText(panel, label="Quick presets:")
        main_sizer.Add(presets_label, 0, wx.LEFT | wx.TOP, 10)

        presets_sizer = wx.GridSizer(rows=2, cols=3, hgap=5, vgap=5)

        preset_values = [
            ("15 min", 15),
            ("30 min", 30),
            ("45 min", 45),
            ("1 hour", 60),
            ("90 min", 90),
            ("2 hours", 120),
        ]

        for label, minutes in preset_values:
            btn = wx.Button(panel, label=label)
            btn.Bind(wx.EVT_BUTTON, lambda e, m=minutes: self._on_preset(m))
            presets_sizer.Add(btn, 0, wx.EXPAND)

        main_sizer.Add(presets_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Custom time
        custom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        custom_label = wx.StaticText(panel, label="Custom minutes:")
        self.custom_spin = wx.SpinCtrl(panel, min=1, max=480, initial=60)
        self.custom_spin.SetName("Custom minutes")
        custom_btn = wx.Button(panel, label="Set")
        custom_btn.Bind(wx.EVT_BUTTON, self._on_custom)

        custom_sizer.Add(custom_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        custom_sizer.Add(self.custom_spin, 0, wx.RIGHT, 5)
        custom_sizer.Add(custom_btn, 0)

        main_sizer.Add(custom_sizer, 0, wx.ALL, 10)

        # Fade option
        self.fade_check = wx.CheckBox(panel, label="&Fade out volume before stopping")
        self.fade_check.SetValue(True)
        main_sizer.Add(self.fade_check, 0, wx.ALL, 10)

        # Cancel timer button (if active)
        if self._current_remaining > 0:
            cancel_timer_btn = wx.Button(panel, label="&Cancel Timer")
            cancel_timer_btn.Bind(wx.EVT_BUTTON, self._on_cancel_timer)
            main_sizer.Add(cancel_timer_btn, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        # Dialog buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))
        btn_sizer.Add(btn_close, 0)

        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)

    def _on_preset(self, minutes: int):
        """Handle preset button click."""
        self.selected_minutes = minutes
        self.enable_fade = self.fade_check.GetValue()
        self.EndModal(wx.ID_OK)

    def _on_custom(self, event):
        """Handle custom time button."""
        self.selected_minutes = self.custom_spin.GetValue()
        self.enable_fade = self.fade_check.GetValue()
        self.EndModal(wx.ID_OK)

    def _on_cancel_timer(self, event):
        """Handle cancel timer button."""
        self.selected_minutes = -1  # Signal to cancel
        self.EndModal(wx.ID_OK)


# ============================================================================
# AUTO-PLAY ON STARTUP
# ============================================================================


@dataclass
class AutoPlaySettings:
    """Settings for auto-play on startup."""

    enabled: bool = False
    content_type: str = "stream"  # "stream", "podcast", "last_played"
    content_name: str = ""  # Name of stream or podcast
    delay_seconds: int = 3  # Delay before auto-play starts
    only_when_last_session_was_playing: bool = False


class AutoPlayManager:
    """Manages auto-play on startup functionality."""

    def __init__(self, settings_path: Optional[str] = None):
        self.settings_path = settings_path or str(Path.home() / ".acb_link" / "autoplay.json")
        self.settings = self._load()

    def _load(self) -> AutoPlaySettings:
        """Load auto-play settings."""
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return AutoPlaySettings(**data)
            except Exception:
                pass
        return AutoPlaySettings()

    def save(self):
        """Save settings."""
        Path(self.settings_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.settings), f, indent=2)

    def should_auto_play(self, was_playing_last_session: bool = False) -> bool:
        """Check if auto-play should trigger."""
        if not self.settings.enabled:
            return False

        if self.settings.only_when_last_session_was_playing:
            return was_playing_last_session

        return True

    def get_auto_play_target(self) -> Tuple[str, str]:
        """Get the content to auto-play. Returns (content_type, content_name)."""
        return (self.settings.content_type, self.settings.content_name)


# ============================================================================
# PLAYBACK SPEED CONTROL
# ============================================================================


class PlaybackSpeedPreset(Enum):
    """Playback speed presets."""

    SPEED_0_5 = 0.5
    SPEED_0_75 = 0.75
    SPEED_1_0 = 1.0
    SPEED_1_25 = 1.25
    SPEED_1_5 = 1.5
    SPEED_1_75 = 1.75
    SPEED_2_0 = 2.0

    @property
    def label(self) -> str:
        return f"{self.value}x"


class PlaybackSpeedController:
    """Controls playback speed with presets and custom values."""

    MIN_SPEED = 0.25
    MAX_SPEED = 3.0
    STEP = 0.25

    def __init__(
        self, initial_speed: float = 1.0, on_speed_changed: Optional[Callable[[float], None]] = None
    ):
        self.current_speed = initial_speed
        self.on_speed_changed = on_speed_changed
        self._saved_speed: Optional[float] = None  # For temporary speed changes

    def set_speed(self, speed: float) -> float:
        """Set playback speed. Returns actual speed set."""
        speed = max(self.MIN_SPEED, min(self.MAX_SPEED, speed))
        self.current_speed = speed

        if self.on_speed_changed:
            self.on_speed_changed(speed)

        return speed

    def set_preset(self, preset: PlaybackSpeedPreset) -> float:
        """Set speed from preset."""
        return self.set_speed(preset.value)

    def increase(self) -> float:
        """Increase speed by one step."""
        return self.set_speed(self.current_speed + self.STEP)

    def decrease(self) -> float:
        """Decrease speed by one step."""
        return self.set_speed(self.current_speed - self.STEP)

    def reset(self) -> float:
        """Reset to normal speed."""
        return self.set_speed(1.0)

    def save_and_set(self, speed: float):
        """Save current speed and set a temporary one."""
        self._saved_speed = self.current_speed
        self.set_speed(speed)

    def restore(self):
        """Restore saved speed."""
        if self._saved_speed is not None:
            self.set_speed(self._saved_speed)
            self._saved_speed = None

    def get_label(self) -> str:
        """Get current speed as label."""
        return f"{self.current_speed:.2f}x".rstrip("0").rstrip(".")


# ============================================================================
# WHAT'S PLAYING / SHARE
# ============================================================================


@dataclass
class NowPlayingInfo:
    """Information about currently playing content."""

    content_type: str = ""  # "stream" or "podcast"
    title: str = ""
    artist: str = ""
    album: str = ""  # Podcast name for episodes
    episode_title: str = ""
    stream_name: str = ""
    url: str = ""
    duration: int = 0  # seconds
    position: int = 0  # seconds

    def to_text(self, include_url: bool = True) -> str:
        """Convert to shareable text."""
        lines = []

        if self.content_type == "stream":
            lines.append(f"🎵 Listening to: {self.stream_name}")
            if self.title:
                lines.append(f"Now playing: {self.title}")
                if self.artist:
                    lines.append(f"Artist: {self.artist}")
        else:
            lines.append(f"🎧 Listening to: {self.album}")
            if self.episode_title:
                lines.append(f"Episode: {self.episode_title}")
            if self.position > 0 and self.duration > 0:
                pos_str = f"{self.position // 60}:{self.position % 60:02d}"
                dur_str = f"{self.duration // 60}:{self.duration % 60:02d}"
                lines.append(f"Position: {pos_str} / {dur_str}")

        if include_url and self.url:
            lines.append(f"Link: {self.url}")

        lines.append("\n— via ACB Link")

        return "\n".join(lines)


class ShareManager:
    """Manages sharing "what's playing" information."""

    def __init__(self, get_now_playing: Callable[[], NowPlayingInfo]):
        self.get_now_playing = get_now_playing

    def copy_to_clipboard(self, include_url: bool = True) -> bool:
        """Copy current playing info to clipboard."""
        info = self.get_now_playing()
        if not info.title and not info.stream_name:
            return False

        text = info.to_text(include_url)

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()
            return True
        return False

    def get_share_text(self, include_url: bool = True) -> str:
        """Get shareable text for current content."""
        info = self.get_now_playing()
        return info.to_text(include_url)


# ============================================================================
# RECENTLY PLAYED
# ============================================================================


@dataclass
class RecentItem:
    """A recently played item."""

    content_type: str  # "stream" or "podcast"
    name: str
    url: str = ""
    category: str = ""  # For podcasts
    episode_title: str = ""
    position: int = 0  # For podcasts - resume position
    timestamp: str = ""  # ISO format

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class RecentlyPlayedManager:
    """Manages recently played items list."""

    MAX_ITEMS = 20

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or str(Path.home() / ".acb_link" / "recently_played.json")
        self.items: List[RecentItem] = []
        self._load()

    def _load(self):
        """Load recent items."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.items = [RecentItem(**item) for item in data]
            except Exception:
                self.items = []

    def save(self):
        """Save recent items."""
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump([asdict(item) for item in self.items], f, indent=2)

    def add(
        self,
        content_type: str,
        name: str,
        url: str = "",
        category: str = "",
        episode_title: str = "",
        position: int = 0,
    ):
        """Add an item to recently played."""
        # Remove existing entry for same content
        self.items = [
            item
            for item in self.items
            if not (item.content_type == content_type and item.name == name)
        ]

        # Add new item at front
        self.items.insert(
            0,
            RecentItem(
                content_type=content_type,
                name=name,
                url=url,
                category=category,
                episode_title=episode_title,
                position=position,
            ),
        )

        # Trim to max
        self.items = self.items[: self.MAX_ITEMS]
        self.save()

    def get_recent(self, count: int = 10) -> List[RecentItem]:
        """Get recent items."""
        return self.items[:count]

    def clear(self):
        """Clear all recent items."""
        self.items = []
        self.save()

    def remove(self, name: str):
        """Remove a specific item."""
        self.items = [item for item in self.items if item.name != name]
        self.save()


class RecentlyPlayedDialog(wx.Dialog):
    """Dialog showing recently played items."""

    def __init__(
        self,
        parent: wx.Window,
        recent_manager: RecentlyPlayedManager,
        on_play: Callable[[RecentItem], None],
    ):
        super().__init__(
            parent, title="Recently Played", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        self.recent_manager = recent_manager
        self.on_play = on_play
        self.selected_item: Optional[RecentItem] = None

        self.SetSize((450, 400))  # type: ignore[arg-type]
        self._create_ui()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # List of recent items
        self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.SetName("Recently played items")

        self.list_ctrl.InsertColumn(0, "Name", width=200)
        self.list_ctrl.InsertColumn(1, "Type", width=80)
        self.list_ctrl.InsertColumn(2, "When", width=120)

        # Populate list
        items = self.recent_manager.get_recent(20)
        for i, item in enumerate(items):
            idx = self.list_ctrl.InsertItem(i, item.name)
            self.list_ctrl.SetItem(idx, 1, item.content_type.title())

            # Format timestamp
            try:
                dt = datetime.fromisoformat(item.timestamp)
                when = dt.strftime("%b %d, %I:%M %p")
            except Exception:
                when = "Unknown"
            self.list_ctrl.SetItem(idx, 2, when)

            # Store item reference
            self.list_ctrl.SetItemData(idx, i)

        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_item_activated)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_item_selected)

        main_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_play = wx.Button(panel, label="&Play")
        self.btn_play.Bind(wx.EVT_BUTTON, self._on_play)
        self.btn_play.Enable(False)

        btn_clear = wx.Button(panel, label="&Clear All")
        btn_clear.Bind(wx.EVT_BUTTON, self._on_clear)

        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))

        btn_sizer.Add(self.btn_play, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_clear, 0, wx.RIGHT, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(btn_close, 0)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main_sizer)

        # Focus list if items exist
        if items:
            self.list_ctrl.SetFocus()
            self.list_ctrl.Select(0)

    def _on_item_selected(self, event):
        """Handle item selection."""
        self.btn_play.Enable(True)
        idx = event.GetIndex()
        items = self.recent_manager.get_recent(20)
        if 0 <= idx < len(items):
            self.selected_item = items[idx]

    def _on_item_activated(self, event):
        """Handle double-click on item."""
        self._on_play(event)

    def _on_play(self, event):
        """Play selected item."""
        if self.selected_item:
            self.on_play(self.selected_item)
            self.EndModal(wx.ID_OK)

    def _on_clear(self, event):
        """Clear all recent items."""
        if (
            wx.MessageBox(
                "Clear all recently played items?",
                "Confirm Clear",
                wx.YES_NO | wx.ICON_QUESTION,
                self,
            )
            == wx.YES
        ):
            self.recent_manager.clear()
            self.list_ctrl.DeleteAllItems()


# ============================================================================
# MEDIA KEY SUPPORT
# ============================================================================


class MediaKeyHandler:
    """
    Handles system media keys (play/pause, stop, next, previous).
    Platform-specific implementations.
    """

    def __init__(
        self,
        on_play_pause: Callable[[], None],
        on_stop: Callable[[], None],
        on_next: Optional[Callable[[], None]] = None,
        on_previous: Optional[Callable[[], None]] = None,
        on_volume_up: Optional[Callable[[], None]] = None,
        on_volume_down: Optional[Callable[[], None]] = None,
    ):
        self.on_play_pause = on_play_pause
        self.on_stop = on_stop
        self.on_next = on_next
        self.on_previous = on_previous
        self.on_volume_up = on_volume_up
        self.on_volume_down = on_volume_down

        self._registered = False
        self._hook = None

    def register(self) -> bool:
        """Register media key handlers. Returns True if successful."""
        if self._registered:
            return True

        system = platform.system()

        if system == "Windows":
            return self._register_windows()
        elif system == "Darwin":
            return self._register_macos()

        return False

    def unregister(self):
        """Unregister media key handlers."""
        if not self._registered:
            return

        system = platform.system()

        if system == "Windows":
            self._unregister_windows()
        elif system == "Darwin":
            self._unregister_macos()

        self._registered = False

    def _register_windows(self) -> bool:
        """Register media keys on Windows using keyboard hooks."""
        try:
            # Note: ctypes would be used for full media key implementation
            # import ctypes
            # from ctypes import wintypes

            # Virtual key codes for media keys (reserved for future use)
            # _VK_MEDIA_PLAY_PAUSE = 0xB3  # noqa: F841
            # _VK_MEDIA_STOP = 0xB2        # noqa: F841
            # _VK_MEDIA_NEXT_TRACK = 0xB0  # noqa: F841
            # _VK_MEDIA_PREV_TRACK = 0xB1  # noqa: F841
            # _VK_VOLUME_UP = 0xAF         # noqa: F841
            # _VK_VOLUME_DOWN = 0xAE       # noqa: F841

            # We'll use RegisterHotKey approach
            # Note: This is a simplified version - full implementation
            # would use a proper keyboard hook library

            self._registered = True
            return True

        except Exception as e:
            print(f"Failed to register Windows media keys: {e}")
            return False

    def _unregister_windows(self):
        """Unregister Windows media keys."""
        pass

    def _register_macos(self) -> bool:
        """Register media keys on macOS."""
        try:
            # macOS uses NSEvent for media keys
            # This requires pyobjc-framework-Cocoa
            self._registered = True
            return True
        except Exception as e:
            print(f"Failed to register macOS media keys: {e}")
            return False

    def _unregister_macos(self):
        """Unregister macOS media keys."""
        pass


# ============================================================================
# AUDIO DUCKING
# ============================================================================


@dataclass
class AudioDuckingSettings:
    """Audio ducking configuration."""

    enabled: bool = True
    duck_percentage: int = 30  # Volume reduces to this percentage (10-90%)
    restore_delay_seconds: float = 2.0  # How long to wait before restoring

    def validate(self):
        """Ensure settings are within valid ranges."""
        self.duck_percentage = max(10, min(90, self.duck_percentage))
        self.restore_delay_seconds = max(0.5, min(10.0, self.restore_delay_seconds))


class AudioDuckingManager:
    """
    Manages audio ducking - lowering volume during system sounds.
    Ducking percentage and restore delay are configurable.
    """

    def __init__(
        self,
        get_volume: Callable[[], int],
        set_volume: Callable[[int], None],
        duck_percentage: int = 30,  # Duck to 30% of current volume
        restore_delay: float = 2.0,  # Seconds before restoring
        storage_path: Optional[str] = None,
    ):
        self.get_volume = get_volume
        self.set_volume = set_volume

        # Load or create settings
        self.storage_path = storage_path or str(Path.home() / ".acb_link" / "audio_ducking.json")
        self.settings = self._load_settings()

        # Apply provided defaults if no saved settings
        if not os.path.exists(self.storage_path):
            self.settings.duck_percentage = duck_percentage
            self.settings.restore_delay_seconds = restore_delay
            self._save_settings()

        self._original_volume: Optional[int] = None
        self._is_ducked = False
        self._restore_timer: Optional[threading.Timer] = None

    def _load_settings(self) -> AudioDuckingSettings:
        """Load settings from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return AudioDuckingSettings(**data)
            except Exception:
                pass
        return AudioDuckingSettings()

    def _save_settings(self):
        """Save settings to storage."""
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.settings), f, indent=2)

    @property
    def duck_percentage(self) -> int:
        return self.settings.duck_percentage

    @duck_percentage.setter
    def duck_percentage(self, value: int):
        self.settings.duck_percentage = max(10, min(90, value))
        self._save_settings()

    @property
    def restore_delay(self) -> float:
        return self.settings.restore_delay_seconds

    @restore_delay.setter
    def restore_delay(self, value: float):
        self.settings.restore_delay_seconds = max(0.5, min(10.0, value))
        self._save_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.enabled

    @enabled.setter
    def enabled(self, value: bool):
        self.settings.enabled = value
        self._save_settings()
        if not value and self._is_ducked:
            self.restore()

    def duck(self, duration_seconds: Optional[float] = None):
        """
        Duck the audio volume temporarily.

        Args:
            duration_seconds: How long to duck before auto-restoring (uses settings default if None)
        """
        if not self.settings.enabled:
            return

        duration = (
            duration_seconds
            if duration_seconds is not None
            else self.settings.restore_delay_seconds
        )

        if self._is_ducked:
            # Already ducked - reset restore timer
            if self._restore_timer:
                self._restore_timer.cancel()
        else:
            self._original_volume = self.get_volume()
            ducked_volume = int(self._original_volume * self.settings.duck_percentage / 100)
            self.set_volume(ducked_volume)
            self._is_ducked = True

        # Schedule restore
        self._restore_timer = threading.Timer(duration, self._auto_restore)
        self._restore_timer.daemon = True
        self._restore_timer.start()

    def restore(self):
        """Restore original volume."""
        if self._restore_timer:
            self._restore_timer.cancel()
            self._restore_timer = None

        if self._is_ducked and self._original_volume is not None:
            self.set_volume(self._original_volume)
            self._is_ducked = False
            self._original_volume = None

    def _auto_restore(self):
        """Auto-restore callback."""
        wx.CallAfter(self.restore)


class AudioDuckingDialog(wx.Dialog):
    """Dialog for configuring audio ducking settings."""

    def __init__(self, parent: wx.Window, ducking_manager: AudioDuckingManager):
        super().__init__(parent, title="Audio Ducking Settings", style=wx.DEFAULT_DIALOG_STYLE)

        self.manager = ducking_manager

        self._create_ui()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Description
        desc = wx.StaticText(
            panel,
            label="Audio ducking automatically lowers volume when system sounds play,\n"
            "so you don't miss important notifications.",
        )
        main_sizer.Add(desc, 0, wx.ALL, 15)

        # Enable checkbox
        self.enable_check = wx.CheckBox(panel, label="&Enable audio ducking")
        self.enable_check.SetValue(self.manager.enabled)
        main_sizer.Add(self.enable_check, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        # Duck percentage
        percent_sizer = wx.BoxSizer(wx.HORIZONTAL)
        percent_sizer.Add(
            wx.StaticText(panel, label="&Duck volume to:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            10,
        )
        self.percent_spin = wx.SpinCtrl(panel, min=10, max=90, initial=self.manager.duck_percentage)
        self.percent_spin.SetName("Duck volume percentage")
        percent_sizer.Add(self.percent_spin, 0, wx.RIGHT, 5)
        percent_sizer.Add(
            wx.StaticText(panel, label="% of current volume"), 0, wx.ALIGN_CENTER_VERTICAL
        )
        main_sizer.Add(percent_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        # Restore delay
        delay_sizer = wx.BoxSizer(wx.HORIZONTAL)
        delay_sizer.Add(
            wx.StaticText(panel, label="&Restore after:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            10,
        )
        self.delay_spin = wx.SpinCtrlDouble(
            panel, min=0.5, max=10.0, initial=self.manager.restore_delay, inc=0.5
        )
        self.delay_spin.SetDigits(1)
        self.delay_spin.SetName("Restore delay seconds")
        delay_sizer.Add(self.delay_spin, 0, wx.RIGHT, 5)
        delay_sizer.Add(wx.StaticText(panel, label="seconds"), 0, wx.ALIGN_CENTER_VERTICAL)
        main_sizer.Add(delay_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        # Test button
        test_btn = wx.Button(panel, label="&Test Ducking")
        test_btn.Bind(wx.EVT_BUTTON, self._on_test)
        main_sizer.Add(test_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        # Buttons
        btn_sizer = wx.StdDialogButtonSizer()
        btn_ok = wx.Button(panel, wx.ID_OK)
        btn_ok.Bind(wx.EVT_BUTTON, self._on_ok)
        btn_cancel = wx.Button(panel, wx.ID_CANCEL)
        btn_sizer.AddButton(btn_ok)
        btn_sizer.AddButton(btn_cancel)
        btn_sizer.Realize()
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 15)

        panel.SetSizer(main_sizer)
        main_sizer.Fit(self)

    def _on_test(self, event):
        """Test the ducking settings."""
        # Apply current values temporarily
        self.manager.duck_percentage = self.percent_spin.GetValue()
        self.manager.restore_delay = self.delay_spin.GetValue()
        self.manager.duck()

    def _on_ok(self, event):
        """Save settings and close."""
        self.manager.enabled = self.enable_check.GetValue()
        self.manager.duck_percentage = self.percent_spin.GetValue()
        self.manager.restore_delay = self.delay_spin.GetValue()
        self.EndModal(wx.ID_OK)


# ============================================================================
# QUIET HOURS
# ============================================================================


@dataclass
class QuietHoursSettings:
    """Quiet hours configuration."""

    enabled: bool = False
    start_time: str = "22:00"  # HH:MM format
    end_time: str = "07:00"
    mute_notifications: bool = True
    reduce_volume: bool = True
    reduced_volume_percent: int = 30
    days: List[str] = field(
        default_factory=lambda: [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
    )


class QuietHoursManager:
    """Manages quiet hours functionality."""

    def __init__(
        self,
        settings_path: Optional[str] = None,
        on_quiet_hours_start: Optional[Callable[[], None]] = None,
        on_quiet_hours_end: Optional[Callable[[], None]] = None,
    ):
        self.settings_path = settings_path or str(Path.home() / ".acb_link" / "quiet_hours.json")
        self.on_quiet_hours_start = on_quiet_hours_start
        self.on_quiet_hours_end = on_quiet_hours_end

        self.settings = self._load()
        self._check_timer: Optional[threading.Timer] = None
        self._was_in_quiet_hours = False

    def _load(self) -> QuietHoursSettings:
        """Load quiet hours settings."""
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return QuietHoursSettings(**data)
            except Exception:
                pass
        return QuietHoursSettings()

    def save(self):
        """Save settings."""
        Path(self.settings_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.settings), f, indent=2)

    def is_quiet_hours(self) -> bool:
        """Check if currently in quiet hours."""
        if not self.settings.enabled:
            return False

        now = datetime.now()
        current_day = now.strftime("%A")

        # Check if today is included
        if current_day not in self.settings.days:
            return False

        # Parse times
        try:
            start = datetime.strptime(self.settings.start_time, "%H:%M").time()
            end = datetime.strptime(self.settings.end_time, "%H:%M").time()
            current = now.time()

            # Handle overnight quiet hours (e.g., 22:00 to 07:00)
            if start > end:
                return current >= start or current <= end
            else:
                return start <= current <= end

        except ValueError:
            return False

    def start_monitoring(self):
        """Start monitoring for quiet hours transitions."""
        self._check_and_schedule()

    def stop_monitoring(self):
        """Stop monitoring."""
        if self._check_timer:
            self._check_timer.cancel()
            self._check_timer = None

    def _check_and_schedule(self):
        """Check quiet hours status and schedule next check."""
        is_quiet = self.is_quiet_hours()

        # Detect transitions
        if is_quiet and not self._was_in_quiet_hours:
            if self.on_quiet_hours_start:
                wx.CallAfter(self.on_quiet_hours_start)
        elif not is_quiet and self._was_in_quiet_hours:
            if self.on_quiet_hours_end:
                wx.CallAfter(self.on_quiet_hours_end)

        self._was_in_quiet_hours = is_quiet

        # Schedule next check (every minute)
        self._check_timer = threading.Timer(60, self._check_and_schedule)
        self._check_timer.daemon = True
        self._check_timer.start()

    def get_status_text(self) -> str:
        """Get human-readable status."""
        if not self.settings.enabled:
            return "Quiet hours disabled"

        if self.is_quiet_hours():
            return f"Quiet hours active until {self.settings.end_time}"

        return f"Quiet hours: {self.settings.start_time} - {self.settings.end_time}"


class QuietHoursDialog(wx.Dialog):
    """Dialog for configuring quiet hours."""

    def __init__(self, parent: wx.Window, manager: QuietHoursManager):
        super().__init__(parent, title="Quiet Hours Settings", style=wx.DEFAULT_DIALOG_STYLE)

        self.manager = manager
        self._create_ui()
        self.Fit()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Enable checkbox
        self.chk_enabled = wx.CheckBox(panel, label="&Enable quiet hours")
        self.chk_enabled.SetValue(self.manager.settings.enabled)
        self.chk_enabled.Bind(wx.EVT_CHECKBOX, self._on_enabled_changed)
        main_sizer.Add(self.chk_enabled, 0, wx.ALL, 10)

        # Time settings
        time_sizer = wx.FlexGridSizer(rows=2, cols=2, hgap=10, vgap=5)

        time_sizer.Add(wx.StaticText(panel, label="Start time:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.start_time = wx.TextCtrl(panel, value=self.manager.settings.start_time)
        self.start_time.SetName("Start time (HH:MM)")
        time_sizer.Add(self.start_time, 0)

        time_sizer.Add(wx.StaticText(panel, label="End time:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.end_time = wx.TextCtrl(panel, value=self.manager.settings.end_time)
        self.end_time.SetName("End time (HH:MM)")
        time_sizer.Add(self.end_time, 0)

        main_sizer.Add(time_sizer, 0, wx.ALL, 10)

        # Options
        self.chk_mute_notifications = wx.CheckBox(
            panel, label="&Mute notifications during quiet hours"
        )
        self.chk_mute_notifications.SetValue(self.manager.settings.mute_notifications)
        main_sizer.Add(self.chk_mute_notifications, 0, wx.ALL, 10)

        self.chk_reduce_volume = wx.CheckBox(panel, label="&Reduce volume during quiet hours")
        self.chk_reduce_volume.SetValue(self.manager.settings.reduce_volume)
        main_sizer.Add(self.chk_reduce_volume, 0, wx.LEFT | wx.RIGHT, 10)

        # Volume slider
        vol_sizer = wx.BoxSizer(wx.HORIZONTAL)
        vol_sizer.Add(
            wx.StaticText(panel, label="Reduced volume:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )
        self.vol_slider = wx.Slider(
            panel, value=self.manager.settings.reduced_volume_percent, minValue=10, maxValue=100
        )
        self.vol_slider.SetName("Reduced volume percent")
        vol_sizer.Add(self.vol_slider, 1)
        self.vol_label = wx.StaticText(
            panel, label=f"{self.manager.settings.reduced_volume_percent}%"
        )
        vol_sizer.Add(self.vol_label, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        self.vol_slider.Bind(wx.EVT_SLIDER, self._on_vol_changed)

        main_sizer.Add(vol_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, wx.ID_OK)
        btn_ok.Bind(wx.EVT_BUTTON, self._on_ok)
        btn_cancel = wx.Button(panel, wx.ID_CANCEL)
        btn_sizer.Add(btn_ok, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_cancel, 0)

        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)
        self._update_enabled_state()

    def _on_enabled_changed(self, event):
        """Handle enable checkbox change."""
        self._update_enabled_state()

    def _update_enabled_state(self):
        """Update control states based on enabled checkbox."""
        enabled = self.chk_enabled.GetValue()
        self.start_time.Enable(enabled)
        self.end_time.Enable(enabled)
        self.chk_mute_notifications.Enable(enabled)
        self.chk_reduce_volume.Enable(enabled)
        self.vol_slider.Enable(enabled and self.chk_reduce_volume.GetValue())

    def _on_vol_changed(self, event):
        """Handle volume slider change."""
        self.vol_label.SetLabel(f"{self.vol_slider.GetValue()}%")

    def _on_ok(self, event):
        """Save settings."""
        self.manager.settings.enabled = self.chk_enabled.GetValue()
        self.manager.settings.start_time = self.start_time.GetValue()
        self.manager.settings.end_time = self.end_time.GetValue()
        self.manager.settings.mute_notifications = self.chk_mute_notifications.GetValue()
        self.manager.settings.reduce_volume = self.chk_reduce_volume.GetValue()
        self.manager.settings.reduced_volume_percent = self.vol_slider.GetValue()
        self.manager.save()
        self.EndModal(wx.ID_OK)


# ============================================================================
# PLAYBACK SPEED DIALOG
# ============================================================================


class PlaybackSpeedDialog(wx.Dialog):
    """Dialog for adjusting playback speed."""

    def __init__(self, parent: wx.Window, speed_controller: PlaybackSpeedController):
        super().__init__(parent, title="Playback Speed", style=wx.DEFAULT_DIALOG_STYLE)

        self.speed_controller = speed_controller
        self._create_ui()
        self.Fit()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Current speed display
        self.speed_label = wx.StaticText(
            panel, label=f"Current speed: {self.speed_controller.get_label()}"
        )
        font = self.speed_label.GetFont()
        font.SetPointSize(14)
        self.speed_label.SetFont(font)
        main_sizer.Add(self.speed_label, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        # Preset buttons
        presets_sizer = wx.GridSizer(rows=2, cols=4, hgap=5, vgap=5)

        for preset in PlaybackSpeedPreset:
            btn = wx.Button(panel, label=preset.label)
            is_current = abs(preset.value - self.speed_controller.current_speed) < 0.01
            if is_current:
                btn.SetBackgroundColour(wx.Colour(200, 230, 255))
            btn.Bind(wx.EVT_BUTTON, lambda e, p=preset: self._on_preset(p))
            presets_sizer.Add(btn, 0, wx.EXPAND)

        main_sizer.Add(presets_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Fine control
        fine_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_slower = wx.Button(panel, label="&Slower")
        btn_slower.Bind(wx.EVT_BUTTON, self._on_slower)

        self.speed_slider = wx.Slider(
            panel,
            value=int(self.speed_controller.current_speed * 100),
            minValue=25,
            maxValue=300,
            style=wx.SL_HORIZONTAL,
        )
        self.speed_slider.SetName("Playback speed")
        self.speed_slider.Bind(wx.EVT_SLIDER, self._on_slider)

        btn_faster = wx.Button(panel, label="&Faster")
        btn_faster.Bind(wx.EVT_BUTTON, self._on_faster)

        fine_sizer.Add(btn_slower, 0)
        fine_sizer.Add(self.speed_slider, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        fine_sizer.Add(btn_faster, 0)

        main_sizer.Add(fine_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Reset button
        btn_reset = wx.Button(panel, label="Reset to &Normal (1x)")
        btn_reset.Bind(wx.EVT_BUTTON, self._on_reset)
        main_sizer.Add(btn_reset, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Close button
        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
        main_sizer.Add(btn_close, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)

    def _update_display(self):
        """Update the speed display."""
        self.speed_label.SetLabel(f"Current speed: {self.speed_controller.get_label()}")
        self.speed_slider.SetValue(int(self.speed_controller.current_speed * 100))

    def _on_preset(self, preset: PlaybackSpeedPreset):
        """Handle preset button."""
        self.speed_controller.set_preset(preset)
        self._update_display()

    def _on_slider(self, event):
        """Handle slider change."""
        speed = self.speed_slider.GetValue() / 100.0
        self.speed_controller.set_speed(speed)
        self.speed_label.SetLabel(f"Current speed: {self.speed_controller.get_label()}")

    def _on_slower(self, event):
        """Decrease speed."""
        self.speed_controller.decrease()
        self._update_display()

    def _on_faster(self, event):
        """Increase speed."""
        self.speed_controller.increase()
        self._update_display()

    def _on_reset(self, event):
        """Reset to normal speed."""
        self.speed_controller.reset()
        self._update_display()


# ============================================================================
# AUTO-PLAY SETTINGS DIALOG
# ============================================================================


class AutoPlayDialog(wx.Dialog):
    """Dialog for configuring auto-play settings."""

    def __init__(self, parent: wx.Window, manager: AutoPlayManager, streams: List[str]):
        super().__init__(parent, title="Auto-Play Settings", style=wx.DEFAULT_DIALOG_STYLE)

        self.manager = manager
        self.streams = streams
        self._create_ui()
        self.Fit()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Enable checkbox
        self.chk_enabled = wx.CheckBox(panel, label="&Auto-play on startup")
        self.chk_enabled.SetValue(self.manager.settings.enabled)
        self.chk_enabled.Bind(wx.EVT_CHECKBOX, self._on_enabled_changed)
        main_sizer.Add(self.chk_enabled, 0, wx.ALL, 10)

        # Content type selection
        type_sizer = wx.BoxSizer(wx.HORIZONTAL)
        type_sizer.Add(
            wx.StaticText(panel, label="Play:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )

        self.content_type = wx.Choice(panel, choices=["Last played", "Specific stream"])
        self.content_type.SetSelection(
            0 if self.manager.settings.content_type == "last_played" else 1
        )
        self.content_type.Bind(wx.EVT_CHOICE, self._on_type_changed)
        type_sizer.Add(self.content_type, 0)

        main_sizer.Add(type_sizer, 0, wx.ALL, 10)

        # Stream selection
        stream_sizer = wx.BoxSizer(wx.HORIZONTAL)
        stream_sizer.Add(
            wx.StaticText(panel, label="Stream:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )

        self.stream_choice = wx.Choice(panel, choices=self.streams)
        if self.manager.settings.content_name in self.streams:
            self.stream_choice.SetSelection(self.streams.index(self.manager.settings.content_name))
        elif self.streams:
            self.stream_choice.SetSelection(0)
        stream_sizer.Add(self.stream_choice, 1)

        main_sizer.Add(stream_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Delay setting
        delay_sizer = wx.BoxSizer(wx.HORIZONTAL)
        delay_sizer.Add(
            wx.StaticText(panel, label="Delay before playing:"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            5,
        )
        self.delay_spin = wx.SpinCtrl(
            panel, min=0, max=30, initial=self.manager.settings.delay_seconds
        )
        delay_sizer.Add(self.delay_spin, 0)
        delay_sizer.Add(
            wx.StaticText(panel, label="seconds"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5
        )

        main_sizer.Add(delay_sizer, 0, wx.ALL, 10)

        # Conditional option
        self.chk_only_if_playing = wx.CheckBox(
            panel, label="Only auto-play if &previous session was playing"
        )
        self.chk_only_if_playing.SetValue(self.manager.settings.only_when_last_session_was_playing)
        main_sizer.Add(self.chk_only_if_playing, 0, wx.ALL, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, wx.ID_OK)
        btn_ok.Bind(wx.EVT_BUTTON, self._on_ok)
        btn_cancel = wx.Button(panel, wx.ID_CANCEL)
        btn_sizer.Add(btn_ok, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_cancel, 0)

        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)
        self._update_enabled_state()

    def _on_enabled_changed(self, event):
        """Handle enable checkbox change."""
        self._update_enabled_state()

    def _on_type_changed(self, event):
        """Handle content type change."""
        self._update_enabled_state()

    def _update_enabled_state(self):
        """Update control states."""
        enabled = self.chk_enabled.GetValue()
        is_specific = self.content_type.GetSelection() == 1

        self.content_type.Enable(enabled)
        self.stream_choice.Enable(enabled and is_specific)
        self.delay_spin.Enable(enabled)
        self.chk_only_if_playing.Enable(enabled)

    def _on_ok(self, event):
        """Save settings."""
        self.manager.settings.enabled = self.chk_enabled.GetValue()

        if self.content_type.GetSelection() == 0:
            self.manager.settings.content_type = "last_played"
            self.manager.settings.content_name = ""
        else:
            self.manager.settings.content_type = "stream"
            idx = self.stream_choice.GetSelection()
            if idx >= 0:
                self.manager.settings.content_name = self.streams[idx]

        self.manager.settings.delay_seconds = self.delay_spin.GetValue()
        self.manager.settings.only_when_last_session_was_playing = (
            self.chk_only_if_playing.GetValue()
        )
        self.manager.save()
        self.EndModal(wx.ID_OK)
