from __future__ import annotations

from typing import List, Dict, Any, Set
from bs4 import BeautifulSoup, Tag

from .base import Rule
from ..models import Severity


_FORM_INPUTS = {"input", "select", "textarea", "button"}


class FormLabelRule(Rule):
    rule_id = "form-label"
    rule_name = "表单控件没有关联的label"
    description = "检查表单控件是否有关联的label"
    default_severity = Severity.ERROR
    default_enabled = True

    def check(self, soup: BeautifulSoup, file_path: str, context: Dict[str, Any] = None) -> List:
        issues = []
        label_for_ids: Set[str] = set()
        for label in soup.find_all("label"):
            if isinstance(label, Tag):
                for_id = label.get("for")
                if for_id:
                    label_for_ids.add(for_id)

        labeled_input_ids: Set[str] = set()

        for input_tag in soup.find_all(_FORM_INPUTS):
            if not isinstance(input_tag, Tag):
                continue

            input_type = input_tag.get("type", "")
            if input_type in {"hidden", "submit", "reset", "button", "image"}:
                continue

            input_id = input_tag.get("id", "")

            if input_id and input_id in label_for_ids:
                labeled_input_ids.add(input_id)
                continue

            if self._has_aria_label(input_tag):
                continue

            parent_label = input_tag.find_parent("label")
            if parent_label is not None:
                continue

            issues.append(self._make_issue(
                f"表单控件 <{input_tag.name}> 没有关联的label",
                file_path,
                element=input_tag,
                input_type=input_type,
                input_name=input_tag.get("name", ""),
            ))

        return issues

    def _has_aria_label(self, tag: Tag) -> bool:
        if tag.get("aria-label"):
            return True
        if tag.get("aria-labelledby"):
            return True
        if tag.get("title"):
            return True
        return False
