[CmdletBinding()]
param(
  [string]$ProjectRoot = (Get-Location).Path,
  [string]$LogPath,
  [int]$Top = 20,
  [switch]$Csv,
  [string]$OutPath
)

$ErrorActionPreference = 'Stop'

if (-not $LogPath) {
  $latest = Get-ChildItem -Path $ProjectRoot -Filter 'pytest_progress_*.log' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $latest) { throw "No pytest_progress_*.log found under $ProjectRoot. Provide -LogPath explicitly." }
  $LogPath = $latest.FullName
}

if (-not (Test-Path -LiteralPath $LogPath)) { throw "Log file not found: $LogPath" }

$pattern = '^(?<raw>\[(?<tag>[A-Z_ ]+)\])\s+(?<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+pid=(?<pid>\d+)\s+(?<nodeid>.+)$'
$tests = @{}

Get-Content -Path $LogPath | ForEach-Object {
  $line = $_
  if ($line -notmatch $pattern) { return }
  $tag = $Matches['tag'].Trim()
  $ts  = [datetime]::ParseExact($Matches['ts'], 'yyyy-MM-dd HH:mm:ss', $null)
  $procId = [int]$Matches['pid']
  $nodeid = $Matches['nodeid']

  if (-not $tests.ContainsKey($nodeid)) {
    $tests[$nodeid] = [ordered]@{
      NodeId=$nodeid; Pid=$procId; Start=$null; Setup=$null; Call=$null; Teardown=$null; Finish=$null;
      SetupOutcome=$null; CallOutcome=$null; TeardownOutcome=$null
    }
  }
  $e = $tests[$nodeid]

  if ($tag -eq 'START') {
    if (-not $e.Start) { $e.Start = $ts }
    if (-not $e.Pid)   { $e.Pid   = $procId }
    return
  }
  if ($tag -eq 'FINISH') {
    $e.Finish = $ts
    return
  }
  $m = [regex]::Match($tag, '^(SETUP|CALL|TEARDOWN)\s+(PASSED|FAILED|SKIPPED|XFAILED|XSKIPPED|ERROR)$')
  if ($m.Success) {
    $stage   = $m.Groups[1].Value
    $outcome = $m.Groups[2].Value
    switch ($stage) {
      'SETUP'    { if (-not $e.Setup)    { $e.Setup = $ts }; $e.SetupOutcome    = $outcome }
      'CALL'     { if (-not $e.Call)     { $e.Call = $ts };  $e.CallOutcome     = $outcome }
      'TEARDOWN' { if (-not $e.Teardown) { $e.Teardown = $ts }; $e.TeardownOutcome = $outcome }
    }
  }
}

$results = @()
foreach ($nodeid in $tests.Keys) {
  $e = $tests[$nodeid]
  $setupSec    = if ($e.Start -and $e.Setup)    { [math]::Round(($e.Setup - $e.Start).TotalSeconds, 3) } else { $null }
  $callSec     = if ($e.Setup -and $e.Call)     { [math]::Round(($e.Call - $e.Setup).TotalSeconds, 3) } else { $null }
  $teardownSec = if ($e.Call -and $e.Teardown)  { [math]::Round(($e.Teardown - $e.Call).TotalSeconds, 3) } elseif ($e.Setup -and $e.Teardown) { [math]::Round(($e.Teardown - $e.Setup).TotalSeconds, 3) } else { $null }
  $totalSec    = if ($e.Start -and $e.Finish)   { [math]::Round(($e.Finish - $e.Start).TotalSeconds, 3) } else { $null }

  $results += [pscustomobject]@{
    NodeId=$e.NodeId
    Pid=$e.Pid
    SetupSec=$setupSec
    CallSec=$callSec
    TeardownSec=$teardownSec
    TotalSec=$totalSec
    SetupOutcome=$e.SetupOutcome
    CallOutcome=$e.CallOutcome
    TeardownOutcome=$e.TeardownOutcome
  }
}

$sorted = $results | Sort-Object -Property @{Expression='TotalSec'; Descending=$true}, @{Expression='CallSec'; Descending=$true}
$topList = $sorted | Select-Object -First $Top

Write-Host "Log: $LogPath"
Write-Host "Total tests parsed: " ($results.Count)

$topList

if ($Csv) {
  if (-not $OutPath) { $OutPath = Join-Path $ProjectRoot ("pytest_phases_" + (Get-Date -Format yyyyMMdd_HHmmss) + ".csv") }
  $sorted | Export-Csv -NoTypeInformation -Path $OutPath -Encoding UTF8
  Write-Host "Saved CSV to: $OutPath"
}
