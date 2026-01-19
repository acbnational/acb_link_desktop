"""
ACB Link - Settings and Configuration
Handles all user settings, themes, and accessibility options.
"""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class ThemeSettings:
    """Visual theme settings for low vision accessibility."""
    name: str = "system"  # system, light, dark, high_contrast_light, high_contrast_dark
    font_size: int = 12
    font_family: str = "Segoe UI"
    bg_color: str = "#FFFFFF"
    fg_color: str = "#000000"
    accent_color: str = "#0078D4"
    button_bg: str = "#E1E1E1"
    button_fg: str = "#000000"
    list_bg: str = "#FFFFFF"
    list_fg: str = "#000000"
    list_selected_bg: str = "#0078D4"
    list_selected_fg: str = "#FFFFFF"
    focus_ring_color: str = "#0078D4"
    focus_ring_width: int = 2
    high_contrast: bool = False
    reduce_motion: bool = False
    large_cursor: bool = False


# Preset themes
THEMES: Dict[str, ThemeSettings] = {
    "light": ThemeSettings(
        name="light",
        bg_color="#FFFFFF",
        fg_color="#1A1A1A",
        accent_color="#0078D4",
        button_bg="#E1E1E1",
        button_fg="#1A1A1A",
        list_bg="#FFFFFF",
        list_fg="#1A1A1A",
    ),
    "dark": ThemeSettings(
        name="dark",
        bg_color="#1E1E1E",
        fg_color="#E0E0E0",
        accent_color="#4CC2FF",
        button_bg="#3C3C3C",
        button_fg="#E0E0E0",
        list_bg="#252525",
        list_fg="#E0E0E0",
        list_selected_bg="#4CC2FF",
    ),
    "high_contrast_light": ThemeSettings(
        name="high_contrast_light",
        bg_color="#FFFFFF",
        fg_color="#000000",
        accent_color="#0000FF",
        button_bg="#FFFFFF",
        button_fg="#000000",
        list_bg="#FFFFFF",
        list_fg="#000000",
        list_selected_bg="#000080",
        list_selected_fg="#FFFFFF",
        focus_ring_color="#FF0000",
        focus_ring_width=3,
        high_contrast=True,
    ),
    "high_contrast_dark": ThemeSettings(
        name="high_contrast_dark",
        bg_color="#000000",
        fg_color="#FFFFFF",
        accent_color="#00FFFF",
        button_bg="#000000",
        button_fg="#FFFFFF",
        list_bg="#000000",
        list_fg="#FFFFFF",
        list_selected_bg="#FFFF00",
        list_selected_fg="#000000",
        focus_ring_color="#00FF00",
        focus_ring_width=3,
        high_contrast=True,
    ),
}


@dataclass
class PlaybackSettings:
    """Audio playback settings."""
    default_speed: float = 1.0
    skip_forward_seconds: int = 30
    skip_backward_seconds: int = 10
    default_volume: int = 100
    remember_position: bool = True
    auto_play_next: bool = False
    normalize_audio: bool = False
    # Equalizer presets
    eq_preset: str = "flat"  # flat, bass_boost, voice, treble
    eq_bass: int = 0  # -10 to +10
    eq_mid: int = 0
    eq_treble: int = 0


@dataclass
class StorageSettings:
    """File storage settings."""
    podcast_download_path: str = ""
    recording_path: str = ""
    max_cache_size_mb: int = 500
    auto_delete_played: bool = False
    recording_format: str = "mp3"  # mp3, wav, ogg
    recording_bitrate: int = 128  # kbps
    
    def __post_init__(self):
        if not self.podcast_download_path:
            self.podcast_download_path = str(Path.home() / "Documents" / "ACB Link" / "Podcasts")
        if not self.recording_path:
            self.recording_path = str(Path.home() / "Documents" / "ACB Link" / "Recordings")


@dataclass
class HomeTabSettings:
    """Home tab customization settings."""
    show_streams: bool = True
    show_podcasts: bool = True
    show_affiliates: bool = True
    show_recent: bool = True
    max_podcasts: int = 5
    max_recent: int = 10


@dataclass 
class SystemTraySettings:
    """System tray behavior settings."""
    enabled: bool = True
    minimize_to_tray: bool = True
    close_to_tray: bool = False
    start_minimized: bool = False
    start_minimized_to_tray: bool = False  # Force start hidden to tray
    show_notifications: bool = True
    notification_duration: int = 5  # seconds
    show_now_playing_notifications: bool = True
    double_click_action: str = "show_hide"  # show_hide, play_pause
    single_click_action: str = "none"  # none, show_hide, play_pause, show_menu


