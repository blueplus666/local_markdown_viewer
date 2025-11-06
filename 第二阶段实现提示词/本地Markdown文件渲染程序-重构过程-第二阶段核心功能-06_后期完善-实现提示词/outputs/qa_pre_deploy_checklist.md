# 部署前检查清单（4.3.4）

- 配置：`config/lad_integration.json` 已按环境校准（enabled/interval/retention）
- 报告：`integration_test_report.json`、`validation_report.json` 成功率 100%
- 监控：`metrics/` 可写、空间充足（≥ 1GB 预留），`reports/`、`errors/` 目录存在
- 日志：`logs/` 目录写权限，日志轮转策略生效
- 权限：无管理员权限依赖，无敏感路径写入
- 回滚：演练通过（见回滚方案文件），可在1分钟内切回
- 备份：重要配置/数据已备份，并记录位置

