#!/usr/bin/makensis

!define APPNAME "comtool"
!define FILENAME "comtool"
!define AUTHOR "Author name"
!define DESCRIPTION "com debug tool"

Unicode True

!define /file VERSION "VERSION"
!define /file INSTALLSIZE "INSTALLSIZE"
!define /file ARCH "ARCH"

InstallDir "$PROGRAMFILES\${APPNAME}"

Name "${APPNAME}"
Icon "COMTool/assets/logo.ico"
outFile "${FILENAME}-${VERSION}-${ARCH}.exe"

!include LogicLib.nsh

Page directory
Page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin" ;Require admin rights on NT4+
        messageBox mb_iconstop "Administrator rights required!"
        setErrorLevel 740 ;ERROR_ELEVATION_REQUIRED
        quit
${EndIf}
!macroend

function .onInit
	setShellVarContext all
	!insertmacro VerifyUserIsAdmin
functionEnd

section "install"

	setOutPath $INSTDIR
	file "COMTool\assets\logo.ico"
	file "${FILENAME}.zip"

	nsisunz::Unzip "$INSTDIR\${FILENAME}.zip" "$INSTDIR"

	delete "$INSTDIR\${FILENAME}.zip"

	writeUninstaller "$INSTDIR\uninstall.exe"

	createDirectory "$SMPROGRAMS\${APPNAME}"
	createShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${FILENAME}.exe" "" "$INSTDIR\COMTool\assets\logo.ico.ico"

	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\COMTool\assets\logo.ico$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${AUTHOR}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSION}"
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
sectionEnd

function un.onInit
	SetShellVarContext all
	MessageBox MB_OKCANCEL "Permanently remove ${APPNAME}?" IDOK next
		Abort
	next:
	!insertmacro VerifyUserIsAdmin
functionEnd

section "uninstall"
	rmDir /r /REBOOTOK "$SMPROGRAMS\${APPNAME}"
	rmDir /r /REBOOTOK $INSTDIR
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
sectionEnd
