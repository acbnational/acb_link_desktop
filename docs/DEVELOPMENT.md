# ACB Link Desktop - Development Guide

This guide covers setting up a development environment for ACB Link Desktop.

## Prerequisites

### Required Software

- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/)
- **VS Code** (recommended) - [Download](https://code.visualstudio.com/)

### Windows-Specific

- **Visual Studio Build Tools** - For compiling certain dependencies
- **VLC 3.0+** (optional) - For VLC audio backend

### macOS-Specific

- **Xcode Command Line Tools** - `xcode-select --install`
- **Homebrew** (recommended) - [Install](https://brew.sh/)

---

## Environment Setup

### Clone the Repository

```bash
git clone https://github.com/acbnational/acb_link_desktop.git
cd acb_link_desktop
```

### Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.\venv\Scripts\activate.bat

# Activate (macOS/Linux)
source venv/bin/activate
```

### Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Development dependencies
pip install -e ".[dev]"

# Windows-specific
pip install accessible_output2 pyaudio python-vlc

# macOS-specific
pip install pyobjc-framework-Cocoa pyaudio

# Optional: Wake word support (~5GB download)
# Enables "Hey ACB Link" activation instead of keyboard shortcut
pip install openwakeword torch torchaudio
```

> **Note:** Wake word support (openwakeword + torch) adds ~5GB of ML dependencies. The standard installer excludes these to keep the download size manageable. Voice control works without them using the `Ctrl+Shift+V` keyboard shortcut.

---

## Project Structure

```
acb_link_desktop/
├── acb_link/                 # Main application package
│   ├── __init__.py          # Package init, version info, exports
│   ├── accessibility.py      # Screen reader & WCAG 2.2 AA support
│   ├── advanced_playback.py  # Bookmarks, A-B repeat
│   ├── advanced_settings.py  # Admin-only advanced settings dialog
│   ├── admin_auth_ui.py      # GitHub-based admin login UI
│   ├── admin_config.py       # Legacy server-based admin config
│   ├── affiliate_admin.py    # Affiliate correction admin panel
│   ├── affiliate_feedback.py # Affiliate correction submission
│   ├── analytics.py          # Privacy-respecting analytics
│   ├── app_enhancements.py   # Performance, notifications, state
│   ├── calendar_integration.py # Calendar sync
│   ├── config.py             # Application configuration
│   ├── data_sync.py          # Data synchronization
│   ├── data.py               # Data structures, constants
│   ├── dialogs.py            # Settings and dialogs
│   ├── distribution.py       # Distribution channels, delta updates
│   ├── enhanced_voice.py     # Advanced voice control
│   ├── event_scheduler.py    # Event scheduling
│   ├── favorites.py          # Favorites management
│   ├── feedback.py           # User feedback system
│   ├── github_admin.py       # GitHub-based admin authentication (NEW)
│   ├── localization.py       # Multi-language support
│   ├── main_frame.py         # Main application window
│   ├── main.py               # Entry point
│   ├── media_player.py       # Audio playback
│   ├── native_player.py      # VLC/system audio backend
│   ├── new_panels.py         # Feature panels (favorites, etc)
│   ├── offline.py            # Offline mode support
│   ├── panels.py             # UI panels
│   ├── playback_enhancements.py # Sleep timer, ducking, etc
│   ├── playlists.py          # Playlist management
│   ├── podcast_manager.py    # Podcast downloads
│   ├── scheduled_recording.py # Stream recording
│   ├── scheduler.py          # System-level scheduling
│   ├── search.py             # Search functionality
│   ├── server.py             # Local web server
│   ├── settings.py           # Settings management
│   ├── shortcuts.py          # Keyboard shortcuts config
│   ├── styles.py             # Theme and styling
│   ├── system_tray.py        # System tray
│   ├── updater.py            # GitHub update system
│   ├── user_experience.py    # UX enhancements
│   ├── utils.py              # Utilities
│   ├── view_settings.py      # View/pane configuration
│   └── voice_control.py      # Voice commands
├── data/                     # Data files
│   └── s3/                   # ACB data (XML, OPML, PLS)
├── docs/                     # Documentation
├── installer/                # Installer scripts
├── scripts/                  # Build scripts
├── tests/                    # Unit tests
├── requirements.txt          # Production dependencies
├── pyproject.toml            # Project configuration
├── acb_link.spec             # PyInstaller spec (Windows)
└── README.md                 # Project readme
```

---

## Running the Application

### Development Mode

```bash
# Run with Python
python -m acb_link

# Run with debug logging
python -m acb_link --debug

# Run with specific log level
python -m acb_link --log-level DEBUG
```

### VS Code Launch Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "ACB Link",
            "type": "debugpy",
            "request": "launch",
            "module": "acb_link",
            "args": ["--debug"],
            "console": "integratedTerminal"
        }
    ]
}
```

---

## Code Style

### Formatting

We use **Black** for code formatting:

```bash
# Format all files
black acb_link/

# Check without modifying
black --check acb_link/
```

### Linting

We use **flake8** for linting:

```bash
flake8 acb_link/
```

### Type Checking

We use **mypy** for type checking:

```bash
mypy acb_link/
```

### Pre-commit Configuration

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

Install:
```bash
pip install pre-commit
pre-commit install
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=acb_link --cov-report=html

# Run specific test file
pytest tests/test_accessibility.py

# Run with verbose output
pytest -v
```

### Writing Tests

```python
# tests/test_example.py
import pytest
from acb_link.accessibility import announce, make_accessible

