from __future__ import annotations

import os
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from .models import ScanResult, PageResult
from .dom_engine import DOMChecker
from .link_graph import LinkGraph
from .contrast import parse_simple_css


class SiteScanner:
    def __init__(
        self,
        root_dir: str,
        dom_checker: Optional[DOMChecker] = None,
        enabled_rules: Optional[List[str]] = None,
        disabled_rules: Optional[List[str]] = None,
        severity_overrides: Optional[Dict[str, Any]] = None,
    ):
        self.root_dir = os.path.abspath(root_dir)
        self.link_graph = LinkGraph(self.root_dir)
        self.dom_checker = dom_checker or DOMChecker(
            enabled_rules=enabled_rules,
            disabled_rules=disabled_rules,
            severity_overrides=severity_overrides,
        )
        self._css_cache: Dict[str, Dict[str, Dict[str, str]]] = {}

    def scan(self) -> ScanResult:
        self.link_graph.build_from_directory()

        html_files = self._find_html_files()
        self._build_link_graph(html_files)

        result = ScanResult(root_dir=self.root_dir, total_pages=len(html_files))

        for file_path in html_files:
            page_result = self._scan_page(file_path)
            result.pages.append(page_result)

        result.metadata = {
            "total_files_indexed": len(self.link_graph.all_files),
            "rules_used": [r.rule_id for r in self.dom_checker.rules if r.enabled],
        }

        return result

    def _find_html_files(self) -> List[str]:
        html_files = []
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            for filename in filenames:
                if filename.lower().endswith((".html", ".htm")):
                    full_path = os.path.join(dirpath, filename)
                    html_files.append(full_path)
        html_files.sort()
        return html_files

    def _build_link_graph(self, html_files: List[str]):
        for file_path in html_files:
            links, anchors = self._extract_links_and_anchors(file_path)
            self.link_graph.add_page(file_path, links, anchors)

    def _extract_links_and_anchors(self, file_path: str) -> tuple[List[str], List[str]]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")

        links = []
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if href and not href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:")):
                links.append(href)

        anchors = []
        for tag in soup.find_all(True):
            tag_id = tag.get("id")
            if tag_id:
                anchors.append(tag_id)
            if tag.name == "a":
                name = tag.get("name")
                if name:
                    anchors.append(name)

        return links, anchors

    def _scan_page(self, file_path: str) -> PageResult:
        context: Dict[str, Any] = {
            "link_graph": self.link_graph,
            "root_dir": self.root_dir,
        }

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")

        page_anchors = []
        for tag in soup.find_all(True):
            tag_id = tag.get("id")
            if tag_id:
                page_anchors.append(tag_id)
            if tag.name == "a":
                name = tag.get("name")
                if name:
                    page_anchors.append(name)
        context["page_anchors"] = page_anchors

        css_styles = self._load_css_styles(soup, file_path)
        if css_styles:
            context["css_styles"] = css_styles

        return self.dom_checker.check_html(html, file_path, context)

    def _load_css_styles(self, soup: BeautifulSoup, file_path: str) -> Dict[str, Dict[str, str]]:
        styles: Dict[str, Dict[str, str]] = {}

        for style_tag in soup.find_all("style"):
            css_text = style_tag.get_text()
            if css_text.strip():
                parsed = parse_simple_css(css_text)
                for sel, props in parsed.items():
                    if sel in styles:
                        styles[sel].update(props)
                    else:
                        styles[sel] = dict(props)

        for link_tag in soup.find_all("link", rel="stylesheet"):
            href = link_tag.get("href", "")
            if not href or href.startswith(("http://", "https://")):
                continue

            file_dir = os.path.dirname(file_path)
            css_path = os.path.join(file_dir, href)
            css_path = os.path.normpath(css_path)

            if not os.path.isfile(css_path):
                continue

            cache_key = os.path.abspath(css_path)
            if cache_key in self._css_cache:
                parsed = self._css_cache[cache_key]
            else:
                try:
                    with open(css_path, "r", encoding="utf-8", errors="replace") as f:
                        css_text = f.read()
                    parsed = parse_simple_css(css_text)
                    self._css_cache[cache_key] = parsed
                except Exception:
                    continue

            for sel, props in parsed.items():
                if sel in styles:
                    styles[sel].update(props)
                else:
                    styles[sel] = dict(props)

        return styles
