; AI Game Shorts - Inno Setup Installer Script
; Download Inno Setup: https://jrsoftware.org/isdl.php
; To compile: ISCC.exe installer.iss

#define MyAppName "AI Game Shorts"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Yash"
#define MyAppURL "https://github.com/yashsuthar12ha-byte/shorts-automation"
#define MyAppExeName "AI_Game_Shorts.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=AI_Game_Shorts_Setup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=ai_game_shorts.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "hindi"; MessagesFile: "compiler:Languages\Hindi.isl"

[Tasks]
Name: "desktopicon"; Description: "&Desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "startmenuicon"; Description: "&Start Menu shortcut"; GroupDescription: "Shortcuts:"

[Files]
; Main program
Source: "dist\AI_Game_Shorts\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Config files
Source: "config\*"; DestDir: "{app}\config"; Flags: ignoreversion
; FFmpeg
Source: "ffmpeg_bin\*"; DestDir: "{app}\ffmpeg_bin"; Flags: ignoreversion
; Sample data
Source: "sample_data\.gitkeep"; DestDir: "{app}\sample_data"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Run AI Game Shorts"; Flags: postinstall nowait skipifsilent shellexec

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create .env from .env.example if not exists
    if not FileExists(ExpandConstant('{app}\.env')) then
    begin
      if FileExists(ExpandConstant('{app}\.env.example')) then
      begin
        FileCopy(ExpandConstant('{app}\.env.example'),
                 ExpandConstant('{app}\.env'), False);
      end;
    end;
  end;
end;
