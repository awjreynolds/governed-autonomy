"""Per-lane state machine soundness for GAPS v1 specs."""

from __future__ import annotations

from collections import deque
from typing import Any

from .errors import ValidationReport


def check(spec: dict[str, Any], report: ValidationReport) -> None:
    for lane in spec.get("lanes", []):
        state_model = lane.get("stateModel")
        if not state_model:
            continue
        lane_id = lane.get("id")
        path = f"$.lanes[id={lane_id}].stateModel"
        states: list[dict[str, Any]] = state_model.get("states") or []
        transitions: list[dict[str, Any]] = state_model.get("transitions") or []

        initial_states = [s["id"] for s in states if s.get("isInitial")]
        terminal_states = {s["id"] for s in states if s.get("isTerminal")}
        all_state_ids = {s["id"] for s in states if "id" in s}

        if len(initial_states) != 1:
            report.add(
                "state-machine",
                path,
                f"expected exactly one initial state (isInitial: true); found {len(initial_states)}",
            )
        if not terminal_states:
            report.add("state-machine", path, "expected at least one terminal state (isTerminal: true); found none")

        transition_ids: dict[str, int] = {}
        for transition in transitions:
            tid = transition.get("id")
            if tid is None:
                continue
            transition_ids[tid] = transition_ids.get(tid, 0) + 1
        for tid, count in transition_ids.items():
            if count > 1:
                report.add("state-machine", f"{path}.transitions[id={tid}]", f"duplicate transition id {tid!r} within lane")

        for transition in transitions:
            src = transition.get("from")
            if src in terminal_states:
                report.add(
                    "state-machine",
                    f"{path}.transitions[id={transition.get('id')}]",
                    f"terminal state {src!r} has outgoing transition",
                )

        if initial_states:
            adjacency: dict[str, list[str]] = {sid: [] for sid in all_state_ids}
            for transition in transitions:
                src = transition.get("from")
                dst = transition.get("to")
                if src in adjacency and dst is not None:
                    adjacency[src].append(dst)
            queue: deque[str] = deque([initial_states[0]])
            reached: set[str] = set()
            while queue:
                node = queue.popleft()
                if node in reached:
                    continue
                reached.add(node)
                for neighbour in adjacency.get(node, []):
                    if neighbour not in reached:
                        queue.append(neighbour)
            for sid in sorted(all_state_ids - reached):
                report.add("state-machine", f"{path}.states[id={sid}]", f"state {sid!r} is unreachable from initial state")

        for sid in all_state_ids:
            if sid in terminal_states:
                continue
            has_outgoing = any(t.get("from") == sid for t in transitions)
            if not has_outgoing:
                report.add("state-machine", f"{path}.states[id={sid}]", f"non-terminal state {sid!r} has no outgoing transition")
