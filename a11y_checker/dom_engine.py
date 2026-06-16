from __future__ import annotations

import os
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from .models import Issue, PageResult, ScanResult
from .rules.base import Rule, RuleRegistry, create_default_registry
from .link_graph import LinkGraph
from .contrast import parse_simple_css


class DOMChecker:
    def __init__(
        self,
        rules: Optional[List[Rule]] = None,
        registry: Optional[RuleRegistry] = None,
        enabled_rules: Optional[List[str]] = None,
        disabled_rules: Optional[List[str]] = None,
        severity_overrides: Optional[Dict[str, Any]] = None,
    ):
        if rules is not None:
            self.rules = rules
        else:
            if registry is None:
                registry = create_default_registry()
            self.rules = registry.create_instances(
                enabled_rules=enabled_rules,
                disabled_rules=disabled_rules,
                severity_overrides=severity_overrides,
            )

    def check_file(self, file_path: str, context: Dict[str, Any] = None) -> PageResult:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()
        return self.check_html(html, file_path, context)

    def check_html(
        self,
        html: str,
        file_path: str = "",
        context: Dict[str, Any] = None,
    ) -> PageResult:
        soup = BeautifulSoup(html, "html.parser")
        issues: List[Issue] = []
        context = context or {}

        if "page_anchors" not in context:
            context["page_anchors"] = self._extract_anchors(soup)

        for rule in self.rules:
            if not rule.enabled:
                continue
            try:
                rule_issues = rule.check(soup, file_path, context)
                issues.extend(rule_issues)
            except Exception as e:
                issues.append(Issue(
                    rule_id="internal-error",
                    rule_name="规则执行错误",
                    severity="error",
                    message=f"规则 {rule.rule_id} 执行失败: {e}",
                    file_path=file_path,
                ))

        return PageResult(file_path=file_path, issues=issues)

    def _extract_anchors(self, soup: BeautifulSoup) -> List[str]:
        anchors = []
        for tag in soup.find_all(True):
            tag_id = tag.get("id")
            if tag_id:
                anchors.append(tag_id)
            if tag.name == "a":
                name = tag.get("name")
                if name:
                    anchors.append(name)
        return anchors

    def get_rule_info(self) -> List[Dict[str, Any]]:
        info = []
        for rule in sorted(self.rules, key=lambda r: r.rule_id):
            info.append({
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "description": rule.description,
                "severity": rule.severity.value,
                "enabled": rule.enabled,
            })
        return info
