from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        value = value.lower()
        for s in cls:
            if s.value == value:
                return s
        raise ValueError(f"Unknown severity: {value}")


@dataclass
class Issue:
    rule_id: str
    rule_name: str
    severity: Severity
    message: str
    file_path: str
    line: int = 0
    column: int = 0
    element: str = ""
    snippet: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Issue":
        d = dict(d)
        d["severity"] = Severity.from_string(d["severity"])
        return cls(**d)


@dataclass
class PageResult:
    file_path: str
    issues: List[Issue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.INFO)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class ScanResult:
    root_dir: str
    total_pages: int = 0
    pages: List[PageResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_errors(self) -> int:
        return sum(p.error_count for p in self.pages)

    @property
    def total_warnings(self) -> int:
        return sum(p.warning_count for p in self.pages)

    @property
    def total_info(self) -> int:
        return sum(p.info_count for p in self.pages)

    @property
    def all_issues(self) -> List[Issue]:
        issues = []
        for p in self.pages:
            issues.extend(p.issues)
        return issues

    def issues_by_rule(self) -> Dict[str, List[Issue]]:
        result: Dict[str, List[Issue]] = {}
        for issue in self.all_issues:
            result.setdefault(issue.rule_id, []).append(issue)
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_dir": self.root_dir,
            "total_pages": self.total_pages,
            "total_errors": self.total_errors,
            "total_warnings": self.total_warnings,
            "total_info": self.total_info,
            "pages": [p.to_dict() for p in self.pages],
            "metadata": self.metadata,
        }
