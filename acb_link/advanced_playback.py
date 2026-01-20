"""
ACB Link - Advanced Playback Features
Bookmarks, skip silence, quick seek, audio profiles, smart speed,
crossfade, mark as listened, and more.
"""

import json
import os
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import wx

# ============================================================================
# AUDIO BOOKMARKS
# ============================================================================


@dataclass
class AudioBookmark:
    """A bookmark at a specific position in audio content."""

    id: str
    content_type: str  # "stream" or "podcast"
    content_name: str
    episode_title: str = ""
    position_seconds: int = 0
    label: str = ""
    notes: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"bm_{int(time.time() * 1000)}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.label:
            mins = self.position_seconds // 60
            secs = self.position_seconds % 60
            self.label = f"{mins}:{secs:02d}"

    @property
    def position_formatted(self) -> str:
        """Get formatted position string."""
        mins = self.position_seconds // 60
        secs = self.position_seconds % 60
        if mins >= 60:
            hours = mins // 60
            mins = mins % 60
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"


class BookmarkManager:
    """Manages audio bookmarks within content."""

    MAX_BOOKMARKS_PER_CONTENT = 50

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or str(Path.home() / ".acb_link" / "bookmarks.json")
        self.bookmarks: Dict[str, List[AudioBookmark]] = {}
        self._load()

    def _load(self):
        """Load bookmarks from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for key, items in data.items():
                    self.bookmarks[key] = [AudioBookmark(**item) for item in items]
            except Exception:
                self.bookmarks = {}

    def save(self):
        """Save bookmarks to storage."""
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        data = {key: [asdict(bm) for bm in items] for key, items in self.bookmarks.items()}
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _get_key(self, content_type: str, content_name: str, episode_title: str = "") -> str:
        """Generate storage key for content."""
        return f"{content_type}:{content_name}:{episode_title}"

    def add_bookmark(
        self,
        content_type: str,
        content_name: str,
        position_seconds: int,
        episode_title: str = "",
        label: str = "",
        notes: str = "",
    ) -> AudioBookmark:
        """Add a bookmark."""
        key = self._get_key(content_type, content_name, episode_title)

        if key not in self.bookmarks:
            self.bookmarks[key] = []

        bookmark = AudioBookmark(
            id="",
            content_type=content_type,
            content_name=content_name,
            episode_title=episode_title,
            position_seconds=position_seconds,
            label=label,
            notes=notes,
        )

        self.bookmarks[key].append(bookmark)

        # Sort by position
        self.bookmarks[key].sort(key=lambda b: b.position_seconds)

        # Limit per content
        if len(self.bookmarks[key]) > self.MAX_BOOKMARKS_PER_CONTENT:
            self.bookmarks[key] = self.bookmarks[key][: self.MAX_BOOKMARKS_PER_CONTENT]

        self.save()
        return bookmark

    def get_bookmarks(
        self, content_type: str, content_name: str, episode_title: str = ""
    ) -> List[AudioBookmark]:
        """Get bookmarks for content."""
        key = self._get_key(content_type, content_name, episode_title)
        return self.bookmarks.get(key, [])

    def remove_bookmark(self, bookmark_id: str):
        """Remove a bookmark by ID."""
        for key, items in self.bookmarks.items():
            self.bookmarks[key] = [bm for bm in items if bm.id != bookmark_id]
        self.save()

    def get_nearest_bookmark(
        self,
        content_type: str,
        content_name: str,
        position: int,
        episode_title: str = "",
        direction: str = "next",  # "next" or "previous"
    ) -> Optional[AudioBookmark]:
        """Get nearest bookmark from current position."""
        bookmarks = self.get_bookmarks(content_type, content_name, episode_title)

        if direction == "next":
            for bm in bookmarks:
                if bm.position_seconds > position:
                    return bm
        else:
            for bm in reversed(bookmarks):
                if bm.position_seconds < position:
                    return bm

        return None


class BookmarkDialog(wx.Dialog):
    """Dialog for managing bookmarks."""

    def __init__(
        self,
        parent: wx.Window,
        bookmark_manager: BookmarkManager,
        content_type: str,
        content_name: str,
        current_position: int,
        episode_title: str = "",
        on_jump_to: Optional[Callable[[int], None]] = None,
    ):
        super().__init__(
            parent, title="Audio Bookmarks", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        self.manager = bookmark_manager
        self.content_type = content_type
        self.content_name = content_name
        self.episode_title = episode_title
        self.current_position = current_position
        self.on_jump_to = on_jump_to

        self.SetSize((500, 400))  # type: ignore[arg-type]
        self._create_ui()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Add bookmark section
        add_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.label_entry = wx.TextCtrl(panel, size=(200, -1))  # type: ignore[arg-type]
        self.label_entry.SetHint("Bookmark label (optional)")
        self.label_entry.SetName("Bookmark label")

        btn_add = wx.Button(panel, label="&Add Bookmark Here")
        btn_add.Bind(wx.EVT_BUTTON, self._on_add)

        add_sizer.Add(self.label_entry, 1, wx.RIGHT, 5)
        add_sizer.Add(btn_add, 0)

        main_sizer.Add(add_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Bookmarks list
        self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.SetName("Bookmarks list")

        self.list_ctrl.InsertColumn(0, "Position", width=100)
        self.list_ctrl.InsertColumn(1, "Label", width=200)
        self.list_ctrl.InsertColumn(2, "Created", width=150)

        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_jump)

        main_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_jump = wx.Button(panel, label="&Jump to Selected")
        btn_jump.Bind(wx.EVT_BUTTON, self._on_jump)

        btn_delete = wx.Button(panel, label="&Delete Selected")
        btn_delete.Bind(wx.EVT_BUTTON, self._on_delete)

        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))

        btn_sizer.Add(btn_jump, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_delete, 0, wx.RIGHT, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(btn_close, 0)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main_sizer)
        self._refresh_list()

    def _refresh_list(self):
        """Refresh the bookmarks list."""
        self.list_ctrl.DeleteAllItems()

        bookmarks = self.manager.get_bookmarks(
            self.content_type, self.content_name, self.episode_title
        )

        for i, bm in enumerate(bookmarks):
            idx = self.list_ctrl.InsertItem(i, bm.position_formatted)
            self.list_ctrl.SetItem(idx, 1, bm.label or "(no label)")
            try:
                dt = datetime.fromisoformat(bm.created_at)
                created = dt.strftime("%b %d, %I:%M %p")
            except Exception:
                created = "Unknown"
            self.list_ctrl.SetItem(idx, 2, created)
            self.list_ctrl.SetItemData(idx, i)

    def _on_add(self, event):
        """Add a new bookmark."""
        label = self.label_entry.GetValue().strip()
        self.manager.add_bookmark(
            self.content_type, self.content_name, self.current_position, self.episode_title, label
        )
        self.label_entry.Clear()
        self._refresh_list()

    def _on_jump(self, event):
        """Jump to selected bookmark."""
        idx = self.list_ctrl.GetFirstSelected()
        if idx < 0:
            return

        bookmarks = self.manager.get_bookmarks(
            self.content_type, self.content_name, self.episode_title
        )

        if 0 <= idx < len(bookmarks):
            if self.on_jump_to:
                self.on_jump_to(bookmarks[idx].position_seconds)

    def _on_delete(self, event):
        """Delete selected bookmark."""
        idx = self.list_ctrl.GetFirstSelected()
        if idx < 0:
            return

        bookmarks = self.manager.get_bookmarks(
            self.content_type, self.content_name, self.episode_title
        )

        if 0 <= idx < len(bookmarks):
            self.manager.remove_bookmark(bookmarks[idx].id)
            self._refresh_list()


# ============================================================================
# QUICK SEEK DIALOG
# ============================================================================


class QuickSeekDialog(wx.Dialog):
    """Dialog for jumping to a specific time position."""

    def __init__(
        self,
        parent: wx.Window,
        current_position: int,
        duration: int,
        on_seek: Callable[[int], None],
    ):
        super().__init__(parent, title="Go to Time Position", style=wx.DEFAULT_DIALOG_STYLE)

        self.current_position = current_position
        self.duration = duration
        self.on_seek = on_seek
        self.target_position = current_position

        self._create_ui()
        self.Fit()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Current position
        cur_mins = self.current_position // 60
        cur_secs = self.current_position % 60
        dur_mins = self.duration // 60
        dur_secs = self.duration % 60

        info = wx.StaticText(
            panel, label=f"Current: {cur_mins}:{cur_secs:02d} / Duration: {dur_mins}:{dur_secs:02d}"
        )
        main_sizer.Add(info, 0, wx.ALL, 10)

        # Time entry
        time_sizer = wx.BoxSizer(wx.HORIZONTAL)

        time_sizer.Add(
            wx.StaticText(panel, label="Go to:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )

        self.hours_spin = wx.SpinCtrl(panel, min=0, max=99, initial=cur_mins // 60, size=(60, -1))  # type: ignore[arg-type]
        self.hours_spin.SetName("Hours")
        time_sizer.Add(self.hours_spin, 0, wx.RIGHT, 2)
        time_sizer.Add(wx.StaticText(panel, label=":"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2)

        self.mins_spin = wx.SpinCtrl(panel, min=0, max=59, initial=cur_mins % 60, size=(60, -1))  # type: ignore[arg-type]
        self.mins_spin.SetName("Minutes")
        time_sizer.Add(self.mins_spin, 0, wx.RIGHT, 2)
        time_sizer.Add(wx.StaticText(panel, label=":"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2)

        self.secs_spin = wx.SpinCtrl(panel, min=0, max=59, initial=cur_secs, size=(60, -1))  # type: ignore[arg-type]
        self.secs_spin.SetName("Seconds")
        time_sizer.Add(self.secs_spin, 0)

        main_sizer.Add(time_sizer, 0, wx.ALL, 10)

        # Quick jump buttons
        quick_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for label, seconds in [
            ("-30s", -30),
            ("-10s", -10),
            ("+10s", 10),
            ("+30s", 30),
            ("+1m", 60),
        ]:
            btn = wx.Button(panel, label=label, size=(50, -1))  # type: ignore[arg-type]
            btn.Bind(wx.EVT_BUTTON, lambda e, s=seconds: self._quick_jump(s))
            quick_sizer.Add(btn, 0, wx.RIGHT, 5)

        main_sizer.Add(quick_sizer, 0, wx.ALL, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_go = wx.Button(panel, wx.ID_OK, label="&Go")
        btn_go.Bind(wx.EVT_BUTTON, self._on_go)

        btn_cancel = wx.Button(panel, wx.ID_CANCEL)

        btn_sizer.Add(btn_go, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_cancel, 0)

        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)

    def _quick_jump(self, delta: int):
        """Quick relative jump."""
        current = (
            self.hours_spin.GetValue() * 3600
            + self.mins_spin.GetValue() * 60
            + self.secs_spin.GetValue()
        )
        new_pos = max(0, min(self.duration, current + delta))

        self.hours_spin.SetValue(new_pos // 3600)
        self.mins_spin.SetValue((new_pos % 3600) // 60)
        self.secs_spin.SetValue(new_pos % 60)

    def _on_go(self, event):
        """Jump to the specified position."""
        position = (
            self.hours_spin.GetValue() * 3600
            + self.mins_spin.GetValue() * 60
            + self.secs_spin.GetValue()
        )
        position = max(0, min(self.duration, position))
        self.on_seek(position)
        self.EndModal(wx.ID_OK)


# ============================================================================
# SKIP SILENCE
# ============================================================================


class SkipSilenceManager:
    """Manages automatic silence skipping during playback."""

    def __init__(
        self,
        get_audio_level: Callable[[], float],
        skip_callback: Callable[[float], None],
        silence_threshold: float = 0.01,  # Audio level below this is silence
        min_silence_duration: float = 2.0,  # Skip after this much silence
        skip_speed_multiplier: float = 4.0,  # Speed up during silence
    ):
        self.get_audio_level = get_audio_level
        self.skip_callback = skip_callback
        self.silence_threshold = silence_threshold
        self.min_silence_duration = min_silence_duration
        self.skip_speed_multiplier = skip_speed_multiplier

        self._enabled = False
        self._silence_start: Optional[float] = None
        self._is_skipping = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        if value and not self._enabled:
            self._start_monitoring()
        elif not value and self._enabled:
            self._stop_monitoring()
        self._enabled = value

    def _start_monitoring(self):
        """Start monitoring audio levels."""
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def _stop_monitoring(self):
        """Stop monitoring."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        self._monitor_thread = None
        self._silence_start = None
        self._is_skipping = False

    def _monitor_loop(self):
        """Monitor audio levels in background."""
        while not self._stop_event.is_set():
            try:
                level = self.get_audio_level()
                current_time = time.time()

                if level < self.silence_threshold:
                    if self._silence_start is None:
                        self._silence_start = current_time
                    elif current_time - self._silence_start >= self.min_silence_duration:
                        if not self._is_skipping:
                            self._is_skipping = True
                            wx.CallAfter(self.skip_callback, self.skip_speed_multiplier)
                else:
                    if self._is_skipping:
                        self._is_skipping = False
                        wx.CallAfter(self.skip_callback, 1.0)  # Reset to normal
                    self._silence_start = None

            except Exception:
                pass

            self._stop_event.wait(0.1)


