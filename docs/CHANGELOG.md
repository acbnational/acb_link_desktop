# Changelog

All notable changes to ACB Link Desktop will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-19 - Initial Release

ACB Link Desktop 1.0.0 is the first public release, providing a comprehensive accessible audio streaming and podcast application for the American Council of the Blind community.

### Core Features

**Audio Streaming**
- 10 ACB Media streams with one-click playback
- Keyboard shortcuts (Alt+1 through Alt+0) for instant stream access
- Native audio player with VLC and system backend support
- Volume control, mute, and playback speed adjustment (0.5x to 2.0x)
- Background playback with system tray integration
- Stream recording in MP3, WAV, and OGG formats

**Podcast Management**
- 37+ official ACB podcasts organized from OPML catalog
- Episode streaming and offline downloads
- Playback position memory across sessions
- Variable speed playback (0.5x to 2.0x)
- Episode sorting and filtering (8 sort options)

**Voice Control System**
- Customizable wake word (default: "hey link")
- 20+ voice commands for hands-free operation
- Custom trigger phrase mapping for any command
- Text-to-speech feedback with configurable rate and volume
- Wake word timeout with automatic re-activation

**Announcement System**
- Home page announcement widget with priority display
- Read/unread tracking with persistence
- Native OS notifications (Windows toast, macOS Notification Center)
- Critical announcement popup dialogs
- Category filtering (General, Update, Feature, Maintenance, Security, etc.)
- Admin announcement publisher for authorized users
- What's New release notes viewer

**Settings & Personalization (14 tabs)**
- General: Browser preference, default tab, update checking
- Appearance: Themes (light, dark, high contrast), fonts, colors
- Playback: Skip intervals, speed, volume, equalizer
- Storage: Paths, cache, recording format
- Home Tab: Widget visibility and limits
- Startup: Run at login, start minimized, auto-play
- System Tray: Minimize behavior, click actions, notifications
- Notifications: Per-type controls, duration, position
- Announcements: Check interval, native notifications, priority filter
- Keyboard: Global hotkeys, media keys, Vim navigation
- Voice Control: Wake word, TTS settings, command customization
- Privacy: History controls, analytics opt-in
- Performance: Memory mode, concurrent downloads, caching
- Accessibility: Screen reader announcements, audio feedback

**Administration**
- GitHub-based admin authentication (zero server cost)
- Role-based access: USER, AFFILIATE_ADMIN, CONFIG_ADMIN, SUPER_ADMIN
- Organization configuration via GitHub repository
- Affiliate feedback submission system
- Admin panels for content management

**Favorites and Playlists**
- Save favorite streams and podcast episodes
- Create and manage custom playlists
- Repeat and shuffle modes
- Quick access from home screen

**Search**
- Global search across all content types
- Real-time results with keyboard navigation
- Filter by streams, podcasts, affiliates, resources

**Calendar Integration**
- ACB events calendar with reminders
- iCal export for external calendars
- Event notifications

**Data Synchronization**
- Live sync with ACB servers
- Offline fallback with bundled data
- Manual sync from Tools menu

**System Scheduling**
- Windows Task Scheduler integration
- macOS launchd integration
- Schedule recordings when app is closed

**Auto-Updates**
- GitHub Releases integration
- Automatic update checking and downloading
- Update notifications

### Accessibility

**WCAG 2.2 AA Compliance**
- Full screen reader support (NVDA, JAWS, Narrator, VoiceOver)
- Complete keyboard-only navigation
- High contrast themes (4 presets)
- Customizable focus indicators
- Accessible names on all controls
- Status change announcements via live regions

### Platform Support

- Windows 10/11 (x64 and ARM64)
- macOS 11+ (Intel and Apple Silicon)
- Python 3.9+ for development

### Security

- All communications over HTTPS
- GitHub-based admin authentication
- Privacy-respecting analytics (opt-in only)
- No telemetry without consent
- Local-only data storage
- PAT tokens stored in memory only (never on disk)

---

## [Unreleased]

Features planned for future releases:

- Podcast subscription management
- Enhanced search with natural language
- Cross-device sync
- Bluetooth remote control support
- Linux support
- Mobile companion app integration

---

## Version History Notes

### Version Numbering

- **Major** (X.0.0): Significant new features, possible breaking changes
- **Minor** (0.X.0): New features, backwards compatible
- **Patch** (0.0.X): Bug fixes, small improvements

### Release Channels

- **Stable**: Production-ready releases (v1.0.0)
- **Beta**: Pre-release testing (v1.1.0-beta.1)
- **Alpha**: Early development (v1.1.0-alpha.1)

---

*For the latest changes, see the [GitHub Releases](https://github.com/acbnational/acb_link_desktop/releases) page.*
