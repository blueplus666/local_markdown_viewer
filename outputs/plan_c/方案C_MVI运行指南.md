### 方案C：混合方案 — 最小可行接入（MVI）运行指南

#### 1. 开关配置
- 路径：`local_markdown_viewer/config/lad_integration.json`
- 默认：
```json
{
  "enabled": false,
  "monitoring": { "enabled": false, "interval_seconds": 30 }
}
```
- 打开最小接入：将 `enabled` 与 `monitoring.enabled` 改为 `true`

#### 2. 运行主程序
- 正常启动 `local_markdown_viewer/main.py`
- 若开启监控：指标与告警将写入 `local_markdown_viewer/metrics/bridge/`

#### 3. 恢复/回滚
- 任意时刻将 `enabled` 或 `monitoring.enabled` 置为 `false` 即停用
- 不移动 `outputs` 产物，主系统保持最小侵入

#### 4. 最小验证（可选）
- 运行测试：`pytest local_markdown_viewer/tests/test_plan_c_mvi.py -q`
- 期望：
  - 默认关闭时不抛异常
  - 开启后自动创建 `metrics/bridge/` 目录

