# 部署目录（4.3.4）

- deploy_config.sample.json：部署配置样例，包含集成开关、监控频率/保留、CI建议
- 建议：在CI中设置 `PYTHONUTF8=1` 以规避GBK控制台编码问题

## 使用说明

- 快速入口（项目根级）：
  ```powershell
  # 从仓库根或 local_markdown_viewer 目录执行均可
  ./local_markdown_viewer/deploy.ps1
  # 或指定配置路径（优先使用 outputs/deploy/deploy_config.json，不存在则回退 sample）
  ./local_markdown_viewer/deploy.ps1 -ConfigPath ./local_markdown_viewer/第二阶段实现提示词/本地Markdown文件渲染程序-重构过程-第二阶段核心功能-06_后期完善-实现提示词/outputs/deploy/deploy_config.sample.json
  ```

- 深层部署脚本直接调用：
  ```powershell
  ./local_markdown_viewer/第二阶段实现提示词/本地Markdown文件渲染程序-重构过程-第二阶段核心功能-06_后期完善-实现提示词/outputs/deploy/deploy.ps1 [-ConfigPath <path>] [-SkipTests] [-WhatIf] [-Rollback]
  ```

- 说明：
  - 默认会运行聚合门禁测试（`tests/test_qa_all.py`），可用 `-SkipTests` 跳过。
  - 运行前会自动设置 `PYTHONUTF8=1` 与 `PYTHONIOENCODING=utf-8`，避免 Windows 控制台编码问题。
  - 脚本会备份被覆盖的目标文件到 `backups/` 目录（同仓库内）。
  - 使用 `-WhatIf` 进行干跑，仅打印将要执行的变更（仍会执行测试，若要完全跳过测试，追加 `-SkipTests`）。
  - 使用 `-Rollback` 执行标准回退：自动将 `config/lad_integration.json` 中 `enabled=false`、`monitoring.enabled=false` 并备份原文件。