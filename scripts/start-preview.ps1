$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Pnpm = "C:\Users\周亚楠\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd"
$QaDir = Join-Path $ProjectRoot ".qa"
New-Item -ItemType Directory -Force -Path $QaDir | Out-Null

$Process = Start-Process `
    -FilePath $Pnpm `
    -ArgumentList @("preview", "--host", "127.0.0.1", "--port", "4321") `
    -WorkingDirectory $ProjectRoot `
    -RedirectStandardOutput (Join-Path $QaDir "preview.stdout.log") `
    -RedirectStandardError (Join-Path $QaDir "preview.stderr.log") `
    -WindowStyle Hidden `
    -PassThru

[PSCustomObject]@{ Pid = $Process.Id; Running = -not $Process.HasExited }
