# LAD-IMPL-007 V4.2附录A：核心组件完整代码

**主文档**: LAD-IMPL-007-UI状态栏更新-完整提示词V4.2-架构对齐版-主文档.md  
**附录类型**: 核心组件完整代码  
**创建时间**: 2025-10-13 10:54:33  
**内容**: CorrelationIdManager、StatusEventEmitter完整实现  
**代码量**: 约800行  

---

## 📦 组件1：CorrelationIdManager完整实现

**文件位置**: `core/correlation_id_manager.py`（新文件）  
**代码行数**: 约150行  
**架构依据**: 第2份续2第274-333行  

### 完整代码

```python
"""
关联ID管理器
实现"快照-日志-状态"三方关联

架构依据：第2份-LAD-IMPL-008日志系统增强完整细化过程文档-续篇2.md 第274-333行
格式标准：{operation_type}_{component}_{timestamp_ms}_{random_suffix}
示例：import_markdown_processor_1696789012345_a1b2c3d4
"""

import uuid
import time
import threading
from typing import Dict, Optional, List


class CorrelationIdManager:
    """关联ID管理器（单例模式，线程安全）
    
    功能：
    1. 生成符合架构标准格式的关联ID
    2. 解析关联ID获取元信息
    3. 管理当前活动的关联ID（按组件）
    4. 记录关联ID历史（用于调试）
    5. 线程安全的访问控制
    
    用途：
    - 实现"快照-日志-状态"三方关联
    - 追踪完整操作流程（用户操作→模块导入→渲染→UI更新→日志记录）
    - 调试和故障排查
    - 性能分析的数据关联
    
    架构标准：
    - 单例模式（全局唯一实例）
    - 线程安全（RLock保护）
    - 格式标准：{operation}_{component}_{timestamp}_{random}
    """
    
    _instance = None
    _lock = None
    
    def __new__(cls):
        """单例模式实现（双重检查锁，线程安全）"""
        if cls._instance is None:
            # 第一次检查
            if cls._lock is None:
                cls._lock = threading.RLock()
            
            with cls._lock:
                # 第二次检查
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        
        return cls._instance
    
    def __init__(self):
        """初始化（只在第一次创建实例时执行）"""
        if not hasattr(self, '_initialized'):
            self._current_correlation_ids = {}  # component -> correlation_id
            self._correlation_history = []  # 历史记录（用于调试）
            self._max_history = 100  # 最多保留100条历史
            self._initialized = True
    
    @staticmethod
    def generate_correlation_id(operation_type: str, component: str = None) -> str:
        """生成关联ID（符合架构标准格式）
        
        ⚠️ 架构标准格式（第2份续2第274-287行）：
        - 带component: {operation_type}_{component}_{timestamp_ms}_{random_suffix}
        - 不带component: {operation_type}_{timestamp_ms}_{random_suffix}
        
        Args:
            operation_type: 操作类型
                - "import": 模块导入操作
                - "render": 渲染处理操作
                - "ui_action": UI交互操作
                - "link": 链接处理操作（012-015任务）
            
            component: 组件名称（可选）
                - "markdown_processor": Markdown处理器模块
                - "status_bar": 状态栏组件
                - "file_select": 文件选择组件
                - "content_viewer": 内容查看器
        
        Returns:
            str: 关联ID字符串
        
        Examples:
            >>> CorrelationIdManager.generate_correlation_id("import", "markdown_processor")
            'import_markdown_processor_1696789012345_a1b2c3d4'
            
            >>> CorrelationIdManager.generate_correlation_id("render")
            'render_1696789012345_a1b2c3d4'
            
            >>> CorrelationIdManager.generate_correlation_id("ui_action", "status_bar")
            'ui_action_status_bar_1696789012345_a1b2c3d4'
        """
        # 生成毫秒级时间戳
        timestamp = int(time.time() * 1000)
        
        # 生成8位随机后缀（UUID的前8位）
        random_suffix = uuid.uuid4().hex[:8]
        
        # 组装关联ID
        if component:
            return f"{operation_type}_{component}_{timestamp}_{random_suffix}"
        else:
            return f"{operation_type}_{timestamp}_{random_suffix}"
    
    @staticmethod
    def parse_correlation_id(correlation_id: str) -> Dict[str, str]:
        """解析关联ID，提取元信息
        
        Args:
            correlation_id: 关联ID字符串
        
        Returns:
            dict: {
                'operation_type': str,  # 操作类型
                'component': str | None,  # 组件名称（可选）
                'timestamp': str,  # 时间戳（毫秒）
                'random_suffix': str  # 随机后缀
            }
            
            如果格式无效，返回: {'raw': correlation_id, 'error': 'Invalid format'}
        
        Examples:
            >>> parse_correlation_id("import_markdown_processor_1696789012345_a1b2c3d4")
            {
                'operation_type': 'import',
                'component': 'markdown_processor',
                'timestamp': '1696789012345',
                'random_suffix': 'a1b2c3d4'
            }
            
            >>> parse_correlation_id("render_1696789012345_a1b2c3d4")
            {
                'operation_type': 'render',
                'component': None,
                'timestamp': '1696789012345',
                'random_suffix': 'a1b2c3d4'
            }
        """
        if not correlation_id:
            return {}
        
        parts = correlation_id.split('_')
        
        if len(parts) < 3:
            return {'raw': correlation_id, 'error': 'Invalid format (too few parts)'}
        
        if len(parts) == 4:
            # 带component的格式：operation_component_timestamp_random
            return {
                'operation_type': parts[0],
                'component': parts[1],
                'timestamp': parts[2],
                'random_suffix': parts[3]
            }
        elif len(parts) == 3:
            # 不带component的格式：operation_timestamp_random
            return {
                'operation_type': parts[0],
                'component': None,
                'timestamp': parts[1],
                'random_suffix': parts[2]
            }
        else:
            # 可能是多段component名称：operation_comp1_comp2_...compN_timestamp_random
            # 例如：ui_action_status_bar_update_1696789012345_a1b2c3d4
            return {
                'operation_type': parts[0],
                'component': '_'.join(parts[1:-2]),  # 中间所有部分作为component
                'timestamp': parts[-2],  # 倒数第二个是timestamp
                'random_suffix': parts[-1]  # 最后一个是random
            }
    
    def set_current_correlation_id(self, component: str, correlation_id: str):
        """设置当前组件的关联ID（线程安全）
        
        Args:
            component: 组件名称
                - "ui": UI层组件
                - "importer": 模块导入器
                - "renderer": 渲染器
                - "link_processor": 链接处理器（012-015任务）
            
            correlation_id: 关联ID字符串
        
        用途：
            在组件开始处理某个操作时设置，用于后续操作的关联
        
        Example:
            >>> manager = CorrelationIdManager()
            >>> corr_id = manager.generate_correlation_id("ui_action", "file_select")
            >>> manager.set_current_correlation_id("ui", corr_id)
        """
        with self.__class__._lock:
            self._current_correlation_ids[component] = correlation_id
            
            # 记录到历史
            self._correlation_history.append({
                'component': component,
                'correlation_id': correlation_id,
                'action': 'set',
                'timestamp': time.time()
            })
            
            # 保持历史记录在限制内
            if len(self._correlation_history) > self._max_history:
                self._correlation_history.pop(0)
    
    def get_current_correlation_id(self, component: str) -> Optional[str]:
        """获取当前组件的关联ID（线程安全）
        
        Args:
            component: 组件名称
        
        Returns:
            str: 关联ID字符串，如果不存在则返回None
        
        Example:
            >>> manager = CorrelationIdManager()
            >>> manager.set_current_correlation_id("ui", "test_1234_abcd")
            >>> manager.get_current_correlation_id("ui")
            'test_1234_abcd'
        """
        with self.__class__._lock:
            return self._current_correlation_ids.get(component)
    
    def clear_correlation_id(self, component: str):
        """清除组件的关联ID（线程安全）
        
        Args:
            component: 组件名称
        
        用途：
            在组件完成处理后清除，避免ID污染下一次操作
        
        Example:
            >>> manager = CorrelationIdManager()
            >>> manager.set_current_correlation_id("ui", "test_1234_abcd")
            >>> manager.clear_correlation_id("ui")
            >>> manager.get_current_correlation_id("ui")
            None
        """
        with self.__class__._lock:
            correlation_id = self._current_correlation_ids.pop(component, None)
            
            if correlation_id:
                # 记录到历史
                self._correlation_history.append({
                    'component': component,
                    'correlation_id': correlation_id,
                    'action': 'clear',
                    'timestamp': time.time()
                })
    
    def get_all_current_correlation_ids(self) -> Dict[str, str]:
        """获取所有当前关联ID（线程安全）
        
        Returns:
            dict: {component_name: correlation_id}
        
        用途：
            调试时查看所有活动的关联ID
        """
        with self.__class__._lock:
            return self._current_correlation_ids.copy()
    
    def get_correlation_history(self, count: int = None) -> List[Dict]:
        """获取关联ID历史（线程安全）
        
        Args:
            count: 获取最近N条记录，None表示获取全部
        
        Returns:
            list: 历史记录列表，每条包含component、correlation_id、action、timestamp
        
        用途：
            调试和追踪关联ID的使用情况
        
        Example:
            >>> manager = CorrelationIdManager()
            >>> history = manager.get_correlation_history(10)
            >>> for record in history:
            ...     print(f"{record['component']}: {record['action']} - {record['correlation_id']}")
        """
        with self.__class__._lock:
            if count is None:
                return self._correlation_history.copy()
            return self._correlation_history[-count:].copy() if count > 0 else []
    
    def clear_all_correlation_ids(self):
        """清除所有关联ID（线程安全）
        
        用途：
            测试或重置时使用
        """
        with self.__class__._lock:
            self._current_correlation_ids.clear()
            self._correlation_history.clear()
```

