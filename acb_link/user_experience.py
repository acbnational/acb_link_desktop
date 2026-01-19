"""
ACB Link - User Experience Enhancements
Quick status, panic key, resume playback, listening stats, export/backup, 
font size toggle, and first-run wizard.
"""

import json
import os
import time
import wx
import wx.adv
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, Callable


# ============================================================================
# LISTENING STATISTICS
# ============================================================================

@dataclass
class ListeningSession:
    """A single listening session."""
    content_type: str  # "stream" or "podcast"
    content_name: str
    started: str  # ISO format timestamp
    duration_seconds: int = 0


@dataclass
class ListeningStats:
    """User listening statistics."""
    total_listening_seconds: int = 0
    total_sessions: int = 0
    streams_listened: Dict[str, int] = field(default_factory=dict)  # name -> seconds
    podcasts_listened: Dict[str, int] = field(default_factory=dict)  # name -> seconds
    favorite_stream: str = ""
    favorite_podcast: str = ""
    longest_session_seconds: int = 0
    current_streak_days: int = 0
    last_listened_date: str = ""  # YYYY-MM-DD
    first_use_date: str = ""
    
    def __post_init__(self):
        if not self.first_use_date:
            self.first_use_date = datetime.now().strftime("%Y-%m-%d")
    
    def record_session(self, content_type: str, content_name: str, duration_seconds: int):
        """Record a listening session."""
        self.total_listening_seconds += duration_seconds
        self.total_sessions += 1
        
        if duration_seconds > self.longest_session_seconds:
            self.longest_session_seconds = duration_seconds
        
        # Track by content type
        if content_type == "stream":
            self.streams_listened[content_name] = (
                self.streams_listened.get(content_name, 0) + duration_seconds
            )
            # Update favorite
            if not self.favorite_stream or \
               self.streams_listened.get(content_name, 0) > self.streams_listened.get(self.favorite_stream, 0):
                self.favorite_stream = content_name
        else:
            self.podcasts_listened[content_name] = (
                self.podcasts_listened.get(content_name, 0) + duration_seconds
            )
            if not self.favorite_podcast or \
               self.podcasts_listened.get(content_name, 0) > self.podcasts_listened.get(self.favorite_podcast, 0):
                self.favorite_podcast = content_name
        
        # Update streak
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_listened_date:
            last_date = datetime.strptime(self.last_listened_date, "%Y-%m-%d")
            today_date = datetime.strptime(today, "%Y-%m-%d")
            diff = (today_date - last_date).days
            if diff == 1:
                self.current_streak_days += 1
            elif diff > 1:
                self.current_streak_days = 1
        else:
            self.current_streak_days = 1
        self.last_listened_date = today
    
    def get_total_time_formatted(self) -> str:
        """Get total listening time as human-readable string."""
        hours = self.total_listening_seconds // 3600
        minutes = (self.total_listening_seconds % 3600) // 60
        if hours > 0:
            return f"{hours} hours, {minutes} minutes"
        return f"{minutes} minutes"
    
    def get_summary(self) -> str:
        """Get a summary of listening statistics."""
        lines = [
            f"Total listening time: {self.get_total_time_formatted()}",
            f"Total sessions: {self.total_sessions}",
            f"Current streak: {self.current_streak_days} days",
        ]
        if self.favorite_stream:
            lines.append(f"Favorite stream: {self.favorite_stream}")
        if self.favorite_podcast:
            lines.append(f"Favorite podcast: {self.favorite_podcast}")
        return "\n".join(lines)


