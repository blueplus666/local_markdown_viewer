# 本地Markdown文件渲染程序重构方案

## 一、项目概述

### 1.1 重构目标
将现有的Flask Web应用重构为PyQt5桌面应用，实现本地Markdown文件渲染和文档管理功能。

### 1.2 核心功能
- 二栏布局：左侧文件树，右侧文档内容显示
- 智能文件解析：自动识别文件类型，支持Markdown渲染和原始内容预览
- 直接复用markdown_processor.py组件
- 可配置的界面样式和逻辑
- 支持本地文件拖拽打开
- 多标签/多窗口支持（可扩展）

### 1.3 技术栈
- **GUI框架**: PyQt5/PyQt6
- **Markdown渲染**: 直接复用markdown_processor.py
- **文件处理**: Python标准库 (os, pathlib)
- **配置管理**: JSON/YAML配置文件

## 二、系统架构设计

### 2.1 整体架构图
```
┌─────────────────────────────────────────────────────────────┐
│                    PyQt5桌面应用                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────────────────────────────┐ │
│  │   主窗口    │    │           文档内容显示              │ │
│  │ MainWindow  │    │        ContentViewer               │ │
│  │             │    │         (UI显示层)                  │ │
│  └─────────────┘    └─────────────────────────────────────┘ │
│  ┌─────────────┐    ┌─────────────────────────────────────┐ │
│  │   文件树    │    │         Markdown渲染器              │ │
│  │ FileTree    │    │    MarkdownRenderer                 │ │
│  │             │    │         (业务逻辑层)                │ │
│  └─────────────┘    └─────────────────────────────────────┘ │
│  ┌─────────────┐    ┌─────────────────────────────────────┐ │
│  │  文件解析   │    │           内容预览器                │ │
│  │FileResolver │    │        ContentPreview               │ │
│  │             │    │         (业务逻辑层)                │ │
│  └─────────────┘    └─────────────────────────────────────┘ │
│  ┌─────────────┐    ┌─────────────────────────────────────┐ │
│  │  配置管理   │    │           其他工具模块              │ │
│  │ConfigManager│    │            Utils                    │ │
│  └─────────────┘    └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

【架构层次说明】
- UI层：ContentViewer (内容显示组件)
- 业务逻辑层：ContentPreview (内容预览器)、MarkdownRenderer (Markdown渲染器)
- 基础服务层：FileResolver (文件解析)、ConfigManager (配置管理)
```

### 2.2 模块结构图
```
local_markdown_viewer/
├── main.py                          # 程序入口
├── config/                          # 配置目录
│   ├── app_config.json             # 应用配置
│   ├── ui_config.json              # 界面配置
│   └── file_types.json             # 文件类型配置
├── ui/                              # 【UI层】用户界面模块
│   ├── main_window.py              # 主窗口类
│   ├── file_tree.py                # 文件树组件
│   ├── content_viewer.py           # 内容显示组件 (UI显示层)
│   └── styles/
│       ├── main.qss                # 主样式表
│       └── themes/                 # 主题样式
├── core/                            # 【业务逻辑层】核心功能模块
│   ├── file_resolver.py            # 文件解析模块 (基础服务)
│   ├── markdown_renderer.py        # Markdown渲染器 (业务逻辑)
│   └── content_preview.py          # 内容预览器 (业务逻辑)
├── utils/                           # 【基础服务层】工具模块
│   ├── config_manager.py           # 配置管理器
│   ├── file_utils.py               # 文件工具
│   └── path_utils.py               # 路径工具
├── resources/                       # 资源文件
│   ├── icons/                      # 图标资源
│   └── templates/                  # 模板文件
└── tests/                          # 测试文件

【分层架构说明】
- UI层：负责用户界面显示和交互
- 业务逻辑层：负责文件内容处理和渲染逻辑
- 基础服务层：提供文件解析、配置管理等基础服务
```

## 三、详细设计

