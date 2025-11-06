#requires -Version 5.1

param(
    [string]$ConfigPath = '',
    [switch]$SkipTests,
    [switch]$WhatIf,
    [switch]$Rollback
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok([string]$msg)   { Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err([string]$msg)  { Write-Host "[ERR ] $msg" -ForegroundColor Red }

function Find-RepoRoot {
    $dir = Split-Path -Parent $PSScriptRoot
    while ($dir -and -not (Test-Path (Join-Path $dir 'local_markdown_viewer\CHANGELOG.md'))) {
        $parent = Split-Path -Parent $dir
        if ($parent -eq $dir) { break }
        $dir = $parent
    }
    if (-not $dir) { throw 'REPO_ROOT_NOT_FOUND' }
    return $dir
}

function Load-Json([string]$path) {
    if (-not (Test-Path $path)) { throw "CONFIG_NOT_FOUND: $path" }
    $content = Get-Content -Path $path -Raw -Encoding UTF8
    return $content | ConvertFrom-Json -ErrorAction Stop
}

function Ensure-Directory([string]$path) {
    if (-not (Test-Path $path)) { if (-not $WhatIf) { New-Item -ItemType Directory -Path $path -Force | Out-Null } else { Write-Info "[DRYRUN] mkdir $path" } }
}

function Backup-File([string]$targetPath, [string]$backupDir) {
    if (Test-Path $targetPath) {
        Ensure-Directory $backupDir
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $name  = Split-Path -Leaf $targetPath
        $bak   = Join-Path $backupDir "$stamp-$name"
        if (-not $WhatIf) {
            Copy-Item -Path $targetPath -Destination $bak -Force
            Write-Info "Backup created: $bak"
        } else {
            Write-Info "[DRYRUN] backup $targetPath -> $bak"
        }
    }
}

function Apply-Configs($repoRoot, $cfg) {
    if (-not ($cfg.PSObject.Properties.Name -contains 'applyConfigs')) { return }
    foreach ($item in $cfg.applyConfigs) {
        $srcRel = [string]$item.source
        $dstRel = [string]$item.target
        $backupRel = [string]($item.backupDir ? $item.backupDir : 'backups')

        $src = Join-Path $repoRoot $srcRel
        $dst = Join-Path $repoRoot $dstRel
        $bakDir = Join-Path $repoRoot $backupRel

        if (-not (Test-Path $src)) { throw "SOURCE_MISSING: $srcRel" }
        Ensure-Directory (Split-Path -Parent $dst)
        Backup-File -targetPath $dst -backupDir $bakDir
        if (-not $WhatIf) {
            Copy-Item -Path $src -Destination $dst -Force
            Write-Ok "Deployed: $srcRel -> $dstRel"
        } else {
            Write-Info "[DRYRUN] would deploy: $srcRel -> $dstRel"
        }
    }
}

function Save-Json($obj, [string]$path) {
    $json = $obj | ConvertTo-Json -Depth 16
    if (-not $WhatIf) {
        $json | Set-Content -Path $path -Encoding UTF8 -Force
        Write-Ok "Updated: $path"
    } else {
        Write-Info "[DRYRUN] would write json: $path"
    }
}

function Perform-Rollback($repoRoot) {
    $ladCfgPath = Join-Path $repoRoot 'local_markdown_viewer\config\lad_integration.json'
    Ensure-Directory (Split-Path -Parent $ladCfgPath)
    if (Test-Path $ladCfgPath) { Backup-File -targetPath $ladCfgPath -backupDir (Join-Path $repoRoot 'backups') }

    if (Test-Path $ladCfgPath) {
        $obj = (Get-Content -Path $ladCfgPath -Raw -Encoding UTF8) | ConvertFrom-Json -ErrorAction Stop
    } else {
        $obj = [pscustomobject]@{}
    }

    $hasRootEnabled = $obj.PSObject.Properties.Name -contains 'enabled'
    $hasRootMonitoring = $obj.PSObject.Properties.Name -contains 'monitoring'
    if ($hasRootEnabled -or $hasRootMonitoring) {
        $obj.enabled = $false
        if ($null -eq $obj.PSObject.Properties['monitoring']) {
            $obj | Add-Member -NotePropertyName 'monitoring' -NotePropertyValue ([pscustomobject]@{}) -Force
        }
        $obj.monitoring.enabled = $false
    } else {
        if ($null -eq $obj.PSObject.Properties['lad_integration']) {
            $obj | Add-Member -NotePropertyName 'lad_integration' -NotePropertyValue ([pscustomobject]@{}) -Force
        }
        if ($null -eq $obj.lad_integration.PSObject.Properties['monitoring']) {
            $obj.lad_integration | Add-Member -NotePropertyName 'monitoring' -NotePropertyValue ([pscustomobject]@{}) -Force
        }
        $obj.lad_integration.enabled = $false
        $obj.lad_integration.monitoring.enabled = $false
    }

    Save-Json -obj $obj -path $ladCfgPath
}

function Configure-Env($cfg) {
    if ($cfg -and ($cfg.PSObject.Properties.Name -contains 'setEnvironment') -and $cfg.setEnvironment) {
        $cfg.setEnvironment.PSObject.Properties | ForEach-Object {
            $name = $_.Name; $value = [string]$_.Value
            if (-not $WhatIf) {
                Set-Item -Path "Env:$name" -Value $value
                Write-Info "ENV set: $name=$value"
            } else {
                Write-Info "[DRYRUN] ENV would set: $name=$value"
            }
        }
    }
}

function Run-Tests($repoRoot) {
    Write-Info 'Running test gate: pytest test_qa_all.py'
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'python'
    $psi.Arguments = '-X utf8 -m pytest local_markdown_viewer/tests/test_qa_all.py -q'
    $psi.WorkingDirectory = $repoRoot
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    if ($stdout) { Write-Host $stdout }
    if ($stderr) { Write-Warn $stderr }
    if ($proc.ExitCode -ne 0) { throw "TESTS_FAILED ($($proc.ExitCode))" }
    Write-Ok 'Tests passed.'
}

try {
    $repoRoot = Find-RepoRoot
    Write-Info "RepoRoot: $repoRoot"

    $defaultCfg = Join-Path $PSScriptRoot 'deploy_config.json'
    $sampleCfg  = Join-Path $PSScriptRoot 'deploy_config.sample.json'
    if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
        $ConfigPath = (Test-Path $defaultCfg) ? $defaultCfg : $sampleCfg
    }
    Write-Info "Using config: $ConfigPath"
    $cfg = Load-Json -path $ConfigPath

    if ($Rollback) {
        Write-Info 'Starting rollback: disable lad_integration and monitoring.'
        Perform-Rollback -repoRoot $repoRoot
        if (-not $SkipTests) { Run-Tests -repoRoot $repoRoot }
        if ($WhatIf) { Write-Ok 'DRYRUN_ROLLBACK_OK' } else { Write-Ok 'ROLLBACK_OK' }
        exit 0
    }

    Configure-Env -cfg $cfg
    Apply-Configs -repoRoot $repoRoot -cfg $cfg

    if (-not $SkipTests) { Run-Tests -repoRoot $repoRoot }

    if ($WhatIf) { Write-Ok 'DRYRUN_OK' } else { Write-Ok 'DEPLOY_OK' }
    exit 0
} catch {
    Write-Err ($_.Exception.Message)
    exit 1
}

