from __future__ import annotations

from typing import List, Dict, Any, Set
from bs4 import BeautifulSoup, Tag

from .base import Rule
from ..models import Severity


_VALID_ARIA_ROLES = {
    "alert", "alertdialog", "application", "article", "banner", "button",
    "cell", "checkbox", "columnheader", "combobox", "complementary", "contentinfo",
    "definition", "dialog", "directory", "document", "feed", "figure", "form",
    "grid", "gridcell", "group", "heading", "img", "link", "list", "listbox",
    "listitem", "log", "main", "marquee", "math", "menu", "menubar", "menuitem",
    "menuitemcheckbox", "menuitemradio", "navigation", "none", "note", "option",
    "presentation", "progressbar", "radio", "radiogroup", "region", "row",
    "rowgroup", "rowheader", "scrollbar", "search", "searchbox", "separator",
    "slider", "spinbutton", "status", "switch", "tab", "table", "tablist",
    "tabpanel", "term", "textbox", "timer", "toolbar", "tooltip", "tree",
    "treegrid", "treeitem",
}


_REDUNDANT_ROLE_MAP: Dict[str, Set[str]] = {
    "a": {"link"},
    "button": {"button"},
    "h1": {"heading"},
    "h2": {"heading"},
    "h3": {"heading"},
    "h4": {"heading"},
    "h5": {"heading"},
    "h6": {"heading"},
    "img": {"img"},
    "input": {"checkbox", "radio", "textbox"},
    "li": {"listitem"},
    "ol": {"list"},
    "ul": {"list"},
    "p": {},
    "table": {"table"},
    "td": {"cell"},
    "th": {"columnheader", "rowheader"},
    "textarea": {"textbox"},
    "nav": {"navigation"},
    "main": {"main"},
    "header": {"banner"},
    "footer": {"contentinfo"},
    "aside": {"complementary"},
    "article": {"article"},
    "section": {"region"},
}


class AriaRule(Rule):
    rule_id = "aria"
    rule_name = "ARIA属性用错或冗余"
    description = "检查ARIA role和属性的使用是否正确"
    default_severity = Severity.WARNING
    default_enabled = True

    def check(self, soup: BeautifulSoup, file_path: str, context: Dict[str, Any] = None) -> List:
        issues = []
        for tag in soup.find_all(True):
            if not isinstance(tag, Tag):
                continue

            role = tag.get("role")
            if role:
                self._check_role(tag, role, file_path, issues)

            self._check_aria_attributes(tag, file_path, issues)

        return issues

    def _check_role(self, tag: Tag, role: str, file_path: str, issues: List):
        if role not in _VALID_ARIA_ROLES:
            issues.append(self._make_issue(
                f"未知的ARIA role: '{role}'",
                file_path,
                element=tag,
                role=role,
            ))
            return

        tag_name = tag.name.lower() if tag.name else ""
        redundant_roles = _REDUNDANT_ROLE_MAP.get(tag_name, set())
        if role in redundant_roles:
            issues.append(self._make_issue(
                f"冗余的ARIA role: <{tag_name}> 自带 '{role}' 语义，不需要显式声明",
                file_path,
                element=tag,
                role=role,
                tag_name=tag_name,
            ))

    def _check_aria_attributes(self, tag: Tag, file_path: str, issues: List):
        for attr in tag.attrs:
            if not attr.startswith("aria-"):
                continue

            attr_name = attr.lower()

            if not self._is_valid_aria_attr(attr_name):
                issues.append(self._make_issue(
                    f"未知的ARIA属性: '{attr_name}'",
                    file_path,
                    element=tag,
                    attribute=attr_name,
                ))

            if attr_name == "aria-hidden" and tag.get("aria-hidden") == "true":
                if tag.find_parent(attrs={"aria-hidden": "true"}):
                    continue
                interactive = tag.find_all(["a", "button", "input", "select", "textarea"])
                if interactive:
                    issues.append(self._make_issue(
                        "aria-hidden='true' 的元素内包含可交互元素，会导致可访问性问题",
                        file_path,
                        element=tag,
                        attribute=attr_name,
                    ))

    def _is_valid_aria_attr(self, attr_name: str) -> bool:
        valid_attrs = {
            "aria-activedescendant", "aria-atomic", "aria-autocomplete", "aria-busy",
            "aria-checked", "aria-colcount", "aria-colindex", "aria-colspan",
            "aria-controls", "aria-current", "aria-describedby", "aria-details",
            "aria-disabled", "aria-dropeffect", "aria-errormessage", "aria-expanded",
            "aria-flowto", "aria-grabbed", "aria-haspopup", "aria-hidden",
            "aria-invalid", "aria-keyshortcuts", "aria-label", "aria-labelledby",
            "aria-level", "aria-live", "aria-modal", "aria-multiline", "aria-multiselectable",
            "aria-orientation", "aria-owns", "aria-placeholder", "aria-posinset",
            "aria-pressed", "aria-readonly", "aria-relevant", "aria-required",
            "aria-roledescription", "aria-rowcount", "aria-rowindex", "aria-rowspan",
            "aria-selected", "aria-setsize", "aria-sort", "aria-valuemax",
            "aria-valuemin", "aria-valuenow", "aria-valuetext",
        }
        return attr_name in valid_attrs
