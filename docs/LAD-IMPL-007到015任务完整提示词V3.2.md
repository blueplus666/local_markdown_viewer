# LAD-IMPL-007到015任务完整提示词V3.2

**文档版本**: V3.7  
**创建时间**: 2025-09-01 17:46:32  
**更新时间**: 2025-09-26 15:45:00  
**模板依据**: 《增强版大型提示词分解计划模板V3.0》  
**适用范围**: LAD本地Markdown渲染器项目  
**更新说明**: 
- V3.2: 最终完善了遗漏的关键资料和文档整合，细化了性能基准指标和代码质量标准
- V3.3: 补充线程安全实现方案到006A任务，详细化009任务测试场景，完善014任务性能基准值
- V3.7: **深度疏漏修复**：基于外部分析修复5个关键疏漏（PerformanceMetrics详细实现、组件初始化顺序、线程安全优先级歧义、测试覆盖率定义、配置文件格式）
- V3.4: 完善006A任务必需输入文件清单，补充线程安全实现专项文档，详细化文档使用说明
- V3.5: 在具体实施要求中明确引用线程安全清单，确保实现时严格按照清单执行
- V3.6: 完善任务目标、前序数据摘要、下一步准备和预设追问计划，全面强化线程安全要求  

---

## 文档说明

本文档提供LAD-IMPL-007到015任务的完整提示词，严格遵循V3.0模板标准，包含：
- 完整的会话元数据
- 标准化的预设追问计划
- 结构化的下一步准备要求
- 明确的数据传递格式

---

## V2.0/架构修正方案联动说明与锚点

为确保本提示词集（007-015）与已确认的“第1份：架构修正方案（V2.0）”保持强一致性，以下为跨任务的联动要求与锚点指引。所有任务在输出与实现时，均需引用并遵循这些锚点。

### A. 全局联动要点（适用于007-015）
- 状态与快照统一：运行态状态取自`ApplicationStateManager`，持久/恢复取自`SnapshotManager`。
- 配置唯一事实来源：外部模块路径等以`config/external_modules.json`为唯一来源；`app_config.json`相关字段空置或仅作默认。
- 错误码与严重度：使用标准化错误码集合（导入/渲染/链接），并记录严重度与可恢复性。
- 性能指标：统一通过`PerformanceMetrics`收集导入/渲染/链接/UI关键指标；持久化交由`UnifiedCacheManager`。
- 日志字段命名统一：关键字段包括`module`、`renderer_type`、`function_mapping_status`、`missing_functions`、`non_callable_functions`、`used_fallback`、`error_code`、`reason`、`duration_ms`、`path`。

### B. 核心模块引用锚点
- 状态管理器：`core/application_state_manager.py`（接口：get_/update_ for module/render/link）。
- 快照管理器：`core/snapshot_manager.py`（接口：save_/get_ for module/render/link）。
- 导入器：`core/dynamic_module_importer.py`（接口：import_module、get_last_import_snapshot、generate_function_mapping_report）。
- 渲染器：`core/markdown_renderer.py`（接口：get_last_render_snapshot、渲染决策快照记录）。
- 缓存：`core/unified_cache_manager.py`（JSON安全落盘、关停节流、快照水合）。
- 配置：`utils/config_manager.py`、`config/external_modules.json`。
- 配置验证：`core/config_validator.py`（新增，任务009主交付）。
- 错误处理：`core/enhanced_error_handler.py`（错误码映射、结构化记录）。
- 性能：`core/performance_metrics.py`（新增，任务011主交付）。

### C. 任务级锚点对照表
- 007（UI状态栏）：数据源取`get_last_import_snapshot()`与`get_last_render_snapshot()`快照；颜色规则与文案严格映射`function_mapping_status`与`renderer_type`。
- 008（日志系统增强）：统一日志字段与上下文注入；接入错误码与性能指标；新增“快照-日志-状态”三方关联ID。
- 009（配置冲突检测）：以`external_modules.json`为准，增加冲突检测与自动修复策略；在启动阶段输出一致性报告。
- 010（错误处理标准化）：错误码域与严重度分级，UI与日志一致；导入/渲染/链接三域覆盖。
- 011（性能监控）：建立指标字典、采集点与基线；输出阶段性性能报告。
- 012（链接处理-接入）：状态与快照并行模型扩展至链接域；日志与安全策略落地。
- 013（链接处理-安全）：安全策略与白名单/黑名单校验；高危外链拦截与日志预警。
- 014（链接处理-体验）：UI交互与预览策略优化；性能与可用性权衡。
- 015（链接处理-验收）：端到端用例矩阵与最终验收基准。

### D. 文档与输出锚点
- 设计文档：`docs/架构设计修正方案.md`、`本地Markdown文件渲染程序-详细设计.md`（已补充“模块矩阵/差异对账/演进路线/测试矩阵”）。
- 过程文档：`docs/第1份-架构修正方案完整细化过程文档.md`、对应检查清单。
- 任务补充：`docs/LAD-IMPL-007任务补充说明V2.0.md`、`docs/任务依赖关系与实施时机总览V2.0.md`。
- 后续每份任务（第2份起）均需生成同类过程文档并分段追加保存。

---

## LAD-IMPL-006A: 架构修正方案实施 - 完整提示词

```
# LAD本地Markdown渲染器架构修正方案实施任务

## 会话元数据
- 任务ID: LAD-IMPL-006A
- 任务类型: 架构重构
- 复杂度级别: 复杂
- 预计交互: 10-12次
- 依赖任务: LAD-IMPL-006, P1级别改进
- 风险等级: 高风险

## 前序数据摘要
### LAD-IMPL-006关键成果
1. 函数映射验证机制已完成，支持complete/incomplete/import_failed三种状态
2. 接口契约表已定义，import_module()返回标准化字段
3. 缓存优化已完成，避免序列化警告

### P1级别改进成果
1. 缓存持久化精简已实施，创建可序列化的缓存数据
2. 接口契约表已添加到LAD-IMPL-006任务完成报告

### 线程安全实现方案准备
1. 线程安全实现详细清单已完成，包含完整的代码实现和测试用例
2. ApplicationStateManager、SnapshotManager、UnifiedCacheManager的线程安全设计已完成
3. 并发测试场景和验证标准已建立

## 任务背景
根据《第1份-架构修正方案完整细化过程文档.md》和《第1份-架构修正方案实施检查清单.md》，实施统一状态管理和快照系统，为LAD-IMPL-007及后续任务提供稳定的架构基础。**重要**：本任务必须严格按照线程安全实现详细清单执行，确保所有组件的并发安全性。

## 本次任务目标
1. 创建ApplicationStateManager统一状态管理器（含线程安全实现）
2. 创建SnapshotManager快照管理器（含线程安全实现）
3. 扩展UnifiedCacheManager原子操作（含线程安全实现）
4. 创建ConfigValidator配置验证器
5. 创建PerformanceMetrics性能指标收集器
6. 标准化错误码体系
7. 建立状态与快照的统一模型
8. **实施完整的线程安全机制**（重要目标）

## 具体实施要求

### 1. 前置验证和架构确认

#### 1.1 核心架构设计文档分析
1. **完整阅读架构设计文档**：
   - `docs/第1份-架构修正方案完整细化过程文档.md`（2106行，v1.1）
     - 理解状态与快照统一模型（第30-102行）
     - 掌握ApplicationStateManager完整接口规范（第104-236行）
     - 掌握SnapshotManager完整接口规范（第238-428行）
     - 理解配置冲突检测机制（第430-616行）
     - 掌握错误码标准化体系（第618-813行）
     - 理解性能监控架构（第815-1094行）
     - **重要**：学习线程安全实现方案补充（第二十一节）
     - **重要**：理解详细测试场景设计补充（第二十二节）

2. **系统整体架构设计参考**：
   - `本地Markdown文件渲染程序-详细设计.md`（1327行，v2.1）
     - 理解系统整体架构图和模块关系
     - 掌握线程安全设计（第十二节）
     - 理解详细测试场景设计（第十三节）

3. **架构修正指导**：
   - `docs/架构设计修正方案.md`（404行，v1.1）
     - 理解统一状态管理架构
     - 掌握线程安全实现补充（第七节）
     - 理解性能基准详细化（第八节）

#### 1.2 线程安全实现专项学习（🚨 关键）
**必须完整学习**：`docs/LAD-IMPL-006A架构修正方案实施-线程安全实现详细清单.md`（1031行，v1.0）
   - **ApplicationStateManager线程安全实现**（完整代码实现）
   - **SnapshotManager线程安全实现**（完整代码实现）
   - **UnifiedCacheManager原子操作扩展**（完整代码实现）
   - **线程安全测试用例**（完整测试代码）
   - **实施要求和验证标准**（必须严格遵循）

#### 1.3 现有系统状态确认
1. **现有实现文件检查**：
   - 检查core/dynamic_module_importer.py的当前实现
   - 检查core/unified_cache_manager.py的当前实现
   - 检查ui/main_window.py的当前状态栏实现
   - 检查core/enhanced_error_handler.py的错误处理机制

2. **配置和环境确认**：
   - 确认config/external_modules.json配置结构
   - 理解整体修复方案（docs/增强修复方案.md）

#### 1.4 参考支撑文档学习
1. **P1级别改进细节**：`docs/P1级别改进实施指南.md`
   - 缓存持久化精简实施细节
   - 接口契约表添加要求

2. **P4级别改进说明**：`docs/P4级别改进说明.md`
   - 可选增强功能说明
   - 后续优化方向参考

### 2. 核心架构组件创建

**重要提醒**：所有组件创建必须严格按照`docs/LAD-IMPL-006A架构修正方案实施-线程安全实现详细清单.md`中的完整代码实现，确保线程安全。

#### 2.0 组件依赖关系与初始化顺序（重要）

**组件依赖关系图**：
```
UnifiedCacheManager (基础层，无依赖)
     ↓
PerformanceMetrics (基础层，无依赖)  
     ↓
SnapshotManager (依赖: UnifiedCacheManager)
     ↓
ApplicationStateManager (依赖: SnapshotManager, PerformanceMetrics)
     ↓
ErrorCodeManager (依赖: 无，但在其他组件中使用)
     ↓
ConfigValidator (依赖: ErrorCodeManager)
```

**强制初始化顺序**：
1. **第一层（基础组件）**：
   - `UnifiedCacheManager` - 缓存管理器（无依赖）
   - `PerformanceMetrics` - 性能指标收集器（无依赖）
   - `ErrorCodeManager` - 错误码管理器（无依赖）

2. **第二层（中间组件）**：
   - `SnapshotManager` - 快照管理器（依赖: UnifiedCacheManager）
   - `ConfigValidator` - 配置验证器（依赖: ErrorCodeManager）

3. **第三层（核心组件）**：
   - `ApplicationStateManager` - 应用状态管理器（依赖: SnapshotManager, PerformanceMetrics）

**初始化代码模板**：
```python
# 正确的初始化顺序示例
def initialize_core_components():
    """按照依赖关系正确初始化所有核心组件"""
    
    # 第一层：基础组件（无依赖）
    cache_manager = UnifiedCacheManager()
    performance_metrics = PerformanceMetrics()
    error_code_manager = ErrorCodeManager()
    
    # 第二层：中间组件（有基础依赖）
    snapshot_manager = SnapshotManager(cache_manager=cache_manager)
    config_validator = ConfigValidator(error_code_manager=error_code_manager)
    
    # 第三层：核心组件（有复杂依赖）
    state_manager = ApplicationStateManager(
        snapshot_manager=snapshot_manager,
        performance_metrics=performance_metrics
    )
    
    return {
        'cache_manager': cache_manager,
        'performance_metrics': performance_metrics,
        'error_code_manager': error_code_manager,
        'snapshot_manager': snapshot_manager,
        'config_validator': config_validator,
        'state_manager': state_manager
    }
