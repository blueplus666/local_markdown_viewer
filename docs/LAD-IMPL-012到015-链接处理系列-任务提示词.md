# LAD-IMPL-012到015: 链接处理系列 - 任务提示词

**文档版本**: V1.0  
**创建时间**: 2025-10-18  
**更新说明**: 初始版本  

> **配置架构说明**  
> 本任务基于 LAD-IMPL-006B 的简化配置架构实现，使用扁平化配置管理。  
> 相关配置位于 `config/` 目录，通过 `ConfigManager` 统一访问。

## 0. 前置条件与AI执行守则

- **[前置-配置存在性]** 优先读取 `config/app_config.json` 中的 `link_processing` 段；如无，再读取 `config/features/link_processing.json` 与 `config/features/security.json`。
- **[前置-代码路径]** 确认以下文件存在并处于可用状态：
  - `core/link_processor.py`（含 `LinkProcessor`、`LinkValidator` 骨架）
  - `ui/content_viewer.py`（LPCLICK 注入路径：`_on_page_load_finished()` → `_handle_lpclick()` → `process_link()` → `_execute_link_action()`）
  - `core/performance_metrics.py` 与 `config/runtime/performance.json`（阈值来源需对齐）
- **[前置-安全默认]** 默认采用 fail-closed：外部链接需校验协议/域名；文件链接默认启用存在性检查。
- **[AI执行守则]**
  - 先校验配置与路径，再执行代码/文档修改；缺项时先补齐最小配置。
  - 不得改动非本系列范围内的核心模块行为；涉及阈值或安全策略变更须显式记录。
  - 对配置读取示例，优先 `app`，其次 `features`，确保向后兼容。

## 1. 任务概览

### 1.1 任务系列说明
由于链接处理功能相对独立，且基于简化配置架构，将012-015任务合并为一个系列，降低实施复杂度。

### 1.2 任务分解

#### LAD-IMPL-012: 链接处理接入（简化版）
- **任务类型**: 功能接入
- **复杂度级别**: 简单
- **预计交互**: 4-5次
- **依赖任务**: LAD-IMPL-011（性能监控）

#### LAD-IMPL-013: 链接处理安全（简化版）
- **任务类型**: 安全增强
- **复杂度级别**: 简单
- **预计交互**: 3-4次
- **依赖任务**: LAD-IMPL-012

#### LAD-IMPL-014: 链接处理体验（简化版）
- **任务类型**: 用户体验
- **复杂度级别**: 简单
- **预计交互**: 3-4次
- **依赖任务**: LAD-IMPL-013

#### LAD-IMPL-015B: 链接处理验收（简化版）
- **任务类型**: 最终验收
- **复杂度级别**: 简单
- **预计交互**: 2-3次
- **依赖任务**: LAD-IMPL-014

## 2. 技术方案

### 2.1 配置架构

#### 2.1.1 配置文件结构
```
config/
├── features/
│   ├── link_processing.json    # 链接处理配置
│   └── security.json           # 安全策略配置
└── schemas/
    └── link_processing_v1.0.json  # 配置Schema
```

#### 2.1.2 链接处理配置 (link_processing.json)
```json
{
  "enabled": true,
  "processor_type": "enhanced", // basic, enhanced, custom
  "default_target": "_blank",
  "timeout_ms": 5000,
  "cache": {
    "enabled": true,
    "ttl_minutes": 30,
    "max_size": 1000
  },
  "preview": {
    "enabled": true,
    "timeout_ms": 2000,
    "max_size_kb": 1024
  },
  "performance": {
    "max_concurrent_checks": 5,
    "rate_limit_per_second": 10
  }
}
```

