# LAD-IMPL-007 V4.2附录B：UI组件完整代码

**主文档**: LAD-IMPL-007-UI状态栏更新-完整提示词V4.2-架构对齐版-主文档.md  
**附录类型**: UI组件完整代码  
**创建时间**: 2025-10-13 10:54:33  
**内容**: DynamicModuleImporter新方法、MainWindow完整实现  
**代码量**: 约1000行  

---

## 📦 组件1：DynamicModuleImporter新增方法（完整）

**文件位置**: `core/dynamic_module_importer.py`（修改）  
**新增代码**: 约250行  

### 完整新增代码

```python
# core/dynamic_module_importer.py 新增方法

from typing import List, Dict, Any


def get_last_import_snapshot(self, config_manager=None) -> Dict[str, Any]:
    """获取最近一次导入结果的精简快照，供UI状态栏使用
    
    ⚠️ 架构对齐（第1份文档第42-72行标准）：
    - 快照类型：module_import_snapshot（标准名称）
    - 模块字段：module（不是module_name）
    - 必须包含：non_callable_functions字段
    - 所有字段符合第1份文档JSON Schema
    
    功能：
    - 封装导入器内部状态为标准快照格式
    - 提供UI友好的数据接口
    - 集成简化配置信息
    - 包含correlation_id用于三方关联
    
    Returns:
        dict: 符合第1份架构文档标准的快照格式 {
            "snapshot_type": "module_import_snapshot",
            "module": "markdown_processor",
            "function_mapping_status": "complete" | "incomplete" | "import_failed",
            "required_functions": [...],
            "available_functions": [...],
            "missing_functions": [],
            "non_callable_functions": [],  # ⚠️ 必须包含
            "path": "/path" or None,
            "used_fallback": bool,
            "error_code": "",
            "message": "",
            "timestamp": "ISO8601",
            "correlation_id": "..." or None
        }
    """
    from datetime import datetime
    
    # 获取配置管理器
    if not config_manager:
        from utils.config_manager import ConfigManager
        config_manager = ConfigManager()
    
    # 获取模块配置（从external_modules.json）
    module_config = config_manager.get_external_module_config("markdown_processor")
    
    # 获取当前关联ID（如果有）
    from core.correlation_id_manager import CorrelationIdManager
    corr_manager = CorrelationIdManager()
    correlation_id = corr_manager.get_current_correlation_id("importer")
    
    # ⚠️ 按第1份架构文档标准格式构建快照（第42-72行）
    snapshot = {
        # 元数据（架构标准）
        "snapshot_type": "module_import_snapshot",  # ⚠️ 标准类型名
        "module": "markdown_processor",  # ⚠️ 标准字段名（不是module_name）
        
        # 函数映射状态（架构标准）
        "function_mapping_status": self._get_function_mapping_status(),
        "required_functions": module_config.get("required_functions", []),
        "available_functions": self._get_available_functions(),
        "missing_functions": self._get_missing_functions(),
        "non_callable_functions": self._get_non_callable_functions(),  # ⚠️ 第1份文档要求
        
        # 路径和fallback（架构标准）
        "path": getattr(self, '_module_path', None),
        "used_fallback": getattr(self, '_used_fallback', False),
        
        # 错误信息（架构标准）
        "error_code": getattr(self, '_last_error_code', ''),
        "message": getattr(self, '_last_message', ''),
        
        # 时间戳（架构标准，ISO8601格式）
        "timestamp": datetime.now().isoformat(),
        
        # 关联ID（第2份文档要求，用于三方关联）
        "correlation_id": correlation_id
    }
    
    return snapshot

def _get_function_mapping_status(self) -> str:
    """获取函数映射状态
    
    ⚠️ 架构标准值（第1份文档第63行）：
    - "complete": 所有必需函数都存在且可调用
    - "incomplete": 部分函数缺失或存在但不可调用
    - "import_failed": 模块导入失败
    
    Returns:
        str: complete | incomplete | import_failed
    """
    # 如果模块未导入或为None
    if not hasattr(self, '_module') or self._module is None:
        return "import_failed"
    
    # 获取必需函数列表
    required = getattr(self, '_required_functions', [])
    if not required:
        # 如果没有必需函数，认为是complete
        return "complete"
    
    # 获取可用函数和不可调用函数
    available = self._get_available_functions()
    non_callable = self._get_non_callable_functions()
    
    # 如果有不可调用的函数，也算incomplete
    if non_callable:
        return "incomplete"
    
    # 检查缺失函数
    missing = set(required) - set(available)
    
    return "complete" if not missing else "incomplete"

def _get_available_functions(self) -> List[str]:
    """获取可用函数列表（存在且可调用的函数）
    
    Returns:
        list: 可用函数名称列表
    """
    if not hasattr(self, '_module') or self._module is None:
        return []
    
    available = []
    required = getattr(self, '_required_functions', [])
    
    for func_name in required:
        if hasattr(self._module, func_name):
            attr = getattr(self._module, func_name)
            if callable(attr):
                available.append(func_name)
    
    return available

def _get_missing_functions(self) -> List[str]:
    """获取缺失函数列表（完全不存在的函数）
    
    Returns:
        list: 缺失函数名称列表
    """
    if not hasattr(self, '_module') or self._module is None:
        # 如果模块未导入，所有必需函数都算缺失
        required = getattr(self, '_required_functions', [])
        return required
    
    required = getattr(self, '_required_functions', [])
    existing = []
    
    for func_name in required:
        if hasattr(self._module, func_name):
            existing.append(func_name)
    
    return list(set(required) - set(existing))

def _get_non_callable_functions(self) -> List[str]:
    """获取不可调用的函数列表（存在但不可调用）
    
    ⚠️ 第1份架构文档要求的字段（第66行）
    
    说明：
    - 某些情况下，模块可能定义了函数名，但不是函数（如类属性）
    - 这种情况需要标识出来，与missing_functions区分
    
    Returns:
        list: 不可调用函数名称列表
    """
    if not hasattr(self, '_module') or self._module is None:
        return []
    
    non_callable = []
    required = getattr(self, '_required_functions', [])
    
    for func_name in required:
        if hasattr(self._module, func_name):
            attr = getattr(self._module, func_name)
            if not callable(attr):
                non_callable.append(func_name)
    
    return non_callable

def set_correlation_id(self, correlation_id: str):
    """设置关联ID（新增方法，供UI传递）
    
    Args:
        correlation_id: 关联ID字符串
    
    用途：
    - UI在触发模块导入前设置correlation_id
    - 导入过程使用此ID进行日志记录和快照保存
    - 实现关联ID在组件间的传播
    
    Example:
        # 在MainWindow中
        correlation_id = CorrelationIdManager.generate_correlation_id("ui_action", "file_select")
        self.dynamic_importer.set_correlation_id(correlation_id)
        self.dynamic_importer.import_module("markdown_processor")
    """
    self._correlation_id = correlation_id
    
    # 同步到CorrelationIdManager（全局管理）
    from core.correlation_id_manager import CorrelationIdManager
    corr_manager = CorrelationIdManager()
    corr_manager.set_current_correlation_id("importer", correlation_id)

def get_correlation_id(self) -> Optional[str]:
    """获取当前关联ID
    
    Returns:
        str: 当前关联ID，如果没有则返回None
    """
    return getattr(self, '_correlation_id', None)
```

