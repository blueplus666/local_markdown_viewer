# 发布概要 - 2025-11-06

## 主题
- 启用测试门禁：pytest “Warnings as Errors”（警告即失败），实现零告警标准化回归

## 关键变更
- pytest 门禁：在 `pytest.ini` 启用 `addopts = -W error` 与 `filterwarnings = error`
- 本地脚本一致性：`run_pytests.ps1` 默认追加 `-W error`
- 测试环境日志策略：禁用 `integrated.log` 文件写入，仅控制台输出（检测 `LAD_TEST_MODE=1`、`PYTEST_CURRENT_TEST` 或 `pytest` 模块）
- 测试用例清理：
  - 将返回值 `return True/False/...` 改为断言，消除 `PytestReturnNotNoneWarning`
  - 使用 `asyncio.run(...)` 替代 `get_event_loop().run_until_complete(...)`

## 验证结果
- 全量回归（在门禁下）：321 passed，0 failed，未见阻断性告警
- 定向用例：函数映射、线程安全、配置访问与链路处理相关集均为绿色

## 使用说明
- 标准执行：
  - 直接运行 `pytest` 即默认“警告即失败”（由 `pytest.ini` 生效）
  - 或运行 `./run_pytests.ps1`（已默认 `-W error`）
- 本地临时放宽（仅调试，不用于 CI）：
  - 可在命令行覆盖为 `-W default` 以排查告警根因

## 开发注意事项
- 测试函数必须使用断言，不返回布尔/对象
- 异步测试统一使用 `asyncio.run`
- 关闭文件句柄/资源/线程，避免资源类告警被升级为错误

## 影响评估
- 通过门禁前的测试告警已清理，现有实现与配置保持向后兼容
- 门禁将提升持续集成质量，低风险

## 关联文档
- CHANGELOG: 根目录 `CHANGELOG.md`（“2025-11-06 测试门禁与零告警落地”节）
- 013 计划文档：`docs/013-前置与并行计划.md`（“八、CI/测试门禁：Warnings as Errors”）
