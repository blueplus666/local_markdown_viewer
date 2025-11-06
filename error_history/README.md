# 错误历史持久化子系统使用指南

## 概述

错误历史持久化子系统是本地Markdown文件渲染器的一个配套子系统，用于管理和分析应用程序运行过程中的错误信息。该子系统提供持久化存储、查询分析、可视化展示等功能，帮助开发者更好地理解和解决系统问题。

## 主要功能

### 1. 错误数据持久化
- 自动捕获并存储系统运行中的错误信息
- 支持结构化存储，包括错误类型、严重程度、上下文信息等
- 提供高效的数据库存储机制

### 2. 数据查询和检索
- 支持多条件组合查询（时间范围、严重程度、模块等）
- 提供分页查询和排序功能
- 支持模糊搜索和精确匹配

### 3. 统计分析
- 实时错误统计和趋势分析
- 按严重程度、分类、模块等多维度统计
- 错误解决率和平均解决时间分析

### 4. 数据可视化
- 错误趋势图表展示
- 统计数据的图形化呈现
- 交互式数据浏览界面

### 5. 系统管理
- 数据库维护和优化
- 数据备份和恢复
- 配置管理和热重载
- 自动数据清理

## 安装和配置

### 依赖要求
- Python 3.8+
- PyQt5
- SQLite3 (Python标准库)

### 安装步骤
1. 确保主系统已正确安装
2. 子系统会随主系统自动集成，无需额外安装

### 配置说明
子系统配置文件位于 `config/features/error_history.json`：

```json
{
  "version": "1.0",
  "enabled": true,
  "database": {
    "path": "data/error_history.db",
    "max_connections": 5,
    "timeout_seconds": 30
  },
  "retention": {
    "days": 90,
    "auto_cleanup": true
  }
}
```

## 使用方法

### 1. 通过主系统菜单访问

启动本地Markdown文件渲染器，在菜单栏选择 **"错误历史(&E)"** 子菜单：

- **查询错误历史(&Q)**: 打开错误查询界面
- **错误统计(&S)**: 查看错误统计信息
- **错误分析(&A)**: 进行错误趋势分析
- **系统管理(&M)**: 管理数据库和配置

### 2. 独立运行

也可以直接运行子系统（主要用于测试）：

```bash
# 从项目根目录运行
python error_history/error_history_standalone.py [mode]

# mode 参数：
# query - 查询模式（默认）
# statistics - 统计模式
# analysis - 分析模式
# management - 管理模式
```

### 3. 编程接口

```python
from error_history.core.manager import ErrorHistoryManager
from error_history.core.models import ErrorRecord, ErrorSeverity

# 创建管理器
manager = ErrorHistoryManager()

# 保存错误
error = ErrorRecord(
    error_id="ERR_001",
    error_type="ValueError",
    error_message="Invalid input value",
    severity=ErrorSeverity.MEDIUM,
    category=ErrorCategory.VALIDATION
)
manager.save_error(error)

# 查询错误
errors = manager.query_errors(
    filters={'severity': ErrorSeverity.HIGH},
    limit=100
)

# 获取统计
stats = manager.get_statistics()
```

## 数据模型

### ErrorRecord（错误记录）
- `error_id`: 错误唯一标识
- `error_type`: 错误类型（如 ValueError, IOError等）
- `error_message`: 错误消息
- `severity`: 严重程度（LOW/MEDIUM/HIGH/CRITICAL）
- `category`: 错误分类（系统/文件/网络/配置等）
- `module`: 发生错误的模块
- `function`: 发生错误的函数
- `line_number`: 错误行号
- `stack_trace`: 完整的堆栈跟踪
- `context`: 错误上下文信息
- `created_at`: 创建时间
- `resolved`: 是否已解决
- `resolution_time`: 解决耗时

## 界面说明

### 查询界面
- **过滤条件**: 支持按日期、严重程度、分类、模块等条件过滤
- **结果列表**: 显示匹配的错误记录
- **详情面板**: 显示选中错误的完整信息
- **操作功能**: 支持标记解决状态、删除记录等