```

**⚠️ 关键约束**：
- 禁止循环依赖：任何组件不得直接或间接依赖自身
- 延迟初始化：如有必要，使用属性注入或工厂模式延迟注入依赖
- 单例模式：确保每个组件在应用中只有一个实例
- 错误处理：初始化失败时必须清理已创建的组件

#### 2.1 ApplicationStateManager创建（线程安全版本）
**🚨 重要**：直接创建线程安全版本，禁止先创建非线程安全版本再修改！

创建`core/application_state_manager.py`，**严格按照线程安全清单的完整代码实现**：
```python
class ApplicationStateManager:
    def __init__(self):
        self._module_states = {}
        self._render_state = {}
        self._link_state = {}
        self._snapshot_manager = SnapshotManager()
        self._performance_metrics = PerformanceMetrics()
    
    # 状态获取接口
    def get_module_status(self, module_name: str) -> Dict[str, Any]
    def get_render_status(self) -> Dict[str, Any]
    def get_link_status(self) -> Dict[str, Any]
    
    # 状态更新接口
    def update_module_status(self, module_name: str, status_data: Dict[str, Any]) -> bool
    def update_render_status(self, status_data: Dict[str, Any]) -> bool
    def update_link_status(self, status_data: Dict[str, Any]) -> bool
    
    # 状态查询接口
    def get_all_states(self) -> Dict[str, Any]
    def get_state_summary(self) -> Dict[str, str]
```

#### 2.2 SnapshotManager创建（线程安全版本）
**🚨 重要**：直接创建线程安全版本，禁止先创建非线程安全版本再修改！

创建`core/snapshot_manager.py`，**严格按照线程安全清单的完整代码实现**：
```python
class SnapshotManager:
    def __init__(self):
        self._cache_manager = UnifiedCacheManager()
        self._snapshot_prefixes = {
            'module': 'module_snapshot_',
            'render': 'render_snapshot',
            'link': 'link_snapshot'
        }
    
    # 快照保存接口
    def save_module_snapshot(self, module_name: str, data: Dict[str, Any]) -> bool
    def save_render_snapshot(self, data: Dict[str, Any]) -> bool
    def save_link_snapshot(self, data: Dict[str, Any]) -> bool
    
    # 快照获取接口
    def get_module_snapshot(self, module_name: str) -> Dict[str, Any]
    def get_render_snapshot(self) -> Dict[str, Any]
    def get_link_snapshot(self) -> Dict[str, Any]
    
    # 快照管理接口
    def clear_all_snapshots(self) -> bool
    def get_snapshot_info(self) -> Dict[str, Any]
```

#### 2.3 ConfigValidator创建（线程安全版本）
**🚨 重要**：直接创建线程安全版本，禁止先创建非线程安全版本再修改！

创建`core/config_validator.py`，实现：
```python
class ConfigValidator:
    def validate_external_modules_config(self) -> Dict[str, Any]
    def detect_config_conflicts(self) -> Dict[str, Any]
    def apply_resolution_strategy(self, conflicts: Dict[str, Any]) -> bool
```

**重要**：同时创建`config/external_modules.json`配置文件，**严格按照以下Schema格式**：

#### 2.3.1 external_modules.json格式定义
```json
{
  "$schema": "external_modules_v1.0.json",
  "version": "1.0",
  "metadata": {
    "description": "LAD本地Markdown渲染器外部模块配置",
    "last_updated": "2025-01-27T15:00:00Z",
    "format_version": "1.0"
  },
  "external_modules": {
    "markdown_extensions": {
      "enabled": true,
      "module_path": "extensions/markdown",
      "priority": 100,
      "config": {
        "enable_tables": true,
        "enable_code_highlight": true,
        "enable_math": false
      }
    },
    "syntax_highlighter": {
      "enabled": true,
      "module_path": "extensions/highlighter",
      "priority": 90,
      "config": {
        "theme": "github",
        "line_numbers": true,
        "languages": ["python", "javascript", "markdown", "json"]
      }
    },
    "link_processor": {
      "enabled": true,
      "module_path": "extensions/links",
      "priority": 80,
      "config": {
        "auto_link_detection": true,
        "relative_path_base": "./docs",
        "external_link_target": "_blank"
      }
    }
  },
  "global_settings": {
    "module_load_timeout": 5000,
    "max_concurrent_modules": 3,
    "error_handling": "graceful",
    "logging_level": "INFO"
  },
  "dependency_resolution": {
    "conflict_strategy": "priority_based",
    "auto_disable_conflicting": true,
    "fallback_modules": ["core_markdown", "basic_renderer"]
  }
}
```

#### 2.3.2 配置字段说明
- **$schema**: 配置文件Schema版本标识
- **version**: 配置格式版本号
- **metadata**: 配置元数据（描述、更新时间等）
- **external_modules**: 外部模块定义
  - **模块键名**: 模块唯一标识（如：markdown_extensions）
  - **enabled**: 模块是否启用（布尔值）
  - **module_path**: 模块相对路径（字符串）
  - **priority**: 加载优先级（整数，数值越大优先级越高）
  - **config**: 模块特定配置（对象）
- **global_settings**: 全局设置
  - **module_load_timeout**: 模块加载超时时间（毫秒）
  - **max_concurrent_modules**: 最大并发加载模块数
  - **error_handling**: 错误处理策略（"strict"/"graceful"）
  - **logging_level**: 日志级别
- **dependency_resolution**: 依赖解析配置
  - **conflict_strategy**: 冲突解决策略
  - **auto_disable_conflicting**: 是否自动禁用冲突模块
  - **fallback_modules**: 回退模块列表

#### 2.3.3 配置验证规则
```python
# ConfigValidator中的验证规则
VALIDATION_RULES = {
    'required_fields': ['version', 'external_modules'],
    'version_format': r'^\d+\.\d+$',
    'module_path_pattern': r'^[a-zA-Z0-9_/.-]+$',
    'priority_range': (1, 999),
    'timeout_range': (1000, 30000),
    'valid_error_handling': ['strict', 'graceful'],
    'valid_log_levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR'],
    'valid_conflict_strategies': ['priority_based', 'manual', 'disable_all']
}
```

#### 2.4 PerformanceMetrics创建
创建`core/performance_metrics.py`，**详细实现规范**：
```python
import time
import threading
import psutil
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager

@dataclass
class MetricEntry:
    """性能指标条目"""
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    cpu_percent: Optional[float] = None

class PerformanceMetrics:
    """性能指标收集器 - 线程安全实现"""
    
    def __init__(self):
        self._timers: Dict[str, MetricEntry] = {}
        self._completed_metrics: Dict[str, MetricEntry] = {}
        self._lock = threading.RLock()
        self._timer_counter = 0
        
    def start_timer(self, operation: str) -> str:
        """开始计时 - 返回计时器ID"""
        with self._lock:
            self._timer_counter += 1
            timer_id = f"{operation}_{self._timer_counter}_{int(time.time()*1000)}"
            
            # 收集开始时的系统指标
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            metric = MetricEntry(
                operation=operation,
                start_time=time.time(),
                memory_before=memory_before
            )
            self._timers[timer_id] = metric
            return timer_id
    
    def end_timer(self, timer_id: str) -> float:
        """结束计时 - 返回持续时间（秒）"""
        with self._lock:
            if timer_id not in self._timers:
                raise ValueError(f"Timer {timer_id} not found")
            
            metric = self._timers[timer_id]
            end_time = time.time()
            duration = end_time - metric.start_time
            
            # 收集结束时的系统指标
            process = psutil.Process()
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            cpu_percent = process.cpu_percent()
            
            # 更新指标
            metric.end_time = end_time
            metric.duration = duration
            metric.memory_after = memory_after
            metric.cpu_percent = cpu_percent
            
            # 移动到完成指标
            self._completed_metrics[timer_id] = metric
            del self._timers[timer_id]
            
            return duration
    
    @contextmanager
    def measure_operation(self, operation: str):
        """上下文管理器方式测量操作"""
        timer_id = self.start_timer(operation)
        try:
            yield timer_id
        finally:
            self.end_timer(timer_id)
    
    def collect_import_metrics(self) -> Dict[str, Any]:
        """收集模块导入相关的性能指标"""
        import_metrics = {
            metric_id: asdict(metric) 
            for metric_id, metric in self._completed_metrics.items() 
            if metric.operation.startswith(('import_', 'module_'))
        }
        
        # 计算统计信息
        durations = [m['duration'] for m in import_metrics.values() if m['duration']]
        return {
            'metrics': import_metrics,
            'total_imports': len(import_metrics),
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0
        }
    
    def collect_render_metrics(self) -> Dict[str, Any]:
        """收集渲染相关的性能指标"""
        render_metrics = {
            metric_id: asdict(metric) 
            for metric_id, metric in self._completed_metrics.items() 
            if metric.operation.startswith(('render_', 'markdown_'))
        }
        
        durations = [m['duration'] for m in render_metrics.values() if m['duration']]
        memory_usage = [m['memory_after'] - m['memory_before'] 
                       for m in render_metrics.values() 
                       if m['memory_after'] and m['memory_before']]
        
        return {
            'metrics': render_metrics,
            'total_renders': len(render_metrics),
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'avg_memory_usage': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
            'max_memory_usage': max(memory_usage) if memory_usage else 0
        }
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统级性能指标"""
        process = psutil.Process()
        return {
            'current_memory_mb': process.memory_info().rss / 1024 / 1024,
            'current_cpu_percent': process.cpu_percent(),
            'thread_count': process.num_threads(),
            'open_files': len(process.open_files()),
            'total_metrics_collected': len(self._completed_metrics),
            'active_timers': len(self._timers)
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要报告"""
        return {
            'timestamp': time.time(),
            'import_metrics': self.collect_import_metrics(),
            'render_metrics': self.collect_render_metrics(),
            'system_metrics': self.collect_system_metrics(),
            'metric_categories': self._categorize_metrics()
        }
    
    def _categorize_metrics(self) -> Dict[str, int]:
        """按操作类型分类指标"""
        categories = {}
        for metric in self._completed_metrics.values():
            category = metric.operation.split('_')[0]
            categories[category] = categories.get(category, 0) + 1
        return categories

# 使用示例
# metrics = PerformanceMetrics()
# 
# # 方式1：手动计时
# timer_id = metrics.start_timer("module_import")
# # ... 执行导入操作
# duration = metrics.end_timer(timer_id)
# 
# # 方式2：上下文管理器
# with metrics.measure_operation("render_markdown") as timer_id:
#     # ... 执行渲染操作
#     pass
```

**重要使用说明**：
1. **线程安全**：使用`threading.RLock()`确保多线程环境下的安全性
2. **资源监控**：自动收集内存和CPU使用情况
3. **分类统计**：按操作类型自动分类和统计
4. **上下文管理器**：提供便捷的`with`语句使用方式
5. **详细指标**：每个操作记录开始/结束时间、持续时间、内存变化、CPU使用率

### 3. 线程安全实现细节参考（架构说明）
**⚠️ 注意**：以下代码仅为架构设计参考，具体实现时直接使用第2节中的线程安全版本创建指导，不要先创建非线程安全版本！
#### 3.1 ApplicationStateManager线程安全设计
```python
import threading
from contextlib import contextmanager

