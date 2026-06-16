from __future__ import annotations

from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag

from .base import Rule
from ..models import Severity


class HtmlLangRule(Rule):
    rule_id = "html-lang"
    rule_name = "页面没声明lang"
    description = "检查<html>标签是否声明了lang属性"
    default_severity = Severity.ERROR
    default_enabled = True

    def check(self, soup: BeautifulSoup, file_path: str, context: Dict[str, Any] = None) -> List:
        issues = []
        html_tag = soup.find("html")
        if html_tag is None or not isinstance(html_tag, Tag):
            issues.append(self._make_issue(
                "页面缺少 <html> 标签",
                file_path,
            ))
            return issues

        lang = html_tag.get("lang")
        if not lang:
            issues.append(self._make_issue(
                "<html> 标签缺少 lang 属性，应声明页面语言",
                file_path,
                element=html_tag,
            ))
        elif len(lang.strip()) < 2:
            issues.append(self._make_issue(
                f"lang 属性值 '{lang}' 不规范，应使用有效的语言代码",
                file_path,
                element=html_tag,
                lang_value=lang,
            ))

        return issues
