#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone Link Handling Debugger
=================================

Purpose:
- Render a Markdown file (default: LAD_Project/README.md)
- Log all hyperlinks found in the rendered HTML
- When the user clicks a link, run core.link_processor to recognize, resolve, validate, and log full details
- If the action is navigable (e.g., open_markdown_in_tree, scroll_to_anchor), perform it inside the viewer

Usage:
  python tests/tools/link_debug_readme.py [markdown_path]

This script isolates the markdown rendering + link processing flow from the main app, to determine whether
the core modules work correctly. If this works but main app still fails to navigate, the issue is outside
these core modules (e.g., outer UI wiring).
"""

from __future__ import annotations

import sys
import logging
import re
from pathlib import Path
from typing import List, Tuple

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QMenu, QAction
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings

# Ensure project root is importable when running from local_markdown_viewer cwd
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
LAD_PROJECT_DIR = WORKSPACE_ROOT / "LAD_Project"

from utils.config_manager import get_config_manager
from core.content_preview import ContentPreview
from core.link_processor import (
    LinkProcessor, LinkContext, LinkType,
    ExternalHandler, RelativeMarkdownHandler, DirectoryHandler, AnchorHandler,
    ImageHandler, MermaidHandler, TocHandler, FileProtocolHandler,
)


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("link_debugger")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger


def extract_links_from_html(html: str) -> List[Tuple[str, str]]:
    """Very simple href extractor: returns list of (href, text?) where text is best-effort.
    We keep it minimal; precision is sufficient for debugging link counts and targets.
    """
    links = []
    # Find <a ... href="...">...</a>
    pattern = re.compile(r"<a\s+[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
    for href, inner in pattern.findall(html or ""):
        # Strip HTML tags inside inner text for readability
        text = re.sub(r"<[^>]+>", "", inner).strip()
        links.append((href.strip(), text))
    return links


class InterceptingPage(QWebEnginePage):
    def __init__(self, on_link_clicked, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_link_clicked = on_link_clicked

    def acceptNavigationRequest(self, url: QUrl, nav_type, isMainFrame: bool) -> bool:
        # Intercept user link clicks only; allow other navigations (initial load, same-document) as needed
        # Always intercept our custom scheme regardless of nav_type
        if url.scheme() == "lpdebug":
            try:
                from urllib.parse import unquote
                raw = unquote(url.toString()[len("lpdebug://"):])
                self._on_link_clicked(QUrl(raw))
            finally:
                return False
        if nav_type == QWebEnginePage.NavigationTypeLinkClicked:
            try:
                self._on_link_clicked(url)
            finally:
                return False  # block default navigation; we handle it
        return super().acceptNavigationRequest(url, nav_type, isMainFrame)

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Surface JS logs to Python stdout for debugging
        print(f"[JS] {message}")
        # Detect synthetic click messages and route to handler
        prefix = "LPCLICK:"
        if isinstance(message, str) and message.startswith(prefix):
            href = message[len(prefix):].strip()
            if href:
                self._on_link_clicked(QUrl(href))


class LinkDebugger(QWidget):
    def __init__(self, markdown_path: Path, logger: logging.Logger):
        super().__init__()
        self.logger = logger
        self.config_manager = get_config_manager()
        self.preview = ContentPreview(self.config_manager)
        self.current_file = markdown_path.resolve()
        self._last_clicked_href: str = ""
        self._history_stack: list[str] = []  # 与 ContentViewer 对齐的简单回退栈
        # 导航保护与历史上限
        self._nav_in_progress: bool = False
        try:
            # 复用 UI 配置文件的命名空间，便于统一管理
            self._history_max: int = int(self.config_manager.get_config("link_debugger.history_max", 200, "ui"))
        except Exception:
            self._history_max = 200

        # Link processor and handlers
        self.link_processor = LinkProcessor(
            config_manager=self.config_manager,
            file_resolver=None,
            logger=logging.getLogger("core.link_processor"),
        )
        self.link_processor.set_handlers({
            LinkType.EXTERNAL_HTTP: ExternalHandler(),
            LinkType.RELATIVE_MD: RelativeMarkdownHandler(),
            LinkType.DIRECTORY: DirectoryHandler(),
            LinkType.ANCHOR: AnchorHandler(),
            LinkType.IMAGE: ImageHandler(),
            LinkType.MERMAID: MermaidHandler(),
            LinkType.TOC: TocHandler(),
            LinkType.FILE_PROTOCOL: FileProtocolHandler(),
        })

        # UI
        layout = QVBoxLayout(self)
        self.view = QWebEngineView(self)
        self.page = InterceptingPage(self._on_link_clicked, self)
        self.view.setPage(self.page)
        # Ensure JS is enabled
        self.view.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        # 接入自定义右键菜单：Back/Forward/Reload，并打印与 ContentViewer 对齐的 NAV 日志
        try:
            from PyQt5.QtCore import Qt
            self.view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self._show_context_menu)
        except Exception as e:
            self.logger.warning(f"设置自定义菜单失败: {e}")
        layout.addWidget(self.view)

        self.setWindowTitle("Link Debugger - README")
        self.resize(1000, 700)

        # Inject after load
        self.view.page().loadFinished.connect(self._on_load_finished)
        self._load_markdown(self.current_file)

    def _load_markdown(self, path: Path) -> None:
        self.logger.info(f"Loading: {path}")
        result = self.preview.preview_file(path)
        if not result.get("success"):
            error_msg = result.get('error_message', '未知错误')
            error_info = result.get('error_info', {})
            
            # 生成 debug_render/*.fail.json 文件
            try:
                import json
                debug_dir = Path(__file__).parent.parent / 'debug_render'
                debug_dir.mkdir(parents=True, exist_ok=True)
                debug_file = debug_dir / f'{path.name}.fail.json'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'stage': 'link_debugger_load',
                        'file_path': str(path),
                        'error_message': error_msg,
                        'error_info': error_info,
                        'result': result
                    }, f, ensure_ascii=False, indent=2)
                self.logger.info(f"已保存错误详情到: {debug_file}")
            except Exception as e:
                self.logger.error(f"保存错误详情失败: {e}")
            
            # 显示详细错误信息
            detailed_error = f"Preview failed: {error_msg}"
            if error_info:
                try:
                    detailed_error += f"\n\n详细错误信息:\n{json.dumps(error_info, ensure_ascii=False, indent=2)}"
                except Exception:
                    pass
            
            self.logger.error(detailed_error)
            self.view.setHtml(f"<pre>{detailed_error}</pre>",
                              baseUrl=QUrl.fromLocalFile(str(path.parent)))
            return

        html = result.get("html", "")
        links = extract_links_from_html(html)
        self.logger.info(f"Found {len(links)} links in HTML")
        for idx, (href, text) in enumerate(links, start=1):
            self.logger.info(f"[{idx}] href={href} text={text}")

        # Set baseUrl so relative links resolve against current file directory
        self.view.setHtml(html, baseUrl=QUrl.fromLocalFile(str(path.parent)))

    def _on_link_clicked(self, url: QUrl) -> None:
        href = url.toString()
        self._last_clicked_href = href
        ctx = LinkContext(href=href, current_file=self.current_file, current_dir=self.current_file.parent,
                          source_component="link_debugger", extra={"session_id": "debug-session"})

        self.logger.info("Clicked link:")
        self.logger.info(f"  href: {href}")
        self.logger.info(f"  current_file: {self.current_file}")

        result = self.link_processor.process_link(ctx)
        self.logger.info("LinkProcessor result:")
        self.logger.info(f"  success: {result.success}")
        self.logger.info(f"  action: {result.action}")
        self.logger.info(f"  message: {result.message}")
        self.logger.info(f"  error_code: {result.error_code}")
        self.logger.info(f"  payload: {result.payload}")

        # Optional: perform action to prove navigation works in isolation
        try:
            self._perform_action(result)
        except Exception as ex:
            self.logger.error(f"Perform action failed: {ex}")

    def _on_load_finished(self, ok: bool) -> None:
        if not ok:
            self.logger.error("Page load failed")
            return
        js = r"""
            (function() {
                console.log('link-debugger: attaching link handlers');
                var anchors = document.querySelectorAll('a[href]');
                for (var i = 0; i < anchors.length; i++) {
                    (function(a){
                        a.addEventListener('click', function(ev){
                            try {
                                ev.preventDefault();
                                var href = a.getAttribute('href') || '';
                                console.log('link-debugger: click -> ' + href);
                                // Emit a console signal that Python listens for; avoids navigation
                                console.log('LPCLICK:' + href);
                            } catch (e) {
                                console.log('link-debugger: error ' + e);
                            }
                            return false;
                        }, true);
                    })(anchors[i]);
                }
                console.log('link-debugger: handlers attached count=' + anchors.length);
            })();
        """
        self.view.page().runJavaScript(js)

    def _perform_action(self, result) -> None:
        action = result.action
        payload = result.payload or {}
        if not action:
            return
        if self._nav_in_progress:
            try:
                self.logger.warning("NAV|skip|reentry_guard_active")
            except Exception:
                pass
            return
        self._nav_in_progress = True

        if action == "open_markdown_in_tree":
            path_str = payload.get("path")
            if path_str:
                new_path = Path(path_str)
                # 入栈当前文件，供 Back 使用
                try:
                    self._history_stack.append(str(self.current_file))
                    if self._history_max > 0 and len(self._history_stack) > self._history_max:
                        self._history_stack = self._history_stack[-self._history_max:]
                except Exception:
                    pass
                try:
                    self.logger.info(f"NAV|open_file|from={self.current_file}|to={new_path}")
                except Exception:
                    pass
                if not new_path.exists():
                    # Fallback 1: resolve against LAD_Project with original href
                    href = self._last_clicked_href or new_path.name
                    try:
                        href_path = Path(href)
                        candidate = (LAD_PROJECT_DIR / href_path.as_posix().lstrip("./")).resolve()
                        if candidate.exists():
                            new_path = candidate
                    except Exception:
                        pass
                if not new_path.exists():
                    # Fallback 2: trim duplicate segments and rebase under workspace root
                    parts = list(new_path.parts)
                    if "LAD_Project" in parts:
                        idx = len(parts) - 1 - parts[::-1].index("LAD_Project")
                        tail = Path(*parts[idx:])  # LAD_Project/...
                        candidate2 = WORKSPACE_ROOT / tail
                        if candidate2.exists():
                            new_path = candidate2
                if new_path.suffix.lower() == ".md":
                    self.current_file = new_path
                    self._load_markdown(new_path)
        elif action == "open_directory":
            # For debugging: navigate to README.md if exists; otherwise fallback to directory index page
            dir_path = Path(payload.get("path", ""))
            if not dir_path.exists():
                href = self._last_clicked_href
                try:
                    href_path = Path(href)
                    candidate = (LAD_PROJECT_DIR / href_path.as_posix().lstrip("./")).resolve()
                    if candidate.exists():
                        dir_path = candidate
                except Exception:
                    pass
            candidate = dir_path / "README.md"
            if candidate.exists():
                try:
                    self._history_stack.append(str(self.current_file))
                    if self._history_max > 0 and len(self._history_stack) > self._history_max:
                        self._history_stack = self._history_stack[-self._history_max:]
                    self.logger.info(f"NAV|open_file|from={self.current_file}|to={candidate}")
                except Exception:
                    pass
                self.current_file = candidate
                self._load_markdown(candidate)
            else:
                # Fallback: render a simple index of the directory entries, avoid fail.json
                try:
                    items = []
                    if dir_path.exists() and dir_path.is_dir():
                        for p in sorted(dir_path.iterdir()):
                            name = p.name
                            href = name + ("/" if p.is_dir() else "")
                            items.append(f"<li><a href='{href}'>{name}</a></li>")
                    html = (
                        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>目录索引</title></head><body>"
                        f"<h3>目录：{dir_path.as_posix()}</h3>"
                        "<p>未找到 README.md，已显示目录列表。</p>"
                        f"<ul>{''.join(items)}</ul>"
                        "</body></html>"
                    )
                    self.view.setHtml(html, baseUrl=QUrl.fromLocalFile(str(dir_path)))
                    self.logger.info("Fallback to directory index page (no README.md)")
                except Exception as ex:
                    self.logger.error(f"目录索引渲染失败: {ex}")
        elif action == "scroll_to_anchor":
            anchor_id = (payload or {}).get("id")
            if anchor_id:
                js = (
                    "(function(){var el=document.getElementById(" +
                    repr(anchor_id) +
                    "); if(el){ el.scrollIntoView(); }})();"
                )
                self.view.page().runJavaScript(js)
        # Other actions (external links, images, mermaid) are logged only
        self._nav_in_progress = False

    # 自定义右键菜单（Back/Forward/Reload），对齐 ContentViewer 的日志语义
    def _show_context_menu(self, pos):
        try:
            try:
                self.logger.warning("NAV|context_menu_opened")
            except Exception:
                pass
            menu = QMenu(self)
            act_back = QAction("Back", self)
            act_forward = QAction("Forward", self)
            act_reload = QAction("Reload", self)

            def _on_back():
                try:
                    if self._nav_in_progress:
                        try:
                            self.logger.warning("NAV|back_skip|reentry_guard_active")
                        except Exception:
                            pass
                        return
                    self._nav_in_progress = True
                    try:
                        self.logger.warning("NAV|back_menu_clicked")
                    except Exception:
                        pass
                    if self._history_stack:
                        prev = self._history_stack.pop()
                        try:
                            self.logger.warning(f"NAV|back_clicked|stack_size_after_pop={len(self._history_stack)}")
                            self.logger.warning(f"NAV|back|from={self.current_file}|to={prev}")
                        except Exception:
                            pass
                        self.current_file = Path(prev)
                        self._load_markdown(self.current_file)
                    else:
                        try:
                            self.logger.warning("NAV|back_clicked|stack_empty")
                        except Exception:
                            pass
                except Exception as e:
                    self.logger.warning(f"Back 操作失败: {e}")
                finally:
                    self._nav_in_progress = False

            def _on_forward():
                self.logger.info("Forward 暂未实现（按主应用统一管理）")

            def _on_reload():
                try:
                    self._load_markdown(self.current_file)
                except Exception as e:
                    self.logger.warning(f"Reload 失败: {e}")

            act_back.triggered.connect(_on_back)
            act_forward.triggered.connect(_on_forward)
            act_reload.triggered.connect(_on_reload)

            menu.addAction(act_back)
            menu.addAction(act_forward)
            menu.addSeparator()
            menu.addAction(act_reload)
            menu.exec_(self.view.mapToGlobal(pos))
        except Exception as e:
            self.logger.warning(f"显示自定义菜单失败: {e}")


def default_markdown_path() -> Path:
    # Resolve workspace root and locate LAD_Project/README.md reliably
    here = Path(__file__).resolve()
    # .../local_markdown_viewer/tests/tools/link_debug_readme.py
    # parents[4] -> workspace root (.. / .. / .. / ..)
    candidates = [
        here.parents[4] / "LAD_Project" / "README.md",  # D:/lad/LAD_Project/README.md
        here.parents[3] / "LAD_Project" / "README.md",  # Fallback if layout differs
        Path.cwd().parents[1] / "LAD_Project" / "README.md",  # When cwd is local_markdown_viewer
    ]
    for p in candidates:
        if p.exists():
            return p
    # Last resort: current cwd README.md
    return Path.cwd() / "README.md"


def main() -> int:
    logger = setup_logging()

    # High DPI attribute must be set before QApplication; keep minimal here
    app = QApplication(sys.argv)

    md_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_markdown_path()
    if not md_path.exists():
        logger.error(f"Markdown not found: {md_path}")
        return 2

    w = LinkDebugger(md_path, logger)
    w.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())