class ListeningStatsManager:
    """Manages listening statistics persistence."""
    
    def __init__(self, stats_path: Optional[str] = None):
        self.stats_path = stats_path or str(
            Path.home() / ".acb_link" / "listening_stats.json"
        )
        self.stats = self._load()
        self._current_session_start: Optional[float] = None
        self._current_content_type: str = ""
        self._current_content_name: str = ""
    
    def _load(self) -> ListeningStats:
        """Load stats from disk."""
        if os.path.exists(self.stats_path):
            try:
                with open(self.stats_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return ListeningStats(**data)
            except Exception:
                pass
        return ListeningStats()
    
    def save(self):
        """Save stats to disk."""
        Path(self.stats_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.stats_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.stats), f, indent=2)
    
    def start_session(self, content_type: str, content_name: str):
        """Start tracking a listening session."""
        # End previous session if any
        self.end_session()
        
        self._current_session_start = time.time()
        self._current_content_type = content_type
        self._current_content_name = content_name
    
    def end_session(self):
        """End and record the current session."""
        if self._current_session_start:
            duration = int(time.time() - self._current_session_start)
            if duration >= 30:  # Only count sessions > 30 seconds
                self.stats.record_session(
                    self._current_content_type,
                    self._current_content_name,
                    duration
                )
                self.save()
        
        self._current_session_start = None
        self._current_content_type = ""
        self._current_content_name = ""
    
    def get_current_session_duration(self) -> int:
        """Get duration of current session in seconds."""
        if self._current_session_start:
            return int(time.time() - self._current_session_start)
        return 0


# ============================================================================
# RESUME PLAYBACK
# ============================================================================

@dataclass
class LastPlaybackState:
    """State of last playback for resume functionality."""
    content_type: str = ""  # "stream" or "podcast"
    content_name: str = ""
    content_url: str = ""
    position_seconds: int = 0
    timestamp: str = ""  # ISO format
    category: str = ""  # For podcasts
    episode_title: str = ""  # For podcasts


class ResumePlaybackManager:
    """Manages resume playback state."""
    
    def __init__(self, state_path: Optional[str] = None):
        self.state_path = state_path or str(
            Path.home() / ".acb_link" / "last_playback.json"
        )
        self.last_state: Optional[LastPlaybackState] = None
        self._load()
    
    def _load(self):
        """Load last playback state."""
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.last_state = LastPlaybackState(**data)
            except Exception:
                self.last_state = None
    
    def save_state(
        self,
        content_type: str,
        content_name: str,
        content_url: str,
        position_seconds: int = 0,
        category: str = "",
        episode_title: str = ""
    ):
        """Save current playback state."""
        self.last_state = LastPlaybackState(
            content_type=content_type,
            content_name=content_name,
            content_url=content_url,
            position_seconds=position_seconds,
            timestamp=datetime.now().isoformat(),
            category=category,
            episode_title=episode_title
        )
        Path(self.state_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.last_state), f, indent=2)
    
    def has_resumable_content(self) -> bool:
        """Check if there's content to resume."""
        if not self.last_state or not self.last_state.content_name:
            return False
        # Check if it was within the last 7 days
        try:
            last_time = datetime.fromisoformat(self.last_state.timestamp)
            if datetime.now() - last_time > timedelta(days=7):
                return False
        except Exception:
            pass
        return True
    
    def get_resume_description(self) -> str:
        """Get human-readable description of resumable content."""
        if not self.last_state:
            return ""
        
        if self.last_state.content_type == "stream":
            return f"Resume playing {self.last_state.content_name}"
        else:
            desc = f"Resume {self.last_state.content_name}"
            if self.last_state.episode_title:
                desc += f" - {self.last_state.episode_title}"
            if self.last_state.position_seconds > 0:
                mins = self.last_state.position_seconds // 60
                secs = self.last_state.position_seconds % 60
                desc += f" at {mins}:{secs:02d}"
            return desc
    
    def clear(self):
        """Clear saved state."""
        self.last_state = None
        if os.path.exists(self.state_path):
            os.remove(self.state_path)


# ============================================================================
# EXPORT / BACKUP SETTINGS
# ============================================================================

