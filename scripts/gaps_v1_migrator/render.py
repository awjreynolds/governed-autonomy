"""Hand-rolled YAML renderer for v1 spec documents.

Stable output: keys emitted in a fixed canonical order at every level;
strings quoted only when necessary; long strings folded.
"""

from __future__ import annotations

import re
from typing import Any


CANONICAL_KEY_ORDER = [
    "gapsVersion", "specStatus", "conformanceLevel",
    "process", "substrate", "roles", "evidenceModel",
    "lanes", "gates", "controlPlaneActions", "projectionPolicy",
    "riskPatterns", "controlAssessment", "freshness", "knownGaps",
    "id", "name", "label", "purpose", "scope", "includes", "excludes",
    "localActions", "category", "defaultAutonomyTier", "defaultRiskTier",
    "definition", "justification", "examples", "roleAffinity",
    "alwaysProhibitedAt",
    "oscalControlCatalogs", "oscalProfile",
    "actionCatalog", "evidenceCatalog", "riskPatternCatalog",
    "accountabilityScope", "decisionRights", "canApprove",
    "caseFileItems", "kind", "shape", "required", "optional",
    "producer", "consumer", "retentionPolicy",
    "authority", "plane", "autonomyTier", "riskTier", "allowedActions", "prohibitedActions",
    "stateModel", "states", "transitions",
    "isInitial", "isTerminal", "from", "to", "gate", "guard",
    "inputs", "rules", "when", "then", "effect", "transitionTo", "recordEvidence", "else",
    "evidenceInputs", "evidenceOutputs", "autonomousResponsibilities", "skills",
    "gateType", "approvalRole", "approvalCondition", "escalationCondition", "decision",
    "skill", "actions",
    "canonicalStateSource", "pathPattern", "externalSystems",
    "role", "mutationRequiresApproval",
    "patternRef", "mitigations", "evidenceRefs",
    "catalogRefs", "controlImplementations",
    "controlId", "mappingStatus", "implementedBy", "evidence", "statement",
    "reviewedAt", "implementationFingerprint", "algorithm", "value", "driftPolicy",
    "summary", "severity", "plannedResolution",
]

_KEY_INDEX = {key: index for index, key in enumerate(CANONICAL_KEY_ORDER)}


def _key_sort(key: str) -> tuple[int, str]:
    return (_KEY_INDEX.get(key, len(CANONICAL_KEY_ORDER)), key)


_PLAIN_SAFE = re.compile(r"^[A-Za-z_][A-Za-z0-9_./:\-]*$")
_VERSION_SAFE = re.compile(r"^[0-9]+(?:\.[0-9]+)+$")


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return str(value)
    if not isinstance(value, str):
        raise TypeError(f"unsupported scalar {value!r}")
    if value == "":
        return "\"\""
    if "\n" in value or len(value) > 72:
        body = "\n".join("  " + line for line in value.rstrip().splitlines())
        return ">\n" + body
    if (
        (_PLAIN_SAFE.match(value) or _VERSION_SAFE.match(value))
        and value not in {"true", "false", "null", "yes", "no", "on", "off", "~"}
    ):
        return value
    return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""


def render(data: Any, indent: int = 0) -> str:
    if isinstance(data, dict):
        lines: list[str] = []
        for key in sorted(data.keys(), key=_key_sort):
            value = data[key]
            prefix = " " * indent + f"{key}:"
            if isinstance(value, dict):
                if not value:
                    lines.append(prefix + " {}")
                else:
                    lines.append(prefix)
                    lines.append(render(value, indent + 2).rstrip())
            elif isinstance(value, list):
                if not value:
                    lines.append(prefix + " []")
                else:
                    lines.append(prefix)
                    for item in value:
                        if isinstance(item, dict):
                            rendered = render(item, indent + 4).rstrip().split("\n")
                            first = rendered[0].lstrip()
                            lines.append(" " * (indent + 2) + "- " + first)
                            lines.extend(rendered[1:])
                        else:
                            lines.append(" " * (indent + 2) + "- " + _scalar(item))
            else:
                rendered_scalar = _scalar(value)
                if rendered_scalar.startswith(">\n"):
                    lines.append(prefix + " >")
                    body = "\n".join(" " * (indent + 2) + line.strip() for line in value.rstrip().splitlines())
                    lines.append(body)
                else:
                    lines.append(prefix + " " + rendered_scalar)
        return "\n".join(lines) + "\n"
    if isinstance(data, list):
        return "\n".join(("- " + _scalar(item)) for item in data) + "\n"
    return _scalar(data) + "\n"