---

## 📦 组件2：StatusChangeEvent完整实现

**文件位置**: `ui/status_events.py`（新文件）  
**代码行数**: 约200行  

### 完整代码

```python
"""
状态变更事件定义
供007任务UI状态栏使用，为008任务日志系统提供事件流

架构对齐：
- 集成第2份文档的CorrelationIdManager
- correlation_id格式符合架构标准
- 支持StateChangeListener集成（008任务）
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass
class StatusChangeEvent:
    """状态变更事件数据类
    
    用途：
    1. 记录UI状态变更
    2. 为日志系统提供事件流
    3. 调试和追踪状态变化
    4. 关联快照、日志、状态数据
    
    架构标准：
    - correlation_id由CorrelationIdManager生成
    - 格式符合第2份续2第274-299行标准
    - 字段名符合第2份文档日志字段规范
    """
    
    # 事件元数据
    event_type: str
    """事件类型
    - "module_status_change": 模块状态变更
    - "render_status_change": 渲染状态变更
    - "link_status_change": 链接状态变更（012-015任务）
    """
    
    event_source: str
    """事件来源，固定为"ui_status_bar" """
    
    timestamp: str
    """ISO8601格式时间戳，如"2025-10-13T10:00:00.123456" """
    
    # 状态数据
    old_status: Dict[str, Any]
    """变更前的状态数据"""
    
    new_status: Dict[str, Any]
    """变更后的状态数据"""
    
    change_reason: str
    """变更原因
    模块状态：initial_status, function_mapping_complete_to_incomplete等
    渲染状态：initial_render_status, renderer_external_to_fallback等
    """
    
    # 额外信息
    details: Dict[str, Any] = field(default_factory=dict)
    """额外详细信息，如{"module_name": "markdown_processor"}"""
    
    # 追踪和关联ID
    correlation_id: Optional[str] = None
    """关联ID（⚠️ 架构关键字段）
    - 由CorrelationIdManager生成
    - 格式：{operation}_{component}_{timestamp}_{random}
    - 用于关联快照、日志、状态数据
    """
    
    tracking_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """事件唯一ID（UUID格式），用于事件本身的追踪"""
    
    snapshot_id: Optional[str] = None
    """关联的快照ID（由008任务设置）"""
    
    def to_dict(self) -> dict:
        """转换为字典（供日志记录使用）
        
        架构标准：字段名符合第2份文档的日志字段规范
        
        Returns:
            dict: 包含所有字段的字典
        """
        return {
            "event_type": self.event_type,
            "event_source": self.event_source,
            "timestamp": self.timestamp,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "change_reason": self.change_reason,
            "details": self.details,
            "correlation_id": self.correlation_id,  # ⚠️ 关键字段
            "tracking_id": self.tracking_id,
            "snapshot_id": self.snapshot_id
        }
    
    def set_snapshot_id(self, snapshot_id: str):
        """设置关联快照ID（供008任务使用）
        
        Args:
            snapshot_id: 快照ID
        
        用途：
            008任务在处理关键状态变更时，保存快照并设置关联ID
        """
        self.snapshot_id = snapshot_id
    
    @classmethod
    def create_module_change_event(
        cls,
        old_status: Dict[str, Any],
        new_status: Dict[str, Any],
        change_reason: str,
        module_name: str,
        correlation_id: str = None
    ) -> 'StatusChangeEvent':
        """创建模块状态变更事件的便捷方法
        
        Args:
            old_status: 变更前状态（符合第1份文档快照格式）
            new_status: 变更后状态（符合第1份文档快照格式）
            change_reason: 变更原因（如"function_mapping_complete_to_incomplete"）
            module_name: 模块名称（如"markdown_processor"）
            correlation_id: 关联ID（如不提供则自动生成）
        
        Returns:
            StatusChangeEvent: 事件对象
        """
        from core.correlation_id_manager import CorrelationIdManager
        
        # 如果没有提供correlation_id，生成一个
        if not correlation_id:
            correlation_id = CorrelationIdManager.generate_correlation_id(
                operation_type="ui_action",
                component="status_bar"
            )
        
        return cls(
            event_type="module_status_change",
            event_source="ui_status_bar",
            timestamp=datetime.now().isoformat(),
            old_status=old_status,
            new_status=new_status,
            change_reason=change_reason,
            details={"module_name": module_name, "ui_component": "status_bar"},
            correlation_id=correlation_id  # ⚠️ 关键
        )
    
    @classmethod
    def create_render_change_event(
        cls,
        old_status: Dict[str, Any],
        new_status: Dict[str, Any],
        change_reason: str,
        correlation_id: str = None
    ) -> 'StatusChangeEvent':
        """创建渲染状态变更事件的便捷方法"""
        from core.correlation_id_manager import CorrelationIdManager
        
        if not correlation_id:
            correlation_id = CorrelationIdManager.generate_correlation_id(
                operation_type="ui_action",
                component="status_bar"
            )
        
        return cls(
            event_type="render_status_change",
            event_source="ui_status_bar",
            timestamp=datetime.now().isoformat(),
            old_status=old_status,
            new_status=new_status,
            change_reason=change_reason,
            details={"ui_component": "status_bar"},
            correlation_id=correlation_id
        )
```

