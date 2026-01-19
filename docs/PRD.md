# ACB Link Desktop Application - Product Requirements Document

## Version 1.0 - January 2026

---

## 1. Executive Summary

### 1.1 Purpose
ACB Link Desktop is a fully accessible Windows desktop application providing comprehensive access to the American Council of the Blind's media network, resources, and community. Designed for blind and visually impaired users, it features complete screen reader compatibility, extensive keyboard navigation, voice control, and customizable accessibility options.

### 1.2 Target Users
- Blind and visually impaired individuals
- Members of the American Council of the Blind
- Users who rely on screen readers (JAWS, NVDA, Narrator)
- Low vision users requiring customizable display options
- Users preferring keyboard or voice-based interfaces

### 1.3 Design Philosophy
- **Native Controls First**: wxPython provides native Windows controls accessible by default
- **Menu-Driven Interface**: Complete application control through keyboard-accessible menus
- **Voice First**: Hands-free operation through natural language commands
- **Comprehensive Settings**: Extensive customization for diverse accessibility needs
- **System Integration**: System tray, notifications, and background operation
- **Platform Flexibility**: Support for both x64 and ARM64 architectures

---

## 2. Application Architecture

### 2.1 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Desktop Framework | wxPython 4.2+ | Native Windows UI controls |
| Web Server | FastAPI + Uvicorn | Local accessible HTML rendering |
| Audio Player | VLC / Windows Media Foundation | Native embedded audio playback |
| Recording | FFmpeg + Threading | Stream and scheduled recording |
| Data Storage | JSON | Settings, favorites, playlists |
| System Tray | wx.adv.TaskBarIcon | Background operation |
| Voice Control | SpeechRecognition + pyttsx3 | Hands-free operation |
| RSS Parsing | feedparser | Podcast feed management |
| Localization | Custom i18n framework | Multi-language support |

### 2.2 Module Structure

```
acb_link/
├── __init__.py             # Package metadata (v1.0.0)
├── main.py                 # Application entry point
├── main_frame.py           # Main window, menus, integration
├── settings.py             # Settings dataclasses
├── data.py                 # Streams, podcasts, constants
├── panels.py               # Core UI panels
├── new_panels.py           # Feature panels (Favorites, Search, etc.)
├── dialogs.py              # Settings dialog with 8 tabs
├── media_player.py         # Legacy playback engine
├── native_player.py        # Native audio (VLC/WMF backends)
├── podcast_manager.py      # RSS parsing, downloads
├── favorites.py            # Favorites & bookmarks
├── playlists.py            # Playlist management
├── scheduled_recording.py  # Recording scheduler
├── search.py               # Global search engine
├── offline.py              # Offline mode & connectivity
├── calendar_integration.py # ACB calendar events
├── event_scheduler.py      # Event scheduling & alerts
├── shortcuts.py            # Configurable keyboard shortcuts
├── enhanced_voice.py       # NLP voice control
├── localization.py         # Multi-language support
├── system_tray.py          # System tray icon
├── server.py               # Local web server
├── utils.py                # Utilities and helpers
├── voice_control.py        # Basic voice commands
├── view_settings.py        # View/layout configuration
├── playback_enhancements.py # Audio ducking, media keys
├── user_experience.py      # First-run wizard, feedback
├── advanced_playback.py    # Copy playing, recently played
├── styles.py               # Color schemes and themes
├── accessibility.py        # Screen reader support
├── updater.py              # Automatic updates
└── config.py               # Configuration management
```

### 2.3 Data Flow

1. User interacts via wxPython controls, keyboard shortcuts, or voice
2. Shortcut manager routes keyboard input to actions
3. Voice commands processed by NLP engine
4. Audio playback handled by native player (VLC/WMF)
5. Settings, favorites, playlists persisted to JSON
6. Background services monitor connectivity, calendar, recordings

---

## 3. Feature Specifications

### 3.1 Tabbed Interface

| Tab | Description | Key Features |
|-----|-------------|--------------|
| Home | Dashboard | Quick access, event alerts |
| Streams | Live audio | 10 stations, shortcuts |
| Podcasts | Podcast browser | RSS, downloads, position memory |
| Affiliates | Organizations | ACB affiliate links |
| Resources | Web resources | ACB websites |
| Favorites | Saved content | Streams, podcasts, bookmarks |
| Playlists | Custom lists | Mixed content, shuffle, repeat |
| Search | Global search | All content types, voice |
| Calendar | ACB events | Reminders, recording, join |

