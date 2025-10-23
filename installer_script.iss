; Inno Setup Script for Internet Speed Test Application
; Compatible with Inno Setup 6.3+ (Stable and Preview versions)
; Save this as: installer_script.iss

#define MyAppName "Internet Speed Test"
#define MyAppVersion "1.0"
#define MyAppPublisher "Saikat Majumder"
#define MyAppExeName "InternetSpeedTest.exe"

[Setup]
; App Identity
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}

; Installation Directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Privileges (no admin needed)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Output Configuration
OutputDir=installer_output
OutputBaseFilename=InternetSpeedTest_Setup_v{#MyAppVersion}
SetupIconFile=app_icon.ico

; Compression
Compression=lzma
SolidCompression=yes

; Modern UI
WizardStyle=modern

; Uninstall Display Icon
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Add any additional files here if needed
; Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\InternetSpeedTest.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion


[Icons]
; Start Menu Icon with custom icon
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
; Desktop Icon (optional) with custom icon
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Run]
; Launch app after installation (optional)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up any created files during uninstall
Type: files; Name: "{app}\speed_test_history.json"