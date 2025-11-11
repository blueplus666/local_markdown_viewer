[CmdletBinding()]
param(
  [string]$ProjectRoot = (Get-Location).Path,
  [string]$Python      = "python",
  [string]$TestPath    = "tests",
  [string[]]$PytestArgs = @("-vv","-s","-W","error"),
  [switch]$Enable013,
  [switch]$OpenTailWindow,
  [int]$TailLines = 100
)

$ErrorActionPreference = "Stop"

$stamp = Get-Date -Format yyyyMMdd_HHmmss
$runLog = Join-Path $ProjectRoot "pytest_run_$stamp.log"
$progressLog = Join-Path $ProjectRoot "pytest_progress_$stamp.log"

# 确保日志文件存在（便于 tail）
New-Item -ItemType File -Path $runLog -Force | Out-Null
New-Item -ItemType File -Path $progressLog -Force | Out-Null

# 实时输出与进度日志路径
$env:PYTHONUNBUFFERED   = "1"
$env:PYTEST_PROGRESS_LOG = $progressLog
$env:LAD_TEST_MODE = "1"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
# 统一设置 Qt 无头平台与日志降噪（便于 CI/本地一致）
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
$env:QT_LOGGING_RULES = "*.debug=false;qt.qpa.*=false;qt.text.*=false;qt.fonts.*=false"
if ($Enable013) { $env:LAD_RUN_013_TESTS = "1" } else { $env:LAD_RUN_013_TESTS = "0" }
$env:QT_OPENGL = "software"
$env:QTWEBENGINE_DISABLE_SANDBOX = "1"
$env:QTWEBENGINE_CHROMIUM_FLAGS = "--no-sandbox --disable-gpu --single-process"
if ($env:WINDIR) { $env:QT_QPA_FONTDIR = (Join-Path $env:WINDIR 'Fonts') }
try {
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
  # ignore encoding setup errors
}

# 可选：在新窗口实时尾随进度日志（[START]/[FINISH]）
$tailProc = $null
if ($OpenTailWindow) {
  $tailCmd = ('Get-Content -Path "{0}" -Tail {1} -Wait' -f $progressLog, $TailLines)
  $tailProc = Start-Process -PassThru -WindowStyle Normal -FilePath "powershell" -ArgumentList @("-NoLogo","-NoExit","-Command",$tailCmd)
}

Push-Location $ProjectRoot
try {
  $pytestCmd = @("-u","-m","pytest") + $PytestArgs + @($TestPath)
  $ErrorActionPreference = "Continue"
  try { $global:PSNativeCommandUseErrorActionPreference = $false } catch {}
  # 实时显示 + 写入运行日志
  & $Python $pytestCmd *>&1 | Tee-Object -FilePath $runLog
  $exitCode = $LASTEXITCODE
  $ErrorActionPreference = "Stop"
}
finally {
  Pop-Location
  if ($tailProc) {
    try {
      $tailProc.CloseMainWindow() | Out-Null
    } catch {
      # ignore close errors
    }
  }
}

Write-Host ""
Write-Host "Run log: $runLog"
Write-Host "Progress log: $progressLog"

# 打印最后一个 [START]（用于定位可能崩溃的用例）
$lastStart = Select-String -Path $progressLog -Pattern '^\[START\].*' | Select-Object -Last 1
if ($lastStart) {
  Write-Host "Last [START]:"
  Write-Host $lastStart.Line
} else {
  Write-Host "No [START] entries found in progress log."
}

# 附带输出进度日志的尾部，便于快速观察上下文
Write-Host ""
Write-Host "Last $TailLines lines of progress log:"
Get-Content -Path $progressLog -Tail $TailLines

exit $exitCode