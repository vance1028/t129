from __future__ import annotations

from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag

from .base import Rule
from ..models import Severity


class HeadingOrderRule(Rule):
    rule_id = "heading-order"
    rule_name = "标题层级乱跳"
    description = "检查标题层级是否按顺序递增，不能跳级"
    default_severity = Severity.WARNING
    default_enabled = True

    def check(self, soup: BeautifulSoup, file_path: str, context: Dict[str, Any] = None) -> List:
        issues = []
        headings: List[Tag] = []
        for i in range(1, 7):
            for h in soup.find_all(f"h{i}"):
                if isinstance(h, Tag):
                    headings.append(h)

        headings.sort(key=lambda x: (x.sourceline or 0, x.sourcepos or 0))

        prev_level = 0
        for heading in headings:
            level = int(heading.name[1])
            if prev_level > 0 and level > prev_level + 1:
                issues.append(self._make_issue(
                    f"标题层级从 h{prev_level} 跳到 h{level}，应该按顺序递增",
                    file_path,
                    element=heading,
                    current_level=level,
                    previous_level=prev_level,
                    heading_text=heading.get_text(strip=True)[:50],
                ))
            prev_level = level

        if not headings:
            issues.append(self._make_issue(
                "页面没有任何标题（h1-h6），建议添加页面主标题",
                file_path,
            ))
        elif headings and int(headings[0].name[1]) != 1:
            first_h = headings[0]
            issues.append(self._make_issue(
                f"页面第一个标题是 {first_h.name}，应该以 h1 开始",
                file_path,
                element=first_h,
                heading_text=first_h.get_text(strip=True)[:50],
            ))

        return issues
