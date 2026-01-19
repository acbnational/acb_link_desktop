# ACB Link Desktop - Build Script for Windows
# Creates Windows executable and installer

param(
    [switch]$SkipInstaller,
    [switch]$Debug,
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "ACB Link Desktop - Windows Build Script" -ForegroundColor Cyan
Write-Host "Version: $Version" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check PyInstaller
try {
    $pyinstallerVersion = pyinstaller --version 2>&1
    Write-Host "  PyInstaller: $pyinstallerVersion" -ForegroundColor Green
} catch {
    Write-Host "  PyInstaller not found. Installing..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Check NSIS (for installer)
if (-not $SkipInstaller) {
    $nsisPath = "C:\Program Files (x86)\NSIS\makensis.exe"
    if (Test-Path $nsisPath) {
        Write-Host "  NSIS: Found" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: NSIS not found. Installer will be skipped." -ForegroundColor Yellow
        Write-Host "  Download from: https://nsis.sourceforge.io/" -ForegroundColor Yellow
        $SkipInstaller = $true
    }
}

Write-Host ""

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
Write-Host "  Done" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install pyinstaller
Write-Host "  Done" -ForegroundColor Green
Write-Host ""

# Build with PyInstaller
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
$pyinstallerArgs = @("acb_link.spec")
if ($Debug) {
    $pyinstallerArgs += "--log-level=DEBUG"
}
pyinstaller @pyinstallerArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: PyInstaller build failed" -ForegroundColor Red
    exit 1
}
Write-Host "  Done" -ForegroundColor Green
Write-Host ""

# Verify build
$exePath = "dist\ACBLink\ACBLink.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "  ERROR: Executable not found at $exePath" -ForegroundColor Red
    exit 1
}
$exeSize = (Get-Item $exePath).Length / 1MB
Write-Host "  Executable size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Green
Write-Host ""

# Build installer
if (-not $SkipInstaller) {
    Write-Host "Building NSIS installer..." -ForegroundColor Yellow
    
    # Copy LICENSE to installer directory
    Copy-Item "LICENSE" "installer\LICENSE"
    
    # Run NSIS
    & $nsisPath "installer\acb_link.nsi"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: NSIS build failed" -ForegroundColor Red
        exit 1
    }
    
    $installerPath = "installer\ACBLink-$Version-Setup.exe"
    if (Test-Path $installerPath) {
        $installerSize = (Get-Item $installerPath).Length / 1MB
        Write-Host "  Installer size: $([math]::Round($installerSize, 2)) MB" -ForegroundColor Green
        
        # Move installer to dist
        Move-Item $installerPath "dist\ACBLink-$Version-Setup.exe"
    }
    Write-Host "  Done" -ForegroundColor Green
    Write-Host ""
}

# Create portable ZIP
Write-Host "Creating portable ZIP..." -ForegroundColor Yellow
$zipPath = "dist\ACBLink-$Version-Portable.zip"
Compress-Archive -Path "dist\ACBLink\*" -DestinationPath $zipPath -Force
$zipSize = (Get-Item $zipPath).Length / 1MB
Write-Host "  Portable ZIP size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Green
Write-Host ""

# Generate checksums
Write-Host "Generating checksums..." -ForegroundColor Yellow
$checksumFile = "dist\ACBLink-$Version-SHA256.txt"
$files = Get-ChildItem "dist\*.exe", "dist\*.zip" -ErrorAction SilentlyContinue
$checksums = @()
foreach ($file in $files) {
    $hash = Get-FileHash $file.FullName -Algorithm SHA256
    $checksums += "$($hash.Hash)  $($file.Name)"
    Write-Host "  $($file.Name): $($hash.Hash.Substring(0, 16))..." -ForegroundColor Green
}
$checksums | Out-File $checksumFile -Encoding UTF8
Write-Host ""

# Summary
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Output files in dist/:" -ForegroundColor Yellow
Get-ChildItem "dist\*.exe", "dist\*.zip", "dist\*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  - $($_.Name)" -ForegroundColor Green
}
Write-Host ""
Write-Host "To test: dist\ACBLink\ACBLink.exe" -ForegroundColor Yellow
Write-Host ""