### 3.1 调用关系图
```
main.py
├── ConfigManager.load_config()
├── MainWindow.__init__()
│   ├── FileTree.__init__()
│   ├── ContentViewer.__init__()
│   └── FileResolver.__init__()
│
FileTree.file_selected()
├── FileResolver.resolve_file_path()           # 文件路径解析
│   ├── analyze_file_type()                   # 文件类型分析
│   └── resolve_relative_path()               # 相对路径解析
├── ContentViewer.display_file()              # UI层：显示文件内容
│   ├── MarkdownRenderer.render()             # 业务逻辑层：Markdown渲染
│   └── ContentPreview.preview_file()         # 业务逻辑层：其他文件预览
│
MarkdownRenderer.render()                      # 调用外部markdown_processor
└── markdown_processor.render_markdown_with_zoom()

【分层调用说明】
- UI层 (ContentViewer) 调用业务逻辑层 (ContentPreview/MarkdownRenderer)
- 业务逻辑层调用基础服务层 (FileResolver)
- 各层职责明确，避免跨层直接调用
```

### 3.2 核心模块设计

#### 3.2.1 主窗口模块 (main_window.py)
```python
class MainWindow(QMainWindow):
    """主窗口类 - 二栏布局管理"""
    
    def __init__(self):
        # 初始化UI组件
        # 设置布局
        # 绑定信号槽
        # 初始化顶部下拉式菜单区域（预留扩展）
```

**功能函数说明:**
- `setup_ui()`: 初始化二栏布局
- `setup_menu_bar()`: 设置菜单栏（支持下拉式菜单，预留扩展）
- `setup_status_bar()`: 设置状态栏
- `handle_file_selected(file_path)`: 处理文件选择事件

#### 3.2.2 文件树模块 (file_tree.py)
```python
class FileTree(QTreeView):
    """文件树组件 - 左侧文件浏览器"""
    
    def __init__(self, root_path):
        # 初始化文件系统模型
        # 设置过滤器
        # 绑定选择事件
```

**功能函数说明:**
- `set_root_path(path)`: 设置根目录
- `filter_files(patterns)`: 文件过滤
- `get_selected_file()`: 获取选中文件路径
- `refresh_tree()`: 刷新文件树

#### 3.2.3 文件解析模块 (file_resolver.py)
```python
class FileResolver:
    """文件解析器 - 智能文件类型识别和路径解析"""
    
    def resolve_file(self, file_path, base_path=None):
        """解析文件路径，返回文件信息"""
        
    def analyze_file_type(self, file_path):
        """分析文件类型"""
        
    def resolve_relative_path(self, relative_path, base_path):
        """解析相对路径为绝对路径"""
```

**功能函数详细说明:**

**resolve_file(file_path, base_path=None)**
- **参数**: 
  - `file_path`: str - 文件路径（绝对或相对）
  - `base_path`: str - 基础路径（用于解析相对路径）
- **返回**: dict - 文件信息字典
- **功能**: 解析文件路径，分析文件类型，返回完整文件信息

**analyze_file_type(file_path)**
- **参数**: `file_path`: str - 文件路径
- **返回**: dict - 文件类型信息
- **功能**: 根据文件扩展名和内容分析文件类型

**resolve_relative_path(relative_path, base_path)**
- **参数**: 
  - `relative_path`: str - 相对路径
  - `base_path`: str - 基础路径
- **返回**: str - 绝对路径
- **功能**: 将相对路径解析为绝对路径

#### 3.2.4 Markdown渲染器模块 (markdown_renderer.py)
```python
class MarkdownRenderer:
    """Markdown渲染器 - 直接复用markdown_processor.py"""
    
    def __init__(self):
        # 导入markdown_processor
        # 初始化渲染器
        
    def render(self, markdown_content):
        """渲染Markdown内容"""
        
    def render_file(self, file_path):
        """渲染Markdown文件"""
```

**功能函数详细说明:**

**render(markdown_content)**
- **参数**: `markdown_content`: str - Markdown文本内容
- **返回**: str - 渲染后的HTML
- **功能**: 调用markdown_processor.render_markdown_with_zoom()渲染内容

