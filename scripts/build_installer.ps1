param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$BuildRoot = "",
    [string]$IsccPath = "",
    [string]$OllamaExePath = "",
    [switch]$Archive
)

$ErrorActionPreference = "Stop"

$resolvedProjectRoot = (Resolve-Path $ProjectRoot).Path
$pythonExe = Join-Path $resolvedProjectRoot ".uvenv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment was not found: $pythonExe"
}

$arguments = @(
    "-m", "app.desktop.build",
    "--project-root", $resolvedProjectRoot,
    "--build-installer"
)

if ($BuildRoot -ne "") {
    $arguments += @("--build-root", $BuildRoot)
}
if ($IsccPath -ne "") {
    $arguments += @("--iscc-path", $IsccPath)
}
if ($OllamaExePath -ne "") {
    $arguments += @("--ollama-exe-path", $OllamaExePath)
}
if ($Archive) {
    $arguments += "--archive"
}

& $pythonExe @arguments
