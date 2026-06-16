from __future__ import annotations

from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag

from .base import Rule
from ..models import Severity


class ImageAltRule(Rule):
    rule_id = "image-alt"
    rule_name = "图片缺少alt文本"
    description = "检查所有img标签是否有alt属性"
    default_severity = Severity.ERROR
    default_enabled = True

    def check(self, soup: BeautifulSoup, file_path: str, context: Dict[str, Any] = None) -> List:
        issues = []
        for img in soup.find_all("img"):
            if not isinstance(img, Tag):
                continue
            alt = img.get("alt")
            if alt is None:
                issues.append(self._make_issue(
                    "图片缺少alt属性",
                    file_path,
                    element=img,
                    src=img.get("src", ""),
                ))
            elif alt.strip() == "" and not self._is_decorative(img):
                issues.append(self._make_issue(
                    "图片alt属性为空，且未标记为装饰性",
                    file_path,
                    element=img,
                    src=img.get("src", ""),
                ))
        return issues

    def _is_decorative(self, img: Tag) -> bool:
        role = img.get("role", "")
        return role == "presentation" or role == "none"