class SettingsBackupManager:
    """Manages export and import of user settings and data."""
    
    def __init__(self, app_data_dir: Optional[str] = None):
        self.app_data_dir = app_data_dir or str(Path.home() / ".acb_link")
    
    def export_all(self, export_path: str) -> bool:
        """
        Export all user data to a ZIP file.
        
        Includes:
        - Settings
        - Favorites
        - Playlists
        - Listening stats
        - Shortcuts
        """
        import zipfile
        
        try:
            files_to_export = [
                (Path.home() / ".acb_link_settings.json", "settings.json"),
                (Path(self.app_data_dir) / "favorites.json", "favorites.json"),
                (Path(self.app_data_dir) / "playlists.json", "playlists.json"),
                (Path(self.app_data_dir) / "listening_stats.json", "listening_stats.json"),
                (Path(self.app_data_dir) / "shortcuts.json", "shortcuts.json"),
                (Path(self.app_data_dir) / "last_playback.json", "last_playback.json"),
            ]
            
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add metadata
                metadata = {
                    "export_date": datetime.now().isoformat(),
                    "version": "2.0",
                    "app": "ACB Link"
                }
                zf.writestr("metadata.json", json.dumps(metadata, indent=2))
                
                # Add each file if it exists
                for source_path, archive_name in files_to_export:
                    if source_path.exists():
                        zf.write(str(source_path), archive_name)
            
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def import_all(self, import_path: str, merge: bool = False) -> tuple:
        """
        Import user data from a ZIP file.
        
        Args:
            import_path: Path to the backup ZIP file
            merge: If True, merge with existing data; if False, replace
            
        Returns:
            Tuple of (success, message)
        """
        import zipfile
        
        try:
            with zipfile.ZipFile(import_path, 'r') as zf:
                # Verify it's an ACB Link backup
                try:
                    metadata = json.loads(zf.read("metadata.json"))
                    if metadata.get("app") != "ACB Link":
                        return False, "Not a valid ACB Link backup file"
                except Exception:
                    return False, "Invalid backup file format"
                
                # Extract files
                Path(self.app_data_dir).mkdir(parents=True, exist_ok=True)
                
                file_mappings = {
                    "settings.json": Path.home() / ".acb_link_settings.json",
                    "favorites.json": Path(self.app_data_dir) / "favorites.json",
                    "playlists.json": Path(self.app_data_dir) / "playlists.json",
                    "listening_stats.json": Path(self.app_data_dir) / "listening_stats.json",
                    "shortcuts.json": Path(self.app_data_dir) / "shortcuts.json",
                    "last_playback.json": Path(self.app_data_dir) / "last_playback.json",
                }
                
                restored_count = 0
                for archive_name, dest_path in file_mappings.items():
                    if archive_name in zf.namelist():
                        content = zf.read(archive_name)
                        
                        if merge and dest_path.exists():
                            # Merge logic for specific file types
                            # For now, just replace
                            pass
                        
                        with open(dest_path, 'wb') as f:
                            f.write(content)
                        restored_count += 1
                
                return True, f"Successfully restored {restored_count} items"
                
        except zipfile.BadZipFile:
            return False, "Invalid or corrupted backup file"
        except Exception as e:
            return False, f"Import error: {e}"
    
    def get_backup_info(self, backup_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a backup file."""
        import zipfile
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zf:
                metadata = json.loads(zf.read("metadata.json"))
                metadata["files"] = [f for f in zf.namelist() if f != "metadata.json"]
                return metadata
        except Exception:
            return None


# ============================================================================
# QUICK STATUS ANNOUNCEMENT
# ============================================================================

class QuickStatusAnnouncer:
    """Provides quick status announcements for screen reader users."""
    
    def __init__(
        self,
        get_playback_state: Callable,
        get_volume: Callable,
        get_current_content: Callable,
        announcer: Callable[[str], None]
    ):
        self.get_playback_state = get_playback_state
        self.get_volume = get_volume
        self.get_current_content = get_current_content
        self.announcer = announcer
    
    def announce_status(self):
        """Announce current playback status."""
        content = self.get_current_content()
        state = self.get_playback_state()
        volume = self.get_volume()
        
        parts = []
        
        # Playback state
        if state == "playing":
            parts.append("Playing")
        elif state == "paused":
            parts.append("Paused")
        else:
            parts.append("Stopped")
        
        # Content name
        if content:
            parts.append(content)
        else:
            parts.append("No content selected")
        
        # Volume
        parts.append(f"Volume {volume} percent")
        
        message = ". ".join(parts)
        self.announcer(message)
        return message


# ============================================================================
# PANIC / BOSS KEY
# ============================================================================

class PanicKeyHandler:
    """Handles panic/boss key functionality."""
    
    def __init__(
        self,
        mute_callback: Callable,
        minimize_callback: Callable,
        is_muted_callback: Callable
    ):
        self.mute_callback = mute_callback
        self.minimize_callback = minimize_callback
        self.is_muted_callback = is_muted_callback
        self._was_muted_before_panic = False
    
    def activate(self):
        """Activate panic mode - mute and minimize."""
        self._was_muted_before_panic = self.is_muted_callback()
        if not self._was_muted_before_panic:
            self.mute_callback()
        self.minimize_callback()
    
    def restore(self):
        """Restore from panic mode."""
        if not self._was_muted_before_panic:
            self.mute_callback()  # Unmute


# ============================================================================
# FONT SIZE QUICK TOGGLE
# ============================================================================

class FontSizeManager:
    """Manages quick font size adjustments."""
    
    MIN_SIZE = 8
    MAX_SIZE = 24
    STEP = 2
    
    def __init__(self, current_size: int, on_size_changed: Callable[[int], None]):
        self.current_size = current_size
        self.on_size_changed = on_size_changed
    
    def increase(self) -> int:
        """Increase font size."""
        if self.current_size < self.MAX_SIZE:
            self.current_size = min(self.current_size + self.STEP, self.MAX_SIZE)
            self.on_size_changed(self.current_size)
        return self.current_size
    
    def decrease(self) -> int:
        """Decrease font size."""
        if self.current_size > self.MIN_SIZE:
            self.current_size = max(self.current_size - self.STEP, self.MIN_SIZE)
            self.on_size_changed(self.current_size)
        return self.current_size
    
    def reset(self) -> int:
        """Reset to default size."""
        self.current_size = 12
        self.on_size_changed(self.current_size)
        return self.current_size


# ============================================================================
# HIGH CONTRAST THEME PRESETS
# ============================================================================

HIGH_CONTRAST_PRESETS = {
    "Yellow on Black": {
        "name": "yellow_on_black",
        "background": "#000000",
        "foreground": "#FFFF00",
        "accent": "#00FFFF",
        "description": "Bright yellow text on black background"
    },
    "White on Black": {
        "name": "white_on_black",
        "background": "#000000",
        "foreground": "#FFFFFF",
        "accent": "#00FF00",
        "description": "White text on black background"
    },
    "Black on White": {
        "name": "black_on_white",
        "background": "#FFFFFF",
        "foreground": "#000000",
        "accent": "#0000FF",
        "description": "Black text on white background"
    },
    "Green on Black": {
        "name": "green_on_black",
        "background": "#000000",
        "foreground": "#00FF00",
        "accent": "#FFFF00",
        "description": "Green text on black (terminal style)"
    },
    "Amber on Black": {
        "name": "amber_on_black",
        "background": "#000000",
        "foreground": "#FFBF00",
        "accent": "#FF6600",
        "description": "Amber/orange text on black"
    },
    "Blue on White": {
        "name": "blue_on_white",
        "background": "#FFFFFF",
        "foreground": "#000080",
        "accent": "#0000FF",
        "description": "Dark blue text on white"
    },
}


# ============================================================================
# FIRST-RUN WELCOME WIZARD
# ============================================================================

class WelcomeWizard(wx.Dialog):
    """First-run welcome wizard for new users."""
    
    def __init__(self, parent: Optional[wx.Window] = None, settings=None):
        super().__init__(
            parent,
            title="Welcome to ACB Link",
            style=wx.DEFAULT_DIALOG_STYLE
        )
        
        self.settings = settings
        self.selected_theme = "light"
        self.selected_stream = "ACB Radio Main"
        self.enable_voice = False
        self.enable_announcements = True
        
        self.SetSize((550, 500))  # type: ignore[arg-type]
        self._create_ui()
        self.Centre()
    
    def _create_ui(self):
        """Create the wizard UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Welcome header
        header = wx.StaticText(panel, label="Welcome to ACB Link!")
        header_font = header.GetFont()
        header_font.SetPointSize(16)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        main_sizer.Add(header, 0, wx.ALL | wx.ALIGN_CENTER, 15)
        
        intro = wx.StaticText(
            panel,
            label="Let's set up ACB Link for the best experience.\n"
                  "You can change any of these settings later."
        )
        intro.Wrap(500)
        main_sizer.Add(intro, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        
        # Create notebook for wizard pages
        self.notebook = wx.Notebook(panel)
        
        # Page 1: Theme selection
        theme_page = self._create_theme_page(self.notebook)
        self.notebook.AddPage(theme_page, "Appearance")
        
        # Page 2: Default stream
        stream_page = self._create_stream_page(self.notebook)
        self.notebook.AddPage(stream_page, "Default Stream")
        
        # Page 3: Accessibility
        access_page = self._create_accessibility_page(self.notebook)
        self.notebook.AddPage(access_page, "Accessibility")
        
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 10)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_back = wx.Button(panel, label="&Back")
        self.btn_back.Bind(wx.EVT_BUTTON, self._on_back)
        self.btn_back.Enable(False)
        
        self.btn_next = wx.Button(panel, label="&Next")
        self.btn_next.Bind(wx.EVT_BUTTON, self._on_next)
        
        self.btn_finish = wx.Button(panel, label="&Finish")
        self.btn_finish.Bind(wx.EVT_BUTTON, self._on_finish)
        self.btn_finish.Hide()
        
        btn_skip = wx.Button(panel, label="&Skip Setup")
        btn_skip.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))
        
        btn_sizer.Add(btn_skip, 0, wx.RIGHT, 10)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(self.btn_back, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_next, 0)
        btn_sizer.Add(self.btn_finish, 0)
        
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        
        # Bind page change
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_page_changed)
    
    def _create_theme_page(self, parent) -> wx.Panel:
        """Create theme selection page."""
        page = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(page, label="Choose a visual theme:")
        sizer.Add(label, 0, wx.ALL, 10)
        
        themes = [
            ("Light", "light", "Standard light theme"),
            ("Dark", "dark", "Dark theme, easier on the eyes"),
            ("High Contrast Light", "high_contrast_light", "Maximum contrast, light background"),
            ("High Contrast Dark", "high_contrast_dark", "Maximum contrast, dark background"),
            ("Yellow on Black", "yellow_on_black", "Yellow text on black, high visibility"),
        ]
        
        self.theme_radio = wx.RadioBox(
            page,
            choices=[t[0] for t in themes],
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS
        )
        self.theme_radio.SetName("Theme selection")
        self.theme_radio.Bind(wx.EVT_RADIOBOX, self._on_theme_selected)
        sizer.Add(self.theme_radio, 0, wx.ALL | wx.EXPAND, 10)
        
        self._theme_values = [t[1] for t in themes]
        
        # Font size
        font_label = wx.StaticText(page, label="Text size:")
        sizer.Add(font_label, 0, wx.LEFT | wx.TOP, 10)
        
        self.font_slider = wx.Slider(
            page, value=12, minValue=8, maxValue=24,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS
        )
        self.font_slider.SetName("Text size")
        sizer.Add(self.font_slider, 0, wx.ALL | wx.EXPAND, 10)
        
        page.SetSizer(sizer)
        return page
    
    def _create_stream_page(self, parent) -> wx.Panel:
        """Create default stream selection page."""
        page = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(page, label="Choose your default stream:")
        sizer.Add(label, 0, wx.ALL, 10)
        
        streams = [
            "ACB Radio Main",
            "ACB Radio Treasure Trove",
            "ACB Radio Cafe",
            "ACB Radio World",
            "ACB Radio Interactive",
        ]
        
        self.stream_list = wx.ListBox(page, choices=streams)
        self.stream_list.SetSelection(0)
        self.stream_list.SetName("Default stream")
        self.stream_list.Bind(wx.EVT_LISTBOX, self._on_stream_selected)
        sizer.Add(self.stream_list, 1, wx.ALL | wx.EXPAND, 10)
        
        hint = wx.StaticText(
            page,
            label="This stream will be highlighted on the home screen.\n"
                  "You can play any stream at any time."
        )
        hint.Wrap(400)
        sizer.Add(hint, 0, wx.ALL, 10)
        
        page.SetSizer(sizer)
        return page
    
    def _create_accessibility_page(self, parent) -> wx.Panel:
        """Create accessibility settings page."""
        page = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(page, label="Accessibility options:")
        sizer.Add(label, 0, wx.ALL, 10)
        
        self.chk_announcements = wx.CheckBox(
            page, label="&Enable screen reader announcements"
        )
        self.chk_announcements.SetValue(True)
        self.chk_announcements.SetName("Screen reader announcements")
        sizer.Add(self.chk_announcements, 0, wx.ALL, 10)
        
        self.chk_voice = wx.CheckBox(
            page, label="Enable &voice control (say commands to control playback)"
        )
        self.chk_voice.SetValue(False)
        self.chk_voice.SetName("Voice control")
        sizer.Add(self.chk_voice, 0, wx.ALL, 10)
        
        self.chk_audio_feedback = wx.CheckBox(
            page, label="Play &audio feedback sounds"
        )
        self.chk_audio_feedback.SetValue(True)
        self.chk_audio_feedback.SetName("Audio feedback")
        sizer.Add(self.chk_audio_feedback, 0, wx.ALL, 10)
        
        # Keyboard shortcuts hint
        shortcuts_hint = wx.StaticText(
            page,
            label="\nQuick keyboard shortcuts:\n"
                  "• Space: Play/Pause\n"
                  "• F5: Announce current status\n"
                  "• Ctrl+Shift+M: Panic key (mute and minimize)\n"
                  "• Ctrl+Plus/Minus: Adjust text size\n"
                  "• F1: Open user guide"
        )
        sizer.Add(shortcuts_hint, 0, wx.ALL, 10)
        
        page.SetSizer(sizer)
        return page
    
    def _on_theme_selected(self, event):
        """Handle theme selection."""
        idx = self.theme_radio.GetSelection()
        self.selected_theme = self._theme_values[idx]
    
    def _on_stream_selected(self, event):
        """Handle stream selection."""
        self.selected_stream = self.stream_list.GetStringSelection()
    
    def _on_page_changed(self, event):
        """Handle page change."""
        page = self.notebook.GetSelection()
        total_pages = self.notebook.GetPageCount()
        
        self.btn_back.Enable(page > 0)
        
        if page == total_pages - 1:
            self.btn_next.Hide()
            self.btn_finish.Show()
        else:
            self.btn_next.Show()
            self.btn_finish.Hide()
        
        self.Layout()
        event.Skip()
    
    def _on_back(self, event):
        """Go to previous page."""
        current = self.notebook.GetSelection()
        if current > 0:
            self.notebook.SetSelection(current - 1)
    
    def _on_next(self, event):
        """Go to next page."""
        current = self.notebook.GetSelection()
        if current < self.notebook.GetPageCount() - 1:
            self.notebook.SetSelection(current + 1)
    
    def _on_finish(self, event):
        """Finish wizard and apply settings."""
        self.enable_voice = self.chk_voice.GetValue()
        self.enable_announcements = self.chk_announcements.GetValue()
        self.EndModal(wx.ID_OK)
    
    def get_settings(self) -> Dict[str, Any]:
        """Get the configured settings."""
        return {
            "theme": self.selected_theme,
            "font_size": self.font_slider.GetValue(),
            "default_stream": self.selected_stream,
            "voice_control": self.enable_voice,
            "screen_reader_announcements": self.enable_announcements,
            "audio_feedback": self.chk_audio_feedback.GetValue(),
        }