### 3.2 Audio Playback

#### Native Player
- **VLC Backend**: Primary, cross-platform compatible
- **Windows Media Foundation**: Fallback, native Windows
- **Gapless Playback**: Seamless playlist transitions
- **Audio Normalization**: Consistent volume levels
- **Sleep Timer**: 15/30/45/60/90/120 minute presets

#### Playback Controls
- Play/Pause/Stop
- Skip forward/backward (configurable intervals)
- Volume adjustment (0-100%)
- Mute toggle
- Playback speed (0.5x - 2.0x)
- Equalizer presets

### 3.3 Podcast Management

#### RSS Integration
- Full feed parsing with feedparser
- Episode metadata extraction
- Automatic feed updates
- Episode download with progress

#### Episode Features
- Position memory and resume
- Auto-mark as played
- Offline playback support
- Bookmark with notes

### 3.4 Favorites & Bookmarks

- Favorite streams, podcasts, episodes
- Bookmarks with timestamps and notes
- Quick access from Home tab
- Export/import functionality

### 3.5 Playlist Management

- Create custom playlists
- Mix streams and episodes
- Shuffle mode
- Repeat modes (None, All, One)
- Import/export playlists

### 3.6 Recording

#### Live Recording
- Stream capture to MP3/WAV/OGG
- Configurable bitrate (64-320 kbps)
- Automatic metadata tagging

#### Scheduled Recording
- Time-based scheduling
- Calendar event integration
- Recording presets
- Queue management

### 3.7 Search

- Global search across all content
- Voice search support
- Content type filtering
- Relevance-based ranking
- Search history

### 3.8 Calendar Integration

- ACB calendar event display
- Multiple views (Today, Week, Month)
- Event reminders (5/15/30/60 min)
- One-click event join
- Automatic recording scheduling
- iCal export

### 3.9 Voice Control

#### Activation
- Wake word: "Hey ACB Link"
- Continuous listening mode
- Manual push-to-talk option

#### Natural Language Processing
- Intent recognition
- Parameter extraction
- Confidence scoring
- Custom command mapping

#### Built-in Commands
- Playback control
- Navigation
- Stream selection (by number)
- Search
- Recording control
- Status queries

### 3.10 Keyboard Shortcuts

#### Configuration
- All actions have assignable shortcuts
- Visual shortcut editor
- Conflict detection
- Import/export configurations
- Reset to defaults

#### Default Stream Shortcuts
- Alt+1 through Alt+0 for streams 1-10

#### Quick Dial Favorites
- Alt+F1 through Alt+F5 for top 5 favorites

#### View Navigation
- F6 / Shift+F6 for pane navigation
- Ctrl+Shift+D for Focus Mode toggle

---

## 4. Menu Structure

### 4.1 File Menu
| Item | Shortcut | Description |
|------|----------|-------------|
| Open in Browser | Ctrl+B | Open content in browser |
| Settings... | Ctrl+, | Open settings dialog |
| Exit | Alt+F4 | Close application |

### 4.2 Playback Menu
| Item | Shortcut | Description |
|------|----------|-------------|
| Play/Pause | Space | Toggle playback |
| Stop | Ctrl+Shift+S | Stop playback |
| Skip Back | Ctrl+Left | Skip backward |
| Skip Forward | Ctrl+Right | Skip forward |
| Volume Up | Ctrl+Up | Increase volume |
| Volume Down | Ctrl+Down | Decrease volume |
| Mute | Ctrl+M | Toggle mute |
| Record | Ctrl+R | Start/stop recording |

### 4.3 Streams Menu
Direct access to all 10 ACB Media streams with configurable shortcuts (Alt+1-0)

### 4.4 Podcasts Menu
Hierarchical submenu by category