# ============================================================================
# AUDIO PROFILES
# ============================================================================


@dataclass
class AudioProfile:
    """Audio settings profile."""

    name: str
    eq_bass: int = 0  # -10 to +10
    eq_mid: int = 0
    eq_treble: int = 0
    volume_boost: int = 0  # -20 to +20 dB
    normalize: bool = False
    mono: bool = False
    is_builtin: bool = False


class AudioProfileManager:
    """Manages audio equalizer profiles."""

    BUILTIN_PROFILES = {
        "flat": AudioProfile("Flat", 0, 0, 0, 0, False, False, True),
        "bass_boost": AudioProfile("Bass Boost", 6, 0, -2, 0, False, False, True),
        "voice": AudioProfile("Voice Enhancement", -2, 4, 2, 3, True, False, True),
        "treble_boost": AudioProfile("Treble Boost", -2, 0, 6, 0, False, False, True),
        "audiobook": AudioProfile("Audiobook", -3, 5, 3, 5, True, False, True),
        "music": AudioProfile("Music", 3, -1, 2, 0, False, False, True),
        "podcast": AudioProfile("Podcast", -2, 6, 2, 4, True, False, True),
        "mono_voice": AudioProfile("Mono Voice", -2, 4, 2, 3, True, True, True),
    }

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or str(Path.home() / ".acb_link" / "audio_profiles.json")
        self.custom_profiles: Dict[str, AudioProfile] = {}
        self.current_profile: str = "flat"
        self._load()

    def _load(self):
        """Load custom profiles."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.current_profile = data.get("current", "flat")
                for name, profile_data in data.get("profiles", {}).items():
                    self.custom_profiles[name] = AudioProfile(**profile_data)
            except Exception:
                pass

    def save(self):
        """Save custom profiles."""
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            "current": self.current_profile,
            "profiles": {name: asdict(p) for name, p in self.custom_profiles.items()},
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_all_profiles(self) -> Dict[str, AudioProfile]:
        """Get all profiles (builtin + custom)."""
        profiles = dict(self.BUILTIN_PROFILES)
        profiles.update(self.custom_profiles)
        return profiles

    def get_profile(self, name: str) -> Optional[AudioProfile]:
        """Get a profile by name."""
        if name in self.BUILTIN_PROFILES:
            return self.BUILTIN_PROFILES[name]
        return self.custom_profiles.get(name)

    def get_current_profile(self) -> AudioProfile:
        """Get the currently active profile."""
        return self.get_profile(self.current_profile) or self.BUILTIN_PROFILES["flat"]

    def set_current_profile(self, name: str):
        """Set the active profile."""
        if name in self.get_all_profiles():
            self.current_profile = name
            self.save()

    def add_profile(self, profile: AudioProfile):
        """Add a custom profile."""
        self.custom_profiles[profile.name.lower().replace(" ", "_")] = profile
        self.save()

    def remove_profile(self, name: str):
        """Remove a custom profile."""
        if name in self.custom_profiles:
            del self.custom_profiles[name]
            if self.current_profile == name:
                self.current_profile = "flat"
            self.save()


class AudioProfileDialog(wx.Dialog):
    """Dialog for selecting and editing audio profiles."""

    def __init__(
        self,
        parent: wx.Window,
        profile_manager: AudioProfileManager,
        on_profile_changed: Callable[[AudioProfile], None],
    ):
        super().__init__(
            parent, title="Audio Profiles", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        self.manager = profile_manager
        self.on_profile_changed = on_profile_changed

        self.SetSize((450, 500))  # type: ignore[arg-type]
        self._create_ui()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Profile selection
        profiles = self.manager.get_all_profiles()
        profile_names = list(profiles.keys())
        display_names = [p.name for p in profiles.values()]

        profile_sizer = wx.BoxSizer(wx.HORIZONTAL)
        profile_sizer.Add(
            wx.StaticText(panel, label="Profile:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )

        self.profile_choice = wx.Choice(panel, choices=display_names)
        self.profile_choice.SetName("Audio profile")
        if self.manager.current_profile in profile_names:
            self.profile_choice.SetSelection(profile_names.index(self.manager.current_profile))
        self.profile_choice.Bind(wx.EVT_CHOICE, self._on_profile_selected)

        profile_sizer.Add(self.profile_choice, 1)
        main_sizer.Add(profile_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Equalizer sliders
        eq_box = wx.StaticBox(panel, label="Equalizer")
        eq_sizer = wx.StaticBoxSizer(eq_box, wx.VERTICAL)

        current = self.manager.get_current_profile()

        # Bass
        bass_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bass_sizer.Add(wx.StaticText(panel, label="Bass:", size=(80, -1)), 0, wx.ALIGN_CENTER_VERTICAL)  # type: ignore[arg-type]
        self.bass_slider = wx.Slider(panel, value=current.eq_bass, minValue=-10, maxValue=10)
        self.bass_slider.SetName("Bass")
        self.bass_label = wx.StaticText(panel, label=f"{current.eq_bass:+d}", size=(40, -1))  # type: ignore[arg-type]
        self.bass_slider.Bind(
            wx.EVT_SLIDER, lambda e: self.bass_label.SetLabel(f"{self.bass_slider.GetValue():+d}")
        )
        bass_sizer.Add(self.bass_slider, 1)
        bass_sizer.Add(self.bass_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        eq_sizer.Add(bass_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Mid
        mid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mid_sizer.Add(wx.StaticText(panel, label="Mid:", size=(80, -1)), 0, wx.ALIGN_CENTER_VERTICAL)  # type: ignore[arg-type]
        self.mid_slider = wx.Slider(panel, value=current.eq_mid, minValue=-10, maxValue=10)
        self.mid_slider.SetName("Mid")
        self.mid_label = wx.StaticText(panel, label=f"{current.eq_mid:+d}", size=(40, -1))  # type: ignore[arg-type]
        self.mid_slider.Bind(
            wx.EVT_SLIDER, lambda e: self.mid_label.SetLabel(f"{self.mid_slider.GetValue():+d}")
        )
        mid_sizer.Add(self.mid_slider, 1)
        mid_sizer.Add(self.mid_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        eq_sizer.Add(mid_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Treble
        treble_sizer = wx.BoxSizer(wx.HORIZONTAL)
        treble_sizer.Add(wx.StaticText(panel, label="Treble:", size=(80, -1)), 0, wx.ALIGN_CENTER_VERTICAL)  # type: ignore[arg-type]
        self.treble_slider = wx.Slider(panel, value=current.eq_treble, minValue=-10, maxValue=10)
        self.treble_slider.SetName("Treble")
        self.treble_label = wx.StaticText(panel, label=f"{current.eq_treble:+d}", size=(40, -1))  # type: ignore[arg-type]
        self.treble_slider.Bind(
            wx.EVT_SLIDER,
            lambda e: self.treble_label.SetLabel(f"{self.treble_slider.GetValue():+d}"),
        )
        treble_sizer.Add(self.treble_slider, 1)
        treble_sizer.Add(self.treble_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        eq_sizer.Add(treble_sizer, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(eq_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Options
        self.normalize_check = wx.CheckBox(panel, label="&Normalize volume")
        self.normalize_check.SetValue(current.normalize)
        main_sizer.Add(self.normalize_check, 0, wx.ALL, 10)

        self.mono_check = wx.CheckBox(panel, label="&Mono output")
        self.mono_check.SetValue(current.mono)
        main_sizer.Add(self.mono_check, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_apply = wx.Button(panel, label="&Apply")
        btn_apply.Bind(wx.EVT_BUTTON, self._on_apply)

        btn_save_as = wx.Button(panel, label="&Save as New...")
        btn_save_as.Bind(wx.EVT_BUTTON, self._on_save_as)

        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))

        btn_sizer.Add(btn_apply, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_save_as, 0, wx.RIGHT, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(btn_close, 0)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main_sizer)

    def _on_profile_selected(self, event):
        """Handle profile selection change."""
        profiles = list(self.manager.get_all_profiles().values())
        idx = self.profile_choice.GetSelection()
        if 0 <= idx < len(profiles):
            profile = profiles[idx]
            self.bass_slider.SetValue(profile.eq_bass)
            self.bass_label.SetLabel(f"{profile.eq_bass:+d}")
            self.mid_slider.SetValue(profile.eq_mid)
            self.mid_label.SetLabel(f"{profile.eq_mid:+d}")
            self.treble_slider.SetValue(profile.eq_treble)
            self.treble_label.SetLabel(f"{profile.eq_treble:+d}")
            self.normalize_check.SetValue(profile.normalize)
            self.mono_check.SetValue(profile.mono)

    def _on_apply(self, event):
        """Apply current settings."""
        profiles = list(self.manager.get_all_profiles().items())
        idx = self.profile_choice.GetSelection()
        if 0 <= idx < len(profiles):
            profile_key = profiles[idx][0]
            self.manager.set_current_profile(profile_key)

            # Create updated profile with current slider values
            profile = AudioProfile(
                name=profiles[idx][1].name,
                eq_bass=self.bass_slider.GetValue(),
                eq_mid=self.mid_slider.GetValue(),
                eq_treble=self.treble_slider.GetValue(),
                normalize=self.normalize_check.GetValue(),
                mono=self.mono_check.GetValue(),
            )
            self.on_profile_changed(profile)

    def _on_save_as(self, event):
        """Save current settings as new profile."""
        dlg = wx.TextEntryDialog(self, "Profile name:", "Save Audio Profile")
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue().strip()
            if name:
                profile = AudioProfile(
                    name=name,
                    eq_bass=self.bass_slider.GetValue(),
                    eq_mid=self.mid_slider.GetValue(),
                    eq_treble=self.treble_slider.GetValue(),
                    normalize=self.normalize_check.GetValue(),
                    mono=self.mono_check.GetValue(),
                )
                self.manager.add_profile(profile)
                wx.MessageBox(f"Profile '{name}' saved.", "Success", wx.OK | wx.ICON_INFORMATION)
        dlg.Destroy()


# ============================================================================
# MARK AS LISTENED / EPISODE TRACKING
# ============================================================================


@dataclass
class EpisodeStatus:
    """Tracking status for a podcast episode."""

    podcast_name: str
    episode_title: str
    is_listened: bool = False
    progress_percent: int = 0
    position_seconds: int = 0
    duration_seconds: int = 0
    last_played: str = ""
    completed_at: str = ""


class EpisodeTracker:
    """Tracks listened/progress status of podcast episodes."""

    COMPLETION_THRESHOLD = 90  # Percent - auto-mark as listened

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or str(Path.home() / ".acb_link" / "episode_status.json")
        self.episodes: Dict[str, EpisodeStatus] = {}
        self._load()

    def _load(self):
        """Load episode status."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for key, status in data.items():
                    self.episodes[key] = EpisodeStatus(**status)
            except Exception:
                pass

    def save(self):
        """Save episode status."""
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        data = {key: asdict(status) for key, status in self.episodes.items()}
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _get_key(self, podcast_name: str, episode_title: str) -> str:
        """Generate storage key."""
        return f"{podcast_name}:{episode_title}"

    def update_progress(self, podcast_name: str, episode_title: str, position: int, duration: int):
        """Update playback progress."""
        key = self._get_key(podcast_name, episode_title)

        if key not in self.episodes:
            self.episodes[key] = EpisodeStatus(
                podcast_name=podcast_name, episode_title=episode_title
            )

        status = self.episodes[key]
        status.position_seconds = position
        status.duration_seconds = duration
        status.progress_percent = int((position / duration * 100) if duration > 0 else 0)
        status.last_played = datetime.now().isoformat()

        # Auto-mark as listened if completed
        if status.progress_percent >= self.COMPLETION_THRESHOLD and not status.is_listened:
            status.is_listened = True
            status.completed_at = datetime.now().isoformat()

        self.save()

    def mark_listened(self, podcast_name: str, episode_title: str, listened: bool = True):
        """Manually mark an episode as listened/unlistened."""
        key = self._get_key(podcast_name, episode_title)

        if key not in self.episodes:
            self.episodes[key] = EpisodeStatus(
                podcast_name=podcast_name, episode_title=episode_title
            )

        self.episodes[key].is_listened = listened
        if listened:
            self.episodes[key].completed_at = datetime.now().isoformat()
        else:
            self.episodes[key].completed_at = ""

        self.save()

    def is_listened(self, podcast_name: str, episode_title: str) -> bool:
        """Check if episode is marked as listened."""
        key = self._get_key(podcast_name, episode_title)
        return self.episodes.get(key, EpisodeStatus("", "")).is_listened

    def get_progress(self, podcast_name: str, episode_title: str) -> int:
        """Get playback progress percent."""
        key = self._get_key(podcast_name, episode_title)
        return self.episodes.get(key, EpisodeStatus("", "")).progress_percent

    def get_status(self, podcast_name: str, episode_title: str) -> Optional[EpisodeStatus]:
        """Get full status for an episode."""
        key = self._get_key(podcast_name, episode_title)
        return self.episodes.get(key)


