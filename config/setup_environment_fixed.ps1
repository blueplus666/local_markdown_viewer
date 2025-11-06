# LAD环境变量配置脚本
# 用于设置PYTHONPATH备选方案

param(
    [switch]$SetEnvironment,
    [switch]$RemoveEnvironment,
    [switch]$TestEnvironment,
    [switch]$BackupCurrent
)

$LAD_MODULE_PATH = "D:\lad\LAD_md_ed2"
$ENV_VAR_NAME = "PYTHONPATH"
$BACKUP_FILE = "pythonpath_backup.txt"

function Backup-CurrentEnvironment {
    Write-Host "备份当前环境变量设置..." -ForegroundColor Yellow
    
    $currentPath = [Environment]::GetEnvironmentVariable($ENV_VAR_NAME, "User")
    if ($currentPath) {
        $currentPath | Out-File -FilePath $BACKUP_FILE -Encoding UTF8
        Write-Host "✓ 当前PYTHONPATH已备份到: $BACKUP_FILE" -ForegroundColor Green
        Write-Host "当前值: $currentPath" -ForegroundColor Gray
    } else {
        "EMPTY" | Out-File -FilePath $BACKUP_FILE -Encoding UTF8
        Write-Host "✓ 当前PYTHONPATH为空，已记录" -ForegroundColor Green
    }
}

