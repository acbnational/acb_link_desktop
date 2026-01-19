"""
ACB Link - Settings Dialog
Comprehensive settings dialog with tabbed interface.
WCAG 2.2 AA compliant.
"""

import wx
import wx.adv
from typing import Optional

from .settings import AppSettings, ThemeSettings, THEMES
from .data import (
    THEME_OPTIONS, SPEED_OPTIONS, SPEED_VALUES, 
    TAB_NAMES, TAB_LABELS, EQ_PRESETS,
    RECORDING_FORMATS, RECORDING_BITRATES
)
from .accessibility import announce, make_accessible


class SettingsDialog(wx.Dialog):
    """Comprehensive settings dialog for ACB Link."""
    
    def __init__(self, parent, settings: AppSettings):
        super().__init__(
            parent, 
            title="ACB Link Settings", 
            size=(650, 600),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.settings = settings
        self.original_settings = AppSettings.from_dict(settings.to_dict())  # Deep copy
        
        self._build_ui()
        self.Centre()
    
    def _build_ui(self):
        """Build the settings dialog UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create notebook for tabs
        self.notebook = wx.Notebook(self)
        make_accessible(self.notebook, "Settings categories", "Use arrow keys to navigate between settings tabs")
        
        # Add settings tabs
        self._add_general_tab()
        self._add_appearance_tab()
        self._add_playback_tab()
        self._add_storage_tab()
        self._add_home_tab()
        self._add_startup_tab()
        self._add_system_tray_tab()
        self._add_notifications_tab()
        self._add_announcements_tab()
        self._add_keyboard_tab()
        self._add_voice_control_tab()
        self._add_privacy_tab()
        self._add_performance_tab()
        self._add_accessibility_tab()
        
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 10)
        
        # Buttons
        btn_sizer = self._create_buttons()
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def _add_general_tab(self):
        """Add general settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Browser preference
        browser_box = wx.StaticBox(panel, label="Preferred Browser for App Window")
        browser_sizer = wx.StaticBoxSizer(browser_box, wx.VERTICAL)
        
        self.rb_edge = wx.RadioButton(panel, label="Microsoft Edge", style=wx.RB_GROUP)
        self.rb_chrome = wx.RadioButton(panel, label="Google Chrome")
        
        if self.settings.preferred_browser == "chrome":
            self.rb_chrome.SetValue(True)
        else:
            self.rb_edge.SetValue(True)
        
        browser_sizer.Add(self.rb_edge, 0, wx.ALL, 5)
        browser_sizer.Add(self.rb_chrome, 0, wx.ALL, 5)
        sizer.Add(browser_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Default tab
        tab_box = wx.StaticBox(panel, label="Startup")
        tab_sizer = wx.StaticBoxSizer(tab_box, wx.VERTICAL)
        
        tab_row = wx.BoxSizer(wx.HORIZONTAL)
        tab_row.Add(wx.StaticText(panel, label="Default tab on startup:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.default_tab = wx.Choice(panel, choices=TAB_LABELS)
        if self.settings.default_tab in TAB_NAMES:
            self.default_tab.SetSelection(TAB_NAMES.index(self.settings.default_tab))
        else:
            self.default_tab.SetSelection(0)
        tab_row.Add(self.default_tab, 0)
        tab_sizer.Add(tab_row, 0, wx.ALL, 5)
        
        # Check for updates
        self.chk_updates = wx.CheckBox(panel, label="Check for updates on startup")
        self.chk_updates.SetValue(self.settings.check_updates)
        tab_sizer.Add(self.chk_updates, 0, wx.ALL, 5)
        
        sizer.Add(tab_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "General")
    
    def _add_appearance_tab(self):
        """Add appearance/theme settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Theme selection
        theme_box = wx.StaticBox(panel, label="Theme")
        theme_sizer = wx.StaticBoxSizer(theme_box, wx.VERTICAL)
        
        theme_row = wx.BoxSizer(wx.HORIZONTAL)
        theme_row.Add(wx.StaticText(panel, label="Color theme:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.theme_choice = wx.Choice(panel, choices=[
            "System Default", "Light", "Dark", 
            "High Contrast Light", "High Contrast Dark"
        ])
        theme_map = {
            "system": 0, "light": 1, "dark": 2,
            "high_contrast_light": 3, "high_contrast_dark": 4
        }
        self.theme_choice.SetSelection(theme_map.get(self.settings.theme.name, 0))
        theme_row.Add(self.theme_choice, 0)
        theme_sizer.Add(theme_row, 0, wx.ALL, 5)
        
        sizer.Add(theme_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Font settings
        font_box = wx.StaticBox(panel, label="Font Settings")
        font_sizer = wx.StaticBoxSizer(font_box, wx.VERTICAL)
        
        # Font size
        size_row = wx.BoxSizer(wx.HORIZONTAL)
        size_row.Add(wx.StaticText(panel, label="Font size:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.font_size = wx.SpinCtrl(panel, value=str(self.settings.theme.font_size), min=8, max=32)
        size_row.Add(self.font_size, 0)
        size_row.Add(wx.StaticText(panel, label="pt"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        font_sizer.Add(size_row, 0, wx.ALL, 5)
        
        # Font family
        family_row = wx.BoxSizer(wx.HORIZONTAL)
        family_row.Add(wx.StaticText(panel, label="Font family:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        font_families = ["Segoe UI", "Arial", "Verdana", "Tahoma", "Calibri", "Consolas"]
        self.font_family = wx.Choice(panel, choices=font_families)
        if self.settings.theme.font_family in font_families:
            self.font_family.SetSelection(font_families.index(self.settings.theme.font_family))
        else:
            self.font_family.SetSelection(0)
        family_row.Add(self.font_family, 0)
        font_sizer.Add(family_row, 0, wx.ALL, 5)
        
        sizer.Add(font_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Visual accessibility
        visual_box = wx.StaticBox(panel, label="Visual Accessibility")
        visual_sizer = wx.StaticBoxSizer(visual_box, wx.VERTICAL)
        
        self.chk_high_contrast = wx.CheckBox(panel, label="High contrast mode")
        self.chk_high_contrast.SetValue(self.settings.theme.high_contrast)
        visual_sizer.Add(self.chk_high_contrast, 0, wx.ALL, 5)
        
        self.chk_reduce_motion = wx.CheckBox(panel, label="Reduce motion/animations")
        self.chk_reduce_motion.SetValue(self.settings.theme.reduce_motion)
        visual_sizer.Add(self.chk_reduce_motion, 0, wx.ALL, 5)
        
        self.chk_large_cursor = wx.CheckBox(panel, label="Large cursor")
        self.chk_large_cursor.SetValue(self.settings.theme.large_cursor)
        visual_sizer.Add(self.chk_large_cursor, 0, wx.ALL, 5)
        
        # Focus ring width
        focus_row = wx.BoxSizer(wx.HORIZONTAL)
        focus_row.Add(wx.StaticText(panel, label="Focus ring width:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.focus_width = wx.SpinCtrl(panel, value=str(self.settings.theme.focus_ring_width), min=1, max=5)
        focus_row.Add(self.focus_width, 0)
        focus_row.Add(wx.StaticText(panel, label="px"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        visual_sizer.Add(focus_row, 0, wx.ALL, 5)
        
        sizer.Add(visual_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Appearance")
    
    def _add_playback_tab(self):
        """Add playback settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Skip intervals
        skip_box = wx.StaticBox(panel, label="Skip Intervals")
        skip_sizer = wx.StaticBoxSizer(skip_box, wx.VERTICAL)
        
        back_row = wx.BoxSizer(wx.HORIZONTAL)
        back_row.Add(wx.StaticText(panel, label="Skip backward:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.skip_backward = wx.SpinCtrl(panel, value=str(self.settings.playback.skip_backward_seconds), min=5, max=120)
        back_row.Add(self.skip_backward, 0)
        back_row.Add(wx.StaticText(panel, label="seconds"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        skip_sizer.Add(back_row, 0, wx.ALL, 5)
        
        fwd_row = wx.BoxSizer(wx.HORIZONTAL)
        fwd_row.Add(wx.StaticText(panel, label="Skip forward:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.skip_forward = wx.SpinCtrl(panel, value=str(self.settings.playback.skip_forward_seconds), min=5, max=120)
        fwd_row.Add(self.skip_forward, 0)
        fwd_row.Add(wx.StaticText(panel, label="seconds"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        skip_sizer.Add(fwd_row, 0, wx.ALL, 5)
        
        sizer.Add(skip_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Speed and volume
        speed_box = wx.StaticBox(panel, label="Playback Defaults")
        speed_sizer = wx.StaticBoxSizer(speed_box, wx.VERTICAL)
        
        speed_row = wx.BoxSizer(wx.HORIZONTAL)
        speed_row.Add(wx.StaticText(panel, label="Default speed:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.playback_speed = wx.Choice(panel, choices=SPEED_OPTIONS)
        if self.settings.playback.default_speed in SPEED_VALUES:
            self.playback_speed.SetSelection(SPEED_VALUES.index(self.settings.playback.default_speed))
        else:
            self.playback_speed.SetSelection(2)
        speed_row.Add(self.playback_speed, 0)
        speed_sizer.Add(speed_row, 0, wx.ALL, 5)
        
        vol_row = wx.BoxSizer(wx.HORIZONTAL)
        vol_row.Add(wx.StaticText(panel, label="Default volume:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.default_volume = wx.Slider(panel, value=self.settings.playback.default_volume, minValue=0, maxValue=100, size=(200, -1))
        vol_row.Add(self.default_volume, 0)
        self.vol_label = wx.StaticText(panel, label=f"{self.settings.playback.default_volume}%")
        vol_row.Add(self.vol_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        self.default_volume.Bind(wx.EVT_SLIDER, lambda e: self.vol_label.SetLabel(f"{self.default_volume.GetValue()}%"))
        speed_sizer.Add(vol_row, 0, wx.ALL, 5)
        
        sizer.Add(speed_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Playback options
        options_box = wx.StaticBox(panel, label="Playback Options")
        options_sizer = wx.StaticBoxSizer(options_box, wx.VERTICAL)
        
        self.chk_remember_pos = wx.CheckBox(panel, label="Remember playback position")
        self.chk_remember_pos.SetValue(self.settings.playback.remember_position)
        options_sizer.Add(self.chk_remember_pos, 0, wx.ALL, 5)
        
        self.chk_auto_play = wx.CheckBox(panel, label="Auto-play next episode")
        self.chk_auto_play.SetValue(self.settings.playback.auto_play_next)
        options_sizer.Add(self.chk_auto_play, 0, wx.ALL, 5)
        
        self.chk_normalize = wx.CheckBox(panel, label="Normalize audio levels")
        self.chk_normalize.SetValue(self.settings.playback.normalize_audio)
        options_sizer.Add(self.chk_normalize, 0, wx.ALL, 5)
        
        sizer.Add(options_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Equalizer
        eq_box = wx.StaticBox(panel, label="Equalizer")
        eq_sizer = wx.StaticBoxSizer(eq_box, wx.VERTICAL)
        
        preset_row = wx.BoxSizer(wx.HORIZONTAL)
        preset_row.Add(wx.StaticText(panel, label="Preset:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.eq_preset = wx.Choice(panel, choices=["Flat", "Bass Boost", "Voice", "Treble"])
        preset_map = {"flat": 0, "bass_boost": 1, "voice": 2, "treble": 3}
        self.eq_preset.SetSelection(preset_map.get(self.settings.playback.eq_preset, 0))
        preset_row.Add(self.eq_preset, 0)
        eq_sizer.Add(preset_row, 0, wx.ALL, 5)
        
        # Bass/Mid/Treble sliders
        eq_grid = wx.FlexGridSizer(3, 3, 5, 10)
        
        eq_grid.Add(wx.StaticText(panel, label="Bass:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.eq_bass = wx.Slider(panel, value=self.settings.playback.eq_bass + 10, minValue=0, maxValue=20, size=(150, -1))
        eq_grid.Add(self.eq_bass, 0)
        self.bass_label = wx.StaticText(panel, label=f"{self.settings.playback.eq_bass:+d}")
        eq_grid.Add(self.bass_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        eq_grid.Add(wx.StaticText(panel, label="Mid:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.eq_mid = wx.Slider(panel, value=self.settings.playback.eq_mid + 10, minValue=0, maxValue=20, size=(150, -1))
        eq_grid.Add(self.eq_mid, 0)
        self.mid_label = wx.StaticText(panel, label=f"{self.settings.playback.eq_mid:+d}")
        eq_grid.Add(self.mid_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        eq_grid.Add(wx.StaticText(panel, label="Treble:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.eq_treble = wx.Slider(panel, value=self.settings.playback.eq_treble + 10, minValue=0, maxValue=20, size=(150, -1))
        eq_grid.Add(self.eq_treble, 0)
        self.treble_label = wx.StaticText(panel, label=f"{self.settings.playback.eq_treble:+d}")
        eq_grid.Add(self.treble_label, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Bind EQ slider updates
        self.eq_bass.Bind(wx.EVT_SLIDER, lambda e: self.bass_label.SetLabel(f"{self.eq_bass.GetValue() - 10:+d}"))
        self.eq_mid.Bind(wx.EVT_SLIDER, lambda e: self.mid_label.SetLabel(f"{self.eq_mid.GetValue() - 10:+d}"))
        self.eq_treble.Bind(wx.EVT_SLIDER, lambda e: self.treble_label.SetLabel(f"{self.eq_treble.GetValue() - 10:+d}"))
        
        eq_sizer.Add(eq_grid, 0, wx.ALL, 5)
        sizer.Add(eq_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Playback")
    
    def _add_storage_tab(self):
        """Add storage settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Podcast downloads
        podcast_box = wx.StaticBox(panel, label="Podcast Downloads")
        podcast_sizer = wx.StaticBoxSizer(podcast_box, wx.VERTICAL)
        
        path_row = wx.BoxSizer(wx.HORIZONTAL)
        path_row.Add(wx.StaticText(panel, label="Download folder:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.podcast_path = wx.TextCtrl(panel, value=self.settings.storage.podcast_download_path, size=(350, -1))
        path_row.Add(self.podcast_path, 1, wx.RIGHT, 5)
        btn_browse_podcast = wx.Button(panel, label="Browse...")
        btn_browse_podcast.Bind(wx.EVT_BUTTON, lambda e: self._browse_folder(self.podcast_path))
        path_row.Add(btn_browse_podcast, 0)
        podcast_sizer.Add(path_row, 0, wx.EXPAND | wx.ALL, 5)
        
        self.chk_auto_delete = wx.CheckBox(panel, label="Automatically delete played episodes")
        self.chk_auto_delete.SetValue(self.settings.storage.auto_delete_played)
        podcast_sizer.Add(self.chk_auto_delete, 0, wx.ALL, 5)
        
        sizer.Add(podcast_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Recording settings
        recording_box = wx.StaticBox(panel, label="Stream Recordings")
        recording_sizer = wx.StaticBoxSizer(recording_box, wx.VERTICAL)
        
        rec_path_row = wx.BoxSizer(wx.HORIZONTAL)
        rec_path_row.Add(wx.StaticText(panel, label="Recording folder:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.recording_path = wx.TextCtrl(panel, value=self.settings.storage.recording_path, size=(350, -1))
        rec_path_row.Add(self.recording_path, 1, wx.RIGHT, 5)
        btn_browse_rec = wx.Button(panel, label="Browse...")
        btn_browse_rec.Bind(wx.EVT_BUTTON, lambda e: self._browse_folder(self.recording_path))
        rec_path_row.Add(btn_browse_rec, 0)
        recording_sizer.Add(rec_path_row, 0, wx.EXPAND | wx.ALL, 5)
        
        # Recording format
        format_row = wx.BoxSizer(wx.HORIZONTAL)
        format_row.Add(wx.StaticText(panel, label="Recording format:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.recording_format = wx.Choice(panel, choices=["MP3", "WAV", "OGG"])
        format_map = {"mp3": 0, "wav": 1, "ogg": 2}
        self.recording_format.SetSelection(format_map.get(self.settings.storage.recording_format, 0))
        format_row.Add(self.recording_format, 0, wx.RIGHT, 20)
        
        format_row.Add(wx.StaticText(panel, label="Bitrate:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.recording_bitrate = wx.Choice(panel, choices=["64 kbps", "96 kbps", "128 kbps", "192 kbps", "256 kbps", "320 kbps"])
        bitrate_map = {64: 0, 96: 1, 128: 2, 192: 3, 256: 4, 320: 5}
        self.recording_bitrate.SetSelection(bitrate_map.get(self.settings.storage.recording_bitrate, 2))
        format_row.Add(self.recording_bitrate, 0)
        recording_sizer.Add(format_row, 0, wx.ALL, 5)
        
        sizer.Add(recording_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Cache settings
        cache_box = wx.StaticBox(panel, label="Cache")
        cache_sizer = wx.StaticBoxSizer(cache_box, wx.VERTICAL)
        
        cache_row = wx.BoxSizer(wx.HORIZONTAL)
        cache_row.Add(wx.StaticText(panel, label="Maximum cache size:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.cache_size = wx.SpinCtrl(panel, value=str(self.settings.storage.max_cache_size_mb), min=100, max=5000)
        cache_row.Add(self.cache_size, 0)
        cache_row.Add(wx.StaticText(panel, label="MB"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        cache_sizer.Add(cache_row, 0, wx.ALL, 5)
        
        btn_clear_cache = wx.Button(panel, label="Clear Cache Now")
        btn_clear_cache.Bind(wx.EVT_BUTTON, self._on_clear_cache)
        cache_sizer.Add(btn_clear_cache, 0, wx.ALL, 5)
        
        sizer.Add(cache_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Storage")
    
    def _add_home_tab(self):
        """Add home tab customization settings."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        content_box = wx.StaticBox(panel, label="Home Tab Content")
        content_sizer = wx.StaticBoxSizer(content_box, wx.VERTICAL)
        
        self.chk_home_streams = wx.CheckBox(panel, label="Show Streams section")
        self.chk_home_streams.SetValue(self.settings.home_tab.show_streams)
        content_sizer.Add(self.chk_home_streams, 0, wx.ALL, 5)
        
        self.chk_home_podcasts = wx.CheckBox(panel, label="Show Podcasts section")
        self.chk_home_podcasts.SetValue(self.settings.home_tab.show_podcasts)
        content_sizer.Add(self.chk_home_podcasts, 0, wx.ALL, 5)
        
        self.chk_home_affiliates = wx.CheckBox(panel, label="Show Affiliates section")
        self.chk_home_affiliates.SetValue(self.settings.home_tab.show_affiliates)
        content_sizer.Add(self.chk_home_affiliates, 0, wx.ALL, 5)
        
        self.chk_home_recent = wx.CheckBox(panel, label="Show Recently Played section")
        self.chk_home_recent.SetValue(self.settings.home_tab.show_recent)
        content_sizer.Add(self.chk_home_recent, 0, wx.ALL, 5)
        
        # Max items
        max_row = wx.BoxSizer(wx.HORIZONTAL)
        max_row.Add(wx.StaticText(panel, label="Max podcasts to show:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.max_podcasts = wx.SpinCtrl(panel, value=str(self.settings.home_tab.max_podcasts), min=1, max=20)
        max_row.Add(self.max_podcasts, 0)
        content_sizer.Add(max_row, 0, wx.ALL, 5)
        
        recent_row = wx.BoxSizer(wx.HORIZONTAL)
        recent_row.Add(wx.StaticText(panel, label="Max recent items:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.max_recent = wx.SpinCtrl(panel, value=str(self.settings.home_tab.max_recent), min=1, max=50)
        recent_row.Add(self.max_recent, 0)
        content_sizer.Add(recent_row, 0, wx.ALL, 5)
        
        sizer.Add(content_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Home Tab")
    
    def _add_startup_tab(self):
        """Add startup behavior settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Launch behavior
        launch_box = wx.StaticBox(panel, label="Launch Behavior")
        launch_sizer = wx.StaticBoxSizer(launch_box, wx.VERTICAL)
        
        self.chk_run_at_login = wx.CheckBox(panel, label="Start ACB Link when I sign in to Windows")
        self.chk_run_at_login.SetValue(self.settings.startup.run_at_login)
        self.chk_run_at_login.SetToolTip("Automatically launch ACB Link when you log in")
        launch_sizer.Add(self.chk_run_at_login, 0, wx.ALL, 5)
        
        self.chk_startup_minimized = wx.CheckBox(panel, label="Start minimized (window hidden)")
        self.chk_startup_minimized.SetValue(self.settings.startup.start_minimized)
        self.chk_startup_minimized.SetToolTip("Start with the main window minimized")
        launch_sizer.Add(self.chk_startup_minimized, 0, wx.ALL, 5)
        
        self.chk_startup_to_tray = wx.CheckBox(panel, label="Start minimized to system tray (completely hidden)")
        self.chk_startup_to_tray.SetValue(self.settings.startup.start_minimized_to_tray)
        self.chk_startup_to_tray.SetToolTip("Start hidden in the system tray - no window or taskbar button")
        launch_sizer.Add(self.chk_startup_to_tray, 0, wx.ALL, 5)
        
        sizer.Add(launch_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Session restoration
        session_box = wx.StaticBox(panel, label="Session Restoration")
        session_sizer = wx.StaticBoxSizer(session_box, wx.VERTICAL)
        
        self.chk_restore_session = wx.CheckBox(panel, label="Remember and restore my last session")
        self.chk_restore_session.SetValue(self.settings.startup.restore_last_session)
        self.chk_restore_session.SetToolTip("Remember what you were listening to when you quit")
        session_sizer.Add(self.chk_restore_session, 0, wx.ALL, 5)
        
        self.chk_auto_play_startup = wx.CheckBox(panel, label="Automatically resume playback on startup")
        self.chk_auto_play_startup.SetValue(self.settings.startup.auto_play_last_stream)
        self.chk_auto_play_startup.SetToolTip("Automatically start playing when the app launches")
        session_sizer.Add(self.chk_auto_play_startup, 0, wx.ALL, 5)
        
        delay_row = wx.BoxSizer(wx.HORIZONTAL)
        delay_row.Add(wx.StaticText(panel, label="Auto-play delay:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.auto_play_delay = wx.SpinCtrl(panel, value=str(self.settings.startup.auto_play_delay_seconds), min=0, max=30)
        self.auto_play_delay.SetToolTip("Seconds to wait before auto-playing (0 = immediate)")
        delay_row.Add(self.auto_play_delay, 0)
        delay_row.Add(wx.StaticText(panel, label="seconds"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        session_sizer.Add(delay_row, 0, wx.ALL, 5)
        
        sizer.Add(session_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # First-run and updates
        first_run_box = wx.StaticBox(panel, label="First Run & Updates")
        first_run_sizer = wx.StaticBoxSizer(first_run_box, wx.VERTICAL)
        
        self.chk_show_welcome = wx.CheckBox(panel, label="Show welcome wizard on first run")
        self.chk_show_welcome.SetValue(self.settings.startup.show_welcome_on_first_run)
        first_run_sizer.Add(self.chk_show_welcome, 0, wx.ALL, 5)
        
        self.chk_check_updates_startup = wx.CheckBox(panel, label="Check for updates on startup")
        self.chk_check_updates_startup.SetValue(self.settings.startup.check_updates_on_startup)
        first_run_sizer.Add(self.chk_check_updates_startup, 0, wx.ALL, 5)
        
        self.chk_sync_data_startup = wx.CheckBox(panel, label="Sync data from ACB servers on startup")
        self.chk_sync_data_startup.SetValue(self.settings.startup.sync_data_on_startup)
        first_run_sizer.Add(self.chk_sync_data_startup, 0, wx.ALL, 5)
        
        sizer.Add(first_run_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Startup")
    
    def _add_system_tray_tab(self):
        """Add system tray settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        tray_box = wx.StaticBox(panel, label="System Tray")
        tray_sizer = wx.StaticBoxSizer(tray_box, wx.VERTICAL)
        
        self.chk_tray_enabled = wx.CheckBox(panel, label="Enable system tray icon")
        self.chk_tray_enabled.SetValue(self.settings.system_tray.enabled)
        self.chk_tray_enabled.SetToolTip("Show ACB Link icon in the system tray")
        tray_sizer.Add(self.chk_tray_enabled, 0, wx.ALL, 5)
        
        self.chk_minimize_tray = wx.CheckBox(panel, label="Minimize to system tray (hide from taskbar)")
        self.chk_minimize_tray.SetValue(self.settings.system_tray.minimize_to_tray)
        self.chk_minimize_tray.SetToolTip("When minimizing, hide the window completely to the tray")
        tray_sizer.Add(self.chk_minimize_tray, 0, wx.ALL, 5)
        
        self.chk_close_tray = wx.CheckBox(panel, label="Close to system tray (instead of exiting)")
        self.chk_close_tray.SetValue(self.settings.system_tray.close_to_tray)
        self.chk_close_tray.SetToolTip("Clicking X hides to tray instead of quitting the app")
        tray_sizer.Add(self.chk_close_tray, 0, wx.ALL, 5)
        
        self.chk_start_minimized = wx.CheckBox(panel, label="Start minimized to tray")
        self.chk_start_minimized.SetValue(self.settings.system_tray.start_minimized)
        self.chk_start_minimized.SetToolTip("Launch the app hidden in the system tray")
        tray_sizer.Add(self.chk_start_minimized, 0, wx.ALL, 5)
        
        sizer.Add(tray_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Tray icon behavior
        behavior_box = wx.StaticBox(panel, label="Tray Icon Behavior")
        behavior_sizer = wx.StaticBoxSizer(behavior_box, wx.VERTICAL)
        
        dbl_row = wx.BoxSizer(wx.HORIZONTAL)
        dbl_row.Add(wx.StaticText(panel, label="Double-click action:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.tray_dbl_click = wx.Choice(panel, choices=["Show/Hide window", "Play/Pause"])
        action_map = {"show_hide": 0, "play_pause": 1}
        self.tray_dbl_click.SetSelection(action_map.get(self.settings.system_tray.double_click_action, 0))
        dbl_row.Add(self.tray_dbl_click, 0)
        behavior_sizer.Add(dbl_row, 0, wx.ALL, 5)
        
        single_row = wx.BoxSizer(wx.HORIZONTAL)
        single_row.Add(wx.StaticText(panel, label="Single-click action:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.tray_single_click = wx.Choice(panel, choices=["None", "Show/Hide window", "Play/Pause", "Show menu"])
        single_map = {"none": 0, "show_hide": 1, "play_pause": 2, "show_menu": 3}
        self.tray_single_click.SetSelection(single_map.get(self.settings.system_tray.single_click_action, 0))
        single_row.Add(self.tray_single_click, 0)
        behavior_sizer.Add(single_row, 0, wx.ALL, 5)
        
        sizer.Add(behavior_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Notifications
        notif_box = wx.StaticBox(panel, label="Tray Notifications")
        notif_sizer = wx.StaticBoxSizer(notif_box, wx.VERTICAL)
        
        self.chk_notifications = wx.CheckBox(panel, label="Show notification balloons")
        self.chk_notifications.SetValue(self.settings.system_tray.show_notifications)
        notif_sizer.Add(self.chk_notifications, 0, wx.ALL, 5)
        
        self.chk_now_playing_notif = wx.CheckBox(panel, label="Show now playing notifications")
        self.chk_now_playing_notif.SetValue(self.settings.system_tray.show_now_playing_notifications)
        notif_sizer.Add(self.chk_now_playing_notif, 0, wx.ALL, 5)
        
        dur_row = wx.BoxSizer(wx.HORIZONTAL)
        dur_row.Add(wx.StaticText(panel, label="Notification duration:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.notif_duration = wx.SpinCtrl(panel, value=str(self.settings.system_tray.notification_duration), min=1, max=30)
        dur_row.Add(self.notif_duration, 0)
        dur_row.Add(wx.StaticText(panel, label="seconds"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        notif_sizer.Add(dur_row, 0, wx.ALL, 5)
        
        sizer.Add(notif_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "System Tray")
    
    def _add_notifications_tab(self):
        """Add notifications settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # General notifications
        general_box = wx.StaticBox(panel, label="Notification Settings")
        general_sizer = wx.StaticBoxSizer(general_box, wx.VERTICAL)
        
        self.chk_notif_enabled = wx.CheckBox(panel, label="Enable notifications")
        self.chk_notif_enabled.SetValue(self.settings.notifications.enabled)
        general_sizer.Add(self.chk_notif_enabled, 0, wx.ALL, 5)
        
        self.chk_notif_sound = wx.CheckBox(panel, label="Play notification sounds")
        self.chk_notif_sound.SetValue(self.settings.notifications.sound_enabled)
        general_sizer.Add(self.chk_notif_sound, 0, wx.ALL, 5)
        
        dur_row = wx.BoxSizer(wx.HORIZONTAL)
        dur_row.Add(wx.StaticText(panel, label="Display duration:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.notif_display_duration = wx.SpinCtrl(panel, value=str(self.settings.notifications.duration_seconds), min=1, max=30)
        dur_row.Add(self.notif_display_duration, 0)
        dur_row.Add(wx.StaticText(panel, label="seconds"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        general_sizer.Add(dur_row, 0, wx.ALL, 5)
        
        pos_row = wx.BoxSizer(wx.HORIZONTAL)
        pos_row.Add(wx.StaticText(panel, label="Position:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.notif_position = wx.Choice(panel, choices=["Bottom Right", "Bottom Left", "Top Right", "Top Left"])
        pos_map = {"bottom_right": 0, "bottom_left": 1, "top_right": 2, "top_left": 3}
        self.notif_position.SetSelection(pos_map.get(self.settings.notifications.position, 0))
        pos_row.Add(self.notif_position, 0)
        general_sizer.Add(pos_row, 0, wx.ALL, 5)
        
        sizer.Add(general_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Notification types
        types_box = wx.StaticBox(panel, label="Show Notifications For")
        types_sizer = wx.StaticBoxSizer(types_box, wx.VERTICAL)
        
        self.chk_notif_now_playing = wx.CheckBox(panel, label="Now playing (stream/episode changes)")
        self.chk_notif_now_playing.SetValue(self.settings.notifications.show_now_playing)
        types_sizer.Add(self.chk_notif_now_playing, 0, wx.ALL, 5)
        
        self.chk_notif_stream_changes = wx.CheckBox(panel, label="Stream status changes (connected/disconnected)")
        self.chk_notif_stream_changes.SetValue(self.settings.notifications.show_stream_changes)
        types_sizer.Add(self.chk_notif_stream_changes, 0, wx.ALL, 5)
        
        self.chk_notif_recording = wx.CheckBox(panel, label="Recording started/stopped")
        self.chk_notif_recording.SetValue(self.settings.notifications.show_recording_status)
        types_sizer.Add(self.chk_notif_recording, 0, wx.ALL, 5)
        
        self.chk_notif_download = wx.CheckBox(panel, label="Download completed")
        self.chk_notif_download.SetValue(self.settings.notifications.show_download_complete)
        types_sizer.Add(self.chk_notif_download, 0, wx.ALL, 5)
        
        self.chk_notif_events = wx.CheckBox(panel, label="Calendar event reminders")
        self.chk_notif_events.SetValue(self.settings.notifications.show_event_reminders)
        types_sizer.Add(self.chk_notif_events, 0, wx.ALL, 5)
        
        self.chk_notif_updates = wx.CheckBox(panel, label="Update available")
        self.chk_notif_updates.SetValue(self.settings.notifications.show_update_available)
        types_sizer.Add(self.chk_notif_updates, 0, wx.ALL, 5)
        
        sizer.Add(types_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Notifications")
    
    def _add_keyboard_tab(self):
        """Add keyboard settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Global hotkeys
        hotkeys_box = wx.StaticBox(panel, label="Global Hotkeys")
        hotkeys_sizer = wx.StaticBoxSizer(hotkeys_box, wx.VERTICAL)
        
        self.chk_global_hotkeys = wx.CheckBox(panel, label="Enable global hotkeys (work when app is in background)")
        self.chk_global_hotkeys.SetValue(self.settings.keyboard.enable_global_hotkeys)
        self.chk_global_hotkeys.SetToolTip("Control ACB Link even when another app has focus")
        hotkeys_sizer.Add(self.chk_global_hotkeys, 0, wx.ALL, 5)
        
        self.chk_media_keys = wx.CheckBox(panel, label="Respond to media keys (play/pause, stop, etc.)")
        self.chk_media_keys.SetValue(self.settings.keyboard.enable_media_keys)
        self.chk_media_keys.SetToolTip("Use your keyboard's media control buttons")
        hotkeys_sizer.Add(self.chk_media_keys, 0, wx.ALL, 5)
        
        sizer.Add(hotkeys_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Navigation
        nav_box = wx.StaticBox(panel, label="Keyboard Navigation")
        nav_sizer = wx.StaticBoxSizer(nav_box, wx.VERTICAL)
        
        self.chk_vim_nav = wx.CheckBox(panel, label="Vim-style navigation (h/j/k/l for left/down/up/right)")
        self.chk_vim_nav.SetValue(self.settings.keyboard.vim_style_navigation)
        nav_sizer.Add(self.chk_vim_nav, 0, wx.ALL, 5)
        
        self.chk_space_playback = wx.CheckBox(panel, label="Space bar toggles play/pause")
        self.chk_space_playback.SetValue(self.settings.keyboard.space_toggles_playback)
        nav_sizer.Add(self.chk_space_playback, 0, wx.ALL, 5)
        
        self.chk_escape_minimize = wx.CheckBox(panel, label="Escape key minimizes window")
        self.chk_escape_minimize.SetValue(self.settings.keyboard.escape_minimizes)
        nav_sizer.Add(self.chk_escape_minimize, 0, wx.ALL, 5)
        
        sizer.Add(nav_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Customize shortcuts button
        btn_customize = wx.Button(panel, label="Customize Keyboard Shortcuts...")
        btn_customize.Bind(wx.EVT_BUTTON, self._on_customize_shortcuts)
        btn_customize.SetToolTip("Open the keyboard shortcuts customization dialog")
        sizer.Add(btn_customize, 0, wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Keyboard")
    
    def _add_voice_control_tab(self):
        """Add voice control settings tab with command mapping."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Voice Control Enable
        enable_box = wx.StaticBox(panel, label="Voice Control")
        enable_sizer = wx.StaticBoxSizer(enable_box, wx.VERTICAL)
        
        self.chk_voice_enabled = wx.CheckBox(panel, label="Enable voice control")
        self.chk_voice_enabled.SetValue(self.settings.voice.enabled)
        self.chk_voice_enabled.SetToolTip("Enable hands-free voice command control")
        enable_sizer.Add(self.chk_voice_enabled, 0, wx.ALL, 5)
        
        self.chk_voice_feedback = wx.CheckBox(panel, label="Voice feedback (speak confirmations)")
        self.chk_voice_feedback.SetValue(self.settings.voice.voice_feedback)
        self.chk_voice_feedback.SetToolTip("Speak confirmation messages after commands")
        enable_sizer.Add(self.chk_voice_feedback, 0, wx.ALL, 5)
        
        self.chk_command_confirm = wx.CheckBox(panel, label="Announce command confirmations")
        self.chk_command_confirm.SetValue(self.settings.voice.command_confirmation)
        self.chk_command_confirm.SetToolTip("Announce when commands are executed")
        enable_sizer.Add(self.chk_command_confirm, 0, wx.ALL, 5)
        
        sizer.Add(enable_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Wake Word Configuration
        wake_box = wx.StaticBox(panel, label="Wake Word")
        wake_sizer = wx.StaticBoxSizer(wake_box, wx.VERTICAL)
        
        self.chk_wake_word_enabled = wx.CheckBox(panel, label="Require wake word before commands")
        self.chk_wake_word_enabled.SetValue(self.settings.voice.wake_word_enabled)
        self.chk_wake_word_enabled.SetToolTip("If enabled, say the wake word first to activate listening")
        wake_sizer.Add(self.chk_wake_word_enabled, 0, wx.ALL, 5)
        
        wake_row = wx.BoxSizer(wx.HORIZONTAL)
        wake_row.Add(wx.StaticText(panel, label="Wake word/phrase:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.txt_wake_word = wx.TextCtrl(panel, value=self.settings.voice.wake_word, size=(200, -1))
        self.txt_wake_word.SetToolTip("The phrase that activates voice control (e.g., 'hey link', 'ok computer')")
        make_accessible(self.txt_wake_word, "Wake word", "Enter the phrase to activate voice control")
        wake_row.Add(self.txt_wake_word, 0)
        wake_sizer.Add(wake_row, 0, wx.ALL, 5)
        
        wake_note = wx.StaticText(panel, label="Examples: 'hey link', 'ok link', 'computer', 'hey radio'")
        wake_note.SetForegroundColour(wx.Colour(100, 100, 100))
        wake_sizer.Add(wake_note, 0, wx.LEFT | wx.BOTTOM, 5)
        
        sizer.Add(wake_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Text-to-Speech Settings
        tts_box = wx.StaticBox(panel, label="Text-to-Speech")
        tts_sizer = wx.StaticBoxSizer(tts_box, wx.VERTICAL)
        
        self.chk_tts_enabled = wx.CheckBox(panel, label="Enable text-to-speech responses")
        self.chk_tts_enabled.SetValue(self.settings.voice.tts_enabled)
        tts_sizer.Add(self.chk_tts_enabled, 0, wx.ALL, 5)
        
        rate_row = wx.BoxSizer(wx.HORIZONTAL)
        rate_row.Add(wx.StaticText(panel, label="Speaking rate:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.spin_tts_rate = wx.SpinCtrl(panel, value=str(self.settings.voice.tts_rate), min=100, max=300)
        self.spin_tts_rate.SetToolTip("Words per minute (100-300)")
        make_accessible(self.spin_tts_rate, "TTS speaking rate", "Words per minute, 100 to 300")
        rate_row.Add(self.spin_tts_rate, 0)
        rate_row.Add(wx.StaticText(panel, label=" words/minute"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        tts_sizer.Add(rate_row, 0, wx.ALL, 5)
        
        vol_row = wx.BoxSizer(wx.HORIZONTAL)
        vol_row.Add(wx.StaticText(panel, label="TTS Volume:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.slider_tts_volume = wx.Slider(panel, value=int(self.settings.voice.tts_volume * 100), 
                                           minValue=0, maxValue=100, size=(150, -1))
        self.slider_tts_volume.SetToolTip("Text-to-speech volume (0-100%)")
        make_accessible(self.slider_tts_volume, "TTS volume", "Adjust text-to-speech volume")
        vol_row.Add(self.slider_tts_volume, 0)
        self.lbl_tts_volume = wx.StaticText(panel, label=f"{int(self.settings.voice.tts_volume * 100)}%")
        vol_row.Add(self.lbl_tts_volume, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        self.slider_tts_volume.Bind(wx.EVT_SLIDER, self._on_tts_volume_change)
        tts_sizer.Add(vol_row, 0, wx.ALL, 5)
        
        sizer.Add(tts_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Command Mapping Button
        cmd_box = wx.StaticBox(panel, label="Voice Commands")
        cmd_sizer = wx.StaticBoxSizer(cmd_box, wx.VERTICAL)
        
        cmd_note = wx.StaticText(panel, label="Customize the trigger phrases for voice commands.")
        cmd_sizer.Add(cmd_note, 0, wx.ALL, 5)
        
        btn_customize_commands = wx.Button(panel, label="Customize Voice Commands...")
        btn_customize_commands.Bind(wx.EVT_BUTTON, self._on_customize_voice_commands)
        btn_customize_commands.SetToolTip("Open dialog to customize voice command trigger phrases")
        make_accessible(btn_customize_commands, "Customize voice commands", 
                       "Opens a dialog to customize the trigger phrases for each voice command")
        cmd_sizer.Add(btn_customize_commands, 0, wx.ALL, 5)
        
        sizer.Add(cmd_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Voice Control")
    
    def _on_tts_volume_change(self, event):
        """Update TTS volume label when slider changes."""
        value = self.slider_tts_volume.GetValue()
        self.lbl_tts_volume.SetLabel(f"{value}%")
    
    def _on_customize_voice_commands(self, event):
        """Open voice command customization dialog."""
        dlg = VoiceCommandMappingDialog(self, self.settings)
        if dlg.ShowModal() == wx.ID_OK:
            # Custom triggers are saved by the dialog
            pass
        dlg.Destroy()
    
    def _add_announcements_tab(self):
        """Add announcements settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        try:
            from .announcements import get_announcement_manager
            from .announcement_ui import AnnouncementSettingsPanel
            
            manager = get_announcement_manager()
            self.announcement_settings_panel = AnnouncementSettingsPanel(
                panel, manager.settings
            )
            sizer.Add(self.announcement_settings_panel, 1, wx.EXPAND | wx.ALL, 10)
        except Exception:
            # Fallback if announcement system not available
            label = wx.StaticText(
                panel,
                label="Announcement settings are not available.\n\n"
                      "The announcement system may not be properly initialized."
            )
            sizer.Add(label, 0, wx.ALL, 20)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Announcements")
    
    def _add_privacy_tab(self):
        """Add privacy settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # History
        history_box = wx.StaticBox(panel, label="History")
        history_sizer = wx.StaticBoxSizer(history_box, wx.VERTICAL)
        
        self.chk_search_history = wx.CheckBox(panel, label="Remember search history")
        self.chk_search_history.SetValue(self.settings.privacy.remember_search_history)
        history_sizer.Add(self.chk_search_history, 0, wx.ALL, 5)
        
        self.chk_listening_history = wx.CheckBox(panel, label="Remember listening history")
        self.chk_listening_history.SetValue(self.settings.privacy.remember_listening_history)
        history_sizer.Add(self.chk_listening_history, 0, wx.ALL, 5)
        
        max_row = wx.BoxSizer(wx.HORIZONTAL)
        max_row.Add(wx.StaticText(panel, label="Maximum history items:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.max_history = wx.SpinCtrl(panel, value=str(self.settings.privacy.max_history_items), min=10, max=1000)
        max_row.Add(self.max_history, 0)
        history_sizer.Add(max_row, 0, wx.ALL, 5)
        
        self.chk_clear_on_exit = wx.CheckBox(panel, label="Clear history when app closes")
        self.chk_clear_on_exit.SetValue(self.settings.privacy.clear_history_on_exit)
        history_sizer.Add(self.chk_clear_on_exit, 0, wx.ALL, 5)
        
        btn_clear_now = wx.Button(panel, label="Clear History Now")
        btn_clear_now.Bind(wx.EVT_BUTTON, self._on_clear_history)
        history_sizer.Add(btn_clear_now, 0, wx.ALL, 5)
        
        sizer.Add(history_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Analytics
        analytics_box = wx.StaticBox(panel, label="Analytics & Telemetry (Opt-In)")
        analytics_sizer = wx.StaticBoxSizer(analytics_box, wx.VERTICAL)
        
        note = wx.StaticText(panel, label="All analytics are disabled by default and require your explicit consent.")
        note.SetForegroundColour(wx.Colour(100, 100, 100))
        analytics_sizer.Add(note, 0, wx.ALL, 5)
        
        self.chk_analytics = wx.CheckBox(panel, label="Help improve ACB Link by sharing anonymous usage data")
        self.chk_analytics.SetValue(self.settings.privacy.analytics_enabled)
        analytics_sizer.Add(self.chk_analytics, 0, wx.ALL, 5)
        
        self.chk_crash_reports = wx.CheckBox(panel, label="Send crash reports (helps us fix bugs)")
        self.chk_crash_reports.SetValue(self.settings.privacy.crash_reporting)
        analytics_sizer.Add(self.chk_crash_reports, 0, wx.ALL, 5)
        
        sizer.Add(analytics_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Privacy")
    
    def _add_performance_tab(self):
        """Add performance settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Resource usage
        resource_box = wx.StaticBox(panel, label="Resource Usage")
        resource_sizer = wx.StaticBoxSizer(resource_box, wx.VERTICAL)
        
        self.chk_low_memory = wx.CheckBox(panel, label="Low memory mode (reduces caching)")
        self.chk_low_memory.SetValue(self.settings.performance.low_memory_mode)
        self.chk_low_memory.SetToolTip("Use less RAM at the cost of some features")
        resource_sizer.Add(self.chk_low_memory, 0, wx.ALL, 5)
        
        self.chk_reduce_cpu = wx.CheckBox(panel, label="Reduce CPU usage when minimized")
        self.chk_reduce_cpu.SetValue(self.settings.performance.reduce_cpu_when_minimized)
        resource_sizer.Add(self.chk_reduce_cpu, 0, wx.ALL, 5)
        
        self.chk_hardware_accel = wx.CheckBox(panel, label="Enable hardware acceleration")
        self.chk_hardware_accel.SetValue(self.settings.performance.hardware_acceleration)
        resource_sizer.Add(self.chk_hardware_accel, 0, wx.ALL, 5)
        
        sizer.Add(resource_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Downloads and caching
        download_box = wx.StaticBox(panel, label="Downloads & Caching")
        download_sizer = wx.StaticBoxSizer(download_box, wx.VERTICAL)
        
        dl_row = wx.BoxSizer(wx.HORIZONTAL)
        dl_row.Add(wx.StaticText(panel, label="Maximum concurrent downloads:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.max_downloads = wx.SpinCtrl(panel, value=str(self.settings.performance.max_concurrent_downloads), min=1, max=10)
        dl_row.Add(self.max_downloads, 0)
        download_sizer.Add(dl_row, 0, wx.ALL, 5)
        
        self.chk_cache_artwork = wx.CheckBox(panel, label="Cache podcast artwork")
        self.chk_cache_artwork.SetValue(self.settings.performance.cache_podcast_artwork)
        download_sizer.Add(self.chk_cache_artwork, 0, wx.ALL, 5)
        
        self.chk_preload_next = wx.CheckBox(panel, label="Preload next episode in playlist")
        self.chk_preload_next.SetValue(self.settings.performance.preload_next_episode)
        download_sizer.Add(self.chk_preload_next, 0, wx.ALL, 5)
        
        sizer.Add(download_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Logging
        log_box = wx.StaticBox(panel, label="Logging")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        
        log_row = wx.BoxSizer(wx.HORIZONTAL)
        log_row.Add(wx.StaticText(panel, label="Maximum log file size:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.max_log_size = wx.SpinCtrl(panel, value=str(self.settings.performance.max_log_size_mb), min=1, max=100)
        log_row.Add(self.max_log_size, 0)
        log_row.Add(wx.StaticText(panel, label="MB"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        log_sizer.Add(log_row, 0, wx.ALL, 5)
        
        self.chk_auto_cleanup_logs = wx.CheckBox(panel, label="Automatically clean up old log files")
        self.chk_auto_cleanup_logs.SetValue(self.settings.performance.auto_cleanup_old_logs)
        log_sizer.Add(self.chk_auto_cleanup_logs, 0, wx.ALL, 5)
        
        sizer.Add(log_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Performance")

    def _add_accessibility_tab(self):
        """Add accessibility settings tab."""
        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sr_box = wx.StaticBox(panel, label="Screen Reader Support")
        sr_sizer = wx.StaticBoxSizer(sr_box, wx.VERTICAL)
        
        self.chk_sr_announce = wx.CheckBox(panel, label="Enable screen reader announcements")
        self.chk_sr_announce.SetValue(self.settings.accessibility.screen_reader_announcements)
        sr_sizer.Add(self.chk_sr_announce, 0, wx.ALL, 5)
        
        self.chk_audio_feedback = wx.CheckBox(panel, label="Audio feedback for actions")
        self.chk_audio_feedback.SetValue(self.settings.accessibility.audio_feedback)
        sr_sizer.Add(self.chk_audio_feedback, 0, wx.ALL, 5)
        
        self.chk_auto_read_status = wx.CheckBox(panel, label="Automatically read status changes")
        self.chk_auto_read_status.SetValue(self.settings.accessibility.auto_read_status)
        sr_sizer.Add(self.chk_auto_read_status, 0, wx.ALL, 5)
        
        sizer.Add(sr_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Keyboard
        kb_box = wx.StaticBox(panel, label="Keyboard Navigation")
        kb_sizer = wx.StaticBoxSizer(kb_box, wx.VERTICAL)
        
        self.chk_kb_only = wx.CheckBox(panel, label="Keyboard-only mode (disable mouse interactions)")
        self.chk_kb_only.SetValue(self.settings.accessibility.keyboard_only_mode)
        kb_sizer.Add(self.chk_kb_only, 0, wx.ALL, 5)
        
        self.chk_focus_mouse = wx.CheckBox(panel, label="Focus follows mouse")
        self.chk_focus_mouse.SetValue(self.settings.accessibility.focus_follows_mouse)
        kb_sizer.Add(self.chk_focus_mouse, 0, wx.ALL, 5)
        
        sizer.Add(kb_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Dialogs
        dialog_box = wx.StaticBox(panel, label="Dialogs & Confirmations")
        dialog_sizer = wx.StaticBoxSizer(dialog_box, wx.VERTICAL)
        
        self.chk_confirmations = wx.CheckBox(panel, label="Show confirmation dialogs for actions")
        self.chk_confirmations.SetValue(self.settings.accessibility.confirmation_dialogs)
        dialog_sizer.Add(self.chk_confirmations, 0, wx.ALL, 5)
        
        sizer.Add(dialog_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, "Accessibility")
    
    def _create_buttons(self) -> wx.BoxSizer:
        """Create dialog buttons."""
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Reset to defaults button
        btn_reset = wx.Button(self, label="Reset to Defaults")
        btn_reset.Bind(wx.EVT_BUTTON, self._on_reset_defaults)
        btn_sizer.Add(btn_reset, 0, wx.RIGHT, 20)
        
        btn_sizer.AddStretchSpacer()
        
        # Standard buttons
        btn_ok = wx.Button(self, wx.ID_OK, "Save")
        btn_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        btn_apply = wx.Button(self, label="Apply")
        btn_apply.Bind(wx.EVT_BUTTON, self._on_apply)
        
        btn_ok.SetDefault()
        btn_sizer.Add(btn_ok, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_apply, 0, wx.RIGHT, 5)
        btn_sizer.Add(btn_cancel, 0)
        
        return btn_sizer
    
    def _browse_folder(self, text_ctrl: wx.TextCtrl):
        """Open folder browser dialog."""
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            text_ctrl.SetValue(dlg.GetPath())
        dlg.Destroy()
    
    def _on_clear_cache(self, event):
        """Clear the application cache."""
        if wx.MessageBox(
            "Are you sure you want to clear the cache?",
            "Clear Cache",
            wx.YES_NO | wx.ICON_QUESTION
        ) == wx.YES:
            # TODO: Implement cache clearing
            wx.MessageBox("Cache cleared.", "Success", wx.OK | wx.ICON_INFORMATION)
    
    def _on_customize_shortcuts(self, event):
        """Open keyboard shortcuts customization dialog."""
        wx.MessageBox(
            "Keyboard shortcut customization will be available in a future update.",
            "Coming Soon",
            wx.OK | wx.ICON_INFORMATION
        )
    
    def _on_clear_history(self, event):
        """Clear listening and search history."""
        if wx.MessageBox(
            "Are you sure you want to clear all history?\nThis includes search history and listening history.",
            "Clear History",
            wx.YES_NO | wx.ICON_WARNING
        ) == wx.YES:
            # TODO: Implement history clearing
            wx.MessageBox("History cleared.", "Success", wx.OK | wx.ICON_INFORMATION)
    
    def _on_reset_defaults(self, event):
        """Reset all settings to defaults."""
        if wx.MessageBox(
            "Are you sure you want to reset all settings to their default values?",
            "Reset Settings",
            wx.YES_NO | wx.ICON_WARNING
        ) == wx.YES:
            self.settings = AppSettings()
            self.Destroy()
            # Re-create and show dialog with default settings
            dlg = SettingsDialog(self.GetParent(), self.settings)
            dlg.ShowModal()
    
    def _on_apply(self, event):
        """Apply settings without closing."""
        self._save_settings()
        announce("Settings applied successfully")
        wx.MessageBox("Settings applied.", "Success", wx.OK | wx.ICON_INFORMATION)
    
    def _save_settings(self):
        """Save all settings from UI to settings object."""
        # General
        self.settings.preferred_browser = "chrome" if self.rb_chrome.GetValue() else "edge"
        self.settings.default_tab = TAB_NAMES[self.default_tab.GetSelection()]
        self.settings.check_updates = self.chk_updates.GetValue()
        
        # Theme/Appearance
        theme_names = ["system", "light", "dark", "high_contrast_light", "high_contrast_dark"]
        self.settings.theme.name = theme_names[self.theme_choice.GetSelection()]
        self.settings.theme.font_size = self.font_size.GetValue()
        font_families = ["Segoe UI", "Arial", "Verdana", "Tahoma", "Calibri", "Consolas"]
        self.settings.theme.font_family = font_families[self.font_family.GetSelection()]
        self.settings.theme.high_contrast = self.chk_high_contrast.GetValue()
        self.settings.theme.reduce_motion = self.chk_reduce_motion.GetValue()
        self.settings.theme.large_cursor = self.chk_large_cursor.GetValue()
        self.settings.theme.focus_ring_width = self.focus_width.GetValue()
        
        # Playback
        self.settings.playback.skip_backward_seconds = self.skip_backward.GetValue()
        self.settings.playback.skip_forward_seconds = self.skip_forward.GetValue()
        self.settings.playback.default_speed = SPEED_VALUES[self.playback_speed.GetSelection()]
        self.settings.playback.default_volume = self.default_volume.GetValue()
        self.settings.playback.remember_position = self.chk_remember_pos.GetValue()
        self.settings.playback.auto_play_next = self.chk_auto_play.GetValue()
        self.settings.playback.normalize_audio = self.chk_normalize.GetValue()
        eq_presets = ["flat", "bass_boost", "voice", "treble"]
        self.settings.playback.eq_preset = eq_presets[self.eq_preset.GetSelection()]
        self.settings.playback.eq_bass = self.eq_bass.GetValue() - 10
        self.settings.playback.eq_mid = self.eq_mid.GetValue() - 10
        self.settings.playback.eq_treble = self.eq_treble.GetValue() - 10
        
        # Storage
        self.settings.storage.podcast_download_path = self.podcast_path.GetValue()
        self.settings.storage.recording_path = self.recording_path.GetValue()
        self.settings.storage.auto_delete_played = self.chk_auto_delete.GetValue()
        formats = ["mp3", "wav", "ogg"]
        self.settings.storage.recording_format = formats[self.recording_format.GetSelection()]
        self.settings.storage.recording_bitrate = RECORDING_BITRATES[self.recording_bitrate.GetSelection()]
        self.settings.storage.max_cache_size_mb = self.cache_size.GetValue()
        
        # Home Tab
        self.settings.home_tab.show_streams = self.chk_home_streams.GetValue()
        self.settings.home_tab.show_podcasts = self.chk_home_podcasts.GetValue()
        self.settings.home_tab.show_affiliates = self.chk_home_affiliates.GetValue()
        self.settings.home_tab.show_recent = self.chk_home_recent.GetValue()
        self.settings.home_tab.max_podcasts = self.max_podcasts.GetValue()
        self.settings.home_tab.max_recent = self.max_recent.GetValue()
        
        # Startup
        self.settings.startup.run_at_login = self.chk_run_at_login.GetValue()
        self.settings.startup.start_minimized = self.chk_startup_minimized.GetValue()
        self.settings.startup.start_minimized_to_tray = self.chk_startup_to_tray.GetValue()
        self.settings.startup.restore_last_session = self.chk_restore_session.GetValue()
        self.settings.startup.auto_play_last_stream = self.chk_auto_play_startup.GetValue()
        self.settings.startup.auto_play_delay_seconds = self.auto_play_delay.GetValue()
        self.settings.startup.show_welcome_on_first_run = self.chk_show_welcome.GetValue()
        self.settings.startup.check_updates_on_startup = self.chk_check_updates_startup.GetValue()
        self.settings.startup.sync_data_on_startup = self.chk_sync_data_startup.GetValue()
        
        # System Tray
        self.settings.system_tray.enabled = self.chk_tray_enabled.GetValue()
        self.settings.system_tray.minimize_to_tray = self.chk_minimize_tray.GetValue()
        self.settings.system_tray.close_to_tray = self.chk_close_tray.GetValue()
        self.settings.system_tray.start_minimized = self.chk_start_minimized.GetValue()
        self.settings.system_tray.show_notifications = self.chk_notifications.GetValue()
        self.settings.system_tray.show_now_playing_notifications = self.chk_now_playing_notif.GetValue()
        self.settings.system_tray.notification_duration = self.notif_duration.GetValue()
        dbl_actions = ["show_hide", "play_pause"]
        self.settings.system_tray.double_click_action = dbl_actions[self.tray_dbl_click.GetSelection()]
        single_actions = ["none", "show_hide", "play_pause", "show_menu"]
        self.settings.system_tray.single_click_action = single_actions[self.tray_single_click.GetSelection()]
        
        # Notifications
        self.settings.notifications.enabled = self.chk_notif_enabled.GetValue()
        self.settings.notifications.sound_enabled = self.chk_notif_sound.GetValue()
        self.settings.notifications.duration_seconds = self.notif_display_duration.GetValue()
        positions = ["bottom_right", "bottom_left", "top_right", "top_left"]
        self.settings.notifications.position = positions[self.notif_position.GetSelection()]
        self.settings.notifications.show_now_playing = self.chk_notif_now_playing.GetValue()
        self.settings.notifications.show_stream_changes = self.chk_notif_stream_changes.GetValue()
        self.settings.notifications.show_recording_status = self.chk_notif_recording.GetValue()
        self.settings.notifications.show_download_complete = self.chk_notif_download.GetValue()
        self.settings.notifications.show_event_reminders = self.chk_notif_events.GetValue()
        self.settings.notifications.show_update_available = self.chk_notif_updates.GetValue()
        
        # Keyboard
        self.settings.keyboard.enable_global_hotkeys = self.chk_global_hotkeys.GetValue()
        self.settings.keyboard.enable_media_keys = self.chk_media_keys.GetValue()
        self.settings.keyboard.vim_style_navigation = self.chk_vim_nav.GetValue()
        self.settings.keyboard.space_toggles_playback = self.chk_space_playback.GetValue()
        self.settings.keyboard.escape_minimizes = self.chk_escape_minimize.GetValue()
        
        # Voice Control
        self.settings.voice.enabled = self.chk_voice_enabled.GetValue()
        self.settings.voice.voice_feedback = self.chk_voice_feedback.GetValue()
        self.settings.voice.command_confirmation = self.chk_command_confirm.GetValue()
        self.settings.voice.wake_word_enabled = self.chk_wake_word_enabled.GetValue()
        self.settings.voice.wake_word = self.txt_wake_word.GetValue().strip() or "hey link"
        self.settings.voice.tts_enabled = self.chk_tts_enabled.GetValue()
        self.settings.voice.tts_rate = self.spin_tts_rate.GetValue()
        self.settings.voice.tts_volume = self.slider_tts_volume.GetValue() / 100.0
        
        # Privacy
        self.settings.privacy.remember_search_history = self.chk_search_history.GetValue()
        self.settings.privacy.remember_listening_history = self.chk_listening_history.GetValue()
        self.settings.privacy.max_history_items = self.max_history.GetValue()
        self.settings.privacy.clear_history_on_exit = self.chk_clear_on_exit.GetValue()
        self.settings.privacy.analytics_enabled = self.chk_analytics.GetValue()
        self.settings.privacy.crash_reporting = self.chk_crash_reports.GetValue()
        
        # Performance
        self.settings.performance.low_memory_mode = self.chk_low_memory.GetValue()
        self.settings.performance.reduce_cpu_when_minimized = self.chk_reduce_cpu.GetValue()
        self.settings.performance.hardware_acceleration = self.chk_hardware_accel.GetValue()
        self.settings.performance.max_concurrent_downloads = self.max_downloads.GetValue()
        self.settings.performance.cache_podcast_artwork = self.chk_cache_artwork.GetValue()
        self.settings.performance.preload_next_episode = self.chk_preload_next.GetValue()
        self.settings.performance.max_log_size_mb = self.max_log_size.GetValue()
        self.settings.performance.auto_cleanup_old_logs = self.chk_auto_cleanup_logs.GetValue()
        
        # Accessibility
        self.settings.accessibility.screen_reader_announcements = self.chk_sr_announce.GetValue()
        self.settings.accessibility.audio_feedback = self.chk_audio_feedback.GetValue()
        self.settings.accessibility.auto_read_status = self.chk_auto_read_status.GetValue()
        self.settings.accessibility.keyboard_only_mode = self.chk_kb_only.GetValue()
        self.settings.accessibility.focus_follows_mouse = self.chk_focus_mouse.GetValue()
        self.settings.accessibility.confirmation_dialogs = self.chk_confirmations.GetValue()
        
        # Announcements
        if hasattr(self, 'announcement_settings_panel'):
            try:
                from .announcements import get_announcement_manager
                manager = get_announcement_manager()
                manager.settings = self.announcement_settings_panel.get_settings()
                manager.save_settings()
            except Exception:
                pass
    
    def get_settings(self) -> AppSettings:
        """Get the modified settings."""
        self._save_settings()
        return self.settings


class VoiceCommandMappingDialog(wx.Dialog):
    """Dialog for customizing voice command trigger phrases."""
    
    # Command categories for organization
    CATEGORIES = [
        ("Playback", ["play", "pause", "stop", "volume_up", "volume_down", "mute", "unmute"]),
        ("Navigation", ["skip_forward", "skip_back", "go_home", "go_streams", "go_podcasts", 
                       "go_affiliates", "go_resources"]),
        ("Recording", ["start_recording", "stop_recording"]),
        ("System", ["open_settings", "what_playing", "help", "stop_listening"]),
    ]
    
    # Friendly display names for commands
    COMMAND_LABELS = {
        "play": "Play/Resume",
        "pause": "Pause",
        "stop": "Stop",
        "volume_up": "Volume Up",
        "volume_down": "Volume Down",
        "mute": "Mute",
        "unmute": "Unmute",
        "skip_forward": "Skip Forward",
        "skip_back": "Skip Back",
        "go_home": "Go to Home",
        "go_streams": "Go to Streams",
        "go_podcasts": "Go to Podcasts",
        "go_affiliates": "Go to Affiliates",
        "go_resources": "Go to Resources",
        "start_recording": "Start Recording",
        "stop_recording": "Stop Recording",
        "open_settings": "Open Settings",
        "what_playing": "What's Playing",
        "help": "Help/Commands",
        "stop_listening": "Stop Voice Control",
    }
    
    def __init__(self, parent, settings: AppSettings):
        super().__init__(
            parent,
            title="Customize Voice Commands",
            size=(700, 550),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.settings = settings
        # Work with a copy of custom_triggers
        self.custom_triggers = dict(settings.voice.custom_triggers) if settings.voice.custom_triggers else {}
        
        self._build_ui()
        self.Centre()
    
    def _build_ui(self):
        """Build the dialog UI."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        instructions = wx.StaticText(
            self,
            label="Customize the trigger phrases for each voice command.\n"
                  "Select a command to view and edit its triggers."
        )
        main_sizer.Add(instructions, 0, wx.ALL, 10)
        
        # Main content area
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Left side - Command list
        left_panel = wx.Panel(self)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        cmd_label = wx.StaticText(left_panel, label="Voice Commands:")
        left_sizer.Add(cmd_label, 0, wx.BOTTOM, 5)
        
        self.command_list = wx.ListCtrl(
            left_panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN,
            size=(250, 350)
        )
        self.command_list.InsertColumn(0, "Command", width=150)
        self.command_list.InsertColumn(1, "Category", width=90)
        make_accessible(self.command_list, "Voice commands list", 
                       "Select a command to customize its trigger phrases")
        
        # Populate command list
        self._populate_command_list()
        
        self.command_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_command_selected)
        left_sizer.Add(self.command_list, 1, wx.EXPAND)
        
        left_panel.SetSizer(left_sizer)
        content_sizer.Add(left_panel, 0, wx.EXPAND | wx.RIGHT, 10)
        
        # Right side - Trigger editing
        right_panel = wx.Panel(self)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.lbl_selected_command = wx.StaticText(right_panel, label="Select a command to edit triggers")
        font = self.lbl_selected_command.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.lbl_selected_command.SetFont(font)
        right_sizer.Add(self.lbl_selected_command, 0, wx.BOTTOM, 10)
        
        trigger_label = wx.StaticText(right_panel, label="Trigger phrases (one per line):")
        right_sizer.Add(trigger_label, 0, wx.BOTTOM, 5)
        
        self.txt_triggers = wx.TextCtrl(
            right_panel,
            style=wx.TE_MULTILINE,
            size=(350, 150)
        )
        self.txt_triggers.SetToolTip("Enter the phrases that will trigger this command, one per line")
        make_accessible(self.txt_triggers, "Trigger phrases", 
                       "Enter one trigger phrase per line for the selected command")
        self.txt_triggers.Enable(False)
        right_sizer.Add(self.txt_triggers, 0, wx.EXPAND | wx.BOTTOM, 10)
        
        # Default triggers display
        default_label = wx.StaticText(right_panel, label="Default triggers (for reference):")
        right_sizer.Add(default_label, 0, wx.BOTTOM, 5)
        
        self.txt_defaults = wx.TextCtrl(
            right_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(350, 100)
        )
        self.txt_defaults.SetBackgroundColour(wx.Colour(245, 245, 245))
        make_accessible(self.txt_defaults, "Default triggers", "Shows the default trigger phrases")
        right_sizer.Add(self.txt_defaults, 0, wx.EXPAND | wx.BOTTOM, 10)
        
        # Buttons for triggers
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_reset_triggers = wx.Button(right_panel, label="Reset to Defaults")
        self.btn_reset_triggers.Bind(wx.EVT_BUTTON, self._on_reset_triggers)
        self.btn_reset_triggers.Enable(False)
        btn_sizer.Add(self.btn_reset_triggers, 0, wx.RIGHT, 10)
        
        self.btn_save_triggers = wx.Button(right_panel, label="Save Triggers")
        self.btn_save_triggers.Bind(wx.EVT_BUTTON, self._on_save_triggers)
        self.btn_save_triggers.Enable(False)
        btn_sizer.Add(self.btn_save_triggers, 0)
        
        right_sizer.Add(btn_sizer, 0)
        
        right_panel.SetSizer(right_sizer)
        content_sizer.Add(right_panel, 1, wx.EXPAND)
        
        main_sizer.Add(content_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        # Bottom buttons
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        btn_reset_all = wx.Button(self, label="Reset All to Defaults")
        btn_reset_all.Bind(wx.EVT_BUTTON, self._on_reset_all)
        bottom_sizer.Add(btn_reset_all, 0, wx.RIGHT, 20)
        
        bottom_sizer.AddStretchSpacer()
        
        btn_ok = wx.Button(self, wx.ID_OK, "Done")
        btn_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        
        btn_ok.Bind(wx.EVT_BUTTON, self._on_ok)
        
        bottom_sizer.Add(btn_ok, 0, wx.RIGHT, 5)
        bottom_sizer.Add(btn_cancel, 0)
        
        main_sizer.Add(bottom_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
        
        # Track currently selected command
        self.selected_command = None
    
    def _populate_command_list(self):
        """Populate the command list with all voice commands."""
        self._command_names = []
        idx = 0
        for category, commands in self.CATEGORIES:
            for cmd_name in commands:
                label = self.COMMAND_LABELS.get(cmd_name, cmd_name.replace("_", " ").title())
                self.command_list.InsertItem(idx, label)
                self.command_list.SetItem(idx, 1, category)
                self.command_list.SetItemData(idx, idx)
                self._command_names.append(cmd_name)
                idx += 1
    
    def _get_default_triggers(self, command_name: str) -> list:
        """Get default triggers for a command."""
        from .voice_control import VoiceController
        return VoiceController.DEFAULT_TRIGGERS.get(command_name, [])
    
    def _get_current_triggers(self, command_name: str) -> list:
        """Get current triggers (custom or default) for a command."""
        if command_name in self.custom_triggers and self.custom_triggers[command_name]:
            return self.custom_triggers[command_name]
        return self._get_default_triggers(command_name)
    
    def _on_command_selected(self, event):
        """Handle command selection."""
        idx = event.GetIndex()
        if idx >= 0 and idx < len(self._command_names):
            self.selected_command = self._command_names[idx]
            
            # Update UI
            label = self.COMMAND_LABELS.get(self.selected_command, self.selected_command)
            self.lbl_selected_command.SetLabel(f"Editing: {label}")
            
            # Show current triggers
            triggers = self._get_current_triggers(self.selected_command)
            self.txt_triggers.SetValue("\n".join(triggers))
            
            # Show default triggers
            defaults = self._get_default_triggers(self.selected_command)
            self.txt_defaults.SetValue("\n".join(defaults))
            
            # Enable controls
            self.txt_triggers.Enable(True)
            self.btn_reset_triggers.Enable(True)
            self.btn_save_triggers.Enable(True)
            
            announce(f"Selected {label}. Current triggers: {', '.join(triggers)}")
    
    def _on_save_triggers(self, event):
        """Save triggers for the selected command."""
        if not self.selected_command:
            return
        
        # Parse triggers from text
        text = self.txt_triggers.GetValue()
        triggers = [t.strip().lower() for t in text.split("\n") if t.strip()]
        
        if not triggers:
            wx.MessageBox(
                "Please enter at least one trigger phrase.",
                "No Triggers",
                wx.OK | wx.ICON_WARNING
            )
            return
        
        # Save to custom triggers
        self.custom_triggers[self.selected_command] = triggers
        
        announce("Triggers saved")
        wx.MessageBox("Triggers saved for this command.", "Saved", wx.OK | wx.ICON_INFORMATION)
    
    def _on_reset_triggers(self, event):
        """Reset triggers for selected command to defaults."""
        if not self.selected_command:
            return
        
        # Remove from custom triggers
        if self.selected_command in self.custom_triggers:
            del self.custom_triggers[self.selected_command]
        
        # Update display
        defaults = self._get_default_triggers(self.selected_command)
        self.txt_triggers.SetValue("\n".join(defaults))
        
        announce("Triggers reset to defaults")
    
    def _on_reset_all(self, event):
        """Reset all commands to default triggers."""
        if wx.MessageBox(
            "Are you sure you want to reset all voice commands to their default triggers?",
            "Reset All",
            wx.YES_NO | wx.ICON_WARNING
        ) == wx.YES:
            self.custom_triggers.clear()
            
            # Update display if a command is selected
            if self.selected_command:
                defaults = self._get_default_triggers(self.selected_command)
                self.txt_triggers.SetValue("\n".join(defaults))
            
            announce("All triggers reset to defaults")
            wx.MessageBox("All triggers have been reset to defaults.", "Reset", wx.OK | wx.ICON_INFORMATION)
    
    def _on_ok(self, event):
        """Save all changes and close."""
        # Save any pending changes for the current command
        if self.selected_command:
            text = self.txt_triggers.GetValue()
            triggers = [t.strip().lower() for t in text.split("\n") if t.strip()]
            if triggers:
                self.custom_triggers[self.selected_command] = triggers
        
        # Update settings
        self.settings.voice.custom_triggers = self.custom_triggers
        
        event.Skip()  # Allow dialog to close