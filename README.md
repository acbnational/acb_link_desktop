# ACB Link Desktop

**Your Gateway to ACB Media Content**

A fully accessible desktop application for streaming ACB Radio, podcasts, and connecting with the American Council of the Blind community.

---

## About

ACB Link Desktop is a cross-platform desktop application developed by BITS (Blind Information Technology Specialists) for the American Council of the Blind. It provides easy access to ACB's streaming audio content, podcasts, and organizational resources with full accessibility support for screen readers.

### Why ACB Link Desktop

- Cross-Platform: Native support for Windows and macOS
- Screen Reader First: Designed for NVDA, JAWS, Narrator, and VoiceOver
- WCAG 2.2 AA Compliant: Meets or exceeds web accessibility guidelines
- System Scheduling: Record streams even when the app is not running
- Auto-Updates: Automatic updates via GitHub Releases
- Offline Capable: Download podcasts for offline listening
- Voice Control: Hands-free operation with wake word activation

---

## Features

### Streaming

- 10 ACB Media Streams including Main, Treasure Trove, and Cafe
- One-click playback with keyboard shortcuts
- Stream recording with multiple format options
- Background playback with system tray integration

### Podcasts

- Over 37 ACB Podcasts organized by category
- Episode downloads for offline listening
- Playback position memory
- Variable speed playback from 0.5x to 2.0x

### Favorites and Playlists

- Save favorite streams and podcast episodes
- Create custom playlists
- Quick access from the home screen

### Search

- Global search across all content
- Filter by streams, podcasts, affiliates, or resources
- Keyboard-accessible results

### Calendar Integration

- ACB events and conventions calendar
- Add events to your calendar with iCal export
- Event reminders

### Voice Control

- Wake word activation with "Hey ACB Link"
- Voice commands for hands-free operation
- Natural language understanding
- Customizable voice feedback

### Accessibility

- Full screen reader support for NVDA, JAWS, Narrator, and VoiceOver
- WCAG 2.2 AA compliant
- High contrast themes
- Keyboard-only navigation
- Customizable focus indicators

### Scheduling

- Schedule recordings when app is closed
- Windows Task Scheduler integration
- macOS launchd integration
- Podcast sync scheduling

### Auto-Updates

- Check for updates via GitHub Releases
- Automatic download and installation
- Update notifications

### Data Synchronization

- Live sync with ACB servers
- Automatic data updates on startup
- Offline fallback with bundled data
- Manual sync from Tools menu

---

## Installation

### Supported Platforms

- Windows 10 and Windows 11 (x64 or ARM64)
- macOS 11 and later (Intel and Apple Silicon)
- Python 3.9 or higher for development

### Quick Install

```powershell
# Clone the repository
git clone https://github.com/acbnational/acb_link_desktop.git
cd acb_link_desktop

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m acb_link
```

### From Release

Download the latest installer from the Releases page:
https://github.com/acbnational/acb_link_desktop/releases

---

## Usage

### Keyboard Shortcuts

Playback Controls:
- Space or Ctrl+P: Play or Pause
- Ctrl+S: Stop
- Ctrl+Up: Volume Up
- Ctrl+Down: Volume Down
- Ctrl+M: Mute
- Ctrl+Right: Skip Forward
- Ctrl+Left: Skip Backward

Navigation:
- Ctrl+1 through Ctrl+9: Switch tabs
- Alt+1 through Alt+0: Play streams 1 through 10
- Ctrl+F: Search
- Ctrl+Comma: Settings
- F1: Help
- Alt+F4: Quit

### Voice Commands

When voice control is enabled, say "Hey ACB Link" then:
- "Play stream one" through "Play stream ten"
- "Pause" or "Stop"
- "Volume up" or "Volume down"
- "Search for" followed by your query
- "Go to streams" or other tab names

### Screen Reader Tips

- Use Tab and Shift+Tab to navigate between controls
- Use Arrow keys to navigate within lists and trees
- Press Enter to activate buttons and play items
- All controls have accessible names and descriptions
- Status changes are announced automatically

---

## Accessibility

ACB Link Desktop is built with accessibility as a core requirement, not an afterthought.

### WCAG 2.2 AA Compliance

All major WCAG 2.2 AA guidelines are met:
- 1.1 Text Alternatives: Complete
- 1.3 Adaptable: Complete
- 1.4 Distinguishable: Complete
- 2.1 Keyboard Accessible: Complete
- 2.4 Navigable: Complete
- 3.2 Predictable: Complete
- 4.1 Compatible: Complete

