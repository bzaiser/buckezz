; Inno Setup Script für Buckezz Desktop
#define MyAppName "Buckezz Desktop"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Buckezz"
#define MyAppExeName "BuckezzDesktop.exe"

[Setup]
AppId={{C8E64A12-87C2-4DBA-9F08-2A1B432DE990}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=static\img\app.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
OutputDir=dist_installer
OutputBaseFilename=BuckezzDesktop_Setup
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Fertig migrierte SQLite-Datenbank nur installieren, falls noch keine existiert (Benutzerdaten bleiben bei Updates erhalten):
Source: "clean_template.sqlite3"; DestDir: "{app}"; DestName: "db.sqlite3"; Flags: onlyifdoesntexist

; Alle Programmdateien installieren / überschreiben:
Source: "dist\BuckezzDesktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: ".env,db.sqlite3,*.sqlite3,data\db.sqlite3"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