# ============================================================================
# LISTENING GOALS
# ============================================================================


@dataclass
class ListeningGoal:
    """A listening goal/target."""

    type: str  # "daily" or "weekly"
    target_minutes: int = 60
    current_minutes: int = 0
    streak_days: int = 0
    last_updated: str = ""
    created_at: str = ""

    @property
    def progress_percent(self) -> int:
        if self.target_minutes <= 0:
            return 100
        return min(100, int(self.current_minutes / self.target_minutes * 100))

    @property
    def is_complete(self) -> bool:
        return self.current_minutes >= self.target_minutes


class ListeningGoalManager:
    """Manages listening goals and streaks."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or str(Path.home() / ".acb_link" / "listening_goals.json")
        self.daily_goal: Optional[ListeningGoal] = None
        self.weekly_goal: Optional[ListeningGoal] = None
        self._load()

    def _load(self):
        """Load goals."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "daily" in data:
                    self.daily_goal = ListeningGoal(**data["daily"])
                if "weekly" in data:
                    self.weekly_goal = ListeningGoal(**data["weekly"])
            except Exception:
                pass

        # Check for new day/week
        self._check_reset()

    def save(self):
        """Save goals."""
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if self.daily_goal:
            data["daily"] = asdict(self.daily_goal)
        if self.weekly_goal:
            data["weekly"] = asdict(self.weekly_goal)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _check_reset(self):
        """Check if goals need to be reset for new period."""
        now = datetime.now()
        today = now.date().isoformat()

        if self.daily_goal:
            last = self.daily_goal.last_updated[:10] if self.daily_goal.last_updated else ""
            if last != today:
                # New day - check streak
                if last and self.daily_goal.is_complete:
                    try:
                        last_date = datetime.fromisoformat(last).date()
                        if (now.date() - last_date).days == 1:
                            self.daily_goal.streak_days += 1
                        else:
                            self.daily_goal.streak_days = 0
                    except Exception:
                        self.daily_goal.streak_days = 0
                elif last:
                    self.daily_goal.streak_days = 0

                self.daily_goal.current_minutes = 0
                self.daily_goal.last_updated = now.isoformat()

        if self.weekly_goal:
            # Reset on Monday
            if now.weekday() == 0:
                last = self.weekly_goal.last_updated[:10] if self.weekly_goal.last_updated else ""
                if last:
                    try:
                        last_date = datetime.fromisoformat(last).date()
                        if (now.date() - last_date).days >= 7:
                            self.weekly_goal.current_minutes = 0
                    except Exception:
                        pass

        self.save()

    def set_daily_goal(self, target_minutes: int):
        """Set daily listening goal."""
        if self.daily_goal:
            self.daily_goal.target_minutes = target_minutes
        else:
            self.daily_goal = ListeningGoal(
                type="daily", target_minutes=target_minutes, created_at=datetime.now().isoformat()
            )
        self.save()

    def set_weekly_goal(self, target_minutes: int):
        """Set weekly listening goal."""
        if self.weekly_goal:
            self.weekly_goal.target_minutes = target_minutes
        else:
            self.weekly_goal = ListeningGoal(
                type="weekly", target_minutes=target_minutes, created_at=datetime.now().isoformat()
            )
        self.save()

    def add_listening_time(self, minutes: int):
        """Add listening time to goals."""
        now = datetime.now().isoformat()

        if self.daily_goal:
            self.daily_goal.current_minutes += minutes
            self.daily_goal.last_updated = now

        if self.weekly_goal:
            self.weekly_goal.current_minutes += minutes
            self.weekly_goal.last_updated = now

        self.save()

    def get_daily_progress(self) -> Tuple[int, int, int]:
        """Get daily progress (current, target, percent)."""
        if not self.daily_goal:
            return (0, 0, 0)
        return (
            self.daily_goal.current_minutes,
            self.daily_goal.target_minutes,
            self.daily_goal.progress_percent,
        )

    def get_weekly_progress(self) -> Tuple[int, int, int]:
        """Get weekly progress (current, target, percent)."""
        if not self.weekly_goal:
            return (0, 0, 0)
        return (
            self.weekly_goal.current_minutes,
            self.weekly_goal.target_minutes,
            self.weekly_goal.progress_percent,
        )