class ApplicationStateManager:
    def __init__(self):
        # 现有初始化代码...
        # 线程安全控制
        self._state_lock = threading.RLock()  # 可重入锁
        self._module_locks = {}  # 模块级别的细粒度锁
        self._lock_manager_lock = threading.Lock()  # 锁管理器的锁
    
    def _get_module_lock(self, module_name: str) -> threading.Lock:
        """获取模块专用锁（懒加载）"""
        with self._lock_manager_lock:
            if module_name not in self._module_locks:
                self._module_locks[module_name] = threading.Lock()
            return self._module_locks[module_name]
    
    @contextmanager
    def _state_transaction(self, module_name: Optional[str] = None):
        """状态事务上下文管理器"""
        if module_name:
            module_lock = self._get_module_lock(module_name)
            with module_lock:
                yield
        else:
            with self._state_lock:
                yield
```

#### 3.2 SnapshotManager线程安全设计
```python
class SnapshotManager:
    def __init__(self):
        # 现有初始化代码...
        self._snapshot_lock = threading.RLock()
        self._write_locks = {}  # 写操作专用锁
        self._write_lock_manager = threading.Lock()
    
    def _get_write_lock(self, key: str) -> threading.Lock:
        """获取写操作专用锁"""
        with self._write_lock_manager:
            if key not in self._write_locks:
                self._write_locks[key] = threading.Lock()
            return self._write_locks[key]
```

#### 3.3 UnifiedCacheManager原子操作扩展
**必须按照线程安全清单中的完整实现**扩展现有的`core/unified_cache_manager.py`：
```python
class UnifiedCacheManager:
    def __init__(self):
        # 现有初始化代码...
        self._atomic_lock = threading.Lock()
        
    def atomic_set(self, key: str, value: Any) -> bool:
        """原子设置操作"""
        try:
            with self._atomic_lock:
                temp_key = f"{key}_temp_{int(time.time() * 1000)}"
                self.set(temp_key, value)
                self.set(key, value)
                self.delete(temp_key)
                return True
        except Exception as e:
            logger.error(f"Atomic set failed for key {key}: {e}")
            return False
```

#### 3.4 线程安全测试要求
**必须按照线程安全清单中的完整测试用例**实施以下测试：
1. **并发状态更新测试**：多线程同时更新不同模块状态
2. **快照一致性测试**：并发读写快照数据的一致性验证
3. **死锁检测测试**：确保锁机制不会导致死锁
4. **性能影响测试**：线程安全机制对性能的影响评估

**参考实现**：线程安全清单中包含完整的测试代码实现，包括TestThreadSafety类和所有测试方法。

### 4. 错误码标准化体系
1. 创建标准化错误码类：
   - ModuleImportErrorCodes（完整定义在第1份架构文档第618-690行）
   - RenderProcessingErrorCodes（完整定义在第1份架构文档第770-813行）
   - LinkProcessingErrorCodes（完整定义在第1份架构文档第692-768行）
   - SystemErrorCodes

2. 实现ErrorCodeManager统一管理器：
```python
class ErrorCodeManager:
    def __init__(self):
        self.error_codes = {
            'module': ModuleImportErrorCodes,
            'render': RenderProcessingErrorCodes,
            'link': LinkProcessingErrorCodes,
            'system': SystemErrorCodes
        }
    
    def get_error_message(self, domain: str, error_code: str) -> str:
        """获取标准化错误消息"""
        if domain in self.error_codes:
            return self.error_codes[domain].get_error_message(error_code)
        return f"Unknown error: {domain}.{error_code}"
    
    def get_error_severity(self, domain: str, error_code: str) -> str:
        """获取错误严重程度"""
        if domain in self.error_codes:
            return self.error_codes[domain].get_error_severity(error_code)
        return "error"
```

### 5. 集成测试和验证
1. 单元测试：每个新创建的类（包含线程安全测试）
2. 集成测试：组件间协作（包含并发场景）
3. 性能测试：状态管理性能（包含线程安全开销评估）
4. 稳定性测试：长时间运行（包含多线程压力测试）
5. **线程安全专项测试**：
   - 并发状态更新测试
   - 快照数据竞争测试
   - 锁机制有效性测试
   - 死锁预防测试

## 快照JSON Schema定义

### module_import_snapshot
```json
{
  "snapshot_type": "module_import_snapshot",
  "module": "markdown_processor",
  "function_mapping_status": "complete|incomplete|import_failed",
  "required_functions": ["render_markdown_with_zoom", "render_markdown_to_html"],
  "available_functions": ["..."],
  "missing_functions": ["..."],
  "non_callable_functions": ["..."],
  "path": "str|null",
  "used_fallback": "bool",
  "error_code": "str",
  "message": "str",
  "timestamp": "iso8601"
}
```

### render_snapshot
```json
{
  "snapshot_type": "render_snapshot",
  "renderer_type": "markdown_processor|markdown_library|text_fallback",
  "reason": "importer_complete|importer_incomplete|importer_failed|non_markdown|user_refresh",
  "details": {
    "file_path": "str",
    "file_ext": "str",
    "size_bytes": "int",
    "elapsed_ms": "int"
  },
  "timestamp": "iso8601"
}
```

### link_snapshot
```json
{
  "snapshot_type": "link_snapshot",
  "link_processor_loaded": "bool",
  "policy_profile": "default|strict|permissive|custom:<name>",
  "last_action": "navigate|open_external|blocked|preview",
  "last_result": "ok|warn|error",
  "details": {
    "href": "str",
    "resolved_path": "str|null",
    "reason": "str|null"
  },
  "error_code": "str",
  "message": "str",
  "timestamp": "iso8601"
}
```

## 代码修改规范
1. 创建备份: backup_20250901_架构修正方案实施_006A
2. 分阶段实施：核心组件→线程安全→错误码→集成测试→性能验证
3. 保持向后兼容性，不影响现有功能
4. 遵循第1份架构文档的详细设计
5. **线程安全优先**：所有状态管理组件必须线程安全

## 验证标准
1. 所有新组件按架构文档实现完整
2. 状态管理器工作正常，数据一致
3. 快照系统持久化和恢复功能正常
4. 配置验证器能检测和解决冲突
5. 性能指标收集工作正常
6. 错误码标准化完整实施
7. **线程安全验证通过**：
   - 并发访问不产生数据竞争
   - 锁机制有效防止状态不一致
   - 无死锁和性能瓶颈
   - 多线程压力测试通过
8. **单元测试覆盖率>90%** - 详细定义：
   - **计算方法**：使用`coverage.py`工具测量代码行覆盖率
   - **范围定义**：所有`core/`目录下的Python文件（`.py`）
   - **验证命令**：`python -m coverage run -m pytest tests/ && python -m coverage report --show-missing`
   - **最低要求**：每个模块的覆盖率不得低于85%，整体平均覆盖率>90%
   - **排除项**：测试文件本身、`__init__.py`空文件、调试代码块

9. **线程安全测试覆盖率>95%** - 详细定义：
   - **范围定义**：所有线程安全相关的代码路径（锁操作、并发访问、状态同步）
   - **计算方法**：
     ```python
     线程安全覆盖率 = (执行的线程安全代码行数 / 总线程安全代码行数) × 100%
     ```
   - **验证工具**：`coverage.py` + 自定义并发测试框架
   - **测试场景**：并发读写、锁竞争、死锁检测、状态一致性
   - **验证命令**：`python -m pytest tests/test_thread_safety.py -v --cov=core --cov-report=html`
   - **必须通过**：所有线程安全测试用例，无数据竞争警告

10. **集成测试全通过** - 补充定义：
    - **测试工具**：pytest + pytest-cov
    - **运行环境**：Python 3.8+ 多线程环境
    - **通过标准**：所有测试用例通过，无WARNING级别以上的日志输出

## 预设追问计划
以下是可能的追问方向，请准备相应内容：
1. 完整性追问: 架构实施是否覆盖文档的所有要求？
2. 深度追问: 状态管理的性能影响如何评估和优化？
3. 质量提升追问: 错误处理机制是否完善可靠？
4. 兼容性追问: 新架构如何与现有代码无缝集成？
5. 扩展性追问: 架构设计如何支持未来功能扩展？
6. **线程安全追问**: 线程安全机制是否完整实施，并发测试是否通过？
7. **性能影响追问**: 线程安全实现对系统性能的影响如何控制和优化？

## 下一步准备
请在任务完成后，提供一个标题为"【关键数据摘要-用于LAD-IMPL-007UI状态栏更新】"的部分，包含：
1. ApplicationStateManager的接口调用方法和返回格式（含线程安全使用说明）
2. SnapshotManager的快照数据结构和获取方法（含并发访问说明）
3. 状态管理器的初始化和配置方法（含线程安全初始化）
4. 错误码体系的使用规范和映射表
5. 性能指标的收集方法和数据格式
6. 配置验证器的使用方法和冲突解决策略
7. **线程安全机制的使用指南**：
   - 锁机制的正确使用方法
   - 并发访问的最佳实践
   - 线程安全验证的方法

这些信息将为LAD-IMPL-007任务提供完整的架构基础支持。

## 输出要求
1. 新创建的所有核心架构组件代码（包含线程安全实现）
2. **线程安全实现代码**：
   - ApplicationStateManager线程安全版本
   - SnapshotManager线程安全版本  
   - UnifiedCacheManager原子操作扩展
   - 线程安全测试用例
3. 错误码标准化实现代码（包含ErrorCodeManager）
4. 架构集成测试用例和结果（包含并发测试）
5. 性能基准测试报告（包含线程安全开销评估）
6. 配置验证和冲突解决实施报告
7. **线程安全验证报告**：
   - 并发测试结果
   - 锁机制有效性验证
   - 性能影响分析
8. 【关键数据摘要-用于LAD-IMPL-007】

## 必需输入文件清单

### 核心架构设计文档
1. `docs/第1份-架构修正方案完整细化过程文档.md` - 完整架构设计（2106行，v1.1）
2. `docs/第1份-架构修正方案实施检查清单.md` - 实施验收标准（142行）
3. `本地Markdown文件渲染程序-详细设计.md` - 系统整体架构设计（1327行，v2.1）
4. `docs/架构设计修正方案.md` - 架构修正指导文档（404行，v1.1）

### 线程安全实现专项文档（重要）
5. `docs/LAD-IMPL-006A架构修正方案实施-线程安全实现详细清单.md` - 线程安全完整实现方案（1031行，v1.0）

### 现有系统实现文件
6. `core/dynamic_module_importer.py` - 现有导入器实现
7. `core/unified_cache_manager.py` - 现有缓存管理器
8. `ui/main_window.py` - 现有UI主窗口
9. `core/enhanced_error_handler.py` - 现有错误处理器

### 配置和方案文件
10. `config/external_modules.json` - 外部模块配置
11. `docs/增强修复方案.md` - 整体修复方案

### 参考支撑文档
12. `docs/P1级别改进实施指南.md` - P1级别改进细节（缓存持久化等）
13. `docs/P4级别改进说明.md` - P4级别改进说明（可选增强功能）
```

---

## LAD-IMPL-007: UI状态栏更新 - 完整提示词