#### 2.1.3 安全配置 (security.json)
```json
{
  "version": "1.0",
  "link_validation": {
    "require_https": true,
    "allow_data_uris": false,
    "allow_javascript": false,
    "allow_mailto": true,
    "allow_tel": true,
    "allow_relative": true
  },
  "whitelist": {
    "enabled": true,
    "domains": ["example.com", "trusted-cdn.com"]
  },
  "blacklist": {
    "enabled": true,
    "domains": ["malicious-site.com"],
    "ip_ranges": ["10.0.0.0/8", "192.168.0.0/16"]
  },
  "sanitization": {
    "strip_attributes": ["onclick", "onerror"],
    "allowed_protocols": ["http", "https", "mailto", "tel"],
    "allow_data_uris": false
  },
  "i18n": {
    "default_locale": "zh-CN",
    "supported_locales": ["zh-CN", "en-US"],
    "fallback_locale": "en-US"
  }
}
```

#### 2.1.4 配置Schema定义

##### link_processing_v1.0.json
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Link Processing Configuration",
  "description": "Schema for link processing configuration",
  "type": "object",
  "properties": {
    "version": {
      "type": "string",
      "description": "Configuration version",
      "enum": ["1.0"]
    },
    "enabled": {
      "type": "boolean",
      "description": "Enable/disable link processing"
    },
    "processor_type": {
      "type": "string",
      "enum": ["basic", "enhanced", "custom"],
      "description": "Type of link processor to use"
    },
    "default_target": {
      "type": "string",
      "description": "Default target for links",
      "default": "_blank"
    },
    "timeout_ms": {
      "type": "integer",
      "minimum": 1000,
      "maximum": 30000,
      "description": "Link processing timeout in milliseconds"
    },
    "cache": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean" },
        "ttl_minutes": { "type": "integer", "minimum": 1 },
        "max_size": { "type": "integer", "minimum": 1 }
      },
      "required": ["enabled"]
    }
  },
  "required": ["version", "enabled"]
}
```

### 2.2 配置版本管理

#### 2.2.1 版本兼容性
- **主版本号**：不兼容的变更，需要迁移工具
- **次版本号**：向后兼容的功能性增强
- **修订号**：向后兼容的问题修正

#### 2.2.2 配置迁移
```python
class ConfigMigrator:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        
    def migrate(self, from_version: str, to_version: str) -> bool:
        """迁移配置到新版本"""
        if from_version == "1.0" and to_version == "1.1":
            return self._migrate_1_0_to_1_1()
        return False
        
    def _migrate_1_0_to_1_1(self) -> bool:
        """从1.0迁移到1.1版本"""
        # 迁移逻辑
        pass
```

### 2.2 并发处理模型

#### 2.2.1 线程池管理
- 使用固定大小的线程池处理并发链接检查
- 通过配置控制最大并发数（`max_concurrent_checks`）
- 实现任务队列和拒绝策略

#### 2.2.2 请求限流
- 基于令牌桶算法实现速率限制（`rate_limit_per_second`）
- 支持动态调整速率限制
- 提供详细的限流统计信息

#### 2.2.3 任务管理
- 支持取消正在执行的链接检查
- 实现任务超时控制（`timeout_ms`）
- 提供任务状态查询接口

### 2.3 配置集成

#### 2.3.1 配置访问
```python
# 获取配置示例（优先 app_config.json，其次 features/ 下配置；保持向后兼容）
config_manager = ConfigManager()
link_config = (
    config_manager.get_config("link_processing", {}, "app")
    or config_manager.get_unified_config().get("app", {}).get("link_processing", {})
    or config_manager.get_config("link_processing", {}, "features")
)
security_config = (
    config_manager.get_config("security", {}, "features")
    or config_manager.get_unified_config().get("features", {}).get("security", {})
)
```

#### 2.3.2 配置热重载
```python
# 配置变更监听示例
class LinkProcessor:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._load_config()
        self.config_manager.add_listener(
            "features.link_processing", 
            self._on_config_changed
        )
    
    def _load_config(self):
        """从配置中加载链接处理参数"""
        link_config = self.config_manager.get_config("link_processing", {}, "features")
        self.enabled = link_config.get("enabled", True)
        self.processor_type = link_config.get("processor_type", "basic")
        self.timeout_ms = link_config.get("timeout_ms", 5000)
        
        # 加载安全配置
        security_config = self.config_manager.get_config("security", {}, "features")
        self.require_https = security_config.get("link_validation", {}).get("require_https", True)
        self.allowed_protocols = security_config.get("sanitization", {}).get("allowed_protocols", ["http", "https"])
    
    def _on_config_changed(self, config_path: str):
        """配置变更时重新加载配置"""
        if "link_processing" in config_path or "security" in config_path:
            self._load_config()
            logger.info("链接处理配置已更新")