**render_file(file_path)**
- **参数**: `file_path`: str - Markdown文件路径
- **返回**: str - 渲染后的HTML
- **功能**: 读取文件并渲染Markdown内容

#### 3.2.5 内容显示模块 (content_viewer.py)
```python
class ContentViewer(QWidget):
    """内容显示组件 - 右侧文档内容显示"""
    
    def __init__(self):
        # 初始化Web视图
        # 设置布局
        # 绑定事件
        
    def display_content(self, file_info):
        """显示文件内容"""
        
    def display_markdown(self, html_content):
        """显示Markdown渲染结果"""
        
    def display_raw_content(self, content, file_type):
        """显示原始内容"""
```

**功能函数详细说明:**

**display_content(file_info)**
- **参数**: `file_info`: dict - 文件信息字典
- **返回**: None
- **功能**: 根据文件类型选择显示方式

**display_markdown(html_content)**
- **参数**: `html_content`: str - 渲染后的HTML
- **返回**: None
- **功能**: 在Web视图中显示Markdown内容

**display_raw_content(content, file_type)**
- **参数**: 
  - `content`: str - 文件原始内容
  - `file_type`: str - 文件类型
- **返回**: None
- **功能**: 显示非Markdown文件的原始内容

#### 3.2.6 配置管理模块 (config_manager.py)
```python
class ConfigManager:
    """配置管理器 - 统一管理应用配置"""
    
    def __init__(self, config_dir):
        # 加载配置文件
        # 初始化默认配置
        
    def get_config(self, key, default=None):
        """获取配置项"""
        
    def set_config(self, key, value):
        """设置配置项"""
        
    def load_ui_config(self):
        """加载界面配置"""
        
    def load_file_types_config(self):
        """加载文件类型配置"""
    
    def update_config(self, key, value):
        """配置文件内容修改（占位，便于后续扩展）"""
```

### 3.2.7 异常处理与用户提示模块（占位）
- 负责文件不存在、权限不足、渲染失败等场景的用户提示和日志记录机制。
- 未来可扩展为统一的异常捕获、弹窗提示、日志写入等功能。

### 3.2.8 用户体验细节模块（占位）
- 负责最近打开文件、主题切换、字体缩放等用户体验增强功能。
- 未来可扩展为用户偏好设置、界面自定义等。

### 3.2.9 文档与帮助系统模块（占位）
- 负责用户手册、内置帮助、FAQ等文档支持。
- 未来可扩展为F1快捷键帮助、在线文档链接等。

### 3.3 原有模块映射表

| 原有模块/文件 | 新模块/文件 | 映射关系 | 说明 |
|--------------|-------------|----------|------|
| app.py (Flask) | main.py + main_window.py | 功能分解 | Flask路由逻辑转换为PyQt信号槽 |
| index.html | main_window.py | 结构转换 | HTML布局转换为PyQt布局 |
| left-panel.html | file_tree.py | 功能迁移 | 文件树功能迁移到PyQt组件 |
| center-panel.html | content_viewer.py | 功能迁移 | 内容显示功能迁移到PyQt组件 |
| right-panel.html | 移除 | 功能合并 | 文件详情功能合并到content_viewer |
| /api/menu_tree | file_tree.py | 直接实现 | 用QFileSystemModel替代API |
| /api/file_info | file_resolver.py | 功能迁移 | 文件信息获取逻辑迁移 |
| markdown_processor.py | markdown_renderer.py | 直接复用 | 直接import和调用 |
| static/main.css | styles/main.qss | 样式转换 | CSS转换为Qt样式表 |

### 3.4 文件分解重组说明

#### 3.4.1 Flask应用分解
- **路由处理** → PyQt信号槽机制
- **模板渲染** → PyQt组件直接显示
- **静态文件服务** → Qt资源系统
- **API接口** → 直接函数调用

#### 3.4.2 HTML组件重组
- **iframe结构** → PyQt布局管理器
- **JavaScript事件** → PyQt信号槽
- **CSS样式** → Qt样式表(QSS)
- **DOM操作** → Qt组件API

