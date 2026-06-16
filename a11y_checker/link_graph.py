from __future__ import annotations

import os
import posixpath
from typing import Dict, List, Tuple, Set, Optional
from urllib.parse import urlparse, unquote


class LinkGraph:
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self._pages: Dict[str, List[str]] = {}
        self._page_anchors: Dict[str, Set[str]] = {}
        self._all_files: Set[str] = set()
        self._built = False

    def add_page(self, file_path: str, links: List[str], anchors: List[str] = None):
        abs_path = os.path.abspath(file_path)
        rel_path = os.path.relpath(abs_path, self.root_dir).replace("\\", "/")
        self._pages[rel_path] = links
        self._page_anchors[rel_path] = set(anchors or [])
        self._all_files.add(rel_path)

    def add_file(self, file_path: str):
        abs_path = os.path.abspath(file_path)
        if os.path.isfile(abs_path):
            rel_path = os.path.relpath(abs_path, self.root_dir).replace("\\", "/")
            self._all_files.add(rel_path)

    def build_from_directory(self):
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                self.add_file(full_path)
        self._built = True

    def _resolve_path(self, base_path: str, target: str) -> Optional[str]:
        if not target:
            return None

        if target.startswith(("http://", "https://", "mailto:", "tel:", "javascript:", "#")):
            return None

        parsed = urlparse(target)
        if parsed.scheme or parsed.netloc:
            return None

        path = unquote(parsed.path)
        if not path:
            return None

        base_dir = os.path.dirname(base_path) if base_path else ""

        if path.startswith("/"):
            rel_path = path.lstrip("/")
        else:
            joined = posixpath.join(base_dir, path)
            rel_path = posixpath.normpath(joined)

        if rel_path in self._all_files:
            return rel_path

        index_files = [
            posixpath.join(rel_path, "index.html"),
            posixpath.join(rel_path, "index.htm"),
        ]
        for idx in index_files:
            if idx in self._all_files:
                return idx

        if not rel_path.endswith((".html", ".htm")):
            for ext in (".html", ".htm"):
                if rel_path + ext in self._all_files:
                    return rel_path + ext

        return None

    def check_link(self, page_path: str, href: str) -> Tuple[bool, str]:
        abs_page = os.path.abspath(page_path)
        rel_page = os.path.relpath(abs_page, self.root_dir).replace("\\", "/")

        parsed = urlparse(href)
        fragment = parsed.fragment

        if href.startswith("#"):
            anchor = href[1:]
            page_anchors = self._page_anchors.get(rel_page, set())
            if anchor and anchor not in page_anchors:
                return True, f"页内锚点不存在: #{anchor}"
            return False, ""

        if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:")):
            return False, "外部链接，不检查"

        target_path = self._resolve_path(rel_page, href)
        if target_path is None:
            cleaned_path = parsed.path
            return True, f"目标文件不存在: {cleaned_path}"

        if fragment:
            target_anchors = self._page_anchors.get(target_path, set())
            if fragment not in target_anchors:
                return True, f"目标文件存在但锚点不存在: #{fragment}"

        return False, ""

    def get_dead_links(self) -> List[Tuple[str, str, str]]:
        dead = []
        for page_path, links in self._pages.items():
            for link in links:
                is_dead, reason = self.check_link(page_path, link)
                if is_dead:
                    dead.append((page_path, link, reason))
        return dead

    @property
    def all_files(self) -> Set[str]:
        return self._all_files.copy()

    @property
    def pages(self) -> Dict[str, List[str]]:
        return dict(self._pages)

    def get_page_anchors(self, page_path: str) -> Set[str]:
        abs_page = os.path.abspath(page_path)
        rel_page = os.path.relpath(abs_page, self.root_dir).replace("\\", "/")
        return self._page_anchors.get(rel_page, set()).copy()