```

#### 2.1.2 配置访问
```python
# 获取配置示例
config = ConfigManager().get_unified_config()
link_config = config.get('link_processing', {})
```

### 2.4 安全处理机制

#### 2.4.1 链接验证
- 协议白名单（基于`allowed_protocols`配置）
- 域名黑名单/白名单验证
- 重定向深度限制
- 危险属性过滤（基于`sanitization.strip_attributes`）

#### 2.4.2 内容安全
- HTML清理和转义
- 防止XSS攻击
- 内容类型验证
- 文件大小限制

### 2.5 错误处理机制

#### 2.5.1 错误分类
- 网络错误（超时、连接拒绝等）
- 安全错误（不安全的协议、证书问题等）
- 配置错误（无效的URL格式等）
- 验证错误（白名单/黑名单拒绝等）

#### 2.5.2 重试策略
- 可配置的重试次数和间隔
- 指数退避算法实现
- 错误白名单（不重试特定错误）
- 基于错误类型的重试策略

#### 2.5.3 错误报告
- 结构化错误日志（包含错误代码和上下文）
- 错误聚合和统计
- 告警阈值配置
- 安全事件审计

### 2.6 状态管理集成

#### 2.2.1 链接状态管理
- 使用 `ApplicationStateManager` 管理链接处理状态
- 实时更新链接处理状态

#### 2.2.2 快照支持
- 集成 `SnapshotManager` 支持链接处理配置快照
- 支持链接处理状态的保存和回滚

### 2.7 性能监控

#### 2.7.1 监控指标
- 链接解析延迟（P50/P90/P99）
- 并发连接数（当前/最大）
- 缓存命中率（读取/写入）
- 错误率和重试率（按类型）
- 安全拦截统计（白名单/黑名单命中）

#### 2.7.2 性能优化
- 连接池管理（复用HTTP连接）
- DNS预解析（减少DNS查询时间）
- 响应缓存策略（基于TTL和大小限制）
- 懒加载非关键资源
- 请求合并和批量处理

#### 2.7.3 资源限制
- 内存使用限制（防止OOM）
- CPU使用限制（防止CPU峰值）
- 网络带宽限制（节流控制）
- 文件描述符限制
- 线程池大小限制

### 2.8 安全增强

#### 2.8.1 安全策略
- 内容安全策略（CSP）集成
- 同源策略（SOP）执行
- 跨域资源共享（CORS）控制
- 安全头部设置（HSTS, X-Frame-Options等）

#### 2.8.2 防护机制
- CSRF保护（令牌验证）
- 点击劫持防护（X-Frame-Options）
- MIME类型嗅探防护
- XSS防护（X-XSS-Protection）
- 内容安全策略（CSP）

#### 2.8.3 安全审计

##### 2.8.3.1 安全事件分类
- **认证**：登录、登出、认证失败
- **授权**：权限变更、访问控制
- **数据访问**：敏感数据访问
- **配置变更**：安全配置修改
- **系统事件**：启动、关闭、错误

##### 2.8.3.2 审计日志格式
```json
{
  "timestamp": "2025-10-18T10:30:00Z",
  "event_id": "evt_1234567890",
  "event_type": "security.link_validation_failed",
  "severity": "high",
  "user": {
    "id": "user123",
    "ip": "192.168.1.1"
  },
  "resource": {
    "type": "link",
    "id": "link_abc123",
    "url": "http://example.com"
  },
  "details": {
    "reason": "domain_blacklisted",
    "action": "blocked"
  }
}
```

##### 2.8.3.3 合规性检查
- GDPR合规性检查
- CCPA合规性检查
- 内部安全策略合规性

### 2.9 性能监控指标

#### 2.9.1 核心指标
| 指标名称 | 类型 | 描述 | 采集频率 |
|---------|------|------|---------|
| link_processing_latency | Histogram | 链接处理延迟(ms) | 每次请求 |
| link_processing_errors | Counter | 处理错误数 | 每次错误 |
| active_link_checks | Gauge | 当前活跃的链接检查数 | 每5秒 |
| cache_hit_rate | Gauge | 缓存命中率 | 每分钟 |

#### 2.9.2 告警规则
```yaml
groups:
- name: link_processing.rules
  rules:
  - alert: HighLinkProcessingLatency
    expr: histogram_quantile(0.95, sum(rate(link_processing_latency_seconds_bucket[5m])) by (le)) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High link processing latency"
      description: "95th percentile link processing latency is {{ $value }}s"
