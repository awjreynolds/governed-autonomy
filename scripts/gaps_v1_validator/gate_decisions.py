"""Gate decision and transition guard completeness checks."""

from __future__ import annotations

from typing import Any

from .errors import ValidationReport
from .feel_subset import FeelParseError, idents_used, parse


def _check_rules(
    rules: list[dict[str, Any]],
    inputs: list[str],
    where: str,
    report: ValidationReport,
    valid_thens: set[str],
) -> None:
    declared = set(inputs)
    for index, rule in enumerate(rules):
        expr = rule.get("when")
        if not isinstance(expr, str):
            report.add("gate-decisions", f"{where}.rules[{index}].when", "missing or non-string expression")
            continue
        try:
            node = parse(expr)
        except FeelParseError as error:
            report.add("gate-decisions", f"{where}.rules[{index}].when", f"FEEL parse error: {error}")
            continue
        used = idents_used(node)
        for ident in sorted(used - declared):
            report.add(
                "gate-decisions",
                f"{where}.rules[{index}].when",
                f"undeclared input {ident!r} (not in {where}.inputs)",
            )
        then = rule.get("then")
        if then is not None and then not in valid_thens:
            report.add("gate-decisions", f"{where}.rules[{index}].then", f"value {then!r} not in {sorted(valid_thens)}")


def check(spec: dict[str, Any], report: ValidationReport) -> None:
    for gate in spec.get("gates", []):
        decision = gate.get("decision")
        if not decision:
            continue
        where = f"$.gates[id={gate.get('id')}].decision"
        inputs = list(decision.get("inputs", []) or [])
        rules = list(decision.get("rules", []) or [])
        else_clause = decision.get("else")
        if not rules:
            report.add("gate-decisions", where, "decision has no rules")
            continue
        _check_rules(rules, inputs, where, report, valid_thens={"approve", "escalate", "reject"})
        if else_clause is None:
            covered_idents: set[str] = set()
            for rule in rules:
                try:
                    covered_idents |= idents_used(parse(rule.get("when") or ""))
                except FeelParseError:
                    continue
            if set(inputs) - covered_idents:
                report.add(
                    "gate-decisions",
                    where,
                    "missing else clause and rules do not reference all declared inputs; provide an else or extend rule coverage",
                )
        if gate.get("gateType") == "blocking":
            outcomes = {rule.get("then") for rule in rules}
            if "approve" not in outcomes:
                report.add("gate-decisions", where, "blocking gate must have at least one rule with then: approve")
            if not (outcomes & {"escalate", "reject"}):
                report.add("gate-decisions", where, "blocking gate must have at least one rule with then: escalate or then: reject")

    for lane in spec.get("lanes", []):
        state_model = lane.get("stateModel") or {}
        for transition in state_model.get("transitions", []) or []:
            guard = transition.get("guard")
            if not guard:
                continue
            where = f"$.lanes[id={lane.get('id')}].stateModel.transitions[id={transition.get('id')}].guard"
            inputs = list(guard.get("inputs", []) or [])
            rules = list(guard.get("rules", []) or [])
            if not rules:
                report.add("gate-decisions", where, "guard has no rules")
                continue
            _check_rules(rules, inputs, where, report, valid_thens={"allow", "block"})
            if guard.get("else") is None:
                covered: set[str] = set()
                for rule in rules:
                    try:
                        covered |= idents_used(parse(rule.get("when") or ""))
                    except FeelParseError:
                        continue
                if set(inputs) - covered:
                    report.add("gate-decisions", where, "missing else clause and rules do not reference all declared inputs")
