; ----------------------------------------
; BorderlessManager Installer Script (Sin compresión)
; ----------------------------------------

[Setup]
AppName=Borderless Manager
AppVersion=1.0
DefaultDirName={pf}\BorderlessManager
DefaultGroupName=Borderless Manager
OutputBaseFilename=BorderlessManagerSetup
Compression=none
SolidCompression=no

[Files]
Source: "dist\BorderlessManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Borderless Manager"; Filename: "{app}\BorderlessManager.exe"
Name: "{userdesktop}\Borderless Manager"; Filename: "{app}\BorderlessManager.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear ícono en el escritorio"; GroupDescription: "Icono:"; Flags: unchecked

[Run]
Filename: "{app}\BorderlessManager.exe"; Description: "Iniciar Borderless Manager"; Flags: nowait postinstall skipifsilent
