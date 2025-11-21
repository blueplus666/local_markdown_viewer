#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
link_processor.py - 接口伪实现（最小可导入版本）
职责：定义链接处理相关的核心类型、接口与占位实现，便于pytest用例骨架运行。

说明：当前仅为骨架，方法大多返回占位结果或抛出NotImplementedError，
后续可按设计文档逐步填充真实逻辑。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Protocol
from urllib.parse import urlparse, unquote
import json
import logging
import os
from utils.config_manager import get_config_manager


class LinkType(Enum):
    ANCHOR = "ANCHOR"
    EXTERNAL_HTTP = "EXTERNAL_HTTP"
    RELATIVE_MD = "RELATIVE_MD"
    FILE_PROTOCOL = "FILE_PROTOCOL"
    IMAGE = "IMAGE"
    MERMAID = "MERMAID"
    TOC = "TOC"
    DIRECTORY = "DIRECTORY"
    UNKNOWN = "UNKNOWN"


class ErrorCode(Enum):
    OK = "OK"
    RESOLVE_ERROR = "RESOLVE_ERROR"
    NOT_FOUND = "NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    SECURITY_BLOCKED = "SECURITY_BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class LinkContext:
    href: str
    current_file: Optional[Path] = None
    current_dir: Optional[Path] = None
    source_component: str = ""
    extra: Dict[str, Any] = None


@dataclass
class ValidationResult:
    ok: bool
    error_code: Optional[ErrorCode] = None
    message: str = ""
    details: Dict[str, Any] = None


@dataclass
class LinkResult:
    success: bool
    action: str = ""
    payload: Dict[str, Any] = None
    message: str = ""
    error_code: Optional[ErrorCode] = None


class ILinkHandler(Protocol):
    def handle(self, ctx: LinkContext, resolved: Any) -> LinkResult:  # pragma: no cover - 占位接口
        ...


class LinkTypeRecognizer:
    """最小识别器占位：仅覆盖最简单规则，便于单测骨架运行。"""

    def recognize(self, href: str, context: LinkContext) -> LinkType:
        if not href:
            return LinkType.UNKNOWN
        h = href.strip().lower()
        if h.startswith('#'):
            return LinkType.ANCHOR
        if h.startswith('mailto:'):
            return LinkType.EXTERNAL_HTTP  # 临时归为外链，交给外部处理器或专用处理器
        if h.startswith('http://') or h.startswith('https://'):
            return LinkType.EXTERNAL_HTTP
        if h.startswith('file:///') or (len(h) > 2 and h[1] == ':' and ('\\' in h or '/' in h)):
            return LinkType.FILE_PROTOCOL
        if h.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
            return LinkType.IMAGE
        if h.endswith('.md') and not (h.startswith('http://') or h.startswith('https://')):
            return LinkType.RELATIVE_MD
        # 简化的目录判定（骨架）：以斜杠结尾
        if h.endswith('/') or h.endswith('\\'):
            return LinkType.DIRECTORY
        # Mermaid图表识别（通过事件extra或文件扩展名）
        if context.extra and context.extra.get("mermaid_container"):
            return LinkType.MERMAID
        if h.endswith(('.mmd', '.mermaid')):
            return LinkType.MERMAID
        # TOC目录项识别（包含#的链接）
        if '#' in h and not h.startswith('#'):
            return LinkType.TOC
        return LinkType.UNKNOWN