```

### 2.10 国际化支持

#### 2.10.1 多语言配置
```json
{
  "i18n": {
    "default_locale": "zh-CN",
    "supported_locales": ["zh-CN", "en-US"],
    "fallback_locale": "en-US"
  }
}
```

#### 2.10.2 错误消息模板
```json
{
  "errors": {
    "link_validation_failed": {
      "zh-CN": "链接验证失败: {reason}",
      "en-US": "Link validation failed: {reason}"
    },
    "security_violation": {
      "zh-CN": "安全策略违规: {policy}",
      "en-US": "Security policy violation: {policy}"
    }
  }
}
```

### 2.12 诊断集成

#### 2.12.1 与自动化诊断系统集成
```python
# 链接处理模块向诊断系统注册诊断项
from diagnostics_manager import DiagnosticsManager

class LinkProcessor:
    def __init__(self, config_manager: ConfigManager, diagnostics_manager: DiagnosticsManager):
        self.config_manager = config_manager
        self.diagnostics_manager = diagnostics_manager
        self._register_diagnostics()
        
    def _register_diagnostics(self):
        """注册链接处理诊断项"""
        self.diagnostics_manager.register_module("link_processing", {
            "validation_diagnostics": self._check_validation_rules,
            "performance_diagnostics": self._check_performance_metrics,
            "security_diagnostics": self._check_security_audit
        })
        
    def _check_validation_rules(self) -> DiagnosticResult:
        """链接验证规则诊断"""
        # 实现验证规则检查逻辑
        pass
        
    def _check_performance_metrics(self) -> DiagnosticResult:
        """性能指标诊断"""
        # 实现性能指标检查逻辑
        pass
        
    def _check_security_audit(self) -> DiagnosticResult:
        """安全审计诊断"""
        # 实现安全审计检查逻辑
        pass
```

#### 2.12.2 诊断配置管理
- 链接处理诊断配置通过统一的 `diagnostics.json` 管理
- 支持模块级别的诊断开关和阈值配置
- 与自动化诊断系统的配置热重载机制集成

### 2.13 链接验证器实现

#### 2.13.1 验证规则
```python
class LinkValidator:
    def __init__(self, config: dict):
        self.config = config
        self._init_validators()
        
    def _init_validators(self):
        self.validators = [
            self._validate_scheme,
            self._validate_domain,
            self._validate_path,
            self._validate_query,
            self._validate_fragment
        ]
        
    def validate(self, url: str) -> ValidationResult:
        """验证链接是否合法"""
        try:
            parsed = urllib.parse.urlparse(url)
            for validator in self.validators:
                result = validator(parsed)
                if not result.valid:
                    return result
            return ValidationResult(valid=True)
        except Exception as e:
            return ValidationResult(
                valid=False,
                code="invalid_url",
                message=f"Invalid URL: {str(e)}"
            )