### Screen Reader Support

- NVDA: Full support via accessible_output2
- JAWS: Full support via accessible_output2
- Narrator: Native Windows accessibility support
- VoiceOver: Full macOS support via AppleScript integration

### Visual Accessibility

- High contrast themes in light and dark variants
- Configurable font sizes from 8 to 32 points
- Customizable focus ring width
- Reduced motion option

---

## Project Structure

```
acb_link_desktop/
├── acb_link/              Main application package
│   ├── __init__.py        Package initialization
│   ├── accessibility.py   WCAG 2.2 AA compliance module
│   ├── config.py          Centralized configuration management
│   ├── data.py            Data structures and constants
│   ├── data_sync.py       Live data synchronization
│   ├── dialogs.py         Settings and other dialogs
│   ├── enhanced_voice.py  Wake word and voice control
│   ├── main_frame.py      Main application window
│   ├── main.py            Application entry point
│   ├── media_player.py    Audio playback engine
│   ├── panels.py          UI panels for Home, Streams, etc.
│   ├── scheduler.py       System-level task scheduling
│   ├── server.py          Local web server
│   ├── settings.py        Settings management
│   ├── styles.py          Theme and styling
│   ├── system_tray.py     System tray integration
│   ├── updater.py         GitHub-based auto-updates
│   ├── utils.py           Utility functions
│   └── voice_control.py   Voice command processing
├── data/                  Data files
│   └── s3/               ACB data including streams and affiliates
├── docs/                  Documentation
├── installer/             Windows NSIS installer scripts
├── scripts/               Build scripts for Windows and macOS
├── tests/                 Unit tests
├── requirements.txt       Python dependencies
├── requirements-dev.txt   Development dependencies
├── pyproject.toml         Project configuration
├── acb_link.spec          PyInstaller spec for Windows
└── README.md              This file
```

---

## Documentation

Comprehensive documentation is available in the docs folder:

- User Guide: docs/USER_GUIDE.md - Complete user manual
- Features: docs/FEATURES.md - Detailed feature list
- Installation: docs/INSTALLATION.md - Installation instructions
- Accessibility: docs/ACCESSIBILITY.md - Accessibility guide
- Development: docs/DEVELOPMENT.md - Developer guide
- Deployment: docs/DEPLOYMENT.md - Build and release procedures
- Changelog: docs/CHANGELOG.md - Version history
- Roadmap: docs/ROADMAP.md - Future plans
- Announcement: docs/ANNOUNCEMENT.md - Release announcement
- PRD: docs/PRD.md - Product requirements
- Technical Reference: docs/TECHNICAL_REFERENCE.md - Technical documentation

---

## Development

### Setting Up Development Environment

```powershell
# Clone and setup
git clone https://github.com/acbnational/acb_link_desktop.git
cd acb_link_desktop
python -m venv venv
.\venv\Scripts\activate

# Install all dependencies including development tools
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with verbose logging
python -m acb_link --debug
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Document all public functions and classes
- Ensure all UI elements have accessible names

### Testing

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=acb_link

# Run accessibility tests
pytest tests/test_accessibility.py
```

---

## Contributing

We welcome contributions from the community. Please read the Contributing Guide in CONTRIBUTING.md before submitting a pull request.

### How to Contribute

1. Fork the repository
2. Create a feature branch: git checkout -b feature/amazing-feature
3. Make your changes
4. Run tests: pytest
5. Commit your changes: git commit -m "Add amazing feature"
6. Push to the branch: git push origin feature/amazing-feature
7. Open a Pull Request

### Reporting Issues

Please use the GitHub Issues page to report bugs or request features:
https://github.com/acbnational/acb_link_desktop/issues

When reporting bugs, please include:
- Your operating system and version
- Your Python version
- Your screen reader if applicable
- Steps to reproduce the issue

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## Acknowledgments

- American Council of the Blind for their mission and support
- BITS (Blind Information Technology Specialists) for development
- The accessibility community for feedback and testing
- Contributors and testers who helped make this project accessible

---

## Contact

- ACB Website: https://acb.org
- BITS: https://acb.org/bits
- Email: bits@acb.org

---

Made with care for the blind and low vision community.

Copyright 2026 American Council of the Blind