---

## 📦 组件3：StatusEventEmitter完整实现

**文件位置**: `ui/status_events.py`（续）  
**代码行数**: 约150行  

### 完整代码

```python
# ui/status_events.py 续

import threading
from typing import Callable, List


class StatusEventEmitter:
    """状态事件发射器（观察者模式，线程安全）
    
    功能：
    1. 管理事件监听器列表
    2. 发射状态变更事件
    3. 记录事件历史（用于调试）
    4. 线程安全的事件通知
    
    用途：
    - 007任务：生成和发射状态变更事件
    - 008任务：注册StateChangeListener监听器
    
    架构说明：
    - 007创建StatusEventEmitter（UI层，事件发射器）
    - 008创建StateChangeListener（日志层，事件监听器）
    - StateChangeListener实现__call__方法，注册到StatusEventEmitter
    - 关系：StatusEventEmitter是Subject，StateChangeListener是Observer
    """
    
    def __init__(self, max_history: int = 100):
        """初始化事件发射器
        
        Args:
            max_history: 最多保留的事件历史数量
        """
        self._listeners: List[Callable] = []  # 监听器列表
        self._event_history: List[StatusChangeEvent] = []  # 事件历史
        self._max_history = max_history  # 历史上限
        self._lock = threading.RLock()  # 线程安全锁
    
    def add_listener(self, listener: Callable):
        """添加事件监听器（供008任务StateChangeListener注册）
        
        Args:
            listener: 回调函数或实现了__call__的对象
                - 签名：listener(event: StatusChangeEvent) -> None
                - 或者是实现了__call__(self, event)的类实例
        
        线程安全：是
        
        Examples:
            # 方式1：函数监听器
            def log_handler(event: StatusChangeEvent):
                logger.info(f"状态变更: {event.event_type}")
            
            emitter.add_listener(log_handler)
            
            # 方式2：类监听器（008任务的StateChangeListener）
            class StateChangeListener:
                def __call__(self, event: StatusChangeEvent):
                    self.logger.log(...)
            
            listener = StateChangeListener(logger)
            emitter.add_listener(listener)  # listener实现了__call__
        """
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable):
        """移除事件监听器（线程安全）
        
        Args:
            listener: 要移除的监听器
        """
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
    
    def emit_event(self, event: StatusChangeEvent):
        """发射状态变更事件（线程安全）
        
        Args:
            event: 状态变更事件对象（包含correlation_id）
        
        行为：
        1. 记录到事件历史
        2. 通知所有监听器
        3. 异常监听器不影响其他监听器
        4. 在锁外执行监听器回调（避免死锁）
        
        线程安全：是（RLock保护）
        """
        with self._lock:
            # 记录事件历史
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            # 复制监听器列表（在锁外执行回调）
            listeners_copy = self._listeners.copy()
        
        # 在锁外通知监听器（避免死锁和长时间持锁）
        for listener in listeners_copy:
            try:
                listener(event)
            except Exception as e:
                # 监听器异常不影响其他监听器
                print(f"[StatusEventEmitter] 监听器错误: {e}")
                import traceback
                traceback.print_exc()
    
    def get_event_history(self, count: int = None) -> List[StatusChangeEvent]:
        """获取事件历史（线程安全）
        
        Args:
            count: 获取最近N个事件，None表示获取全部
        
        Returns:
            list: 事件列表（最新的在后面）
        
        用途：
            调试和查看最近的状态变更
        """
        with self._lock:
            if count is None:
                return self._event_history.copy()
            return self._event_history[-count:].copy() if count > 0 else []
    
    def clear_history(self):
        """清空事件历史（线程安全）
        
        用途：
            测试或内存管理
        """
        with self._lock:
            self._event_history.clear()
    
    def get_listener_count(self) -> int:
        """获取监听器数量（线程安全）
        
        Returns:
            int: 当前注册的监听器数量
        
        用途：
            验证008任务的StateChangeListener是否成功注册
        """
        with self._lock:
            return len(self._listeners)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取事件发射器统计信息
        
        Returns:
            dict: {
                'listener_count': int,
                'event_history_count': int,
                'total_events_emitted': int（等于历史数量，可能被截断）
            }
        """
        with self._lock:
            return {
                'listener_count': len(self._listeners),
                'event_history_count': len(self._event_history),
                'max_history': self._max_history
            }
```

