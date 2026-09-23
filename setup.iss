[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
AppId={{9F82A2E6-B9F2-4D3C-9B05-C0A9A8C7F5D1}
AppName=Tweakify
AppVersion=2.0
AppPublisher=Jaber
DefaultDirName={autopf}\Tweakify
DefaultGroupName=Tweakify
AllowNoIcons=yes
; Output directory where the setup file will be created
OutputDir=Output
OutputBaseFilename=Tweakify_Setup_v2.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico
; Requires admin privileges to install and run since it's a Windows tweaking tool
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Make sure this path correctly points to the compiled Tweakify.exe
Source: "dist\Tweakify.exe"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\Tweakify"; Filename: "{app}\Tweakify.exe"
Name: "{group}\{cm:UninstallProgram,Tweakify}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Tweakify"; Filename: "{app}\Tweakify.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Tweakify.exe"; Description: "{cm:LaunchProgram,Tweakify}"; Flags: nowait postinstall skipifsilent
