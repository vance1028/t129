from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup, Tag

from .base import Rule
from ..models import Severity
from ..contrast import parse_color, contrast_ratio, meets_aa, get_text_colors, parse_simple_css


_TEXT_ELEMENTS = {"p", "span", "div", "li", "td", "th", "a", "button", "label", "h1", "h2", "h3", "h4", "h5", "h6", "strong", "em"}

_LARGE_TEXT_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

_DEFAULT_BG = (255, 255, 255, 1.0)


class ColorContrastRule(Rule):
    rule_id = "color-contrast"
    rule_name = "文字和背景颜色对比度不足"
    description = "检查文本的前景色和背景色对比度是否达到WCAG AA级标准"
    default_severity = Severity.ERROR
    default_enabled = True

    def check(self, soup: BeautifulSoup, file_path: str, context: Dict[str, Any] = None) -> List:
        issues = []
        context = context or {}
        css_styles = context.get("css_styles")
        if css_styles is None:
            style_tags = soup.find_all("style")
            css_text = ""
            for style in style_tags:
                css_text += style.get_text() + "\n"
            if css_text.strip():
                css_styles = parse_simple_css(css_text)
                context["css_styles"] = css_styles

        body_bg = self._get_body_bg(soup, css_styles)
        checked_elements = set()
        self._check_children(soup, css_styles, body_bg, file_path, issues, checked_elements)
        return issues

    def _get_body_bg(self, soup: BeautifulSoup, css_styles: Optional[Dict]) -> Tuple[int, int, int, float]:
        body = soup.find("body")
        if body and isinstance(body, Tag):
            _, bg_color = get_text_colors(body, css_styles)
            if bg_color:
                parsed = parse_color(bg_color)
                if parsed:
                    return parsed
        return _DEFAULT_BG

    def _check_children(
        self,
        parent,
        css_styles,
        parent_bg: Tuple[int, int, int, float],
        file_path: str,
        issues: List,
        checked: set,
    ):
        for child in parent.children:
            if not isinstance(child, Tag):
                continue
            if id(child) in checked:
                continue
            checked.add(id(child))

            tag_name = child.name.lower() if child.name else ""

            if tag_name in _TEXT_ELEMENTS:
                text = child.get_text(strip=True)
                if not text or len(text) < 2:
                    self._check_children(child, css_styles, parent_bg, file_path, issues, checked)
                    continue

                fg_str, bg_str = get_text_colors(child, css_styles)
                current_bg = parent_bg
                if bg_str:
                    parsed_bg = parse_color(bg_str)
                    if parsed_bg:
                        current_bg = parsed_bg

                if not fg_str:
                    self._check_children(child, css_styles, current_bg, file_path, issues, checked)
                    continue

                fg_color = parse_color(fg_str)
                if not fg_color:
                    self._check_children(child, css_styles, current_bg, file_path, issues, checked)
                    continue

                ratio = contrast_ratio(fg_color, current_bg, current_bg)
                is_large = tag_name in _LARGE_TEXT_TAGS

                if not meets_aa(ratio, is_large_text=is_large):
                    threshold = 3.0 if is_large else 4.5
                    issues.append(self._make_issue(
                        f"文本颜色对比度不足 (当前 {ratio:.2f}:1，AA标准 {threshold}:1)",
                        file_path,
                        element=child,
                        contrast_ratio=round(ratio, 2),
                        threshold=threshold,
                        fg_color=fg_str,
                        bg_color=bg_str or "white",
                        is_large_text=is_large,
                        text_preview=text[:50],
                    ))

                self._check_children(child, css_styles, current_bg, file_path, issues, checked)
            else:
                _, bg_str = get_text_colors(child, css_styles)
                current_bg = parent_bg
                if bg_str:
                    parsed_bg = parse_color(bg_str)
                    if parsed_bg:
                        current_bg = parsed_bg
                self._check_children(child, css_styles, current_bg, file_path, issues, checked)