```
# LAD本地Markdown渲染器UI状态栏更新任务

## 会话元数据
- 任务ID: LAD-IMPL-007
- 任务类型: UI增强
- 复杂度级别: 中等复杂
- 预计交互: 6-7次
- 依赖任务: LAD-IMPL-006A (架构修正方案实施)
- 风险等级: 低风险

## 前序数据摘要
### LAD-IMPL-006关键成果
1. 函数映射验证机制已完成，支持complete/incomplete/import_failed三种状态
2. 接口契约表已定义，import_module()返回标准化字段
3. 缓存优化已完成，避免序列化警告

### P1级别改进成果
1. 缓存持久化精简已实施，创建可序列化的缓存数据
2. 接口契约表已添加到LAD-IMPL-006任务完成报告

## 任务背景
根据《增强修复方案.md》C1部分和《LAD-IMPL-007任务补充说明.md》P2级别改进要求，更新UI状态栏显示模块导入状态、渲染状态和函数映射状态，提供清晰的用户反馈。

## 本次任务目标
1. 设计状态栏显示逻辑和UI布局
2. 实现三种状态的可视化指示器（complete/incomplete/import_failed）
3. 添加状态变更的实时更新机制
4. 提供状态详情的悬停提示
5. 实施P2级别改进：运行态状态栏数据接口和报告接口扩展

## 具体实施要求

### 1. 前置验证和一致性检查
1. 验证P1级别改进的实际效果：
   - 检查缓存数据在系统重启后的持久性
   - 验证缓存清理机制的有效性
   - 测试接口契约表在实际使用中的准确性
2. 检查V3.0文档与现有补充说明文档的一致性：
   - 对比LAD-IMPL-007任务补充说明.md与V3.0文档的要求
   - 验证任务目标、实施要求、验证标准的一致性
   - 检查输出要求和数据传递格式的一致性
3. 深入了解相关组件的实现：
   - 分析core/unified_cache_manager.py的实现细节
   - 了解core/enhanced_error_handler.py的错误处理机制
   - 检查config/external_modules.json的配置结构
   - 分析core/markdown_renderer.py的渲染逻辑
   - 了解utils/config_manager.py的配置管理机制

### 2. 核心状态栏功能
1. 修改ui/main_window.py的状态栏组件
2. 添加模块状态、渲染状态、函数状态指示器
3. 实现状态颜色编码（绿色/黄色/红色）
4. 添加状态详情的工具提示

### 3. P2级别改进实施
#### 2.1 运行态状态栏数据接口
在core/dynamic_module_importer.py中新增方法：
```python
def get_last_import_snapshot(self) -> Dict[str, Any]:
    """获取最近一次导入结果的精简快照，供UI状态栏使用"""
```

#### 2.2 报告接口扩展
扩展generate_function_mapping_report方法：
```python
def generate_function_mapping_report(self, as_dict: bool = False) -> Union[str, Dict[str, Any]]:
    """生成函数映射完整性报告，支持字典格式返回"""
```

#### 2.3 main.py状态栏集成
实现状态栏更新逻辑：
- complete: "✅ Markdown处理器已加载（动态导入）"
- incomplete: "⚠️ Markdown处理器部分可用（函数缺失）"
- import_failed: "❌ Markdown处理器不可用（导入失败）"

## 代码修改规范
1. 创建备份: backup_20250901_UI状态栏更新_007
2. 分阶段实施：接口扩展→状态栏组件→集成测试
3. 保持向后兼容性，不影响现有功能
4. 遵循现有代码规范和架构设计

## 验证标准
1. 状态栏能准确反映当前系统状态
2. 状态变更能实时更新显示
3. 用户能通过状态栏快速了解系统状况
4. UI响应流畅，不影响主要功能
5. P2级别改进功能完整且稳定

## 预设追问计划
以下是可能的追问方向，请准备相应内容：
1. 完整性追问: 状态栏是否覆盖了所有可能的状态组合？
2. 深度追问: 状态更新机制是否足够实时和准确？
3. 质量提升追问: UI设计是否用户友好且直观？
4. 跨领域整合追问: 状态栏如何与现有UI组件协调工作？
5. P2改进追问: 新增接口是否满足后续任务需求？

## 下一步准备
请在任务完成后，提供一个标题为"【关键数据摘要-用于LAD-IMPL-008日志系统增强】"的部分，包含：
1. UI状态事件定义和触发条件
2. 状态栏数据接口的调用方法和返回格式
3. P2级别改进的接口文档和使用示例
4. 状态更新的日志记录要求

这些信息将用于LAD-IMPL-008日志系统增强任务，请确保数据格式标准化且易于集成。

## 输出要求
1. 修改后的UI状态栏代码
2. P2级别改进的完整实现
3. 状态显示逻辑文档
4. UI测试用例和验证结果
5. 【关键数据摘要-用于LAD-IMPL-008】
```

---

## LAD-IMPL-008: 日志系统增强 - 完整提示词

```
# LAD本地Markdown渲染器日志系统增强任务

## 会话元数据
- 任务ID: LAD-IMPL-008
- 任务类型: 系统增强
- 复杂度级别: 复杂
- 预计交互: 10-12次
- 依赖任务: LAD-IMPL-007
- 风险等级: 中风险

## 前序数据摘要
### 从LAD-IMPL-007获取的UI状态事件和系统状态定义
1. **UI状态事件定义**：
   - module_status_changed: 模块导入状态变更事件（包含module_name, old_status, new_status, timestamp）
   - render_status_changed: 渲染状态变更事件（包含renderer_type, file_path, success, duration_ms）
   - status_bar_updated: 状态栏显示更新事件（包含module_indicator, render_indicator, link_indicator）
   - user_interaction: 用户交互事件（包含action_type, target, response_time_ms）

2. **系统状态定义**：
   - module_import_state: 状态值['complete', 'incomplete', 'import_failed']，快照字段包含模块、函数映射状态、缺失函数等
   - render_state: 状态值['ready', 'processing', 'completed', 'failed']，快照字段包含渲染器类型、文件路径、处理阶段等
   - ui_state: 状态值['idle', 'updating', 'responsive', 'busy']，快照字段包含活动视图、最后操作、响应时间等

3. **P2级别改进接口数据**：
   - get_last_import_snapshot(): 返回最近导入结果的精简快照，供UI状态栏使用
   - generate_function_mapping_report(as_dict=True): 生成函数映射完整性报告的字典格式
   - 状态栏更新逻辑: complete/incomplete/import_failed的具体UI文本和颜色映射

4. **状态更新的日志记录要求**：
   - 每次状态变更必须记录correlation_id用于关联
   - 状态栏数据接口调用需要记录调用方法和返回格式
   - P2级别改进的接口使用需要详细记录调用示例

## 任务背景
根据《增强修复方案.md》C2部分、D部分以及《第2份-LAD-IMPL-008日志系统增强完整细化过程文档.md》系列设计文档，实施统一结构化日志系统，添加性能监控、错误追踪和日志分析功能，建立完整的系统观测性。

## 本次任务目标
1. 实现基于correlation_id的结构化日志格式
2. 建立统一的日志键名规范（LOG_KEYS标准）
3. 实施完整的性能监控体系（PerformanceMetrics集成）
4. 创建智能日志文件轮转和清理机制
5. 建立日志级别动态配置系统
6. 实现日志分析查询API和Web仪表板
7. 集成错误码标准化体系

## 具体实施要求

### 1. 前置分析和设计文档整合
1. 深入学习第2份系列设计文档：
   - 完整阅读`docs/第2份-LAD-IMPL-008日志系统增强完整细化过程文档.md`
   - 完整阅读`docs/第2份-LAD-IMPL-008日志系统增强完整细化过程文档-续篇1.md`（472行）
   - 完整阅读`docs/第2份-LAD-IMPL-008日志系统增强疏漏补充.md`（948行）
   - 理解错误码标准化体系（ModuleImportErrorCodes、RenderProcessingErrorCodes等）
   - 掌握性能监控架构设计（PerformanceMetrics类完整接口）
   - 理解日志级别动态配置机制（DynamicLogConfigManager、RuntimeLogLevelController）

2. 验证LAD-IMPL-007的实施效果：
   - 检查ApplicationStateManager的状态管理接口调用
   - 验证SnapshotManager的快照数据格式和持久化
   - 测试UI状态栏与系统状态的一致性和实时更新
   - 确认P2级别改进接口的稳定性和数据格式

3. 分析现有日志系统现状：
   - 检查core/enhanced_error_handler.py的当前错误处理机制
   - 分析现有日志配置文件结构和管理方式
   - 了解core/markdown_renderer.py中的日志记录逻辑
   - 检查utils/config_manager.py中的配置管理机制

### 2. 结构化日志系统核心实现

#### 2.1 统一日志格式和Correlation ID机制
创建`core/structured_logger.py`，实现：
```python
class StructuredLogger:
    def __init__(self, correlation_id_generator, performance_metrics):
        self.correlation_id = correlation_id_generator
        self.performance_metrics = performance_metrics
        self.log_formatter = UnifiedLogFormatter()
    
    def log_with_context(self, level, message, **context_data)
    def start_operation_log(self, operation_name) -> str  # 返回correlation_id
    def end_operation_log(self, correlation_id, result, **metrics)
    def log_state_change(self, state_type, old_state, new_state, correlation_id)
    def log_performance_metrics(self, metrics_data, correlation_id)
```

#### 2.2 日志键名统一规范实施
基于设计文档实现标准LOG_KEYS：
```python
UNIFIED_LOG_KEYS = {
    # 核心状态字段
    'module': '模块名称',
    'renderer_type': '渲染器类型',
    'function_mapping_status': '函数映射状态',
    'correlation_id': '关联ID',
    'operation_name': '操作名称',
    'timestamp': 'ISO8601时间戳',
    
    # 性能字段
    'duration_ms': '操作耗时（毫秒）',
    'memory_usage_mb': '内存使用（MB）',
    'cpu_percent': 'CPU使用率',
    
    # 错误处理字段
    'error_code': '标准化错误码',
    'error_severity': '错误严重程度',
    'recoverable': '是否可恢复',
    'suggested_action': '建议操作',
    
    # 状态变更字段
    'old_state': '原始状态',
    'new_state': '新状态',
    'change_reason': '变更原因',
    'triggered_by': '触发来源'
}
```

#### 2.3 PerformanceMetrics集成
基于设计文档的PerformanceMetrics架构，集成到日志系统：
```python
# 从LAD-IMPL-006A获取的PerformanceMetrics实例
performance_metrics = app_state_manager.get_performance_metrics()

# 集成到结构化日志器
structured_logger = StructuredLogger(
    correlation_id_generator=CorrelationIDGenerator(),
    performance_metrics=performance_metrics
)
```

### 3. 错误码标准化体系集成

#### 3.1 错误码管理器集成
基于续篇1文档的ErrorCodeManager设计：
```python
class LoggingErrorCodeManager:
    def __init__(self):
        self.error_code_manager = ErrorCodeManager()  # 从LAD-IMPL-006A
    
    def log_error_with_code(self, error_code: str, context: Dict[str, Any])
    def format_error_log_entry(self, error_code: str, context: Dict[str, Any])
    def get_error_categorization(self, error_code: str) -> Dict[str, Any]
```

#### 3.2 标准化错误码应用
在所有模块中应用标准化错误码：
- ModuleImportErrorCodes: MOD_IMPORT_*, MOD_VALID_*, MOD_CFG_*
- RenderProcessingErrorCodes: REN_EXEC_*, REN_CONTENT_*, REN_OUTPUT_*
- LinkProcessingErrorCodes: LNK_SEC_*, LNK_URL_*, LNK_NET_*
- SystemErrorCodes: SYS_INIT_*, SYS_RES_*, SYS_PERM_*

### 4. 日志级别动态配置系统

#### 4.1 配置热重载机制
基于疏漏补充文档的DynamicLogConfigManager设计：
```python
dynamic_config = DynamicLogConfigManager('config/logging.json')
dynamic_config.start_watching()  # 开始监控配置文件变化