class PathResolver:
    def resolve_relative(self, current_file: Path, href: str) -> Path:
        """基于当前文件解析相对路径，并执行Windows风格标准化。
        - 当前文件为空时退化为基于当前工作目录解析
        - 绝对路径直接标准化返回
        - 正确处理 ./ 和 ../ 相对路径语义
        - 修复：相对路径应基于当前文件所在目录，而非累积嵌套
        """
        # 绝对路径：直接标准化
        candidate = Path(href)
        if candidate.is_absolute():
            try:
                # 使用 strict=False 的 resolve 折叠 .. 和 .，不依赖存在性
                return self.normalize_windows_path(candidate.resolve(strict=False))
            except Exception:
                return self.normalize_windows_path(candidate)
        
        # 基础目录：使用当前文件的目录
        base_dir = current_file.parent if current_file else Path.cwd()
        
        # 处理相对路径：确保正确解析 ./ 和 ../ 
        # 关键修复：使用 resolve() 正确处理相对路径，避免目录累积
        try:
            # 先组合路径，然后标准化解析
            combined = base_dir / href
            # 使用 resolve(strict=False) 正确处理 ./ 和 ../ 语义
            resolved = combined.resolve(strict=False)
        except Exception:
            # 降级处理
            resolved = base_dir / href
        
        return self.normalize_windows_path(resolved)

    def resolve_file_protocol(self, url: str) -> Path:
        """解析 file:// URL 为本地路径（Windows优先）。
        兼容形如 file:///C:/path/to/file.md 或 file:///d:/docs/a.md
        """
        parsed = urlparse(url)
        if parsed.scheme != "file":
            raise ValueError("URL scheme is not file")
        raw_path = unquote(parsed.path or "")
        # Windows场景：/C:/path 形式，去掉起始斜杠
        if len(raw_path) >= 3 and raw_path[0] == "/" and raw_path[2] == ":":
            raw_path = raw_path.lstrip("/")
        # 统一使用本机Path处理
        return self.normalize_windows_path(Path(raw_path))

    def normalize_windows_path(self, path: Path) -> Path:
        # 使用os.path.normpath消除冗余段，尽量不访问文件系统
        normed = os.path.normpath(str(path))
        return Path(normed)


class LinkValidator:
    def validate(self, resolved: Any, policy: Dict[str, Any]) -> ValidationResult:
        """最小可用校验：
        - URL: 协议/域名白名单（allowed_protocols/allowed_domains）
        - Path: 存在性、深度、禁止模式（forbidden_patterns）、可选ACL可读性
        """
        policy = policy or {}
        security = (policy.get("security") or {})
        windows_specific = (policy.get("windows_specific") or {})

        # URL校验
        if isinstance(resolved, str):
            pr = urlparse(resolved)
            if pr.scheme:
                allowed_protocols = security.get("allowed_protocols")
                if allowed_protocols and pr.scheme not in allowed_protocols:
                    return ValidationResult(ok=False, error_code=ErrorCode.SECURITY_BLOCKED, message="protocol not allowed", details={"scheme": pr.scheme})
                if pr.scheme in ("http", "https"):
                    allowed_domains = security.get("allowed_domains")
                    # fail-closed：空列表或None → 拒绝外链
                    if not allowed_domains or pr.netloc not in allowed_domains:
                        return ValidationResult(ok=False, error_code=ErrorCode.SECURITY_BLOCKED, message="domain not allowed", details={"domain": pr.netloc})
                return ValidationResult(ok=True)

        # 路径校验
        if isinstance(resolved, Path):
            # 先检查原始路径字符串中的禁止模式（在标准化之前）
            original_path_str = str(resolved)
            forbidden_patterns = security.get("forbidden_patterns") or []
            for pat in forbidden_patterns:
                if pat and pat in original_path_str:
                    return ValidationResult(ok=False, error_code=ErrorCode.SECURITY_BLOCKED, message="forbidden pattern", details={"pattern": pat})
            
            # 标准化
            path_str = os.path.normpath(original_path_str)
            p = Path(path_str)
            
            # 深度限制（在存在性检查之前，避免路径不存在时跳过深度检查）
            max_depth = windows_specific.get("max_path_depth")
            if max_depth:
                # 以盘符/根为起点计算层级
                parts = [part for part in p.parts if part not in (p.anchor, "")]
                if len(parts) > int(max_depth):
                    return ValidationResult(ok=False, error_code=ErrorCode.SECURITY_BLOCKED, message="max depth exceeded", details={"depth": len(parts), "max": max_depth})
            
            # 驱动器字母验证（Windows特定，在存在性检查之前）
            drive_letters = windows_specific.get("drive_letters")
            if drive_letters:
                drive = p.drive
                if drive and drive not in drive_letters:
                    return ValidationResult(ok=False, error_code=ErrorCode.SECURITY_BLOCKED, message="drive not allowed", details={"drive": drive})
            
            # 存在性（默认检查）
            if policy.get("check_exists", True):
                if not p.exists():
                    return ValidationResult(ok=False, error_code=ErrorCode.NOT_FOUND, message="path not found", details={"path": path_str})
            # 可选ACL（默认不检查，避免跨平台不稳定）
            if policy.get("check_acl", False):
                if not os.access(path_str, os.R_OK):
                    return ValidationResult(ok=False, error_code=ErrorCode.PERMISSION_DENIED, message="no read permission", details={"path": path_str})
            
            return ValidationResult(ok=True)

        # 其他类型默认通过
        return ValidationResult(ok=True)