def test_announce_does_not_raise():
    """Test that announce doesn't raise exceptions."""
    # Should not raise even if no screen reader
    announce("Test message")

def test_make_accessible_sets_name():
    """Test that make_accessible sets control name."""
    import wx
    app = wx.App()
    frame = wx.Frame(None)
    button = wx.Button(frame, label="Test")

    make_accessible(button, "Test Button", "A test button")

    assert button.GetName() == "Test Button"

    frame.Destroy()
    app.Destroy()
```

---

## Accessibility Development

### Required Practices

1. **All controls must have accessible names**:
   ```python
   from .accessibility import make_accessible

   button = wx.Button(parent, label="▶")
   make_accessible(button, "Play", "Start playback")
   ```

2. **List controls need descriptions**:
   ```python
   from .accessibility import make_list_accessible

   list_ctrl = wx.ListCtrl(parent)
   make_list_accessible(list_ctrl, "Streams list", "Select a stream")
   ```

3. **Status changes must be announced**:
   ```python
   from .accessibility import announce

   def on_play(self):
       self.player.play()
       announce(f"Playing {self.current_stream}")
   ```

### Testing Accessibility

1. **With NVDA (Windows)**:
   - Install NVDA (free): https://www.nvaccess.org/
   - Run ACB Link
   - Navigate with Tab, Arrow keys
   - Verify all controls are announced

2. **With VoiceOver (macOS)**:
   - Enable: Command+F5
   - Navigate with VO+Arrow keys
   - Verify all controls are accessible

---

## Admin Module Development

### GitHub-Based Authentication

The admin system uses GitHub as an identity provider. Key modules:

- `github_admin.py` - Core authentication and role management
- `admin_auth_ui.py` - Login dialogs and session display
- `advanced_settings.py` - Admin-only settings dialog
- `affiliate_admin.py` - Affiliate correction review panel

### Testing Admin Features

To test admin features locally:

1. **Create a GitHub PAT** with `read:org` scope
2. **Set up test roles** by adjusting repository permissions:
   - Organization owner → SUPER_ADMIN
   - Repository admin → CONFIG_ADMIN
   - Repository write → AFFILIATE_ADMIN

3. **Mock authentication** for unit tests:
   ```python
   from acb_link.github_admin import AdminRole, AdminSession

   # Create mock session for testing
   mock_session = AdminSession(
       user_id="test_user",
       username="testuser",
       role=AdminRole.CONFIG_ADMIN,
       permissions={"advanced_settings", "view_audit_log"},
       authenticated_at=datetime.now(),
       expires_at=datetime.now() + timedelta(hours=8)
   )
   ```

4. **Test role requirements**:
   ```python
   from acb_link.github_admin import GitHubAdminManager

   manager = GitHubAdminManager()

   # Test that unauthorized access is blocked
   with pytest.raises(PermissionError):
       manager.require_role(AdminRole.SUPER_ADMIN)
   ```

### Adding New Admin Features

1. Define required role/permission in `github_admin.py`
2. Add UI in appropriate dialog module
3. Use `require_role()` or `require_permission()` decorators
4. Ensure all controls are accessible
5. Add audit logging for sensitive operations

---

## Building Installers

### Windows

```powershell
# Build executable
.\scripts\build_windows.ps1

# Build with installer
.\scripts\build_windows.ps1

# Skip installer (just executable)
.\scripts\build_windows.ps1 -SkipInstaller
```

Output:
- `dist/ACBLink/ACBLink.exe` - Executable
- `dist/ACBLink-X.X.X-Setup.exe` - Installer
- `dist/ACBLink-X.X.X-Portable.zip` - Portable ZIP

### macOS

```bash
# Make script executable
chmod +x scripts/build_macos.sh

# Build
./scripts/build_macos.sh

# Build with specific version
./scripts/build_macos.sh 1.0.0
```

Output:
- `dist/ACB Link Desktop.app` - Application bundle
- `dist/ACBLink-X.X.X-macOS.dmg` - DMG installer

---

## Release Process

### Version Bump

1. Update version in `acb_link/__init__.py`:
   ```python
   __version__ = "1.0.0"
   ```

2. Update version in `pyproject.toml`:
   ```toml
   version = "1.0.0"
   ```

3. Update CHANGELOG.md

### Create Release

1. Commit version changes:
   ```bash
   git add -A
   git commit -m "Release v1.0.0"
   git tag v1.0.0
   git push origin main --tags
   ```

2. Build installers for all platforms

3. Create GitHub Release:
   - Go to Releases > Draft new release
   - Select tag v1.0.0
   - Add release notes
   - Upload installer files
   - Publish release

---

## Debugging

### Log Files

Logs are stored in:
- Windows: `%USERPROFILE%\.acb_link\logs\`
- macOS: `~/.acb_link/logs/`

### Debug Mode

```bash
python -m acb_link --debug
```

This enables:
- Verbose logging
- Debug menu
- Error dialogs with stack traces

### Common Issues

**wxPython not found**:
```bash
pip install wxPython
```

**accessible_output2 import error (Windows)**:
```bash
pip install accessible_output2
```

**pyaudio build fails**:
- Windows: Install from wheel
- macOS: `brew install portaudio && pip install pyaudio`

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

### Quick Checklist

- [ ] Code follows style guidelines (Black, flake8)
- [ ] Type hints added for new functions
- [ ] Tests added for new functionality
- [ ] Accessibility maintained/improved
- [ ] Documentation updated
- [ ] Changelog updated

---

*Development Guide Version 1.0*
*Last Updated: January 2026*
