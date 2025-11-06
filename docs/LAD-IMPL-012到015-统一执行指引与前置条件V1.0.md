# LAD-IMPL-012到015 统一执行指引与前置条件 V1.0

- 文档版本: V1.0
- 适用范围: 012（链接接入，简化版）、013（安全）、014（体验）、015B（链接验收）、015（自动化诊断-并行轨）
- 架构基线: V4.0 简化配置架构（006B后）

---

## 1. 执行目标与总览

- **[主线目标]** 完成链接处理主线 012→013→014→015B 的稳定落地，形成可验收的功能与测试闭环。
- **[并行轨]** 015 自动化诊断作为并行轨提供支持，不阻塞 015B（链接验收）。
- **[支线]** 012 并发测试为可选支线，为 013/014/015 提供辅助数据；缺依赖时允许跳过。

---

## 2. 前置条件（Preflight Checks）

- **[配置存在性]**
  - 优先 `config/app_config.json` 中存在 `link_processing` 段；否则检查 `config/features/link_processing.json` 与 `config/features/security.json`。
  - 存在 `config/runtime/performance.json`（阈值配置）；若无，使用 `config/features/logging.json` 中 `performance` 作为兜底。
  - （可选）`config/features/diagnostics.json` 用于 015；缺失不阻塞主线。
  - （建议）`config/features/error_history.json` 用于 011 错误历史持久化开关与可观测性；缺失可临时使用内置默认，建议补齐最小配置（见附录）。
- **[关键代码文件]** 必须存在且可导入：
  - `core/link_processor.py`、`ui/content_viewer.py`
  - `core/performance_metrics.py`、`utils/config_manager.py`
  - `error_history/core/manager.py`
- **[UI注入路径]** `ui/content_viewer.py` 中 LPCLICK 路径：`_on_page_load_finished()` 注入脚本 → `javaScriptConsoleMessage` → `_handle_lpclick()` → `LinkProcessor.process_link()` → `_execute_link_action()`。
- **[初始化顺序检查]** `ui/main_window.py::initialize_architecture_components()`：先构造 `dynamic_importer` 再注入依赖；`ApplicationStateManager` 初始化不应受条件分支影响。
- **[安全默认]** fail-closed：
  - 外部链接默认进行协议/域名校验；
  - 文件链接默认 `check_exists = true`；
  - 不允许“默认放开”。
- **[依赖与工具]**
  - 必需：`pytest`。
  - 可选：`pytest-xdist`、`pytest-asyncio`、`locust`、`watchdog`、`openpyxl`、`psutil`、`beautifulsoup4`。
  - 若 `requirements.txt` 无可选依赖，不作为失败条件；仅输出建议。

---

## 3. AI 执行守则（防疏漏）

- **[顺序]** 先配置与路径校验，再执行代码或文档修改；缺项先补齐最小配置（文档+样例），避免直接改核心逻辑。
- **[兼容]** 配置读取示例需优先 `app`，其次 `features`，保持向后兼容。
- **[审计]** 任何“阈值/安全策略”的变更须在提交信息与本指引的“变更记录”中标注。
- **[跳过策略]** 对于并发测试或不可用依赖，标注“跳过”，写入 `docs/execution_log.jsonl`，不阻断主线。
- **[产物]** 统一产出：
  - 人工可读：`*.md`
  - 机器可读：`*.json`/`*.jsonl`

---

## 4. 任务分解与验收点

### 4.1 LAD-IMPL-012（链接接入，简化版）
- **实施要点**
  - 修正策略读取：`LinkProcessor` 读取顺序 `app.link_processing` → `features/link_processing.json`；加载 `features/security.json`。
  - 强制 fail-closed：外部链接一律校验；文件链接 `check_exists=true`；修正 `should_validate_url` 判定。
  - `ContentViewer` 统一采用 LPCLICK 注入路径，移除旧轮询/重复注入路径。
  - 对齐 `PerformanceMetrics` 与 `runtime/performance.json` 的阈值来源。
