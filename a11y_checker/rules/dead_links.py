from __future__ import annotations

from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag

from .base import Rule
from ..models import Severity
from ..link_graph import LinkGraph


class DeadLinkRule(Rule):
    rule_id = "dead-link"
    rule_name = "站内死链"
    description = "检查站内链接和页内锚点是否有效"
    default_severity = Severity.ERROR
    default_enabled = True

    def check(self, soup: BeautifulSoup, file_path: str, context: Dict[str, Any] = None) -> List:
        issues = []
        context = context or {}
        link_graph: LinkGraph = context.get("link_graph")
        page_anchors: List[str] = context.get("page_anchors", [])

        for a in soup.find_all("a"):
            if not isinstance(a, Tag):
                continue
            href = a.get("href", "")
            if not href:
                continue

            if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:")):
                continue

            if href.startswith("#"):
                anchor = href[1:]
                if anchor and anchor not in page_anchors:
                    issues.append(self._make_issue(
                        f"页内锚点 '{href}' 目标不存在",
                        file_path,
                        element=a,
                        href=href,
                        link_type="anchor",
                    ))
            elif link_graph is not None:
                is_dead, reason = link_graph.check_link(file_path, href)
                if is_dead:
                    issues.append(self._make_issue(
                        f"站内链接失效: {href} ({reason})",
                        file_path,
                        element=a,
                        href=href,
                        reason=reason,
                        link_type="internal",
                    ))

        return issues