---

## 📝 使用示例

### 在MainWindow中使用

```python
# ui/main_window.py

from ui.status_events import StatusChangeEvent, StatusEventEmitter
from core.correlation_id_manager import CorrelationIdManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 创建关联ID管理器和事件发射器
        self.correlation_manager = CorrelationIdManager()
        self.status_event_emitter = StatusEventEmitter()
    
    def update_status_bar(self):
        """更新状态栏"""
        # 1. 生成correlation_id
        correlation_id = CorrelationIdManager.generate_correlation_id("ui_action", "status_bar")
        self.correlation_manager.set_current_correlation_id("ui", correlation_id)
        
        try:
            # 2. 获取状态
            current_status = self._get_module_status_safe()
            
            # 3. 检测变更
            if self._has_module_status_changed(current_status):
                # 4. 创建事件（包含correlation_id）
                event = StatusChangeEvent.create_module_change_event(
                    old_status=self._last_module_status or {},
                    new_status=current_status,
                    change_reason="function_mapping_changed",
                    module_name="markdown_processor",
                    correlation_id=correlation_id  # ⚠️ 传递关联ID
                )
                
                # 5. 发射事件
                self.status_event_emitter.emit_event(event)
                
                # 6. 更新缓存
                self._last_module_status = current_status.copy()
        
        finally:
            # 7. 清除correlation_id
            self.correlation_manager.clear_correlation_id("ui")
```