level_controller = RuntimeLogLevelController()
level_controller.register_logger('import', import_logger)
level_controller.register_logger('render', render_logger)
level_controller.register_logger('ui', ui_logger)
```

#### 4.2 Web API控制接口
实现动态配置API：
- GET /api/config/log-level: 获取当前日志级别配置
- POST /api/config/log-level: 设置特定日志器级别
- POST /api/config/log-level/restore: 恢复原始日志级别

### 5. 智能日志轮转和清理机制

#### 5.1 轮转管理器实施
基于疏漏补充文档的IntelligentLogRotationManager：
```python
rotation_config = {
    'max_size_mb': 10,
    'backup_count': 5,
    'compress_backups': True,
    'retention_days': 30,
    'rotation_time': '00:00'
}

rotation_manager = IntelligentLogRotationManager(log_file_path, rotation_config)
scheduler = LogRotationScheduler(rotation_manager)
scheduler.start()
```

#### 5.2 磁盘空间监控
实施DiskSpaceMonitor进行磁盘空间管理：
```python
disk_monitor = DiskSpaceMonitor(log_dir='logs/', min_free_gb=1.0)
space_ok, free_gb, message = disk_monitor.check_space()
if not space_ok:
    disk_monitor.emergency_cleanup(rotation_manager)
```

### 6. 日志分析查询API和Web仪表板

#### 6.1 日志查询API实现
创建`api/log_query_api.py`：
```python
@app.route('/api/logs/query', methods=['POST'])
def query_logs():
    # 支持时间范围、级别、模块、correlation_id等查询条件
    pass

@app.route('/api/logs/performance', methods=['GET'])  
def get_performance_metrics():
    # 返回性能指标数据
    pass

@app.route('/api/logs/errors', methods=['GET'])
def get_error_statistics():
    # 返回错误统计信息
    pass
```

#### 6.2 实时性能监控仪表板
基于疏漏补充文档的Web仪表板设计，实现：
- 实时指标收集器（RealTimeMetricsCollector）
- 系统概览、导入性能、渲染性能、资源使用、错误统计、UI响应性能
- Chart.js实现的动态图表展示
- 每5秒自动更新的实时数据

### 7. 模块集成和日志注入

#### 7.1 DynamicModuleImporter日志增强
在core/dynamic_module_importer.py中集成结构化日志：
```python
def import_module(self, module_config):
    correlation_id = self.structured_logger.start_operation_log('module_import')
    try:
        # 导入逻辑...
        self.structured_logger.log_with_context(
            'INFO', 'Module import completed',
            module=module_name,
            function_mapping_status=status,
            correlation_id=correlation_id,
            **performance_metrics
        )
    except Exception as e:
        error_code = self.determine_error_code(e)
        self.structured_logger.log_error_with_code(error_code, {
            'module': module_name,
            'correlation_id': correlation_id,
            'exception': str(e)
        })
```

#### 7.2 MarkdownRenderer日志增强
类似地在core/markdown_renderer.py中集成日志：
```python
def render(self, content, file_path):
    correlation_id = self.structured_logger.start_operation_log('content_render')
    # 渲染逻辑和日志记录...
```

#### 7.3 MainWindow UI日志增强  
在ui/main_window.py中添加UI操作日志：
```python
def update_status_bar(self, status_data):
    correlation_id = self.structured_logger.start_operation_log('ui_status_update')
    # UI更新逻辑和日志记录...
```

## 验证标准
1. **结构化日志完整性**：所有关键操作都有correlation_id关联的完整日志链路
2. **性能监控准确性**：性能指标数据能准确反映系统瓶颈和趋势
3. **错误处理标准化**：所有错误都使用标准化错误码，包含完整上下文信息
4. **日志管理高效性**：日志轮转、清理机制工作正常，不占用过多磁盘空间
5. **动态配置有效性**：日志级别可动态调整，配置热重载功能正常
6. **查询分析易用性**：日志查询API响应及时，Web仪表板数据准确
7. **系统性能影响**：日志系统增强后，对主要功能的性能影响<5%

## 预设追问计划
以下是可能的追问方向，请准备相应内容：
1. 完整性追问: 日志覆盖是否包含所有关键操作路径和异常场景？
2. 深度追问: correlation_id机制如何确保日志链路的完整性和准确性？
3. 质量提升追问: 错误码标准化如何提升问题诊断和解决效率？
4. 性能影响追问: 结构化日志和性能监控的开销如何优化和控制？
5. 扩展性追问: 日志系统如何支持未来功能模块的接入和扩展？
6. 运维支持追问: 日志分析工具和仪表板如何支持实际的运维和故障排除？

## 下一步准备
请在任务完成后，提供一个标题为"【关键数据摘要-用于LAD-IMPL-009基础功能验证】"的部分，包含：
1. **日志验证标准和检查要点**：
   - Correlation_id链路完整性验证方法
   - 结构化日志格式的验证脚本
   - 性能指标准确性的基准对比方法

2. **性能基准数据和监控指标**：
   - 系统关键操作的性能基线数据
   - 监控告警阈值设置建议
   - 性能退化检测的自动化方法

3. **日志分析工具的使用方法**：
   - 日志查询API的调用示例和参数说明
   - Web仪表板的使用指南和功能说明
   - 常见问题的日志分析和诊断方法

4. **系统监控和故障诊断指南**：
   - 基于错误码的故障分类和处理流程
   - 性能瓶颈识别和优化建议
   - 日志系统自身的健康检查方法

这些信息将确保LAD-IMPL-009基础功能验证任务能够全面评估系统质量和可维护性。

## 输出要求
1. **结构化日志系统核心代码**：
   - core/structured_logger.py（StructuredLogger类完整实现）
   - core/correlation_id_generator.py（关联ID生成器）
   - core/unified_log_formatter.py（统一日志格式器）

2. **错误码标准化实现代码**：
   - core/logging_error_code_manager.py（日志错误码管理器）
   - 各模块的错误码应用集成代码

3. **动态配置系统代码**：
   - core/dynamic_log_config_manager.py（配置热重载管理器）
   - core/runtime_log_level_controller.py（运行时级别控制器）
   - api/log_config_api.py（配置控制API）

4. **日志轮转和清理系统**：
   - core/intelligent_log_rotation_manager.py（智能轮转管理器）
   - core/log_rotation_scheduler.py（轮转调度器）
   - core/disk_space_monitor.py（磁盘空间监控器）

5. **日志分析和监控系统**：
   - api/log_query_api.py（日志查询API）
   - static/performance_dashboard.html（性能监控仪表板）
   - core/real_time_metrics_collector.py（实时指标收集器）

6. **模块集成代码**：
   - 更新后的core/dynamic_module_importer.py（集成结构化日志）
   - 更新后的core/markdown_renderer.py（集成结构化日志）
   - 更新后的ui/main_window.py（集成UI操作日志）

7. **配置和文档**：
   - config/logging.json（日志配置文件模板）
   - docs/日志系统使用指南.md（完整使用文档）
   - docs/故障诊断手册.md（基于日志的故障排除指南）

8. **测试验证**：
   - tests/test_structured_logging.py（结构化日志测试用例）
   - tests/test_performance_monitoring.py（性能监控测试用例）
   - tests/test_log_rotation.py（日志轮转测试用例）

9. **【关键数据摘要-用于LAD-IMPL-009】**

## 必需输入文件清单
1. `docs/第2份-LAD-IMPL-008日志系统增强完整细化过程文档.md` - 核心设计文档
2. `docs/第2份-LAD-IMPL-008日志系统增强完整细化过程文档-续篇1.md` - 错误码和性能监控设计（472行）
3. `docs/第2份-LAD-IMPL-008日志系统增强疏漏补充.md` - 动态配置和仪表板设计（948行）
4. `core/application_state_manager.py` - 状态管理器（来自LAD-IMPL-006A）
5. `core/snapshot_manager.py` - 快照管理器（来自LAD-IMPL-006A）
6. `core/performance_metrics.py` - 性能指标收集器（来自LAD-IMPL-006A）
7. `core/enhanced_error_handler.py` - 现有错误处理器
8. `core/dynamic_module_importer.py` - 动态模块导入器
9. `core/markdown_renderer.py` - Markdown渲染器
10. `ui/main_window.py` - 主窗口UI
11. `docs/增强修复方案.md` - 整体修复方案C2、D部分
12. LAD-IMPL-007任务的完整输出结果（UI状态事件定义、系统状态定义、关键数据摘要）
```

---

## LAD-IMPL-009: 基础功能验证 - 完整提示词

```
# LAD本地Markdown渲染器基础功能验证任务

## 会话元数据
- 任务ID: LAD-IMPL-009
- 任务类型: 集成测试
- 复杂度级别: 中等复杂
- 预计交互: 6-7次
- 依赖任务: LAD-IMPL-007, LAD-IMPL-008
- 风险等级: 中风险

## 前序数据摘要
[从LAD-IMPL-007获取UI状态事件和LAD-IMPL-008获取日志验证标准]

## 任务背景
在链接功能接入前，全面验证修复后的基础功能完整性和稳定性，确保核心渲染功能正常工作。同时实施P3级别改进：测试用例沉淀和日志结构化统一。

## 本次任务目标
1. 验证模块导入机制的稳定性和一致性
2. 测试渲染器的各种工作模式和状态处理
3. 验证UI状态栏和日志系统的正确工作
4. 进行回归测试，确保无功能退化
5. 实施P3级别改进：测试用例持久化和日志结构化验证

## 具体测试要求

### 1. 前置验证和集成检查
1. 验证LAD-IMPL-007和LAD-IMPL-008的实施效果：
   - 检查状态栏功能的完整性和稳定性
   - 验证日志系统的结构化程度和键名统一性
   - 测试P2和P3级别改进的集成效果
2. 参考现有测试框架：
   - 分析test/目录下的现有测试用例
   - 了解测试框架的结构和标准
   - 检查测试覆盖率和质量要求

### 2. 模块导入测试
- 配置文件方案测试：external_modules.json配置完整性
- 环境变量方案测试：PYTHONPATH fallback机制
- Fallback机制测试：各种失败场景的graceful处理

### 3. 渲染功能测试
- 正常渲染测试：各种Markdown语法渲染正确性
- 错误处理测试：异常输入的处理能力
- 性能表现测试：渲染速度和资源使用

### 3. UI集成测试
- 状态显示测试：状态栏准确反映系统状态
- 用户交互测试：UI响应和反馈机制
- 错误反馈测试：用户友好的错误提示

### 4. 日志系统测试
- 日志记录测试：完整记录关键操作
- 格式验证测试：日志格式标准化
- 性能监控测试：监控数据准确性

### 5. P3级别改进实施
#### 5.1 测试用例沉淀
创建tests/test_function_mapping.py：
- 成功路径测试
- 失败路径测试（缺失函数、不可调用函数）
- Fallback路径测试
- 边界情况测试（缓存持久性、系统重启等）
- 性能测试（大量模块导入、并发访问等）

#### 5.2 日志结构化统一验证
验证LOG_KEYS在Importer和Renderer中的一致使用
- 检查日志键名的完整性和一致性
- 验证日志数据的准确性和完整性
- 测试日志系统的性能和稳定性

### 6. 详细测试场景设计（重要补充）

#### 6.1 边界条件测试场景设计
**空值和NULL处理测试**：
- 空配置文件测试：测试external_modules.json为空或格式错误的处理
- 空模块路径测试：测试模块路径为空字符串或None的处理
- NULL函数映射测试：测试函数映射表为空或包含NULL值的处理
- 空快照数据测试：测试快照数据为空或损坏的恢复机制

**极限值测试**：
- 超大文件渲染测试：测试>100MB Markdown文件的渲染能力和内存管理
- 超长路径处理测试：测试>260字符路径的处理（Windows限制）
- 大量并发请求测试：测试>100个并发模块导入请求的处理
- 内存耗尽场景测试：测试系统内存不足时的降级处理

**格式异常测试**：
- 损坏的配置文件测试：测试JSON格式错误、编码错误的配置文件
- 无效的JSON格式测试：测试包含语法错误的配置文件处理
- 编码异常文件测试：测试非UTF-8编码的Markdown文件处理
- 权限不足文件测试：测试无读取权限的文件访问处理

#### 6.2 异常场景测试用例
**网络异常模拟**：
- 网络断开测试：测试网络连接中断时的链接处理
- 连接超时测试：测试网络请求超时的处理机制
- DNS解析失败测试：测试域名解析失败的处理

**文件系统异常**：
- 磁盘空间不足测试：测试磁盘空间不足时的缓存清理和错误处理
- 文件被锁定测试：测试文件被其他程序锁定时的处理
- 目录不存在测试：测试配置中指定的目录不存在的处理
- 文件权限异常测试：测试文件权限变更导致的访问失败

**系统资源异常**：
- 内存不足测试：测试系统内存不足时的优雅降级
- CPU高负载测试：测试CPU高负载情况下的性能表现
- 线程池耗尽测试：测试线程资源耗尽时的队列处理
- 文件句柄耗尽测试：测试文件句柄达到系统限制时的处理

#### 6.3 回滚和恢复测试
**配置回滚测试**：
- 配置文件损坏回滚：测试配置文件损坏时回滚到上一个有效配置
- 模块导入失败回滚：测试模块导入失败时的fallback机制
- 缓存数据损坏恢复：测试缓存数据损坏时的重建机制

**数据恢复测试**：
- 快照数据恢复：测试从快照恢复应用状态的完整性
- 部分数据丢失恢复：测试部分状态数据丢失时的补偿机制
- 状态不一致修复：测试检测和修复状态不一致的机制

**服务降级测试**：
- 渲染器降级：测试动态模块不可用时降级到内置渲染器
- 功能禁用测试：测试关键功能异常时的功能禁用和提示
- 只读模式测试：测试写入操作失败时的只读模式切换

## 验证标准
1. 所有基础功能正常工作，无崩溃或异常
2. 错误处理机制有效，用户反馈清晰
3. 性能指标符合预期，无明显退化
4. 日志记录完整准确，便于问题诊断
5. 测试用例覆盖核心功能，结果可重复

## 预设追问计划
以下是可能的追问方向，请准备相应内容：
1. 完整性追问: 测试覆盖是否包含所有关键场景？
2. 深度追问: 发现的问题如何分类和优先级排序？
3. 质量提升追问: 测试自动化程度如何提升？
4. 回归防护追问: 如何确保未来修改不破坏现有功能？
5. P3改进追问: 测试用例的维护性和扩展性如何？

## 下一步准备
请在任务完成后，提供一个标题为"【关键数据摘要-用于LAD-IMPL-010链接功能分析】"的部分，包含：
1. 基础功能状态总结和稳定性评估
2. 系统性能基准数据
3. 已知问题清单和影响评估
4. 测试框架和验证方法说明
5. 为链接功能接入准备的兼容性检查点

这些信息将确保链接功能能在稳定的基础上安全接入。

## 输出要求
1. 完整的功能验证报告
2. 发现问题的详细记录和解决方案
3. 性能基准测试结果
4. P3级别改进的实施报告
5. 测试用例持久化文件
6. 【关键数据摘要-用于LAD-IMPL-010】
```

