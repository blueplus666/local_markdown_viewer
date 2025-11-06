# LAD-IMPL-015: 自动化诊断 - 任务提示词

**文档版本**: V1.1  
**创建时间**: 2025-10-18  
**更新说明**: 适配V4.0简化配置架构

> **配置架构说明**  
> 本任务基于 LAD-IMPL-006B 的简化配置架构实现，使用扁平化配置管理。  
> 相关配置位于 `config/` 目录，通过 `ConfigManager` 统一访问。

## 0. 前置条件与AI执行守则

- **[前置-功能就绪]** 已具备：
  - `core/performance_metrics.py` 可用（与 `config/runtime/performance.json` 阈值对齐）。
  - 链接处理接入已可运行：`core/link_processor.py` 与 `ui/content_viewer.py` LPCLICK 路径畅通。
- **[前置-配置]** 诊断配置优先读取 `config/features/diagnostics.json`；如无，可在 `app_config.json` 下提供 `diagnostics` 段落作为兜底。
- **[前置-依赖关系]** 本任务与 `LAD-IMPL-015B（链接处理验收）` 可并行；不强依赖“增强并发测试”。
- **[AI执行守则]**
  - 不新增重型依赖（除非明确标注为可选），优先最小可行实现与可插拔架构。
  - 修改配置时保持向后兼容：优先 `features/diagnostics.json`，其次 `app.diagnostics`。
  - 诊断规则与报告结构需稳定、可扩展，并提供机器可读输出。

## 1. 任务概览

### 1.1 基本信息
- **任务ID**: LAD-IMPL-015
- **任务名称**: 自动化诊断
- **任务类型**: 功能开发
- **复杂度级别**: 高
- **预计交互**: 6-7次
- **依赖任务**: LAD-IMPL-011（性能监控）、LAD-IMPL-012（链接处理接入，简化版）
- **风险等级**: 中风险

### 1.2 任务目标
1. 实现系统健康检查
2. 开发自动化诊断工具
3. 提供修复建议
4. 集成到监控系统

## 2. 技术方案

### 2.1 配置集成

#### 2.1.1 配置文件
```json
// config/diagnostics.json
{
  "diagnostics": {
    "version": "1.0",
    "global": {
      "enabled": true,
      "schedule": "0 */6 * * *",
      "retention_days": 30,
      "alert_thresholds": {
        "cpu_usage": 90,
        "memory_usage": 85,
        "disk_usage": 90,
        "error_rate": 5,
        "response_time_ms": 1000
      }
    },
    "modules": {
      "system_health": {
        "enabled": true,
        "checks": ["cpu", "memory", "disk", "network"]
      },
      "link_processing": {
        "enabled": true,
        "checks": ["validation", "performance", "security"]
      },
      "performance": {
        "enabled": true,
        "metrics": ["latency", "throughput", "errors"]
      }
    }
  }
}
```

#### 2.1.2 配置访问（优先 features 其后 app）
```python
# 获取配置示例
cm = ConfigManager()
diag_config = (
    cm.get_config("diagnostics", {}, "features")
    or cm.get_unified_config().get("app", {}).get("diagnostics", {})
)
global_config = diag_config.get('global', {})
modules_config = diag_config.get('modules', {})
```

### 2.2 统一配置管理

#### 2.2.1 配置热重载
```python
class DiagnosticsManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._load_config()
        self.config_manager.add_listener("diagnostics", self._on_config_changed)
    
    def _load_config(self):
        """从配置中加载诊断参数"""
        diag_config = self.config_manager.get_config("diagnostics", {}, "features")
        self.enabled = diag_config.get("global", {}).get("enabled", True)
        self.modules = diag_config.get("modules", {})
        
    def _on_config_changed(self, config_path: str):
        """配置变更时重新加载"""
        if "diagnostics" in config_path:
            self._load_config()
            logger.info("诊断配置已更新")
```

### 2.3 状态管理集成

#### 2.3.1 诊断状态管理
- 使用 `ApplicationStateManager` 管理诊断状态
- 实时更新诊断进度和结果

#### 2.3.2 快照支持
- 集成 `SnapshotManager` 支持诊断配置快照
- 支持诊断场景的保存和回放

### 2.4 诊断项目

#### 2.4.1 系统健康检查
- 服务状态
- 资源使用情况
- 依赖服务连通性
- 配置有效性

#### 2.4.2 性能诊断
- 响应时间分析
- 资源瓶颈识别
- 慢查询检测
- 内存泄漏检测

#### 2.4.3 链接处理诊断
- 链接验证诊断
  - 协议合规性检查
  - 域名白名单/黑名单验证
  - 重定向安全评估
- 性能问题诊断
  - 链接解析延迟分析
  - 并发处理瓶颈识别
  - 缓存命中率评估
- 安全审计诊断
  - 安全策略合规检查
  - 潜在风险识别
  - 修复建议生成

#### 2.4.4 诊断工具
- **诊断引擎**: 核心诊断逻辑
- **规则引擎**: 诊断规则管理
- **修复建议器**: 提供修复方案
- **报告生成器**: 生成诊断报告

### 2.5 集成方案
- REST API
- 命令行工具
- 定时任务
- 告警集成

## 3. 任务衔接

### 3.1 前置任务
- LAD-IMPL-011：性能监控就绪
  - 确保监控指标收集就绪，阈值配置与运行时配置对齐
- LAD-IMPL-012：链接处理接入（简化版）
  - LPCLICK 路径畅通，基础处理动作可执行
- （可选）增强并发测试支线
  - 若未具备依赖，可跳过，不阻塞本任务

### 3.2 后续任务
- LAD-IMPL-015B：链接处理验收（并行）
  - 可基于已有诊断结果辅助验收，但不作为强制依赖
- V2.0：自愈机制
  - 基于诊断结果实施自愈
  - 完善自动化运维流程

## 4. 实施步骤

### 3.1 需求分析
1. 确定诊断范围
2. 设计诊断规则
3. 定义诊断指标

### 3.2 开发实施
1. 开发诊断引擎
2. 实现诊断规则
3. 开发修复建议器
4. 实现报告生成

### 3.3 测试验证
1. 单元测试
2. 集成测试
3. 性能测试

### 3.4 部署上线
1. 部署诊断服务
2. 配置监控告警
3. 培训文档

## 5. 验收标准

### 5.1 功能验收
- [ ] 支持所有预定义的诊断项
- [ ] 提供准确的修复建议
- [ ] 生成详细的诊断报告
- [ ] 支持定时执行
- [ ] 链接处理诊断功能完整
  - [ ] 协议合规性检查
  - [ ] 域名白名单/黑名单验证
  - [ ] 重定向安全评估
  - [ ] 性能问题诊断
  - [ ] 安全审计诊断

### 5.2 性能要求
- 诊断执行时间 < 30秒
- 支持并发诊断
- 低资源消耗

## 6. 相关文档

### 6.1 配置文档
- `config/diagnostics.json` 配置说明
- 状态管理接口文档
- 快照管理指南

### 6.2 诊断文档

#### 6.2.1 设计文档
- 架构设计
- 接口定义
- 数据模型

#### 6.2.2 用户手册
- 快速开始
- 配置说明
- 常见问题

## 7. 风险与缓解

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| 误报率高 | 中 | 中 | 优化诊断规则 |
| 性能影响 | 高 | 低 | 资源限制和调度 |
| 修复建议不准确 | 中 | 中 | 持续优化建议引擎 |

## 8. 后续任务

1. 增加更多诊断规则
2. 优化修复建议
3. 增强报告功能
4. 集成更多监控数据源

---

**最后更新**: 2025-10-18
