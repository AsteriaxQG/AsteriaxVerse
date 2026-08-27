#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

#define MyAppName "Asteriax Verse"
#define MyAppPublisher "AsteriaxTTV"
#define MyAppExeName "AsteriaxVerse.exe"
#define MyAppURL "https://github.com/AsteriaxQG/AsteriaxVerse"

[Setup]
AppId={{89C5B17C-90C0-493A-B3CB-40655C4419B8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\Asteriax Verse
DefaultGroupName=Asteriax Verse
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename=AsteriaxVerse-Setup-{#MyAppVersion}
SetupIconFile=..\assets\asteriax.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
LicenseFile=..\LICENSE.txt
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}
RestartApplications=no
SetupLogging=yes
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Installateur Asteriax Verse
VersionInfoProductName={#MyAppName}
VersionInfoCopyright=Copyright AsteriaxTTV

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: checkedonce

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Asteriax Verse"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\Asteriax Verse"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer Asteriax Verse"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