---

## 📦 组件2：MainWindow完整实现

**文件位置**: `ui/main_window.py`（大量修改）  
**修改代码**: 约800行  

### 完整代码（关键部分）

```python
# ui/main_window.py

from PyQt6.QtWidgets import QMainWindow, QStatusBar
from PyQt6.QtCore import QMetaObject, Qt, QTimer
from ui.status_events import StatusChangeEvent, StatusEventEmitter
from core.correlation_id_manager import CorrelationIdManager
import threading
import time
from typing import Callable, Dict, Any


class MainWindow(QMainWindow):
    """主窗口（集成007任务的所有架构组件）"""
    
    def __init__(self):
        super().__init__()
        
        # ... 现有初始化代码保持不变 ...
        
        # 初始化006A架构组件（标准顺序，重要）
        self.initialize_architecture_components()
        
        # 创建关联ID管理器（单例）
        self.correlation_manager = CorrelationIdManager()
        
        # 创建状态事件发射器
        self.status_event_emitter = StatusEventEmitter()
        
        # 存储上次状态（用于变更检测）
        self._last_module_status = None
        self._last_render_status = None
        
        # 设置状态更新触发器
        self.setup_status_update_triggers()
    
    def initialize_architecture_components(self):
        """初始化006A架构组件（严格按标准顺序）
        
        ⚠️ 初始化顺序不可颠倒（避免循环依赖）：
        1. 基础层：ConfigManager、UnifiedCacheManager
        2. 监控层：PerformanceMetrics、ErrorCodeManager
        3. 快照层：SnapshotManager
        4. 状态层：ApplicationStateManager
        5. 验证层：ConfigValidator
        """
        from utils.config_manager import ConfigManager
        from core.application_state_manager import ApplicationStateManager
        from core.snapshot_manager import SnapshotManager
        from core.unified_cache_manager import UnifiedCacheManager
        from core.performance_metrics import PerformanceMetrics
        from core.error_code_manager import ErrorCodeManager
        from core.config_validator import ConfigValidator
        
        # 步骤1：基础层
        self.config_manager = ConfigManager()
        self.cache_manager = UnifiedCacheManager()
        
        # 步骤2：监控层
        self.performance_metrics = PerformanceMetrics(self.config_manager)
        self.error_manager = ErrorCodeManager(self.config_manager)
        
        # 步骤3：快照层
        self.snapshot_manager = SnapshotManager(self.config_manager)
        self.snapshot_manager.set_cache_manager(self.cache_manager)
        
        # 步骤4：状态层
        self.state_manager = ApplicationStateManager(self.config_manager)
        self.state_manager.set_snapshot_manager(self.snapshot_manager)
        self.state_manager.set_performance_metrics(self.performance_metrics)
        
        # 步骤5：验证层
        self.validator = ConfigValidator(self.config_manager)
    
    def setup_status_update_triggers(self):
        """设置状态更新触发器"""
        # 初始更新
        self.update_status_bar()
        
        # 定时更新（可选，用于轮询）
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(5000)  # 每5秒更新一次
    
    def update_status_bar(self):
        """更新状态栏（架构对齐版，集成所有架构标准）
        
        ⚠️ 架构对齐要点：
        1. 使用PerformanceMetrics标准方法（start_timer/end_timer）
        2. 生成和传播correlation_id
        3. 获取符合第1份文档格式的快照
        4. 发射包含correlation_id的事件
        5. 使用架构标准的UI映射规则
        6. 使用错误严重度分级
        """
        # 步骤1：生成关联ID（第2份文档标准）
        correlation_id = CorrelationIdManager.generate_correlation_id(
            operation_type="ui_action",
            component="status_bar"
        )
        self.correlation_manager.set_current_correlation_id("ui", correlation_id)
        
        # 步骤2：启动性能计时（第1份文档标准方法）
        timer_id = self.performance_metrics.start_timer(
            name='status_bar_update',
            correlation_id=correlation_id  # ⚠️ 传递关联ID
        )
        
        try:
            # 步骤3：获取当前状态（符合第1份文档快照格式）
            current_module_status = self._get_module_status_safe()
            current_render_status = self._get_render_status_safe()
            
            # 步骤4：检测并发射状态变更事件（传递correlation_id）
            self._check_and_emit_status_changes(
                current_module_status,
                current_render_status,
                correlation_id  # ⚠️ 传递关联ID
            )
            
            # 步骤5：构建状态消息和颜色（基于架构映射规则）
            status_message = self._build_status_message(
                current_module_status,
                current_render_status
            )
            status_color = self._get_status_color(current_module_status)
            
            # 步骤6：更新UI
            self.statusBar().showMessage(status_message)
            self.statusBar().setStyleSheet(f"background-color: {status_color};")
            
            # 步骤7：记录成功指标
            self.performance_metrics.increment_counter('status_bar_update_success_count')
            
        except AttributeError as e:
            # 006A组件不可用
            self.statusBar().showMessage("⚠️ 状态管理器不可用，请检查006A任务是否完成")
            self.statusBar().setStyleSheet("background-color: orange;")
            self.performance_metrics.increment_counter('status_bar_update_failure_count')
            
        except Exception as e:
            # 其他错误
            error_msg = f"❌ 状态更新错误: {str(e)}"
            self.statusBar().showMessage(error_msg)
            self.statusBar().setStyleSheet("background-color: red;")
            self.performance_metrics.increment_counter('status_bar_update_failure_count')
        
        finally:
            # 步骤8：结束计时（自动记录到直方图）
            duration_ms = self.performance_metrics.end_timer(timer_id)
            
            # 性能告警
            if duration_ms > 100:
                print(f"⚠️ 状态栏更新耗时过长: {duration_ms:.2f}ms")
            
            # 清除关联ID
            self.correlation_manager.clear_correlation_id("ui")
    
    def _get_module_status_safe(self) -> dict:
        """安全获取模块状态（符合第1份文档快照格式）
        
        Returns:
            dict: 符合第1份文档第42-72行标准的模块快照
        """
        try:
            # 优先使用P2改进的接口
            if hasattr(self, 'dynamic_importer') and \
               hasattr(self.dynamic_importer, 'get_last_import_snapshot'):
                snapshot = self.dynamic_importer.get_last_import_snapshot(self.config_manager)
                
                # ⚠️ 验证快照格式符合第1份文档标准
                assert snapshot.get('snapshot_type') == 'module_import_snapshot', \
                    f"快照类型错误: {snapshot.get('snapshot_type')}，应为'module_import_snapshot'"
                assert 'module' in snapshot, "缺少'module'字段（应为'module'，不是'module_name'）"
                assert 'non_callable_functions' in snapshot, "缺少'non_callable_functions'字段（第1份文档第66行要求）"
                
                return snapshot
            else:
                # 降级使用ApplicationStateManager
                return self.state_manager.get_module_status("markdown_processor")
        
        except Exception as e:
            # 返回默认快照（符合架构格式）
            return self._get_default_module_snapshot(str(e))
    
    def _get_default_module_snapshot(self, error_message: str = "") -> dict:
        """获取默认模块快照（符合第1份文档格式）"""
        from datetime import datetime
        
        return {
            "snapshot_type": "module_import_snapshot",
            "module": "markdown_processor",
            "function_mapping_status": "import_failed",
            "required_functions": [],
            "available_functions": [],
            "missing_functions": [],
            "non_callable_functions": [],
            "path": None,
            "used_fallback": False,
            "error_code": "SYSTEM_ERROR",
            "message": error_message or "Unknown error",
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_render_status_safe(self) -> dict:
        """安全获取渲染状态"""
        try:
            return self.state_manager.get_render_status()
        except Exception as e:
            return {
                "snapshot_type": "render_snapshot",
                "renderer_type": "unknown",
                "reason": "error",
                "details": {"error_message": str(e)},
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_and_emit_status_changes(
        self, 
        current_module_status: dict, 
        current_render_status: dict,
        correlation_id: str  # ⚠️ 关联ID参数
    ):
        """检测状态变更并发射事件（集成correlation_id）"""
        # 检测模块状态变更
        if self._has_module_status_changed(current_module_status):
            event = StatusChangeEvent.create_module_change_event(
                old_status=self._last_module_status or {},
                new_status=current_module_status,
                change_reason=self._determine_module_change_reason(
                    self._last_module_status,
                    current_module_status
                ),
                module_name=current_module_status.get("module", "markdown_processor"),
                correlation_id=correlation_id  # ⚠️ 传递关联ID
            )
            self.status_event_emitter.emit_event(event)
            self._last_module_status = current_module_status.copy()
        
        # 检测渲染状态变更
        if self._has_render_status_changed(current_render_status):
            event = StatusChangeEvent.create_render_change_event(
                old_status=self._last_render_status or {},
                new_status=current_render_status,
                change_reason=self._determine_render_change_reason(
                    self._last_render_status,
                    current_render_status
                ),
                correlation_id=correlation_id  # ⚠️ 传递关联ID
            )
            self.status_event_emitter.emit_event(event)
            self._last_render_status = current_render_status.copy()
    
    def _build_status_message(self, module_status: dict, render_status: dict) -> str:
        """构建状态消息（使用架构标准字段）"""
        # 获取配置的状态消息模板
        app_config = self.config_manager.get_config("app_config") or {}
        ui_config = app_config.get("ui", {})
        status_messages = ui_config.get("status_bar_messages", {})
        
        # 使用架构标准字段名（第1份文档）
        module_name = module_status.get("module", "unknown")  # ⚠️ 不是module_name
        mapping_status = module_status.get("function_mapping_status", "unknown")
        
        # 检查导入失败
        if mapping_status == "import_failed":
            error_code = module_status.get("error_code", "")
            error_msg = module_status.get("message", "未知错误")
            
            # ⚠️ 使用错误严重度分级（第1份文档第676-692行）
            if error_code:
                severity = self.error_manager.get_error_severity(error_code)
                severity_icon = {
                    "critical": "🔴",
                    "error": "❌",
                    "warning": "⚠️"
                }.get(severity, "❌")
                
                return f"{severity_icon} [{error_code}] {error_msg}"
            else:
                return f"❌ 导入失败: {error_msg}"
        
        # ⚠️ 检查不可调用函数（第1份文档标准字段）
        non_callable = module_status.get("non_callable_functions", [])
        if non_callable:
            return f"⚠️ 函数存在但不可调用: {', '.join(non_callable)}"
        
        # 检查函数映射不完整
        if mapping_status == "incomplete":
            missing = module_status.get("missing_functions", [])
            return f"⚠️ 函数映射不完整，缺失: {', '.join(missing)}"
        
        # 成功状态
        renderer_type = render_status.get("renderer_type", "unknown")
        
        # 从配置获取消息模板
        if mapping_status in status_messages:
            template = status_messages[mapping_status]
            return template.get("text", f"✅ {module_name}就绪 | 渲染器: {renderer_type}")
        
        # 默认消息
        return f"✅ {module_name} | 渲染器: {renderer_type}"
    
    def _get_status_color(self, module_status: dict) -> str:
        """获取状态颜色（符合第1份文档UI映射规则）
        
        ⚠️ 架构标准（第1份文档第99-103行）：
        - function_mapping_status: complete → 绿色
        - function_mapping_status: incomplete → 黄色
        - function_mapping_status: import_failed → 红色
        
        ⚠️ 错误严重度影响（第1份文档第676-692行）：
        - critical错误 → 深红色
        - error错误 → 红色
        - warning警告 → 黄色
        """
        # 获取颜色配置（从ui_config.json）
        ui_config = self.config_manager.get_config("ui_config") or {}
        colors = ui_config.get("colors", {
            "success": "#90EE90",  # 绿色
            "warning": "#FFD700",  # 黄色
            "error": "#FF6B6B",    # 红色
            "critical": "#8B0000", # 深红色
            "disabled": "#D3D3D3", # 灰色
            "default": "#F0F0F0"
        })
        
        # 检查错误严重度（第1份文档第676-692行）
        error_code = module_status.get("error_code", "")
        if error_code:
            severity = self.error_manager.get_error_severity(error_code)
            severity_color_map = {
                "critical": colors.get("critical", "darkred"),
                "error": colors.get("error", "red"),
                "warning": colors.get("warning", "yellow")
            }
            return severity_color_map.get(severity, colors.get("error", "red"))
        
        # ⚠️ 架构标准映射（第1份文档第100行）
        mapping_status = module_status.get("function_mapping_status", "unknown")
        color_map = {
            "complete": colors.get("success", "green"),      # 架构标准：绿色
            "incomplete": colors.get("warning", "yellow"),   # 架构标准：黄色
            "import_failed": colors.get("error", "red")      # 架构标准：红色
        }
        
        return color_map.get(mapping_status, colors.get("default", "lightgray"))
    
    def on_file_selected(self, file_path: str):
        """文件选择事件（关联ID传播起点）
        
        ⚠️ 架构标准流程（第2份续2第302-333行）：
        1. 生成correlation_id
        2. 设置到关联ID管理器
        3. 传播到所有组件（importer、renderer）
        4. 执行文件加载
        5. 更新状态栏（会使用correlation_id）
        6. 操作完成后清除correlation_id
        """
        # 步骤1：生成关联ID
        correlation_id = CorrelationIdManager.generate_correlation_id(
            operation_type="ui_action",
            component="file_select"
        )
        
        # 步骤2：设置到关联ID管理器
        self.correlation_manager.set_current_correlation_id("ui", correlation_id)
        
        # 步骤3：传播到DynamicModuleImporter
        if hasattr(self, 'dynamic_importer'):
            self.dynamic_importer.set_correlation_id(correlation_id)
        
        # 步骤4：传播到MarkdownRenderer（为后续任务准备）
        if hasattr(self, 'markdown_renderer') and \
           hasattr(self.markdown_renderer, 'set_correlation_id'):
            self.markdown_renderer.set_correlation_id(correlation_id)
        
        # 步骤5：执行文件加载
        try:
            self._load_file(file_path)
            
            # 步骤6：更新状态栏（会生成StatusChangeEvent，包含correlation_id）
            self.update_status_bar()
            
        finally:
            # 步骤7：清除关联ID
            self.correlation_manager.clear_correlation_id("ui")
    
    # 为008任务提供的公开接口
    def register_status_event_listener(self, listener: Callable):
        """注册状态事件监听器（供008任务StateChangeListener使用）
        
        Args:
            listener: 回调函数或实现__call__的对象
                - 回调函数签名：listener(event: StatusChangeEvent) -> None
                - 或者是实现了__call__(self, event: StatusChangeEvent)的类实例
        
        Example（008任务使用）:
            from core.state_change_listener import StateChangeListener
            from core.enhanced_logger import EnhancedLogger
            
            logger = EnhancedLogger('lad.ui')
            listener = StateChangeListener(logger)
            main_window.register_status_event_listener(listener)
        """
        self.status_event_emitter.add_listener(listener)
    
    def unregister_status_event_listener(self, listener: Callable):
        """注销状态事件监听器"""
        self.status_event_emitter.remove_listener(listener)
    
    def get_ui_snapshot_data(self) -> dict:
        """获取UI状态快照数据（供008任务日志记录使用）
        
        Returns:
            dict: {
                "current_module_status": dict（符合第1份文档格式）,
                "current_render_status": dict（符合第1份文档格式）,
                "status_bar_text": str,
                "event_history": List[dict],
                "current_correlation_id": str or None
            }
        """
        return {
            "current_module_status": self._last_module_status,
            "current_render_status": self._last_render_status,
            "status_bar_text": self.statusBar().currentMessage(),
            "event_history": [e.to_dict() for e in self.status_event_emitter.get_event_history(10)],
            "current_correlation_id": self.correlation_manager.get_current_correlation_id("ui")
        }
```

（MainWindow其他辅助方法见主文档步骤6）

---

**附录B结束**  
**内容**: DynamicModuleImporter新方法、MainWindow完整代码  
**代码行数**: 约800行  
**下一个附录**: 附录C - 测试用例和详细清单

