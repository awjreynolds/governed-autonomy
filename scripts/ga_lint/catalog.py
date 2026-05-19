"""Catalog loading helpers for ga-lint."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .loader import load_yaml


ACTION_CATEGORIES = {
    "data-plane-read",
    "data-plane-draft",
    "data-plane-persist",
    "data-plane-external",
    "control-plane",
    "meta",
    "prohibited-anti-pattern",
}


@dataclass(frozen=True)
class CatalogIndex:
    ids: set[str]
    action_categories: dict[str, str]

    def exists(self, ref: str) -> bool:
        return ref in self.ids

    def action_category(self, ref: str) -> str | None:
        return self.action_categories.get(ref)


def load_catalogs(repo_root: Path) -> CatalogIndex:
    catalog_root = repo_root / "gaps" / "catalogs" / "v1"
    ids: set[str] = set()
    action_categories: dict[str, str] = {}

    actions_doc = load_yaml(catalog_root / "actions.yml")
    for action in actions_doc.get("actions", []):
        ref = f"catalog:action:{action['id']}"
        ids.add(ref)
        action_categories[ref] = action.get("category", "")

    evidence_doc = load_yaml(catalog_root / "evidence-kinds.yml")
    for item in evidence_doc.get("evidenceKinds", []):
        ids.add(f"catalog:evidence:{item['id']}")

    risk_doc = load_yaml(catalog_root / "risk-patterns.yml")
    for item in risk_doc.get("riskPatterns", []):
        ids.add(f"catalog:risk:{item['id']}")

    return CatalogIndex(ids=ids, action_categories=action_categories)

