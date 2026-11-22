Unicode true
Name "Adam Desktop"
OutFile "AdamSetup.exe"
InstallDir "$LOCALAPPDATA\AdamDesktop"
RequestExecutionLevel user
CRCCheck off
SetCompressor lzma
BrandingText "Adam - criado por Felipe Hudson"

!include "MUI2.nsh"
!define MUI_ICON "adam.ico"
!define MUI_UNICON "adam.ico"
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_FUNCTION LaunchAdam
!define MUI_FINISHPAGE_RUN_TEXT "Abrir o Adam Desktop agora"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "PortugueseBR"

Function LaunchAdam
  ExecShell "" "$DESKTOP\Adam Desktop.lnk"
FunctionEnd

Section "Adam Desktop"
  SetOutPath "$INSTDIR"
  File /r "stage\python"
  File "stage\adam_desktop.py"
  File "stage\LEIA-ME.txt"
  File "adam.ico"
  SetCompress off
  File "stage\server.txt"
  SetCompress auto
  CreateShortCut "$DESKTOP\Adam Desktop.lnk" "$INSTDIR\python\python.exe" '"$INSTDIR\adam_desktop.py"' "$INSTDIR\adam.ico"
  CreateDirectory "$SMPROGRAMS\Adam Desktop"
  CreateShortCut "$SMPROGRAMS\Adam Desktop\Adam Desktop.lnk" "$INSTDIR\python\python.exe" '"$INSTDIR\adam_desktop.py"' "$INSTDIR\adam.ico"
  CreateShortCut "$SMPROGRAMS\Adam Desktop\Desinstalar.lnk" "$INSTDIR\Desinstalar.exe"
  WriteUninstaller "$INSTDIR\Desinstalar.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AdamDesktop" "DisplayName" "Adam Desktop"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AdamDesktop" "UninstallString" '"$INSTDIR\Desinstalar.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AdamDesktop" "DisplayIcon" "$INSTDIR\adam.ico"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AdamDesktop" "Publisher" "Felipe Hudson"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\Adam Desktop.lnk"
  RMDir /r "$SMPROGRAMS\Adam Desktop"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\AdamDesktop"
SectionEnd