### 统计界面
- **概览卡片**: 显示总错误数、解决率等关键指标
- **趋势图表**: 按时间显示错误数量变化
- **分布统计**: 按严重程度、分类等维度的分布情况

### 分析界面
- **模式识别**: 自动识别常见的错误模式
- **根本原因分析**: 基于堆栈跟踪进行原因分析
- **影响评估**: 评估错误对系统的影响程度

### 管理界面
- **配置管理**: 修改数据库路径、清理策略等配置
- **数据库维护**: 优化数据库、备份数据、清理过期记录
- **系统监控**: 查看数据库状态、连接信息等

## 清理调度与热重载

### 配置字段
- `retention.days`: 数据保留天数（默认 90）
- `retention.auto_cleanup` 或顶层 `auto_cleanup`: 是否启用自动清理（默认启用）
- `cleanup_schedule`: 清理计划，支持两种格式：
  - `@every 10s` / `@every 5m` / `@every 1h` 等间隔模式
  - 简化 cron：`m h * * *`（分钟 小时），例如 `0 2 * * *` 表示每天 02:00 执行

示例（features/error_history.json）：

```json
{
  "enabled": true,
  "database": { "path": "data/error_history.db", "max_connections": 5, "timeout_seconds": 30 },
  "retention": { "days": 90, "auto_cleanup": true },
  "cleanup_schedule": "0 2 * * *"
}
```

### 配置来源优先级
1. `config/features/error_history.json`（推荐，结构化嵌套）
2. `config/error_handling.json`（兼容扁平结构，会自动映射到内部结构）
3. 历史通路：`ConfigManager.get_config('features.error_history')`
4. 数据库表 `system_config` 中保存的配置

### 热重载机制
- 默认轮询：每 2 秒检测上述配置文件的修改时间（mtime），发现变化后自动 `reload_config()` 并应用。
- 事件监听（可选）：若安装 `watchdog`，将使用文件系统事件驱动，响应更及时。
  - 安装方式（可选）：`pip install watchdog`

### 管理面板操作
- **立即清理**：立刻按 `retention.days` 清理过期数据。
- **重启调度器**：在修改计划或开关 `auto_cleanup` 后一键重启调度器。
- **刷新状态**：查看是否启用、是否运行中、上次/下次执行时间、计划表达式与模式（interval/daily）。

### 注意事项
- 修改 `database.path` 等底层参数可能需要重启子系统才能完全生效。
- 多实例/多进程场景建议引入分布式锁或“每日一次”标记，避免重复清理。

## 性能和监控

### 性能指标
- **查询响应时间**: < 100ms（正常查询）
- **存储延迟**: < 50ms（错误保存）
- **内存占用**: < 50MB（UI界面）
- **数据库大小**: 根据错误数量动态调整

### 监控功能
- 数据库连接状态监控
- 存储空间使用率监控
- 错误记录性能监控
- 自动告警和通知

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库文件路径权限
   - 确认SQLite3可用性
   - 查看错误日志获取详细信息

2. **查询无结果**
   - 检查过滤条件是否过于严格
   - 确认时间范围设置正确
   - 验证数据库中是否有数据

3. **界面无法打开**
   - 确认PyQt5已正确安装
   - 检查Python版本兼容性
   - 查看控制台错误信息

4. **配置不生效**
   - 确认配置文件格式正确
   - 重启应用程序以应用配置变更
   - 检查配置文件权限

### 日志位置
- 主系统日志: `logs/lad_markdown_viewer.log`
- 错误历史相关日志会输出到主日志文件

## 技术支持

如遇到问题，请：

1. 查看应用程序日志获取错误信息
2. 检查配置文件是否正确
3. 确认所有依赖都已安装
4. 联系技术支持团队

## 更新记录

### v1.0.0 (2025-10-20)
- 初始版本发布
- 实现基础的错误历史持久化功能
- 提供查询、统计、分析、管理四大功能模块
- 支持与主系统的无缝集成