class LinkProcessor:
    def __init__(self, config_manager: Any = None, file_resolver: Any = None, logger: Any = None,
                 snapshot_manager: Any = None, performance_metrics: Any = None) -> None:
        self.config_manager = config_manager or get_config_manager()
        self.file_resolver = file_resolver
        self.snapshot_manager = snapshot_manager
        self.performance_metrics = performance_metrics
        # 统一适配为 LoggerAdapter，并固定额外字段
        self._cached_build_version: Optional[str] = None
        build_version = self._resolve_build_version(config_manager)
        if logger is not None and not isinstance(logger, logging.LoggerAdapter):
            self.logger = logging.LoggerAdapter(
                logger,
                {"app": "local_markdown_viewer", "module_name": "link_processor", "build_version": build_version},
            )
        else:
            self.logger = logger
        self.recognizer = LinkTypeRecognizer()
        self.path_resolver = PathResolver()
        self.validator = LinkValidator()
        self._handlers: Dict[LinkType, ILinkHandler] = {}
        # 从配置加载策略
        self.policy = self._load_policy_from_config()

    def set_handlers(self, handlers: Dict[LinkType, ILinkHandler]) -> None:
        self._handlers.update(handlers)

    def set_policy(self, policy: Dict[str, Any]) -> None:
        self.policy = policy or {}
        
    def _load_policy_from_config(self) -> Dict[str, Any]:
        """从配置管理器加载链接处理策略"""
        if not self.config_manager:
            return {"check_exists": True, "security": {}}
        try:
            cm = self.config_manager or get_config_manager()
            get_uc = getattr(cm, "get_unified_config", None)
            get_cfg = getattr(cm, "get_config", None)

            link_cfg: Dict[str, Any] = {}
            sec_cfg: Dict[str, Any] = {}

            # 优先读取 app_config.json 下的 link_processing（推荐：app.link_processing），其次顶层link_processing
            if callable(get_uc):
                link_cfg = get_uc("app.link_processing", {}) or link_cfg
                # features/link_processing.json 兜底
                link_cfg = link_cfg or get_uc("features.link_processing", {}) or {}
                # security 优先 features，再到 app
                sec_cfg = get_uc("features.security", {}) or get_uc("app.security", {}) or {}
            if not link_cfg and callable(get_cfg):
                # 兼容：如果在app_config根部有link_processing
                try:
                    link_cfg = get_cfg("link_processing", {}, "app")
                except Exception:
                    link_cfg = {}
            if not sec_cfg and callable(get_cfg):
                try:
                    sec_cfg = get_cfg("security", {}, "app")
                except Exception:
                    sec_cfg = {}

            # 默认策略（fail-closed：存在性检查为True）
            policy: Dict[str, Any] = {
                "enabled": (link_cfg.get("enabled", True) if isinstance(link_cfg, dict) else True),
                # 兼容旧键：relative_paths → check_exists（仅当未显式提供check_exists时）
                "check_exists": bool(
                    link_cfg.get("check_exists", link_cfg.get("relative_paths", True))
                ) if isinstance(link_cfg, dict) else True,
                "external_links": (link_cfg.get("external_links", True) if isinstance(link_cfg, dict) else True),
                "image_links": (link_cfg.get("image_links", True) if isinstance(link_cfg, dict) else True),
                "mermaid_links": (link_cfg.get("mermaid_links", True) if isinstance(link_cfg, dict) else True),
                "file_protocol": (link_cfg.get("file_protocol", True) if isinstance(link_cfg, dict) else True),
                "cache_enabled": (link_cfg.get("cache_enabled", True) if isinstance(link_cfg, dict) else True),
                "cache_size": (link_cfg.get("cache_size", 1000) if isinstance(link_cfg, dict) else 1000),
                "error_handling": (link_cfg.get("error_handling", "strict") if isinstance(link_cfg, dict) else "strict"),
                "windows_specific": (link_cfg.get("windows_specific", {}) if isinstance(link_cfg, dict) else {}),
                # security 合并：link_cfg.security 优先，否则采用独立的 sec_cfg
                "security": (link_cfg.get("security") if isinstance(link_cfg, dict) else None) or sec_cfg or {},
                "logging": (link_cfg.get("logging", {}) if isinstance(link_cfg, dict) else {}),
            }

            return policy
        except Exception as ex:
            if self.logger:
                self.logger.warning(f"Failed to load link processing config: {ex}")
            # 默认保持保守策略
            return {"check_exists": True, "security": {}}

    def process_link(self, ctx: LinkContext) -> LinkResult:  # pragma: no cover - 简化骨架
        try:
            # 保护extra
            if ctx.extra is None:
                ctx.extra = {}
            session_id = ctx.extra.get("session_id")

            link_type = self.recognizer.recognize(ctx.href, ctx)
            result: LinkResult

            # 预处理：解析与验证
            if link_type in (LinkType.RELATIVE_MD, LinkType.DIRECTORY):
                base_file = ctx.current_file or (ctx.current_dir / "_base_.md" if ctx.current_dir else None)
                resolved_path = self.path_resolver.resolve_relative(base_file, ctx.href)
                vres = self.validator.validate(resolved_path, self.policy)
                if not vres.ok:
                    result = LinkResult(success=False, action="show_error", payload={"path": str(resolved_path)}, message=vres.message, error_code=vres.error_code)
                else:
                    handler = self._handlers.get(link_type)
                    if handler is None:
                        result = LinkResult(success=False, action="", payload={}, message="Handler not implemented", error_code=ErrorCode.UNSUPPORTED)
                    else:
                        result = handler.handle(ctx, resolved_path)

            elif link_type == LinkType.FILE_PROTOCOL:
                try:
                    resolved_path = self.path_resolver.resolve_file_protocol(ctx.href)
                except Exception as ex:
                    result = LinkResult(success=False, action="show_error", payload={}, message=str(ex), error_code=ErrorCode.RESOLVE_ERROR)
                else:
                    vres = self.validator.validate(resolved_path, self.policy)
                    if not vres.ok:
                        result = LinkResult(success=False, action="show_error", payload={"path": str(resolved_path)}, message=vres.message, error_code=vres.error_code)
                    else:
                        handler = self._handlers.get(LinkType.FILE_PROTOCOL)
                        if handler is None:
                            result = LinkResult(success=False, action="", payload={}, message="Handler not implemented", error_code=ErrorCode.UNSUPPORTED)
                        else:
                            result = handler.handle(ctx, resolved_path)

            elif link_type == LinkType.EXTERNAL_HTTP:
                # 始终执行URL校验（fail-closed 策略）
                vres = self.validator.validate(ctx.href, self.policy)
                if not vres.ok:
                    result = LinkResult(success=False, action="show_error", payload={"url": ctx.href}, message=vres.message, error_code=vres.error_code)
                else:
                    handler = self._handlers.get(link_type)
                    if handler is None:
                        result = LinkResult(success=False, action="", payload={}, message="Handler not implemented", error_code=ErrorCode.UNSUPPORTED)
                    else:
                        result = handler.handle(ctx, ctx.href)

            elif link_type == LinkType.IMAGE:
                # 图片链接处理
                handler = self._handlers.get(link_type)
                if handler is None:
                    result = LinkResult(success=False, action="", payload={}, message="Handler not implemented", error_code=ErrorCode.UNSUPPORTED)
                else:
                    result = handler.handle(ctx, ctx.href)
                    
            elif link_type == LinkType.MERMAID:
                # Mermaid图表链接处理
                handler = self._handlers.get(link_type)
                if handler is None:
                    result = LinkResult(success=False, action="", payload={}, message="Handler not implemented", error_code=ErrorCode.UNSUPPORTED)
                else:
                    result = handler.handle(ctx, ctx.href)
                    
            elif link_type == LinkType.TOC:
                # TOC目录项处理
                handler = self._handlers.get(link_type)
                if handler is None:
                    result = LinkResult(success=False, action="", payload={}, message="Handler not implemented", error_code=ErrorCode.UNSUPPORTED)
                else:
                    result = handler.handle(ctx, ctx.href)
                    
            else:
                # 其他类型维持原有简单路由（例如 ANCHOR）
                handler = self._handlers.get(link_type)
                if handler is None:
                    result = LinkResult(success=False, action="", payload={}, message="Handler not implemented", error_code=ErrorCode.UNSUPPORTED)
                else:
                    result = handler.handle(ctx, ctx.href)

            # 日志
            self._log_event(session_id, ctx, link_type, result)
            self._record_link_snapshot(ctx, result)
            return result
        except Exception as ex:  # 骨架容错
            if self.logger:
                self.logger.exception("link_processor_internal_error")
            result = LinkResult(success=False, action="", payload={}, message=str(ex), error_code=ErrorCode.INTERNAL_ERROR)
            self._record_link_snapshot(ctx, result)
            return result

    def _log_event(self, session_id: Optional[str], ctx: LinkContext, link_type: LinkType, result: LinkResult) -> None:
        if not self.logger:
            return
        try:
            event = {
                "session_id": session_id,
                "href": ctx.href,
                "type": link_type.name if isinstance(link_type, LinkType) else str(link_type),
                "action": result.action,
                "success": result.success,
                "error_code": result.error_code.name if result.error_code else None,
            }
            logging_cfg = (self.policy.get("logging") or {})
            if logging_cfg.get("json", False):
                # 结构化JSON日志
                # 附带固定字段
                event.update({
                    "app": "local_markdown_viewer",
                    "module_name": "link_processor",
                    "build_version": self._resolve_build_version(self.config_manager),
                })
                self.logger.info(json.dumps(event, ensure_ascii=False))
            else:
                # 标准extra字段（推荐）
                # 确保extra字段正确传递到LogRecord
                self.logger.info("link_processed", extra=event)
        except Exception:
            # 不影响主流程
            pass

    def _record_link_snapshot(self, ctx: LinkContext, result: LinkResult) -> None:
        snapshot_manager = getattr(self, "snapshot_manager", None)
        if snapshot_manager:
            try:
                extra = ctx.extra or {}
                snapshot_manager.save_link_snapshot({
                    "link_processor_loaded": True,
                    "policy_profile": extra.get("policy", "default"),
                    "last_action": result.action or "none",
                    "last_result": "ok" if result.success else ("warn" if result.action else "error"),
                    "details": {
                        "href": ctx.href,
                        "current_file": str(ctx.current_file) if ctx.current_file else None,
                        "current_dir": str(ctx.current_dir) if ctx.current_dir else None,
                        "source_component": ctx.source_component,
                        "action": result.action,
                        "message": result.message,
                    },
                    "error_code": (result.error_code.name if result.error_code else ""),
                    "message": result.message,
                })
            except Exception:
                pass
        metrics = getattr(self, "performance_metrics", None)
        if metrics:
            try:
                metrics.record_link_update({
                    "last_result": "ok" if result.success else "error",
                })
            except Exception:
                pass

    def _resolve_build_version(self, config_manager: Any) -> str:
        # 缓存命中
        if self._cached_build_version:
            return self._cached_build_version
        # 1) 配置项
        try:
            if config_manager and hasattr(config_manager, "get_config"):
                v = config_manager.get_config("build.version", None)
                if v:
                    self._cached_build_version = str(v)
                    return self._cached_build_version
        except Exception:
            pass
        # 2) 环境变量
        env_v = os.environ.get("LAD_BUILD_VERSION")
        if env_v:
            self._cached_build_version = env_v
            return self._cached_build_version
        # 3) pyproject.toml（PEP 621 或 poetry）
        try:
            from pathlib import Path as _Path
            here = _Path(__file__).resolve()
            for parent in list(here.parents)[:6]:
                cand = parent / "pyproject.toml"
                if cand.exists():
                    ver = self._read_pyproject_version(cand)
                    if ver:
                        self._cached_build_version = ver
                        return ver
        except Exception:
            pass
        # 4) 默认
        self._cached_build_version = "dev"
        return self._cached_build_version

    def _read_pyproject_version(self, toml_path: Path) -> Optional[str]:
        """最小无依赖解析：
        - 优先 [project] 表中的 version = "x.y.z"
        - 其次 [tool.poetry] 中的 version = "x.y.z"
        """
        try:
            text = toml_path.read_text(encoding="utf-8", errors="ignore")
            # 简单状态机识别当前段
            current = None
            version_in_project = None
            version_in_poetry = None
            for raw in text.splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    current = line.strip("[]").strip()
                    continue
                if line.startswith("version") and "=" in line:
                    # 提取右侧字符串
                    try:
                        right = line.split("=", 1)[1].strip()
                        if right.startswith("\""):
                            val = right.split("\"", 2)[1]
                        elif right.startswith("'"):
                            val = right.split("'", 2)[1]
                        else:
                            val = right
                    except Exception:
                        continue
                    if current == "project" and not version_in_project:
                        version_in_project = val
                    elif current == "tool.poetry" and not version_in_poetry:
                        version_in_poetry = val
            return version_in_project or version_in_poetry
        except Exception:
            return None