# ============================================================================
# DIALOGS
# ============================================================================

class ListeningStatsDialog(wx.Dialog):
    """Dialog showing listening statistics."""
    
    def __init__(self, parent: wx.Window, stats: ListeningStats):
        super().__init__(
            parent,
            title="Listening Statistics",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.stats = stats
        self.SetSize((450, 400))  # type: ignore[arg-type]
        self._create_ui()
        self.Centre()
    
    def _create_ui(self):
        """Create the dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header
        header = wx.StaticText(panel, label="Your Listening Statistics")
        header_font = header.GetFont()
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        main_sizer.Add(header, 0, wx.ALL, 15)
        
        # Stats grid
        grid = wx.FlexGridSizer(cols=2, hgap=20, vgap=10)
        
        stats_items = [
            ("Total Listening Time:", self.stats.get_total_time_formatted()),
            ("Total Sessions:", str(self.stats.total_sessions)),
            ("Current Streak:", f"{self.stats.current_streak_days} days"),
            ("Longest Session:", f"{self.stats.longest_session_seconds // 60} minutes"),
            ("Favorite Stream:", self.stats.favorite_stream or "None yet"),
            ("Favorite Podcast:", self.stats.favorite_podcast or "None yet"),
            ("Member Since:", self.stats.first_use_date),
        ]
        
        for label, value in stats_items:
            label_ctrl = wx.StaticText(panel, label=label)
            label_ctrl.SetFont(label_ctrl.GetFont().Bold())
            grid.Add(label_ctrl, 0, wx.ALIGN_RIGHT)
            
            value_ctrl = wx.StaticText(panel, label=value)
            grid.Add(value_ctrl, 0)
        
        main_sizer.Add(grid, 0, wx.ALL | wx.EXPAND, 15)
        
        # Top streams
        if self.stats.streams_listened:
            main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 5)
            
            streams_label = wx.StaticText(panel, label="Top Streams:")
            streams_label.SetFont(streams_label.GetFont().Bold())
            main_sizer.Add(streams_label, 0, wx.LEFT | wx.TOP, 15)
            
            sorted_streams = sorted(
                self.stats.streams_listened.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for name, seconds in sorted_streams:
                hours = seconds // 3600
                mins = (seconds % 3600) // 60
                time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                item = wx.StaticText(panel, label=f"  • {name}: {time_str}")
                main_sizer.Add(item, 0, wx.LEFT, 20)
        
        main_sizer.AddStretchSpacer()
        
        # Close button
        btn_close = wx.Button(panel, wx.ID_CLOSE, label="&Close")
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
        btn_close.SetDefault()
        main_sizer.Add(btn_close, 0, wx.ALL | wx.ALIGN_CENTER, 15)
        
        panel.SetSizer(main_sizer)


class ExportImportDialog(wx.Dialog):
    """Dialog for exporting and importing settings."""
    
    def __init__(self, parent: wx.Window, backup_manager: SettingsBackupManager):
        super().__init__(
            parent,
            title="Export / Import Settings",
            style=wx.DEFAULT_DIALOG_STYLE
        )
        
        self.backup_manager = backup_manager
        self.SetSize((450, 300))  # type: ignore[arg-type]
        self._create_ui()
        self.Centre()
    
    def _create_ui(self):
        """Create the dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Description
        desc = wx.StaticText(
            panel,
            label="Export your settings, favorites, and playlists to a backup file,\n"
                  "or import from a previous backup."
        )
        main_sizer.Add(desc, 0, wx.ALL, 15)
        
        # Export section
        export_box = wx.StaticBox(panel, label="Export")
        export_sizer = wx.StaticBoxSizer(export_box, wx.VERTICAL)
        
        export_desc = wx.StaticText(
            panel,
            label="Create a backup of all your settings and data."
        )
        export_sizer.Add(export_desc, 0, wx.ALL, 5)
        
        btn_export = wx.Button(panel, label="&Export Backup...")
        btn_export.Bind(wx.EVT_BUTTON, self._on_export)
        export_sizer.Add(btn_export, 0, wx.ALL, 5)
        
        main_sizer.Add(export_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Import section
        import_box = wx.StaticBox(panel, label="Import")
        import_sizer = wx.StaticBoxSizer(import_box, wx.VERTICAL)
        
        import_desc = wx.StaticText(
            panel,
            label="Restore settings from a backup file."
        )
        import_sizer.Add(import_desc, 0, wx.ALL, 5)
        
        btn_import = wx.Button(panel, label="&Import Backup...")
        btn_import.Bind(wx.EVT_BUTTON, self._on_import)
        import_sizer.Add(btn_import, 0, wx.ALL, 5)
        
        main_sizer.Add(import_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Close button
        main_sizer.AddStretchSpacer()
        btn_close = wx.Button(panel, wx.ID_CLOSE)
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
        main_sizer.Add(btn_close, 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        
        panel.SetSizer(main_sizer)
    
    def _on_export(self, event):
        """Handle export button."""
        with wx.FileDialog(
            self,
            "Export Backup",
            wildcard="ACB Link Backup (*.acbbackup)|*.acbbackup",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            defaultFile=f"acblink_backup_{datetime.now().strftime('%Y%m%d')}.acbbackup"
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                path = dialog.GetPath()
                if self.backup_manager.export_all(path):
                    wx.MessageBox(
                        f"Backup exported successfully to:\n{path}",
                        "Export Complete",
                        wx.OK | wx.ICON_INFORMATION
                    )
                else:
                    wx.MessageBox(
                        "Failed to export backup. Please try again.",
                        "Export Error",
                        wx.OK | wx.ICON_ERROR
                    )
    
    def _on_import(self, event):
        """Handle import button."""
        with wx.FileDialog(
            self,
            "Import Backup",
            wildcard="ACB Link Backup (*.acbbackup)|*.acbbackup|All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                path = dialog.GetPath()
                
                # Confirm before importing
                info = self.backup_manager.get_backup_info(path)
                if not info:
                    wx.MessageBox(
                        "This doesn't appear to be a valid ACB Link backup file.",
                        "Invalid Backup",
                        wx.OK | wx.ICON_ERROR
                    )
                    return
                
                msg = (
                    f"This backup was created on {info.get('export_date', 'unknown date')}.\n\n"
                    f"Importing will replace your current settings.\n"
                    f"Do you want to continue?"
                )
                if wx.MessageBox(msg, "Confirm Import", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
                    success, message = self.backup_manager.import_all(path)
                    if success:
                        wx.MessageBox(
                            f"{message}\n\nPlease restart ACB Link for changes to take effect.",
                            "Import Complete",
                            wx.OK | wx.ICON_INFORMATION
                        )
                    else:
                        wx.MessageBox(
                            f"Import failed: {message}",
                            "Import Error",
                            wx.OK | wx.ICON_ERROR
                        )


class ResumePlaybackDialog(wx.Dialog):
    """Dialog asking user if they want to resume playback."""
    
    def __init__(self, parent: wx.Window, resume_manager: ResumePlaybackManager):
        super().__init__(
            parent,
            title="Resume Playback",
            style=wx.DEFAULT_DIALOG_STYLE
        )
        
        self.resume_manager = resume_manager
        self._create_ui()
        self.Centre()
    
    def _create_ui(self):
        """Create the dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Message
        desc = self.resume_manager.get_resume_description()
        msg = wx.StaticText(panel, label=f"Would you like to resume?\n\n{desc}")
        msg.Wrap(350)
        main_sizer.Add(msg, 0, wx.ALL, 20)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        btn_resume = wx.Button(panel, wx.ID_YES, label="&Resume")
        btn_resume.SetDefault()
        
        btn_no = wx.Button(panel, wx.ID_NO, label="&Start Fresh")
        
        btn_sizer.Add(btn_resume, 0, wx.RIGHT, 10)
        btn_sizer.Add(btn_no, 0)
        
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 15)
        
        panel.SetSizer(main_sizer)
        self.Fit()


# ============================================================================
# FIRST RUN CHECK
# ============================================================================

def is_first_run() -> bool:
    """Check if this is the first run of the application."""
    marker_path = Path.home() / ".acb_link" / ".first_run_complete"
    return not marker_path.exists()


def mark_first_run_complete():
    """Mark that first run is complete."""
    marker_path = Path.home() / ".acb_link" / ".first_run_complete"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.touch()


def show_welcome_wizard_if_needed(parent: wx.Window, settings) -> Optional[Dict[str, Any]]:
    """Show welcome wizard if this is the first run."""
    if is_first_run():
        wizard = WelcomeWizard(parent, settings)
        if wizard.ShowModal() == wx.ID_OK:
            result = wizard.get_settings()
            mark_first_run_complete()
            wizard.Destroy()
            return result
        wizard.Destroy()
        mark_first_run_complete()  # Mark complete even if skipped
    return None