- **测试要点**
  - URL 校验（协议/域名白名单、黑名单）
  - 相对路径解析、`file://` 解析、锚点滚动
  - 动作路由（打开文件/外链/目录/锚点）
  - fail-closed 行为验证
- **产物**
  - `docs/012-执行报告.md`
  - `tests/test_link_processor_minimal.py`
  - `docs/012-metrics-samples.json`

### 4.2 LAD-IMPL-013（安全）
- **实施要点**
  - 定义并启用 `features/security.json`（协议白名单、域名白名单/黑名单、路径与模式限制）。
  - `LinkValidator` 完整化：scheme/domain/path/query/fragment 校验；重定向深度限制；危险属性过滤。
  - 安全日志与审计事件：结构化输出，计数与聚合。
- **测试要点**
  - 协议白名单、域名白/黑名单命中与拒绝
  - 风险链接阻断与记录
  - 安全审计事件格式与留存策略
- **产物**
  - `config/features/security.json`
  - `tests/test_link_security_rules.py`
  - `docs/013-安全规则说明.md`

### 4.3 LAD-IMPL-014（体验）
- **实施要点**
  - 链接预览（超时/大小限制）、加载状态、错误提示优化
  - 性能埋点：P50/P90/P99 时延、并发检查数、缓存命中率、错误/重试率
- **测试要点**
  - 预览超时与大小限制
  - 指示器/状态栏更新频率与阈值
- **产物**
  - `docs/014-体验优化说明.md`
  - `tests/test_link_preview_and_ux.py`

### 4.4 LAD-IMPL-015B（链接验收）
- **实施要点**
  - 端到端测试清单：配置热更新、路径解析全类、动作路由、审计与性能门限
- **验收要点**
  - 功能、性能、安全三类通过率达到标准
- **产物**
  - `docs/015B-验收报告.md`
  - `tests/test_link_e2e_acceptance.py`

### 4.5 LAD-IMPL-015（自动化诊断，并行轨）
- **实施要点**
  - `DiagnosticsManager` 整合链接处理诊断项：验证规则、性能指标、审计一致性
  - 配置：`features/diagnostics.json`（优先），`app.diagnostics`（兜底）
- **产物**
  - `docs/015-诊断方案.md`
  - `tests/test_link_processing_diagnostics.py`

---

## 5. 执行顺序与跳过/恢复

- **建议顺序**：Preflight → 012 → 013 → 014 → 015B；015 并行推进。
- **跳过条件**：并发测试缺依赖、诊断缺可选依赖等。
- **记录要求**：在 `docs/execution_log.jsonl` 按 JSON Lines 记录 `{ task, action, reason, timestamp }`。
- **恢复策略**：补齐依赖/配置后直接恢复相应步骤；报告以追加方式存档。

---

## 6. 产物与存档

- 报告：`docs/012-*.md`、`docs/013-*.md`、`docs/014-*.md`、`docs/015B-*.md`、`docs/015-*.md`
- 测试：`tests/test_link_*.py` 系列
- 配置：`config/features/link_processing.json`、`config/features/security.json`、`config/features/diagnostics.json`（可选）、`config/features/error_history.json`（建议）
- 指标样例：`docs/012-metrics-samples.json`

---

## 7. 常见问题（FAQ）

- Q: `features/` 下的配置缺失？
  - A: 可临时使用 `app_config.json` 中的同名段落，后续再拆分迁移到 `features/`。
- Q: 性能阈值以哪个为准？
  - A: 优先 `runtime/performance.json`；其次 `features/logging.json` 内 `performance`。
- Q: 自动化诊断是否阻塞 015B？
  - A: 否。015 与 015B 并行，互相增强但不阻塞。

---

## 8. 变更记录

- 2025-10-22：创建本统一执行指引，明确主线/并行/支线关系；补充前置检查与跳过/恢复策略；规范产物与可观测性要求。

---

## 附录：features/error_history.json 最小配置示例

```json
{
  "error_history": {
    "enabled": true,
    "retention_days": 30,
    "storage": "jsonl",
    "export_xlsx": false
  }
}
```
