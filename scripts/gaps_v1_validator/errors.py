"""Validator error types and aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    path: str
    message: str

    def format(self) -> str:
        return f"[{self.rule}] {self.path}: {self.message}"


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, rule: str, path: str, message: str) -> None:
        self.issues.append(ValidationIssue(rule=rule, path=path, message=message))

    def extend(self, others: Iterable[ValidationIssue]) -> None:
        self.issues.extend(others)

    @property
    def ok(self) -> bool:
        return not self.issues

    def render(self) -> str:
        return "\n".join(issue.format() for issue in self.issues)
