# LAD-IMPL-007 实施代码Part2（续前文）

本文件是 `LAD-IMPL-007-UI状态栏更新-完整提示词V4.1-简化配置版本.md` 的补充代码部分

---

## 步骤3续：创建事件发射器

在 `ui/status_events.py` 中继续添加：

```python
from typing import Callable, List
import threading


class StatusEventEmitter:
    """状态事件发射器（观察者模式）
    
    功能：
    1. 管理事件监听器
    2. 发射状态变更事件
    3. 记录事件历史（供调试）
    4. 线程安全的事件通知
    
    用途：
    - 007任务：生成状态变更事件
    - 008任务：注册监听器记录日志
    """
    
    def __init__(self, max_history: int = 100):
        self._listeners: List[Callable] = []
        self._event_history: List[StatusChangeEvent] = []
        self._max_history = max_history
        self._lock = threading.RLock()
    
    def add_listener(self, listener: Callable):
        """添加事件监听器（供008任务日志系统注册）
        
        Args:
            listener: 回调函数，签名为 listener(event: StatusChangeEvent)
        
        Example:
            def log_handler(event: StatusChangeEvent):
                logger.info(f"状态变更: {event.event_type}")
            
            emitter.add_listener(log_handler)
        """
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable):
        """移除事件监听器"""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
    
    def emit_event(self, event: StatusChangeEvent):
        """发射状态变更事件
        
        Args:
            event: 状态变更事件对象
        
        行为：
        1. 记录到事件历史
        2. 通知所有监听器
        3. 异常监听器不影响其他监听器
        """
        with self._lock:
            # 记录事件历史
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            # 通知所有监听器（在锁外执行，避免死锁）
            listeners_copy = self._listeners.copy()
        
        # 在锁外通知监听器
        for listener in listeners_copy:
            try:
                listener(event)
            except Exception as e:
                print(f"[StatusEventEmitter] 监听器错误: {e}")
    
    def get_event_history(self, count: int = None) -> List[StatusChangeEvent]:
        """获取事件历史
        
        Args:
            count: 获取最近N个事件，None表示全部
        
        Returns:
            事件列表（最新的在后面）
        """
        with self._lock:
            if count is None:
                return self._event_history.copy()
            return self._event_history[-count:].copy() if count > 0 else []
    
    def clear_history(self):
        """清空事件历史"""
        with self._lock:
            self._event_history.clear()
    
    def get_listener_count(self) -> int:
        """获取监听器数量"""
        with self._lock:
            return len(self._listeners)
```

---

## 步骤4：实现DynamicModuleImporter新接口（P2改进）

在 `core/dynamic_module_importer.py` 中新增方法：

```python
def get_last_import_snapshot(self, config_manager=None) -> Dict[str, Any]:
    """获取最近一次导入结果的精简快照，供UI状态栏使用
    
    功能：
    - 封装导入器内部状态
    - 提供UI友好的数据格式
    - 集成简化配置信息
    
    Returns:
        dict: {
            "module_name": "markdown_processor",
            "config_enabled": True,
            "config_version": "1.0.0",
            "import_status": "success",  # success/failed/not_imported
            "function_mapping_status": "complete",  # complete/incomplete/import_failed
            "required_functions": ["func1", "func2"],
            "available_functions": ["func1", "func2"],
            "missing_functions": [],
            "error_code": "",  # 如果有错误
            "error_message": "",  # 如果有错误
            "timestamp": "2025-10-11T16:00:00.000Z"
        }
    """
    from datetime import datetime
    
    if not config_manager:
        from utils.config_manager import ConfigManager
        config_manager = ConfigManager()
    
    # 获取模块配置
    module_config = config_manager.get_external_module_config("markdown_processor")
    
    # 获取导入状态
    import_status = getattr(self, '_last_import_status', 'not_imported')
    
    # 获取函数映射状态
    function_mapping_status = self._get_function_mapping_status()
    
    # 获取函数列表
    required_functions = module_config.get("required_functions", [])
    available_functions = self._get_available_functions()
    missing_functions = list(set(required_functions) - set(available_functions))
    
    # 获取错误信息
    error_code = getattr(self, '_last_error_code', '')
    error_message = getattr(self, '_last_error_message', '')
    
    snapshot = {
        "module_name": "markdown_processor",
        "config_enabled": module_config.get("enabled", False),
        "config_version": module_config.get("version", "unknown"),
        "import_status": import_status,
        "function_mapping_status": function_mapping_status,
        "required_functions": required_functions,
        "available_functions": available_functions,
        "missing_functions": missing_functions,
        "error_code": error_code,
        "error_message": error_message,
        "timestamp": datetime.now().isoformat()
    }
    
    return snapshot

def _get_function_mapping_status(self) -> str:
    """获取函数映射状态
    
    Returns:
        "complete": 所有必需函数都可用
        "incomplete": 部分函数缺失
        "import_failed": 模块导入失败
    """
    if not hasattr(self, '_module') or self._module is None:
        return "import_failed"
    
    required = getattr(self, '_required_functions', [])
    if not required:
        return "complete"
    
    available = self._get_available_functions()
    missing = set(required) - set(available)
    
    return "complete" if not missing else "incomplete"

def _get_available_functions(self) -> List[str]:
    """获取可用函数列表"""
    if not hasattr(self, '_module') or self._module is None:
        return []
    
    available = []
    required = getattr(self, '_required_functions', [])
    
    for func_name in required:
        if hasattr(self._module, func_name) and callable(getattr(self._module, func_name)):
            available.append(func_name)
    
    return available
```

