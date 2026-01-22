"""
ACB Link - Main Frame
Main application window with menubar and tabbed interface.
Enhanced with all roadmap features: podcasts, playlists, favorites, search, offline mode, etc.
WCAG 2.2 AA Compliant.

Version 1.0.0 - Initial Public Release
"""

import webbrowser
from pathlib import Path
from typing import Optional

import wx
import wx.adv

from .accessibility import announce, make_button_accessible
from .advanced_settings import show_advanced_settings
from .calendar_integration import CalendarManager
from .config import get_config
from .data import PODCASTS, STREAMS, TAB_NAMES
from .dialogs import SettingsDialog
from .enhanced_voice import EnhancedVoiceController, VoiceState
from .favorites import FavoritesManager
from .localization import get_translation_manager
from .media_player import MediaPlayer, StreamRecorder
from .native_player import NativeAudioPlayer, SleepTimer
from .offline import OfflineManager
from .panels import AffiliatesPanel, HomePanel, PodcastsPanel, ResourcesPanel, StreamsPanel

# Playback enhancements
from .playback_enhancements import (
    AudioDuckingDialog,
    AudioDuckingManager,
    AutoPlayDialog,
    AutoPlayManager,
    EnhancedSleepTimer,
    MediaKeyHandler,
    NowPlayingInfo,
    PlaybackSpeedController,
    PlaybackSpeedDialog,
    QuietHoursDialog,
    QuietHoursManager,
    RecentlyPlayedDialog,
    RecentlyPlayedManager,
    ShareManager,
    SleepTimerDialog,
)
from .playlists import PlaylistManager, PlaylistPlayer

# New roadmap feature imports
from .podcast_manager import PodcastManager
from .scheduled_recording import ScheduledRecordingManager
from .search import GlobalSearch
from .server import LocalWebServer
from .settings import AppSettings
from .styles import UIConstants, get_style_manager, hex_to_colour
from .system_tray import ACBLinkTaskBarIcon

# User experience enhancements
from .user_experience import (
    HIGH_CONTRAST_PRESETS,
    ExportImportDialog,
    FontSizeManager,
    ListeningStatsDialog,
    ListeningStatsManager,
    PanicKeyHandler,
    QuickStatusAnnouncer,
    ResumePlaybackDialog,
    ResumePlaybackManager,
    SettingsBackupManager,
    show_welcome_wizard_if_needed,
)
from .utils import PlaybackPositionManager, RecentItemsManager, setup_logging

# View settings and pane navigation
from .view_settings import (
    FavoritesQuickDial,
    FocusModeManager,
    PaneNavigator,
    PaneType,
    StreamScheduleManager,
    ViewSettingsDialog,
    ViewSettingsManager,
    VisualSettingsManager,
)


