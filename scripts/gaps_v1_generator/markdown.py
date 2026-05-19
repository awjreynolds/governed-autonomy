"""Small Markdown rendering helpers."""

from __future__ import annotations

from typing import Iterable


def table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return ""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(cells: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)) + " |"

    separator = "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    return "\n".join([fmt_row(headers), separator, *[fmt_row(row) for row in rows]])


def bullet_list(items: Iterable[str], indent: int = 0) -> str:
    prefix = " " * indent + "- "
    return "\n".join(prefix + item for item in items)