---

## 步骤5：实现MainWindow的完整UI状态栏更新逻辑

在 `ui/main_window.py` 中修改和新增：

```python
from PyQt6.QtCore import QMetaObject, Qt, QTimer
from ui.status_events import StatusChangeEvent, StatusEventEmitter
import threading
import time


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ... 现有初始化代码 ...
        
        # 初始化006A架构组件
        self.initialize_architecture_components()
        
        # 创建状态事件发射器
        self.status_event_emitter = StatusEventEmitter()
        
        # 存储上次状态（用于变更检测）
        self._last_module_status = None
        self._last_render_status = None
        
        # 设置状态更新触发器
        self.setup_status_update_triggers()
    
    def initialize_architecture_components(self):
        """初始化006A架构组件"""
        from utils.config_manager import ConfigManager
        from core.application_state_manager import ApplicationStateManager
        from core.snapshot_manager import SnapshotManager
        from core.unified_cache_manager import UnifiedCacheManager
        from core.performance_metrics import PerformanceMetrics
        from core.error_code_manager import ErrorCodeManager
        
        # 按标准顺序初始化
        self.config_manager = ConfigManager()
        self.cache_manager = UnifiedCacheManager()
        self.performance_metrics = PerformanceMetrics(self.config_manager)
        self.error_manager = ErrorCodeManager(self.config_manager)
        
        self.snapshot_manager = SnapshotManager(self.config_manager)
        self.snapshot_manager.set_cache_manager(self.cache_manager)
        
        self.state_manager = ApplicationStateManager(self.config_manager)
        self.state_manager.set_snapshot_manager(self.snapshot_manager)
        self.state_manager.set_performance_metrics(self.performance_metrics)
    
    def setup_status_update_triggers(self):
        """设置状态更新触发器"""
        # 初始更新
        self.update_status_bar()
        
        # 定时更新（可选，用于轮询）
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(5000)  # 每5秒更新一次
    
    def update_status_bar(self):
        """更新状态栏（完整实现，带事件生成和性能监控）"""
        perf_start = time.perf_counter()
        
        try:
            # 步骤1：获取当前状态
            state_fetch_start = time.perf_counter()
            current_module_status = self._get_module_status_safe()
            current_render_status = self._get_render_status_safe()
            state_fetch_time = (time.perf_counter() - state_fetch_start) * 1000
            
            # 步骤2：检测并发射状态变更事件
            self._check_and_emit_status_changes(
                current_module_status,
                current_render_status
            )
            
            # 步骤3：构建状态消息和颜色
            message_build_start = time.perf_counter()
            status_message = self._build_status_message(
                current_module_status,
                current_render_status
            )
            status_color = self._get_status_color(current_module_status)
            message_build_time = (time.perf_counter() - message_build_start) * 1000
            
            # 步骤4：更新UI
            ui_update_start = time.perf_counter()
            self.statusBar().showMessage(status_message)
            self.statusBar().setStyleSheet(f"background-color: {status_color};")
            ui_update_time = (time.perf_counter() - ui_update_start) * 1000
            
            # 步骤5：记录性能指标
            total_time = (time.perf_counter() - perf_start) * 1000
            self._record_performance_metrics({
                "total_time_ms": total_time,
                "state_fetch_time_ms": state_fetch_time,
                "message_build_time_ms": message_build_time,
                "ui_update_time_ms": ui_update_time
            })
            
            # 性能告警
            if total_time > 100:
                print(f"⚠️ 状态栏更新耗时过长: {total_time:.2f}ms")
            
        except AttributeError as e:
            # 006A组件不可用
            self.statusBar().showMessage("⚠️ 状态管理器不可用，请检查006A任务是否完成")
            self.statusBar().setStyleSheet("background-color: orange;")
            
        except Exception as e:
            # 其他错误
            error_msg = f"❌ 状态更新错误: {str(e)}"
            self.statusBar().showMessage(error_msg)
            self.statusBar().setStyleSheet("background-color: red;")
    
    def _get_module_status_safe(self) -> dict:
        """安全获取模块状态"""
        try:
            # 优先使用P2改进的接口
            if hasattr(self, 'dynamic_importer') and hasattr(self.dynamic_importer, 'get_last_import_snapshot'):
                return self.dynamic_importer.get_last_import_snapshot(self.config_manager)
            else:
                # 降级使用ApplicationStateManager
                return self.state_manager.get_module_status("markdown_processor")
        except Exception as e:
            return {
                "config_enabled": False,
                "import_status": "error",
                "function_mapping_status": "import_failed",
                "error_message": str(e)
            }
    
    def _get_render_status_safe(self) -> dict:
        """安全获取渲染状态"""
        try:
            return self.state_manager.get_render_status()
        except Exception as e:
            return {
                "renderer_type": "unknown",
                "reason": "error",
                "error_message": str(e)
            }
    
    def _check_and_emit_status_changes(self, current_module_status: dict, current_render_status: dict):
        """检测状态变更并发射事件"""
        # 检测模块状态变更
        if self._has_module_status_changed(current_module_status):
            event = StatusChangeEvent.create_module_change_event(
                old_status=self._last_module_status or {},
                new_status=current_module_status,
                change_reason=self._determine_module_change_reason(
                    self._last_module_status,
                    current_module_status
                ),
                module_name="markdown_processor"
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
                )
            )
            self.status_event_emitter.emit_event(event)
            self._last_render_status = current_render_status.copy()
    
    def _has_module_status_changed(self, current_status: dict) -> bool:
        """检测模块状态是否变更"""
        if self._last_module_status is None:
            return True
        
        key_fields = ["function_mapping_status", "import_status", "error_code"]
        for field in key_fields:
            if self._last_module_status.get(field) != current_status.get(field):
                return True
        
        return False
    
    def _has_render_status_changed(self, current_status: dict) -> bool:
        """检测渲染状态是否变更"""
        if self._last_render_status is None:
            return True
        
        return self._last_render_status.get("renderer_type") != current_status.get("renderer_type")
    
    def _determine_module_change_reason(self, old_status: dict, new_status: dict) -> str:
        """确定模块状态变更原因"""
        if old_status is None:
            return "initial_status"
        
        old_mapping = old_status.get("function_mapping_status")
        new_mapping = new_status.get("function_mapping_status")
        
        if old_mapping != new_mapping:
            return f"function_mapping_{old_mapping}_to_{new_mapping}"
        
        old_import = old_status.get("import_status")
        new_import = new_status.get("import_status")
        
        if old_import != new_import:
            return f"import_status_{old_import}_to_{new_import}"
        
        return "unknown_change"
    
    def _determine_render_change_reason(self, old_status: dict, new_status: dict) -> str:
        """确定渲染状态变更原因"""
        if old_status is None:
            return "initial_render_status"
        
        old_renderer = old_status.get("renderer_type")
        new_renderer = new_status.get("renderer_type")
        
        return f"renderer_{old_renderer}_to_{new_renderer}"
    
    def _build_status_message(self, module_status: dict, render_status: dict) -> str:
        """构建状态消息（基于简化配置）"""
        # 获取配置的状态消息模板
        app_config = self.config_manager.get_config("app_config") or {}
        ui_config = app_config.get("ui", {})
        status_messages = ui_config.get("status_bar_messages", {})
        
        # 检查模块启用状态
        if not module_status.get("config_enabled"):
            return "模块已禁用"
        
        # 检查导入状态
        import_status = module_status.get("import_status", "not_imported")
        if import_status == "failed" or import_status == "error":
            error_code = module_status.get("error_code", "")
            error_msg = module_status.get("error_message", "未知错误")
            return f"[{error_code}] {error_msg}" if error_code else f"导入失败: {error_msg}"
        
        # 检查函数映射状态
        mapping_status = module_status.get("function_mapping_status", "unknown")
        
        if mapping_status == "incomplete":
            missing = module_status.get("missing_functions", [])
            return f"⚠️ 函数映射不完整，缺失: {', '.join(missing)}"
        
        # 成功状态
        renderer_type = render_status.get("renderer_type", "unknown")
        
        # 从配置获取消息模板
        if mapping_status in status_messages:
            template = status_messages[mapping_status]
            return template.get("text", f"✅ 模块就绪 | 渲染器: {renderer_type}")
        
        # 默认消息
        module_name = module_status.get("module_name", "unknown")
        return f"✅ {module_name} | 渲染器: {renderer_type}"
    
    def _get_status_color(self, module_status: dict) -> str:
        """获取状态颜色（基于简化配置）"""
        # 获取颜色配置
        ui_config = self.config_manager.get_config("ui_config") or {}
        colors = ui_config.get("colors", {
            "success": "#90EE90",
            "warning": "#FFD700",
            "error": "#FF6B6B",
            "disabled": "#D3D3D3",
            "default": "#F0F0F0"
        })
        
        # 检查配置启用状态
        if not module_status.get("config_enabled"):
            return colors.get("disabled", "gray")
        
        # 检查导入状态
        import_status = module_status.get("import_status", "not_imported")
        if import_status in ("failed", "error"):
            return colors.get("error", "red")
        
        # 检查函数映射状态
        mapping_status = module_status.get("function_mapping_status", "unknown")
        color_map = {
            "complete": colors.get("success", "green"),
            "incomplete": colors.get("warning", "yellow"),
            "import_failed": colors.get("error", "red")
        }
        
        return color_map.get(mapping_status, colors.get("default", "lightgray"))
    
    def _record_performance_metrics(self, metrics: dict):
        """记录性能指标"""
        if hasattr(self, 'performance_metrics'):
            try:
                self.performance_metrics.record_ui_update({
                    "component": "status_bar",
                    **metrics
                })
            except Exception as e:
                pass  # 性能记录失败不影响主流程
    
    # 为008任务提供的公开接口
    def register_status_event_listener(self, listener: Callable):
        """注册状态事件监听器（供008任务日志系统使用）
        
        Args:
            listener: 回调函数，签名为 listener(event: StatusChangeEvent)
        
        Example:
            def log_status_change(event: StatusChangeEvent):
                logger.info(f"状态变更: {event.event_type}", extra=event.to_dict())
            
            main_window.register_status_event_listener(log_status_change)
        """
        self.status_event_emitter.add_listener(listener)
    
    def unregister_status_event_listener(self, listener: Callable):
        """注销状态事件监听器"""
        self.status_event_emitter.remove_listener(listener)
    
    def get_status_event_emitter(self) -> StatusEventEmitter:
        """获取事件发射器（供008任务使用）"""
        return self.status_event_emitter
    
    def get_ui_snapshot_data(self) -> dict:
        """获取UI状态快照数据（供日志记录）"""
        return {
            "current_module_status": self._last_module_status,
            "current_render_status": self._last_render_status,
            "status_bar_text": self.statusBar().currentMessage(),
            "event_history": self.status_event_emitter.get_event_history(10)
        }
    
    # 线程安全的UI更新
    def update_status_bar_safe(self):
        """线程安全的状态栏更新（供后台线程调用）"""
        if threading.current_thread() == threading.main_thread():
            self.update_status_bar()
        else:
            QMetaObject.invokeMethod(
                self,
                "update_status_bar",
                Qt.ConnectionType.QueuedConnection
            )
```