class ListeningGoalDialog(wx.Dialog):
    """Dialog for setting and viewing listening goals."""

    def __init__(self, parent: wx.Window, goal_manager: ListeningGoalManager):
        super().__init__(parent, title="Listening Goals", style=wx.DEFAULT_DIALOG_STYLE)

        self.manager = goal_manager
        self._create_ui()
        self.Fit()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Daily goal
        daily_box = wx.StaticBox(panel, label="Daily Goal")
        daily_sizer = wx.StaticBoxSizer(daily_box, wx.VERTICAL)

        daily_current, daily_target, daily_pct = self.manager.get_daily_progress()

        daily_prog_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.daily_gauge = wx.Gauge(panel, range=100, style=wx.GA_HORIZONTAL)
        self.daily_gauge.SetValue(daily_pct)
        daily_prog_sizer.Add(self.daily_gauge, 1, wx.RIGHT, 10)
        self.daily_label = wx.StaticText(
            panel, label=f"{daily_current}/{daily_target} min ({daily_pct}%)"
        )
        daily_prog_sizer.Add(self.daily_label, 0, wx.ALIGN_CENTER_VERTICAL)
        daily_sizer.Add(daily_prog_sizer, 0, wx.EXPAND | wx.ALL, 5)

        daily_set_sizer = wx.BoxSizer(wx.HORIZONTAL)
        daily_set_sizer.Add(
            wx.StaticText(panel, label="Target:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )
        self.daily_spin = wx.SpinCtrl(panel, min=5, max=480, initial=daily_target or 60)
        self.daily_spin.SetName("Daily target minutes")
        daily_set_sizer.Add(self.daily_spin, 0, wx.RIGHT, 5)
        daily_set_sizer.Add(wx.StaticText(panel, label="minutes"), 0, wx.ALIGN_CENTER_VERTICAL)
        daily_sizer.Add(daily_set_sizer, 0, wx.ALL, 5)

        if self.manager.daily_goal:
            streak_text = f"Current streak: {self.manager.daily_goal.streak_days} days"
            daily_sizer.Add(wx.StaticText(panel, label=streak_text), 0, wx.ALL, 5)

        main_sizer.Add(daily_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Weekly goal
        weekly_box = wx.StaticBox(panel, label="Weekly Goal")
        weekly_sizer = wx.StaticBoxSizer(weekly_box, wx.VERTICAL)

        weekly_current, weekly_target, weekly_pct = self.manager.get_weekly_progress()

        weekly_prog_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.weekly_gauge = wx.Gauge(panel, range=100, style=wx.GA_HORIZONTAL)
        self.weekly_gauge.SetValue(weekly_pct)
        weekly_prog_sizer.Add(self.weekly_gauge, 1, wx.RIGHT, 10)
        self.weekly_label = wx.StaticText(
            panel, label=f"{weekly_current}/{weekly_target} min ({weekly_pct}%)"
        )
        weekly_prog_sizer.Add(self.weekly_label, 0, wx.ALIGN_CENTER_VERTICAL)
        weekly_sizer.Add(weekly_prog_sizer, 0, wx.EXPAND | wx.ALL, 5)

        weekly_set_sizer = wx.BoxSizer(wx.HORIZONTAL)
        weekly_set_sizer.Add(
            wx.StaticText(panel, label="Target:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5
        )
        self.weekly_spin = wx.SpinCtrl(panel, min=30, max=2400, initial=weekly_target or 300)
        self.weekly_spin.SetName("Weekly target minutes")
        weekly_set_sizer.Add(self.weekly_spin, 0, wx.RIGHT, 5)
        weekly_set_sizer.Add(wx.StaticText(panel, label="minutes"), 0, wx.ALIGN_CENTER_VERTICAL)
        weekly_sizer.Add(weekly_set_sizer, 0, wx.ALL, 5)

        main_sizer.Add(weekly_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_save = wx.Button(panel, label="&Save Goals")
        btn_save.Bind(wx.EVT_BUTTON, self._on_save)

        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))

        btn_sizer.Add(btn_save, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_close, 0)

        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)

    def _on_save(self, event):
        """Save goals."""
        self.manager.set_daily_goal(self.daily_spin.GetValue())
        self.manager.set_weekly_goal(self.weekly_spin.GetValue())
        wx.MessageBox("Goals saved!", "Success", wx.OK | wx.ICON_INFORMATION)


# ============================================================================
# QUICK NOTES
# ============================================================================


@dataclass
class QuickNote:
    """A timestamped note taken during playback."""

    id: str
    content_type: str
    content_name: str
    episode_title: str = ""
    position_seconds: int = 0
    text: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"note_{int(time.time() * 1000)}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class QuickNotesManager:
    """Manages quick notes taken during playback."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or str(Path.home() / ".acb_link" / "quick_notes.json")
        self.notes: List[QuickNote] = []
        self._load()

    def _load(self):
        """Load notes."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.notes = [QuickNote(**n) for n in data]
            except Exception:
                pass

    def save(self):
        """Save notes."""
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump([asdict(n) for n in self.notes], f, indent=2)

    def add_note(
        self,
        content_type: str,
        content_name: str,
        position_seconds: int,
        text: str,
        episode_title: str = "",
    ) -> QuickNote:
        """Add a quick note."""
        note = QuickNote(
            id="",
            content_type=content_type,
            content_name=content_name,
            episode_title=episode_title,
            position_seconds=position_seconds,
            text=text,
        )
        self.notes.insert(0, note)
        self.save()
        return note

    def get_notes_for_content(
        self, content_type: str, content_name: str, episode_title: str = ""
    ) -> List[QuickNote]:
        """Get notes for specific content."""
        return [
            n
            for n in self.notes
            if (
                n.content_type == content_type
                and n.content_name == content_name
                and n.episode_title == episode_title
            )
        ]

    def get_all_notes(self) -> List[QuickNote]:
        """Get all notes."""
        return self.notes

    def delete_note(self, note_id: str):
        """Delete a note."""
        self.notes = [n for n in self.notes if n.id != note_id]
        self.save()

    def export_notes(self) -> str:
        """Export all notes as formatted text."""
        lines = ["ACB Link Quick Notes", "=" * 40, ""]

        for note in self.notes:
            mins = note.position_seconds // 60
            secs = note.position_seconds % 60

            lines.append(f"Content: {note.content_name}")
            if note.episode_title:
                lines.append(f"Episode: {note.episode_title}")
            lines.append(f"Position: {mins}:{secs:02d}")
            lines.append(f"Note: {note.text}")
            try:
                dt = datetime.fromisoformat(note.created_at)
                lines.append(f"Created: {dt.strftime('%Y-%m-%d %H:%M')}")
            except Exception:
                pass
            lines.append("-" * 40)
            lines.append("")

        return "\n".join(lines)


class QuickNotesDialog(wx.Dialog):
    """Dialog for viewing and adding quick notes."""

    def __init__(
        self,
        parent: wx.Window,
        notes_manager: QuickNotesManager,
        content_type: str = "",
        content_name: str = "",
        current_position: int = 0,
        episode_title: str = "",
        on_jump_to: Optional[Callable[[int], None]] = None,
    ):
        super().__init__(
            parent, title="Quick Notes", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        self.manager = notes_manager
        self.content_type = content_type
        self.content_name = content_name
        self.episode_title = episode_title
        self.current_position = current_position
        self.on_jump_to = on_jump_to

        self.SetSize((550, 450))  # type: ignore[arg-type]
        self._create_ui()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Add note section
        add_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.note_entry = wx.TextCtrl(panel, size=(350, -1))  # type: ignore[arg-type]
        self.note_entry.SetHint("Type a note...")
        self.note_entry.SetName("Note text")

        btn_add = wx.Button(panel, label="&Add Note")
        btn_add.Bind(wx.EVT_BUTTON, self._on_add)

        add_sizer.Add(self.note_entry, 1, wx.RIGHT, 5)
        add_sizer.Add(btn_add, 0)

        main_sizer.Add(add_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Filter
        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.filter_check = wx.CheckBox(panel, label="Show only notes for current content")
        self.filter_check.SetValue(True)
        self.filter_check.Bind(wx.EVT_CHECKBOX, lambda e: self._refresh_list())
        filter_sizer.Add(self.filter_check, 0)
        main_sizer.Add(filter_sizer, 0, wx.LEFT | wx.RIGHT, 10)

        # Notes list
        self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.SetName("Notes list")

        self.list_ctrl.InsertColumn(0, "Time", width=70)
        self.list_ctrl.InsertColumn(1, "Note", width=300)
        self.list_ctrl.InsertColumn(2, "Content", width=130)

        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_jump)

        main_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_jump = wx.Button(panel, label="&Jump to")
        btn_jump.Bind(wx.EVT_BUTTON, self._on_jump)

        btn_delete = wx.Button(panel, label="&Delete")
        btn_delete.Bind(wx.EVT_BUTTON, self._on_delete)

        btn_export = wx.Button(panel, label="&Export All")
        btn_export.Bind(wx.EVT_BUTTON, self._on_export)

        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))

        btn_sizer.Add(btn_jump, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_delete, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_export, 0, wx.RIGHT, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(btn_close, 0)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main_sizer)
        self._refresh_list()

    def _refresh_list(self):
        """Refresh notes list."""
        self.list_ctrl.DeleteAllItems()

        if self.filter_check.GetValue() and self.content_name:
            notes = self.manager.get_notes_for_content(
                self.content_type, self.content_name, self.episode_title
            )
        else:
            notes = self.manager.get_all_notes()

        self._notes = notes

        for i, note in enumerate(notes):
            mins = note.position_seconds // 60
            secs = note.position_seconds % 60

            idx = self.list_ctrl.InsertItem(i, f"{mins}:{secs:02d}")
            self.list_ctrl.SetItem(idx, 1, note.text[:100])
            self.list_ctrl.SetItem(idx, 2, note.content_name[:30])

    def _on_add(self, event):
        """Add a new note."""
        text = self.note_entry.GetValue().strip()
        if not text:
            return

        self.manager.add_note(
            self.content_type, self.content_name, self.current_position, text, self.episode_title
        )

        self.note_entry.Clear()
        self._refresh_list()

    def _on_jump(self, event):
        """Jump to selected note position."""
        idx = self.list_ctrl.GetFirstSelected()
        if idx < 0 or not self.on_jump_to:
            return

        if 0 <= idx < len(self._notes):
            self.on_jump_to(self._notes[idx].position_seconds)

    def _on_delete(self, event):
        """Delete selected note."""
        idx = self.list_ctrl.GetFirstSelected()
        if idx < 0:
            return

        if 0 <= idx < len(self._notes):
            self.manager.delete_note(self._notes[idx].id)
            self._refresh_list()

    def _on_export(self, event):
        """Export notes to file."""
        with wx.FileDialog(
            self,
            "Export Notes",
            wildcard="Text files (*.txt)|*.txt",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                text = self.manager.export_notes()
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                wx.MessageBox(f"Exported to {path}", "Success", wx.OK | wx.ICON_INFORMATION)


# ============================================================================
# CROSSFADE
# ============================================================================


class CrossfadeManager:
    """Manages crossfade between audio tracks."""

    def __init__(
        self,
        get_volume: Callable[[], int],
        set_volume: Callable[[int], None],
        duration_seconds: float = 3.0,
    ):
        self.get_volume = get_volume
        self.set_volume = set_volume
        self.duration_seconds = duration_seconds

        self._enabled = True
        self._original_volume: int = 100
        self._fade_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    def start_fade_out(self, on_complete: Callable[[], None]):
        """Start fading out current track."""
        if not self._enabled:
            on_complete()
            return

        self._original_volume = self.get_volume()
        self._stop_event.clear()

        self._fade_thread = threading.Thread(
            target=self._fade_loop, args=(self._original_volume, 0, on_complete, True), daemon=True
        )
        self._fade_thread.start()

    def start_fade_in(self, target_volume: Optional[int] = None):
        """Start fading in new track."""
        if not self._enabled:
            return

        target = target_volume or self._original_volume
        self._stop_event.clear()

        self._fade_thread = threading.Thread(
            target=self._fade_loop, args=(0, target, None, False), daemon=True
        )
        self._fade_thread.start()

    def _fade_loop(
        self,
        start_vol: int,
        end_vol: int,
        on_complete: Optional[Callable[[], None]],
        is_fade_out: bool,
    ):
        """Execute fade in background."""
        steps = int(self.duration_seconds * 10)
        vol_step = (end_vol - start_vol) / steps
        current_vol = float(start_vol)

        for _ in range(steps):
            if self._stop_event.is_set():
                break

            current_vol += vol_step
            wx.CallAfter(self.set_volume, int(current_vol))
            self._stop_event.wait(0.1)

        if not self._stop_event.is_set():
            wx.CallAfter(self.set_volume, end_vol)
            if on_complete:
                wx.CallAfter(on_complete)

    def cancel(self):
        """Cancel any active fade."""
        self._stop_event.set()
        if self._fade_thread:
            self._fade_thread.join(timeout=0.5)


# ============================================================================
# SMART SPEED
# ============================================================================


class SmartSpeedManager:
    """
    Manages smart speed - dynamically adjusts playback speed during pauses/silence.
    Speeds up during long pauses, maintains normal speed during speech.
    """

    def __init__(
        self,
        get_audio_level: Callable[[], float],
        set_playback_speed: Callable[[float], None],
        base_speed: float = 1.0,
        silence_speed: float = 2.0,
        silence_threshold: float = 0.02,
        min_silence_ms: int = 300,  # Minimum silence before speeding up
    ):
        self.get_audio_level = get_audio_level
        self.set_playback_speed = set_playback_speed
        self.base_speed = base_speed
        self.silence_speed = silence_speed
        self.silence_threshold = silence_threshold
        self.min_silence_ms = min_silence_ms

        self._enabled = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._silence_start: Optional[float] = None
        self._is_fast = False
        self._time_saved_ms: int = 0  # Track time saved

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        if value and not self._enabled:
            self._start_monitoring()
        elif not value and self._enabled:
            self._stop_monitoring()
        self._enabled = value

    @property
    def time_saved_seconds(self) -> float:
        return self._time_saved_ms / 1000.0

    def set_base_speed(self, speed: float):
        """Set the base playback speed."""
        self.base_speed = speed
        if not self._is_fast:
            self.set_playback_speed(speed)

    def _start_monitoring(self):
        """Start monitoring audio levels."""
        self._stop_event.clear()
        self._time_saved_ms = 0
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def _stop_monitoring(self):
        """Stop monitoring."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        self._monitor_thread = None
        self._silence_start = None
        if self._is_fast:
            self._is_fast = False
            wx.CallAfter(self.set_playback_speed, self.base_speed)

    def _monitor_loop(self):
        """Monitor audio in background."""
        while not self._stop_event.is_set():
            try:
                level = self.get_audio_level()
                now = time.time()

                if level < self.silence_threshold:
                    if self._silence_start is None:
                        self._silence_start = now
                    elif (now - self._silence_start) * 1000 >= self.min_silence_ms:
                        if not self._is_fast:
                            self._is_fast = True
                            wx.CallAfter(self.set_playback_speed, self.silence_speed)
                        # Track time saved
                        saved = 100 * (1 - self.base_speed / self.silence_speed)
                        self._time_saved_ms += int(saved)
                else:
                    if self._is_fast:
                        self._is_fast = False
                        wx.CallAfter(self.set_playback_speed, self.base_speed)
                    self._silence_start = None

            except Exception:
                pass

            self._stop_event.wait(0.1)


# ============================================================================
# SOUND CHECK / AUDIO TEST
# ============================================================================


class SoundCheckDialog(wx.Dialog):
    """Dialog for testing audio output with sample tones."""

    FREQUENCIES = [
        (250, "Low (250 Hz)"),
        (500, "Mid-Low (500 Hz)"),
        (1000, "Mid (1000 Hz)"),
        (2000, "Mid-High (2000 Hz)"),
        (4000, "High (4000 Hz)"),
    ]

    def __init__(
        self,
        parent: wx.Window,
        play_tone_callback: Callable[[int, float], None],  # frequency, duration
    ):
        super().__init__(parent, title="Sound Check", style=wx.DEFAULT_DIALOG_STYLE)

        self.play_tone = play_tone_callback
        self._create_ui()
        self.Fit()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        info = wx.StaticText(
            panel,
            label="Test your audio by playing sample tones at different frequencies.\n"
            "Adjust your volume before playing.",
        )
        main_sizer.Add(info, 0, wx.ALL, 10)

        # Frequency buttons
        for freq, label in self.FREQUENCIES:
            btn = wx.Button(panel, label=f"Play {label}")
            btn.Bind(wx.EVT_BUTTON, lambda e, f=freq: self._on_play(f))
            main_sizer.Add(btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Play all button
        btn_all = wx.Button(panel, label="Play &All Tones")
        btn_all.Bind(wx.EVT_BUTTON, self._on_play_all)
        main_sizer.Add(btn_all, 0, wx.EXPAND | wx.ALL, 10)

        # Close button
        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))
        main_sizer.Add(btn_close, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)

    def _on_play(self, frequency: int):
        """Play a single tone."""
        self.play_tone(frequency, 0.5)

    def _on_play_all(self, event):
        """Play all tones in sequence."""

        def play_sequence():
            for freq, _ in self.FREQUENCIES:
                self.play_tone(freq, 0.3)
                time.sleep(0.5)

        thread = threading.Thread(target=play_sequence, daemon=True)
        thread.start()


# ============================================================================
# DOWNLOAD QUEUE MANAGER
# ============================================================================


@dataclass
class DownloadItem:
    """An item in the download queue."""

    id: str
    content_type: str  # "podcast", "stream_recording"
    name: str
    url: str
    file_path: str = ""
    progress: int = 0  # 0-100
    status: str = "queued"  # "queued", "downloading", "completed", "failed", "paused"
    error: str = ""
    added_at: str = ""
    completed_at: str = ""
    size_bytes: int = 0
    downloaded_bytes: int = 0


class DownloadQueueManager:
    """Manages background download queue."""

    MAX_CONCURRENT = 2

    def __init__(
        self,
        download_folder: Optional[str] = None,
        on_progress: Optional[Callable[[str, int], None]] = None,
        on_complete: Optional[Callable[[DownloadItem], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None,
    ):
        self.download_folder = download_folder or str(Path.home() / ".acb_link" / "downloads")
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error

        self.queue: List[DownloadItem] = []
        self._active_downloads: Dict[str, threading.Thread] = {}
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def add_to_queue(
        self, content_type: str, name: str, url: str, filename: str = ""
    ) -> DownloadItem:
        """Add an item to the download queue."""
        item_id = f"dl_{int(time.time() * 1000)}"

        if not filename:
            filename = f"{name.replace(' ', '_')}.mp3"

        item = DownloadItem(
            id=item_id,
            content_type=content_type,
            name=name,
            url=url,
            file_path=str(Path(self.download_folder) / filename),
            added_at=datetime.now().isoformat(),
        )

        with self._lock:
            self.queue.append(item)

        self._process_queue()
        return item

    def remove_from_queue(self, item_id: str):
        """Remove an item from the queue."""
        with self._lock:
            self.queue = [item for item in self.queue if item.id != item_id]

    def pause_download(self, item_id: str):
        """Pause a download."""
        with self._lock:
            for item in self.queue:
                if item.id == item_id:
                    item.status = "paused"
                    break

    def resume_download(self, item_id: str):
        """Resume a paused download."""
        with self._lock:
            for item in self.queue:
                if item.id == item_id and item.status == "paused":
                    item.status = "queued"
                    break
        self._process_queue()

    def get_queue(self) -> List[DownloadItem]:
        """Get current queue."""
        with self._lock:
            return list(self.queue)

    def get_active_count(self) -> int:
        """Get number of active downloads."""
        return sum(1 for item in self.queue if item.status == "downloading")

    def _process_queue(self):
        """Process queued items."""
        with self._lock:
            active = sum(1 for item in self.queue if item.status == "downloading")

            for item in self.queue:
                if active >= self.MAX_CONCURRENT:
                    break
                if item.status == "queued":
                    item.status = "downloading"
                    active += 1
                    self._start_download(item)

    def _start_download(self, item: DownloadItem):
        """Start downloading an item."""
        thread = threading.Thread(target=self._download_worker, args=(item,), daemon=True)
        self._active_downloads[item.id] = thread
        thread.start()

    def _download_worker(self, item: DownloadItem):
        """Download worker thread."""
        try:
            import urllib.request

            Path(self.download_folder).mkdir(parents=True, exist_ok=True)

            # Download with progress tracking
            def progress_hook(block_num, block_size, total_size):
                if total_size > 0:
                    item.size_bytes = total_size
                    item.downloaded_bytes = block_num * block_size
                    item.progress = min(100, int(item.downloaded_bytes / total_size * 100))
                    if self.on_progress:
                        wx.CallAfter(self.on_progress, item.id, item.progress)

            urllib.request.urlretrieve(item.url, item.file_path, progress_hook)

            item.status = "completed"
            item.progress = 100
            item.completed_at = datetime.now().isoformat()

            if self.on_complete:
                wx.CallAfter(self.on_complete, item)

        except Exception as e:
            item.status = "failed"
            item.error = str(e)
            if self.on_error:
                wx.CallAfter(self.on_error, item.id, str(e))

        finally:
            with self._lock:
                if item.id in self._active_downloads:
                    del self._active_downloads[item.id]
            self._process_queue()


class DownloadQueueDialog(wx.Dialog):
    """Dialog for managing download queue."""

    def __init__(self, parent: wx.Window, queue_manager: DownloadQueueManager):
        super().__init__(
            parent, title="Download Queue", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        self.manager = queue_manager
        self.SetSize((550, 400))  # type: ignore[arg-type]
        self._create_ui()
        self.Centre()

        # Start refresh timer
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_refresh, self._timer)
        self._timer.Start(1000)

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Queue list
        self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.SetName("Download queue")

        self.list_ctrl.InsertColumn(0, "Name", width=200)
        self.list_ctrl.InsertColumn(1, "Status", width=100)
        self.list_ctrl.InsertColumn(2, "Progress", width=100)
        self.list_ctrl.InsertColumn(3, "Size", width=100)

        main_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_pause = wx.Button(panel, label="&Pause")
        btn_pause.Bind(wx.EVT_BUTTON, self._on_pause)

        btn_resume = wx.Button(panel, label="&Resume")
        btn_resume.Bind(wx.EVT_BUTTON, self._on_resume)

        btn_remove = wx.Button(panel, label="&Remove")
        btn_remove.Bind(wx.EVT_BUTTON, self._on_remove)

        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, self._on_close)

        btn_sizer.Add(btn_pause, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_resume, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_remove, 0, wx.RIGHT, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(btn_close, 0)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main_sizer)
        self._refresh_list()

    def _refresh_list(self):
        """Refresh the queue list."""
        self.list_ctrl.DeleteAllItems()

        self._queue = self.manager.get_queue()

        for i, item in enumerate(self._queue):
            idx = self.list_ctrl.InsertItem(i, item.name)
            self.list_ctrl.SetItem(idx, 1, item.status.title())
            self.list_ctrl.SetItem(idx, 2, f"{item.progress}%")

            if item.size_bytes > 0:
                size_mb = item.size_bytes / (1024 * 1024)
                self.list_ctrl.SetItem(idx, 3, f"{size_mb:.1f} MB")
            else:
                self.list_ctrl.SetItem(idx, 3, "Unknown")

    def _on_refresh(self, event):
        """Periodic refresh."""
        self._refresh_list()

    def _on_pause(self, event):
        """Pause selected download."""
        idx = self.list_ctrl.GetFirstSelected()
        if 0 <= idx < len(self._queue):
            self.manager.pause_download(self._queue[idx].id)
            self._refresh_list()

    def _on_resume(self, event):
        """Resume selected download."""
        idx = self.list_ctrl.GetFirstSelected()
        if 0 <= idx < len(self._queue):
            self.manager.resume_download(self._queue[idx].id)
            self._refresh_list()

    def _on_remove(self, event):
        """Remove selected download."""
        idx = self.list_ctrl.GetFirstSelected()
        if 0 <= idx < len(self._queue):
            self.manager.remove_from_queue(self._queue[idx].id)
            self._refresh_list()

    def _on_close(self, event):
        """Close dialog."""
        self._timer.Stop()
        self.EndModal(wx.ID_CLOSE)


# ============================================================================
# SOCIAL SHARING
# ============================================================================


class SocialShareManager:
    """Manages sharing to social media platforms."""

    PLATFORMS = {
        "twitter": "https://twitter.com/intent/tweet?text={text}&url={url}",
        "facebook": "https://www.facebook.com/sharer/sharer.php?u={url}&quote={text}",
        "mastodon": "https://mastodon.social/share?text={text}",
        "linkedin": "https://www.linkedin.com/sharing/share-offsite/?url={url}",
        "email": "mailto:?subject={subject}&body={text}%0A%0A{url}",
    }

    @classmethod
    def share(cls, platform: str, text: str, url: str = "", subject: str = ""):
        """Open share dialog for a platform."""
        import urllib.parse
        import webbrowser

        if platform not in cls.PLATFORMS:
            return False

        template = cls.PLATFORMS[platform]
        share_url = template.format(
            text=urllib.parse.quote(text),
            url=urllib.parse.quote(url),
            subject=urllib.parse.quote(subject or "Shared from ACB Link"),
        )

        webbrowser.open(share_url)
        return True

    @classmethod
    def copy_to_clipboard(cls, text: str, url: str = "") -> bool:
        """Copy share text to clipboard."""
        full_text = text
        if url:
            full_text += f"\n\n{url}"

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(full_text))
            wx.TheClipboard.Close()
            return True
        return False


class ShareDialog(wx.Dialog):
    """Dialog for sharing content to social media."""

    def __init__(self, parent: wx.Window, content_name: str, content_url: str = ""):
        super().__init__(parent, title="Share", style=wx.DEFAULT_DIALOG_STYLE)

        self.content_name = content_name
        self.content_url = content_url

        self._create_ui()
        self.Fit()
        self.Centre()

    def _create_ui(self):
        """Create dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Share text
        self.share_text = wx.TextCtrl(
            panel,
            value=f"🎧 Listening to {self.content_name} on ACB Link!",
            style=wx.TE_MULTILINE,
            size=(350, 80),  # type: ignore[arg-type]
        )
        self.share_text.SetName("Share text")
        main_sizer.Add(self.share_text, 0, wx.EXPAND | wx.ALL, 10)

        # Platform buttons
        platforms = [
            ("&Twitter/X", "twitter"),
            ("&Facebook", "facebook"),
            ("&Mastodon", "mastodon"),
            ("&LinkedIn", "linkedin"),
            ("&Email", "email"),
        ]

        btn_grid = wx.GridSizer(rows=2, cols=3, hgap=5, vgap=5)

        for label, platform in platforms:
            btn = wx.Button(panel, label=label)
            btn.Bind(wx.EVT_BUTTON, lambda e, p=platform: self._on_share(p))
            btn_grid.Add(btn, 0, wx.EXPAND)

        # Copy button
        btn_copy = wx.Button(panel, label="&Copy to Clipboard")
        btn_copy.Bind(wx.EVT_BUTTON, self._on_copy)
        btn_grid.Add(btn_copy, 0, wx.EXPAND)

        main_sizer.Add(btn_grid, 0, wx.EXPAND | wx.ALL, 10)

        # Close button
        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))
        main_sizer.Add(btn_close, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)

    def _on_share(self, platform: str):
        """Share to platform."""
        text = self.share_text.GetValue()
        SocialShareManager.share(platform, text, self.content_url)

    def _on_copy(self, event):
        """Copy to clipboard."""
        text = self.share_text.GetValue()
        if SocialShareManager.copy_to_clipboard(text, self.content_url):
            wx.MessageBox("Copied to clipboard!", "Success", wx.OK | wx.ICON_INFORMATION)