---

## LAD-IMPL-010: 链接功能分析 - 完整提示词

```
# LAD本地Markdown渲染器链接功能分析任务

## 会话元数据
- 任务ID: LAD-IMPL-010
- 任务类型: 需求分析
- 复杂度级别: 简单
- 预计交互: 4-5次
- 依赖任务: LAD-IMPL-009
- 风险等级: 低风险

## 前序数据摘要
[从LAD-IMPL-009获取基础功能状态和验证结果]

## 任务背景
分析《确认的链接功能接入方案.md》的技术要求，制定链接功能与现有修复方案的集成策略。该方案采用"智能分析合并 + 比较参考优化"的混合策略，确保功能完整性和系统稳定性。

## 本次任务目标
1. 深入分析链接功能的技术需求和实现方案
2. 评估与现有修复方案的兼容性和集成点
3. 识别潜在的技术风险和实现难点
4. 制定详细的集成实施计划

## 具体分析要求

### 1. 前置验证和基础确认
1. 验证LAD-IMPL-009的实施效果：
   - 确认基础功能的完整性和稳定性
   - 验证P1-P3级别改进的集成效果
   - 检查系统性能基准和监控指标
2. 深入了解现有系统架构：
   - 分析ui/main_window.py和ui/content_viewer.py的当前实现
   - 了解现有配置系统的扩展能力
   - 检查现有日志系统的扩展性

### 2. 技术需求分析
- 链接处理逻辑：链接识别、解析、验证、处理的完整流程
- UI集成要求：链接功能在UI层的集成需求
- 性能影响：评估链接功能对系统性能的影响

### 3. 兼容性评估
- 与现有渲染器的接口兼容性
- 与现有配置系统的兼容性
- 与现有日志系统的兼容性
- 与已实施的P1-P3改进的兼容性

### 3. 风险识别
- 技术风险：实现复杂度、技术难点
- 性能风险：性能影响、资源消耗
- 用户体验风险：交互复杂度、学习成本
- 安全风险：恶意链接、路径遍历攻击

### 4. 实施规划
- 集成步骤：详细的实施步骤和时间安排
- 测试策略：测试计划、测试用例
- 回滚预案：回滚方案、应急处理

### 5. 文件映射分析
根据《确认的链接功能接入方案.md》：
#### A类：智能分析合并（核心功能文件）
- ui/content_viewer.py ← backup_link_fixes/content_viewer_backup.py
- core/link_processor.py ← backup_link_fixes/link_processor_backup.py
- core/content_preview.py ← backup_link_fixes/content_preview_backup.py

#### B类：比较参考优化（稳定性文件）
- main.py（参考 backup_link_fixes/main_backup.py）
- ui/main_window.py（参考 backup_link_fixes/main_window_backup.py）

## 验证标准
1. 技术需求分析完整准确
2. 兼容性评估覆盖所有关键接口
3. 风险识别全面，解决方案可行
4. 实施计划详细可执行

## 预设追问计划
以下是可能的追问方向，请准备相应内容：
1. 完整性追问: 链接功能分析是否覆盖所有使用场景？
2. 深度追问: 集成风险评估是否充分考虑边界情况？
3. 质量提升追问: 实施计划的可操作性如何进一步细化？
4. 兼容性追问: 与现有改进（P1-P3）的协同性如何保证？
5. 安全性追问: 链接处理的安全措施是否完善？

## 下一步准备
请在分析完成后，提供一个标题为"【关键数据摘要-用于LAD-IMPL-011链接功能合并】"的部分，包含：
1. 集成策略和技术要求的详细说明
2. 文件合并的优先级和依赖关系
3. 关键接口的兼容性检查清单
4. 风险控制措施和应急预案
5. 测试验证的具体要求和标准

这些信息将直接指导LAD-IMPL-011的实施执行。

## 输出要求
1. 链接功能技术需求分析报告
2. 集成兼容性评估结果
3. 风险识别和缓解策略
4. 详细的实施计划和时间表
5. 【关键数据摘要-用于LAD-IMPL-011】
```

---

## LAD-IMPL-011: 链接功能合并 - 完整提示词

```
# LAD本地Markdown渲染器链接功能合并任务

## 会话元数据
- 任务ID: LAD-IMPL-011
- 任务类型: 功能开发
- 复杂度级别: 复杂
- 预计交互: 9-10次
- 依赖任务: LAD-IMPL-010
- 风险等级: 高风险

## 前序数据摘要
[从LAD-IMPL-010获取集成策略和技术要求]

## 任务背景
将链接功能集成到修复后的渲染器中，按照《确认的链接功能接入方案.md》执行智能分析合并策略，确保功能完整性和系统稳定性。

## 本次任务目标
1. 实现链接功能的核心逻辑集成
2. 修改渲染器以支持链接处理
3. 更新UI组件以支持链接功能
4. 确保与现有功能的无缝集成

## 具体实施要求

### 1. 前置验证和风险评估
1. 验证LAD-IMPL-010的分析结果：
   - 确认集成策略的可行性和风险控制措施
   - 验证技术要求的完整性和准确性
   - 检查实施计划的详细程度和可操作性
2. 深入了解备份文件：
   - 分析backup_link_fixes/content_viewer_backup.py的链接处理逻辑
   - 分析backup_link_fixes/link_processor_backup.py的链接处理机制
   - 分析backup_link_fixes/content_preview_backup.py的预览功能
   - 分析backup_link_fixes/main_backup.py的启动逻辑
   - 分析backup_link_fixes/main_window_backup.py的UI集成
   - 了解备份版本的功能特性和实现细节
   - 检查备份版本与当前版本的差异和冲突点

### 2. 核心集成（A类文件：智能分析合并）
#### 2.1 ui/content_viewer.py
- 合并策略: 保留当前版本的基础修复，接入备份版本的链接处理功能
- 重点关注: 自定义QWebEnginePage、链接点击处理逻辑、导航历史管理、错误处理和状态管理

#### 2.2 core/link_processor.py
- 合并策略: 完整接入备份版本的实现
- 重点关注: 链接类型识别、路径解析、链接验证、处理器管理

#### 2.3 core/content_preview.py
- 合并策略: 保留当前版本基础，增强链接集成功能
- 重点关注: 内容预览、HTML生成、链接集成

### 3. 优化改进（B类文件：比较参考优化）
#### 3.1 main.py
- 策略: 保持现有版本，参考backup_link_fixes/main_backup.py进行优化
- 重点关注: 轻量探测逻辑、高DPI设置、运行时配置

#### 3.2 ui/main_window.py
- 策略: 保持现有版本，参考backup_link_fixes/main_window_backup.py进行优化
- 重点关注: ContentViewer集成、文件树集成

### 4. 系统集成
1. 配置集成：扩展配置文件支持链接功能参数
2. 日志集成：添加链接功能相关的日志记录
3. 状态集成：确保链接状态与UI状态栏协调
4. 错误集成：统一错误处理和用户反馈

## 代码修改规范
1. 创建备份: backup_20250901_链接功能合并_011
2. 分阶段实施：核心逻辑→UI集成→配置扩展→日志完善
3. 保持向后兼容性，不影响现有功能
4. 遵循现有代码规范和架构设计

## 验证标准
1. 链接功能正常工作，符合设计要求
2. 现有功能不受影响，无回归问题
3. 代码质量符合项目标准：
   - 代码规范：遵循PEP 8编码规范
   - 代码结构：模块化设计，职责清晰
   - 代码注释：关键逻辑有详细注释
   - 错误处理：完善的异常处理机制
   - 性能优化：无明显性能瓶颈
4. 集成测试通过，性能表现良好

## 预设追问计划
以下是可能的追问方向，请准备相应内容：
1. 完整性追问: 链接功能是否覆盖所有预期的链接类型？
2. 深度追问: 合并过程中的冲突如何解决和验证？
3. 质量提升追问: 代码集成质量如何保证和改进？
4. 兼容性追问: 与现有功能的兼容性如何全面验证？
5. 性能追问: 链接功能对系统性能的影响如何评估？

## 下一步准备
请在任务完成后，提供一个标题为"【关键数据摘要-用于LAD-IMPL-012链接功能测试】"的部分，包含：
1. 集成结果总结和功能清单
2. 链接功能的测试要求和验证标准
3. 已知问题和限制说明
4. 测试用例设计的关键要求
5. 性能基准和监控要点

这些信息将确保链接功能得到全面和有效的测试验证。

## 输出要求
1. 修改后的完整代码
2. 功能集成说明文档
3. 集成测试用例和结果
4. 代码变更和影响分析
5. 【关键数据摘要-用于LAD-IMPL-012】
```

