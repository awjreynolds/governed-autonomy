from __future__ import annotations

import unittest

from scripts.ga_lint.merge import effective_authority_for_step, merge_authority


class MergeAuthorityTests(unittest.TestCase):
    def test_step_allowed_actions_replace_process_default(self) -> None:
        authority = {
            "default_autonomy_tier": "draft",
            "default_allowed_actions": ["catalog:action:draft-artifact"],
            "prohibited_actions": ["catalog:action:approve-own-work"],
        }
        step = {
            "authority_overrides": {
                "allowed_actions": ["catalog:action:gather-context"],
                "prohibited_actions": ["local:write-prod"],
                "autonomy_tier": "assist",
            }
        }

        effective = merge_authority(authority, step)

        self.assertEqual(effective.allowed_actions, ["catalog:action:gather-context"])
        self.assertEqual(effective.prohibited_actions, ["catalog:action:approve-own-work", "local:write-prod"])
        self.assertEqual(effective.autonomy_tier, "assist")

    def test_missing_step_override_inherits_defaults(self) -> None:
        effective = merge_authority(
            {
                "default_autonomy_tier": "draft",
                "default_allowed_actions": ["catalog:action:draft-artifact"],
                "prohibited_actions": ["catalog:action:approve-own-work"],
            },
            {},
        )

        self.assertEqual(effective.allowed_actions, ["catalog:action:draft-artifact"])
        self.assertEqual(effective.prohibited_actions, ["catalog:action:approve-own-work"])
        self.assertEqual(effective.autonomy_tier, "draft")

    def test_effective_authority_for_step_uses_same_merge_semantics(self) -> None:
        effective = effective_authority_for_step(
            {
                "authority": {
                    "default_autonomy_tier": "draft",
                    "default_allowed_actions": ["catalog:action:draft-artifact"],
                    "prohibited_actions": ["catalog:action:approve-own-work"],
                },
                "steps": [
                    {
                        "id": "design",
                        "authority_overrides": {
                            "allowed_actions": ["catalog:action:gather-context"],
                            "prohibited_actions": ["local:write-prod"],
                            "autonomy_tier": "assist",
                        },
                    }
                ],
            },
            "design",
        )

        self.assertEqual(effective.allowed_actions, ["catalog:action:gather-context"])
        self.assertEqual(effective.prohibited_actions, ["catalog:action:approve-own-work", "local:write-prod"])
        self.assertEqual(effective.autonomy_tier, "assist")


if __name__ == "__main__":
    unittest.main()
