#define MyAppName "Echelon"
#define MyAppVersion "1.0"
#define MyAppPublisher "CR2 Creative"
#define MyAppURL "https://cr2creative.com"
#define MyAppExeName "Echelon.exe"
#define MyAppID "cr2creative.echelon.1.0"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
AppId={{{#MyAppID}}
AppName=Echelon
AppVersion=1.0
DefaultDirName={pf}\Echelon
DefaultGroupName=Echelon
UninstallDisplayIcon={app}\Echelon.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.
OutputBaseFilename=EchelonSetup
; Use icon from main ICONS folder
SetupIconFile=..\..\..\..\ICONS\Echelon.ico
UsePreviousAppDir=yes
Publisher=CR2 Creative

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\Echelon\Echelon.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Echelon\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\Echelon\template_structure_icon.svg"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\Echelon"; Filename: "{app}\Echelon.exe"
Name: "{group}\Uninstall Echelon"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Echelon"; Filename: "{app}\Echelon.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Echelon"; Filename: "{app}\Echelon.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\Echelon.exe"; Description: "{cm:LaunchProgram,Echelon}"; Flags: nowait postinstall skipifsilent 