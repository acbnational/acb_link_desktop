# Accessibility Guide

ACB Link Desktop is designed to be fully accessible to users who are blind or visually impaired.
This guide covers accessibility features and best practices.

## Screen Reader Support

### Windows

ACB Link Desktop supports these screen readers:

| Screen Reader | Support Level | Notes |
|---------------|---------------|-------|
| **NVDA** | Full | Recommended for best experience |
| **JAWS** | Full | All features work |
| **Narrator** | Full | Windows built-in |
| **System Access** | Good | Basic support |

**To verify screen reader detection:**
1. Open ACB Link Desktop
2. The screen reader should announce "ACB Link Desktop window"
3. Navigate with Tab to hear control names

### macOS

ACB Link Desktop has deep VoiceOver integration:

| Feature | Support Level |
|---------|---------------|
| **Element announcement** | Full |
| **Rotor navigation** | Full |
| **Keyboard commands** | Full |
| **VoiceOver gestures** | Supported |

**Enable VoiceOver:**
- Press **Command + F5**
- Or: System Preferences > Accessibility > VoiceOver

---

## Keyboard Navigation

### Global Shortcuts

| Action | Windows | macOS |
|--------|---------|-------|
| Play/Pause | Space | Space |
| Stop | Ctrl+S | Command+S |
| Volume Up | Ctrl+Up | Command+Up |
| Volume Down | Ctrl+Down | Command+Down |
| Mute | Ctrl+M | Command+M |
| Next Stream | Ctrl+Right | Command+Right |
| Previous Stream | Ctrl+Left | Command+Left |
| Settings | Ctrl+Comma | Command+Comma |
| Check Updates | Ctrl+U | Command+U |
| Exit | Alt+F4 | Command+Q |

### Navigation

| Action | Key |
|--------|-----|
| Move between controls | Tab / Shift+Tab |
| Move between panes | F6 / Shift+F6 |
| Switch to next tab | Ctrl+Tab |
| Switch to previous tab | Ctrl+Shift+Tab |
| Jump to specific tab | Ctrl+1 through Ctrl+5 |
| Move in lists | Arrow Up/Down |
| Select item | Enter or Space |
| Open context menu | Application key or Shift+F10 |
| Cancel/Close | Escape |

### Pane Navigation (F6)

The application is divided into four navigable panes:

1. **Tab Bar** - Switch between main sections (Streams, Podcasts, etc.)
2. **Tab Content** - The current panel's main content area
3. **Player Controls** - Playback controls at the bottom
4. **Status Bar** - Application status information

Press F6 to cycle forward through panes, Shift+F6 to cycle backward.
Screen reader announces the pane name when focus changes.

### Tab Navigation (Ctrl+Tab)

Switch between the main content tabs:

- **Ctrl+Tab** - Move to the next tab
- **Ctrl+Shift+Tab** - Move to the previous tab
- **Ctrl+1 to Ctrl+5** - Jump directly to a specific tab

Focus automatically moves to the primary control in each tab.

### Menu Navigation

| Action | Key |
|--------|-----|
| Open menu bar | Alt or F10 |
| Navigate menus | Arrow keys |
| Select menu item | Enter |
| Close menu | Escape |

---

## Interface Elements

### Streams List

The streams list shows available audio streams.

**Navigating:**
1. Press Tab until you reach "Streams list"
2. Use Up/Down arrows to move through streams
3. Press Enter to play the selected stream
4. Screen reader announces stream name and status

**Columns:**
- Stream name
- Category
- Status (playing/stopped)

### Podcasts List

Browse and play podcast episodes.

**Navigating:**
1. Tab to "Podcasts panel"
2. Tab to "Podcast list" to browse shows
3. Select a show with Enter
4. Tab to "Episodes list"
5. Select an episode with Enter to play

### Media Controls

Located at the bottom of the window.

**Controls (in order):**
1. Play button - Starts playback
2. Pause button - Pauses playback
3. Stop button - Stops playback
4. Volume slider - Adjusts volume (0-100%)
5. Mute checkbox - Toggles mute

### Settings Dialog

Access via File > Settings or Ctrl+Comma.

**Tab pages:**
1. **General** - Startup options, theme
2. **Playback** - Audio backend, quality
3. **Accessibility** - Screen reader, font size
4. **Scheduling** - Recurring tasks
5. **Updates** - Auto-update settings

### Admin Dialogs

Administrative features are fully accessible:

**GitHub Login Dialog:**
- Clear instructions for obtaining a Personal Access Token
- Help link opens GitHub token creation page
- Password field for secure token entry
- Role assignment announced upon successful login
- Error messages are descriptive and actionable

**Advanced Settings Dialog (Requires CONFIG_ADMIN):**
- All settings have accessible labels and tooltips
- Radio buttons for mutually exclusive options
- Help text explains each setting's impact
- Success/failure messages are announced

**Affiliate Admin Panel (Requires AFFILIATE_ADMIN):**
- List of pending corrections is keyboard navigable
- Approve/Reject buttons have clear accessible names
- Status updates are announced via live region
- Confirmation dialogs for destructive actions