---

## LAD-IMPL-012: 链接功能测试 - 完整提示词

```
# LAD本地Markdown渲染器链接功能测试任务

## 会话元数据
- 任务ID: LAD-IMPL-012
- 任务类型: 功能测试
- 复杂度级别: 中等复杂
- 预计交互: 6-7次
- 依赖任务: LAD-IMPL-011
- 风险等级: 中风险

## 前序数据摘要
[从LAD-IMPL-011获取集成结果和测试要求]

## 任务背景
验证链接功能的完整性和正确性，确保链接功能与现有功能的兼容性，为系统集成测试做好准备。

## 本次任务目标
1. 验证链接功能的完整性和正确性
2. 测试各种链接类型的处理能力
3. 验证链接功能的错误处理机制
4. 确保链接功能与现有功能的兼容性

## 具体测试要求

### 1. 前置验证和集成检查
1. 验证LAD-IMPL-011的集成结果：
   - 确认链接功能集成的完整性和正确性
   - 验证与现有功能的兼容性和稳定性
   - 检查代码质量和架构设计的一致性
2. 深入了解测试环境：
   - 分析test/目录下的现有测试框架
   - 了解测试用例的设计标准和覆盖要求
   - 检查测试数据的准备和管理方式

### 2. 内部链接测试
- 锚点链接：测试页面内锚点跳转功能
- 相对路径链接：测试相对路径文件链接
- 目录链接：测试目录导航功能
- TOC链接：测试文档目录链接处理

### 3. 外部链接测试
- HTTP/HTTPS链接：测试网络链接处理
- 文件协议链接：测试本地文件链接（file://）
- 邮件链接：测试邮件链接处理（mailto:）
- 其他协议：测试特殊协议链接

### 4. 特殊链接测试
- 图片链接：测试图片链接处理和放大功能
- Mermaid图表链接：测试图表内链接处理
- 嵌套链接：测试复杂结构中的链接
- 动态链接：测试动态生成的链接

### 5. 错误处理测试
- 无效链接：测试无效链接的错误处理
- 权限问题：测试权限不足的处理
- 网络问题：测试网络不可用的处理
- 恶意链接：测试安全防护机制

### 6. 性能测试
- 大量链接：测试大量链接的处理性能
- 复杂链接：测试复杂链接的处理能力
- 并发链接：测试并发链接的处理
- 内存使用：测试链接处理的内存影响

### 7. 集成测试
- 与渲染器集成：确保链接处理不影响渲染
- 与UI集成：确保链接操作的UI反馈正常
- 与配置集成：确保链接配置生效
- 与日志集成：确保链接操作被正确记录

## 验证标准
1. 所有链接类型都能正确处理
2. 错误处理机制有效可靠
3. 性能表现符合预期
4. 与现有功能完全兼容
5. 安全机制有效防护

## 预设追问计划
以下是可能的追问方向，请准备相应内容：
1. 完整性追问: 测试是否覆盖所有链接使用场景？
2. 深度追问: 边界情况和异常情况的处理是否充分？
3. 质量提升追问: 测试自动化和回归防护如何加强？
4. 性能追问: 链接处理的性能瓶颈如何识别和优化？
5. 安全追问: 链接安全防护是否经过充分验证？

## 下一步准备
请在任务完成后，提供一个标题为"【关键数据摘要-用于LAD-IMPL-013集成测试】"的部分，包含：
1. 链接功能测试结果总结
2. 发现问题的分类和影响评估
3. 性能基准数据和瓶颈分析
4. 集成测试的重点关注领域
5. 系统整体稳定性评估要求

这些信息将为系统级集成测试提供重要参考。

## 输出要求
1. 链接功能测试报告
2. 发现问题的详细记录和解决方案
3. 性能测试结果和分析
4. 测试用例库和自动化脚本
5. 【关键数据摘要-用于LAD-IMPL-013】
```

---

## LAD-IMPL-013: 集成测试 - 完整提示词

```
# LAD本地Markdown渲染器集成测试任务

## 会话元数据
- 任务ID: LAD-IMPL-013
- 任务类型: 系统测试
- 复杂度级别: 复杂
- 预计交互: 8-9次
- 依赖任务: LAD-IMPL-012
- 风险等级: 高风险

## 前序数据摘要
[从LAD-IMPL-012获取测试结果和集成要求]

## 任务背景
验证整个系统的集成完整性，确保所有功能模块的协同工作和系统的稳定性。这是最终验收前的关键测试阶段。

## 本次任务目标
1. 验证整个系统的集成完整性
2. 测试所有功能模块的协同工作
3. 验证系统的稳定性和可靠性
4. 确保系统在各种环境下的正常运行

## 具体测试要求

### 1. 前置验证和系统检查
1. 验证LAD-IMPL-012的测试结果：
   - 确认链接功能测试的完整性和准确性
   - 验证发现问题的分类和影响评估
   - 检查性能基准数据和瓶颈分析
2. 深入了解系统架构：
   - 分析整个系统的模块依赖关系
   - 了解各模块间的接口和数据流
   - 检查系统配置和运行环境要求

### 2. 端到端测试
- 文件加载：测试文件加载的完整流程
- 渲染显示：测试渲染到显示的完整流程
- 用户交互：测试用户交互的完整流程
- 链接处理：测试链接处理的端到端流程

### 3. 模块协同测试
- 导入器与渲染器：测试模块导入和渲染的协同
- 渲染器与UI：测试渲染结果和UI显示的协同
- UI与链接处理：测试UI操作和链接处理的协同
- 配置与日志：测试配置管理和日志记录的协同

### 3. 压力测试
- 大量文件：测试大量文件的处理能力
- 复杂内容：测试复杂内容的处理能力
- 长时间运行：测试长时间运行的稳定性
- 高并发操作：测试并发操作的处理能力

### 4. 兼容性测试
- 操作系统：测试不同操作系统的兼容性
- Python版本：测试不同Python版本的兼容性
- 依赖库：测试不同依赖库版本的兼容性
- 配置环境：测试不同配置环境的兼容性

### 5. 回归测试
- 现有功能：确保现有功能不受影响
- 性能回归：确保性能没有退化
- 稳定性回归：确保稳定性没有退化
- P1-P3改进：确保所有改进功能正常

### 6. 异常场景测试
- 网络异常：测试网络问题的处理
- 文件异常：测试文件问题的处理
- 权限异常：测试权限问题的处理
- 配置异常：测试配置问题的处理

## 验证标准
1. 所有功能模块协同工作正常
2. 系统在各种环境下稳定运行
3. 性能指标符合预期要求
4. 无功能回归和性能退化
5. 异常处理机制完善有效

## 预设追问计划
以下是可能的追问方向，请准备相应内容：
1. 完整性追问: 集成测试是否覆盖所有关键集成点？
2. 深度追问: 系统瓶颈和故障点如何识别和处理？
3. 质量提升追问: 集成测试的自动化和持续化如何实现？
4. 稳定性追问: 长期运行和高负载下的稳定性如何保证？
5. 回归防护追问: 如何建立有效的回归测试机制？

## 下一步准备
请在任务完成后，提供一个标题为"【关键数据摘要-用于LAD-IMPL-014性能验证】"的部分，包含：
1. 系统集成状态总结和稳定性评估
2. 性能基准数据和监控要求
3. 已识别的性能瓶颈和优化方向
4. 性能验证的重点测试项目
5. 系统监控和性能分析的要求

这些信息将为性能验证提供准确的基准和目标。

## 输出要求
1. 集成测试报告
2. 系统稳定性评估
3. 性能基准测试结果
4. 问题记录和解决方案
5. 【关键数据摘要-用于LAD-IMPL-014】
```

---

## LAD-IMPL-014: 性能验证 - 完整提示词

