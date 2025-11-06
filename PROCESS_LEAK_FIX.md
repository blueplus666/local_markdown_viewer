# WebEngine进程泄漏修复总结

## 问题描述

用户报告了以下问题：
1. 初始启动程序后，有三个进程
2. 不知道是什么操作，就增加了两个进程，有了五个进程
3. main.py拖拉程序的边框，试图改变窗口大小时，程序卡死
4. 每次打开过一个markdown文件，就多一个c++进程，markdown文件已经关闭了都不会释放

## 根本原因分析

### 1. WebEngine进程泄漏
- **问题**：每次调用`setPage()`创建新的`QWebEnginePage`对象时，WebEngine会创建新的渲染进程
- **原因**：旧的Page对象没有被正确清理，导致进程累积
- **表现**：每打开一个markdown文件就增加一个C++进程

### 2. 信号连接重复
- **问题**：`loadStarted`、`loadProgress`、`loadFinished`信号重复连接
- **原因**：在`display_file()`中没有先断开旧的信号连接
- **表现**：事件处理混乱，可能导致卡死

### 3. 资源清理不完整
- **问题**：`ContentViewer`关闭时没有清理WebEngine资源
- **原因**：缺少`closeEvent`处理
- **表现**：程序退出时进程残留

## 修复方案

### 1. 添加Page对象清理机制
```python
def _cleanup_old_page(self):
    """清理旧的WebEngine Page对象，防止进程泄漏"""
    try:
        if hasattr(self, '_cv_page') and self._cv_page:
            # 断开Page的所有信号连接
            try:
                self._cv_page.destroyed.disconnect()
            except Exception:
                pass
            # 删除Page对象
            self._cv_page.deleteLater()
            self._cv_page = None
            self.logger.debug("已清理旧的WebEngine Page对象")
    except Exception as e:
        self.logger.warning(f"清理旧Page对象失败: {e}")
```

### 2. 修复信号连接管理
```python
def display_file(self, file_path: str, force_reload: bool = False):
    # 清理旧的WebEngine Page对象，防止进程泄漏
    self._cleanup_old_page()
    
    # 断开旧的信号连接，防止重复处理
    try:
        if self.web_engine_view:
            self.web_engine_view.loadStarted.disconnect()
            self.web_engine_view.loadProgress.disconnect()
            self.web_engine_view.loadFinished.disconnect()
    except Exception:
        pass
```

### 3. 增强关闭事件处理
```python
def closeEvent(self, event):
    """关闭事件处理，确保清理WebEngine资源"""
    try:
        self._cleanup_old_page()
        if self.web_engine_view:
            # 断开所有信号连接
            try:
                self.web_engine_view.loadStarted.disconnect()
                self.web_engine_view.loadProgress.disconnect()
                self.web_engine_view.loadFinished.disconnect()
            except Exception:
                pass
            # 清理WebEngine视图
            self.web_engine_view.deleteLater()
            self.web_engine_view = None
        self.logger.info("ContentViewer资源已清理")
    except Exception as e:
        self.logger.error(f"ContentViewer清理失败: {e}")
    finally:
        event.accept()
```

### 4. 主窗口关闭事件增强
```python
def closeEvent(self, event):
    """窗口关闭事件处理"""
    self.logger.info("应用程序即将关闭")
    try:
        # 清理ContentViewer资源
        if self.content_viewer:
            try:
                self.content_viewer.closeEvent(event)
            except Exception as e:
                self.logger.warning(f"ContentViewer清理失败: {e}")
        # ... 其他清理逻辑
    except Exception:
        pass
    event.accept()
```

### 5. 修复集成版日志问题
- 在`main_window_integrated.py`开头添加日志设置
- 修复"name 'open' is not defined"错误

## 修复效果

### 进程管理
- ✅ 每次打开markdown文件不再创建新的C++进程
- ✅ 关闭文件时正确释放WebEngine资源
- ✅ 程序退出时清理所有进程

### 稳定性
- ✅ 窗口拖拽调整大小不再卡死
- ✅ 信号连接不再重复，避免事件风暴
- ✅ 资源清理完整，避免内存泄漏

### 日志系统
- ✅ 集成版不再出现"name 'open' is not defined"错误
- ✅ 统一的日志格式和错误处理

## 测试验证

1. **启动测试**：程序正常启动，初始进程数量稳定
2. **文件操作测试**：打开/关闭markdown文件，进程数量不增加
3. **窗口操作测试**：拖拽调整窗口大小，程序不卡死
4. **退出测试**：正常关闭程序，所有进程被清理

## 技术要点

1. **WebEngine进程管理**：使用`deleteLater()`确保Qt对象正确清理
2. **信号连接管理**：在重新连接前先断开旧连接
3. **资源生命周期**：在`closeEvent`中确保所有资源被释放
4. **错误处理**：使用try-catch包装所有清理操作，避免清理失败影响程序退出

## 预防措施

1. **代码审查**：新增WebEngine相关代码时检查资源管理
2. **测试覆盖**：添加进程数量监控测试
3. **文档更新**：更新开发文档，说明WebEngine资源管理要求 