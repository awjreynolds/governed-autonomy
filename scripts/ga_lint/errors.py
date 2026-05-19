"""Lint issue types and aggregation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable, Literal


Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    path: str
    message: str
    severity: Severity = "error"

    def format(self) -> str:
        return f"{self.path}: {self.rule} {self.severity}: {self.message}"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, rule: str, path: str, message: str, severity: Severity = "error") -> None:
        self.issues.append(ValidationIssue(rule=rule, path=path, message=message, severity=severity))

    def extend(self, others: Iterable[ValidationIssue]) -> None:
        self.issues.extend(others)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def render(self) -> str:
        return "\n".join(issue.format() for issue in self.issues)