### 在008任务中使用

```python
# 008任务的日志系统

from ui.main_window import MainWindow
from ui.status_events import StatusChangeEvent
from core.enhanced_logger import EnhancedLogger

class StateChangeListener:
    """状态变更监听器（008任务实现）
    
    架构依据：第2份续2第499-538行
    """
    
    def __init__(self, logger: EnhancedLogger):
        self.logger = logger
        self.previous_states = {}
    
    def __call__(self, event: StatusChangeEvent):
        """监听器回调（实现__call__使其可直接注册）
        
        Args:
            event: 007任务发射的StatusChangeEvent
        """
        # 设置correlation_id到日志器
        self.logger.set_correlation_id(event.correlation_id)
        
        # 记录日志
        self.logger.log_with_context(
            level='INFO',
            message=f"UI状态变更: {event.event_type}",
            operation='state_change',
            component='ui_status_bar',
            correlation_id=event.correlation_id,  # ⚠️ 关键
            **event.to_dict()
        )

# 在008任务初始化时注册
def setup_logging(main_window: MainWindow):
    enhanced_logger = EnhancedLogger('lad.ui')
    listener = StateChangeListener(enhanced_logger)
    main_window.register_status_event_listener(listener)
```

---

**附录A结束**  
**内容**: CorrelationIdManager、StatusChangeEvent、StatusEventEmitter完整代码  
**代码行数**: 约600行  
**下一个附录**: 附录B - UI组件完整代码