### 4.5 View Menu
| Item | Shortcut | Description |
|------|----------|-------------|
| Home | Ctrl+1 | Home tab |
| Streams | Ctrl+2 | Streams tab |
| Podcasts | Ctrl+3 | Podcasts tab |
| Affiliates | Ctrl+4 | Affiliates tab |
| Resources | Ctrl+5 | Resources tab |
| Favorites | Ctrl+6 | Favorites tab |
| Playlists | Ctrl+7 | Playlists tab |
| Search | Ctrl+8 | Search tab |
| Calendar | Ctrl+9 | Calendar tab |
| --- | | |
| Toolbar | | Toggle toolbar visibility |
| Tab Bar | | Toggle tab bar visibility |
| Status Bar | | Toggle status bar visibility |
| Player Controls | Ctrl+Shift+P | Toggle player controls |
| Sidebar | Ctrl+\\ | Toggle sidebar |
| --- | | |
| Focus Mode | Ctrl+Shift+D | Minimal distraction-free interface |
| Full Screen | F11 | Toggle full screen mode |
| View Settings... | | Open view configuration dialog |
| --- | | |
| Next Pane | F6 | Move focus to next pane |
| Previous Pane | Shift+F6 | Move focus to previous pane |

### 4.6 Tools Menu
| Item | Description |
|------|-------------|
| Start/Stop Web Server | Toggle local web server |
| Audio Ducking | Toggle audio ducking on/off |
| Audio Ducking Settings... | Configure ducking percentage (10-90%) and delay |
| Media Key Support | Toggle hardware media key support |
| Auto-Play on Startup... | Configure automatic playback |
| Quiet Hours... | Configure scheduled volume reduction |
| Scheduled Tasks... | Manage scheduled recordings |
| Listening Statistics | View listening history and stats |
| Export/Import Settings | Backup and restore all settings |
| Sync Data | Manually synchronize with ACB servers |
| Clear Cache | Remove cached data |
| Clear Recent Items | Clear playback history |

### 4.7 Help Menu
| Item | Shortcut | Description |
|------|----------|-------------|
| User Guide | F1 | Open documentation |
| Keyboard Shortcuts | | Show shortcuts dialog |
| ACB Website | | Open acb.org |
| Check for Updates | | Check for new version |
| About ACB Link | | Version and credits |

---

## 5. Settings Dialog

### 5.1 Eight Settings Tabs

#### General Tab
- Preferred browser (Edge/Chrome)
- Default startup tab
- Check for updates on startup

#### Appearance Tab
- Color theme with 9 schemes:
  - Light, Dark
  - High Contrast Light, High Contrast Dark
  - Yellow on Black, White on Black
  - Green on Black, Black on White, Blue on White
- Font size (8-32pt)
- Font family selection
- High contrast mode
- Reduce motion option
- Large cursor option
- Focus ring width

#### Playback Tab
- Skip intervals (5-120 seconds)
- Default playback speed
- Default volume level
- Remember playback position
- Auto-play next episode
- Equalizer settings

#### Storage Tab
- Download folder location
- Recording folder location
- Recording format (MP3/WAV/OGG)
- Recording bitrate (64-320 kbps)
- Maximum cache size
- Auto-delete options

#### Home Tab Customization
- Show/hide sections
- Maximum items per section
- Event alerts configuration

#### System Tray Tab
- Enable system tray icon
- Minimize to tray
- Close to tray
- Start minimized
- Notification settings

#### Accessibility Tab
- Screen reader announcements
- Audio feedback for actions
- Keyboard-only mode
- Focus follows mouse
- Confirmation dialogs

#### Keyboard Shortcuts Tab
- View all shortcuts
- Edit any shortcut
- Conflict detection
- Reset to defaults
- Import/Export

---

## 6. Stream Data

| # | Station ID | Name | Content | Shortcut |
|---|-----------|------|---------|----------|
| 1 | a11911 | ACB Media 1 | Flagship | Alt+1 |
| 2 | a27778 | ACB Media 2 | Flagship | Alt+2 |
| 3 | a17972 | ACB Media 3 | Old Time Radio | Alt+3 |
| 4 | a89697 | ACB Media 4 | Advocacy | Alt+4 |
| 5 | a46090 | ACB Media 5 | Audio Description | Alt+5 |
| 6 | a36240 | ACB Media 6 | International | Alt+6 |
| 7 | a95398 | ACB Media 7 | ACB Café | Alt+7 |
| 8 | a18975 | ACB Media 8 | Classical | Alt+8 |
| 9 | a44175 | ACB Media 9 | Jazz | Alt+9 |
| 10 | a85327 | ACB Media 10 | Country | Alt+0 |

