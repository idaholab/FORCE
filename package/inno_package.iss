; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "FORCE"
#define MyAppVersion "0.8"
#define MyAppPublisher "Idaho National Laboratory"
#define MyAppURL "https://github.com/idaholab/FORCE"
#define MyAppExeName "MyProg.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{D0EBD58D-0C2A-4451-8E20-C3C9C1AA5BE0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Remove the following line to run in administrative install mode (install for all users.)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=inno_output
OutputBaseFilename=force_setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "raven_install\heron.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "raven_install\raven_framework.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "raven_install\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\FORCE\HERON"; Filename: "{app}\heron.exe"
Name: "{autoprograms}\FORCE\RAVEN"; Filename: "{app}\raven_framework.exe"
Name: "{autoprograms}\FORCE\TEAL"; Filename: "{app}\teal.exe"
Name: "{autodesktop}\HERON"; Filename: "{app}\heron.exe"; Tasks: desktopicon
Name: "{autodesktop}\RAVEN"; Filename: "{app}\raven_framework.exe"; Tasks: desktopicon
Name: "{autodesktop}\TEAL"; Filename: "{app}\teal.exe"; Tasks: desktopicon


; [Run]
; Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

