from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Type, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag

from ..models import Issue, Severity


class Rule(ABC):
    rule_id: str = ""
    rule_name: str = ""
    description: str = ""
    default_severity: Severity = Severity.WARNING
    default_enabled: bool = True

    def __init__(self, severity: Optional[Severity] = None, enabled: Optional[bool] = None):
        self.severity = severity if severity is not None else self.default_severity
        self.enabled = enabled if enabled is not None else self.default_enabled

    @abstractmethod
    def check(self, soup: BeautifulSoup, file_path: str, context: Dict[str, Any] = None) -> List[Issue]:
        pass

    def _make_issue(
        self,
        message: str,
        file_path: str,
        element: Optional[Tag] = None,
        **context_kwargs: Any,
    ) -> Issue:
        line = 0
        col = 0
        snippet = ""
        elem_str = ""
        if element is not None:
            if hasattr(element, "sourceline") and element.sourceline is not None:
                line = element.sourceline
            if hasattr(element, "sourcepos") and element.sourcepos is not None:
                col = element.sourcepos
            try:
                snippet = str(element)[:200]
            except Exception:
                snippet = ""
            elem_str = element.name
            if element.get("id"):
                elem_str += f"#{element['id']}"
            classes = element.get("class", [])
            if classes:
                elem_str += "." + ".".join(classes)

        context = context_kwargs
        return Issue(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            severity=self.severity,
            message=message,
            file_path=file_path,
            line=line,
            column=col,
            element=elem_str,
            snippet=snippet,
            context=context,
        )


class RuleRegistry:
    def __init__(self):
        self._rules: Dict[str, Type[Rule]] = {}

    def register(self, rule_class: Type[Rule]) -> None:
        if not rule_class.rule_id:
            raise ValueError(f"Rule {rule_class.__name__} has no rule_id")
        self._rules[rule_class.rule_id] = rule_class

    def unregister(self, rule_id: str) -> None:
        self._rules.pop(rule_id, None)

    def get(self, rule_id: str) -> Optional[Type[Rule]]:
        return self._rules.get(rule_id)

    def list_rules(self) -> List[str]:
        return list(self._rules.keys())

    def create_instances(
        self,
        enabled_rules: Optional[List[str]] = None,
        disabled_rules: Optional[List[str]] = None,
        severity_overrides: Optional[Dict[str, Severity]] = None,
    ) -> List[Rule]:
        instances = []
        severity_overrides = severity_overrides or {}
        for rule_id, rule_cls in self._rules.items():
            enabled = rule_cls.default_enabled
            if enabled_rules is not None:
                enabled = rule_id in enabled_rules
            if disabled_rules is not None and rule_id in disabled_rules:
                enabled = False
            severity = severity_overrides.get(rule_id, rule_cls.default_severity)
            instances.append(rule_cls(severity=severity, enabled=enabled))
        return instances

    def get_rule_info(self) -> List[Dict[str, Any]]:
        info = []
        for rule_id, rule_cls in sorted(self._rules.items()):
            info.append({
                "rule_id": rule_id,
                "rule_name": rule_cls.rule_name,
                "description": rule_cls.description,
                "default_severity": rule_cls.default_severity.value,
                "default_enabled": rule_cls.default_enabled,
            })
        return info


def create_default_registry() -> RuleRegistry:
    from . import DEFAULT_RULES
    registry = RuleRegistry()
    for rule_cls in DEFAULT_RULES:
        registry.register(rule_cls)
    return registry