# 简单的占位处理器，便于路由测试
class ExternalHandler:
    def handle(self, ctx: LinkContext, resolved: Any) -> LinkResult:
        return LinkResult(success=True, action="open_browser", payload={"url": ctx.href}, message="", error_code=None)


class RelativeMarkdownHandler:
    def handle(self, ctx: LinkContext, resolved: Any) -> LinkResult:
        return LinkResult(success=True, action="open_markdown_in_tree", payload={"path": str(resolved)}, message="", error_code=None)


class DirectoryHandler:
    def handle(self, ctx: LinkContext, resolved: Any) -> LinkResult:
        return LinkResult(success=True, action="open_directory", payload={"path": str(resolved)}, message="", error_code=None)


class AnchorHandler:
    def handle(self, ctx: LinkContext, resolved: Any) -> LinkResult:
        # 提取锚点ID（去掉#号）
        anchor_id = ctx.href.lstrip('#')
        return LinkResult(success=True, action="scroll_to_anchor", payload={"id": anchor_id}, message="", error_code=None)


class ImageHandler:
    def handle(self, ctx: LinkContext, resolved: Any) -> LinkResult:
        return LinkResult(success=True, action="open_image_viewer", payload={"path": str(resolved)}, message="", error_code=None)


class MermaidHandler:
    def handle(self, ctx: LinkContext, resolved: Any) -> LinkResult:
        return LinkResult(success=True, action="open_mermaid_viewer", payload={"path": str(resolved)}, message="", error_code=None)