@dataclass
class StartupSettings:
    """Application startup behavior settings."""
    run_at_login: bool = False
    start_minimized: bool = False
    start_minimized_to_tray: bool = False
    restore_last_session: bool = True
    auto_play_last_stream: bool = False
    auto_play_delay_seconds: int = 3
    show_welcome_on_first_run: bool = True
    check_updates_on_startup: bool = True
    sync_data_on_startup: bool = True


@dataclass
class PlaybackBehaviorSettings:
    """Advanced playback behavior settings."""
    remember_volume: bool = True
    remember_speed: bool = True
    remember_position: bool = True
    resume_threshold_seconds: int = 30  # Min position to offer resume
    mark_played_threshold_percent: int = 90  # % to mark episode as played
    auto_advance_playlist: bool = True
    loop_playlist: bool = False
    shuffle_playlist: bool = False
    crossfade_seconds: int = 0  # 0 = disabled
    buffer_size_seconds: int = 30


@dataclass
class NotificationSettings:
    """Notification behavior settings."""
    enabled: bool = True
    sound_enabled: bool = True
    show_now_playing: bool = True
    show_stream_changes: bool = True
    show_recording_status: bool = True
    show_download_complete: bool = True
    show_event_reminders: bool = True
    show_update_available: bool = True
    duration_seconds: int = 5
    position: str = "bottom_right"  # bottom_right, bottom_left, top_right, top_left


@dataclass
class KeyboardSettings:
    """Keyboard shortcut and navigation settings."""
    enable_global_hotkeys: bool = False
    enable_media_keys: bool = True
    vim_style_navigation: bool = False
    escape_minimizes: bool = False
    space_toggles_playback: bool = True
    custom_shortcuts: dict = None
    
    def __post_init__(self):
        if self.custom_shortcuts is None:
            self.custom_shortcuts = {}


@dataclass
class PrivacySettings:
    """Privacy and data collection settings."""
    remember_search_history: bool = True
    remember_listening_history: bool = True
    max_history_items: int = 100
    clear_history_on_exit: bool = False
    analytics_enabled: bool = False
    crash_reporting: bool = False
    send_anonymous_usage: bool = False


@dataclass
class PerformanceSettings:
    """Performance and resource usage settings."""
    low_memory_mode: bool = False
    max_concurrent_downloads: int = 3
    cache_podcast_artwork: bool = True
    preload_next_episode: bool = True
    hardware_acceleration: bool = True
    reduce_cpu_when_minimized: bool = True
    max_log_size_mb: int = 10
    auto_cleanup_old_logs: bool = True


@dataclass
class AccessibilitySettings:
    """Accessibility-specific settings."""
    screen_reader_announcements: bool = True
    audio_feedback: bool = True
    keyboard_only_mode: bool = False
    focus_follows_mouse: bool = False
    auto_read_status: bool = True
    confirmation_dialogs: bool = True


@dataclass
class AnalyticsSettings:
    """Privacy-respecting analytics settings (all opt-in)."""
    analytics_enabled: bool = False
    consent_level: str = "none"  # none, basic, standard, full
    crash_reporting: bool = False
    usage_statistics: bool = False
    feature_tracking: bool = False
    performance_monitoring: bool = False
    include_system_info: bool = False


@dataclass
class VoiceSettings:
    """Voice control configuration settings."""
    enabled: bool = False
    wake_word: str = "hey link"
    wake_word_enabled: bool = True
    continuous_listening: bool = False
    voice_feedback: bool = True
    tts_enabled: bool = True
    tts_rate: int = 175  # Words per minute (100-300)
    tts_volume: float = 0.9  # 0.0-1.0
    tts_voice: str = ""  # Empty = system default
    recognition_timeout: float = 5.0  # Seconds
    ambient_noise_adjustment: bool = True
    command_confirmation: bool = True  # Speak confirmation after commands
    custom_triggers: dict = None  # Command name -> list of custom triggers
    
    def __post_init__(self):
        if self.custom_triggers is None:
            self.custom_triggers = {}


