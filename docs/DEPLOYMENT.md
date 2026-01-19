# ACB Link Desktop - Deployment Guide

**Version:** 1.0.0  
**Last Updated:** January 2026  
**Developed by:** Blind Information Technology Solutions (BITS)

This guide covers building, packaging, and deploying ACB Link Desktop for distribution.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Build Process](#build-process)
3. [Windows Deployment](#windows-deployment)
4. [macOS Deployment](#macos-deployment)
5. [GitHub Releases](#github-releases)
6. [Version Management](#version-management)
7. [Update Infrastructure](#update-infrastructure)
8. [Configuration Reference](#configuration-reference)
9. [Administrator Management](#administrator-management)
10. [Quality Assurance](#quality-assurance)
11. [Distribution Checklist](#distribution-checklist)

---

## Prerequisites

### Development Environment

**All Platforms:**
- Python 3.9 or higher
- Git
- Access to ACB GitHub organization

**Windows:**
- Visual Studio Build Tools 2019 or higher
- NSIS 3.0 or higher (for installer)
- PyInstaller
- Code signing certificate (optional but recommended)

**macOS:**
- Xcode Command Line Tools
- create-dmg (install via Homebrew)
- PyInstaller or py2app
- Apple Developer certificate (optional but recommended)

### Install Build Dependencies

```bash
# Clone repository
git clone https://github.com/acbnational/acb_link_desktop.git
cd acb_link_desktop

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Windows-specific
pip install accessible_output2

# macOS-specific  
pip install pyobjc-framework-Cocoa
```

---

## Build Process

### Version Update

Before building, update the version number in these files:

1. **acb_link/__init__.py**:
   ```python
   __version__ = "1.0.0"
   ```

2. **pyproject.toml**:
   ```toml
   version = "1.0.0"
   ```

3. **installer/version_info.txt** (Windows):
   ```
   filevers=(1, 0, 0, 0),
   prodvers=(1, 0, 0, 0),
   ```

4. **installer/acb_link.nsi** (Windows):
   ```nsi
   !define VERSION "1.0.0"
   ```

### Build Commands

**Windows:**
```powershell
# Run build script
.\scripts\build_windows.ps1
```

**macOS:**
```bash
# Make executable
chmod +x scripts/build_macos.sh

# Run build script
./scripts/build_macos.sh
```

---

## Windows Deployment

### Build Process

The Windows build script performs these steps:

1. **PyInstaller compilation**: Creates standalone executable
2. **Resource embedding**: Adds version info and icon
3. **Dependency bundling**: Includes all Python packages
4. **Data file inclusion**: Bundles offline data and documentation
5. **NSIS installer creation**: Builds professional installer
6. **Portable ZIP**: Creates portable version

### Build Output

After successful build:

```
dist/
├── ACBLink/
│   ├── ACBLink.exe          # Main executable
│   ├── data/                # Bundled data
│   ├── docs/                # Documentation
│   └── [dependencies]       # Python libraries
├── ACBLink-1.0.0-Setup.exe  # Installer
├── ACBLink-1.0.0-Portable.zip
└── checksums.txt            # SHA256 hashes
```

### NSIS Installer Features

The installer provides:

- Modern UI wizard
- License agreement display
- Installation directory selection
- Start Menu shortcuts
- Desktop shortcut (optional)
- Registry entries for Add/Remove Programs
- Uninstaller
- 64-bit Windows verification

### Code Signing (Recommended)

Sign the executable and installer for trust:

```powershell
# Sign executable
signtool sign /n "Your Certificate Name" /t http://timestamp.digicert.com dist\ACBLink\ACBLink.exe

# Sign installer
signtool sign /n "Your Certificate Name" /t http://timestamp.digicert.com dist\ACBLink-1.0.0-Setup.exe
```

---

## macOS Deployment

### Build Process

The macOS build script performs these steps:

1. **py2app or PyInstaller**: Creates app bundle
2. **Info.plist generation**: Sets app metadata
3. **Icon embedding**: Adds app icon
4. **Framework bundling**: Includes dependencies
5. **DMG creation**: Creates distributable disk image

### Build Output

After successful build:

```
dist/
├── ACB Link Desktop.app/    # Application bundle
├── ACBLink-1.0.0-macOS.dmg  # Disk image
└── checksums.txt            # SHA256 hashes
```

### App Bundle Structure

```
ACB Link Desktop.app/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   │   └── ACBLink         # Main executable
│   ├── Resources/
│   │   ├── icon.icns
│   │   ├── data/
│   │   └── docs/
│   └── Frameworks/
│       └── [dependencies]
```

### Code Signing and Notarization

For distribution outside the Mac App Store:

```bash
# Sign the app
codesign --deep --force --options runtime \
  --sign "Developer ID Application: Your Name" \
  "dist/ACB Link Desktop.app"

# Create signed DMG
codesign --sign "Developer ID Application: Your Name" \
  dist/ACBLink-1.0.0-macOS.dmg

# Notarize with Apple
xcrun notarytool submit dist/ACBLink-1.0.0-macOS.dmg \
  --apple-id your@email.com \
  --team-id TEAMID \
  --password app-specific-password \
  --wait

# Staple notarization ticket
xcrun stapler staple dist/ACBLink-1.0.0-macOS.dmg
```

---

## GitHub Releases

### Creating a Release

1. **Commit version changes**:
   ```bash
   git add -A
   git commit -m "Release v1.0.0"
   ```

2. **Create and push tag**:
   ```bash
   git tag v1.0.0
   git push origin main --tags
   ```

3. **Build artifacts** on each platform

4. **Create GitHub Release**:
   - Go to Releases, then Draft a new release
   - Select tag v1.0.0
   - Set release title: "ACB Link Desktop v1.0.0"
   - Write release notes
   - Upload build artifacts
   - Publish release

### Release Notes Template

```markdown
## ACB Link Desktop v1.0.0

### Downloads

**Windows:**
- `ACBLink-1.0.0-Setup.exe` - Installer (recommended)
- `ACBLink-1.0.0-Portable.zip` - Portable version

**macOS:**
- `ACBLink-1.0.0-macOS.dmg` - macOS installer

### What's New

- Feature 1 description
- Feature 2 description

### Bug Fixes

- Fix 1 description
- Fix 2 description

### Checksums (SHA256)

See `checksums.txt` for verification hashes.

### Accessibility

Full support for:
- NVDA, JAWS, Narrator (Windows)
- VoiceOver (macOS)
```

### GitHub Actions Automation

The repository includes GitHub Actions workflows that:

1. **On tag push**: Automatically build for Windows and macOS
2. **Create draft release**: With all artifacts attached
3. **Generate checksums**: For security verification

See `.github/workflows/build.yml` for details.

---

## Version Management

### Semantic Versioning

ACB Link Desktop uses semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes or major features
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes and small improvements

### Version Channels

- **Stable**: Production releases (v1.0.0)
- **Beta**: Pre-release testing (v1.1.0-beta.1)
- **Alpha**: Early development (v1.1.0-alpha.1)

### Version Files

Keep these files synchronized:

| File | Location | Format |
|------|----------|--------|
| __init__.py | acb_link/ | `__version__ = "1.0.0"` |
| pyproject.toml | root | `version = "1.0.0"` |
| version_info.txt | installer/ | `filevers=(1, 0, 0, 0)` |
| acb_link.nsi | installer/ | `!define VERSION "1.0.0"` |

---

## Update Infrastructure

### GitHub-Based Updates

ACB Link Desktop uses GitHub Releases for free, reliable updates:

1. **Update check**: Application queries GitHub API
2. **Version comparison**: Compares current vs latest release
3. **Download**: Fetches installer from release assets
4. **Installation**: Launches installer, app closes
5. **Restart**: User relaunches updated application

### API Endpoint

```
GET https://api.github.com/repos/acbnational/acb_link_desktop/releases/latest
```

### Asset Naming Convention

Use consistent names for automatic detection:

- Windows installer: `ACBLink-{version}-Setup.exe`
- Windows portable: `ACBLink-{version}-Portable.zip`
- macOS DMG: `ACBLink-{version}-macOS.dmg`
- Checksums: `checksums.txt`

---

## Configuration Reference

ACB Link Desktop uses a centralized configuration system defined in `acb_link/config.py`. All settings are stored in JSON files that can be modified for custom deployments.

### Configuration File Locations

| Platform | Config Path |
|----------|-------------|
| Windows | `%APPDATA%\ACB Link\config.json` |
| macOS | `~/Library/Application Support/ACB Link/config.json` |
| Linux | `~/.acb_link/config.json` |

### Data Source Configuration

The application fetches live data from ACB servers. These URLs can be customized for testing or alternative deployments.

```json
{
  "live_data": {
    "base_url": "https://link.acb.org",
    "streams": {
      "name": "streams",
      "description": "ACB Media streaming stations",
      "live_url": "https://link.acb.org/streams.xml",
      "offline_path": "data/s3/streams.xml",
      "cache_duration_hours": 168,
      "enabled": true
    },
    "podcasts": {
      "name": "podcasts",
      "description": "ACB podcast feeds (OPML)",
      "live_url": "https://link.acb.org/link.opml",
      "offline_path": "data/s3/link.opml",
      "cache_duration_hours": 24,
      "enabled": true
    },
    "state_affiliates": {
      "name": "state_affiliates",
      "description": "State affiliate organizations",
      "live_url": "https://link.acb.org/states.xml",
      "offline_path": "data/s3/states.xml",
      "cache_duration_hours": 168,
      "enabled": true
    },
    "special_interest_groups": {
      "name": "special_interest_groups",
      "description": "Special interest group affiliates",
      "live_url": "https://link.acb.org/sigs.xml",
      "offline_path": "data/s3/sigs.xml",
      "cache_duration_hours": 168,
      "enabled": true
    },
    "publications": {
      "name": "publications",
      "description": "ACB publications and resources",
      "live_url": "https://link.acb.org/publications.xml",
      "offline_path": "data/s3/publications.xml",
      "cache_duration_hours": 168,
      "enabled": true
    },
    "categories": {
      "name": "categories",
      "description": "Content categories",
      "live_url": "https://link.acb.org/categories.xml",
      "offline_path": "data/s3/categories.xml",
      "cache_duration_hours": 168,
      "enabled": true
    },
    "acb_sites": {
      "name": "acb_sites",
      "description": "ACB website directory",
      "live_url": "https://link.acb.org/acbsites.xml",
      "offline_path": "data/s3/acbsites.xml",
      "cache_duration_hours": 168,
      "enabled": true
    }
  }
}
```

#### Data Source Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `name` | string | - | Internal identifier for the data source |
| `description` | string | - | Human-readable description |
| `live_url` | string | - | URL to fetch live data from |
| `offline_path` | string | - | Path to bundled offline data (relative to app) |
| `cache_duration_hours` | int | 24 | How long to cache data before re-fetching |
| `last_sync` | string | null | ISO timestamp of last successful sync |
| `enabled` | bool | true | Whether this data source is active |

### Update Configuration

Settings for the GitHub-based automatic update system.

```json
{
  "updates": {
    "enabled": true,
    "check_on_startup": true,
    "check_interval_hours": 24,
    "github_repo": "acbnational/acb_link_desktop",
    "github_api_url": "https://api.github.com/repos/acbnational/acb_link_desktop/releases/latest",
    "download_url_template": "https://github.com/acbnational/acb_link_desktop/releases/download/v{version}/{filename}",
    "last_check": null,
    "skipped_version": null
  }
}
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | bool | true | Enable/disable automatic updates |
| `check_on_startup` | bool | true | Check for updates when app starts |
| `check_interval_hours` | int | 24 | Hours between automatic update checks |
| `github_repo` | string | "acbnational/acb_link_desktop" | GitHub repository for updates |
| `github_api_url` | string | (see above) | Full URL to GitHub releases API |
| `download_url_template` | string | (see above) | Template for download URLs |
| `last_check` | string | null | ISO timestamp of last update check |
| `skipped_version` | string | null | Version user chose to skip |

### Network Configuration

Settings for network requests and connectivity.

```json
{
  "network": {
    "timeout_seconds": 30,
    "retry_count": 3,
    "retry_delay_seconds": 5,
    "user_agent": "ACBLinkDesktop/1.0",
    "proxy_enabled": false,
    "proxy_url": null
  }
}
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `timeout_seconds` | int | 30 | Network request timeout |
| `retry_count` | int | 3 | Number of retry attempts on failure |
| `retry_delay_seconds` | int | 5 | Delay between retries |
| `user_agent` | string | "ACBLinkDesktop/1.0" | HTTP User-Agent header |
| `proxy_enabled` | bool | false | Enable proxy for network requests |
| `proxy_url` | string | null | Proxy server URL (e.g., "http://proxy:8080") |

### Path Configuration

File and directory paths (auto-configured per platform, but can be overridden).

```json
{
  "paths": {
    "app_data_dir": "%APPDATA%\\ACB Link",
    "cache_dir": "%APPDATA%\\ACB Link\\cache",
    "logs_dir": "%APPDATA%\\ACB Link\\logs",
    "downloads_dir": "C:\\Users\\{user}\\Documents\\ACB Link\\Podcasts",
    "recordings_dir": "C:\\Users\\{user}\\Documents\\ACB Link\\Recordings",
    "settings_file": "%APPDATA%\\ACB Link\\settings.json",
    "favorites_file": "%APPDATA%\\ACB Link\\favorites.json",
    "playlists_file": "%APPDATA%\\ACB Link\\playlists.json",
    "history_file": "%APPDATA%\\ACB Link\\history.json"
  }
}
```

| Setting | Type | Description |
|---------|------|-------------|
| `app_data_dir` | string | Main application data directory |
| `cache_dir` | string | Cache for downloaded content |
| `logs_dir` | string | Application log files |
| `downloads_dir` | string | Downloaded podcast episodes |
| `recordings_dir` | string | Stream recordings |
| `settings_file` | string | User settings JSON file |
| `favorites_file` | string | Saved favorites |
| `playlists_file` | string | User playlists |
| `history_file` | string | Playback history |

### Default Values Configuration

Application default values that users can override in settings.

```json
{
  "defaults": {
    "default_volume": 80,
    "default_playback_speed": 1.0,
    "default_skip_forward": 30,
    "default_skip_backward": 10,
    "default_tab": "home",
    "default_theme": "system",
    "default_font_size": 12,
    "default_font_family": "Segoe UI",
    "start_minimized": false,
    "minimize_to_tray": true,
    "close_to_tray": false,
    "remember_window_position": true,
    "default_recording_format": "mp3",
    "default_recording_bitrate": 128,
    "auto_sync_on_startup": true,
    "sync_interval_hours": 24
  }
}
```

#### Audio Settings

| Setting | Type | Default | Range | Description |
|---------|------|---------|-------|-------------|
| `default_volume` | int | 80 | 0-100 | Initial volume level (%) |
| `default_playback_speed` | float | 1.0 | 0.5-3.0 | Playback speed multiplier |
| `default_skip_forward` | int | 30 | 1-300 | Forward skip in seconds |
| `default_skip_backward` | int | 10 | 1-300 | Backward skip in seconds |

#### UI Settings

| Setting | Type | Default | Options | Description |
|---------|------|---------|---------|-------------|
| `default_tab` | string | "home" | home, streams, podcasts, favorites | Initial tab on startup |
| `default_theme` | string | "system" | system, light, dark, high_contrast | Color theme |
| `default_font_size` | int | 12 | 8-24 | Base font size in points |
| `default_font_family` | string | "Segoe UI" | Any system font | UI font family |

#### Behavior Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `start_minimized` | bool | false | Start app minimized to tray |
| `minimize_to_tray` | bool | true | Minimize to system tray instead of taskbar |
| `close_to_tray` | bool | false | Close to tray instead of exiting |
| `remember_window_position` | bool | true | Save and restore window position |

#### Recording Settings

| Setting | Type | Default | Options | Description |
|---------|------|---------|---------|-------------|
| `default_recording_format` | string | "mp3" | mp3, wav, ogg, flac | Recording output format |
| `default_recording_bitrate` | int | 128 | 64, 128, 192, 256, 320 | MP3 bitrate (kbps) |

#### Sync Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `auto_sync_on_startup` | bool | true | Sync data when app starts |
| `sync_interval_hours` | int | 24 | Hours between automatic syncs |

### Application Metadata

```json
{
  "version": "1.0.0",
  "first_run": true,
  "install_date": "2025-01-19T10:30:00",
  "last_run": "2025-01-19T15:45:00"
}
```

| Setting | Type | Description |
|---------|------|-------------|
| `version` | string | Application version (read-only) |
| `first_run` | bool | True until first-run wizard completes |
| `install_date` | string | ISO timestamp of first installation |
| `last_run` | string | ISO timestamp of last application launch |

### Server-Side Data Hosting

If hosting your own ACB Link data server, ensure these endpoints are available:

| Endpoint | Format | Description |
|----------|--------|-------------|
| `/streams.xml` | XML | Streaming station definitions |
| `/link.opml` | OPML | Podcast feed directory |
| `/states.xml` | XML | State affiliate organizations |
| `/sigs.xml` | XML | Special interest groups |
| `/publications.xml` | XML | Publications directory |
| `/categories.xml` | XML | Content categories |
| `/acbsites.xml` | XML | ACB website directory |

#### Server Requirements

- HTTPS required for security
- CORS headers if serving to web clients
- Gzip compression recommended
- Cache-Control headers for CDN caching

#### Custom Server Deployment

To point ACB Link to a custom server:

1. **Edit config.json**:
   ```json
   {
     "live_data": {
       "base_url": "https://your-server.example.com",
       "streams": {
         "live_url": "https://your-server.example.com/streams.xml"
       }
     }
   }
   ```

2. **Or set environment variable** (for testing):
   ```bash
   ACB_LINK_BASE_URL=https://your-server.example.com
   ```

3. **Distribute custom config** with installer for organization-wide deployment

### Enterprise Deployment

For large-scale deployment with managed settings:

1. **Create master config.json** with organization defaults
2. **Bundle with installer** to override defaults
3. **Use Group Policy** (Windows) to deploy config file
4. **Lock settings** by removing write permissions

---

## Administrator Management

ACB Link Desktop includes a role-based administration system for managing organization-wide configuration and affiliate data. **This system uses GitHub for free, zero-cost authentication** - no custom server required!

### Why GitHub-Based Authentication?

Using GitHub for admin authentication provides significant advantages:

- **Completely free**: No server costs, hosting, or maintenance
- **Battle-tested security**: GitHub's authentication is trusted by millions
- **No passwords to manage**: Uses GitHub Personal Access Tokens
- **Instant provisioning**: Add admins by adding GitHub collaborators
- **Instant revocation**: Remove access by removing collaborators
- **Built-in audit trail**: GitHub tracks all permission changes
- **MFA supported**: If user has GitHub MFA enabled, it's automatically used

### Admin Roles

The system maps GitHub repository permissions to admin roles:

| GitHub Permission | Admin Role | Level | Capabilities |
|-------------------|------------|-------|--------------|
| None or Read | `USER` | 0 | Standard user - no admin access |
| Write/Triage | `AFFILIATE_ADMIN` | 1 | Review and approve affiliate corrections |
| Maintain/Admin | `CONFIG_ADMIN` | 2 | Modify data sources, network settings |
| Organization Owner | `SUPER_ADMIN` | 3 | All capabilities plus admin management |

Each higher role inherits all capabilities of lower roles.

### How Admins Are Defined

Administrators are defined by their **GitHub permissions on the config repository**. To grant someone admin access:

1. Add them as a collaborator to the `acbnational/acb_link_config` repository
2. Set their permission level:
   - **Write access** → Affiliate Admin
   - **Admin access** → Config Admin
   - **Organization owner** → Super Admin

That's it! No server configuration, no password management, no database.

### Setting Up the Config Repository

#### 1. Create the Config Repository

Create a GitHub repository to store organization configuration:

```bash
# Repository: acbnational/acb_link_config (or your organization)
# Can be private for internal configs or public for transparency
```

#### 2. Add the Config File

Create `org_config.json` in the repository root:

```json
{
  "version": "1.0",
  "organization": {
    "name": "American Council of the Blind",
    "short_name": "ACB",
    "support_email": "support@acb.org"
  },
  "settings": {
    "data_sources": {},
    "network": {},
    "features": {}
  },
  "updated_at": "2025-01-15T10:00:00Z",
  "updated_by": "initial-setup"
}
```

#### 3. Add Admin Collaborators

Go to repository Settings → Collaborators and teams:

| User | Permission | Resulting Role |
|------|------------|----------------|
| `ceo-github` | Admin | CONFIG_ADMIN |
| `it-staff` | Admin | CONFIG_ADMIN |
| `affiliate-rep` | Write | AFFILIATE_ADMIN |
| `volunteer` | Write | AFFILIATE_ADMIN |

Organization owners automatically have SUPER_ADMIN access.

### Authentication Flow

When an admin action is required:

```
1. User attempts admin action (e.g., Advanced Settings)
2. Application shows GitHub login dialog
3. User enters their GitHub Personal Access Token (PAT)
4. Application calls GitHub API to:
   a. Verify token is valid (GET /user)
   b. Check user's repo permission (GET /repos/.../collaborators/.../permission)
   c. Check if org owner (GET /orgs/.../memberships/...)
5. Role assigned based on highest permission level
6. Token stored in memory (NOT on disk) for session
7. Subsequent admin operations use the same token
8. Token cleared when app exits
```

### Creating a GitHub Personal Access Token

Users need to create a PAT to authenticate:

1. Go to https://github.com/settings/tokens/new
2. Set description: "ACB Link Desktop Admin"
3. Select scopes:
   - `read:org` (required - to check organization membership)
4. Click "Generate token"
5. Copy the token (it won't be shown again)

Or use this direct link:
```
https://github.com/settings/tokens/new?scopes=read:org&description=ACB%20Link%20Desktop%20Admin
```

**Note**: The token only needs `read:org` scope. It cannot make changes to repositories - it's only used to verify the user's identity and permissions.

### Configuration Storage

Organization config is stored directly in the GitHub repository:

```
acbnational/acb_link_config/
├── org_config.json      # Main organization configuration
├── README.md            # Documentation for admins
└── .github/
    └── CODEOWNERS       # Optional: require reviews for config changes
```

#### Fetching Config

The app fetches config from GitHub:

```python
# Public repo - no auth needed
GET https://api.github.com/repos/acbnational/acb_link_config/contents/org_config.json

# Private repo - needs token
GET https://api.github.com/repos/acbnational/acb_link_config/contents/org_config.json
Authorization: Bearer ghp_xxxxx
```

#### Updating Config

Config Admins can push changes through the GitHub API:

```python
PUT https://api.github.com/repos/acbnational/acb_link_config/contents/org_config.json
Authorization: Bearer ghp_xxxxx
Content-Type: application/json

{
  "message": "Update network timeout settings",
  "content": "base64_encoded_content",
  "sha": "current_file_sha"
}
```

### Managing Admins

#### Adding a New Admin

1. Go to `https://github.com/acbnational/acb_link_config/settings/access`
2. Click "Add people" or "Add teams"
3. Enter their GitHub username
4. Select permission level:
   - **Write** for Affiliate Admin
   - **Admin** for Config Admin
5. Click "Add"

The user can now authenticate with their GitHub PAT.

#### Removing an Admin

1. Go to repository settings → Collaborators
2. Find the user
3. Click "Remove"

Their access is revoked immediately - their PAT will no longer grant admin permissions.

#### Changing Admin Roles

1. Go to repository settings → Collaborators
2. Find the user
3. Change their permission level
4. The change takes effect on their next authentication

### GitHub Organization Setup (Optional)

For larger organizations, use GitHub Teams:

```
acbnational (organization)
├── acb_link_config (repository)
│   └── Teams:
│       ├── acb-it (Admin access) → CONFIG_ADMIN
│       ├── affiliate-managers (Write access) → AFFILIATE_ADMIN
│       └── volunteers (Read access) → USER
```

Organization owners automatically have SUPER_ADMIN access to all repositories.

### Security Features

#### Built-in GitHub Security

- **Two-factor authentication**: If user has MFA on GitHub, it protects their PAT
- **Token expiration**: Users can set PAT expiration (recommended: 90 days)
- **IP restrictions**: GitHub Enterprise allows IP allowlists
- **Audit logging**: GitHub logs all API access
- **Rate limiting**: Protects against abuse

#### Application Security

- **No credential storage**: PATs never saved to disk
- **Memory-only sessions**: Token cleared on app exit
- **Minimum scopes**: Only `read:org` scope required
- **Permission verification**: Every admin action re-checks permissions

### Audit Trail

GitHub provides a complete audit trail:

1. **Repository access log**: Who accessed the config repo
2. **Collaborator changes**: When admins were added/removed
3. **Commit history**: All config changes with author and timestamp
4. **Branch protection**: Optionally require reviews for config changes

To view audit logs:
- Repository: Settings → Security → Audit log
- Organization: Settings → Audit log

### Fallback for Offline Use

If GitHub is unreachable:

1. Config Admin can export current config to local file
2. App uses cached config (read-only)
3. Admin changes queued until connectivity restored
4. Clear indication shown that app is in offline mode

### Migration from Server-Based Auth

If you previously used a custom server:

1. Create the GitHub config repository
2. Export existing config to `org_config.json`
3. Add collaborators matching previous admin list
4. Update app config to use GitHub:

```json
{
  "admin": {
    "provider": "github",
    "config_repo": "acbnational/acb_link_config",
    "config_path": "org_config.json"
  }
}
```

The `admin_config.py` module is still available for legacy/self-hosted deployments.

### Permissions Reference

#### AFFILIATE_ADMIN Permissions

| Permission | Description |
|------------|-------------|
| `review_corrections` | View pending affiliate corrections |
| `approve_corrections` | Approve corrections for application |
| `reject_corrections` | Reject corrections with notes |
| `apply_corrections` | Apply approved corrections to XML files |

#### CONFIG_ADMIN Permissions

Includes all AFFILIATE_ADMIN permissions, plus:

| Permission | Description |
|------------|-------------|
| `modify_data_sources` | Change data source URLs |
| `modify_network_settings` | Change timeout, retry, proxy settings |
| `modify_defaults` | Change organization default values |
| `modify_update_settings` | Change update server configuration |
| `view_audit_log` | View admin action history |

#### SUPER_ADMIN Permissions

Includes all permissions, plus:

| Permission | Description |
|------------|-------------|
| `manage_admins` | Create, modify, delete admin accounts |
| `modify_signing_keys` | Rotate configuration signing keys |
| `export_audit_log` | Export full audit history |
| `emergency_rollback` | Rollback to previous config versions |

---

## Quality Assurance

### Pre-Release Testing

Before each release:

1. **Functionality testing**: All features work correctly
2. **Accessibility testing**: Screen readers work properly
3. **Platform testing**: Test on Windows 10, 11, macOS
4. **Upgrade testing**: Test upgrade from previous version
5. **Clean install testing**: Test fresh installation

### Accessibility Testing Checklist

- [ ] NVDA reads all controls correctly
- [ ] JAWS reads all controls correctly
- [ ] Narrator reads all controls correctly
- [ ] VoiceOver reads all controls correctly
- [ ] Keyboard navigation works throughout
- [ ] Focus order is logical
- [ ] Status changes are announced
- [ ] High contrast themes work

### Automated Testing

Run test suite before release:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=acb_link --cov-report=html

# Run accessibility tests
pytest tests/test_accessibility.py
```

---

## Distribution Checklist

### Pre-Release

- [ ] Version numbers updated in all files
- [ ] Changelog updated
- [ ] Documentation updated
- [ ] All tests passing
- [ ] Accessibility verified

### Build

- [ ] Windows build successful
- [ ] Windows installer tested
- [ ] macOS build successful
- [ ] macOS DMG tested
- [ ] Checksums generated

### Release

- [ ] Git tag created
- [ ] GitHub Release drafted
- [ ] Release notes written
- [ ] Artifacts uploaded
- [ ] Release published

### Post-Release

- [ ] Update website download links
- [ ] Announce on ACB mailing lists
- [ ] Monitor for user feedback
- [ ] Check auto-update works

---

## Troubleshooting

### Windows Build Issues

**PyInstaller fails:**
```powershell
# Clean build
Remove-Item -Recurse -Force build, dist
pyinstaller --clean acb_link.spec
```

**Missing DLLs:**
- Ensure Visual C++ Redistributable is installed
- Check hidden imports in spec file

### macOS Build Issues

**Code signing fails:**
- Verify certificate is in Keychain
- Check certificate name matches exactly

**Notarization fails:**
- Enable hardened runtime
- Check for unsigned frameworks

### Update Issues

**Update not detected:**
- Verify release is published (not draft)
- Check asset naming convention
- Test GitHub API endpoint manually

---

*Deployment Guide Version 1.0.0*  
*Last Updated: January 2026*  
*Copyright 2026 American Council of the Blind / BITS*
