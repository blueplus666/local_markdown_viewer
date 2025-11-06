# Requires -Version 5.1
param(
  [string]$ProcessName = 'python',
  [int]$Pid = 0,
  [switch]$Json
)

function Get-TargetProcess {
  if ($Pid -gt 0) { return Get-Process -Id $Pid -ErrorAction SilentlyContinue }
  $procs = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue | Sort-Object -Property StartTime -Descending
  if ($procs) { return $procs[0] }
  return $null
}

function Get-ChildProcesses([int]$ParentPid) {
  try {
    return Get-CimInstance Win32_Process -Filter "ParentProcessId = $ParentPid" | Select-Object ProcessId, Name, CommandLine
  } catch { @() }
}

function Get-ProcessSummary($p) {
  if (-not $p) { return $null }
  $children = Get-ChildProcesses -ParentPid $p.Id
  $mods = @()
  try { $mods = $p.Modules | Select-Object -First 20 | ForEach-Object { $_.ModuleName } } catch { }
  [pscustomobject]@{
    pid = $p.Id
    name = $p.ProcessName
    cpu = $p.CPU
    handles = $p.Handles
    threads = $p.Threads.Count
    workingSetMB = [math]::Round(($p.WorkingSet64/1MB),2)
    startTime = ($p.StartTime) 2>$null
    modulesPreview = $mods
    childCount = ($children | Measure-Object).Count
    children = $children
  }
}

function Get-ThreadPreview($p) {
  try {
    return $p.Threads | Select-Object -First 50 Id, PriorityLevel, ThreadState, WaitReason
  } catch { @() }
}

function Get-HandleSnapshot($p) {
  # Lightweight: only counts by type via perf counters fallback
  try {
    return [pscustomobject]@{ handleCount = $p.Handles }
  } catch { [pscustomobject]@{ handleCount = $null } }
}

$proc = Get-TargetProcess
if (-not $proc) {
  $msg = "Target process not found. Use -Pid or -ProcessName to specify."
  if ($Json) { Write-Output (@{ ok = $false; message = $msg } | ConvertTo-Json -Depth 5) } else { Write-Host $msg }
  exit 1
}

$summary = Get-ProcessSummary -p $proc
$threads = Get-ThreadPreview -p $proc
$handles = Get-HandleSnapshot -p $proc

$result = [pscustomobject]@{
  ok = $true
  inspectedAt = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  process = $summary
  threadsPreview = $threads
  handles = $handles
}

if ($Json) { $result | ConvertTo-Json -Depth 6 } else { $result | Format-List | Out-String | Write-Host }

exit 0

