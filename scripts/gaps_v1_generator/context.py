"""Load a spec and its catalogs into a structured context for generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gaps_v1_validator.loader import load_yaml, resolve_catalog_path  # noqa: E402


@dataclass
class GeneratorContext:
    spec: dict[str, Any]
    spec_path: Path
    actions_by_id: dict[str, dict[str, Any]]
    evidence_kinds_by_id: dict[str, dict[str, Any]]
    risk_patterns_by_id: dict[str, dict[str, Any]]
    case_file_items_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    gates_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    roles_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def process_id(self) -> str:
        return self.spec["process"]["id"]

    @property
    def process_name(self) -> str:
        return self.spec["process"]["name"]


def build_context(spec_path: Path) -> GeneratorContext:
    spec = load_yaml(spec_path)
    substrate = spec.get("substrate", {}) or {}

    actions = load_yaml(resolve_catalog_path(spec_path, substrate["actionCatalog"])).get("actions", [])
    evidence = load_yaml(resolve_catalog_path(spec_path, substrate["evidenceCatalog"])).get("evidenceKinds", [])
    risk = load_yaml(resolve_catalog_path(spec_path, substrate["riskPatternCatalog"])).get("riskPatterns", [])

    actions_by_id = {entry["id"]: entry for entry in actions}
    for local in spec.get("process", {}).get("localActions", []) or []:
        actions_by_id.setdefault(local["id"], local)

    return GeneratorContext(
        spec=spec,
        spec_path=spec_path,
        actions_by_id=actions_by_id,
        evidence_kinds_by_id={entry["id"]: entry for entry in evidence},
        risk_patterns_by_id={entry["id"]: entry for entry in risk},
        case_file_items_by_id={item["id"]: item for item in spec.get("evidenceModel", {}).get("caseFileItems", []) or []},
        gates_by_id={gate["id"]: gate for gate in spec.get("gates", []) or []},
        roles_by_id={role["id"]: role for role in spec.get("roles", []) or []},
    )
