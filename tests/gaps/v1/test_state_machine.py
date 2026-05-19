"""Tests for state_machine.check."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate-gaps-v1.py"
MINIMAL = (ROOT / "gaps" / "examples" / "v1" / "minimal" / "ga-process.v1.yml").read_text()


def run(content: str) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", dir=ROOT, delete=False) as handle:
        handle.write(content)
        path = Path(handle.name)
    try:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        path.unlink(missing_ok=True)


def with_state_model(states_block: str, transitions_block: str) -> str:
    states = textwrap.indent("\n".join(line.strip() for line in states_block.splitlines()), "        ")
    transitions = textwrap.indent("\n".join(line.strip() for line in transitions_block.splitlines()), "        ")
    lane_extension = (
        "    stateModel:\n"
        "      states:\n"
        f"{states}\n"
        "      transitions:\n"
        f"{transitions}\n"
    )
    return MINIMAL.replace(
        "    skills:\n      - minimal-example-draft\n",
        lane_extension + "    skills:\n      - minimal-example-draft\n",
    )


class StateMachineTests(unittest.TestCase):
    def test_unreachable_state_fails(self) -> None:
        content = with_state_model(
            states_block="        - {id: open, label: Open, isInitial: true}\n        - {id: detached, label: Detached, isTerminal: true}\n        - {id: closed, label: Closed, isTerminal: true}",
            transitions_block="        - {id: t1, from: open, to: closed}",
        )
        result = run(content)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("detached", result.stderr)
        self.assertIn("unreachable", result.stderr)

    def test_no_initial_state_fails(self) -> None:
        content = with_state_model(
            states_block="        - {id: open, label: Open}\n        - {id: closed, label: Closed, isTerminal: true}",
            transitions_block="        - {id: t1, from: open, to: closed}",
        )
        result = run(content)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("isInitial", result.stderr)

    def test_two_initial_states_fails(self) -> None:
        content = with_state_model(
            states_block="        - {id: a, label: A, isInitial: true}\n        - {id: b, label: B, isInitial: true, isTerminal: true}",
            transitions_block="        - {id: t1, from: a, to: b}",
        )
        result = run(content)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one initial state", result.stderr)

    def test_no_terminal_state_fails(self) -> None:
        content = with_state_model(
            states_block="        - {id: open, label: Open, isInitial: true}",
            transitions_block="        - {id: t1, from: open, to: open}",
        )
        result = run(content)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("at least one terminal state", result.stderr)

    def test_terminal_with_outgoing_transition_fails(self) -> None:
        content = with_state_model(
            states_block="        - {id: open, label: Open, isInitial: true}\n        - {id: closed, label: Closed, isTerminal: true}",
            transitions_block="        - {id: t1, from: open, to: closed}\n        - {id: t2, from: closed, to: open}",
        )
        result = run(content)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("terminal state", result.stderr)
        self.assertIn("outgoing", result.stderr)


if __name__ == "__main__":
    unittest.main()
