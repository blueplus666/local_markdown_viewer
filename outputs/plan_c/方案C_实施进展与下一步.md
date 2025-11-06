### 方案C：混合方案 — 实施进展与下一步

- 项目根目录：`D:/lad/LAD_md_ed2/local_markdown_viewer/`
- 生成时间：2025-08-19

---

### 一、当前实施进展（基于仓库实际状态）

- 独立工具集已就绪（位于：`第二阶段实现提示词/.../outputs/`）：
  - 集成协调：`system_integration_coordinator.py`
  - 监控部署：`monitoring_system_deployer.py`
  - 性能基线：`performance_benchmark_tester.py`
  - 链接预备：`link_processor_integration_preparer.py`
  - 对比分析：`comparison_analysis_tool.py`
  - 测试验证：`integration_test_suite.py`, `validation_test.py`, `mock_dependencies.py`
  - 配置：`deployment_config.json`
  - 文档：`系统集成与监控工具集-技术文档.md`, `README.md`
  - 报告数据：`integration_test_report.json`, `validation_report.json`, `monitoring_data/`

- 主系统侧（`local_markdown_viewer/`）尚未发现直接引用：
  - 未检出 `SystemIntegrationCoordinator` 在 `main.py` 等入口处的导入/调用
  - 监控部署器当前仅在 `outputs` 内用于测试脚本中被引用

结论：方案C按“先独立闭环、再控步集成”的策略已完成独立闭环，就绪度高；尚需落地主系统集成与最小接入验证。

---

### 二、最小可行集成（MVI）计划

目标：在不破坏现有功能的前提下，使主系统具备最小监控与集成能力开关。

步骤：
1) 在主系统创建目录（不移动outputs产物）：
   - `local_markdown_viewer/monitoring/`（放置薄封装与接口桥）
   - `local_markdown_viewer/integration/`（放置启动钩子与协调桥）
2) 薄封装桥接：
   - 在 `integration/bridge.py` 内以相对导入形式调用 `outputs/system_integration_coordinator.py`
   - 在 `monitoring/bridge.py` 内以相对导入形式调用 `outputs/monitoring_system_deployer.py`
3) 入口接入：
   - 在 `main.py` 增加可选启动：读取配置后，按需 `await bridge.integrate_all_modules()`；监控以独立异步任务或独立进程启动
4) 可配置与回滚：
   - `config/lad_integration.json` 新增总开关与采样率、阈值；默认关闭，便于回滚
5) 验证：
   - 运行最小场景，检查日志/指标写入与UI无阻塞

---

### 三、下一步详细任务（按优先级）

1. 配置与开关
   - 新增 `config/lad_integration.json`（默认 `enabled=false`）
   - 与 `deployment_config.json` 对齐关键项（interval、阈值、存储路径）

2. 集成协调最小接入
   - 在 `local_markdown_viewer/integration/bridge.py` 提供：`async def integrate_if_enabled()`
   - 在 `main.py` 启动路径调用：`await integrate_if_enabled()`

3. 监控最小接入
   - 在 `local_markdown_viewer/monitoring/bridge.py` 提供：`async def start_monitoring_if_enabled()`
   - 以低频、低开销模式启动，写入 `local_markdown_viewer/metrics/`

4. CI最低保障
   - 增加一个轻量用例：应用启动→渲染一个小MD→落地一条指标
   - 失败即回滚（开关关闭）

5. 文档与运行手册
   - 在 `outputs/plan_c/` 下补充《运行接入指南（MVI）》与常见故障

---

### 四、完成定义（DoD）

- 本地默认配置为关闭，不影响现网功能
- 打开 `enabled=true` 后：
  - 协调器成功运行，模块状态可记录
  - 监控每≥30s写入一次指标，CPU/内存占用不超过既定阈值
  - 关闭后恢复到接入前状态

---

### 五、风险与缓解

- 风险：事件循环阻塞、文件IO开销、路径相对导入失败
- 缓解：异步/线程池隔离、按需采样、路径基于 `Path(__file__)` 计算、默认关闭开关