```
# LAD本地Markdown渲染器性能验证任务

## 会话元数据
- 任务ID: LAD-IMPL-014
- 任务类型: 性能测试
- 复杂度级别: 中等复杂
- 预计交互: 6-7次
- 依赖任务: LAD-IMPL-013
- 风险等级: 中风险

## 前序数据摘要
[从LAD-IMPL-013获取系统状态和性能要求]

## 任务背景
验证系统性能指标符合预期，识别性能瓶颈和优化机会，建立性能基准和监控标准，为最终验收提供性能保证。

## 本次任务目标
1. 验证系统性能指标符合预期
2. 识别性能瓶颈和优化机会
3. 建立性能基准和监控标准
4. 确保系统在高负载下的稳定性

## 具体测试要求

### 1. 前置验证和基准确认
1. 验证LAD-IMPL-013的集成测试结果：
   - 确认系统集成状态的完整性和稳定性
   - 验证性能基准数据的准确性和可靠性
   - 检查已识别的性能瓶颈和优化方向
2. 深入了解性能监控：
   - 分析现有性能监控机制和指标
   - 了解性能测试工具和方法
   - 检查性能基准的建立和维护方式

### 2. 启动性能
- 应用启动时间：测量应用启动所需时间（目标：< 3秒）
- 模块加载时间：测量各模块加载时间（目标：< 1秒）
- 初始化时间：测量系统初始化时间（目标：< 2秒）
- 配置加载时间：测量配置文件加载时间（目标：< 500ms）

### 3. 渲染性能
- 小文件渲染：测试小文件的渲染时间（目标：< 100ms）
- 大文件渲染：测试大文件的渲染时间（目标：< 2秒）
- 复杂内容渲染：测试复杂内容的渲染时间（目标：< 5秒）
- 链接处理性能：测试链接处理的性能影响（目标：< 200ms）

### 4. 内存使用
- 内存占用：测量系统运行时的内存占用（目标：< 100MB）
- 内存泄漏：检测是否存在内存泄漏（目标：24小时无泄漏）
- 内存增长：监控内存使用的增长趋势（目标：增长< 10MB/小时）
- 缓存效率：评估缓存机制的内存效率（目标：缓存命中率> 80%）

### 5. 响应性能
- UI响应时间：测量UI操作的响应时间（目标：< 100ms）
- 用户交互延迟：测量用户交互的延迟（目标：< 50ms）
- 并发处理：测试并发操作的处理能力（目标：支持10个并发操作）
- 链接跳转速度：测试链接跳转的响应速度（目标：< 300ms）

### 6. 资源使用
- CPU使用率：监控CPU使用情况（目标：平均< 30%）
- 磁盘I/O：监控磁盘读写性能（目标：读写速度> 50MB/s）
- 网络请求：监控网络请求性能（如适用）（目标：响应时间< 1秒）
- 文件句柄：监控文件句柄使用情况（目标：< 100个句柄）

### 7. 性能基准
- 基线性能：建立系统性能基线
- 性能回归：对比历史性能数据
- 性能目标：验证是否达到性能目标
- 性能监控：建立持续性能监控机制

### 8. 详细性能基准值和监控指标（重要补充）

#### 8.1 启动性能基准
**应用启动性能**：
- 冷启动时间：< 3秒（从程序启动到主窗口显示）
- 热启动时间：< 1秒（程序已在内存中的重新启动）
- 模块加载时间：< 1秒（动态模块导入和初始化）
- 配置加载时间：< 500ms（所有配置文件读取和解析）
- UI初始化时间：< 800ms（主窗口和组件初始化）

**启动阶段监控指标**：
- 内存占用增长率：< 50MB/秒
- CPU使用峰值：< 80%（启动阶段）
- 磁盘I/O峰值：< 100MB/秒
- 启动失败率：< 0.1%

#### 8.2 渲染性能基准
**文件大小分级基准**：
- 小文件（< 1MB）：< 100ms（渲染到显示）
- 中等文件（1-10MB）：< 500ms
- 大文件（10-50MB）：< 2秒
- 超大文件（50-100MB）：< 5秒
- 巨大文件（> 100MB）：< 10秒或提示分页处理

**渲染复杂度基准**：
- 纯文本渲染：< 50ms/MB
- 包含图片渲染：< 200ms/MB
- 包含表格渲染：< 300ms/MB
- 包含代码块渲染：< 150ms/MB
- 包含Mermaid图表：< 1秒/图表
- 包含数学公式：< 500ms/公式

**渲染质量指标**：
- 渲染准确率：> 99.9%（与标准Markdown规范对比）
- 样式一致性：> 98%（与预期样式对比）
- 链接有效性：> 99%（内部链接解析正确率）

#### 8.3 响应性能基准
**UI交互响应**：
- 按钮点击响应：< 50ms
- 菜单展开响应：< 30ms
- 文件切换响应：< 100ms
- 搜索结果显示：< 200ms
- 滚动响应延迟：< 16ms（60FPS）

**用户操作延迟**：
- 文件打开延迟：< 300ms（小文件）
- 文件保存延迟：< 100ms
- 设置修改生效：< 50ms
- 主题切换延迟：< 200ms
- 窗口缩放响应：< 100ms

**并发处理能力**：
- 支持并发操作数：> 10个
- 队列处理延迟：< 50ms
- 线程切换开销：< 5ms
- 锁获取延迟：< 1ms

#### 8.4 内存使用基准
**内存占用限制**：
- 基础内存占用：< 50MB（空载状态）
- 正常使用内存：< 100MB（打开1个中等文件）
- 峰值内存占用：< 200MB（打开多个大文件）
- 内存增长率：< 10MB/小时（长期运行）
- 内存回收效率：> 90%（文件关闭后）

**缓存内存管理**：
- 缓存命中率：> 80%
- 缓存内存占用：< 30MB
- 缓存清理触发阈值：内存使用 > 150MB
- 缓存重建时间：< 1秒

**内存泄漏检测**：
- 24小时运行内存增长：< 50MB
- 文件操作内存泄漏：0MB/操作
- 渲染操作内存泄漏：0MB/渲染
- 缓存操作内存泄漏：0MB/缓存操作

#### 8.5 资源使用基准
**CPU使用限制**：
- 空闲状态CPU：< 5%
- 正常使用CPU：< 30%
- 渲染时CPU峰值：< 80%
- 长期平均CPU：< 20%

**磁盘I/O性能**：
- 文件读取速度：> 50MB/s
- 文件写入速度：> 30MB/s
- 缓存读写速度：> 100MB/s
- 配置文件访问：< 10ms

**网络性能（如适用）**：
- HTTP请求响应：< 1秒
- 图片加载时间：< 2秒
- 外链验证时间：< 500ms
- 网络超时设置：5秒

#### 8.6 性能监控告警阈值
**关键性能告警**：
- 启动时间 > 5秒：严重告警
- 渲染时间 > 10秒：严重告警
- 内存使用 > 300MB：警告告警
- CPU持续 > 90%：严重告警
- 响应时间 > 1秒：警告告警

**性能退化检测**：
- 性能下降 > 20%：触发调查
- 内存增长 > 50%：触发清理
- 响应延迟 > 2倍：触发优化
- 错误率 > 1%：触发修复

**自动优化触发**：
- 缓存命中率 < 70%：优化缓存策略
- 内存使用 > 80%：触发内存清理
- CPU使用 > 70%：降低处理优先级
- 磁盘空间 < 1GB：清理临时文件

## 验证标准
1. 性能指标符合预期要求
2. 系统在高负载下稳定运行
3. 内存使用合理，无泄漏
4. 响应时间满足用户体验要求
5. 资源使用效率高

## 预设追问计划
以下是可能的追问方向，请准备相应内容：
1. 完整性追问: 性能测试是否覆盖所有关键性能指标？
2. 深度追问: 性能瓶颈的根本原因如何深入分析？
3. 质量提升追问: 性能优化的效果如何量化评估？
4. 持续监控追问: 如何建立长期的性能监控体系？
5. 优化策略追问: 性能优化的优先级和实施路径如何确定？

## 下一步准备
请在任务完成后，提供一个标题为"【关键数据摘要-用于LAD-IMPL-015最终验收】"的部分，包含：
1. 性能指标总结和达标情况
2. 性能基准数据和监控建议
3. 已知性能限制和使用建议
4. 系统质量评估和改进建议
5. 最终验收的关键检查点

这些信息将为最终验收提供完整的质量保证数据。

## 输出要求
1. 性能验证报告
2. 性能基准数据
3. 优化建议和改进方案
4. 性能监控配置
5. 【关键数据摘要-用于LAD-IMPL-015】
```

---

## LAD-IMPL-015: 最终验收 - 完整提示词

```
# LAD本地Markdown渲染器最终验收任务

## 会话元数据
- 任务ID: LAD-IMPL-015
- 任务类型: 验收测试
- 复杂度级别: 中等复杂
- 预计交互: 5-6次
- 依赖任务: LAD-IMPL-014
- 风险等级: 低风险

## 前序数据摘要
[从LAD-IMPL-014获取性能指标和验收标准]

## 任务背景
验证系统功能完整性，确认系统质量达到交付标准，验证文档完整性和准确性，准备系统交付和部署。

## 本次任务目标
1. 验证系统功能完整性
2. 确认系统质量达到交付标准
3. 验证文档完整性和准确性
4. 准备系统交付和部署

## 具体验收要求

### 1. 前置验证和准备确认
1. 验证LAD-IMPL-014的性能验证结果：
   - 确认性能指标达标情况和基准数据
   - 验证性能监控配置和持续监控机制
   - 检查已知性能限制和使用建议
2. 深入了解验收标准：
   - 分析项目验收标准和交付要求
   - 了解质量保证流程和检查点
   - 检查文档完整性和准确性要求

### 2. 功能验收
#### 2.1 核心功能验收
- 模块导入功能：配置驱动的动态导入
- 渲染功能：完整的Markdown渲染能力
- UI功能：状态栏显示和用户交互
- 链接功能：全类型链接处理能力

#### 2.2 扩展功能验收
- 函数映射验证：完整性校验机制
- 缓存功能：优化的缓存机制
- 日志功能：结构化日志系统
- 错误处理：完善的错误处理机制

#### 2.3 集成功能验收
- 系统集成：所有模块协同工作
- 配置集成：统一的配置管理
- 监控集成：完整的系统监控
- 测试集成：自动化测试体系

### 3. 质量验收
#### 3.1 代码质量验收
- 代码规范：符合项目编码标准
- 代码结构：清晰的模块结构
- 代码注释：完整的代码文档
- 代码测试：充分的测试覆盖

#### 3.2 文档质量验收
- 技术文档：完整的技术文档
- 用户文档：清晰的使用指南
- API文档：准确的接口文档
- 维护文档：详细的维护指南

#### 3.3 测试质量验收
- 测试覆盖：全面的测试覆盖
- 测试用例：完整的测试用例
- 测试报告：详细的测试报告
- 测试自动化：可重复的自动化测试

### 4. 性能验收
#### 4.1 性能指标验收
- 启动性能：应用启动时间 < 3秒
- 渲染性能：大文件渲染时间 < 2秒
- 响应性能：UI响应时间 < 100ms
- 内存使用：正常使用 < 100MB

#### 4.2 稳定性验收
- 长期运行：24小时连续运行无崩溃
- 高负载：大量文件处理稳定
- 异常处理：各种异常情况graceful处理
- 资源回收：无内存泄漏和资源泄漏

#### 4.3 可靠性验收
- 错误恢复：错误后能正确恢复
- 数据完整：处理过程数据完整
- 配置兼容：不同配置环境兼容
- 版本兼容：向后兼容性保证

### 5. 安全验收
#### 5.1 安全检查
- 输入验证：恶意输入防护
- 文件访问：文件访问权限控制
- 链接安全：恶意链接防护
- 配置安全：敏感配置保护

#### 5.2 漏洞扫描
- 代码扫描：静态代码安全扫描
- 依赖扫描：第三方依赖安全扫描
- 运行时扫描：运行时安全检查
- 配置扫描：配置安全检查

#### 5.3 权限验证
- 文件权限：文件访问权限正确
- 目录权限：目录访问权限正确
- 网络权限：网络访问权限合理
- 系统权限：系统资源访问权限适当

### 6. 交付准备
#### 6.1 交付清单
- 源代码：完整的源代码包
- 文档：完整的文档包
- 测试：完整的测试包
- 配置：标准的配置模板

#### 6.2 部署准备
- 安装脚本：自动化安装脚本
- 配置指南：部署配置指南
- 运维手册：系统运维手册
- 故障排除：常见问题解决方案

## 验证标准
1. 所有功能正常工作
2. 系统质量达到交付标准
3. 文档完整准确
4. 系统安全可靠
5. 交付物完整

## 预设追问计划
以下是可能的追问方向，请准备相应内容：
1. 完整性追问: 验收是否覆盖所有交付要求？
2. 深度追问: 质量标准是否达到行业最佳实践？
3. 质量提升追问: 如何确保交付质量的持续性？
4. 风险追问: 部署和使用过程中的潜在风险如何控制？
5. 改进追问: 基于验收结果的后续改进计划如何制定？

## 下一步准备
请在验收完成后，提供一个标题为"【关键数据摘要-用于LAD-IMPL-016高级功能增强】"的部分，包含：
1. 验收结果总结和系统状态
2. 系统质量评估和改进空间
3. 已知限制和后续优化方向
4. P4级别改进的实施条件评估
5. 系统维护和升级建议

这些信息将为后续的高级功能增强提供基础。

## 输出要求
1. 最终验收报告
2. 系统交付文档
3. 部署指南和运维手册
4. 质量评估报告
5. 【关键数据摘要-用于LAD-IMPL-016】
```

---

## 文档使用说明

### 1. 提示词使用流程
1. **任务准备**: 复制对应任务的完整提示词
2. **数据准备**: 从前序任务获取"关键数据摘要"部分
3. **任务执行**: 按照提示词要求执行任务
4. **追问执行**: 根据预设追问计划深化分析
5. **数据传递**: 生成"下一步准备"要求的数据摘要

### 2. 质量保证要求
- 每个任务必须完整执行预设追问计划
- 每个任务必须生成标准格式的数据摘要
- 所有代码修改必须遵循备份和验证规范
- 所有输出必须符合项目质量标准

### 3. 风险控制措施
- 高风险任务需要额外的验证步骤
- 所有修改必须有完整的回滚方案
- 关键功能修改需要多轮测试验证
- 及时记录和解决发现的问题

---

**文档状态**: 已确认，作为任务执行的标准指导  
**最后更新**: 2025-01-27 16:25:00  
**版本**: V3.6  
**下次评估**: 各任务完成后  
**更新内容**: 
- V3.2: 最终完善了遗漏的关键资料和文档整合，细化了性能基准指标和代码质量标准
- V3.3: 补充线程安全实现方案到006A任务，详细化009任务测试场景，完善014任务性能基准值
- V3.4: 完善006A任务必需输入文件清单，补充线程安全实现专项文档，详细化文档使用说明
- V3.5: 在具体实施要求中明确引用线程安全清单，确保实现时严格按照清单执行
- V3.6: 完善任务目标、前序数据摘要、下一步准备和预设追问计划，全面强化线程安全要求