class MainFrame(wx.Frame):
    """Main application window for ACB Link. WCAG 2.2 AA Compliant."""

    def __init__(self):
        super().__init__(None, title="ACB Link", size=(1000, 700), style=wx.DEFAULT_FRAME_STYLE)

        # Initialize components
        self.logger = setup_logging()
        self.settings = AppSettings.load()
        self.recent_items = RecentItemsManager()
        self.playback_positions = PlaybackPositionManager()

        # Initialize announcement system
        self._init_announcement_system()

        # Initialize localization
        self.translations = get_translation_manager()
        if hasattr(self.settings, "language") and self.settings.language:
            self.translations.set_language(self.settings.language)

        # Initialize style manager
        self.style_manager = get_style_manager()
        if self.settings.theme and self.settings.theme.name:
            self.style_manager.set_scheme(self.settings.theme.name)
        self.style_manager.set_font_size(
            self.settings.theme.font_size if self.settings.theme else 11
        )

        # Media player
        self.media_player: Optional[MediaPlayer] = None
        self.stream_recorder: Optional[StreamRecorder] = None
        self.current_stream: Optional[str] = None
        self.is_recording = False

        # Initialize new roadmap managers
        self._init_managers()

        # Web server
        self.web_server = LocalWebServer()

        # System tray
        self.tray_icon: Optional[ACBLinkTaskBarIcon] = None

        # Build UI
        self._build_menubar()
        self._build_statusbar()
        self._build_ui()
        self._setup_accelerators()
        self._bind_events()

        # Initialize system tray if enabled
        if self.settings.system_tray.enabled:
            self._init_tray_icon()

        # Start web server
        self._start_server()

        # Apply theme
        self._apply_theme()

        # Center and show
        self.Centre()

        # Handle start minimized options
        # Priority: start_minimized_to_tray > start_minimized > normal
        if (
            self.settings.system_tray.start_minimized
            or self.settings.startup.start_minimized_to_tray
            or self.settings.system_tray.start_minimized_to_tray
        ):
            # Start hidden to system tray
            self.Hide()
        elif self.settings.startup.start_minimized:
            # Start minimized but visible in taskbar
            self.Iconize(True)
            self.Show()
        else:
            self.Show()

        # Start background services
        self._start_background_services()

        self.logger.info("ACB Link started")

    def _init_managers(self):
        """Initialize all feature managers."""
        # Podcast manager with RSS support
        self.podcast_manager = PodcastManager(on_episode_downloaded=self._on_episode_downloaded)

        # Native audio player
        self.native_player = NativeAudioPlayer(
            on_playback_started=self._on_playback_started,
            on_playback_stopped=self._on_playback_stopped,
            on_error=self._on_playback_error,
        )

        # Sleep timer
        self.sleep_timer = SleepTimer(on_timer_end=self._on_sleep_timer_end)

        # Favorites and bookmarks
        self.favorites_manager = FavoritesManager(on_favorites_changed=self._on_favorites_changed)

        # Playlist manager
        self.playlist_manager = PlaylistManager(on_playlists_changed=self._on_playlists_changed)
        self.playlist_player = PlaylistPlayer(
            playlist_manager=self.playlist_manager, audio_player=self.native_player
        )

        # Scheduled recording
        self.recording_manager = ScheduledRecordingManager(
            on_recording_started=self._on_scheduled_recording_start,
            on_recording_complete=self._on_scheduled_recording_complete,
        )

        # Global search
        self.search_engine = GlobalSearch(
            podcasts=PODCASTS, streams=STREAMS, favorites_manager=self.favorites_manager
        )

        # Offline mode
        self.offline_manager = OfflineManager(
            on_connectivity_changed=self._on_connectivity_changed,
            on_download_progress=self._on_download_progress,
        )

        # Calendar integration
        self.calendar_manager = CalendarManager(on_event_reminder=self._on_event_reminder)

        # Enhanced voice control
        self.voice_controller = EnhancedVoiceController(on_command=self._on_voice_command)
        self.voice_controller.on_state_change = self._on_voice_state_change

        # User experience managers
        self.listening_stats = ListeningStatsManager()
        self.resume_manager = ResumePlaybackManager()
        self.backup_manager = SettingsBackupManager()
        self.font_size_manager = FontSizeManager(
            self.settings.theme.font_size if self.settings.theme else 12, self._on_font_size_changed
        )
        self.panic_handler = PanicKeyHandler(
            mute_callback=self._toggle_mute,
            minimize_callback=self._minimize_to_tray,
            is_muted_callback=lambda: getattr(self, "_is_muted", False),
        )
        self.quick_status = QuickStatusAnnouncer(
            get_playback_state=self._get_playback_state,
            get_volume=lambda: (
                self.volume_slider.GetValue() if hasattr(self, "volume_slider") else 100
            ),
            get_current_content=lambda: self.current_stream or "",
            announcer=announce,
        )

        # Playback enhancement managers
        self.enhanced_sleep_timer = EnhancedSleepTimer(
            on_timer_end=self._on_enhanced_sleep_timer_end,
            on_timer_tick=self._on_sleep_timer_tick,
            on_fade_start=self._on_sleep_timer_fade_start,
        )

        self.auto_play_manager = AutoPlayManager()

        self.playback_speed = PlaybackSpeedController(
            initial_speed=self.settings.playback.default_speed if self.settings.playback else 1.0,
            on_speed_changed=self._on_playback_speed_changed,
        )

        self.share_manager = ShareManager(get_now_playing=self._get_now_playing_info)

        self.recently_played = RecentlyPlayedManager()

        self.media_key_handler = MediaKeyHandler(
            on_play_pause=lambda: wx.CallAfter(self._on_play_pause, None),
            on_stop=lambda: wx.CallAfter(self._on_stop, None),
            on_next=None,  # Not applicable for streams
            on_previous=None,
            on_volume_up=lambda: wx.CallAfter(self._on_volume_up, None),
            on_volume_down=lambda: wx.CallAfter(self._on_volume_down, None),
        )

        self.audio_ducking = AudioDuckingManager(
            get_volume=lambda: (
                self.volume_slider.GetValue() if hasattr(self, "volume_slider") else 100
            ),
            set_volume=lambda v: (
                self.volume_slider.SetValue(v) if hasattr(self, "volume_slider") else None
            ),
            duck_percentage=30,
        )

        self.quiet_hours = QuietHoursManager(
            on_quiet_hours_start=self._on_quiet_hours_start,
            on_quiet_hours_end=self._on_quiet_hours_end,
        )

        # View and layout managers
        self.view_settings = ViewSettingsManager()
        self.visual_settings = VisualSettingsManager()
        self.visual_settings.add_change_callback(self._on_visual_settings_changed)

        # Pane navigator for F6/Shift+F6
        self.pane_navigator = PaneNavigator(
            announcer=announce if self.settings.accessibility.screen_reader_announcements else None
        )

        # Focus mode manager
        self.focus_mode = FocusModeManager(
            view_manager=self.view_settings,
            on_enter=self._on_focus_mode_enter,
            on_exit=self._on_focus_mode_exit,
        )

        # Stream schedule manager
        self.schedule_manager = StreamScheduleManager()

        # Favorites quick dial (Alt+F1-F5)
        self.quick_dial = FavoritesQuickDial(
            get_favorites=lambda: self.favorites_manager.get_favorites()[:5],
            play_callback=self._play_favorite,
            announcer=announce if self.settings.accessibility.screen_reader_announcements else None,
        )

    def _start_background_services(self):
        """Start background services after UI is ready."""
        # Show first-run wizard if needed
        wizard_settings = show_welcome_wizard_if_needed(self, self.settings)
        if wizard_settings:
            self._apply_wizard_settings(wizard_settings)

        # Check for resume playback
        if self.resume_manager.has_resumable_content():
            wx.CallAfter(self._show_resume_dialog)

        # Check for announcements on startup
        self._check_announcements_on_startup()

        # Start connectivity monitoring
        self.offline_manager.start_monitoring()

        # Start calendar refresh
        self.calendar_manager.start_refresh_timer()

        # Start scheduled recording checker
        self.recording_manager.start()

        # Start voice control if enabled in settings
        if getattr(self.settings, "voice_control_enabled", False):
            self.voice_controller.start()

        # Start quiet hours monitoring
        self.quiet_hours.start_monitoring()

        # Check for auto-play on startup
        wx.CallLater(self.auto_play_manager.settings.delay_seconds * 1000, self._check_auto_play)

    def _check_auto_play(self):
        """Check and execute auto-play if configured."""
        if not self.auto_play_manager.should_auto_play():
            return

        content_type, content_name = self.auto_play_manager.get_auto_play_target()

        if content_type == "last_played":
            # Get last played from recently played
            recent = self.recently_played.get_recent(1)
            if recent:
                self._play_from_recent(recent[0])
                if self.settings.accessibility.screen_reader_announcements:
                    announce(f"Auto-playing {recent[0].name}")
        elif content_type == "stream" and content_name:
            self._play_stream(content_name)
            if self.settings.accessibility.screen_reader_announcements:
                announce(f"Auto-playing {content_name}")

    def _apply_wizard_settings(self, wizard_settings: dict):
        """Apply settings from welcome wizard."""
        # Apply theme
        theme_name = wizard_settings.get("theme", "light")
        if theme_name in HIGH_CONTRAST_PRESETS:
            # Handle custom high contrast presets
            preset = HIGH_CONTRAST_PRESETS.get(theme_name.replace("_", " ").title(), {})
            if preset:
                self.style_manager.set_scheme(preset.get("name", "light"))
        else:
            self.style_manager.set_scheme(theme_name)

        # Apply font size
        font_size = wizard_settings.get("font_size", 12)
        self.style_manager.set_font_size(font_size)
        self.settings.theme.font_size = font_size

        # Apply accessibility settings
        if self.settings.accessibility:
            self.settings.accessibility.screen_reader_announcements = wizard_settings.get(
                "screen_reader_announcements", True
            )
            self.settings.accessibility.audio_feedback = wizard_settings.get("audio_feedback", True)

        # Save settings
        self.settings.save()

        # Refresh UI
        self._apply_theme()

    def _show_resume_dialog(self):
        """Show resume playback dialog."""
        dialog = ResumePlaybackDialog(self, self.resume_manager)
        result = dialog.ShowModal()
        dialog.Destroy()

        if result == wx.ID_YES:
            state = self.resume_manager.last_state
            if state and state.content_type == "stream":
                self._play_stream(state.content_name)
            elif state and state.content_type == "podcast":
                # For podcasts, we'd need more context - just play stream for now
                self._play_stream(state.content_name)

    # Manager callback handlers

    def _on_episode_downloaded(self, episode):
        """Handle episode download complete."""
        wx.CallAfter(self._show_notification, "Download Complete", f"Episode: {episode.title}")
        self.logger.info(f"Episode downloaded: {episode.title}")

    def _on_playback_started(self, url: str):
        """Handle native playback started."""
        self.btn_play_pause.SetLabel("⏸")
        self.statusbar.SetStatusText("Playing", 1)

    def _on_playback_stopped(self):
        """Handle native playback stopped."""
        self.btn_play_pause.SetLabel("▶")
        self.statusbar.SetStatusText("Stopped", 1)

    def _on_playback_error(self, error: str):
        """Handle playback error."""
        self.logger.error(f"Playback error: {error}")
        wx.CallAfter(wx.MessageBox, f"Playback error: {error}", "Error", wx.OK | wx.ICON_ERROR)

    def _on_sleep_timer_end(self):
        """Handle sleep timer end - stop playback."""
        wx.CallAfter(self._on_stop, None)
        wx.CallAfter(self._show_notification, "Sleep Timer", "Playback stopped")

    def _on_favorites_changed(self):
        """Handle favorites list change."""
        # Refresh favorites panel if it exists
        if hasattr(self, "favorites_panel"):
            wx.CallAfter(self.favorites_panel.refresh)

    def _on_playlists_changed(self):
        """Handle playlists change."""
        # Refresh playlists panel if it exists
        if hasattr(self, "playlists_panel"):
            wx.CallAfter(self.playlists_panel.refresh)

    def _on_scheduled_recording_start(self, recording):
        """Handle scheduled recording started."""
        self.is_recording = True
        wx.CallAfter(self._update_recording_ui, True)
        wx.CallAfter(self._show_notification, "Recording Started", f"Recording: {recording.name}")

    def _on_scheduled_recording_complete(self, recording, filepath):
        """Handle scheduled recording complete."""
        self.is_recording = False
        wx.CallAfter(self._update_recording_ui, False)
        wx.CallAfter(self._show_notification, "Recording Complete", f"Saved: {filepath}")

    def _update_recording_ui(self, is_recording: bool):
        """Update UI for recording state."""
        if is_recording:
            self.btn_record.SetLabel("⏹")
            self.btn_record.SetToolTip("Stop recording")
            self.statusbar.SetStatusText("Recording...", 2)
        else:
            self.btn_record.SetLabel("⏺")
            self.btn_record.SetToolTip("Start recording")
            self.statusbar.SetStatusText("", 2)

    def _on_connectivity_changed(self, is_online: bool):
        """Handle connectivity status change."""
        status = "Online" if is_online else "Offline"
        wx.CallAfter(self.statusbar.SetStatusText, status, 0)

        if not is_online:
            wx.CallAfter(
                self._show_notification,
                "Network Status",
                "You are now offline. Some features may be limited.",
            )

    def _on_download_progress(self, item_id: str, progress: float):
        """Handle download progress update."""
        # Could update a progress indicator
        pass

    def _on_event_reminder(self, event):
        """Handle calendar event reminder."""
        wx.CallAfter(
            self._show_notification, "Event Reminder", f"{event.title} starts in {event.time_until}"
        )

    def _on_voice_command(self, intent: str, query):
        """Handle voice command."""
        wx.CallAfter(self._process_voice_command, intent, query)

    def _process_voice_command(self, intent: str, query):
        """Process voice command on main thread."""
        if intent == "play":
            stream_name = query.parameters.get("stream_name")
            if stream_name:
                self._play_stream(stream_name)
            elif query.parameters.get("stream_number"):
                num = query.parameters["stream_number"]
                streams_list = list(STREAMS.keys())
                if 1 <= num <= len(streams_list):
                    self._play_stream(streams_list[num - 1])
        elif intent == "pause":
            self._on_play_pause(None)
        elif intent == "stop":
            self._on_stop(None)
        elif intent == "volume":
            if "level" in query.parameters:
                self.volume_slider.SetValue(query.parameters["level"])
                self._on_volume_change(None)
            elif query.parameters.get("direction") == "up":
                self._on_volume_up(None)
            elif query.parameters.get("direction") == "down":
                self._on_volume_down(None)
        elif intent == "search":
            _results = self.search_engine.search(query.target)  # noqa: F841 - TODO: display results
            # Navigate to search tab and show results
            self.notebook.SetSelection(5)  # Search tab index
        elif intent == "navigate":
            target = query.target.lower()
            tab_map = {
                "home": 0,
                "streams": 1,
                "podcasts": 2,
                "favorites": 3,
                "playlists": 4,
                "search": 5,
                "calendar": 6,
            }
            if target in tab_map:
                self.notebook.SetSelection(tab_map[target])
        elif intent == "record":
            self._on_record_toggle(None)
        elif intent == "settings":
            self._on_settings(None)
        elif intent == "status":
            status = self.now_playing.GetLabel()
            self.voice_controller.speak(status)

    def _on_voice_state_change(self, state: VoiceState):
        """Handle voice control state change."""
        # Update status bar or indicator
        state_text = {
            VoiceState.DISABLED: "",
            VoiceState.LISTENING_FOR_WAKE: "🎤 Say 'Hey ACB Link'",
            VoiceState.LISTENING_FOR_COMMAND: "🎤 Listening...",
            VoiceState.PROCESSING: "🎤 Processing...",
            VoiceState.SPEAKING: "🔊 Speaking...",
        }
        wx.CallAfter(self.statusbar.SetStatusText, state_text.get(state, ""), 0)

    def _show_notification(self, title: str, message: str):
        """Show a notification via system tray or message."""
        if self.tray_icon and self.settings.system_tray.show_notifications:
            self.tray_icon.show_notification(title, message)
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"{title}: {message}")

    def _build_menubar(self):
        """Build the application menubar with Edit, View, and Play menus."""
        menubar = wx.MenuBar()

        # ===== FILE MENU =====
        file_menu = wx.Menu()

        self.menu_open_browser = file_menu.Append(
            wx.ID_ANY, "Open in &Browser\tCtrl+B", "Open content in browser"
        )
        file_menu.AppendSeparator()

        self.menu_settings = file_menu.Append(
            wx.ID_PREFERENCES, "&Settings...\tCtrl+,", "Open settings"
        )
        self.menu_advanced_settings = file_menu.Append(
            wx.ID_ANY, "Advanced Settings...\tCtrl+Shift+,", "Open advanced configuration"
        )
        file_menu.AppendSeparator()

        self.menu_exit = file_menu.Append(wx.ID_EXIT, "E&xit\tAlt+F4", "Exit application")

        menubar.Append(file_menu, "&File")

        # ===== EDIT MENU =====
        edit_menu = wx.Menu()

        self.menu_copy = edit_menu.Append(wx.ID_COPY, "&Copy\tCtrl+C", "Copy selected text")
        self.menu_select_all = edit_menu.Append(
            wx.ID_SELECTALL, "Select &All\tCtrl+A", "Select all text"
        )
        edit_menu.AppendSeparator()

        self.menu_copy_now_playing = edit_menu.Append(
            wx.ID_ANY, "Copy What's &Playing\tCtrl+Shift+C", "Copy current track info to clipboard"
        )
        self.menu_copy_stream_url = edit_menu.Append(
            wx.ID_ANY, "Copy Stream &URL", "Copy current stream URL to clipboard"
        )
        edit_menu.AppendSeparator()

        # Preferences (duplicate in Edit menu for discoverability)
        self.menu_preferences = edit_menu.Append(
            wx.ID_ANY, "&Preferences...\tCtrl+,", "Open settings"
        )

        menubar.Append(edit_menu, "&Edit")

        # ===== VIEW MENU =====
        view_menu = wx.Menu()

        # Tab navigation
        tabs_submenu = wx.Menu()
        self.menu_home = tabs_submenu.Append(wx.ID_ANY, "&Home\tCtrl+1", "Go to Home tab")
        self.menu_streams_tab = tabs_submenu.Append(
            wx.ID_ANY, "&Streams\tCtrl+2", "Go to Streams tab"
        )
        self.menu_podcasts_tab = tabs_submenu.Append(
            wx.ID_ANY, "&Podcasts\tCtrl+3", "Go to Podcasts tab"
        )
        self.menu_affiliates_tab = tabs_submenu.Append(
            wx.ID_ANY, "&Affiliates\tCtrl+4", "Go to Affiliates tab"
        )
        self.menu_resources_tab = tabs_submenu.Append(
            wx.ID_ANY, "&Resources\tCtrl+5", "Go to Resources tab"
        )
        view_menu.AppendSubMenu(tabs_submenu, "Go to &Tab")
        view_menu.AppendSeparator()

        # Show/Hide UI elements (sticky checkboxes)
        self.menu_show_toolbar = view_menu.AppendCheckItem(
            wx.ID_ANY, "Show &Toolbar", "Toggle toolbar visibility"
        )
        self.menu_show_toolbar.Check(self.view_settings.settings.show_toolbar)

        self.menu_show_tab_bar = view_menu.AppendCheckItem(
            wx.ID_ANY, "Show Tab &Bar", "Toggle tab bar visibility"
        )
        self.menu_show_tab_bar.Check(self.view_settings.settings.show_tab_bar)

        self.menu_show_status_bar = view_menu.AppendCheckItem(
            wx.ID_ANY, "Show &Status Bar", "Toggle status bar visibility"
        )
        self.menu_show_status_bar.Check(self.view_settings.settings.show_status_bar)

        self.menu_show_player = view_menu.AppendCheckItem(
            wx.ID_ANY, "Show &Player Controls\tCtrl+Shift+P", "Toggle player controls visibility"
        )
        self.menu_show_player.Check(self.view_settings.settings.show_player_panel)

        self.menu_show_now_playing = view_menu.AppendCheckItem(
            wx.ID_ANY, "Show &Now Playing Banner", "Toggle now playing banner"
        )
        self.menu_show_now_playing.Check(self.view_settings.settings.show_now_playing_banner)

        self.menu_show_sidebar = view_menu.AppendCheckItem(
            wx.ID_ANY, "Show Side&bar\tCtrl+\\", "Toggle sidebar visibility"
        )
        self.menu_show_sidebar.Check(self.view_settings.settings.show_sidebar)
        view_menu.AppendSeparator()

        # Pane navigation
        self.menu_next_pane = view_menu.Append(
            wx.ID_ANY, "&Next Pane\tF6", "Move focus to next pane"
        )
        self.menu_prev_pane = view_menu.Append(
            wx.ID_ANY, "&Previous Pane\tShift+F6", "Move focus to previous pane"
        )

        # Tab cycling
        self.menu_next_tab = view_menu.Append(
            wx.ID_ANY, "Next Tab\tCtrl+Tab", "Switch to next tab"
        )
        self.menu_prev_tab = view_menu.Append(
            wx.ID_ANY, "Previous Tab\tCtrl+Shift+Tab", "Switch to previous tab"
        )
        view_menu.AppendSeparator()

        # Focus mode
        self.menu_focus_mode = view_menu.AppendCheckItem(
            wx.ID_ANY, "&Focus Mode\tCtrl+Shift+D", "Minimal distraction-free interface"
        )
        self.menu_focus_mode.Check(self.view_settings.settings.focus_mode)

        self.menu_full_screen = view_menu.Append(
            wx.ID_ANY, "F&ull Screen\tF11", "Toggle full screen mode"
        )
        view_menu.AppendSeparator()

        # Quick actions
        self.menu_quick_status = view_menu.Append(
            wx.ID_ANY, "&Quick Status\tF5", "Announce current playback status"
        )
        self.menu_panic_key = view_menu.Append(
            wx.ID_ANY, "&Panic Key (Mute && Minimize)\tCtrl+Shift+M", "Instantly mute and minimize"
        )
        view_menu.AppendSeparator()

        # Text size submenu
        text_size_submenu = wx.Menu()
        self.menu_increase_font = text_size_submenu.Append(
            wx.ID_ANY, "&Increase\tCtrl++", "Make text larger"
        )
        self.menu_decrease_font = text_size_submenu.Append(
            wx.ID_ANY, "&Decrease\tCtrl+-", "Make text smaller"
        )
        self.menu_reset_font = text_size_submenu.Append(
            wx.ID_ANY, "&Reset\tCtrl+0", "Reset text to default size"
        )
        view_menu.AppendSubMenu(text_size_submenu, "Text Si&ze")
        view_menu.AppendSeparator()

        # Podcast sort submenu
        self.podcast_sort_menu = wx.Menu()
        self.menu_sort_date_newest = self.podcast_sort_menu.AppendRadioItem(
            wx.ID_ANY, "&Newest First", "Sort episodes by date, newest first"
        )
        self.menu_sort_date_oldest = self.podcast_sort_menu.AppendRadioItem(
            wx.ID_ANY, "&Oldest First", "Sort episodes by date, oldest first"
        )
        self.podcast_sort_menu.AppendSeparator()
        self.menu_sort_title_az = self.podcast_sort_menu.AppendRadioItem(
            wx.ID_ANY, "Title &A-Z", "Sort episodes by title alphabetically"
        )
        self.menu_sort_title_za = self.podcast_sort_menu.AppendRadioItem(
            wx.ID_ANY, "Title &Z-A", "Sort episodes by title reverse alphabetically"
        )
        self.podcast_sort_menu.AppendSeparator()
        self.menu_sort_duration_long = self.podcast_sort_menu.AppendRadioItem(
            wx.ID_ANY, "&Longest First", "Sort episodes by duration, longest first"
        )
        self.menu_sort_duration_short = self.podcast_sort_menu.AppendRadioItem(
            wx.ID_ANY, "&Shortest First", "Sort episodes by duration, shortest first"
        )
        self.podcast_sort_menu.AppendSeparator()
        self.menu_sort_unplayed = self.podcast_sort_menu.AppendRadioItem(
            wx.ID_ANY, "&Unplayed First", "Show unplayed episodes first"
        )
        self.menu_sort_downloaded = self.podcast_sort_menu.AppendRadioItem(
            wx.ID_ANY, "&Downloaded First", "Show downloaded episodes first"
        )
        self.menu_sort_date_newest.Check(True)  # Default
        view_menu.AppendSubMenu(self.podcast_sort_menu, "&Sort Podcast Episodes")
        view_menu.AppendSeparator()

        # Customize home page
        self.menu_customize_home = view_menu.Append(
            wx.ID_ANY, "Customize &Home Page...", "Choose which widgets appear on the home page"
        )
        view_menu.AppendSeparator()

        # View settings dialog
        self.menu_view_settings = view_menu.Append(
            wx.ID_ANY, "View &Settings...", "Configure view and appearance settings"
        )

        menubar.Append(view_menu, "&View")

        # ===== PLAY MENU =====
        play_menu = wx.Menu()

        self.menu_play_pause = play_menu.Append(wx.ID_ANY, "&Play/Pause\tSpace", "Toggle playback")
        self.menu_stop = play_menu.Append(wx.ID_ANY, "&Stop\tCtrl+S", "Stop playback")
        play_menu.AppendSeparator()

        # Navigation
        self.menu_skip_back = play_menu.Append(
            wx.ID_ANY, "Skip &Back 15s\tCtrl+Left", "Skip backward 15 seconds"
        )
        self.menu_skip_fwd = play_menu.Append(
            wx.ID_ANY, "Skip &Forward 15s\tCtrl+Right", "Skip forward 15 seconds"
        )
        play_menu.AppendSeparator()

        # Volume submenu
        volume_submenu = wx.Menu()
        self.menu_vol_up = volume_submenu.Append(
            wx.ID_ANY, "Volume &Up\tCtrl+Up", "Increase volume"
        )
        self.menu_vol_down = volume_submenu.Append(
            wx.ID_ANY, "Volume &Down\tCtrl+Down", "Decrease volume"
        )
        volume_submenu.AppendSeparator()
        self.menu_mute = volume_submenu.Append(wx.ID_ANY, "&Mute/Unmute\tCtrl+M", "Toggle mute")
        play_menu.AppendSubMenu(volume_submenu, "&Volume")
        play_menu.AppendSeparator()

        # Playback controls
        self.menu_playback_speed = play_menu.Append(
            wx.ID_ANY, "Playback S&peed...\tCtrl+P", "Adjust playback speed"
        )
        self.menu_sleep_timer = play_menu.Append(
            wx.ID_ANY, "Sleep &Timer...\tCtrl+T", "Set sleep timer"
        )
        play_menu.AppendSeparator()

        # Recording
        self.menu_record = play_menu.Append(
            wx.ID_ANY, "&Record Stream\tCtrl+R", "Start/stop recording"
        )
        play_menu.AppendSeparator()

        # History
        self.menu_recently_played = play_menu.Append(
            wx.ID_ANY, "Recently P&layed...\tCtrl+Shift+R", "Show recently played items"
        )

        menubar.Append(play_menu, "&Play")

        # ===== STREAMS MENU =====
        streams_menu = wx.Menu()

        # Quick dial favorites (Alt+F1-F5)
        quick_dial_submenu = wx.Menu()
        self.menu_quick_dial_1 = quick_dial_submenu.Append(
            wx.ID_ANY, "Quick Dial &1\tAlt+F1", "Play favorite #1"
        )
        self.menu_quick_dial_2 = quick_dial_submenu.Append(
            wx.ID_ANY, "Quick Dial &2\tAlt+F2", "Play favorite #2"
        )
        self.menu_quick_dial_3 = quick_dial_submenu.Append(
            wx.ID_ANY, "Quick Dial &3\tAlt+F3", "Play favorite #3"
        )
        self.menu_quick_dial_4 = quick_dial_submenu.Append(
            wx.ID_ANY, "Quick Dial &4\tAlt+F4", "Play favorite #4"
        )
        self.menu_quick_dial_5 = quick_dial_submenu.Append(
            wx.ID_ANY, "Quick Dial &5\tAlt+F5", "Play favorite #5"
        )
        streams_menu.AppendSubMenu(quick_dial_submenu, "&Quick Dial Favorites")
        streams_menu.AppendSeparator()

        for name in STREAMS.keys():
            item = streams_menu.Append(wx.ID_ANY, name)
            self.Bind(wx.EVT_MENU, lambda e, n=name: self._play_stream(n), item)

        menubar.Append(streams_menu, "&Streams")

        # ===== PODCASTS MENU =====
        podcasts_menu = wx.Menu()

        for category, pods in PODCASTS.items():
            category_menu = wx.Menu()
            for podcast_name in pods.keys():
                item = category_menu.Append(wx.ID_ANY, podcast_name)
                self.Bind(
                    wx.EVT_MENU,
                    lambda e, c=category, p=podcast_name: self._play_podcast(c, p),
                    item,
                )
            podcasts_menu.AppendSubMenu(category_menu, category)

        menubar.Append(podcasts_menu, "&Podcasts")

        # ===== TOOLS MENU =====
        tools_menu = wx.Menu()

        self.menu_sync_data = tools_menu.Append(
            wx.ID_ANY, "Sync &Data...\tCtrl+Shift+S", "Synchronize data with ACB servers"
        )
        tools_menu.AppendSeparator()

        self.menu_start_server = tools_menu.Append(
            wx.ID_ANY, "Start &Web Server", "Start local web server"
        )
        self.menu_stop_server = tools_menu.Append(
            wx.ID_ANY, "S&top Web Server", "Stop local web server"
        )
        tools_menu.AppendSeparator()

        self.menu_scheduled_tasks = tools_menu.Append(
            wx.ID_ANY, "Scheduled &Tasks...", "Manage scheduled tasks"
        )
        tools_menu.AppendSeparator()

        self.menu_listening_stats = tools_menu.Append(
            wx.ID_ANY, "&Listening Statistics...", "View your listening statistics"
        )
        self.menu_export_import = tools_menu.Append(
            wx.ID_ANY, "&Export/Import Settings...", "Backup or restore your settings"
        )
        tools_menu.AppendSeparator()

        self.menu_auto_play = tools_menu.Append(
            wx.ID_ANY, "&Auto-Play on Startup...", "Configure auto-play settings"
        )
        self.menu_quiet_hours = tools_menu.Append(
            wx.ID_ANY, "&Quiet Hours...", "Configure quiet hours"
        )
        self.menu_toggle_audio_ducking = tools_menu.AppendCheckItem(
            wx.ID_ANY, "Enable Audio &Ducking", "Lower volume during system sounds"
        )
        self.menu_audio_ducking_settings = tools_menu.Append(
            wx.ID_ANY, "Audio Ducking &Settings...", "Configure audio ducking percentage and delay"
        )
        self.menu_toggle_media_keys = tools_menu.AppendCheckItem(
            wx.ID_ANY, "&Media Key Support", "Use keyboard media keys"
        )
        tools_menu.AppendSeparator()

        self.menu_clear_cache = tools_menu.Append(
            wx.ID_ANY, "Clear &Cache...", "Clear application cache"
        )
        self.menu_clear_recent = tools_menu.Append(
            wx.ID_ANY, "Clear &Recent Items...", "Clear recent items history"
        )
        tools_menu.AppendSeparator()

        self.menu_affiliate_admin = tools_menu.Append(
            wx.ID_ANY,
            "Affiliate Correction &Admin...\tCtrl+Shift+A",
            "Review and approve affiliate data corrections (Admin)",
        )

        menubar.Append(tools_menu, "&Tools")

        # ===== HELP MENU =====
        help_menu = wx.Menu()

        self.menu_user_guide = help_menu.Append(wx.ID_ANY, "&User Guide\tF1", "Open user guide")
        self.menu_shortcuts = help_menu.Append(
            wx.ID_ANY, "&Keyboard Shortcuts", "Show keyboard shortcuts"
        )
        help_menu.AppendSeparator()

        # Announcements submenu
        self.menu_announcements = help_menu.Append(
            wx.ID_ANY, "&Announcements...\tCtrl+Shift+A", "View announcements and updates"
        )
        self.menu_whats_new = help_menu.Append(
            wx.ID_ANY, "&What's New in This Version", "See what's new in this version of ACB Link"
        )
        help_menu.AppendSeparator()

        self.menu_acb_website = help_menu.Append(wx.ID_ANY, "ACB &Website", "Visit ACB website")
        self.menu_check_updates = help_menu.Append(
            wx.ID_ANY, "Check for &Updates", "Check for application updates"
        )
        help_menu.AppendSeparator()

        self.menu_send_feedback = help_menu.Append(
            wx.ID_ANY, "Send &Feedback...\tCtrl+Shift+F", "Send feedback or report an issue"
        )
        self.menu_suggest_affiliate_correction = help_menu.Append(
            wx.ID_ANY,
            "Suggest &Affiliate Correction...\tCtrl+Shift+E",
            "Suggest corrections to state or SIG affiliate information",
        )
        help_menu.AppendSeparator()

        self.menu_about = help_menu.Append(wx.ID_ABOUT, "&About ACB Link", "About this application")

        menubar.Append(help_menu, "&Help")

        self.SetMenuBar(menubar)

    def _build_statusbar(self):
        """Build the status bar."""
        self.statusbar = self.CreateStatusBar(3)
        self.statusbar.SetStatusWidths([-3, -1, -1])
        self.statusbar.SetStatusText("Ready", 0)
        self.statusbar.SetStatusText("", 1)  # Playback status
        self.statusbar.SetStatusText("", 2)  # Recording status

    def _build_ui(self):
        """Build the main UI."""
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Notebook for tabs
        self.notebook = wx.Notebook(main_panel)

        # Create panels
        self.home_panel = HomePanel(
            self.notebook, self.settings, self._play_stream, self._play_podcast
        )
        self.streams_panel = StreamsPanel(
            self.notebook, self._play_stream, self._start_recording, self._stop_recording
        )
        self.podcasts_panel = PodcastsPanel(self.notebook, self._play_podcast_episode)
        self.affiliates_panel = AffiliatesPanel(
            self.notebook, on_suggest_correction=self._on_suggest_affiliate_correction
        )
        self.resources_panel = ResourcesPanel(self.notebook)

        # Add pages
        self.notebook.AddPage(self.home_panel, "Home")
        self.notebook.AddPage(self.streams_panel, "Streams")
        self.notebook.AddPage(self.podcasts_panel, "Podcasts")
        self.notebook.AddPage(self.affiliates_panel, "Affiliates")
        self.notebook.AddPage(self.resources_panel, "Resources")

        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

        # Player controls panel
        player_panel = self._build_player_controls(main_panel)
        main_sizer.Add(player_panel, 0, wx.EXPAND | wx.ALL, 5)

        main_panel.SetSizer(main_sizer)

        # Set default tab
        if self.settings.default_tab in TAB_NAMES:
            self.notebook.SetSelection(TAB_NAMES.index(self.settings.default_tab))

        # Register navigable panes for F6 navigation
        self._register_panes()

        # Apply initial view settings
        self._apply_view_settings()

    def _build_player_controls(self, parent) -> wx.Panel:
        """Build the media player controls panel with modern styling."""
        panel = wx.Panel(parent)
        self.player_panel = panel  # Store reference for theming

        # Apply initial styling
        scheme = self.style_manager.scheme
        panel.SetBackgroundColour(hex_to_colour(scheme.player_bg))

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Progress bar (visual separator at top)
        progress_panel = wx.Panel(panel, size=(-1, 4))
        progress_panel.SetBackgroundColour(hex_to_colour(scheme.accent))
        main_sizer.Add(progress_panel, 0, wx.EXPAND)

        # Controls sizer
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        controls_sizer.AddSpacer(UIConstants.PADDING_MEDIUM)

        # Now playing section (left)
        now_playing_sizer = wx.BoxSizer(wx.VERTICAL)

        self.now_playing_label = wx.StaticText(panel, label="Now Playing")
        label_font = self.now_playing_label.GetFont()
        label_font.SetPointSize(9)
        self.now_playing_label.SetFont(label_font)
        self.now_playing_label.SetForegroundColour(hex_to_colour(scheme.text_secondary))
        now_playing_sizer.Add(self.now_playing_label, 0, wx.BOTTOM, 2)

        self.now_playing = wx.StaticText(panel, label="Not playing")
        title_font = self.now_playing.GetFont()
        title_font.SetPointSize(12)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.now_playing.SetFont(title_font)
        self.now_playing.SetForegroundColour(hex_to_colour(scheme.text_primary))
        self.now_playing.SetMinSize((280, -1))
        now_playing_sizer.Add(self.now_playing, 0)

        controls_sizer.Add(
            now_playing_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, UIConstants.PADDING_MEDIUM
        )
        controls_sizer.AddStretchSpacer()

        # Playback buttons (center) with WCAG 2.2 AA accessible names
        playback_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Create modern playback buttons with accessible names
        btn_size = (UIConstants.ICON_BUTTON_SIZE, UIConstants.ICON_BUTTON_SIZE)
        btn_large_size = (UIConstants.ICON_BUTTON_SIZE + 8, UIConstants.ICON_BUTTON_SIZE + 8)

        self.btn_skip_back = wx.Button(panel, label="⏮", size=btn_size)
        make_button_accessible(
            self.btn_skip_back,
            "Skip Backward",
            "Ctrl+Left",
            f"Skip back {self.settings.playback.skip_backward_seconds} seconds",
        )
        self.btn_skip_back.Bind(wx.EVT_BUTTON, self._on_skip_back)
        playback_sizer.Add(self.btn_skip_back, 0, wx.ALL, 2)

        self.btn_play_pause = wx.Button(panel, label="▶", size=btn_large_size)
        make_button_accessible(self.btn_play_pause, "Play", "Space", "Play or pause playback")
        self.btn_play_pause.Bind(wx.EVT_BUTTON, self._on_play_pause)
        self.btn_play_pause.SetBackgroundColour(hex_to_colour(scheme.accent))
        self.btn_play_pause.SetForegroundColour(hex_to_colour("#FFFFFF"))
        playback_sizer.Add(self.btn_play_pause, 0, wx.ALL, 2)

        self.btn_stop = wx.Button(panel, label="⏹", size=btn_size)
        make_button_accessible(self.btn_stop, "Stop", "Ctrl+S", "Stop playback")
        self.btn_stop.Bind(wx.EVT_BUTTON, self._on_stop)
        playback_sizer.Add(self.btn_stop, 0, wx.ALL, 2)

        self.btn_skip_fwd = wx.Button(panel, label="⏭", size=btn_size)
        make_button_accessible(
            self.btn_skip_fwd,
            "Skip Forward",
            "Ctrl+Right",
            f"Skip forward {self.settings.playback.skip_forward_seconds} seconds",
        )
        self.btn_skip_fwd.Bind(wx.EVT_BUTTON, self._on_skip_forward)
        playback_sizer.Add(self.btn_skip_fwd, 0, wx.ALL, 2)

        controls_sizer.Add(
            playback_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, UIConstants.PADDING_SMALL
        )
        controls_sizer.AddStretchSpacer()

        # Volume section (right) with accessible names
        volume_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_mute = wx.Button(panel, label="🔊", size=(32, 32))
        make_button_accessible(self.btn_mute, "Mute", "Ctrl+M", "Toggle audio mute")
        self.btn_mute.Bind(wx.EVT_BUTTON, self._on_mute)
        volume_sizer.Add(self.btn_mute, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        self.volume_slider = wx.Slider(
            panel,
            value=self.settings.playback.default_volume,
            minValue=0,
            maxValue=100,
            size=(120, -1),
            style=wx.SL_HORIZONTAL,
        )
        self.volume_slider.SetName("Volume")
        self.volume_slider.SetToolTip("Volume slider - Use arrow keys to adjust")
        self.volume_slider.Bind(wx.EVT_SLIDER, self._on_volume_change)
        volume_sizer.Add(self.volume_slider, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        self.vol_value = wx.StaticText(panel, label=f"{self.settings.playback.default_volume}%")
        self.vol_value.SetMinSize((40, -1))
        self.vol_value.SetName("Volume level")
        self.vol_value.SetForegroundColour(hex_to_colour(scheme.text_secondary))
        volume_sizer.Add(self.vol_value, 0, wx.ALIGN_CENTER_VERTICAL)

        controls_sizer.Add(
            volume_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, UIConstants.PADDING_MEDIUM
        )

        # Record button (far right) with accessible name
        self.btn_record = wx.Button(panel, label="⏺", size=btn_size)
        make_button_accessible(
            self.btn_record, "Record", "Ctrl+R", "Start or stop recording current stream"
        )
        self.btn_record.Bind(wx.EVT_BUTTON, self._on_record_toggle)
        self.btn_record.SetForegroundColour(hex_to_colour(scheme.error))
        controls_sizer.Add(
            self.btn_record, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, UIConstants.PADDING_MEDIUM
        )

        controls_sizer.AddSpacer(UIConstants.PADDING_MEDIUM)

        main_sizer.Add(controls_sizer, 1, wx.EXPAND)
        panel.SetSizer(main_sizer)

        # Set minimum height for player bar
        panel.SetMinSize((-1, UIConstants.PLAYER_BAR_HEIGHT))

        return panel

    def _setup_accelerators(self):
        """Set up keyboard accelerators."""
        accel_entries = [
            # Tab navigation (direct access)
            (wx.ACCEL_CTRL, ord("1"), self.menu_home.GetId()),
            (wx.ACCEL_CTRL, ord("2"), self.menu_streams_tab.GetId()),
            (wx.ACCEL_CTRL, ord("3"), self.menu_podcasts_tab.GetId()),
            (wx.ACCEL_CTRL, ord("4"), self.menu_affiliates_tab.GetId()),
            (wx.ACCEL_CTRL, ord("5"), self.menu_resources_tab.GetId()),
            # Tab cycling (Ctrl+Tab / Ctrl+Shift+Tab)
            (wx.ACCEL_CTRL, wx.WXK_TAB, self.menu_next_tab.GetId()),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, wx.WXK_TAB, self.menu_prev_tab.GetId()),
            # Pane navigation (F6 / Shift+F6)
            (wx.ACCEL_NORMAL, wx.WXK_F6, self.menu_next_pane.GetId()),
            (wx.ACCEL_SHIFT, wx.WXK_F6, self.menu_prev_pane.GetId()),
            # View toggles
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("D"), self.menu_focus_mode.GetId()),
            (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, ord("P"), self.menu_show_player.GetId()),
            # Affiliate correction
            (
                wx.ACCEL_CTRL | wx.ACCEL_SHIFT,
                ord("E"),
                self.menu_suggest_affiliate_correction.GetId(),
            ),
            # Quick dial (Alt+F1-F5)
            (wx.ACCEL_ALT, wx.WXK_F1, self.menu_quick_dial_1.GetId()),
            (wx.ACCEL_ALT, wx.WXK_F2, self.menu_quick_dial_2.GetId()),
            (wx.ACCEL_ALT, wx.WXK_F3, self.menu_quick_dial_3.GetId()),
            # Note: Alt+F4 is reserved for system close, so we skip it in accelerators
            (wx.ACCEL_ALT, wx.WXK_F5, self.menu_quick_dial_5.GetId()),
        ]
        accel_table = wx.AcceleratorTable(accel_entries)
        self.SetAcceleratorTable(accel_table)

    def _bind_events(self):
        """Bind menu and other events."""
        # File menu
        self.Bind(wx.EVT_MENU, self._on_open_browser, self.menu_open_browser)
        self.Bind(wx.EVT_MENU, self._on_settings, self.menu_settings)
        self.Bind(wx.EVT_MENU, self._on_advanced_settings, self.menu_advanced_settings)
        self.Bind(wx.EVT_MENU, self._on_exit, self.menu_exit)

        # Playback menu
        self.Bind(wx.EVT_MENU, self._on_play_pause, self.menu_play_pause)
        self.Bind(wx.EVT_MENU, self._on_stop, self.menu_stop)
        self.Bind(wx.EVT_MENU, self._on_skip_back, self.menu_skip_back)
        self.Bind(wx.EVT_MENU, self._on_skip_forward, self.menu_skip_fwd)
        self.Bind(wx.EVT_MENU, self._on_volume_up, self.menu_vol_up)
        self.Bind(wx.EVT_MENU, self._on_volume_down, self.menu_vol_down)
        self.Bind(wx.EVT_MENU, self._on_mute, self.menu_mute)
        self.Bind(wx.EVT_MENU, self._on_record_toggle, self.menu_record)
        self.Bind(wx.EVT_MENU, self._on_sleep_timer, self.menu_sleep_timer)
        self.Bind(wx.EVT_MENU, self._on_playback_speed, self.menu_playback_speed)
        self.Bind(wx.EVT_MENU, self._on_copy_now_playing, self.menu_copy_now_playing)
        self.Bind(wx.EVT_MENU, self._on_recently_played, self.menu_recently_played)

        # Edit menu
        self.Bind(wx.EVT_MENU, self._on_copy, self.menu_copy)
        self.Bind(wx.EVT_MENU, self._on_select_all, self.menu_select_all)
        self.Bind(wx.EVT_MENU, self._on_copy_now_playing, self.menu_copy_now_playing)
        self.Bind(wx.EVT_MENU, self._on_copy_stream_url, self.menu_copy_stream_url)
        self.Bind(wx.EVT_MENU, self._on_settings, self.menu_preferences)

        # View menu - tab navigation
        self.Bind(wx.EVT_MENU, lambda e: self.notebook.SetSelection(0), self.menu_home)
        self.Bind(wx.EVT_MENU, lambda e: self.notebook.SetSelection(1), self.menu_streams_tab)
        self.Bind(wx.EVT_MENU, lambda e: self.notebook.SetSelection(2), self.menu_podcasts_tab)
        self.Bind(wx.EVT_MENU, lambda e: self.notebook.SetSelection(3), self.menu_affiliates_tab)
        self.Bind(wx.EVT_MENU, lambda e: self.notebook.SetSelection(4), self.menu_resources_tab)

        # View menu - show/hide UI elements
        self.Bind(wx.EVT_MENU, self._on_toggle_toolbar, self.menu_show_toolbar)
        self.Bind(wx.EVT_MENU, self._on_toggle_tab_bar, self.menu_show_tab_bar)
        self.Bind(wx.EVT_MENU, self._on_toggle_status_bar, self.menu_show_status_bar)
        self.Bind(wx.EVT_MENU, self._on_toggle_player_panel, self.menu_show_player)
        self.Bind(wx.EVT_MENU, self._on_toggle_now_playing, self.menu_show_now_playing)
        self.Bind(wx.EVT_MENU, self._on_toggle_sidebar, self.menu_show_sidebar)

        # View menu - pane navigation
        self.Bind(wx.EVT_MENU, self._on_next_pane, self.menu_next_pane)
        self.Bind(wx.EVT_MENU, self._on_prev_pane, self.menu_prev_pane)

        # View menu - tab cycling
        self.Bind(wx.EVT_MENU, self._on_next_tab, self.menu_next_tab)
        self.Bind(wx.EVT_MENU, self._on_prev_tab, self.menu_prev_tab)

        # View menu - modes
        self.Bind(wx.EVT_MENU, self._on_toggle_focus_mode, self.menu_focus_mode)
        self.Bind(wx.EVT_MENU, self._on_toggle_full_screen, self.menu_full_screen)

        # View menu - quick actions and text size
        self.Bind(wx.EVT_MENU, self._on_quick_status, self.menu_quick_status)
        self.Bind(wx.EVT_MENU, self._on_panic_key, self.menu_panic_key)
        self.Bind(wx.EVT_MENU, self._on_increase_font, self.menu_increase_font)
        self.Bind(wx.EVT_MENU, self._on_decrease_font, self.menu_decrease_font)
        self.Bind(wx.EVT_MENU, self._on_reset_font, self.menu_reset_font)
        self.Bind(wx.EVT_MENU, self._on_view_settings, self.menu_view_settings)

        # View menu - podcast sorting
        self.Bind(
            wx.EVT_MENU, lambda e: self._on_podcast_sort("date_newest"), self.menu_sort_date_newest
        )
        self.Bind(
            wx.EVT_MENU, lambda e: self._on_podcast_sort("date_oldest"), self.menu_sort_date_oldest
        )
        self.Bind(wx.EVT_MENU, lambda e: self._on_podcast_sort("title_az"), self.menu_sort_title_az)
        self.Bind(wx.EVT_MENU, lambda e: self._on_podcast_sort("title_za"), self.menu_sort_title_za)
        self.Bind(
            wx.EVT_MENU,
            lambda e: self._on_podcast_sort("duration_longest"),
            self.menu_sort_duration_long,
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self._on_podcast_sort("duration_shortest"),
            self.menu_sort_duration_short,
        )
        self.Bind(
            wx.EVT_MENU, lambda e: self._on_podcast_sort("unplayed_first"), self.menu_sort_unplayed
        )
        self.Bind(
            wx.EVT_MENU,
            lambda e: self._on_podcast_sort("downloaded_first"),
            self.menu_sort_downloaded,
        )

        # View menu - customize home page
        self.Bind(wx.EVT_MENU, self._on_customize_home, self.menu_customize_home)

        # Streams menu - quick dial
        self.Bind(wx.EVT_MENU, lambda e: self.quick_dial.play_by_index(0), self.menu_quick_dial_1)
        self.Bind(wx.EVT_MENU, lambda e: self.quick_dial.play_by_index(1), self.menu_quick_dial_2)
        self.Bind(wx.EVT_MENU, lambda e: self.quick_dial.play_by_index(2), self.menu_quick_dial_3)
        self.Bind(wx.EVT_MENU, lambda e: self.quick_dial.play_by_index(3), self.menu_quick_dial_4)
        self.Bind(wx.EVT_MENU, lambda e: self.quick_dial.play_by_index(4), self.menu_quick_dial_5)

        # Tools menu
        self.Bind(wx.EVT_MENU, self._on_sync_data, self.menu_sync_data)
        self.Bind(wx.EVT_MENU, self._on_start_server, self.menu_start_server)
        self.Bind(wx.EVT_MENU, self._on_stop_server, self.menu_stop_server)
        self.Bind(wx.EVT_MENU, self._on_scheduled_tasks, self.menu_scheduled_tasks)
        self.Bind(wx.EVT_MENU, self._on_listening_stats, self.menu_listening_stats)
        self.Bind(wx.EVT_MENU, self._on_export_import, self.menu_export_import)
        self.Bind(wx.EVT_MENU, self._on_clear_cache, self.menu_clear_cache)
        self.Bind(wx.EVT_MENU, self._on_clear_recent, self.menu_clear_recent)
        self.Bind(wx.EVT_MENU, self._on_auto_play, self.menu_auto_play)
        self.Bind(wx.EVT_MENU, self._on_quiet_hours, self.menu_quiet_hours)
        self.Bind(wx.EVT_MENU, self._on_toggle_audio_ducking, self.menu_toggle_audio_ducking)
        self.Bind(wx.EVT_MENU, self._on_audio_ducking_settings, self.menu_audio_ducking_settings)
        self.Bind(wx.EVT_MENU, self._on_toggle_media_keys, self.menu_toggle_media_keys)
        self.Bind(wx.EVT_MENU, self._on_affiliate_admin, self.menu_affiliate_admin)

        # Help menu
        self.Bind(wx.EVT_MENU, self._on_user_guide, self.menu_user_guide)
        self.Bind(wx.EVT_MENU, self._on_shortcuts, self.menu_shortcuts)
        self.Bind(wx.EVT_MENU, self._on_view_announcements, self.menu_announcements)
        self.Bind(wx.EVT_MENU, self._on_whats_new, self.menu_whats_new)
        self.Bind(wx.EVT_MENU, self._on_acb_website, self.menu_acb_website)
        self.Bind(wx.EVT_MENU, self._on_check_updates, self.menu_check_updates)
        self.Bind(wx.EVT_MENU, self._on_send_feedback, self.menu_send_feedback)
        self.Bind(
            wx.EVT_MENU,
            self._on_suggest_affiliate_correction_menu,
            self.menu_suggest_affiliate_correction,
        )
        self.Bind(wx.EVT_MENU, self._on_about, self.menu_about)

        # Window events
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_ICONIZE, self._on_iconize)

    def _init_announcement_system(self):
        """Initialize the announcement system."""
        try:
            from .announcements import initialize_announcement_manager

            # Initialize with app data directory
            data_dir = Path.home() / ".acb_link"
            self.announcement_manager = initialize_announcement_manager(data_dir)

            # Register callbacks
            self.announcement_manager.add_critical_announcement_callback(
                self._on_critical_announcement
            )
            self.announcement_manager.add_new_announcements_callback(self._on_new_announcements)

            self.logger.info("Announcement system initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize announcement system: {e}")
            self.announcement_manager = None

    def _check_announcements_on_startup(self):
        """Check for announcements on startup if enabled."""
        if self.announcement_manager is None:
            return

        settings = self.announcement_manager.settings

        # Check for unacknowledged critical announcements first
        critical = self.announcement_manager.get_critical_unacknowledged()
        for announcement in critical:
            wx.CallAfter(self._show_critical_announcement, announcement)

        # Fetch new announcements if enabled
        if settings.check_on_startup:
            self.announcement_manager.fetch_announcements(callback=self._on_announcements_fetched)

        # Start background checking if configured
        if settings.check_interval_minutes > 0:
            self.announcement_manager.start_background_checking()

    def _on_announcements_fetched(self, success: bool, message: str):
        """Handle announcement fetch completion."""
        if success:
            self.logger.info(f"Announcements: {message}")
            # Check for critical announcements that need immediate attention
            critical = self.announcement_manager.get_critical_unacknowledged()
            for announcement in critical:
                wx.CallAfter(self._show_critical_announcement, announcement)
        else:
            self.logger.warning(f"Failed to fetch announcements: {message}")

    def _on_critical_announcement(self, announcement):
        """Handle critical announcement callback."""
        wx.CallAfter(self._show_critical_announcement, announcement)

    def _show_critical_announcement(self, announcement):
        """Show critical announcement dialog."""
        try:
            from .announcement_ui import CriticalAnnouncementDialog

            dialog = CriticalAnnouncementDialog(self, announcement, self.announcement_manager)
            dialog.ShowModal()
            dialog.Destroy()
        except Exception as e:
            self.logger.error(f"Failed to show critical announcement: {e}")

    def _on_new_announcements(self, announcements):
        """Handle new announcements callback."""
        count = len(announcements)
        if count > 0:
            self.logger.info(f"Received {count} new announcement(s)")
            # Update status bar
            if hasattr(self, "statusbar"):
                self.statusbar.SetStatusText(f"{count} new announcement(s)", 0)
            # Refresh home panel if visible
            if hasattr(self, "home_panel"):
                wx.CallAfter(self.home_panel.refresh_announcements)

    def _on_view_announcements(self, event):
        """Show announcement history dialog."""
        try:
            from .announcement_ui import AnnouncementHistoryDialog

            dialog = AnnouncementHistoryDialog(self, self.announcement_manager)
            dialog.ShowModal()
            dialog.Destroy()
        except Exception as e:
            self.logger.error(f"Failed to show announcements: {e}")

    def _on_admin_create_announcement(self, event):
        """Show admin announcement creation dialog."""
        try:
            from .announcement_ui import AdminAnnouncementDialog

            dialog = AdminAnnouncementDialog(self, self.announcement_manager)
            if dialog.ShowModal() == wx.ID_OK:
                announce("Announcement published")
            dialog.Destroy()
        except Exception as e:
            self.logger.error(f"Failed to create announcement: {e}")

    def _init_tray_icon(self):
        """Initialize system tray icon."""
        self.tray_icon = ACBLinkTaskBarIcon(
            frame=self,
            on_play_pause=self._on_play_pause,
            on_stop=self._on_stop,
            on_record=self._on_record_toggle,
            on_settings=self._on_settings,
            streams=STREAMS,
        )
        if self.settings.system_tray.show_notifications:
            self.tray_icon.show_notification("ACB Link", "Application started")

    def _start_server(self):
        """Start the local web server."""
        try:
            self.web_server.start()
            self.statusbar.SetStatusText("Server running", 0)
            self.logger.info(f"Web server started at {self.web_server.base_url}")
        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")

    def _apply_theme(self):
        """Apply theme settings to the UI."""
        theme = self.settings.theme

        # Update style manager
        if theme and theme.name:
            self.style_manager.set_scheme(theme.name)
        if theme:
            self.style_manager.set_font_size(theme.font_size)

        # Apply styles to entire window hierarchy
        self.style_manager.apply_to_window(self)

        # Special styling for player panel
        if hasattr(self, "player_panel"):
            self.style_manager.style_player_panel(self.player_panel)

        # Refresh display
        self.Refresh()
        self.Update()

    # Playback handlers

    def _play_stream(self, stream_name: str):
        """Play a stream by name."""
        if stream_name not in STREAMS:
            return

        station_id = STREAMS[stream_name]
        url = f"https://live365.com/station/{station_id}"

        self.current_stream = stream_name
        self.now_playing.SetLabel(f"Playing: {stream_name}")
        self.statusbar.SetStatusText(f"Playing: {stream_name}", 1)
        self.btn_play_pause.SetLabel("⏸")
        make_button_accessible(self.btn_play_pause, "Pause", "Space", "Pause playback")

        # Update streams panel
        self.streams_panel.set_stream_status(stream_name, "Playing")

        # Add to recent
        self.recent_items.add_item("stream", stream_name, station_id=station_id)

        # Add to recently played (new manager)
        self.recently_played.add("stream", stream_name, url=url)

        # Track listening stats
        self.listening_stats.start_session("stream", stream_name)

        # Save resume state
        self.resume_manager.save_state("stream", stream_name, url)

        # Open in browser (since we can't embed Live365)
        webbrowser.open(url)

        # Announce to screen reader (WCAG 4.1.3 Status Messages)
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"Now playing {stream_name}")

        # Notify tray
        if self.tray_icon and self.settings.system_tray.show_notifications:
            self.tray_icon.show_notification("Now Playing", stream_name)

        self.logger.info(f"Playing stream: {stream_name}")

    def _play_podcast(self, category: str, podcast_name: str):
        """Play a podcast."""
        if category in PODCASTS and podcast_name in PODCASTS[category]:
            feed_url = PODCASTS[category][podcast_name]
            self.now_playing.SetLabel(f"Podcast: {podcast_name}")
            self.recent_items.add_item("podcast", podcast_name, category=category)
            # TODO: Parse RSS and play first episode
            webbrowser.open(feed_url)

    def _play_podcast_episode(self, podcast_name: str, episode_index: int):
        """Play a specific podcast episode."""
        self.now_playing.SetLabel(f"Episode from: {podcast_name}")
        # TODO: Implement episode playback

    def _start_recording(self, stream_name: str):
        """Start recording a stream."""
        self.is_recording = True
        self.btn_record.SetLabel("⏹")
        self.btn_record.SetToolTip("Stop recording")
        self.statusbar.SetStatusText("Recording...", 2)

        if self.tray_icon:
            self.tray_icon.set_recording_state(True)

        self.logger.info(f"Started recording: {stream_name}")

    def _stop_recording(self):
        """Stop recording."""
        self.is_recording = False
        self.btn_record.SetLabel("⏺")
        self.btn_record.SetToolTip("Start recording")
        self.statusbar.SetStatusText("", 2)

        if self.tray_icon:
            self.tray_icon.set_recording_state(False)

        self.logger.info("Stopped recording")

    # Event handlers

    def _on_play_pause(self, event):
        """Toggle play/pause."""
        # TODO: Implement media control
        pass

    def _on_stop(self, event):
        """Stop playback."""
        # End listening session for stats
        self.listening_stats.end_session()

        self.current_stream = None
        self.now_playing.SetLabel("Not playing")
        self.statusbar.SetStatusText("", 1)
        self.btn_play_pause.SetLabel("▶")

    def _on_skip_back(self, event):
        """Skip backward."""
        # TODO: Implement skip
        pass

    def _on_skip_forward(self, event):
        """Skip forward."""
        # TODO: Implement skip
        pass

    def _on_volume_change(self, event):
        """Handle volume slider change."""
        vol = self.volume_slider.GetValue()
        self.vol_value.SetLabel(f"{vol}%")

    def _on_volume_up(self, event):
        """Increase volume."""
        current = self.volume_slider.GetValue()
        self.volume_slider.SetValue(min(100, current + 5))
        self._on_volume_change(None)

    def _on_volume_down(self, event):
        """Decrease volume."""
        current = self.volume_slider.GetValue()
        self.volume_slider.SetValue(max(0, current - 5))
        self._on_volume_change(None)

    def _on_mute(self, event):
        """Toggle mute."""
        # TODO: Implement mute
        pass

    def _on_record_toggle(self, event):
        """Toggle recording."""
        if self.is_recording:
            self._stop_recording()
        elif self.current_stream:
            self._start_recording(self.current_stream)

    def _on_open_browser(self, event):
        """Open current content in browser."""
        self.web_server.open_in_browser("/", self.settings.preferred_browser)

    def _on_settings(self, event):
        """Open settings dialog."""
        dlg = SettingsDialog(self, self.settings)
        if dlg.ShowModal() == wx.ID_OK:
            self.settings = dlg.get_settings()
            self.settings.save()
            self._apply_theme()

            # Update tray icon
            if self.settings.system_tray.enabled and not self.tray_icon:
                self._init_tray_icon()
            elif not self.settings.system_tray.enabled and self.tray_icon:
                self.tray_icon.Destroy()
                self.tray_icon = None
        dlg.Destroy()

    def _on_advanced_settings(self, event):
        """Open advanced settings dialog with configuration options."""
        config = get_config()
        if show_advanced_settings(self, config, self.settings):
            # Settings were changed and saved
            announce("Advanced settings saved. Some changes may require restart.")
            self.statusbar.SetStatusText("Advanced settings updated", 0)

    def _on_start_server(self, event):
        """Start web server."""
        if not self.web_server.is_running():
            self._start_server()

    def _on_stop_server(self, event):
        """Stop web server."""
        self.web_server.stop()
        self.statusbar.SetStatusText("Server stopped", 0)

    def _on_sync_data(self, event):
        """Synchronize data with ACB servers."""
        from .accessibility import announce
        from .data_sync import get_sync_manager

        # Create progress dialog
        progress = wx.ProgressDialog(
            "Synchronizing Data",
            "Connecting to ACB servers...",
            maximum=100,
            parent=self,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT,
        )

        announce("Synchronizing data with ACB servers")

        def update_progress(source_name: str, current: int, total: int):
            percent = int((current / total) * 100)
            message = f"Syncing {source_name}... ({current}/{total})"
            wx.CallAfter(progress.Update, percent, message)

        try:
            sync_manager = get_sync_manager()
            sync_manager.set_progress_callback(update_progress)

            # Run sync in background
            import threading

            result_holder = [None]

            def do_sync():
                result_holder[0] = sync_manager.sync_all(force=True)

            thread = threading.Thread(target=do_sync)
            thread.start()

            # Wait for completion with progress updates
            while thread.is_alive():
                wx.Yield()
                thread.join(0.1)

            progress.Destroy()

            status = result_holder[0]
            if status:
                # Show results
                if status.total_changes > 0:
                    message = "Sync complete.\n\n"
                    message += (
                        f"Sources updated: {status.successful_sources}/{status.total_sources}\n"
                    )
                    message += f"Total changes: {status.total_changes}"

                    announce(f"Sync complete. {status.total_changes} changes found.")
                    wx.MessageBox(message, "Sync Complete", wx.OK | wx.ICON_INFORMATION)
                else:
                    announce("Data is up to date. No changes found.")
                    wx.MessageBox(
                        "All data is up to date.", "Sync Complete", wx.OK | wx.ICON_INFORMATION
                    )

        except Exception as e:
            progress.Destroy()
            self.logger.error(f"Sync failed: {e}")
            announce("Sync failed")
            wx.MessageBox(f"Sync failed: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def _on_scheduled_tasks(self, event):
        """Show scheduled tasks dialog."""
        from .accessibility import announce

        announce("Scheduled tasks dialog")

        # Show simple list for now
        from .scheduler import list_scheduled_tasks

        try:
            tasks = list_scheduled_tasks()

            if tasks:
                message = "Scheduled Tasks:\n\n"
                for task in tasks:
                    message += f"• {task.name}\n"
                    message += f"  Scheduled: {task.scheduled_time}\n"
                    message += f"  Type: {task.task_type.value}\n\n"
            else:
                message = "No scheduled tasks."

            wx.MessageBox(message, "Scheduled Tasks", wx.OK | wx.ICON_INFORMATION)

        except Exception as e:
            self.logger.error(f"Failed to list tasks: {e}")
            wx.MessageBox(
                "No scheduled tasks found.", "Scheduled Tasks", wx.OK | wx.ICON_INFORMATION
            )

    def _on_clear_cache(self, event):
        """Clear application cache."""
        if (
            wx.MessageBox("Clear all cached data?", "Clear Cache", wx.YES_NO | wx.ICON_QUESTION)
            == wx.YES
        ):
            from .utils import CacheManager

            cache = CacheManager()
            cache.clear_cache()
            wx.MessageBox("Cache cleared.", "Success", wx.OK | wx.ICON_INFORMATION)

    def _on_clear_recent(self, event):
        """Clear recent items."""
        if (
            wx.MessageBox(
                "Clear recent items history?", "Clear History", wx.YES_NO | wx.ICON_QUESTION
            )
            == wx.YES
        ):
            self.recent_items.clear()
            wx.MessageBox("History cleared.", "Success", wx.OK | wx.ICON_INFORMATION)

    def _on_affiliate_admin(self, event):
        """Show affiliate correction admin dialog."""
        try:
            # Get the XML directory path
            from pathlib import Path

            from .affiliate_admin import show_admin_review_dialog

            xml_dir = Path(__file__).parent.parent / "data" / "s3"

            show_admin_review_dialog(self, xml_dir=xml_dir)
        except ImportError as e:
            self.logger.error(f"Failed to load affiliate admin module: {e}")
            wx.MessageBox(
                "Affiliate admin module is not available.", "Error", wx.OK | wx.ICON_ERROR
            )
        except Exception as e:
            self.logger.error(f"Error opening affiliate admin: {e}")
            wx.MessageBox(f"Error opening affiliate admin: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def _on_listening_stats(self, event):
        """Show listening statistics dialog."""
        dialog = ListeningStatsDialog(self, self.listening_stats.stats)
        dialog.ShowModal()
        dialog.Destroy()

    def _on_export_import(self, event):
        """Show export/import settings dialog."""
        dialog = ExportImportDialog(self, self.backup_manager)
        dialog.ShowModal()
        dialog.Destroy()

    def _on_quick_status(self, event):
        """Announce current playback status (F5)."""
        status = self.quick_status.announce_status()
        # Also show in status bar briefly
        self.statusbar.SetStatusText(status, 0)

    def _on_panic_key(self, event):
        """Panic key - mute and minimize (Ctrl+Shift+M)."""
        self.panic_handler.activate()

    def _on_increase_font(self, event):
        """Increase font size (Ctrl+Plus)."""
        new_size = self.font_size_manager.increase()
        announce(f"Text size: {new_size}")

    def _on_decrease_font(self, event):
        """Decrease font size (Ctrl+Minus)."""
        new_size = self.font_size_manager.decrease()
        announce(f"Text size: {new_size}")

    def _on_reset_font(self, event):
        """Reset font size to default (Ctrl+0)."""
        new_size = self.font_size_manager.reset()
        announce(f"Text size reset to {new_size}")

    def _on_font_size_changed(self, new_size: int):
        """Handle font size change."""
        self.style_manager.set_font_size(new_size)
        self.settings.theme.font_size = new_size
        self.settings.save()
        self._apply_theme()

    def _toggle_mute(self):
        """Toggle mute state."""
        self._on_mute(None)

    def _minimize_to_tray(self):
        """Minimize window to tray or taskbar."""
        self.Iconize(True)
        if self.settings.system_tray.minimize_to_tray:
            self.Hide()

    def _get_playback_state(self) -> str:
        """Get current playback state as string."""
        if hasattr(self, "native_player") and self.native_player:
            if self.native_player.is_playing():
                return "playing"
            elif self.native_player.is_paused():
                return "paused"
        return "stopped"

    # =========================================================================
    # PLAYBACK ENHANCEMENT HANDLERS
    # =========================================================================

    def _on_sleep_timer(self, event):
        """Show sleep timer dialog."""
        remaining = self.enhanced_sleep_timer.get_remaining()
        dialog = SleepTimerDialog(self, remaining)
        result = dialog.ShowModal()

        if result == wx.ID_OK:
            minutes = dialog.selected_minutes
            if minutes == -1:
                # Cancel timer
                self.enhanced_sleep_timer.cancel()
                announce("Sleep timer cancelled")
            elif minutes > 0:
                self.enhanced_sleep_timer.start(minutes, dialog.enable_fade)
                announce(f"Sleep timer set for {minutes} minutes")

        dialog.Destroy()

    def _on_enhanced_sleep_timer_end(self):
        """Handle enhanced sleep timer end."""
        self._on_stop(None)
        if self.settings.accessibility.screen_reader_announcements:
            announce("Sleep timer ended. Playback stopped.")
        self._show_notification("Sleep Timer", "Playback stopped")

    def _on_sleep_timer_tick(self, remaining_seconds: int):
        """Handle sleep timer tick for status updates."""
        # Update status bar with remaining time
        if remaining_seconds > 0:
            mins = remaining_seconds // 60
            if remaining_seconds <= 60:
                self.statusbar.SetStatusText(f"Sleep: {remaining_seconds}s", 2)
            else:
                self.statusbar.SetStatusText(f"Sleep: {mins}m", 2)

    def _on_sleep_timer_fade_start(self):
        """Handle sleep timer fade start."""
        # Begin gradual volume reduction
        if self.settings.accessibility.screen_reader_announcements:
            announce("Sleep timer fading out in 30 seconds")

    def _on_playback_speed(self, event):
        """Show playback speed dialog."""
        dialog = PlaybackSpeedDialog(self, self.playback_speed)
        dialog.ShowModal()
        dialog.Destroy()

    def _on_playback_speed_changed(self, speed: float):
        """Handle playback speed change."""
        # Apply to native player
        if hasattr(self, "native_player") and self.native_player:
            self.native_player.set_playback_rate(speed)

        # Update settings
        if self.settings.playback:
            self.settings.playback.default_speed = speed
            self.settings.save()

        # Announce
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"Playback speed: {speed}x")

    def _on_copy_now_playing(self, event):
        """Copy what's playing to clipboard."""
        success = self.share_manager.copy_to_clipboard()
        if success:
            announce("Copied to clipboard")
            self.statusbar.SetStatusText("Track info copied", 0)
        else:
            announce("Nothing playing")

    def _get_now_playing_info(self) -> NowPlayingInfo:
        """Get current now playing information."""
        info = NowPlayingInfo()

        if self.current_stream:
            info.content_type = "stream"
            info.stream_name = self.current_stream
            info.title = self.current_stream
            if self.current_stream in STREAMS:
                info.url = f"https://live365.com/station/{STREAMS[self.current_stream]}"

        return info

    def _on_recently_played(self, event):
        """Show recently played dialog."""
        dialog = RecentlyPlayedDialog(self, self.recently_played, self._play_from_recent)
        dialog.ShowModal()
        dialog.Destroy()

    def _play_from_recent(self, item):
        """Play an item from recently played."""
        if item.content_type == "stream":
            self._play_stream(item.name)
        elif item.content_type == "podcast":
            self._play_podcast(item.category, item.name)

        # Update recently played with new timestamp
        self.recently_played.add(
            content_type=item.content_type,
            name=item.name,
            url=item.url,
            category=item.category,
            episode_title=item.episode_title,
        )

    def _on_auto_play(self, event):
        """Show auto-play settings dialog."""
        stream_names = list(STREAMS.keys())
        dialog = AutoPlayDialog(self, self.auto_play_manager, stream_names)
        dialog.ShowModal()
        dialog.Destroy()

    def _on_quiet_hours(self, event):
        """Show quiet hours settings dialog."""
        dialog = QuietHoursDialog(self, self.quiet_hours)
        dialog.ShowModal()
        dialog.Destroy()

    def _on_quiet_hours_start(self):
        """Handle quiet hours starting."""
        if self.quiet_hours.settings.reduce_volume:
            self.audio_ducking.duck(duration_seconds=86400)  # Long duration
        if self.settings.accessibility.screen_reader_announcements:
            announce("Quiet hours started")

    def _on_quiet_hours_end(self):
        """Handle quiet hours ending."""
        self.audio_ducking.restore()
        if self.settings.accessibility.screen_reader_announcements:
            announce("Quiet hours ended")

    def _on_toggle_audio_ducking(self, event):
        """Toggle audio ducking on/off."""
        is_checked = self.menu_toggle_audio_ducking.IsChecked()
        self.audio_ducking.enabled = is_checked
        status = "enabled" if is_checked else "disabled"
        announce(f"Audio ducking {status}")

    def _on_audio_ducking_settings(self, event):
        """Open audio ducking settings dialog."""
        dialog = AudioDuckingDialog(self, self.audio_ducking)
        dialog.ShowModal()
        dialog.Destroy()
        # Update checkbox state in case enabled was changed
        self.menu_toggle_audio_ducking.Check(self.audio_ducking.enabled)

    def _on_toggle_media_keys(self, event):
        """Toggle media key support on/off."""
        is_checked = self.menu_toggle_media_keys.IsChecked()

        if is_checked:
            success = self.media_key_handler.register()
            if success:
                announce("Media key support enabled")
            else:
                self.menu_toggle_media_keys.Check(False)
                announce("Could not enable media keys")
        else:
            self.media_key_handler.unregister()
            announce("Media key support disabled")

    def _on_user_guide(self, event):
        """Open user guide."""
        # TODO: Open local user guide or online version
        webbrowser.open("https://www.acb.org")

    def _on_shortcuts(self, event):
        """Show keyboard shortcuts."""
        shortcuts = """
ACB Link Keyboard Shortcuts

Playback:
  Space           Play/Pause
  Ctrl+S          Stop
  Ctrl+Left       Skip backward
  Ctrl+Right      Skip forward
  Ctrl+Up         Volume up
  Ctrl+Down       Volume down
  Ctrl+M          Mute/Unmute
  Ctrl+R          Record
  Ctrl+T          Sleep timer
  Ctrl+P          Playback speed

Navigation:
  Ctrl+1          Home tab
  Ctrl+2          Streams tab
  Ctrl+3          Podcasts tab
  Ctrl+4          Affiliates tab
  Ctrl+5          Resources tab

Quick Actions:
  F5              Announce current status
  Ctrl+Shift+M    Panic key (mute and minimize)
  Ctrl+Shift+C    Copy what's playing
  Ctrl+Shift+R    Recently played
  Ctrl++          Increase text size
  Ctrl+-          Decrease text size
  Ctrl+0          Reset text size

General:
  Ctrl+B          Open in browser
  Ctrl+,          Settings
  Ctrl+Shift+F    Send feedback
  Ctrl+Shift+E    Suggest affiliate correction
  F1              User Guide
  Alt+F4          Exit
"""
        dlg = wx.MessageDialog(self, shortcuts, "Keyboard Shortcuts", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def _on_acb_website(self, event):
        """Open ACB website."""
        webbrowser.open("https://www.acb.org")

    def _on_check_updates(self, event):
        """Check for application updates using GitHub releases."""
        from . import __version__
        from .updater import check_for_updates_manual

        # Show checking message
        self.statusbar.SetStatusText("Checking for updates...", 0)
        announce("Checking for updates")

        # Check for updates (shows dialog with results)
        check_for_updates_manual(__version__, self)

        self.statusbar.SetStatusText("Ready", 0)

    def _on_send_feedback(self, event):
        """Show feedback dialog."""
        from .feedback import show_feedback_dialog

        show_feedback_dialog(self)

    def _on_suggest_affiliate_correction_menu(self, event):
        """Show affiliate correction dialog from menu."""
        self._on_suggest_affiliate_correction(None)

    def _on_suggest_affiliate_correction(self, affiliate_data):
        """
        Show the affiliate correction dialog.

        Args:
            affiliate_data: Optional dict with affiliate data, or None to select in dialog
        """
        try:
            from .affiliate_feedback import AffiliateInfo, show_affiliate_correction_dialog

            # Get all affiliates from the panel
            all_affiliates = self.affiliates_panel.get_all_affiliates_as_info()

            # If no affiliates loaded, show error
            if not all_affiliates:
                wx.MessageBox(
                    "Unable to load affiliate data. Please try syncing data first.",
                    "Affiliate Data Not Available",
                    wx.OK | wx.ICON_WARNING,
                    self,
                )
                return

            # Get selected affiliate if provided
            selected_info = None
            if affiliate_data:
                selected_info = AffiliateInfo.from_dict(affiliate_data)
            elif self.notebook.GetSelection() == 3:  # Affiliates tab
                selected_info = self.affiliates_panel.get_selected_affiliate_as_info()

            show_affiliate_correction_dialog(self, all_affiliates, selected_info)

        except ImportError as e:
            wx.MessageBox(
                f"Could not load affiliate correction module: {e}",
                "Error",
                wx.OK | wx.ICON_ERROR,
                self,
            )

    def _on_whats_new(self, event):
        """Show what's new in this version."""
        try:
            from . import __version__
            from .announcement_ui import AnnouncementDetailDialog
            from .announcements import (
                Announcement,
                AnnouncementCategory,
                AnnouncementPriority,
                get_announcement_manager,
            )

            # Check if there's an announcement for this version
            manager = get_announcement_manager()
            for announcement in manager.get_all_announcements(
                include_expired=True, include_read=True
            ):
                if announcement.version == __version__:
                    dialog = AnnouncementDetailDialog(self, announcement, manager)
                    dialog.ShowModal()
                    dialog.Destroy()
                    return

            # No version-specific announcement, show generic changelog
            changelog_path = Path(__file__).parent.parent / "docs" / "CHANGELOG.md"
            if changelog_path.exists():
                with open(changelog_path, "r", encoding="utf-8") as f:
                    changelog_content = f.read()

                # Create a temporary announcement from changelog
                announcement = Announcement(
                    id="changelog",
                    title=f"What's New in ACB Link {__version__}",
                    summary=f"Release notes and changes in version {__version__}",
                    content=changelog_content[:5000],  # Limit content
                    priority=AnnouncementPriority.NORMAL,
                    category=AnnouncementCategory.UPDATE,
                    version=__version__,
                    author="ACB Link Team",
                )
                dialog = AnnouncementDetailDialog(self, announcement, manager)
                dialog.ShowModal()
                dialog.Destroy()
            else:
                wx.MessageBox(
                    f"ACB Link version {__version__}\n\n"
                    "Check the Help menu for documentation and updates.",
                    "What's New",
                    wx.OK | wx.ICON_INFORMATION,
                    self,
                )
        except Exception as e:
            self.logger.error(f"Failed to show what's new: {e}")
            wx.MessageBox(
                "Unable to load version information.", "What's New", wx.OK | wx.ICON_WARNING, self
            )

    def _on_about(self, event):
        """Show about dialog."""
        from . import __author__, __version__

        info = wx.adv.AboutDialogInfo()
        info.SetName("ACB Link")
        info.SetVersion(__version__)
        info.SetDescription(
            "Desktop application for ACB media content.\n\nProvides accessible access to ACB streams, podcasts, and resources."
        )
        info.SetCopyright("© American Council of the Blind")
        info.AddDeveloper(__author__)
        info.SetWebSite("https://www.acb.org")

        wx.adv.AboutBox(info)

    def _on_iconize(self, event):
        """Handle window minimize."""
        if event.IsIconized() and self.settings.system_tray.minimize_to_tray:
            self.Hide()
        event.Skip()

    def _on_close(self, event):
        """Handle window close."""
        if self.settings.system_tray.close_to_tray and self.tray_icon:
            self.Hide()
        else:
            self._cleanup()
            event.Skip()

    def _cleanup(self):
        """Clean up resources before exit."""
        # Stop recording if active
        if self.is_recording:
            self._stop_recording()

        # End listening stats session
        self.listening_stats.end_session()

        # Stop announcement background checking
        if hasattr(self, "announcement_manager") and self.announcement_manager:
            self.announcement_manager.stop_background_checking()

        # Stop all managers
        self.voice_controller.stop()
        self.offline_manager.stop_monitoring()
        self.calendar_manager.stop_refresh_timer()
        self.recording_manager.stop()
        self.native_player.stop()
        self.sleep_timer.cancel()
        self.enhanced_sleep_timer.cancel()
        self.quiet_hours.stop_monitoring()
        self.media_key_handler.unregister()

        # Stop server
        self.web_server.stop()

        # Save settings
        self.settings.save()

        # Save manager data
        self.favorites_manager.save()
        self.playlist_manager.save()
        self.recently_played.save()

        # Destroy tray icon
        if self.tray_icon:
            self.tray_icon.Destroy()

        self.logger.info("ACB Link shutdown")

    def show_from_tray(self):
        """Show window from system tray."""
        self.Show()
        self.Iconize(False)
        self.Raise()

    def exit_app(self):
        """Exit the application."""
        self._cleanup()
        self.Destroy()

    # =========================================================================
    # EDIT MENU HANDLERS
    # =========================================================================

    def _on_copy(self, event):
        """Handle copy command."""
        focus = wx.Window.FindFocus()
        if focus and hasattr(focus, "Copy"):
            focus.Copy()

    def _on_select_all(self, event):
        """Handle select all command."""
        focus = wx.Window.FindFocus()
        if focus and hasattr(focus, "SelectAll"):
            focus.SelectAll()

    def _on_copy_stream_url(self, event):
        """Copy current stream URL to clipboard."""
        if self.current_stream and self.current_stream in STREAMS:
            url = STREAMS[self.current_stream]
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(url))
                wx.TheClipboard.Close()
                if self.settings.accessibility.screen_reader_announcements:
                    announce("Stream URL copied to clipboard")
        else:
            if self.settings.accessibility.screen_reader_announcements:
                announce("No stream currently playing")

    # =========================================================================
    # VIEW MENU HANDLERS - Show/Hide UI Elements
    # =========================================================================

    def _on_toggle_toolbar(self, event):
        """Toggle toolbar visibility."""
        show = self.menu_show_toolbar.IsChecked()
        self.view_settings.set("show_toolbar", show)
        self._apply_view_settings()
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"Toolbar {'shown' if show else 'hidden'}")

    def _on_toggle_tab_bar(self, event):
        """Toggle tab bar visibility."""
        show = self.menu_show_tab_bar.IsChecked()
        self.view_settings.set("show_tab_bar", show)
        self._apply_view_settings()
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"Tab bar {'shown' if show else 'hidden'}")

    def _on_toggle_status_bar(self, event):
        """Toggle status bar visibility."""
        show = self.menu_show_status_bar.IsChecked()
        self.view_settings.set("show_status_bar", show)
        self._apply_view_settings()
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"Status bar {'shown' if show else 'hidden'}")

    def _on_toggle_player_panel(self, event):
        """Toggle player controls visibility."""
        show = self.menu_show_player.IsChecked()
        self.view_settings.set("show_player_panel", show)
        self._apply_view_settings()
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"Player controls {'shown' if show else 'hidden'}")

    def _on_toggle_now_playing(self, event):
        """Toggle now playing banner visibility."""
        show = self.menu_show_now_playing.IsChecked()
        self.view_settings.set("show_now_playing_banner", show)
        self._apply_view_settings()
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"Now playing banner {'shown' if show else 'hidden'}")

    def _on_toggle_sidebar(self, event):
        """Toggle sidebar visibility."""
        show = self.menu_show_sidebar.IsChecked()
        self.view_settings.set("show_sidebar", show)
        self._apply_view_settings()
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"Sidebar {'shown' if show else 'hidden'}")

    def _apply_view_settings(self):
        """Apply current view settings to UI."""
        settings = self.view_settings.settings

        # Status bar
        if hasattr(self, "statusbar"):
            self.statusbar.Show(settings.show_status_bar)

        # Player panel
        if hasattr(self, "player_panel"):
            self.player_panel.Show(settings.show_player_panel)

        # Notebook (tab bar) - in wxPython we can't hide the tab bar directly
        # but we can adjust styling/visibility

        # Trigger layout refresh
        self.Layout()
        self.Refresh()

    # =========================================================================
    # VIEW MENU HANDLERS - Pane Navigation (F6 / Shift+F6)
    # =========================================================================

    def _get_current_tab_primary_control(self) -> Optional[wx.Window]:
        """
        Get the primary focusable control for the currently selected tab.
        This ensures F6 navigation focuses the most useful control in each tab.
        """
        selection = self.notebook.GetSelection()
        if selection == -1:
            return None

        # Map tab indices to their primary controls
        panel_map = {
            0: self.home_panel,
            1: self.streams_panel,
            2: self.podcasts_panel,
            3: self.affiliates_panel,
            4: self.resources_panel,
        }

        panel = panel_map.get(selection)
        if not panel:
            return None

        # Try to find the primary list or tree control in the panel
        for attr in ["streams_list", "podcast_list", "episodes_list", "affiliates_tree",
                     "resources_list", "list_ctrl", "tree_ctrl"]:
            if hasattr(panel, attr):
                ctrl = getattr(panel, attr)
                if ctrl and ctrl.IsShown():
                    return ctrl

        # Fallback to first focusable child
        return self._find_first_focusable_child(panel)

    def _find_first_focusable_child(self, parent: wx.Window) -> Optional[wx.Window]:
        """Find the first focusable child control in a window."""
        for child in parent.GetChildren():
            if child.IsShown() and child.IsEnabled():
                # Prefer interactive controls
                if isinstance(child, (wx.ListCtrl, wx.TreeCtrl, wx.Button, wx.TextCtrl,
                                     wx.Choice, wx.ComboBox, wx.Slider, wx.CheckBox)):
                    return child
                # Recursively search containers
                if isinstance(child, (wx.Panel, wx.ScrolledWindow)):
                    result = self._find_first_focusable_child(child)
                    if result:
                        return result
        return parent

    def _register_panes(self):
        """Register navigable panes for F6 navigation."""
        # Tab bar itself - allow navigating to the tab strip for tab switching
        self.pane_navigator.register_pane(
            PaneType.TOOLBAR,  # Use TOOLBAR type for tab bar
            self.notebook,
            "Tab bar",
            lambda: True,
            focus_target=self.notebook,  # Focus the notebook for tab key navigation
        )

        # Tab content - the content area within the selected tab
        self.pane_navigator.register_pane(
            PaneType.TAB_CONTENT,
            self.notebook,
            "Tab content",
            lambda: True,
            focus_target=None,  # Will use dynamic focus via _focus_tab_content
        )

        # Player controls
        if hasattr(self, "player_panel"):
            self.pane_navigator.register_pane(
                PaneType.PLAYER_CONTROLS,
                self.player_panel,
                "Player controls",
                lambda: self.player_panel.IsShown(),
                focus_target=self.btn_play_pause if hasattr(self, "btn_play_pause") else None,
            )

        # Status bar (if visible)
        if hasattr(self, "statusbar"):
            self.pane_navigator.register_pane(
                PaneType.STATUS_BAR,
                self.statusbar,
                "Status bar",
                lambda: self.statusbar.IsShown(),
                focus_target=None,
            )

        # Set up custom focus handler for dynamic tab content focus
        self.pane_navigator.set_focus_callback(self._custom_pane_focus)

    def _custom_pane_focus(self, pane) -> bool:
        """
        Custom focus handler for pane navigation.
        Returns True if focus was handled, False to use default behavior.
        """
        if pane.pane_type == PaneType.TAB_CONTENT:
            # Focus the primary control in the current tab
            target = self._get_current_tab_primary_control()
            if target:
                target.SetFocus()
                if self.settings.accessibility.screen_reader_announcements:
                    # Announce tab name and focused control
                    tab_name = self.notebook.GetPageText(self.notebook.GetSelection())
                    control_name = target.GetName() or target.GetLabel() or "content"
                    announce(f"{tab_name} tab, {control_name}")
                return True
        elif pane.pane_type == PaneType.TOOLBAR:
            # Focus the notebook itself to allow Ctrl+Tab/Ctrl+Shift+Tab tab switching
            self.notebook.SetFocus()
            if self.settings.accessibility.screen_reader_announcements:
                tab_name = self.notebook.GetPageText(self.notebook.GetSelection())
                announce(f"Tab bar, {tab_name} selected. Use Ctrl+Tab to switch tabs.")
            return True
        return False  # Use default focus behavior

    def _on_next_pane(self, event):
        """Navigate to next pane (F6)."""
        self.pane_navigator.navigate_next()

    def _on_prev_pane(self, event):
        """Navigate to previous pane (Shift+F6)."""
        self.pane_navigator.navigate_previous()

    def _on_next_tab(self, event):
        """Navigate to next tab (Ctrl+Tab)."""
        current = self.notebook.GetSelection()
        count = self.notebook.GetPageCount()
        next_idx = (current + 1) % count
        self.notebook.SetSelection(next_idx)
        # Focus the tab content and announce
        tab_name = self.notebook.GetPageText(next_idx)
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"{tab_name} tab")
        # Focus the primary control in the new tab
        wx.CallAfter(self._focus_current_tab_content)

    def _on_prev_tab(self, event):
        """Navigate to previous tab (Ctrl+Shift+Tab)."""
        current = self.notebook.GetSelection()
        count = self.notebook.GetPageCount()
        prev_idx = (current - 1) % count
        self.notebook.SetSelection(prev_idx)
        # Focus the tab content and announce
        tab_name = self.notebook.GetPageText(prev_idx)
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"{tab_name} tab")
        # Focus the primary control in the new tab
        wx.CallAfter(self._focus_current_tab_content)

    def _focus_current_tab_content(self):
        """Focus the primary control in the current tab."""
        target = self._get_current_tab_primary_control()
        if target:
            target.SetFocus()

    # =========================================================================
    # VIEW MENU HANDLERS - Focus Mode and Full Screen
    # =========================================================================

    def _on_toggle_focus_mode(self, event):
        """Toggle focus mode."""
        is_active = self.focus_mode.toggle()
        self.menu_focus_mode.Check(is_active)

        # Update other menu items to reflect focus mode state
        self._sync_view_menu_checks()

        if self.settings.accessibility.screen_reader_announcements:
            announce(f"Focus mode {'enabled' if is_active else 'disabled'}")

    def _on_focus_mode_enter(self):
        """Called when entering focus mode."""
        self._apply_view_settings()

    def _on_focus_mode_exit(self):
        """Called when exiting focus mode."""
        self._apply_view_settings()

    def _sync_view_menu_checks(self):
        """Synchronize view menu checkboxes with current settings."""
        settings = self.view_settings.settings
        self.menu_show_toolbar.Check(settings.show_toolbar)
        self.menu_show_tab_bar.Check(settings.show_tab_bar)
        self.menu_show_status_bar.Check(settings.show_status_bar)
        self.menu_show_player.Check(settings.show_player_panel)
        self.menu_show_now_playing.Check(settings.show_now_playing_banner)
        self.menu_show_sidebar.Check(settings.show_sidebar)
        self.menu_focus_mode.Check(settings.focus_mode)

    def _on_toggle_full_screen(self, event):
        """Toggle full screen mode."""
        is_full = self.IsFullScreen()
        self.ShowFullScreen(not is_full)
        if self.settings.accessibility.screen_reader_announcements:
            announce(f"Full screen {'disabled' if is_full else 'enabled'}")

    # =========================================================================
    # VIEW MENU HANDLERS - View Settings Dialog
    # =========================================================================

    def _on_view_settings(self, event):
        """Open view settings dialog."""
        dialog = ViewSettingsDialog(self, self.view_settings, self.visual_settings)
        if dialog.ShowModal() == wx.ID_OK:
            self._apply_view_settings()
            self._sync_view_menu_checks()
        dialog.Destroy()

    def _on_podcast_sort(self, sort_key: str):
        """Handle podcast episode sort order change from View menu."""
        from .enhanced_podcasts import EpisodeSortOrder

        sort_map = {
            "date_newest": EpisodeSortOrder.DATE_NEWEST,
            "date_oldest": EpisodeSortOrder.DATE_OLDEST,
            "title_az": EpisodeSortOrder.TITLE_AZ,
            "title_za": EpisodeSortOrder.TITLE_ZA,
            "duration_longest": EpisodeSortOrder.DURATION_LONGEST,
            "duration_shortest": EpisodeSortOrder.DURATION_SHORTEST,
            "unplayed_first": EpisodeSortOrder.UNPLAYED_FIRST,
            "downloaded_first": EpisodeSortOrder.DOWNLOADED_FIRST,
        }

        if sort_key in sort_map:
            # If we have the enhanced podcasts panel, update its sort
            if hasattr(self, "podcasts_panel") and hasattr(self.podcasts_panel, "set_sort_order"):
                self.podcasts_panel.set_sort_order(sort_map[sort_key])
                from .accessibility import announce
                from .enhanced_podcasts import SORT_LABELS

                announce(f"Episodes sorted by {SORT_LABELS[sort_map[sort_key]]}")

    def _on_customize_home(self, event):
        """Open home page customization dialog."""
        from .home_widgets import HomePageCustomizeDialog

        if hasattr(self, "home_settings"):
            dialog = HomePageCustomizeDialog(self, self.home_settings)
            if dialog.ShowModal() == wx.ID_OK:
                # Refresh home panel
                if hasattr(self, "home_panel") and hasattr(self.home_panel, "refresh"):
                    self.home_panel._build_widgets()
                from .accessibility import announce

                announce("Home page updated")
            dialog.Destroy()
        else:
            wx.MessageBox(
                "Home page customization will be available after enabling the enhanced home panel.",
                "Feature Not Available",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )

    def _on_visual_settings_changed(self):
        """Handle visual settings change."""
        wx.CallAfter(self._apply_visual_settings)

    def _apply_visual_settings(self):
        """Apply visual settings to the UI."""
        self.visual_settings.apply_to_window(self)

    # =========================================================================
    # FAVORITES QUICK DIAL HANDLER
    # =========================================================================

    def _play_favorite(self, favorite):
        """Play a favorite item."""
        if hasattr(favorite, "content_type"):
            if favorite.content_type == "stream":
                self._play_stream(favorite.content_name)
            elif favorite.content_type == "podcast":
                # Handle podcast favorites
                pass
