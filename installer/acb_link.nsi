; ACB Link Desktop - NSIS Installer Script
; Creates a professional Windows installer with accessibility support

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "x64.nsh"

; ============================================================================
; Installer Attributes
; ============================================================================

!define APP_NAME "ACB Link Desktop"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "American Council of the Blind"
!define APP_URL "https://acb.org"
!define APP_EXE "ACBLink.exe"
!define APP_ICON "acb512.ico"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "ACBLink-${APP_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "InstallDir"
RequestExecutionLevel admin

; ============================================================================
; Modern UI Configuration
; ============================================================================

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Welcome page
!insertmacro MUI_PAGE_WELCOME

; License page
!insertmacro MUI_PAGE_LICENSE "LICENSE"

; Components page (for optional wake word support)
!insertmacro MUI_PAGE_COMPONENTS

; Directory page
!insertmacro MUI_PAGE_DIRECTORY

; Install files page
!insertmacro MUI_PAGE_INSTFILES

; Finish page with launch option
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APP_NAME}"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"

; ============================================================================
; Component Descriptions
; ============================================================================

LangString DESC_SecMain ${LANG_ENGLISH} "Core application files for ACB Link Desktop (required)"
LangString DESC_SecWakeWord ${LANG_ENGLISH} "Wake word detection - enables 'Hey ACB Link' voice activation. Requires ~5GB download of AI/ML components. Without this, voice control works via Ctrl+Shift+V keyboard shortcut."

; ============================================================================
; Accessibility Support
; ============================================================================

; Set accessible installer properties
BrandingText "${APP_NAME} - Accessible Installer"

; ============================================================================
; Installer Sections
; ============================================================================

Section "Main Application" SecMain
    SectionIn RO  ; Required section

    SetOutPath "$INSTDIR"

    ; Copy all files from PyInstaller output
    File /r "dist\ACBLink\*.*"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\User Guide.lnk" "$INSTDIR\docs\USER_GUIDE.md"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

    ; Create Desktop shortcut
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0

    ; Write registry keys for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1

    ; Get installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "EstimatedSize" "$0"

    ; Write application path for auto-updates
    WriteRegStr HKLM "Software\${APP_NAME}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\${APP_NAME}" "Version" "${APP_VERSION}"

SectionEnd

Section /o "Wake Word Support (5GB download)" SecWakeWord
    ; Optional section - unchecked by default
    ; This section runs pip to install wake word dependencies

    DetailPrint "Installing wake word support..."
    DetailPrint "This may take several minutes and requires ~5GB disk space."

    ; Run pip to install openwakeword and dependencies
    ; Uses bundled Python from PyInstaller
    nsExec::ExecToLog '"$INSTDIR\python\python.exe" -m pip install openwakeword torch torchaudio'
    Pop $0
    ${If} $0 != 0
        MessageBox MB_OK|MB_ICONEXCLAMATION "Wake word support installation failed.$\n$\nYou can install it later by running:$\npip install openwakeword torch torchaudio"
    ${Else}
        DetailPrint "Wake word support installed successfully!"
    ${EndIf}

SectionEnd

; Component descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecWakeWord} $(DESC_SecWakeWord)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ============================================================================
; Uninstaller Section
; ============================================================================

Section "Uninstall"

    ; Remove application files
    RMDir /r "$INSTDIR"

    ; Remove Start Menu shortcuts
    RMDir /r "$SMPROGRAMS\${APP_NAME}"

    ; Remove Desktop shortcut
    Delete "$DESKTOP\${APP_NAME}.lnk"

    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "Software\${APP_NAME}"

    ; Note: We don't remove user data in ~/.acb_link
    ; Users may want to keep their settings

SectionEnd

; ============================================================================
; Functions
; ============================================================================

Function .onInit
    ; Check for 64-bit Windows
    ${If} ${RunningX64}
        SetRegView 64
    ${Else}
        MessageBox MB_OK|MB_ICONSTOP "This application requires 64-bit Windows."
        Abort
    ${EndIf}

    ; Check for previous installation
    ReadRegStr $0 HKLM "Software\${APP_NAME}" "InstallDir"
    ${If} $0 != ""
        StrCpy $INSTDIR $0
    ${EndIf}
FunctionEnd

Function un.onInit
    MessageBox MB_YESNO "Are you sure you want to uninstall ${APP_NAME}?$\n$\nYour settings and downloaded content will be preserved." IDYES +2
    Abort
FunctionEnd
