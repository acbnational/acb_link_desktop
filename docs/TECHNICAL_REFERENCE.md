# ACB Link Desktop - Technical Reference

**Version:** 1.0.0
**Last Updated:** January 2025
**Audience:** Developers, Contributors, System Administrators

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Reference](#module-reference)
3. [Core Classes](#core-classes)
4. [Data Structures](#data-structures)
5. [Configuration System](#configuration-system)
6. [Audio Playback](#audio-playback)
7. [Voice Control](#voice-control)
8. [Keyboard Shortcuts](#keyboard-shortcuts)
9. [Event System](#event-system)
10. [Localization](#localization)
11. [Platform Support](#platform-support)
12. [Build & Deployment](#build--deployment)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ACB Link Desktop 1.0                         │
├─────────────────────────────────────────────────────────────────────┤
│                              UI Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  MainFrame   │  │    Panels    │  │       Dialogs            │   │
│  │  (wxPython)  │  │  (9 tabs)    │  │   (Settings, Shortcuts)  │   │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬──────────────┘   │
│         │                 │                       │                  │
│  ┌──────┴─────────────────┴───────────────────────┴──────────────┐  │
│  │                      Manager Layer                             │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │  │
│  │  │  Podcast   │  │  Favorites │  │  Playlist  │  │ Search   │ │  │
│  │  │  Manager   │  │  Manager   │  │  Manager   │  │ Engine   │ │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │  │
│  │  │  Calendar  │  │  Recording │  │  Shortcut  │  │ Offline  │ │  │
│  │  │  Manager   │  │  Manager   │  │  Manager   │  │ Manager  │ │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      Service Layer                             │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │  │
│  │  │   Native   │  │   Voice    │  │   Event    │  │  Local   │ │  │
│  │  │   Player   │  │  Control   │  │ Scheduler  │  │  Server  │ │  │
│  │  │ (VLC/WMF)  │  │   (NLP)    │  │            │  │ (FastAPI)│ │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     Platform Layer                             │  │
│  │  • Windows x64/ARM64  • System Tray  • Accessibility APIs     │  │
│  │  • File System        • Audio APIs    • Speech Recognition    │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Accessibility First**: All UI elements screen reader compatible
2. **Modular Design**: Single responsibility per module
3. **Extensibility**: Plugin-ready architecture
4. **Offline Capable**: Graceful degradation without internet
5. **Platform Flexible**: x64 and ARM64 support
6. **Configurable**: Everything can be customized

---

## Module Reference

### Directory Structure

```
acb_link/
├── __init__.py             # Package metadata, exports (v1.0.0)
├── main.py                 # Application entry point
├── main_frame.py           # Main window, menus, manager integration
├── settings.py             # Settings dataclasses, themes
├── data.py                 # Static data (streams, podcasts)
│
├── panels.py               # Core UI panels (Home, Streams, Podcasts)
├── new_panels.py           # Feature panels (Favorites, Search, Calendar, Shortcuts)
├── dialogs.py              # Settings dialog (14 tabs)
│
├── native_player.py        # Audio playback (VLC/WMF backends)
├── media_player.py         # Legacy playback engine
├── podcast_manager.py      # RSS parsing, episode downloads
├── playback_enhancements.py # Audio ducking, media keys
├── advanced_playback.py    # Copy playing, recently played
│
├── favorites.py            # Favorites & bookmarks management
├── playlists.py            # Playlist creation & playback
├── scheduled_recording.py  # Recording scheduler
├── search.py               # Global search engine
├── offline.py              # Connectivity & offline mode
├── calendar_integration.py # ACB calendar events
├── event_scheduler.py      # Event scheduling & alerts
│
├── shortcuts.py            # Configurable keyboard shortcuts
├── enhanced_voice.py       # NLP voice control
├── voice_control.py        # Basic voice commands
├── localization.py         # Multi-language support
│
├── view_settings.py        # View/layout configuration
├── user_experience.py      # First-run wizard, feedback
├── styles.py               # Color schemes and themes
├── accessibility.py        # Screen reader support
├── updater.py              # Automatic updates
├── config.py               # Configuration management
├── data_sync.py            # Data synchronization
├── feedback.py             # User feedback submission
├── scheduler.py            # System task scheduling
│
├── system_tray.py          # System tray icon & menu
├── server.py               # Local FastAPI web server
└── utils.py                # Logging, caching, helpers
```

### Module Descriptions

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `main.py` | Application entry point | `App` |
| `main_frame.py` | Main window | `MainFrame` |
| `settings.py` | Configuration | `AppSettings`, `ThemeSettings` |
| `view_settings.py` | View & layout | `ViewSettings`, `ViewSettingsDialog` |
| `data.py` | Static data | `STREAMS`, `PODCASTS` |
| `panels.py` | Core UI panels | `HomePanel`, `StreamsPanel`, `PodcastsPanel` |
| `new_panels.py` | Feature panels | `FavoritesPanel`, `SearchPanel`, `ShortcutsPanel` |
| `native_player.py` | Audio playback | `NativeAudioPlayer`, `SleepTimer` |
| `playback_enhancements.py` | Playback features | `AudioDuckingManager`, `AudioDuckingSettings`, `AudioDuckingDialog` |
| `advanced_playback.py` | Advanced features | `CopyPlayingManager`, `RecentlyPlayedManager` |
| `podcast_manager.py` | Podcast handling | `PodcastManager`, `PodcastEpisode` |
| `favorites.py` | Favorites | `FavoritesManager`, `Favorite`, `Bookmark` |
| `playlists.py` | Playlists | `PlaylistManager`, `PlaylistPlayer` |
| `scheduled_recording.py` | Recording | `ScheduledRecordingManager` |
| `search.py` | Search | `GlobalSearch`, `SearchResult` |
| `offline.py` | Offline mode | `OfflineManager`, `ConnectivityMonitor`, `DownloadQueue` |
| `calendar_integration.py` | Calendar | `CalendarManager`, `CalendarEvent` |
| `event_scheduler.py` | Event alerts | `EventScheduler`, `ScheduledEvent` |
| `shortcuts.py` | Shortcuts | `ShortcutManager`, `Shortcut` |
| `enhanced_voice.py` | Voice NLP | `EnhancedVoiceController`, `NaturalLanguageProcessor` |
| `localization.py` | i18n | `TranslationManager`, `Language` |
| `user_experience.py` | UX features | `FirstRunWizard`, `ResumePlaybackDialog` |
| `styles.py` | Themes | `ColorScheme`, `ThemeManager` |
| `accessibility.py` | Screen readers | `announce`, `make_accessible` |
| `updater.py` | Updates | `UpdateChecker`, `UpdateDialog` |
| `feedback.py` | User feedback | `FeedbackDialog`, `FeedbackType` |
| `affiliate_feedback.py` | Affiliate corrections | `AffiliateCorrectionDialog`, `AffiliateInfo` |
| `affiliate_admin.py` | Correction admin | `CorrectionManager`, `AdminReviewPanel` |
| `github_admin.py` | GitHub-based admin auth | `GitHubAdminManager`, `AdminRole`, `AdminSession` |
| `admin_config.py` | Legacy admin config | `AdminConfigManager`, `OrganizationConfig` |
| `admin_auth_ui.py` | Admin authentication UI | `AdminLoginDialog`, `require_admin_login` |
| `advanced_settings.py` | Admin settings dialog | `AdvancedSettingsDialog` (admin-only) |
| `data_sync.py` | Data sync | `DataSyncManager` |
| `scheduler.py` | System tasks | `SystemScheduler` |

---

## Core Classes

### MainFrame

The main application window.

```python
class MainFrame(wx.Frame):
    """Main application window for ACB Link."""

    def __init__(self):
        # Initialize managers
        self.podcast_manager = PodcastManager()
        self.native_player = NativeAudioPlayer()
        self.favorites_manager = FavoritesManager()
        self.playlist_manager = PlaylistManager()
        self.search_engine = GlobalSearch()
        self.calendar_manager = CalendarManager()
        self.shortcut_manager = ShortcutManager()
        self.voice_controller = EnhancedVoiceController()

    def _build_menubar(self): ...
    def _build_ui(self): ...
    def _setup_accelerators(self): ...
```

### AppSettings

Application configuration.

```python
@dataclass
class AppSettings:
    theme: ThemeSettings
    playback: PlaybackSettings
    storage: StorageSettings
    home_tab: HomeTabSettings
    system_tray: SystemTraySettings
    accessibility: AccessibilitySettings

    @classmethod
    def load(cls) -> 'AppSettings': ...
    def save(self): ...
```

### NativeAudioPlayer

Audio playback with VLC/WMF backends.

```python
class NativeAudioPlayer:
    def __init__(
        self,
        on_playback_started: Callable = None,
        on_playback_stopped: Callable = None,
        on_error: Callable = None
    ):
        self.backend = self._detect_backend()  # VLC or WMF

    def play(self, url: str): ...
    def pause(self): ...
    def stop(self): ...
    def set_volume(self, level: int): ...
    def seek(self, position: float): ...
```

### ShortcutManager

Configurable keyboard shortcuts.

```python
class ShortcutManager:
    def __init__(self):
        self.shortcuts: Dict[str, Shortcut] = {}
        self._load_config()

    def get_shortcut(self, shortcut_id: str) -> Optional[Shortcut]: ...
    def set_shortcut(self, shortcut_id: str, key: str) -> bool: ...
    def get_shortcut_by_key(self, key: str) -> Optional[Shortcut]: ...
    def reset_all(self): ...
    def export_shortcuts(self, path: str) -> bool: ...
    def import_shortcuts(self, path: str) -> bool: ...
```

---

## Data Structures

### Streams

```python
STREAMS = {
    "ACB Media 1": "a11911",
    "ACB Media 2": "a27778",
    "ACB Media 3": "a17972",
    "ACB Media 4": "a89697",
    "ACB Media 5": "a46090",
    "ACB Media 6": "a36240",
    "ACB Media 7": "a95398",
    "ACB Media 8": "a18975",
    "ACB Media 9": "a44175",
    "ACB Media 10": "a85327",
}
```

### Shortcut

```python
@dataclass
class Shortcut:
    id: str
    name: str
    description: str
    category: ShortcutCategory
    default_key: str
    current_key: Optional[str] = None
    is_global: bool = False
    enabled: bool = True
```

### Favorite

```python
@dataclass
class Favorite:
    id: str
    name: str
    favorite_type: FavoriteType  # STREAM, PODCAST, EPISODE
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    added_at: datetime = field(default_factory=datetime.now)
```

### ScheduledEvent

```python
@dataclass
class ScheduledEvent:
    id: str
    calendar_event_id: str
    title: str
    start_time: datetime
    end_time: Optional[datetime]
    stream_url: Optional[str]
    alert_enabled: bool = True
    alert_minutes_before: int = 15
    alert_type: AlertType = AlertType.NOTIFICATION
    action: EventAction = EventAction.ALERT_ONLY
    record_enabled: bool = False
```

---

## Configuration System

### File Locations

| File | Purpose |
|------|---------|
| `~/.acb_link/settings.json` | Main settings |
| `~/.acb_link/shortcuts.json` | Keyboard shortcuts |
| `~/.acb_link/favorites.json` | Favorites & bookmarks |
| `~/.acb_link/playlists.json` | User playlists |
| `~/.acb_link/scheduled_events.json` | Calendar events |
| `~/.acb_link/voice_config.json` | Voice control settings |
| `~/.acb_link/view_settings.json` | View/layout settings |
| `~/.acb_link/audio_ducking.json` | Audio ducking settings |
| `~/.acb_link/cache/` | Downloaded content cache |
| `~/.acb_link/downloads/` | Podcast episodes |
| `~/.acb_link/recordings/` | Stream recordings |

### Settings Schema

```json
{
  "theme": {
    "name": "dark",
    "font_size": 14,
    "font_family": "Segoe UI",
    "high_contrast": false
  },
  "playback": {
    "default_speed": 1.0,
    "skip_forward_seconds": 30,
    "skip_backward_seconds": 10,
    "default_volume": 100
  },
  "accessibility": {
    "screen_reader_announcements": true,
    "audio_feedback": true,
    "keyboard_only_mode": false
  }
}
```

### Audio Ducking Settings Schema

```json
{
  "enabled": true,
  "duck_percentage": 30,
  "restore_delay_seconds": 2.0
}
```

---

## Audio Playback

### Backend Selection

```python
class NativeAudioPlayer:
    def _detect_backend(self) -> str:
        # Try VLC first
        try:
            import vlc
            return "vlc"
        except ImportError:
            pass

        # Fall back to Windows Media Foundation
        return "wmf"
```

### Playback States

```python
class PlayerState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"
    ERROR = "error"
```

### Sleep Timer

```python
class SleepTimer:
    def set_timer(self, minutes: int): ...
    def cancel(self): ...
    def get_remaining(self) -> int: ...  # seconds
```

### Audio Ducking

```python
@dataclass
class AudioDuckingSettings:
    enabled: bool = True
    duck_percentage: int = 30  # 10-90%
    restore_delay_seconds: float = 2.0  # 0.5-10.0 seconds

class AudioDuckingManager:
    def __init__(self, player):
        self.player = player
        self.settings = self._load_settings()

    @property
    def duck_percentage(self) -> int: ...

    @duck_percentage.setter
    def duck_percentage(self, value: int): ...  # Clamps to 10-90

    @property
    def restore_delay(self) -> float: ...

    @restore_delay.setter
    def restore_delay(self, value: float): ...  # Clamps to 0.5-10.0

    def start_ducking(self): ...
    def stop_ducking(self): ...
    def _on_system_sound(self): ...
```

### View Settings

```python
@dataclass
class ViewSettings:
    show_toolbar: bool = True
    show_tab_bar: bool = True
    show_status_bar: bool = True
    show_player_controls: bool = True
    show_now_playing: bool = True
    show_sidebar: bool = False
    focus_mode: bool = False

class ViewSettingsDialog(wx.Dialog):
    """Dialog for configuring view/layout settings."""
    def __init__(self, parent, view_settings: ViewSettings): ...
```

---

## Voice Control

### Dependencies

Voice control has two operational modes:

**Core Dependencies (Always Included):**
- `SpeechRecognition` - Google Speech Recognition API
- `pyttsx3` - Text-to-speech engine
- Activated via keyboard shortcut (`Ctrl+Shift+V`)

**Optional Wake Word Dependencies (~5GB download):**
```bash
pip install openwakeword torch torchaudio
```

The application automatically detects available components:
```python
try:
    import openwakeword
    HAS_OPENWAKEWORD = True
except ImportError:
    HAS_OPENWAKEWORD = False
```

### Configuration

Voice control settings are stored in `VoiceSettings` dataclass:

```python
@dataclass
class VoiceSettings:
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
    command_confirmation: bool = True
    custom_triggers: dict = None  # Command name -> list of triggers
    # Key feedback sounds
    key_sounds_enabled: bool = True  # Play sounds on key press/release
    key_down_sound: str = ""  # Custom key down sound path (empty = default)
    key_up_sound: str = ""  # Custom key up sound path (empty = default)
```

### Key Feedback Sounds

The `KeySoundPlayer` class provides audio feedback during voice recognition:

```python
class KeySoundPlayer:
    """Plays audio cues when voice recognition starts/stops."""

    def play_key_down(self):
        """Play sound when voice recognition activates."""

    def play_key_up(self):
        """Play sound when voice recognition deactivates."""

    def apply_settings(self, voice_settings):
        """Apply settings from VoiceSettings dataclass."""
```

Default sounds are located in the `sounds/` directory:
- `key_down.mp3` - Played when voice recognition starts
- `key_up.mp3` - Played when voice recognition stops

Users can specify custom sound files (MP3, WAV, OGG) in Settings > Voice Control.

### Wake Word Activation (Optional)

> **Note:** Requires `openwakeword` package. Without it, `wake_word_enabled` is ignored and voice control uses keyboard activation only.

```python
class VoiceController:
    DEFAULT_WAKE_WORD = "hey link"

    def set_wake_word(self, wake_word: str, enabled: bool = True):
        """Set custom wake word."""
        self.wake_word = wake_word.lower().strip()
        self.wake_word_enabled = enabled

    def _handle_recognized_text(self, text: str):
        """Handle recognized speech, checking wake word first."""
        if self.wake_word_enabled and not self.wake_word_active:
            if self.wake_word.lower() in text:
                self.wake_word_active = True
                self._reset_wake_word_timer()
                self.speak_async("Listening")
```

### Custom Command Triggers

Users can customize trigger phrases for any command:

```python
# Default triggers for built-in commands
DEFAULT_TRIGGERS = {
    "play": ["play", "start", "resume", "continue"],
    "pause": ["pause", "wait", "hold"],
    "stop": ["stop", "end", "halt"],
    "volume_up": ["volume up", "louder", "increase volume"],
    "volume_down": ["volume down", "quieter", "decrease volume"],
    # ... more commands
}

# Apply custom triggers from settings
def apply_settings(self, voice_settings):
    if voice_settings.custom_triggers:
        for cmd_name, triggers in voice_settings.custom_triggers.items():
            if cmd_name in self.commands and triggers:
                self.commands[cmd_name].triggers = list(triggers)
```

### Supported Intents

| Intent | Default Triggers | Action |
|--------|------------------|--------|
| `play` | "play", "start", "resume", "continue" | Start/resume playback |
| `pause` | "pause", "wait", "hold" | Pause playback |
| `stop` | "stop", "end", "halt" | Stop playback |
| `volume_up` | "volume up", "louder", "turn it up" | Increase volume |
| `volume_down` | "volume down", "quieter", "softer" | Decrease volume |
| `mute` | "mute", "silence", "quiet" | Mute audio |
| `unmute` | "unmute", "sound on" | Restore audio |
| `go_home` | "go home", "home tab", "show home" | Navigate to Home |
| `go_streams` | "go to streams", "streams tab" | Navigate to Streams |
| `go_podcasts` | "go to podcasts", "podcasts tab" | Navigate to Podcasts |
| `start_recording` | "start recording", "record" | Begin recording |
| `stop_recording` | "stop recording", "end recording" | Stop recording |
| `open_settings` | "settings", "preferences", "options" | Open settings |
| `what_playing` | "what's playing", "now playing" | Announce current |
| `help` | "help", "list commands" | List commands |
| `stop_listening` | "stop listening", "voice off" | Deactivate voice |

### Text-to-Speech

```python
def set_tts_rate(self, rate: int):
    """Set speaking rate (100-300 words per minute)."""
    if self.tts_engine:
        self.tts_engine.setProperty('rate', rate)

def set_tts_volume(self, volume: float):
    """Set TTS volume (0.0 to 1.0)."""
    if self.tts_engine:
        self.tts_engine.setProperty('volume', max(0.0, min(1.0, volume)))

def set_tts_voice(self, voice_name: str) -> bool:
    """Set TTS voice by name."""
    voices = self.tts_engine.getProperty('voices')
    for voice in voices:
        if voice_name.lower() in voice.name.lower():
            self.tts_engine.setProperty('voice', voice.id)
            return True
    return False
```

---

## Keyboard Shortcuts

### Default Shortcuts

```python
DEFAULT_SHORTCUTS = {
    "play_pause": Shortcut(id="play_pause", default_key="Space", ...),
    "stop": Shortcut(id="stop", default_key="Ctrl+Shift+S", ...),
    "stream_1": Shortcut(id="stream_1", default_key="Alt+1", ...),
    "stream_2": Shortcut(id="stream_2", default_key="Alt+2", ...),
    # ... streams 3-10
    "tab_home": Shortcut(id="tab_home", default_key="Ctrl+1", ...),
    "tab_streams": Shortcut(id="tab_streams", default_key="Ctrl+2", ...),
    # ... more shortcuts
}
```

### Shortcut Categories

```python
class ShortcutCategory(Enum):
    PLAYBACK = "playback"
    NAVIGATION = "navigation"
    STREAMS = "streams"
    GENERAL = "general"
    RECORDING = "recording"
    VOLUME = "volume"
```

### Conflict Detection

```python
def set_shortcut(self, shortcut_id: str, new_key: str) -> bool:
    # Check for conflicts
    existing = self.get_shortcut_by_key(new_key)
    if existing and existing.id != shortcut_id:
        return False  # Conflict detected

    self.shortcuts[shortcut_id].current_key = new_key
    self._save_config()
    return True
```

---

## Event System

### Calendar Event Flow

```
Calendar Manager                Event Scheduler
      │                               │
      │  get_upcoming_events()        │
      │─────────────────────────────►│
      │                               │
      │         schedule_event()      │
      │◄─────────────────────────────│
      │                               │
      │                    ┌──────────┴──────────┐
      │                    │ Background Checker  │
      │                    │  (30 sec interval)  │
      │                    └──────────┬──────────┘
      │                               │
      │                    Alert Time │
      │                    ───────────┼──►  on_alert callback
      │                               │
      │                    Start Time │
      │                    ───────────┼──►  on_auto_tune / on_auto_record
```

### Event Callbacks

```python
event_scheduler = EventScheduler(
    on_alert=lambda event: show_notification(event),
    on_auto_tune=lambda name, url: player.play(url),
    on_auto_record=lambda event: recorder.start(event)
)
```

---

## Localization

### Translation Keys

```python
class TranslationKey(Enum):
    APP_NAME = "app_name"
    MENU_FILE = "menu_file"
    MENU_PLAYBACK = "menu_playback"
    # ...
```

### Adding Languages

```python
TRANSLATIONS = {
    Language.ENGLISH: {
        TranslationKey.APP_NAME: "ACB Link",
        TranslationKey.MENU_FILE: "File",
        # ...
    },
    Language.SPANISH: {
        TranslationKey.APP_NAME: "ACB Link",
        TranslationKey.MENU_FILE: "Archivo",
        # ...
    },
}
```

### Usage

```python
from acb_link.localization import _

label = _(TranslationKey.MENU_FILE)  # Returns translated string
```

---

## Platform Support

### Windows x64

- Primary development platform
- Full feature support
- Tested on Windows 10/11

### Windows ARM64

- Full compatibility
- Pure Python codebase
- Dependencies available:
  - wxPython ARM64 wheels
  - VLC ARM64 builds
  - All pip packages ARM compatible

### Requirements

| Component | x64 | ARM64 |
|-----------|-----|-------|
| Python | 3.9+ | 3.9+ |
| wxPython | 4.2+ | 4.2+ |
| VLC | 3.0+ | 3.0+ |
| Memory | 256MB | 256MB |

---

## Build & Deployment

### Development Setup

```bash
# Clone repository
git clone https://github.com/acbnational/acb_link_desktop.git
cd acb_link_desktop

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python -m acb_link
```

### Building Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller --onedir --windowed --name "ACB Link" acb_link/main.py
```

### Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=acb_link tests/
```

---

## API Reference

### Local Web Server

The local FastAPI server provides accessible HTML content.

**Base URL:** `http://localhost:8765`

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page |
| `/streams` | GET | Streams list |
| `/podcasts` | GET | Podcasts browser |
| `/health` | GET | Server health check |

---

## Administration & Security

### GitHub-Based Admin Authentication (`github_admin.py`)

ACB Link uses GitHub for admin authentication - completely free, no custom server required.

#### Why GitHub?

- **$0 cost** - No server hosting or maintenance
- **Battle-tested security** - GitHub's auth trusted by millions
- **Instant provisioning** - Add admin = add GitHub collaborator
- **Built-in MFA** - Inherits user's GitHub 2FA settings
- **Audit trail** - GitHub logs all permission changes

#### Role Mapping from GitHub Permissions

```python
class AdminRole(Enum):
    USER = 0              # No repo access or read-only
    AFFILIATE_ADMIN = 1   # Write/Triage permission on config repo
    CONFIG_ADMIN = 2      # Maintain/Admin permission on config repo
    SUPER_ADMIN = 3       # Organization owner
```

#### Admin Session

```python
@dataclass
class AdminSession:
    username: str           # GitHub username
    display_name: str       # GitHub display name
    role: AdminRole         # Determined from repo permissions
    permissions: List[AdminPermission]
    github_token: str       # PAT (memory only, never saved)
    authenticated_at: datetime

    def has_role(self, required_role: AdminRole) -> bool: ...
    def has_permission(self, perm: AdminPermission) -> bool: ...
```

#### GitHub Admin Manager

```python
class GitHubAdminManager:
    """Central manager for GitHub-based admin authentication."""

    def authenticate(self, github_token: str) -> Tuple[bool, str, Optional[AdminSession]]:
        """
        Authenticate with GitHub PAT.

        1. Validate token via GET /user
        2. Check repo permissions via GitHub API
        3. Check org ownership if applicable
        4. Create session with appropriate role
        """
        ...

    def require_role(self, required_role: AdminRole) -> Tuple[bool, str]:
        """Check if current session has required role."""
        ...

    def fetch_org_config(self) -> Tuple[bool, str, Optional[Dict]]:
        """Fetch org config from GitHub repository."""
        ...

    def update_org_config(self, config: Dict, commit_message: str) -> Tuple[bool, str]:
        """Push config changes to GitHub (requires CONFIG_ADMIN)."""
        ...
```

#### Configuration Storage

Organization config is stored in a GitHub repository:

```
acbnational/acb_link_config/
├── org_config.json      # Organization configuration
├── README.md            # Documentation for admins
└── .github/
    └── CODEOWNERS       # Optional: require reviews
```

### Legacy Admin Configuration (`admin_config.py`)

For organizations preferring self-hosted servers, the legacy system remains available.

#### Admin Token (Legacy)

```python
@dataclass
class AdminToken:
    token_id: str
    username: str
    role: AdminRole
    permissions: List[AdminPermission]
    issued_at: datetime
    expires_at: datetime

    def is_valid(self) -> bool: ...
    def has_permission(self, perm: AdminPermission) -> bool: ...
    def has_role(self, required_role: AdminRole) -> bool: ...
```

#### Organization Configuration

Server-synced configuration that applies to all installations:

```python
@dataclass
class OrganizationConfig:
    # Data source URLs
    base_url: str = "https://acb.org/acblink"
    streams_url: str = "{base_url}/streams.xml"
    podcasts_url: str = "{base_url}/podcasts.xml"
    affiliates_url: str = "{base_url}/states.xml"

    # Network settings
    timeout_seconds: int = 30
    retry_count: int = 3

    # Update settings
    update_server: str = "https://github.com/acb-org/acb-link/releases"

    # Organization defaults
    default_theme: str = "system"
    default_volume: int = 100
```

### Affiliate Correction Admin (`affiliate_admin.py`)

Secure workflow for reviewing and applying affiliate data corrections.

#### Correction Queue

```python
@dataclass
class AffiliateCorrection:
    id: str
    affiliate_name: str
    affiliate_type: str
    state_code: str
    corrections: Dict[str, str]  # field -> new_value
    original_values: Dict[str, str]
    status: str  # pending, approved, rejected, applied
    submitted_at: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    applied_at: Optional[str] = None
```

#### Correction Manager

```python
class CorrectionManager:
    def submit_correction(self, correction: AffiliateCorrection) -> str:
        """Queue a correction for review."""
        ...

    def approve_correction(self, correction_id: str,
                          admin_name: str) -> Tuple[bool, str]:
        """Approve a pending correction (requires AFFILIATE_ADMIN)."""
        ...

    def apply_correction(self, correction_id: str,
                        admin_name: str) -> Tuple[bool, str]:
        """Apply approved correction to XML (with backup)."""
        ...
```

#### XML Updater

```python
class XMLUpdater:
    """Safely update affiliate XML files."""

    def update_affiliate(self, xml_file: str,
                        changes: Dict[str, str]) -> Tuple[bool, str]:
        """
        Update affiliate data with automatic backup.

        1. Create backup of original file
        2. Parse and validate XML
        3. Apply changes
        4. Validate result
        5. Write atomically
        """
        ...

    def rollback(self, backup_file: str) -> Tuple[bool, str]:
        """Restore from backup if issues detected."""
        ...
```

### Admin Authentication UI (`admin_auth_ui.py`)

WCAG 2.2 AA compliant admin login dialogs using GitHub PAT.

```python
def require_admin_login(
    parent: wx.Window,
    required_role: AdminRole,
    context: str = "Admin Access"
) -> Tuple[bool, Optional[AdminSession]]:
    """
    Show GitHub PAT login dialog if needed.

    Args:
        parent: Parent window for dialog
        required_role: Minimum role required (mapped from GitHub permissions)
        context: Description of what requires admin access

    Returns:
        (success, session) - session is None if cancelled/failed
    """
    ...
```

### Security Best Practices

1. **GitHub PAT Scopes**: Only `read:org` scope required (minimal permissions)
2. **Memory-Only Storage**: Tokens never written to disk
3. **MFA Inherited**: User's GitHub 2FA protects their PAT
4. **Audit via Git**: All config changes tracked in commit history
5. **Automatic Backups**: XML files backed up before any modification
6. **Failsafe Operation**: App works with cached config if GitHub unavailable
7. **Instant Revocation**: Remove collaborator = immediate access loss

---

## Error Handling

### Playback Errors

```python
def _on_playback_error(self, error: str):
    self.logger.error(f"Playback error: {error}")
    self.state = PlayerState.ERROR
    if self.on_error:
        self.on_error(error)
```

### Connectivity Errors

```python
class ConnectivityMonitor:
    def _check_connectivity(self):
        try:
            requests.get("https://acb.org", timeout=5)
            self._set_online(True)
        except:
            self._set_online(False)
```

---

## Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Document public methods
- Write unit tests

### Pull Request Process

1. Fork the repository
2. Create feature branch
3. Write tests
4. Submit PR with description

---

*Technical Reference Version 1.0*
*Last Updated: January 2025*
*© American Council of the Blind*
