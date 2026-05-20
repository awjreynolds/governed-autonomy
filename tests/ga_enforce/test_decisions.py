from __future__ import annotations

import json
import unittest

from scripts.ga_enforce.decisions import allow, deny, post_block


class DecisionsTests(unittest.TestCase):
    def test_pre_tool_deny_uses_blocking_stderr(self) -> None:
        result = deny("blocked")

        self.assertEqual(result["exit_code"], 2)
        self.assertEqual(result["stdout"], "")
        self.assertEqual(result["stderr"], "blocked")

    def test_post_tool_block_uses_exit_zero_json_feedback(self) -> None:
        result = post_block("missing evidence")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stderr"], "")
        decision = json.loads(result["stdout"])

        self.assertEqual(decision["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        self.assertEqual(decision["hookSpecificOutput"]["decision"], "block")

    def test_allow_exits_zero_without_stdout(self) -> None:
        self.assertEqual(allow(), {"exit_code": 0, "stdout": "", "stderr": ""})


if __name__ == "__main__":
    unittest.main()