@dataclass
class AppSettings:
    """Main application settings container."""
    # General
    preferred_browser: str = "edge"
    default_tab: str = "home"
    check_updates: bool = True
    language: str = "en"
    
    # Sub-settings
    theme: ThemeSettings = None
    playback: PlaybackSettings = None
    storage: StorageSettings = None
    home_tab: HomeTabSettings = None
    system_tray: SystemTraySettings = None
    startup: StartupSettings = None
    playback_behavior: PlaybackBehaviorSettings = None
    notifications: NotificationSettings = None
    keyboard: KeyboardSettings = None
    privacy: PrivacySettings = None
    performance: PerformanceSettings = None
    accessibility: AccessibilitySettings = None
    analytics: AnalyticsSettings = None
    voice: VoiceSettings = None
    
    def __post_init__(self):
        if self.theme is None:
            self.theme = ThemeSettings()
        if self.playback is None:
            self.playback = PlaybackSettings()
        if self.storage is None:
            self.storage = StorageSettings()
        if self.home_tab is None:
            self.home_tab = HomeTabSettings()
        if self.system_tray is None:
            self.system_tray = SystemTraySettings()
        if self.startup is None:
            self.startup = StartupSettings()
        if self.playback_behavior is None:
            self.playback_behavior = PlaybackBehaviorSettings()
        if self.notifications is None:
            self.notifications = NotificationSettings()
        if self.keyboard is None:
            self.keyboard = KeyboardSettings()
        if self.privacy is None:
            self.privacy = PrivacySettings()
        if self.performance is None:
            self.performance = PerformanceSettings()
        if self.accessibility is None:
            self.accessibility = AccessibilitySettings()
        if self.analytics is None:
            self.analytics = AnalyticsSettings()
        if self.voice is None:
            self.voice = VoiceSettings()
    
    @staticmethod
    def get_settings_path() -> str:
        """Get the settings file path."""
        return str(Path.home() / ".acb_link_settings.json")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "preferred_browser": self.preferred_browser,
            "default_tab": self.default_tab,
            "check_updates": self.check_updates,
            "language": self.language,
            "theme": asdict(self.theme),
            "playback": asdict(self.playback),
            "storage": asdict(self.storage),
            "home_tab": asdict(self.home_tab),
            "system_tray": asdict(self.system_tray),
            "startup": asdict(self.startup),
            "playback_behavior": asdict(self.playback_behavior),
            "notifications": asdict(self.notifications),
            "keyboard": asdict(self.keyboard),
            "privacy": asdict(self.privacy),
            "performance": asdict(self.performance),
            "accessibility": asdict(self.accessibility),
            "analytics": asdict(self.analytics),
            "voice": asdict(self.voice),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppSettings":
        """Create settings from dictionary."""
        settings = cls(
            preferred_browser=data.get("preferred_browser", "edge"),
            default_tab=data.get("default_tab", "home"),
            check_updates=data.get("check_updates", True),
            language=data.get("language", "en"),
        )
        
        if "theme" in data:
            settings.theme = ThemeSettings(**data["theme"])
        if "playback" in data:
            settings.playback = PlaybackSettings(**data["playback"])
        if "storage" in data:
            settings.storage = StorageSettings(**data["storage"])
        if "home_tab" in data:
            settings.home_tab = HomeTabSettings(**data["home_tab"])
        if "system_tray" in data:
            settings.system_tray = SystemTraySettings(**data["system_tray"])
        if "startup" in data:
            settings.startup = StartupSettings(**data["startup"])
        if "playback_behavior" in data:
            settings.playback_behavior = PlaybackBehaviorSettings(**data["playback_behavior"])
        if "notifications" in data:
            settings.notifications = NotificationSettings(**data["notifications"])
        if "keyboard" in data:
            # Handle custom_shortcuts which may have issues with dataclass
            kb_data = data["keyboard"].copy()
            if "custom_shortcuts" not in kb_data:
                kb_data["custom_shortcuts"] = {}
            settings.keyboard = KeyboardSettings(**kb_data)
        if "privacy" in data:
            settings.privacy = PrivacySettings(**data["privacy"])
        if "performance" in data:
            settings.performance = PerformanceSettings(**data["performance"])
        if "accessibility" in data:
            settings.accessibility = AccessibilitySettings(**data["accessibility"])
        if "analytics" in data:
            settings.analytics = AnalyticsSettings(**data["analytics"])
        if "voice" in data:
            # Handle custom_triggers which may have issues with dataclass
            voice_data = data["voice"].copy()
            if "custom_triggers" not in voice_data:
                voice_data["custom_triggers"] = {}
            settings.voice = VoiceSettings(**voice_data)
        
        return settings
    
    def save(self, filepath: Optional[str] = None):
        """Save settings to JSON file."""
        if filepath is None:
            filepath = self.get_settings_path()
        
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: Optional[str] = None) -> "AppSettings":
        """Load settings from JSON file."""
        if filepath is None:
            filepath = cls.get_settings_path()
        
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls.from_dict(data)
            except Exception:
                pass
        
        return cls()
    
    def apply_theme(self, theme_name: str):
        """Apply a preset theme."""
        if theme_name in THEMES:
            self.theme = THEMES[theme_name]
        elif theme_name == "system":
            # Detect system theme (simplified - always light for now)
            self.theme = THEMES["light"]
            self.theme.name = "system"
    
    def ensure_directories(self):
        """Ensure storage directories exist."""
        Path(self.storage.podcast_download_path).mkdir(parents=True, exist_ok=True)
        Path(self.storage.recording_path).mkdir(parents=True, exist_ok=True)
