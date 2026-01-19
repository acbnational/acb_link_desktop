# ACB Link Desktop - Complete Feature List

**Version 1.0.0 - Initial Release**
**Last Updated:** January 2026
**WCAG 2.2 AA Compliant | Windows and macOS | Screen Reader Optimized**

This document provides a comprehensive list of all features available in ACB Link Desktop.

---

## Table of Contents

1. [Audio Streaming](#audio-streaming)
2. [Podcast Management](#podcast-management)
3. [Favorites and Bookmarks](#favorites-and-bookmarks)
4. [Recording](#recording)
5. [Search](#search)
6. [Calendar Integration](#calendar-integration)
7. [Voice Control](#voice-control)
8. [Announcements and Updates](#announcements-and-updates) *(v1.2.0+)*
9. [Automatic Updates](#automatic-updates)
10. [User Feedback](#user-feedback)
11. [Data Synchronization](#data-synchronization)
12. [Quick Actions](#quick-actions)
13. [Listening Statistics](#listening-statistics)
14. [Playback Enhancements](#playback-enhancements)
15. [View Settings and Layout](#view-settings-and-layout)
16. [Settings Backup](#settings-backup)
17. [System Scheduling](#system-scheduling)
18. [Accessibility](#accessibility)
19. [Platform Support](#platform-support)
20. [System Tray](#system-tray)
21. [Settings](#settings)
22. [Administration](#administration-v110) *(v1.1.0+)*
23. [Technical Features](#technical-features)

---

## Audio Streaming

ACB Link Desktop provides access to all ACB Media streaming stations.

### Live Streams

ACB Link includes 10 live audio streams:

| Stream | Content | Keyboard Shortcut |
|--------|---------|-------------------|
| ACB Media 1 | Flagship programming | Alt+1 |
| ACB Media 2 | Flagship programming | Alt+2 |
| ACB Media 3 | Old Time Radio (Treasure Trove) | Alt+3 |
| ACB Media 4 | Advocacy and news | Alt+4 |
| ACB Media 5 | Audio Description content | Alt+5 |
| ACB Media 6 | International programming | Alt+6 |
| ACB Media 7 | ACB Café | Alt+7 |
| ACB Media 8 | Classical music | Alt+8 |
| ACB Media 9 | Jazz music | Alt+9 |
| ACB Media 10 | Country music | Alt+0 |

### Playback Features

- **One-click playback**: Select any stream and press Enter to start listening
- **Keyboard shortcuts**: Use Alt+1 through Alt+0 for instant stream access
- **Stream status indicators**: See which streams are currently live
- **Background playback**: Continue listening while using other applications
- **Volume control**: Adjust volume with Ctrl+Up and Ctrl+Down
- **Mute toggle**: Press Ctrl+M to mute or unmute

### Native Audio Player

- **Dual backend support**: VLC and native Windows Media Foundation or macOS AVFoundation
- **Gapless playback**: Seamless transitions in playlists
- **Audio normalization**: Consistent volume levels across content
- **Equalizer presets**: Flat, bass boost, voice enhancement, treble boost
- **Sleep timer**: Auto-stop after 15, 30, 45, 60, 90, or 120 minutes

---

## Podcast Management

Access 37 official ACB podcasts directly from the application with a rich browsing experience.

### Browse and Discover

- **OPML-based catalog**: All ACB podcasts loaded from standard OPML format
- **Podcast browser**: Split-pane interface with podcast list and episode details
- **Search and filter**: Quickly find podcasts by name
- **Episode metadata**: Title, description, duration, publish date, and download status
- **RSS feed parsing**: Automatic feed updates with caching
- **Real-time loading**: Episodes load dynamically when selecting a podcast

### Episode Management

| Sort Option | Description |
|-------------|-------------|
| Newest First | Most recent episodes at top (default) |
| Oldest First | Chronological order |
| Title A-Z | Alphabetical by title |
| Title Z-A | Reverse alphabetical |
| Longest First | By duration, longest first |
| Shortest First | By duration, shortest first |
| Unplayed First | New episodes prioritized |
| Downloaded First | Offline content prioritized |

**Access:** View menu, Sort Podcast Episodes

### Download and Offline Listening

- **Stream episodes**: Play directly without downloading
- **Download episodes**: Save for offline listening
- **Download management**: Delete downloads to save space
- **Download progress**: Visual progress tracking
- **Smart download queue**: Priority-based downloading
- **Offline playback**: Listen without an internet connection

### Playback Features

- **Position memory**: Resume where you left off
- **Mark as played/unplayed**: Manual episode status control
- **Auto-mark as played**: Track listening history
- **Playback speed**: 0.5x to 2.0x speed adjustment
- **Skip intervals**: Configurable 5 to 120 second skips

### Context Menu Options

Right-click on episodes for quick actions:
- Stream Episode
- Download Episode / Delete Download
- Mark as Played / Mark as Unplayed
- Add Episode to Favorites
- Copy Episode URL
- Episode Details

---

## Favorites and Bookmarks

Save and organize your favorite content for quick access.

### Favorites

- **Favorite streams**: Quick access to preferred stations
- **Favorite podcasts**: Mark your top shows
- **Favorite episodes**: Save must-listen content
- **One-click add**: Instantly add to favorites
- **Quick access**: Favorites panel and Home tab widget

### Bookmarks

- **Episode bookmarks**: Mark specific timestamps
- **Bookmark notes**: Add personal annotations
- **Jump to bookmark**: Instant position recall
- **Export and import**: Share your bookmarks

---

## Recording

Capture live streams for later listening.

### Live Recording

- **Stream recording**: Capture any live broadcast
- **Multiple formats**: MP3, WAV, OGG
- **Quality options**: 64 to 320 kbps
- **Custom save location**: Choose your folder

### Scheduled Recording

- **System-level scheduling**: Records even when application is closed
- **Windows Task Scheduler integration**: Native Windows support
- **macOS launchd integration**: Native macOS support
- **Recording presets**: Quick setup templates
- **Automatic metadata**: ID3 tag embedding

---

## Search

Find content quickly with powerful search capabilities.

### Global Search

- **Search everything**: Streams, podcasts, episodes, favorites
- **Voice search**: Speak your query
- **Filter by type**: Narrow results
- **Relevance ranking**: Best matches first

### Search Features

- **Search history**: Quick re-search
- **Suggestions**: Auto-complete queries
- **Result preview**: See details before playing

---

## Calendar Integration

Stay connected with ACB events.

### ACB Calendar

- **Event display**: See upcoming ACB events
- **Multiple views**: Today, week, month, all upcoming
- **Live event indicators**: Know what is happening now
- **Event details**: Full descriptions and information

### Scheduling and Alerts

- **Home page alerts**: Upcoming event widget
- **Event reminders**: 5, 15, 30, or 60 minute alerts
- **Alert types**: Notification, sound, voice
- **One-click join**: Jump right into events
- **Event recording**: Schedule recordings automatically
- **iCal export**: Add to external calendars

---

## Voice Control

Hands-free operation with fully configurable voice commands.

### Activation Methods

**Keyboard Shortcut (Default):**
Press `Ctrl+Shift+V` to toggle voice control on/off. This method works out of the box with no additional setup.

**Wake Word Activation (Optional - Requires Additional Download):**

> **Note:** Wake word detection requires AI/ML components (~5GB) not included in the standard installer. To enable "Hey ACB Link" style activation:
> ```bash
> pip install openwakeword torch torchaudio
> ```
> Restart ACB Link after installation. The app automatically detects and enables wake word support.

When installed, wake word features include:
- **Customizable wake word**: Change from default "hey link" to any phrase you prefer
- **Examples**: "hey link", "ok link", "computer", "hey radio"
- **Optional wake word**: Disable wake word for continuous command listening
- **Timeout after activation**: Returns to wake word listening after 10 seconds of silence

### Voice Commands

| Command | Action |
|---------|--------|
| "Play" | Start playback |
| "Pause" | Pause playback |
| "Stop" | Stop playback |
| "Volume up" | Increase volume |
| "Volume down" | Decrease volume |
| "Mute" | Mute audio |
| "Unmute" | Restore audio |
| "Skip forward" | Skip ahead |
| "Skip back" | Skip backward |
| "Play stream 1" through "Play stream 10" | Play specific stream |
| "Go to streams" | Navigate to Streams tab |
| "Go to podcasts" | Navigate to Podcasts tab |
| "Go to home" | Navigate to Home tab |
| "Start recording" | Begin recording |
| "Stop recording" | End recording |
| "Settings" | Open settings dialog |
| "What's playing?" | Announce current content |
| "Help" | List available commands |
| "Stop listening" | Deactivate voice control |

### Custom Triggers

You can customize the trigger phrases for any voice command:

1. Go to **Settings** → **Voice Control**
2. Click **Customize Voice Commands...**
3. Select a command from the list
4. Edit the trigger phrases (one per line)
5. Click **Save Triggers**

This allows you to:

- Add phrases in your native language
- Use shorter or longer phrases
- Add regional variations
- Remove triggers you accidentally speak

### Text-to-Speech Settings

Configure how ACB Link speaks to you:

| Setting | Description |
|---------|-------------|
| Speaking rate | 100-300 words per minute |
| TTS volume | 0-100% independent of playback |
| Voice feedback | Spoken confirmations after commands |
| Command confirmation | Announce when commands execute |

---

## Announcements and Updates

Stay informed with ACB Link's comprehensive announcement system. Never miss important updates, new features, or critical alerts.

### Home Widget

The announcement widget appears prominently on the home page when you have unread announcements:

- **Always visible first**: Unread announcements are shown before other content
- **Priority indicators**: Critical and high-priority announcements are highlighted
- **Quick access**: Click any announcement to view full details
- **Mark all as read**: Clear all announcements with one click
- **View history**: Access all past announcements

### Announcement Types

| Priority | Description | Notification |
|----------|-------------|--------------|
| Critical | Emergency alerts, security issues, infrastructure problems | Popup dialog + native notification |
| High | Important updates, breaking changes | Native notification |
| Normal | Standard announcements, feature updates | Widget only (default) |
| Low | Minor updates, tips | Widget only |
| Info | General information | Widget only |

### Categories

- 📢 **General**: Organization-wide announcements
- 🔄 **Update**: Application version updates with release notes
- ✨ **New Feature**: Newly added functionality
- 🔧 **Maintenance**: Scheduled maintenance windows
- 🏗️ **Infrastructure**: Server or service changes
- 🔒 **Security**: Security advisories
- 📚 **New Content**: New podcasts, streams, or resources
- 📅 **Event**: Upcoming ACB events
- 💡 **Tip**: Tips and tricks for using ACB Link
- 👥 **Community**: Community news and updates

### Native Notifications

ACB Link uses your operating system's native notification system:

**Windows:**
- Toast notifications in Action Center
- Critical alerts break through Focus Assist
- Sound notifications (configurable)

**macOS:**
- Notification Center integration
- Alert sounds for high-priority items
- Respect Do Not Disturb settings

### What's New

Access release notes directly from the Help menu:

1. Go to **Help** → **What's New in This Version**
2. View all changes in the current version
3. Access the full changelog

### Announcement Settings

Customize your announcement experience in Settings → Announcements:

| Setting | Description |
|---------|-------------|
| Check on startup | Fetch new announcements when app starts |
| Check interval | How often to check (0 = manual only) |
| Native notifications | Show OS notifications |
| Critical dialogs | Always show popup for critical alerts |
| Notification sound | Play sound for notifications |
| Show widget | Display widget on home page |
| Max widget items | Announcements shown in widget |
| Minimum priority | Lowest priority for notifications |
| History retention | How long to keep read announcements |

### Admin Publishing

*(Requires CONFIG_ADMIN or SUPER_ADMIN role)*

Administrators can publish announcements to all users:

1. Go to **Help** → **Announcements**
2. Click **Create Announcement** (admin only)
3. Fill in title, summary, and content
4. Select category and priority
5. Set optional expiration date
6. Preview and publish

**Admin Features:**
- **Markdown support**: Format content with headers, lists, links
- **Priority levels**: Control urgency and notification behavior
- **Targeting**: Show to specific versions or platforms
- **Acknowledgment required**: Force users to acknowledge critical alerts
- **Expiration**: Auto-hide announcements after a date
- **Version tagging**: Associate with app versions for release notes

---

## Automatic Updates

Keep your application up to date automatically.

### GitHub-Based Updates

- **Free infrastructure**: Uses GitHub Releases
- **Automatic checking**: On startup (configurable)
- **Manual check**: Help menu, Check for Updates
- **Release notes**: View changes before updating
- **Checksum verification**: Secure downloads

### Update Options

- **Download and install**: One-click update
- **Skip version**: Do not remind for this version
- **Remind later**: Check again in 24 hours

---

## User Feedback

Submit feedback and report issues directly from the application with intelligent categorization.

### Feedback Types

- **Bug Report**: Report application errors or unexpected behavior
- **Feature Request**: Suggest new features or improvements
- **Accessibility Issue**: Report accessibility barriers or screen reader problems
- **Usability Issue**: Report confusing behavior or UI that could be clearer
- **Performance Issue**: Report slowness, lag, or freezing
- **General Feedback**: Share any other thoughts or suggestions

### Feature Areas

Categorize your feedback by the application area it relates to:

| Feature Area | Description |
|--------------|-------------|
| General / Application-wide | Issues affecting the overall application |
| Streams & Live Audio | Live stream selection and playback |
| Podcasts & Episodes | Podcast feeds, episodes, downloads |
| State Affiliates & SIGs | Affiliate directory listings |
| Playback & Media Controls | Play, pause, volume, speed controls |
| Recording & Downloads | Stream recording, scheduled recordings |
| Favorites & Bookmarks | Quick access to saved content |
| Playlists | Creating and managing playlists |
| Search | Finding content across the app |
| Calendar & Events | ACB calendar integration |
| Voice Control | Speech recognition and commands |
| Settings & Preferences | Application configuration |
| Keyboard Shortcuts | Hotkeys and accelerators |
| Accessibility & Screen Readers | Screen reader support, focus management |
| Data Synchronization | Syncing with ACB servers |
| System Tray | Tray icon and notifications |
| Updates & Installation | App updates and version checks |

### Dynamic Hints

The feedback dialog provides context-sensitive hints based on your selections:
- Description hints update when you change feedback type
- Feature area descriptions help you select the right category
- Tooltips on all controls for additional guidance

### Submission Options

- **GitHub Issues**: Opens your browser with a pre-filled issue form (requires free GitHub account)
- **Copy to Clipboard**: Copy formatted feedback for email submission

### System Information

Optionally include anonymous system details to help diagnose issues:
- ACB Link version
- Python and wxPython versions
- Operating system and architecture
- Screen reader status (Windows)

Access: Help menu, Send Feedback (Control Shift F)

### Affiliate Correction Requests

Help keep affiliate data accurate by suggesting corrections to state affiliate and special interest group (SIG) information.

**Available Corrections:**
- Organization name
- Contact person name
- Email address
- Phone number
- Website URL
- X (Twitter) handle
- Facebook page

**How to Submit:**
1. Navigate to the Affiliates tab
2. Select an affiliate from the State Affiliates or Special Interest Groups list
3. Right-click and choose "Suggest Correction..." or click the "Suggest Correction" button
4. Check the fields you want to correct and enter the new values
5. Choose a submission method:
   - **Submit for Review**: Save locally for admin review (recommended)
   - **Submit via GitHub**: Open a GitHub issue (requires account)
   - **Copy to Clipboard**: For email submission

**Access:**
- Affiliates tab context menu (right-click)
- Affiliates tab "Suggest Correction" button
- Help menu, Suggest Affiliate Correction (Ctrl+Shift+E)

### Affiliate Correction Administration

Administrators can review, approve, and automatically apply affiliate data corrections without manually editing XML files.

**Features:**
- **Correction Queue**: All submitted corrections are stored in a pending queue
- **Review Interface**: View pending, approved, rejected, and applied corrections
- **Approval Workflow**: Review corrections individually with approve/reject actions
- **Batch Processing**: Apply all approved corrections at once
- **Automatic XML Updates**: Approved corrections are safely applied to data files
- **Backup System**: Automatic backup before any changes
- **Audit Trail**: Complete history of all changes with timestamps and reviewers
- **Rollback Capability**: Restore from backups if needed

**How to Use:**
1. Open Tools menu → Affiliate Correction Admin (Ctrl+Shift+A)
2. Filter corrections by status (Pending, Approved, Rejected, Applied)
3. Select a correction and click "View Details" to see full information
4. Click "Approve" or "Reject" for pending corrections
5. Click "Apply to Data" to update the XML file with approved corrections

**Access:** Tools menu, Affiliate Correction Admin (Ctrl+Shift+A)

---

## Quick Actions

Quickly access common functions without navigating menus.

### Quick Status (F5)

- **Instant feedback**: Announces current playback state
- **Screen reader optimized**: Clear spoken summary
- **Includes**: Playing/paused/stopped, content name, volume level

### Panic Key (Ctrl+Shift+M)

- **Instant mute**: Immediately silences audio
- **Auto-minimize**: Minimizes window to tray
- **One-key activation**: Fast response when needed

### Text Size Adjustment

- **Ctrl+Plus**: Increase text size
- **Ctrl+Minus**: Decrease text size
- **Ctrl+0**: Reset to default size
- **Instant apply**: Changes take effect immediately
- **Auto-save**: Preferences persist across sessions

### Resume Playback

- **Automatic prompt**: On startup if previous session detected
- **Context preserved**: Stream name and position saved
- **Optional**: Can skip and start fresh

---

## Listening Statistics

Track your listening habits and engagement.

### Statistics Tracked

- **Total listening time**: Cumulative across all sessions
- **Total sessions**: Number of listening sessions
- **Current streak**: Consecutive days of listening
- **Longest session**: Your longest single listening session
- **Favorite stream**: Most listened-to stream
- **Favorite podcast**: Most listened-to podcast
- **Top streams**: Ranked by listening time

### Privacy

- **Local storage only**: Data never leaves your computer (default)
- **No tracking**: No external analytics by default
- **Opt-in telemetry**: Optional privacy-respecting analytics (see below)

---

## Privacy-Respecting Analytics

ACB Link Desktop includes optional, privacy-first analytics to help improve the application.

### Privacy Principles

- **Opt-in only**: All analytics are disabled by default
- **No PII**: No personally identifiable information is ever collected
- **Transparent**: View exactly what data would be sent before submission
- **User-controlled**: Clear all collected data at any time
- **Local-first**: Statistics stored locally, submission is optional

### Consent Levels

| Level | What's Collected |
|-------|------------------|
| **None** (default) | Nothing - all analytics disabled |
| **Basic** | Crash reports only |
| **Standard** | Crashes + anonymous usage patterns |
| **Full** | All above + performance metrics |

### Data You Can Review

Access: Tools menu > Analytics Settings

- View all collected events
- See statistics summary
- Export data as JSON
- Clear all data

### What We DON'T Collect

- Names, emails, or contact information
- IP addresses or location data
- Content of what you listen to
- Listening history or preferences
- Any data that could identify you

---

## Distribution Channels

ACB Link Desktop is available through multiple distribution channels.

### GitHub Releases (Primary)

- Direct download from GitHub
- Delta updates for efficient bandwidth
- Checksums for verification
- Release notes with each version

### Microsoft Store (Windows)

- Automatic updates via Store
- Sandboxed installation
- Easy uninstall

### Mac App Store (macOS)

- Automatic updates via App Store
- Sandboxed installation
- Gatekeeper verified

### Delta Updates

When updating from GitHub releases:

- Only changed files are downloaded
- Typical savings: 60-80% smaller downloads
- Automatic fallback to full installer if needed
- Checksum verification for security
- **User controlled**: Clear statistics anytime

Access: Tools menu, Listening Statistics

---

## Playback Enhancements

Advanced playback controls and automation features.

### Sleep Timer

- **Quick presets**: 15, 30, 45, 60, 90, and 120 minutes
- **Custom duration**: Set any time up to 8 hours
- **Volume fade-out**: Gradual volume reduction before stopping
- **Status display**: Remaining time shown in status bar
- **Easy cancel**: Stop timer anytime
- **Keyboard shortcut**: Ctrl+T

Access: Playback menu, Sleep Timer

### Playback Speed Control

- **Speed presets**: 0.5x, 0.75x, 1x, 1.25x, 1.5x, 1.75x, 2x
- **Fine control**: Slider for precise adjustment (0.25x to 3x)
- **Persistent**: Preference saved across sessions
- **Instant feedback**: Audible announcement of speed
- **Keyboard shortcut**: Ctrl+P

Access: Playback menu, Playback Speed

### Copy What's Playing

- **One-click copy**: Copy current track info to clipboard
- **Rich content**: Includes stream name, track, artist, link
- **Share-ready**: Formatted text ready for pasting
- **Keyboard shortcut**: Ctrl+Shift+C

Access: Playback menu, Copy What's Playing

### Recently Played

- **Quick access**: 20 most recent streams and podcasts
- **One-click play**: Double-click or press Enter to resume
- **Timestamps**: See when each item was played
- **Clear option**: Remove all history
- **Keyboard shortcut**: Ctrl+Shift+R

Access: Playback menu, Recently Played

### Auto-Play on Startup

- **Automatic start**: Begin playback when app launches
- **Content options**: Last played or specific stream
- **Configurable delay**: 0-30 second delay before playing
- **Conditional**: Only auto-play if previous session was active

Access: Tools menu, Auto-Play on Startup

### Quiet Hours

- **Scheduled silence**: Automatic behavior during set times
- **Time range**: Configure start and end times
- **Daily schedule**: Repeats every day
- **Options**: Mute notifications, reduce volume
- **Volume control**: Set reduced volume percentage

Access: Tools menu, Quiet Hours

### Audio Ducking

- **Auto-lower**: Volume reduces during system sounds
- **Configurable percentage**: Duck to 10-90% of current volume (default 30%)
- **Configurable restore delay**: Set 0.5 to 10 seconds before volume restores (default 2 seconds)
- **Test button**: Preview ducking effect from settings dialog
- **Toggle**: Enable/disable from Tools menu checkbox
- **Settings dialog**: Full configuration via Tools menu

Access:
- Tools menu, Audio Ducking (checkbox to toggle)
- Tools menu, Audio Ducking Settings... (full configuration dialog)

### Media Key Support

- **Hardware keys**: Use keyboard media buttons
- **Play/Pause**: Works globally
- **Stop**: Works globally
- **Volume**: Up and down keys supported
- **Toggle**: Enable/disable from Tools menu

Access: Tools menu, Media Key Support (checkbox)

---

## View Settings and Layout

Customize the application interface to match your preferences.

### Show/Hide UI Elements

Control visibility of interface components via the View menu:

- **Toolbar**: Show or hide the button toolbar
- **Tab Bar**: Show or hide the navigation tabs
- **Status Bar**: Show or hide the status information bar
- **Player Controls**: Show or hide playback controls
- **Now Playing Banner**: Show or hide the current track display
- **Sidebar**: Show or hide the optional favorites sidebar

All settings are saved automatically and persist between sessions.

### Pane Navigation (F6)

Professional-style keyboard navigation between interface sections:

- **F6**: Move focus to the next pane
- **Shift+F6**: Move focus to the previous pane
- **Screen reader**: Pane name announced on focus change

Works like VS Code, Outlook, and other professional applications.

### Focus Mode

Minimal, distraction-free interface:

- **One shortcut**: Ctrl+Shift+D to toggle
- **Auto-hide**: Toolbar, tab bar, status bar, sidebar all hidden
- **Preserved**: Player controls remain visible
- **Restored**: Previous layout restored on exit

### Full Screen Mode

- **Toggle**: F11 or View menu
- **Exit**: F11 or Escape

### View Settings Dialog

Comprehensive configuration dialog:

- **UI Elements tab**: Configure element visibility
- **Appearance tab**: Colors, fonts, spacing
- **Accessibility tab**: High contrast, focus indicators, motion

Access: View menu, View Settings

### Favorites Quick Dial

Instant access to your top 5 favorites:

- **Alt+F1**: Play favorite #1
- **Alt+F2**: Play favorite #2
- **Alt+F3**: Play favorite #3
- **Alt+F4**: Play favorite #4
- **Alt+F5**: Play favorite #5

Quick dial slots are automatically assigned from your favorites list.

### Color Schemes

Built-in accessible color schemes:

- **Light**: Standard light theme
- **Dark**: Comfortable dark theme
- **High Contrast Dark**: Maximum contrast, dark background
- **High Contrast Light**: Maximum contrast, light background
- **Yellow on Black**: High visibility option
- **White on Black**: Classic high contrast
- **Green on Black**: Terminal-style display
- **Black on White**: Reversed high contrast
- **Blue on White**: Gentle high contrast

---

## Customizable Home Page

Create a personalized dashboard with the content that matters most to you.

### Available Widgets

| Widget | Description | Default |
|--------|-------------|---------|
| Welcome | Getting started tips and shortcuts | Enabled |
| Now Playing | Current playback with controls | Enabled |
| Favorite Streams | Quick access buttons for favorite streams | Enabled |
| Favorite Podcasts | Your favorite podcasts with latest episodes | Enabled |
| Recent Episodes | Recently played podcast episodes | Enabled |
| Upcoming Events | ACB calendar events | Enabled |
| My Affiliates | Your selected state/SIG affiliates | Disabled |
| Quick Actions | Common actions (search, record, settings) | Enabled |
| Downloads | Active download progress | Disabled |
| Listening Statistics | Your listening history stats | Disabled |

### Customization Features

- **Enable/Disable widgets**: Choose which sections appear
- **Reorder widgets**: Arrange sections in your preferred order
- **Collapse sections**: Minimize widgets to save space
- **Custom titles**: Rename widgets (coming soon)

### Accessibility Features

- **Heading navigation**: Each widget has proper heading level (H2)
- **Keyboard shortcuts**: Ctrl+H to jump between sections
- **Screen reader friendly**: All sections have accessible names and descriptions
- **Collapse announcements**: State changes announced to screen readers

### Customization Dialog

1. Open View menu, select "Customize Home Page"
2. Check/uncheck widgets to enable/disable
3. Use "Move Up" and "Move Down" to reorder
4. Click OK to apply changes

Access: View menu, Customize Home Page

---

## Settings Backup

Export and import your configuration and data.

### Backup Contents

- User settings and preferences
- Favorites and bookmarks
- Playlists
- Listening statistics
- Keyboard shortcuts
- Last playback state

### Features

- **One-click export**: Creates .acbbackup file
- **Restore anywhere**: Import on new computer
- **Version tagged**: Backup includes metadata
- **Merge option**: Combine with existing settings (future)

Access: Tools menu, Export/Import Settings

---

## First-Run Wizard

Guided setup for new users.

### Setup Pages

1. **Appearance**: Theme selection and text size
2. **Default Stream**: Choose preferred stream
3. **Accessibility**: Screen reader and voice control options

### Theme Options

- Light, Dark, High Contrast Light, High Contrast Dark
- Yellow on Black (high visibility)
- Customizable text size (8-24 pt)

---

## Data Synchronization

Keep your data current with ACB servers.

### Live Data Sources

ACB Link synchronizes the following data from ACB servers:

| Data | Description | Update Frequency |
|------|-------------|------------------|
| Streams | Audio stream URLs and metadata | Weekly |
| Podcasts | Podcast feed directory (37 feeds) | Daily |
| State Affiliates | 47 state organizations | Weekly |
| Special Interest Groups | 18 SIG organizations | Weekly |
| Publications | ACB publications directory | Weekly |
| ACB Sites | ACB website directory | Weekly |

### Synchronization Features

- **Automatic sync**: On startup (configurable)
- **Manual sync**: Tools menu, Sync Data
- **Offline storage**: Bundled data for offline use
- **Change detection**: Only downloads when content changes
- **Sync status**: View last sync time and results

---

## System Scheduling

Schedule tasks that run even when the application is closed.

### Windows Integration

- **Task Scheduler**: Native Windows Task Scheduler integration
- **Background execution**: Tasks run without opening the application
- **Task management**: View, enable, disable, and delete tasks

### macOS Integration

- **launchd**: Native macOS launchd integration
- **Launch agents**: Tasks stored in user's LaunchAgents folder
- **Persistent scheduling**: Tasks survive reboots

### Schedulable Tasks

- **Recordings**: Schedule stream recordings
- **Reminders**: Set event reminders
- **Podcast sync**: Automatic feed updates

---

## Accessibility

ACB Link Desktop is designed to be fully accessible.

### WCAG 2.2 AA Compliance

| Guideline | Description | Status |
|-----------|-------------|--------|
| 1.1 | Text Alternatives | Complete |
| 1.3 | Adaptable | Complete |
| 1.4 | Distinguishable | Complete |
| 2.1 | Keyboard Accessible | Complete |
| 2.4 | Navigable | Complete |
| 3.2 | Predictable | Complete |
| 4.1 | Compatible | Complete |

### Screen Reader Support

**Windows:**
- JAWS: Full support via accessible_output2
- NVDA: Full support via accessible_output2
- Narrator: Native Windows accessibility support
- System Access: Basic support

**macOS:**
- VoiceOver: Full support via AppleScript integration
- Accessibility API: Native NSAccessibility support

### Accessibility Features

- **Accessible names**: All controls properly labeled
- **Live announcements**: Status changes spoken automatically
- **Logical focus order**: Predictable keyboard navigation
- **Focus indicators**: Visible focus ring on all controls
- **High contrast themes**: Light, Dark, High Contrast Light, High Contrast Dark
- **Font size adjustment**: 8pt to 32pt
- **Large cursor option**: Enhanced visibility
- **Reduce motion**: Minimize animations

---

## Platform Support

### Windows

- **Windows 10**: Full support
- **Windows 11**: Full support
- **x64 architecture**: Native support
- **ARM64 architecture**: Full support (Surface Pro X and similar devices)

### macOS

- **macOS 10.14 (Mojave)**: Minimum version
- **macOS 11 (Big Sur) and later**: Full support
- **Apple Silicon**: Native M1, M2, M3 support
- **Intel Macs**: Full support

### Installers

- **Windows**: NSIS installer (.exe) or portable ZIP
- **macOS**: DMG with drag-to-install

---

## System Tray

### Background Operation

- **Tray icon**: Always accessible
- **Minimize to tray**: Hide window, keep playing
- **Close to tray**: X button minimizes instead of exiting
- **Start minimized to tray**: Launch completely hidden in system tray

### Tray Icon Behavior

Configurable click actions:

| Action | Options |
|--------|---------|
| **Double-click** | Show/Hide window, Play/Pause |
| **Single-click** | None, Show/Hide, Play/Pause, Show menu |

### Tray Menu

- **Show or hide window**: Toggle visibility
- **Playback controls**: Play, pause, stop
- **Stream selection**: Quick stream switching
- **Recording control**: Start or stop from tray
- **Settings**: Quick access to settings dialog
- **Exit**: Fully quit the application

### Tray Notifications

- **Now playing notifications**: See what's playing when streams change
- **Configurable duration**: 1-30 seconds
- **Enable/disable**: Full control over notification behavior

---

## Settings

ACB Link Desktop offers comprehensive settings organized into intuitive categories.

### Configuration Tabs

1. **General**: Browser, default tab, language
2. **Appearance**: Theme, fonts, visual accessibility options
3. **Playback**: Speed, volume, skip intervals, equalizer
4. **Storage**: Download paths, recording formats, cache management
5. **Home Tab**: Widget visibility and item counts
6. **Startup**: Launch behavior, session restoration, auto-play
7. **System Tray**: Tray icon behavior, minimize/close options
8. **Notifications**: What notifications to show and how
9. **Keyboard**: Global hotkeys, media keys, navigation style
10. **Privacy**: History management, analytics opt-in
11. **Performance**: Resource usage, downloads, caching
12. **Accessibility**: Screen reader, keyboard-only mode

### Startup Settings

Control how ACB Link launches:

| Setting | Description |
|---------|-------------|
| **Start at login** | Launch ACB Link when you sign in to Windows |
| **Start minimized** | Launch with window minimized |
| **Start minimized to tray** | Launch completely hidden in system tray |
| **Restore last session** | Remember what you were listening to |
| **Auto-play on startup** | Automatically resume playback |
| **Auto-play delay** | Wait 0-30 seconds before auto-playing |
| **Check updates on startup** | Look for new versions automatically |
| **Sync data on startup** | Update stream/podcast data from ACB servers |

### Notification Settings

Fine-tune your notification experience:

| Setting | Description |
|---------|-------------|
| **Enable notifications** | Master toggle for all notifications |
| **Play sounds** | Audio feedback with notifications |
| **Display duration** | How long notifications stay visible |
| **Position** | Screen corner for notifications |

**Notification Types:**
- Now playing changes
- Stream status (connected/disconnected)
- Recording started/stopped
- Download completed
- Calendar event reminders
- Update available

### Keyboard Settings

| Setting | Description |
|---------|-------------|
| **Global hotkeys** | Control ACB Link from any application |
| **Media keys** | Respond to keyboard media buttons |
| **Vim-style navigation** | h/j/k/l for left/down/up/right |
| **Space toggles playback** | Space bar plays/pauses |
| **Escape minimizes** | Escape key minimizes window |

### Privacy Settings

| Setting | Description |
|---------|-------------|
| **Remember search history** | Save recent searches |
| **Remember listening history** | Track what you've listened to |
| **Maximum history items** | Limit stored history (10-1000) |
| **Clear history on exit** | Automatic cleanup when app closes |
| **Analytics (opt-in)** | Help improve ACB Link |
| **Crash reporting (opt-in)** | Send crash reports |

### Performance Settings

| Setting | Description |
|---------|-------------|
| **Low memory mode** | Reduce RAM usage |
| **Reduce CPU when minimized** | Lower CPU when not visible |
| **Hardware acceleration** | Use GPU for rendering |
| **Max concurrent downloads** | Simultaneous podcast downloads (1-10) |
| **Cache podcast artwork** | Store images locally |
| **Preload next episode** | Buffer next playlist item |
| **Max log file size** | Limit log storage (1-100 MB) |
| **Auto-cleanup old logs** | Remove outdated log files |

### Settings Features

- **JSON storage**: Human-readable configuration files
- **Import and export**: Backup and restore settings
- **Reset to defaults**: Easy recovery of default values
- **Apply without closing**: Test changes before saving

---

## Advanced Settings

For expert users who need to configure internal application behavior.

### Access

- **Keyboard Shortcut**: Ctrl+Shift+,
- **Menu**: File → Advanced Settings...

### Warning System

- Confirmation dialog before entering
- Clear explanation of risks
- Option to skip warning in future

### Configuration Tabs

| Tab | Purpose |
|-----|---------|
| Data Sources | Configure URLs for ACB data feeds |
| Network | Timeout, retries, proxy settings |
| Paths | Application and user data directories |
| Updates | Update server and check intervals |
| Defaults | Default values for volume, speed, theme |
| Experimental | Developer features, debug logging |

### Safety Features

- **Validation**: All fields validated before saving
- **Reset to Defaults**: One-click restore of all settings
- **Export/Import**: Backup configuration to JSON file
- **Validate Button**: Check settings without saving

### Admin Authentication (v1.1.0+)

Advanced Settings now requires administrator authentication via GitHub:

| GitHub Permission | Admin Role | Access Level |
|-------------------|------------|--------------|
| None/Read | USER | Cannot access Advanced Settings |
| Write | AFFILIATE_ADMIN | Cannot access Advanced Settings |
| Admin/Maintain | CONFIG_ADMIN | Full access to Advanced Settings |
| Organization Owner | SUPER_ADMIN | Full access to Advanced Settings |

**How to Authenticate:**
1. Create a GitHub Personal Access Token at github.com/settings/tokens
2. Required scope: `read:org` (to verify organization membership)
3. Enter the token when prompted in ACB Link
4. Your role is determined by your GitHub repo permissions

### Server Sync

- Changes made by admins sync to GitHub repository
- All users receive updated configuration on restart
- Git commit history provides complete audit trail
- Offline fallback uses last valid cached configuration

### Data Source Configuration

Configure URLs and caching for each data source:

| Source | Description |
|--------|-------------|
| Streams | Live streaming channel information |
| Podcasts | OPML podcast catalog |
| State Affiliates | State affiliate organizations |
| Special Interest Groups | SIG affiliate data |
| Publications | ACB publications and resources |
| Categories | Content categorization |
| ACB Sites | ACB website directory |

### Network Settings

- **Connection timeout**: 5-120 seconds
- **Retry count**: 0-10 attempts
- **Retry delay**: 1-60 seconds
- **User agent**: Custom identification string
- **Proxy support**: HTTP/HTTPS proxy configuration

### Path Configuration

- **App data directory**: Settings and cache location
- **Cache directory**: Temporary files
- **Logs directory**: Application logs
- **Downloads directory**: Podcast downloads
- **Recordings directory**: Stream recordings

---

## Administration (v1.1.0+)

ACB Link includes a comprehensive administration system for managing organization-wide configuration. **The system uses GitHub for free, zero-cost authentication** - no custom server required!

### Why GitHub-Based Authentication?

- **Completely free** - No server costs, hosting, or maintenance
- **Battle-tested security** - GitHub's auth is trusted by millions
- **No passwords to manage** - Uses GitHub Personal Access Tokens
- **Instant provisioning** - Add admins by adding GitHub collaborators
- **Instant revocation** - Remove access by removing collaborators
- **Built-in MFA** - If user has GitHub MFA, it's automatically used
- **Audit trail included** - GitHub tracks all permission changes

### Admin Roles

Roles are determined by your permissions on the ACB Link config repository:

| GitHub Permission | Admin Role | Level | Capabilities |
|-------------------|------------|-------|--------------|
| None/Read | USER | 0 | Standard application usage |
| Write/Triage | AFFILIATE_ADMIN | 1 | Review and approve affiliate corrections |
| Maintain/Admin | CONFIG_ADMIN | 2 | Modify data sources and network settings |
| Organization Owner | SUPER_ADMIN | 3 | All capabilities plus admin management |

### Admin Login

- **Access via**: File → Admin Login or when attempting admin actions
- **Authentication**: GitHub Personal Access Token (PAT)
- **Session duration**: Until app closes (token in memory only)
- **Security**: PAT never saved to disk, minimal scopes required
- **Accessibility**: WCAG 2.2 AA compliant login dialog

### Creating a GitHub Token

1. Go to https://github.com/settings/tokens/new
2. Set description: "ACB Link Desktop Admin"
3. Select scope: `read:org` (only scope needed)
4. Click "Generate token" and copy it
5. Enter the token in ACB Link when prompted

### Organization Configuration

Admins can configure organization-wide settings stored in GitHub:

| Setting Category | Examples |
|-----------------|----------|
| Data Sources | Stream URLs, podcast feeds, affiliate data |
| Network | Timeouts, retries, proxy configuration |
| Updates | Update server, check intervals |
| Defaults | Default theme, volume, playback settings |

### Affiliate Correction Administration

Secure workflow for updating affiliate data without manual XML editing:

1. **User submits** correction via Feedback dialog
2. **Correction queued** for admin review
3. **Admin authenticates** with GitHub PAT (if not already)
4. **Admin reviews** in dedicated Admin Review Panel
5. **Approval/Rejection** with notes for audit trail
6. **Automatic backup** created before any changes
7. **XML updated** atomically with validation
8. **Rollback available** if issues detected

### Access Methods

| Feature | Menu Location | Shortcut |
|---------|---------------|----------|
| Admin Login | File → Admin Login | - |
| Advanced Settings | File → Advanced Settings | Ctrl+Shift+, |
| Affiliate Admin | Tools → Affiliate Correction Admin | Ctrl+Shift+A |

### Security Features

- **GitHub handles auth** - Battle-tested security infrastructure
- **Minimal token scope** - Only `read:org` permission required
- **Memory-only storage** - PAT never written to disk
- **MFA inherited** - User's GitHub 2FA protects their token
- **Audit via Git** - All config changes tracked in commit history
- **Automatic Backups** - Data backed up before modifications
- **Failsafe Operation** - App works offline with cached config

---

## Technical Features

### Local Web Server

- **FastAPI backend**: Modern async server
- **Uvicorn**: High-performance ASGI
- **Port 8765**: Default local port
- **Accessible HTML**: WCAG compliant rendering

### Data Management

- **JSON settings**: Stored in user profile
- **Playback positions**: Resume tracking
- **Recent items**: History management
- **Favorites storage**: Persistent favorites
- **Playlist storage**: Saved playlists

### Configuration Files

All configuration is stored in JSON files:

| File | Purpose | Location |
|------|---------|----------|
| config.json | Application configuration | App data folder |
| settings.json | User preferences | App data folder |
| favorites.json | Saved favorites | App data folder |
| playlists.json | User playlists | App data folder |
| history.json | Listening history | App data folder |

### Performance

- **Fast startup**: Less than 3 seconds
- **Low memory**: Less than 200 MB typical
- **Background tasks**: Threaded operations
- **Lazy loading**: On-demand resource loading

---

*Feature List Version 1.0*
*Last Updated: January 2026*
*Copyright 2026 American Council of the Blind / BITS*