---

## 步骤6-10 及其他内容简要说明

由于文档长度限制，步骤6-10的详细内容请参考主文档。关键内容包括：

### 步骤6：配置文件准备
- 在 `config/app_config.json` 添加 UI 配置段
- 在 `config/ui_config.json` 添加颜色配置

### 步骤7：创建单元测试
- `tests/test_status_events.py` - 事件系统测试
- `tests/test_ui_status_bar.py` - UI状态栏测试

### 步骤8：创建集成测试
- `tests/test_007_integration.py` - 完整集成测试

### 步骤9：性能测试和优化
- 性能基线验证
- 性能告警测试

### 步骤10：最终验收
- 功能验收清单
- 代码质量检查
- 文档完整性检查

---

## 与008任务的接口说明

### 008任务可以这样使用007的接口

```python
# 在008任务的日志系统初始化时
from ui.main_window import MainWindow
from core.enhanced_logger import EnhancedLogger

class LoggingSystem:
    def __init__(self, main_window: MainWindow):
        self.main_window = main_window
        self.logger = EnhancedLogger()
        
        # 注册状态事件监听
        self.main_window.register_status_event_listener(self._on_status_change)
    
    def _on_status_change(self, event: StatusChangeEvent):
        """处理状态变更事件"""
        # 记录到日志
        self.logger.info(
            f"UI状态变更: {event.event_type}",
            extra=event.to_dict()
        )
        
        # 如果是关键状态变更，保存快照
        if self._is_critical_change(event):
            snapshot = self.main_window.state_manager.get_module_status(
                event.details.get("module_name")
            )
            snapshot_id = self._save_snapshot(snapshot)
            event.set_correlation_id(snapshot_id)
    
    def _is_critical_change(self, event: StatusChangeEvent) -> bool:
        """判断是否为关键状态变更"""
        critical_reasons = [
            "import_status_success_to_failed",
            "function_mapping_complete_to_incomplete"
        ]
        return any(reason in event.change_reason for reason in critical_reasons)
```