class TocHandler:
    def handle(self, ctx: LinkContext, resolved: Any) -> LinkResult:
        # TOC项统一路由到锚点处理
        anchor_id = ctx.href.lstrip('#')
        return LinkResult(success=True, action="scroll_to_anchor", payload={"id": anchor_id}, message="", error_code=None)


class FileProtocolHandler:
    def handle(self, ctx: LinkContext, resolved: Any) -> LinkResult:
        return LinkResult(success=True, action="open_markdown_in_tree", payload={"path": str(resolved)}, message="", error_code=None)


# --- 文档注释：引用示例（仅供参考，非运行代码） ---
# 链接处理模块中对统一异常与缓存通配删除工具的示例用法：
# from core.errors import FileReadError, ErrorSeverity
# from cache.delete_pattern_utils import delete_pattern
# 
# 示例：处理链接时读取依赖文件，捕获统一异常
# try:
# 	ref = file_resolver.read_file(ref_path)
# except FileReadError:
# 	logger.warning("Reference not readable", extra={"severity": ErrorSeverity.LOW.value})
# 
# 示例：按域名失效外部链接解析缓存
# domain = "example.com"
# pattern = f"link_resolution:*:{domain}*"  # 具体规则视键结构调整
# _ = delete_pattern(resolution_cache, pattern)

