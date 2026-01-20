# ACB Link Desktop - Build Script for Windows
# Creates Windows executable, installer (EXE/MSI), and portable version

param(
    [switch]$SkipInstaller,
    [switch]$SkipMSI,
    [switch]$SkipPortable,
    [switch]$Debug,
    [switch]$Clean,
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "ACB Link Desktop - Windows Build Script" -ForegroundColor Cyan
Write-Host "Version: $Version" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Change to project root
Push-Location $ProjectRoot

try {
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
        pip install pyinstaller pyinstaller-hooks-contrib
    }

    # Check NSIS (for EXE installer)
    $nsisPath = "C:\Program Files (x86)\NSIS\makensis.exe"
    if (-not (Test-Path $nsisPath)) {
        $nsisPath = "C:\Program Files\NSIS\makensis.exe"
    }
    $hasNSIS = Test-Path $nsisPath
    if ($hasNSIS) {
        Write-Host "  NSIS: Found" -ForegroundColor Green
    } else {
        Write-Host "  NSIS: Not found (EXE installer will be skipped)" -ForegroundColor Yellow
        Write-Host "    Download from: https://nsis.sourceforge.io/" -ForegroundColor DarkGray
    }

    # Check WiX Toolset (for MSI installer)
    $wixPath = Get-Command candle.exe -ErrorAction SilentlyContinue
    $hasWiX = $null -ne $wixPath
    if ($hasWiX) {
        Write-Host "  WiX Toolset: Found" -ForegroundColor Green
    } else {
        # Try common install locations
        $wixPaths = @(
            "${env:WIX}bin\candle.exe",
            "C:\Program Files (x86)\WiX Toolset v3.14\bin\candle.exe",
            "C:\Program Files (x86)\WiX Toolset v3.11\bin\candle.exe"
        )
        foreach ($path in $wixPaths) {
            if (Test-Path $path) {
                $hasWiX = $true
                $env:PATH = "$env:PATH;$(Split-Path $path)"
                Write-Host "  WiX Toolset: Found at $path" -ForegroundColor Green
                break
            }
        }
        if (-not $hasWiX) {
            Write-Host "  WiX Toolset: Not found (MSI installer will be skipped)" -ForegroundColor Yellow
            Write-Host "    Install with: dotnet tool install --global wix" -ForegroundColor DarkGray
        }
    }

    Write-Host ""

    # Clean previous builds
    if ($Clean -or -not (Test-Path "dist\ACBLink\ACBLink.exe")) {
        Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
        if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
        if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
        Write-Host "  Done" -ForegroundColor Green
        Write-Host ""

        # Install dependencies (skip if just packaging)
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt --quiet
        pip install pyinstaller pyinstaller-hooks-contrib --quiet
        Write-Host "  Done" -ForegroundColor Green
        Write-Host ""

        # Build with PyInstaller
        Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
        Write-Host "  (This may take several minutes)" -ForegroundColor DarkGray

        $pyinstallerArgs = @("--clean", "--noconfirm", "acb_link.spec")
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
    } else {
        Write-Host "Using existing build (use -Clean to rebuild)" -ForegroundColor Yellow
        Write-Host ""
    }

    # Verify build
    $exePath = "dist\ACBLink\ACBLink.exe"
    if (-not (Test-Path $exePath)) {
        Write-Host "  ERROR: Executable not found at $exePath" -ForegroundColor Red
        exit 1
    }

    # Calculate build size
    $buildSize = (Get-ChildItem "dist\ACBLink" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "Build Statistics:" -ForegroundColor Yellow
    Write-Host "  Total size: $([math]::Round($buildSize, 1)) MB" -ForegroundColor Green

    # List largest components
    $largestFolders = Get-ChildItem "dist\ACBLink\_internal" -Directory -ErrorAction SilentlyContinue |
        ForEach-Object {
            $size = (Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
            [PSCustomObject]@{Name=$_.Name; SizeMB=[math]::Round($size,1)}
        } | Sort-Object SizeMB -Descending | Select-Object -First 5

    if ($largestFolders) {
        Write-Host "  Largest components:" -ForegroundColor DarkGray
        foreach ($folder in $largestFolders) {
            Write-Host "    - $($folder.Name): $($folder.SizeMB) MB" -ForegroundColor DarkGray
        }
    }
    Write-Host ""

    # Build NSIS EXE installer
    if (-not $SkipInstaller -and $hasNSIS) {
        Write-Host "Building NSIS installer (EXE)..." -ForegroundColor Yellow

        # Copy LICENSE to installer directory
        Copy-Item "LICENSE" "installer\LICENSE" -Force

        # Run NSIS
        Push-Location "installer"
        try {
            & $nsisPath "acb_link.nsi"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  WARNING: NSIS build failed" -ForegroundColor Yellow
            } else {
                $installerPath = "ACBLink-$Version-Setup.exe"
                if (Test-Path $installerPath) {
                    $installerSize = (Get-Item $installerPath).Length / 1MB
                    Move-Item $installerPath "..\dist\ACBLink-$Version-Setup.exe" -Force
                    Write-Host "  EXE Installer: $([math]::Round($installerSize, 1)) MB" -ForegroundColor Green
                }
            }
        } finally {
            Pop-Location
        }
        Write-Host ""
    }

    # Build MSI installer
    if (-not $SkipMSI -and $hasWiX) {
        Write-Host "Building MSI installer..." -ForegroundColor Yellow

        # Create WiX source file if it doesn't exist
        $wxsPath = "installer\acb_link.wxs"
        if (-not (Test-Path $wxsPath)) {
            Write-Host "  Generating WiX source file..." -ForegroundColor DarkGray
            & heat.exe dir "dist\ACBLink" -cg ProductComponents -dr INSTALLDIR -gg -scom -sreg -sfrag -srd -var var.SourceDir -out "installer\files.wxs"
        }

        if (Test-Path $wxsPath) {
            Push-Location "installer"
            try {
                # Compile
                & candle.exe -dSourceDir="..\dist\ACBLink" -dVersion="$Version" "acb_link.wxs" "files.wxs" -out ".\obj\"
                if ($LASTEXITCODE -eq 0) {
                    # Link
                    & light.exe -ext WixUIExtension "obj\acb_link.wixobj" "obj\files.wixobj" -out "..\dist\ACBLink-$Version.msi"
                    if ($LASTEXITCODE -eq 0) {
                        $msiSize = (Get-Item "..\dist\ACBLink-$Version.msi").Length / 1MB
                        Write-Host "  MSI Installer: $([math]::Round($msiSize, 1)) MB" -ForegroundColor Green
                    }
                }
            } catch {
                Write-Host "  WARNING: MSI build failed: $_" -ForegroundColor Yellow
            } finally {
                Pop-Location
            }
        } else {
            Write-Host "  Skipped: WiX source file not found" -ForegroundColor Yellow
            Write-Host "  Create installer\acb_link.wxs to enable MSI builds" -ForegroundColor DarkGray
        }
        Write-Host ""
    }

    # Create portable ZIP
    if (-not $SkipPortable) {
        Write-Host "Creating portable ZIP..." -ForegroundColor Yellow
        $zipPath = "dist\ACBLink-$Version-Portable.zip"
        if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
        Compress-Archive -Path "dist\ACBLink\*" -DestinationPath $zipPath -CompressionLevel Optimal
        $zipSize = (Get-Item $zipPath).Length / 1MB
        Write-Host "  Portable ZIP: $([math]::Round($zipSize, 1)) MB" -ForegroundColor Green
        Write-Host ""
    }

    # Generate checksums
    Write-Host "Generating checksums..." -ForegroundColor Yellow
    $checksumFile = "dist\ACBLink-$Version-SHA256.txt"
    $files = Get-ChildItem "dist\*.exe", "dist\*.msi", "dist\*.zip" -ErrorAction SilentlyContinue
    $checksums = @()
    foreach ($file in $files) {
        $hash = Get-FileHash $file.FullName -Algorithm SHA256
        $checksums += "$($hash.Hash)  $($file.Name)"
        Write-Host "  $($file.Name)" -ForegroundColor Green
        Write-Host "    SHA256: $($hash.Hash)" -ForegroundColor DarkGray
    }
    $checksums | Out-File $checksumFile -Encoding UTF8
    Write-Host ""

    # Summary
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "Build Complete!" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Output files:" -ForegroundColor Yellow
    Get-ChildItem "dist\*.exe", "dist\*.msi", "dist\*.zip" -ErrorAction SilentlyContinue | ForEach-Object {
        $size = [math]::Round($_.Length / 1MB, 1)
        Write-Host "  $($_.Name) ($size MB)" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "To test: .\dist\ACBLink\ACBLink.exe" -ForegroundColor Yellow
    Write-Host ""

} finally {
    Pop-Location
}