---

## 完整的执行检查清单

### 执行前检查（必须）
- [ ] 006B任务已完成（运行test_config_manager.py验证）
- [ ] 006A任务已完成（运行test_006a_integration.py验证）
- [ ] ConfigManager.get_unified_config方法可用
- [ ] ApplicationStateManager已创建且可用
- [ ] SnapshotManager已创建且可用
- [ ] ErrorCodeManager已创建且可用
- [ ] external_modules.json配置正确
- [ ] app_config.json UI配置段存在

### 实施过程检查
- [ ] 步骤1：前置验证完成
- [ ] 步骤2：现有UI代码分析完成
- [ ] 步骤3：事件生成机制实现（StatusEventEmitter）
- [ ] 步骤4：DynamicModuleImporter接口实现（get_last_import_snapshot）
- [ ] 步骤5：UI状态栏更新逻辑实现
- [ ] 步骤6：配置文件支持添加
- [ ] 步骤7：单元测试创建
- [ ] 步骤8：集成测试创建
- [ ] 步骤9：性能测试完成
- [ ] 步骤10：最终验收通过

### 功能验证检查
- [ ] 状态栏能正确显示模块状态
- [ ] 状态栏颜色与状态匹配
- [ ] 错误码正确显示
- [ ] 函数映射状态正确反映
- [ ] 配置变更后状态栏更新
- [ ] 多线程环境下运行稳定
- [ ] 事件生成机制正常工作
- [ ] 008任务能成功注册监听器

### 代码质量检查
- [ ] 无linter错误
- [ ] 代码符合项目规范
- [ ] 注释完整清晰
- [ ] 异常处理完善
- [ ] 线程安全机制正确
- [ ] 性能影响可接受（更新<100ms）

---

**文档结束**  
**版本**: V4.1 Part2  
**创建时间**: 2025-10-11 16:38:35

