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
function Write-Err([string]$msg)  { Write-Host "[ERR ] $msg" -ForegroundColor Red }

try {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $nestedRel = '第二阶段实现提示词\本地Markdown文件渲染程序-重构过程-第二阶段核心功能-06_后期完善-实现提示词\outputs\deploy\deploy.ps1'
    $nested = Join-Path $scriptDir $nestedRel

    if (-not (Test-Path $nested)) { throw "NESTED_DEPLOY_NOT_FOUND: $nestedRel" }

    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'

    $argsSplat = @{}
    # Default to root-level deploy_config.json if not provided
    if ($PSBoundParameters.ContainsKey('ConfigPath')) {
        $argsSplat['ConfigPath'] = $ConfigPath
    } else {
        $rootCfg = Join-Path $scriptDir 'deploy_config.json'
        if (Test-Path $rootCfg) { $argsSplat['ConfigPath'] = $rootCfg }
    }
    if ($PSBoundParameters.ContainsKey('SkipTests'))  { $argsSplat['SkipTests']  = $SkipTests }
    if ($PSBoundParameters.ContainsKey('WhatIf'))     { $argsSplat['WhatIf']     = $WhatIf }
    if ($PSBoundParameters.ContainsKey('Rollback'))   { $argsSplat['Rollback']   = $Rollback }

    Write-Info "Forwarding to nested deploy: $nestedRel"
    & $nested @argsSplat
    exit $LASTEXITCODE
} catch {
    Write-Err ($_.Exception.Message)
    exit 1
}

