#ifndef MyAppName
  #define MyAppName "TeamMindHub"
#endif
#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif
#ifndef MyAppExeName
  #define MyAppExeName "TeamMindHub.exe"
#endif
#ifndef SourceDir
  #define SourceDir "..\.tmp\desktop-build\dist\TeamMindHub"
#endif
#ifndef BuildOutputDir
  #define BuildOutputDir "..\.tmp\desktop-build\release"
#endif
#ifndef BuildOutputBaseFilename
  #define BuildOutputBaseFilename "TeamMindHub-Setup"
#endif
#ifndef OllamaExecutable
  #define OllamaExecutable ""
#endif

[Setup]
AppId={{4F951AB4-6B6D-4C41-A2BC-A07C5442C2DB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=TeamMindHub
WizardStyle=modern
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#BuildOutputDir}
OutputBaseFilename={#BuildOutputBaseFilename}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
var
  ModelPage: TWizardPage;
  LightweightRadio: TNewRadioButton;
  StandardRadio: TNewRadioButton;
  HighPerformanceRadio: TNewRadioButton;
  DownloadModelCheck: TNewCheckBox;
  ModelHintLabel: TNewStaticText;

function GetSelectedModelValue(): String;
begin
  if LightweightRadio.Checked then
    Result := 'llama3.2:3b'
  else if HighPerformanceRadio.Checked then
    Result := 'deepseek-r1:14b'
  else
    Result := 'deepseek-r1:8b';
end;

function GetSelectedModelLabel(): String;
begin
  if LightweightRadio.Checked then
    Result := '轻量模式'
  else if HighPerformanceRadio.Checked then
    Result := '高性能模式'
  else
    Result := '标准模式';
end;

function GetAppBaseDir(): String;
begin
  Result := ExpandConstant('{localappdata}\TeamMindHub');
end;

function GetEnvFilePath(): String;
begin
  Result := GetAppBaseDir() + '\.env.local';
end;

function GetLocalOllamaBaseUrl(): String;
begin
  Result := 'http://127.0.0.1:11434';
end;

function BuildEnvFileContent(): String;
var
  NewLine: String;
begin
  NewLine := #13#10;
  Result :=
    'OLLAMA_BASE_URL=' + GetLocalOllamaBaseUrl() + NewLine +
    'OLLAMA_MODEL=' + GetSelectedModelValue() + NewLine +
    'OLLAMA_TIMEOUT_SECONDS=60' + NewLine;
end;

procedure PersistDesktopEnvFile();
var
  EnvFilePath: String;
begin
  EnvFilePath := GetEnvFilePath();
  if not ForceDirectories(ExtractFileDir(EnvFilePath)) then
    RaiseException('无法创建 TeamMindHub 配置目录：' + ExtractFileDir(EnvFilePath));
  if not SaveStringToFile(EnvFilePath, BuildEnvFileContent(), False) then
    RaiseException('无法写入桌面配置文件：' + EnvFilePath);
end;

function ResolveOllamaExecutable(): String;
var
  Candidate: String;
begin
  Result := '';

  Candidate := '{#OllamaExecutable}';
  if (Candidate <> '') and FileExists(Candidate) then
  begin
    Result := Candidate;
    exit;
  end;

  Candidate := ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe');
  if FileExists(Candidate) then
  begin
    Result := Candidate;
    exit;
  end;

  Candidate := ExpandConstant('{localappdata}\Programs\Ollama\ollama app.exe');
  if FileExists(Candidate) then
  begin
    Result := Candidate;
    exit;
  end;

  Candidate := ExpandConstant('{pf}\Ollama\ollama.exe');
  if FileExists(Candidate) then
  begin
    Result := Candidate;
    exit;
  end;

  Candidate := ExpandConstant('{pf32}\Ollama\ollama.exe');
  if FileExists(Candidate) then
    Result := Candidate;
end;

procedure PullSelectedOllamaModel();
var
  OllamaPath: String;
  ResultCode: Integer;
  Params: String;
begin
  OllamaPath := ResolveOllamaExecutable();
  if OllamaPath = '' then
  begin
    MsgBox(
      '安装完成，但没有检测到 Ollama 可执行文件。' + #13#10 +
      '已为你保存默认模型配置，你可以稍后手动安装或启动 Ollama。',
      mbInformation,
      MB_OK
    );
    exit;
  end;

  Params := 'pull ' + GetSelectedModelValue();
  if not Exec(OllamaPath, Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    MsgBox(
      '安装完成，但自动拉取模型失败。' + #13#10 +
      'Ollama 路径：' + OllamaPath + #13#10 +
      '模型：' + GetSelectedModelValue(),
      mbInformation,
      MB_OK
    );
    exit;
  end;

  if ResultCode <> 0 then
  begin
    MsgBox(
      'Ollama 已启动，但模型下载未成功完成。' + #13#10 +
      '你可以稍后手动执行：ollama pull ' + GetSelectedModelValue(),
      mbInformation,
      MB_OK
    );
  end;
end;

procedure InitializeWizard();
begin
  ModelPage := CreateCustomPage(
    wpSelectTasks,
    '本地模型配置',
    '选择安装后默认使用的 Ollama 模型档位。'
  );

  LightweightRadio := TNewRadioButton.Create(ModelPage);
  LightweightRadio.Parent := ModelPage.Surface;
  LightweightRadio.Caption := '轻量模式: llama3.2:3b';
  LightweightRadio.Left := ScaleX(0);
  LightweightRadio.Top := ScaleY(12);
  LightweightRadio.Width := ModelPage.SurfaceWidth;
  LightweightRadio.Checked := False;

  StandardRadio := TNewRadioButton.Create(ModelPage);
  StandardRadio.Parent := ModelPage.Surface;
  StandardRadio.Caption := '标准模式: deepseek-r1:8b';
  StandardRadio.Left := ScaleX(0);
  StandardRadio.Top := LightweightRadio.Top + ScaleY(26);
  StandardRadio.Width := ModelPage.SurfaceWidth;
  StandardRadio.Checked := True;

  HighPerformanceRadio := TNewRadioButton.Create(ModelPage);
  HighPerformanceRadio.Parent := ModelPage.Surface;
  HighPerformanceRadio.Caption := '高性能模式: deepseek-r1:14b';
  HighPerformanceRadio.Left := ScaleX(0);
  HighPerformanceRadio.Top := StandardRadio.Top + ScaleY(26);
  HighPerformanceRadio.Width := ModelPage.SurfaceWidth;

  ModelHintLabel := TNewStaticText.Create(ModelPage);
  ModelHintLabel.Parent := ModelPage.Surface;
  ModelHintLabel.Left := ScaleX(0);
  ModelHintLabel.Top := HighPerformanceRadio.Top + ScaleY(34);
  ModelHintLabel.Width := ModelPage.SurfaceWidth;
  ModelHintLabel.Height := ScaleY(70);
  ModelHintLabel.AutoSize := False;
  ModelHintLabel.Caption :=
    '轻量模式建议 8GB 内存起步，标准模式建议 16GB 内存，高性能模式建议 24GB 以上内存。' + #13#10 +
    '安装程序会把你选择的模型写入 %LOCALAPPDATA%\TeamMindHub\.env.local。';

  DownloadModelCheck := TNewCheckBox.Create(ModelPage);
  DownloadModelCheck.Parent := ModelPage.Surface;
  DownloadModelCheck.Left := ScaleX(0);
  DownloadModelCheck.Top := ModelHintLabel.Top + ScaleY(80);
  DownloadModelCheck.Width := ModelPage.SurfaceWidth;
  DownloadModelCheck.Caption := '安装完成后立即尝试下载所选模型';
  DownloadModelCheck.Checked := False;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    PersistDesktopEnvFile();
    if DownloadModelCheck.Checked then
      PullSelectedOllamaModel();
  end;
end;