## 四、配置文件设计

### 4.1 应用配置文件 (app_config.json)
```json
{
  "app": {
    "name": "本地Markdown文件渲染器",
    "version": "1.0.0",
    "default_root_path": "D:/lad/LAD_Project",
    "window": {
      "width": 1200,
      "height": 800,
      "min_width": 800,
      "min_height": 600
    }
  },
  "file_tree": {
    "show_hidden_files": false,
    "file_filters": ["*.md", "*.txt", "*.py", "*.json"],
    "exclude_patterns": ["*.log", "*.tmp"]
  },
  "markdown": {
    "enable_zoom": true,
    "enable_syntax_highlight": true,
    "theme": "default"
  }
}
```

### 4.2 界面配置文件 (ui_config.json)
```json
{
  "layout": {
    "left_panel_width": 300,
    "right_panel_width": "auto",
    "splitter_handle_width": 4
  },
  "colors": {
    "primary": "#2196f3",
    "secondary": "#f5f5f5",
    "text": "#333333",
    "background": "#ffffff"
  },
  "fonts": {
    "main": "微软雅黑",
    "code": "Consolas",
    "size": 14
  }
}
```

### 4.3 文件类型配置文件 (file_types.json)
```json
{
  "markdown_files": {
    "extensions": [".md", ".markdown", ".mdown"],
    "renderer": "markdown",
    "preview_mode": "rendered"
  },
  "text_files": {
    "extensions": [".txt", ".log", ".ini", ".cfg"],
    "renderer": "text",
    "preview_mode": "raw"
  },
  "code_files": {
    "extensions": [".py", ".js", ".html", ".css", ".json"],
    "renderer": "syntax_highlight",
    "preview_mode": "highlighted"
  },
  "binary_files": {
    "extensions": [".exe", ".dll", ".so", ".dylib"],
    "renderer": "binary",
    "preview_mode": "info_only"
  }
}
```

## 五、实现步骤

### 5.1 第一阶段：基础框架
1. 创建项目结构
2. 实现配置管理器
3. 搭建主窗口框架
4. 实现二栏布局

### 5.2 第二阶段：核心功能
1. 实现文件树组件
2. 实现文件解析器
3. 集成markdown_processor.py
4. 实现内容显示组件

### 5.3 第三阶段：界面优化
1. 实现样式系统
2. 添加主题支持
3. 优化用户体验
4. 添加快捷键支持

### 5.4 第四阶段：测试完善
1. 单元测试
2. 集成测试
3. 性能优化
4. 打包发布

## 六、技术要点

### 6.1 关键实现细节
- **文件类型识别**: 基于扩展名和文件头分析
- **路径解析**: 支持相对路径和绝对路径
- **Markdown渲染**: 直接调用markdown_processor.py
- **内容预览**: 支持多种文件类型的预览
- **配置管理**: 基于JSON的灵活配置系统

### 6.2 性能优化
- **缓存机制接口规范**: 所有涉及缓存的组件，其get_cache_info()方法必须返回如下结构：
  ```python
  {
      'total': 当前缓存条目数（int）, 
      'limit': 缓存上限（int）, 
      ...  # 其他可选字段
  }
  ```
  兼容保留原有字段（如'total_items'、'cache_size'），但主窗口和所有新代码只依赖统一字段。

### 6.3 扩展性设计
- **插件系统**: 支持自定义渲染器
- **主题系统**: 支持自定义界面主题
- **配置热更新**: 支持运行时配置更新
- **多语言支持**: 国际化支持

## 七、总结

本方案通过PyQt5框架重构现有Flask应用，实现了：
1. **直接复用markdown_processor.py** - 无需重写Markdown渲染逻辑
2. **二栏布局设计** - 简洁高效的用户界面
3. **智能文件解析** - 自动识别文件类型和路径
4. **可配置架构** - 通过配置文件减少代码耦合
5. **模块化设计** - 清晰的模块结构和调用关系

该方案既保持了原有功能的完整性，又提供了更好的本地化体验和扩展性。 