from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.ga_enforce.active_step import clear_active_step, read_active_step, write_active_step


class ActiveStepTests(unittest.TestCase):
    def test_read_write_and_clear_active_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            process = Path(tmp)
            write_active_step(process, {"step": "draft", "done": {"tool_name": "Bash", "command_glob": "ga-step done draft"}})

            self.assertEqual(read_active_step(process)["step"], "draft")

            clear_active_step(process)

            self.assertEqual(read_active_step(process), {})


if __name__ == "__main__":
    unittest.main()
