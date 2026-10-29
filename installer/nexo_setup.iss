; Script do Inno Setup para gerar o Instalador do Nexo para Windows
; O aplicativo pode ser instalado em Arquivos de Programas (Com Admin),
; e em execucao grava todos os dados do usuario em %LOCALAPPDATA%\Nexo (Sem precisar de Admin).

#define MyAppName "Nexo"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Nexo - Gestao de Custos e Precificacao"
#define MyAppExeName "Nexo.exe"

[Setup]
AppId={{8F6E2A19-4B2C-4D7E-9A5C-1C3E9B8D7F21}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\dist
OutputBaseFilename=Instalador_Nexo_v{#MyAppVersion}
SetupIconFile=..\nexo_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\Nexo\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Nexo\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

