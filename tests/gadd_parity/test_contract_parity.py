from __future__ import annotations

import unittest
from pathlib import Path

from tests.gadd_parity.parity import (
    load_fixture,
    manifest_commands,
    validate_command_adapter,
    validate_expected_commands,
    validate_skill_contract,
    validate_skill_surface,
)


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "reference-packages" / "gadd"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class GaddContractParityTests(unittest.TestCase):
    def expected_commands(self) -> list[dict[str, str]]:
        data = load_fixture(FIXTURES / "expected-commands.yml")
        commands = data.get("commands")
        self.assertIsInstance(commands, list)
        return commands

    def contracts(self) -> dict[str, dict]:
        data = load_fixture(FIXTURES / "required-skill-contracts.yml")
        contracts = data.get("contracts")
        self.assertIsInstance(contracts, dict)
        return contracts

    def assert_no_errors(self, errors: list[str]) -> None:
        self.assertEqual([], errors, "\n".join(errors))

    def test_reference_package_has_expected_gadd_command_manifest(self) -> None:
        self.assert_no_errors(validate_expected_commands(PACKAGE_ROOT, self.expected_commands()))

    def test_reference_package_command_adapters_match_manifest(self) -> None:
        commands = manifest_commands(PACKAGE_ROOT)
        errors: list[str] = []
        for item in self.expected_commands():
            command = item["command"]
            errors.extend(validate_command_adapter(PACKAGE_ROOT, command, commands[command]))
        self.assert_no_errors(errors)

    def test_reference_package_skills_match_manifest_surface(self) -> None:
        commands = manifest_commands(PACKAGE_ROOT)
        errors: list[str] = []
        for item in self.expected_commands():
            command = item["command"]
            errors.extend(validate_skill_surface(PACKAGE_ROOT, command, commands[command]))
        self.assert_no_errors(errors)

    def test_high_risk_command_contracts_are_present(self) -> None:
        errors: list[str] = []
        for command, contract in self.contracts().items():
            errors.extend(validate_skill_contract(PACKAGE_ROOT, command, contract))
        self.assert_no_errors(errors)


if __name__ == "__main__":
    unittest.main()
