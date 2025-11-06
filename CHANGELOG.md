## [2025-11-06] 测试门禁（warnings as errors）与零告警落地
 - 启用 CI 测试门禁：pytest 全局“警告即失败”（pytest.ini 配置 `addopts = -W error`，`filterwarnings = error`）
 - 本地脚本 `run_pytests.ps1` 默认追加 `-W error`，与 CI 行为一致
 - 测试环境禁用集成文件日志写入（integrated.log），仅输出到控制台，避免 `PytestUnraisableExceptionWarning`
 - 清理遗留测试告警：将 `return True/False` 改为断言；使用 `asyncio.run(...)` 替代 `get_event_loop().run_until_complete(...)`
 - 全量回归验证通过（321 passed，0 failed，在门禁下无阻断性告警）

## [2025-09-01] 核心功能优化与文档体系标准化

### 核心功能优化
- **LAD-IMPL-004**: 完成DynamicModuleImporter优化，支持配置驱动的模块导入和函数验证
- **LAD-IMPL-005**: 完成HybridMarkdownRenderer优化，实现智能渲染策略和详细日志记录
- **LAD-IMPL-006**: 完成函数映射验证机制，支持complete/incomplete/import_failed三种状态
- **P1级别改进**: 实施缓存持久化精简和接口契约表完善

### 技术改进
- 优化core/dynamic_module_importer.py，支持缓存持久化和标准化返回格式
- 优化core/markdown_renderer.py，实现智能渲染决策和结构化日志
- 完善config/external_modules.json配置管理
- 统一错误处理和日志记录机制

### 文档体系标准化
- 创建LAD-IMPL-007到015任务完整提示词V3.2.md（39KB标准化文档）
- 建立完整的任务依赖关系与实施时机总览
- 制定文档使用关系和优先级说明
- 创建新会话执行准备方案V1.0

### 质量保证
- 完成多次深入检查复核，确保无疏漏
- 建立完整的风险控制措施
- 制定标准化的数据传递格式
- 实现向后兼容性保证

### 项目状态
- 技术基础：稳固且已验证
- 文档体系：完备且标准化
- 执行准备：就绪，可启动新会话执行LAD-IMPL-007

## [2025-08-06] 接口统一与性能监控修正
- 统一ContentViewer、MarkdownRenderer、ContentPreview等所有缓存相关组件的get_cache_info接口为{'total', 'limit', ...}。
- 主窗口性能监控与性能信息展示去除兼容性适配，直接依赖统一接口。
- 文档与接口说明同步更新。

## [2025-08-19] 4.3.4 质量保证与部署实施
- 完成方案C（混合方案）收尾：将 outputs 产物迁入主项目目录（integration/、monitoring/、benchmarks/），形成稳定包路径
- main.py 读取 config/lad_integration.json，按开关异步执行集成与监控（不阻塞UI）
- 统一监控输出目录至 metrics/，新增 retention_days 配置并生效
- 新增 QA 用例：tests/test_qa_minimal.py（最小门禁）、tests/test_qa_all.py（聚合门禁，强制UTF-8，编码防护）
- 新增并回填文档：4.3.4 计划/报告、部署前检查清单、回滚方案；新增部署样例配置（deploy_config.sample.json）
- 修复 Windows 控制台 GBK 解码问题（子进程输出 UTF-8 捕获，errors=replace），聚合用例 3 passed

#### 对齐提示词与追问回填
- 方案报告已增加“对齐提示词”声明，并按提示词结构回填“范围/目标/原则/变更清单”。
- “预设追问计划”三轮问答（完整性/深度/质量提升）均已在报告中逐条应答。

### 详细发布说明
- 更完整的变更说明请参见：`local_markdown_viewer/第二阶段实现提示词/本地Markdown文件渲染程序-重构过程-第二阶段核心功能-06_后期完善-实现提示词/outputs/发布说明_4.3.4_变更汇总.md`
