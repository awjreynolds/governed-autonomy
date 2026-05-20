from __future__ import annotations

import json
import unittest

from scripts.ga_enforce.decisions import allow, deny, post_block


class DecisionsTests(unittest.TestCase):
    def test_pre_tool_deny_uses_hook_specific_permission_decision(self) -> None:
        decision = json.loads(deny("blocked")["stdout"])

        self.assertEqual(decision["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(deny("blocked")["exit_code"], 2)

    def test_post_tool_block_uses_post_tool_decision(self) -> None:
        decision = json.loads(post_block("missing evidence")["stdout"])

        self.assertEqual(decision["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        self.assertEqual(decision["hookSpecificOutput"]["decision"], "block")
        self.assertEqual(post_block("missing evidence")["exit_code"], 2)

    def test_allow_exits_zero_without_stdout(self) -> None:
        self.assertEqual(allow(), {"exit_code": 0, "stdout": ""})


if __name__ == "__main__":
    unittest.main()