---

## Accessibility Settings

### Screen Reader Options

**Menu: File > Settings > Accessibility**

| Setting | Description |
|---------|-------------|
| **Enable announcements** | Turn spoken feedback on/off |
| **Announce status changes** | Speak when playback status changes |
| **Announce connections** | Speak connection status |
| **Verbose mode** | Include additional details |

### Visual Options

| Setting | Description |
|---------|-------------|
| **Theme** | Light, Dark, or High Contrast |
| **Font size** | Small, Medium, Large, Extra Large |
| **Show focus ring** | Visible indicator on focused control |

### High Contrast Mode

For users with low vision:

1. Open Settings (Ctrl+Comma)
2. Go to Accessibility tab
3. Select "High Contrast" theme
4. Click OK

This provides:
- Black background, white text
- Bold, larger fonts
- Thick focus indicators
- No background images

---

## Voice Control

ACB Link Desktop includes voice command support.

### Enabling Voice Control

1. Open Settings (Ctrl+Comma)
2. Go to Voice Control tab
3. Check "Enable voice commands"
4. Configure wake word (default: "ACB Link")

### Key Feedback Sounds

Voice control provides audio feedback to indicate when listening starts and stops:

- **Key down sound**: Plays when voice recognition activates
- **Key up sound**: Plays when voice recognition deactivates

To configure key feedback sounds:

1. Go to Settings > Voice Control
2. Scroll to "Key Feedback Sounds" section
3. Enable or disable sounds with the checkbox
4. Optionally set custom sound files (MP3, WAV, or OGG)

This audio feedback is especially helpful for screen reader users to know when the system is listening for commands.

### Commands

| Say This | Action |
|----------|--------|
| "Play" | Start playback |
| "Pause" | Pause playback |
| "Stop" | Stop playback |
| "Next stream" | Switch to next stream |
| "Previous stream" | Switch to previous stream |
| "Volume up" | Increase volume |
| "Volume down" | Decrease volume |
| "What's playing?" | Announce current stream |

---

## Status Announcements

ACB Link Desktop automatically announces important events:

| Event | Announcement Example |
|-------|---------------------|
| Stream connected | "Now playing ACB Main Audio" |
| Stream disconnected | "Stream disconnected, reconnecting" |
| Recording started | "Recording started" |
| Recording stopped | "Recording saved to Downloads" |
| Volume changed | "Volume 50 percent" |
| Error | "Error: Unable to connect to stream" |

---

## Tips for Screen Reader Users

### Efficient Navigation

1. **Use Tab** to move between major sections
2. **Use Arrow keys** within lists
3. **Use shortcuts** for frequent actions (Space=Play/Pause)
4. **Use the Help menu** to see all shortcuts

### First Time Setup

1. On first launch, you'll hear "Welcome to ACB Link Desktop"
2. Tab to the Streams list
3. Press Down to hear available streams
4. Press Enter to play

### Finding Streams

1. Press Ctrl+F to open search
2. Type part of the stream name
3. Results are announced as you type
4. Press Down to move through results
5. Press Enter to play

---

## Troubleshooting

### Screen Reader Not Detecting Application

**Windows:**
1. Ensure screen reader is running
2. Restart ACB Link Desktop
3. Try running as Administrator

**macOS:**
1. Ensure VoiceOver is enabled (Command+F5)
2. Check System Preferences > Security > Privacy > Accessibility
3. Grant ACB Link Desktop access

### Announcements Not Working

1. Open Settings > Accessibility
2. Verify "Enable announcements" is checked
3. Check your screen reader volume

### Focus Problems

If focus seems lost:
1. Press Alt to activate menu bar
2. Press Escape to close menus
3. Press Tab to move to a control

### Keyboard Shortcuts Not Working

1. Ensure ACB Link Desktop window has focus
2. Check that no dialog is open
3. Verify shortcut in Help > Keyboard Shortcuts

---

## Compliance

ACB Link Desktop is designed to meet:

- **WCAG 2.2 Level AA** - Web Content Accessibility Guidelines
- **Section 508** - US accessibility requirements
- **EN 301 549** - European accessibility standard

### Compliance Checklist

- [x] All functionality accessible via keyboard
- [x] All images have text alternatives
- [x] Sufficient color contrast (4.5:1 minimum)
- [x] Focus visible on all interactive elements
- [x] Text resizable up to 200%
- [x] Status messages announced to screen readers
- [x] No keyboard traps
- [x] Consistent navigation
- [x] Labels for all form controls
- [x] Error identification and suggestions

---

## Feedback

We welcome feedback on accessibility:

- **Email**: [accessibility@acb.org](mailto:accessibility@acb.org)
- **GitHub Issues**: [Report accessibility issues](https://github.com/acbnational/acb_link_desktop/issues)

Please include:
- Your screen reader and version
- Operating system
- Steps to reproduce any issues
- Expected vs. actual behavior

---

*Accessibility Guide Version 1.0*  
*Last Updated: January 2026*