---

## 7. Accessibility Compliance

### 7.1 WCAG 2.2 AA Requirements

| Criterion | Status | Implementation |
|-----------|--------|----------------|
| 1.4.3 Contrast | ✅ | 4.5:1 minimum ratio |
| 1.4.4 Text Resize | ✅ | Scalable to 200% |
| 2.1.1 Keyboard | ✅ | Full keyboard access |
| 2.1.2 No Traps | ✅ | Escape always works |
| 2.4.3 Focus Order | ✅ | Logical tab sequence |
| 2.4.7 Focus Visible | ✅ | Customizable focus ring |
| 4.1.2 Name/Role | ✅ | All controls labeled |

### 7.2 Screen Reader Testing

| Screen Reader | Compatibility | Notes |
|---------------|---------------|-------|
| JAWS 2024+ | Full | Tested extensively |
| NVDA 2024+ | Full | Tested extensively |
| Narrator | Full | Windows built-in |

### 7.3 Keyboard Navigation

- Tab/Shift+Tab for focus navigation
- Arrow keys for list/tree navigation
- Enter for activation
- Escape for cancel/close
- Menu mnemonics (Alt+letter)
- Configurable accelerator keys

---

## 8. File Locations

| Purpose | Location |
|---------|----------|
| Settings | ~/.acb_link/settings.json |
| Favorites | ~/.acb_link/favorites.json |
| Playlists | ~/.acb_link/playlists.json |
| Shortcuts | ~/.acb_link/shortcuts.json |
| Scheduled Events | ~/.acb_link/scheduled_events.json |
| Voice Config | ~/.acb_link/voice_config.json |
| View Settings | ~/.acb_link/view_settings.json |
| Audio Ducking | ~/.acb_link/audio_ducking.json |
| Cache | ~/.acb_link/cache/ |
| Downloads | ~/.acb_link/downloads/ |
| Recordings | ~/.acb_link/recordings/ |
| Logs | ~/.acb_link/logs/ |

---

## 9. Technical Requirements

### 9.1 System Requirements

| Requirement | Specification |
|-------------|---------------|
| Operating System | Windows 10/11 (x64 or ARM64) |
| Python | 3.9 or later |
| RAM | 256 MB minimum |
| Disk Space | 100 MB + downloads/recordings |
| Internet | Required for streaming |
| Audio | Sound card with speakers/headphones |

### 9.2 Dependencies

```
# Core
wxPython>=4.2.0
fastapi>=0.100.0
uvicorn>=0.23.0

# Audio
python-vlc>=3.0.0

# Podcasts
feedparser>=6.0.0
requests>=2.28.0

# Voice
SpeechRecognition>=3.10.0
pyttsx3>=2.90

# Utilities
python-dateutil>=2.8.0
```

### 9.3 ARM64 Compatibility

All components are ARM64 compatible:
- Pure Python codebase
- wxPython ARM64 wheels available
- VLC ARM64 builds available
- No x86-specific dependencies

---

## 10. Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| App Launch | < 3 sec | ✅ Met |
| Stream Start | < 2 sec | ✅ Met |
| Memory Usage | < 200 MB | ✅ Met |
| Crash Rate | < 0.1% | ✅ Met |

---

## 11. Security Considerations

- Local-only settings storage
- No cloud data transmission without consent
- HTTPS enforcement for web content
- No credential storage (uses browser for auth)

---

## 12. Administration & Configuration Sync

### 12.1 Overview

ACB Link includes a secure administration system for managing organization-wide configuration. **This system uses GitHub for free, zero-cost authentication** - no custom server infrastructure required.

### 12.2 Configuration Tiers

| Tier | Scope | Storage | Editable By |
|------|-------|---------|-------------|
| User Preferences | Individual | Local JSON | Any user |
| Organization Config | Organization-wide | GitHub repo | Admins only |
| Affiliate Data | Content | XML files | Affiliate Admins |

### 12.3 Admin Roles (GitHub-Based)

Roles are determined by GitHub repository permissions:

