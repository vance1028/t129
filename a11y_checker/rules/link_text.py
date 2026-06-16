from __future__ import annotations

from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag

from .base import Rule
from ..models import Severity


_VAGUE_LINK_TEXTS = {
    "点击这里",
    "点击此处",
    "这里",
    "此处",
    "更多",
    "了解更多",
    "read more",
    "click here",
    "here",
    "more",
    "learn more",
    "link",
    "链接",
}


class LinkTextRule(Rule):
    rule_id = "link-text"
    rule_name = "链接文字含糊不达意"
    description = "检查链接文字是否清晰描述链接目标"
    default_severity = Severity.WARNING
    default_enabled = True

    def check(self, soup: BeautifulSoup, file_path: str, context: Dict[str, Any] = None) -> List:
        issues = []
        for a in soup.find_all("a"):
            if not isinstance(a, Tag):
                continue
            href = a.get("href", "")
            if not href or href.startswith("#"):
                continue

            text = a.get_text(strip=True)
            text_lower = text.lower().strip()

            if not text_lower:
                img = a.find("img")
                if img and img.get("alt"):
                    alt_text = img.get("alt", "").strip()
                    if alt_text:
                        continue
                issues.append(self._make_issue(
                    "链接没有可访问的文本内容",
                    file_path,
                    element=a,
                    href=href,
                ))
                continue

            if text_lower in _VAGUE_LINK_TEXTS:
                issues.append(self._make_issue(
                    f"链接文字 '{text}' 含糊不清，不能清楚表达链接目标",
                    file_path,
                    element=a,
                    href=href,
                    link_text=text,
                ))

        return issues
