from __future__ import annotations

import unittest

from scripts.ga_enforce.action_map import match_tool_action


class ActionMapTests(unittest.TestCase):
    def test_matches_bash_subcommand_pattern(self) -> None:
        action = match_tool_action(
            {
                "catalog:action:approve-own-work": ["Bash(git push *)"],
            },
            {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}},
        )

        self.assertEqual(action, "catalog:action:approve-own-work")

    def test_matches_tool_name_pattern(self) -> None:
        action = match_tool_action(
            {
                "catalog:action:draft-artifact": ["Write"],
            },
            {"tool_name": "Write", "tool_input": {"file_path": "evidence/draft.md"}},
        )

        self.assertEqual(action, "catalog:action:draft-artifact")


if __name__ == "__main__":
    unittest.main()
