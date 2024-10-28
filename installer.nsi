!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "EZLan"
OutFile "EZLan_Setup.exe"
InstallDir "$PROGRAMFILES\EZLan"
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON "ezlan\resources\icon.ico"
!define MUI_UNICON "ezlan\resources\icon.ico"
!define MUI_FINISHPAGE_RUN "$INSTDIR\EZLan.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch EZLan"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "$INSTDIR"
    
    # Copy main executable and resources
    File "dist\EZLan.exe"
    File /r "ezlan\resources\*.*"
    
    # Copy TAP driver installer
    File "ezlan\resources\tap-windows.exe"
    
    # Create program shortcuts
    CreateDirectory "$SMPROGRAMS\EZLan"
    CreateShortcut "$SMPROGRAMS\EZLan\EZLan.lnk" "$INSTDIR\EZLan.exe"
    CreateShortcut "$DESKTOP\EZLan.lnk" "$INSTDIR\EZLan.exe"
    
    # Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    # Registry information for add/remove programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EZLan" \
                     "DisplayName" "EZLan"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EZLan" \
                     "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EZLan" \
                     "DisplayIcon" "$INSTDIR\EZLan.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EZLan" \
                     "Publisher" "EZLan"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EZLan" \
                     "DisplayVersion" "1.0.0"
    
    # Install TAP driver with wizard
    MessageBox MB_OK "The TAP driver installation wizard will now start. Please complete the installation."
    ExecWait '"$INSTDIR\tap-windows.exe"'
    
    # Give time for driver installation to complete
    Sleep 10000
SectionEnd

Section "Uninstall"
    # Remove application files
    Delete "$INSTDIR\EZLan.exe"
    Delete "$INSTDIR\tap-windows.exe"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR\resources"
    
    # Remove shortcuts
    Delete "$SMPROGRAMS\EZLan\EZLan.lnk"
    Delete "$DESKTOP\EZLan.lnk"
    RMDir "$SMPROGRAMS\EZLan"
    RMDir "$INSTDIR"
    
    # Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EZLan"
    
    # Clean up TAP adapters
    nsExec::ExecToLog 'netsh interface delete "EZLan-TAP"'
SectionEnd