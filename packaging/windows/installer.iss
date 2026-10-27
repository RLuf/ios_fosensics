; Inno Setup Script para iOS Forensics TUI Suite (Windows x64)
; Empacota: ios_forensics.exe + libimobiledevice/usbmuxd Win64 + Drivers USB + Certificado

#ifndef MyAppVersion
  #define MyAppVersion "1.2.0"
#endif

#define MyAppName "iOS Forensics TUI Suite"
#define MyAppPublisher "RLuf Forensics"
#define MyAppURL "https://github.com/RLuf/ios_fosensics"
#define MyAppExeName "ios_forensics.exe"

[Setup]
AppId={{8F49E62A-5C71-4B89-9E3A-1D09C5F84B12}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\iOS_Forensics
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
OutputDir=..\..\dist\installer
OutputBaseFilename=iOS_Forensics_Setup_v{#MyAppVersion}_x64
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
ChangesEnvironment=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "installdrivers"; Description: "Instalar/Reparar Drivers USB Apple (VID_05AC) e Serviço Apple Mobile Device Service (AMDS)"; GroupDescription: "Drivers & Serviços Forenses:"
Name: "trustcert"; Description: "Instalar Certificado de Assinatura Authenticode nos Editores Confiáveis"; GroupDescription: "Segurança:"

[Files]
; Executável principal compilado pelo PyInstaller
Source: "..\..\dist\ios_forensics.exe"; DestDir: "{app}"; Flags: ignoreversion
; Código-fonte de referência e documentação
Source: "..\..\ios_forensics_tui.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
; Binários libimobiledevice / usbmuxd / afcclient (Win64)
Source: "..\..\build\bundle\bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
; Drivers USB Apple, Certificado (.cer) e script PowerShell de provisionamento
Source: "..\..\build\bundle\drivers\*"; DestDir: "{app}\drivers"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Inspeção Forense e Debug USB iOS (TUI)"
Name: "{group}\Exportação Rápida CLI (Relatório JSON + Fotos + SQLite)"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--cli-export"
Name: "{group}\Reparar Drivers USB Apple & Serviços (UAC)"; Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\drivers\install_drivers.ps1"""
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Instala certificado e drivers automaticamente durante o setup se selecionado
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\drivers\install_drivers.ps1"" -Quiet"; StatusMsg: "Configurando drivers USB Apple e serviço Apple Mobile Device Service (AMDS)..."; Flags: runhidden waituntilterminated; Tasks: installdrivers
; Opção de abrir o TUI ao finalizar a instalação
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