```

#### 2.13.2 链接预取优化
```python
class LinkPrefetcher:
    def __init__(self, config: dict):
        self.config = config
        self.cache = LinkCache(config.get('cache', {}))
        
    async def prefetch_links(self, urls: List[str]):
        """预取链接"""
        sem = asyncio.Semaphore(self.config.get('max_concurrent', 5))
        
        async def fetch(url):
            async with sem:
                if await self.cache.has(url):
                    return
                    
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=10) as response:
                            content = await response.read()
                            await self.cache.set(url, {
                                'status': response.status,
                                'content_type': response.content_type,
                                'content': content[:self.config.get('max_preview_size', 1024)]
                            })
                except Exception as e:
                    logger.warning(f"Failed to prefetch {url}: {str(e)}")
        
        await asyncio.gather(*[fetch(url) for url in urls])
```

## 3. 任务衔接

### 3.1 前置任务
- LAD-IMPL-011：性能监控
  - 确保性能监控功能就绪
  - 验证性能数据收集准确性

### 3.2 后续任务
- LAD-IMPL-015（自动化诊断，并行轨，不阻塞 015B）
  - 链接处理诊断集成到自动化诊断系统中
  - 基于诊断结果进行问题修复
- V2.0：自愈机制
  - 基于链接处理状态实现自愈
  - 自动化问题诊断和修复

## 4. 实施步骤

### 4.1 LAD-IMPL-012: 链接处理接入
1. 实现基础链接解析功能
2. 集成配置管理
3. 添加基本的状态管理
4. 实现简单的链接点击处理

### 4.2 LAD-IMPL-013: 链接处理安全
1. 实现白名单/黑名单机制
2. 添加HTTPS强制验证
3. 实现安全日志记录
4. 添加安全测试用例

### 4.3 LAD-IMPL-014: 链接处理体验
1. 实现链接预览功能
2. 添加加载状态指示
3. 优化错误提示
4. 添加性能监控点

### 4.4 LAD-IMPL-015B: 链接处理验收
1. 执行端到端测试
2. 验证配置管理
3. 性能基准测试
4. 安全审计

## 5. 验收标准

### 5.1 功能要求
- [ ] 支持基本的链接点击功能
- [ ] 实现白名单/黑名单过滤
- [ ] 提供链接预览功能
- [ ] 支持配置热更新
- [ ] 实现链接重定向跟踪
- [ ] 支持取消和重试操作
- [ ] 提供详细的错误信息
- [ ] 与自动化诊断系统集成
- [ ] 支持诊断结果的收集和报告
- [ ] 实现诊断驱动的配置优化

### 5.2 性能要求
- [ ] 链接解析延迟 < 50ms（P99）
- [ ] 支持至少100个并发链接检查
- [ ] 内存占用稳定，无泄漏
- [ ] 缓存命中率 > 90%
- [ ] 系统资源占用 < 5%（空载）

### 5.3 安全要求
- [ ] 所有外部链接都经过安全验证
- [ ] 敏感操作有审计日志
- [ ] 配置变更需要授权
- [ ] 实现CSRF防护
- [ ] 支持内容安全策略
- [ ] 提供详细的安全事件报告

## 6. 相关文档

### 6.1 配置文档
- `config/app_config.json` - 主配置文件
- `config/external_modules.json` - 外部模块配置
- `config/features/link_processing.json` - 链接处理配置（优先）
- `config/features/security.json` - 安全策略配置（优先）
- `config/features/error_history.json` - 错误历史持久化配置（建议补齐最小配置）
- `config/features/diagnostics.json` - 自动化诊断配置（可选）

### 6.2 架构文档
- `core/application_state_manager.py` - 状态管理
- `core/snapshot_manager.py` - 快照管理
- `utils/config_manager.py` - 配置管理

### 6.3 参考文档
- LAD-IMPL-006B: 简化配置架构设计
- LAD-IMPL-011: 性能监控任务
- LAD-IMPL-015: 自动化诊断系统
- V2.0: 自愈机制设计

---

**最后更新**: 2025-10-18
