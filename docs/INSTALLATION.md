# ACB Link Desktop - Installation Guide

## System Requirements

### Windows

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| OS | Windows 10 (64-bit) | Windows 11 |
| Architecture | x64 or ARM64 | x64 or ARM64 |
| RAM | 256 MB | 512 MB |
| Storage | 100 MB | 500 MB (+ 5GB for optional wake word) |
| Internet | Required for streaming | Broadband |

### macOS

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| OS | macOS 10.14 (Mojave) | macOS 13+ |
| Architecture | Intel or Apple Silicon | Apple Silicon |
| RAM | 256 MB | 512 MB |
| Storage | 100 MB | 500 MB (+ 5GB for optional wake word) |
| Internet | Required for streaming | Broadband |

---

## Windows Installation

### Option 1: Installer (Recommended)

1. **Download** the latest installer:
   - Go to [GitHub Releases](https://github.com/acbnational/acb_link_desktop/releases)
   - Download `ACBLink-X.X.X-Setup.exe`

2. **Verify download** (optional but recommended):
   - Download `ACBLink-X.X.X-SHA256.txt`
   - Open PowerShell and run:
     ```powershell
     Get-FileHash ACBLink-X.X.X-Setup.exe -Algorithm SHA256
     ```
   - Compare with the checksum file

3. **Run installer**:
   - Double-click the downloaded file
   - If Windows SmartScreen appears, click "More info" then "Run anyway"
   - Follow the installation wizard
   - Choose installation directory (default: `C:\Program Files\ACB Link Desktop`)

4. **Launch**:
   - From Start Menu: "ACB Link Desktop"
   - From Desktop shortcut
   - Keyboard: `Win`, type "ACB Link", press `Enter`

### Option 2: Portable Version

1. **Download** the portable ZIP:
   - Download `ACBLink-X.X.X-Portable.zip`

2. **Extract**:
   - Right-click the ZIP file
   - Select "Extract All..."
   - Choose a location (e.g., `C:\ACBLink`)

3. **Run**:
   - Navigate to the extracted folder
   - Run `ACBLink.exe`

### Windows ARM64 Notes

ACB Link fully supports Windows on ARM devices (Surface Pro X, etc.):
- Same installer works for x64 and ARM64
- All features available
- VLC ARM64 builds supported

---

## macOS Installation

### Option 1: DMG Installer (Recommended)

1. **Download** the DMG:
   - Go to [GitHub Releases](https://github.com/acbnational/acb_link_desktop/releases)
   - Download `ACBLink-X.X.X-macOS.dmg`

2. **Install**:
   - Double-click the DMG to mount it
   - Drag "ACB Link Desktop" to Applications folder
   - Eject the DMG

3. **First Launch** (important for unsigned builds):
   - Open Finder and go to Applications
   - Right-click (or Control-click) "ACB Link Desktop"
   - Select "Open"
   - Click "Open" in the security dialog
   - Subsequent launches work normally

4. **VoiceOver Users**:
   - Enable VoiceOver: `Command+F5`
   - Navigate with `VO+Right/Left`
   - Activate with `VO+Space`

### Gatekeeper and Security

If you see "ACB Link Desktop cannot be opened because the developer cannot be verified":

1. Open **System Preferences** > **Security & Privacy**
2. Click the **General** tab
3. You'll see a message about ACB Link being blocked
4. Click **Open Anyway**

### Apple Silicon Notes

ACB Link runs natively on Apple Silicon (M1, M2, M3):
- No Rosetta 2 required
- Full performance
- Full VoiceOver support

---

## Installing from Source

For developers or advanced users:

### Prerequisites

- Python 3.9 or later
- Git
- pip (Python package manager)

### Steps

```bash
# Clone the repository
git clone https://github.com/acbnational/acb_link_desktop.git
cd acb_link_desktop

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Windows-specific dependencies
pip install accessible_output2 pyaudio python-vlc

# macOS-specific dependencies
pip install pyobjc-framework-Cocoa pyaudio

# Run the application
python -m acb_link
```

---

## Post-Installation Setup

### First Launch

1. **Settings**: Press `Ctrl+,` to open Settings
2. **Theme**: Choose your preferred theme (Appearance tab)
3. **Font Size**: Adjust if needed (8-32pt)
4. **Default Tab**: Set your preferred startup tab
5. **System Tray**: Configure tray behavior

### Optional: Wake Word Support

ACB Link supports hands-free activation with a customizable wake word (e.g., "Hey ACB Link"). This feature requires additional AI/ML components (~5GB download) that are **not included** in the standard installer to keep the download size manageable.

**Default behavior without wake word support:**
- Voice control still works fully via keyboard shortcut (`Ctrl+Shift+V`)
- Say commands directly after activating voice control
- All voice commands function normally

**To enable wake word detection:**

1. Open a command prompt or terminal
2. Run the following command:
   ```bash
   pip install openwakeword torch torchaudio
   ```
3. Restart ACB Link Desktop
4. The app will automatically detect and enable wake word support
5. Configure your preferred wake word in Settings > Voice Control

**Note:** Wake word support requires approximately 5GB of disk space and may take several minutes to download. It includes PyTorch and OpenWakeWord libraries for local, privacy-respecting wake word detection.
### Administrator Setup (Optional)

If you are an ACB administrator who needs to manage application configuration:

1. **Get GitHub Access**: Ensure you have a GitHub account with appropriate repository permissions:
   - Organization owner → Super Admin access
   - Repository admin → Config Admin access
   - Repository write → Affiliate Admin access

2. **Create Personal Access Token**:
   - Go to GitHub Settings > Developer Settings > Personal Access Tokens
   - Generate a new token with `read:org` scope
   - Copy the token securely

3. **Login to Admin Features**:
   - Access Tools > Advanced Settings or Tools > Affiliate Corrections
   - Enter your GitHub username and PAT
   - Your role is automatically determined from repository permissions

**Note**: Regular users do not need admin setup. Admin features are only for ACB staff managing configuration or affiliate data.
### Screen Reader Configuration

**NVDA/JAWS (Windows):**
- ACB Link works automatically with NVDA and JAWS
- All controls are properly labeled
- Status changes are announced

**VoiceOver (macOS):**
- ACB Link integrates deeply with VoiceOver
- Enable VoiceOver: `Command+F5`
- All controls accessible via VoiceOver navigation

### Firewall Configuration

ACB Link uses a local web server on port 8765. If prompted:
- **Windows Firewall**: Allow access for "ACB Link Desktop"
- Only local connections are needed (no internet server)

---

## Updating

### Automatic Updates

1. ACB Link checks for updates on startup
2. If an update is available, you'll be notified
3. Click "Download & Install" to update
4. The app will restart after installation

### Manual Update Check

1. Go to **Help > Check for Updates**
2. Follow the prompts if an update is available

### Manual Update

1. Download the new version from GitHub Releases
2. Run the installer (it will upgrade in place)
3. Your settings and data are preserved

---

## Uninstalling

### Windows

**Via Control Panel:**
1. Open **Settings > Apps > Apps & Features**
2. Find "ACB Link Desktop"
3. Click "Uninstall"

**Via Start Menu:**
1. Open Start Menu
2. Find "ACB Link Desktop"
3. Right-click > "Uninstall"

**User data** is preserved in `%USERPROFILE%\.acb_link`. Delete this folder to remove all data.

### macOS

1. Open Finder
2. Go to Applications
3. Drag "ACB Link Desktop" to Trash
4. Empty Trash

**User data** is preserved in `~/.acb_link`. Delete this folder to remove all data.

---

## Troubleshooting Installation

### Windows: "Windows protected your PC"

1. Click "More info"
2. Click "Run anyway"
3. This is normal for unsigned applications

### Windows: Missing DLLs

Install the Visual C++ Redistributable:
- Download from [Microsoft](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)
- Install and restart

### macOS: "App is damaged and can't be opened"

Run in Terminal:
```bash
xattr -cr /Applications/ACB\ Link\ Desktop.app
```

### macOS: VoiceOver not announcing

1. Check System Preferences > Security & Privacy > Accessibility
2. Ensure ACB Link Desktop has accessibility permissions

### General: Application won't start

1. Check the log file:
   - Windows: `%USERPROFILE%\.acb_link\logs\acb_link.log`
   - macOS: `~/.acb_link/logs/acb_link.log`
2. Report the error to support

---

## Getting Help

- **Email**: bits@acb.org
- **GitHub Issues**: [Report a bug](https://github.com/acbnational/acb_link_desktop/issues)
- **Phone**: 1-800-424-8666

---

*Installation Guide Version 1.0*
*Last Updated: January 2026*