| GitHub Permission | Role | Level | Capabilities |
|-------------------|------|-------|--------------|
| None/Read | USER | 0 | Standard app usage, personal settings |
| Write/Triage | AFFILIATE_ADMIN | 1 | Review/approve affiliate corrections |
| Maintain/Admin | CONFIG_ADMIN | 2 | Modify organization config, data sources |
| Organization Owner | SUPER_ADMIN | 3 | All capabilities, admin management |

### 12.4 Security Model

#### GitHub-Based Authentication
- Uses GitHub Personal Access Tokens (PAT)
- Token validates via GitHub API (`GET /user`)
- Role determined by repository permissions
- MFA inherited from user's GitHub account settings
- No custom server = no server vulnerabilities

#### Token Security
- PAT stored in memory only (never on disk)
- Minimal scope required: `read:org`
- Session cleared on app exit
- Instant revocation by removing GitHub collaborator

#### Audit Trail
- All config changes tracked in Git commit history
- GitHub logs all API access and permission changes
- Complete history with timestamps and authors
- Native GitHub diff viewing for config changes

### 12.5 Configuration Sync Process

```
Authentication Flow:
1. User attempts admin action
2. App prompts for GitHub PAT
3. App validates token via GitHub API
4. App checks user's repo permissions
5. App checks org ownership (for SUPER_ADMIN)
6. Role assigned based on highest permission
7. Token stored in memory for session
8. Subsequent admin ops use same token

Config Fetch Flow:
1. App starts or admin requests sync
2. Fetch config from GitHub repo via API
3. Parse JSON config file
4. Cache locally for offline use
5. Apply to application settings

Config Update Flow (Admin):
1. Admin makes changes in Advanced Settings
2. App verifies admin has CONFIG_ADMIN role
3. Fetch current config SHA from GitHub
4. Push updated config with commit message
5. Git history provides audit trail
6. Other users get update on next restart
```

### 12.6 Protected Settings (Admin-Only)

| Category | Settings |
|----------|----------|
| Data Sources | Stream URLs, podcast feeds, affiliate data URLs |
| Network | Timeouts, retries, proxy configuration |
| Updates | GitHub repo, API URL, update server |
| Paths | Application data directories |
| Defaults | Organization-wide default values |

### 12.7 User Settings (Free to Modify)

| Category | Settings |
|----------|----------|
| Appearance | Theme, font size, colors, contrast |
| Playback | Volume, speed, skip intervals |
| Behavior | System tray, minimize behavior |
| Accessibility | Screen reader options, audio feedback |
| Storage | Personal download/recording paths |

### 12.8 Affiliate Correction Workflow

```
1. User submits correction via Feedback dialog
2. Correction queued for review (JSON)
3. Affiliate Admin authenticates with GitHub PAT
4. Admin reviews in Admin Review Panel
5. Admin approves/rejects with notes
6. Approved corrections applied to XML files
7. Automatic backup created before changes
8. Git-style audit log updated
9. Rollback available if issues detected
```

### 12.9 Failsafe Design

- **Offline Operation**: App works without GitHub connectivity
- **Cache Fallback**: Uses last valid cached config if GitHub unavailable
- **Bundled Defaults**: Hardcoded safe defaults if no cache exists
- **Human Approval**: All affiliate changes require explicit admin approval
- **Automatic Backups**: XML files backed up before any modification
- **Rollback**: Can restore from backups if issues detected

---

## 13. Future Roadmap

Items not yet implemented:

### Cloud & Sync
- [ ] ACB member login
- [ ] Cross-device sync
- [ ] Cloud playlist storage
- [ ] Listening statistics

### AI Features
- [ ] Podcast transcription
- [ ] Searchable transcripts
- [ ] Content summarization
- [ ] Personalized recommendations

### Platform Expansion
- [ ] macOS support
- [ ] Linux support
- [ ] iOS companion app
- [ ] Android companion app

### Language Support
- [ ] French translation
- [ ] German translation
- [ ] Right-to-left language support

---

## 14. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2025 | Initial release with full feature set including podcasts, favorites, playlists, search, calendar, voice, shortcuts, localization, and ARM support |

---

*Document Version: 1.0*  
*Last Updated: January 2026*  
*Copyright © 2026 American Council of the Blind*