function Set-LADEnvironment {
    Write-Host "设置LAD环境变量..." -ForegroundColor Yellow
    
    # 备份当前环境
    Backup-CurrentEnvironment
    
    # 获取当前PYTHONPATH
    $currentPath = [Environment]::GetEnvironmentVariable($ENV_VAR_NAME, "User")
    
    # 检查是否已经包含LAD路径
    if ($currentPath -and $currentPath.Contains($LAD_MODULE_PATH)) {
        Write-Host "LAD路径已存在于PYTHONPATH中" -ForegroundColor Yellow
        return
    }
    
    # 构建新的PYTHONPATH
    if ($currentPath) {
        $newPath = $LAD_MODULE_PATH + ";" + $currentPath
    } else {
        $newPath = $LAD_MODULE_PATH
    }
    
    try {
        # 设置用户级环境变量
        [Environment]::SetEnvironmentVariable($ENV_VAR_NAME, $newPath, "User")
        Write-Host "✓ PYTHONPATH已设置为: $newPath" -ForegroundColor Green
        
        # 更新当前会话的环境变量
        $env:PYTHONPATH = $newPath
        Write-Host "✓ 当前会话环境变量已更新" -ForegroundColor Green
        
        Write-Host "注意: 新的环境变量将在新的PowerShell会话中生效" -ForegroundColor Cyan
    } catch {
        Write-Host "❌ 设置环境变量失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Remove-LADEnvironment {
    Write-Host "移除LAD环境变量..." -ForegroundColor Yellow
    
    $currentPath = [Environment]::GetEnvironmentVariable($ENV_VAR_NAME, "User")
    
    if (-not $currentPath) {
        Write-Host "PYTHONPATH当前为空，无需移除" -ForegroundColor Yellow
        return
    }
    
    if (-not $currentPath.Contains($LAD_MODULE_PATH)) {
        Write-Host "PYTHONPATH中未找到LAD路径，无需移除" -ForegroundColor Yellow
        return
    }
    
    # 移除LAD路径
    $pathArray = $currentPath -split ";"
    $filteredArray = $pathArray | Where-Object { $_ -ne $LAD_MODULE_PATH }
    $newPath = $filteredArray -join ";"
    
    # 如果结果为空，删除环境变量
    if ([string]::IsNullOrWhiteSpace($newPath)) {
        [Environment]::SetEnvironmentVariable($ENV_VAR_NAME, $null, "User")
        Write-Host "✓ PYTHONPATH已清空" -ForegroundColor Green
    } else {
        [Environment]::SetEnvironmentVariable($ENV_VAR_NAME, $newPath, "User")
        Write-Host "✓ PYTHONPATH已更新为: $newPath" -ForegroundColor Green
    }
    
    # 更新当前会话
    $env:PYTHONPATH = $newPath
    Write-Host "✓ 当前会话环境变量已更新" -ForegroundColor Green
}

function Test-LADEnvironment {
    Write-Host "测试LAD环境变量配置..." -ForegroundColor Yellow
    
    # 检查环境变量设置
    $userPath = [Environment]::GetEnvironmentVariable($ENV_VAR_NAME, "User")
    $sessionPath = $env:PYTHONPATH
    
    Write-Host "用户级PYTHONPATH: $userPath" -ForegroundColor Gray
    Write-Host "会话级PYTHONPATH: $sessionPath" -ForegroundColor Gray
    
    # 检查LAD路径是否存在
    if ($userPath -and $userPath.Contains($LAD_MODULE_PATH)) {
        Write-Host "✓ LAD路径存在于用户级环境变量中" -ForegroundColor Green
    } else {
        Write-Host "❌ LAD路径不存在于用户级环境变量中" -ForegroundColor Red
    }
    
    # 测试模块导入
    Write-Host "测试模块导入..." -ForegroundColor Yellow
    
    try {
        $pythonCode = @"
import sys
print('Python路径:')
for path in sys.path:
    print(f'  {path}')

try:
    import lad_markdown_viewer
    print('✓ lad_markdown_viewer模块导入成功')
    
    # 测试特定函数
    from lad_markdown_viewer import markdown_processor
    print('✓ markdown_processor子模块导入成功')
    
    if hasattr(markdown_processor, 'render_markdown_to_html'):
        print('✓ render_markdown_to_html函数可访问')
    else:
        print('❌ render_markdown_to_html函数不可访问')
        
    if hasattr(markdown_processor, 'render_markdown_with_zoom'):
        print('✓ render_markdown_with_zoom函数可访问')
    else:
        print('❌ render_markdown_with_zoom函数不可访问')
        
except ImportError as e:
    print(f'❌ 模块导入失败: {e}')
except Exception as e:
    print(f'❌ 测试过程发生错误: {e}')
"@
        
        $testResult = python -c $pythonCode
        Write-Host $testResult
    } catch {
        Write-Host "❌ Python测试执行失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Restore-Environment {
    Write-Host "恢复环境变量..." -ForegroundColor Yellow
    
    if (-not (Test-Path $BACKUP_FILE)) {
        Write-Host "❌ 备份文件不存在: $BACKUP_FILE" -ForegroundColor Red
        return
    }
    
    $backupContent = Get-Content $BACKUP_FILE -Raw
    $backupContent = $backupContent.Trim()
    
    if ($backupContent -eq "EMPTY") {
        [Environment]::SetEnvironmentVariable($ENV_VAR_NAME, $null, "User")
        $env:PYTHONPATH = $null
        Write-Host "✓ PYTHONPATH已清空（恢复到原始状态）" -ForegroundColor Green
    } else {
        [Environment]::SetEnvironmentVariable($ENV_VAR_NAME, $backupContent, "User")
        $env:PYTHONPATH = $backupContent
        Write-Host "✓ PYTHONPATH已恢复为: $backupContent" -ForegroundColor Green
    }
}

# 主执行逻辑
if ($BackupCurrent) {
    Backup-CurrentEnvironment
} elseif ($SetEnvironment) {
    Set-LADEnvironment
} elseif ($RemoveEnvironment) {
    Remove-LADEnvironment
} elseif ($TestEnvironment) {
    Test-LADEnvironment
} else {
    Write-Host "LAD环境变量管理脚本" -ForegroundColor Cyan
    Write-Host "用法:" -ForegroundColor White
    Write-Host "  .\setup_environment_fixed.ps1 -SetEnvironment     # 设置LAD环境变量" -ForegroundColor Gray
    Write-Host "  .\setup_environment_fixed.ps1 -RemoveEnvironment  # 移除LAD环境变量" -ForegroundColor Gray
    Write-Host "  .\setup_environment_fixed.ps1 -TestEnvironment    # 测试环境变量配置" -ForegroundColor Gray
    Write-Host "  .\setup_environment_fixed.ps1 -BackupCurrent      # 备份当前环境变量" -ForegroundColor Gray
    Write-Host ""
    Write-Host "恢复环境变量:" -ForegroundColor White
    Write-Host "  Restore-Environment                               # 从备份恢复" -ForegroundColor Gray
}
