# LAD环境变量简化配置脚本

param(
    [string]$Action = "help"
)

$LAD_PATH = "D:\lad\LAD_md_ed2"

switch ($Action) {
    "backup" {
        Write-Host "备份当前PYTHONPATH..." -ForegroundColor Yellow
        $current = [Environment]::GetEnvironmentVariable("PYTHONPATH", "User")
        if ($current) {
            $current | Out-File "pythonpath_backup.txt" -Encoding UTF8
            Write-Host "已备份到 pythonpath_backup.txt" -ForegroundColor Green
        } else {
            "EMPTY" | Out-File "pythonpath_backup.txt" -Encoding UTF8
            Write-Host "当前PYTHONPATH为空，已记录" -ForegroundColor Green
        }
    }
    
    "set" {
        Write-Host "设置LAD环境变量..." -ForegroundColor Yellow
        $current = [Environment]::GetEnvironmentVariable("PYTHONPATH", "User")
        
        if ($current -and $current.Contains($LAD_PATH)) {
            Write-Host "LAD路径已存在" -ForegroundColor Yellow
        } else {
            if ($current) {
                $newPath = $LAD_PATH + ";" + $current
            } else {
                $newPath = $LAD_PATH
            }
            
            [Environment]::SetEnvironmentVariable("PYTHONPATH", $newPath, "User")
            Write-Host "PYTHONPATH已设置为: $newPath" -ForegroundColor Green
        }
    }
    
    "test" {
        Write-Host "测试环境变量配置..." -ForegroundColor Yellow
        $userPath = [Environment]::GetEnvironmentVariable("PYTHONPATH", "User")
        Write-Host "用户PYTHONPATH: $userPath" -ForegroundColor Gray
        
        if ($userPath -and $userPath.Contains($LAD_PATH)) {
            Write-Host "✓ LAD路径存在于环境变量中" -ForegroundColor Green
        } else {
            Write-Host "❌ LAD路径不存在于环境变量中" -ForegroundColor Red
        }
    }
    
    "remove" {
        Write-Host "移除LAD环境变量..." -ForegroundColor Yellow
        $current = [Environment]::GetEnvironmentVariable("PYTHONPATH", "User")
        
        if ($current -and $current.Contains($LAD_PATH)) {
            $paths = $current -split ";"
            $filtered = $paths | Where-Object { $_ -ne $LAD_PATH }
            $newPath = $filtered -join ";"
            
            if ($newPath) {
                [Environment]::SetEnvironmentVariable("PYTHONPATH", $newPath, "User")
                Write-Host "PYTHONPATH已更新为: $newPath" -ForegroundColor Green
            } else {
                [Environment]::SetEnvironmentVariable("PYTHONPATH", $null, "User")
                Write-Host "PYTHONPATH已清空" -ForegroundColor Green
            }
        } else {
            Write-Host "未找到LAD路径，无需移除" -ForegroundColor Yellow
        }
    }
    
    default {
        Write-Host "LAD环境变量管理脚本" -ForegroundColor Cyan
        Write-Host "用法: .\environment_setup_simple.ps1 [Action]" -ForegroundColor White
        Write-Host "  backup  - 备份当前环境变量" -ForegroundColor Gray
        Write-Host "  set     - 设置LAD环境变量" -ForegroundColor Gray
        Write-Host "  test    - 测试环境变量配置" -ForegroundColor Gray
        Write-Host "  remove  - 移除LAD环境变量" -ForegroundColor Gray
    }
}
