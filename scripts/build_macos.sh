#!/bin/bash
# ACB Link Desktop - Build Script for macOS
# Creates macOS application bundle and DMG installer

set -e

VERSION="${1:-1.0.0}"
APP_NAME="ACB Link Desktop"
BUNDLE_ID="org.acb.link.desktop"

echo "============================================"
echo "ACB Link Desktop - macOS Build Script"
echo "Version: $VERSION"
echo "============================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  Python: $PYTHON_VERSION"
else
    echo "  ERROR: Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Check PyInstaller
if command -v pyinstaller &> /dev/null; then
    PYINSTALLER_VERSION=$(pyinstaller --version)
    echo "  PyInstaller: $PYINSTALLER_VERSION"
else
    echo "  PyInstaller not found. Installing..."
    pip3 install pyinstaller
fi

# Check create-dmg (optional)
if command -v create-dmg &> /dev/null; then
    echo "  create-dmg: Found"
    HAS_CREATE_DMG=1
else
    echo "  WARNING: create-dmg not found. DMG will be created with hdiutil."
    echo "  For better DMG, install: brew install create-dmg"
    HAS_CREATE_DMG=0
fi

echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist
echo "  Done"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller
echo "  Done"
echo ""

# Create macOS spec file
echo "Creating macOS spec file..."
cat > acb_link_macos.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-
"""ACB Link Desktop - macOS PyInstaller Specification"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['acb_link/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('docs', 'docs'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'wx', 'wx.html2', 'wx.adv', 'wx.media',
        'fastapi', 'uvicorn',
        'speech_recognition', 'pyttsx3',
        'feedparser', 'requests', 'dateutil', 'icalendar',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ACBLink',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='ACBLink',
)

app = BUNDLE(
    coll,
    name='ACB Link Desktop.app',
    icon='data/s3/acb512.png',
    bundle_identifier='org.acb.link.desktop',
    info_plist={
        'CFBundleName': 'ACB Link Desktop',
        'CFBundleDisplayName': 'ACB Link Desktop',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSHumanReadableCopyright': '© 2026 American Council of the Blind',
        'NSHighResolutionCapable': True,
        'NSAppleEventsUsageDescription': 'ACB Link Desktop uses AppleEvents for VoiceOver integration.',
        'NSMicrophoneUsageDescription': 'ACB Link Desktop uses the microphone for voice control.',
        'LSMinimumSystemVersion': '10.14',
        # Accessibility
        'NSAccessibilityUsageDescription': 'ACB Link Desktop provides full VoiceOver support for accessibility.',
    },
)
EOF
echo "  Done"
echo ""

# Build with PyInstaller
echo "Building macOS application bundle..."
pyinstaller acb_link_macos.spec

if [ ! -d "dist/ACB Link Desktop.app" ]; then
    echo "  ERROR: Application bundle not created"
    exit 1
fi

APP_SIZE=$(du -sh "dist/ACB Link Desktop.app" | cut -f1)
echo "  Application size: $APP_SIZE"
echo "  Done"
echo ""

# Sign the application (if certificate available)
echo "Checking for code signing certificate..."
if security find-identity -v -p codesigning | grep -q "Developer ID Application"; then
    echo "  Found signing certificate. Signing application..."
    codesign --deep --force --verify --verbose \
        --sign "Developer ID Application" \
        "dist/ACB Link Desktop.app"
    echo "  Done"
else
    echo "  WARNING: No signing certificate found. Application will be unsigned."
    echo "  Users may need to allow the app in System Preferences > Security."
fi
echo ""

# Create DMG
echo "Creating DMG installer..."
DMG_NAME="ACBLink-$VERSION-macOS.dmg"

if [ "$HAS_CREATE_DMG" -eq 1 ]; then
    # Use create-dmg for a nicer DMG
    create-dmg \
        --volname "ACB Link Desktop" \
        --volicon "data/s3/acb512.png" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "ACB Link Desktop.app" 150 200 \
        --hide-extension "ACB Link Desktop.app" \
        --app-drop-link 450 200 \
        "dist/$DMG_NAME" \
        "dist/ACB Link Desktop.app"
else
    # Use hdiutil (basic DMG)
    hdiutil create -volname "ACB Link Desktop" \
        -srcfolder "dist/ACB Link Desktop.app" \
        -ov -format UDZO \
        "dist/$DMG_NAME"
fi

DMG_SIZE=$(du -sh "dist/$DMG_NAME" | cut -f1)
echo "  DMG size: $DMG_SIZE"
echo "  Done"
echo ""

# Generate checksums
echo "Generating checksums..."
cd dist
shasum -a 256 "$DMG_NAME" > "ACBLink-$VERSION-SHA256.txt"
echo "  Done"
cd ..
echo ""

# Summary
echo "============================================"
echo "Build Complete!"
echo "============================================"
echo ""
echo "Output files in dist/:"
ls -la dist/*.app dist/*.dmg dist/*.txt 2>/dev/null || true
echo ""
echo "To test: open \"dist/ACB Link Desktop.app\""
echo ""

# VoiceOver testing instructions
echo "============================================"
echo "VoiceOver Testing Instructions"
echo "============================================"
echo ""
echo "1. Enable VoiceOver: Command+F5"
echo "2. Open ACB Link Desktop.app"
echo "3. Test navigation with VoiceOver:"
echo "   - VO+Right/Left: Navigate between elements"
echo "   - VO+Space: Activate element"
echo "   - VO+Shift+M: Open menu"
echo "4. Verify all controls are announced properly"
echo ""
