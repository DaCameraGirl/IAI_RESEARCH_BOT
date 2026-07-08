"""Tests for scripts/study_bot.py (isolated state file)."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class TestStudyBot(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        state_src = REPO / "bot_state.json"
        self.state_path = self.tmp_path / "bot_state.json"
        shutil.copy(state_src, self.state_path)
        self.bot_script = REPO / "scripts" / "study_bot.py"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def patch_state_path(self) -> None:
        """Monkey-patch STATE_PATH in study_bot for this test run."""
        import importlib

        if "study_bot" in sys.modules:
            del sys.modules["study_bot"]
        sys.path.insert(0, str(REPO / "scripts"))
        import study_bot  # noqa: E402

        study_bot.STATE_PATH = self.state_path
        study_bot.REPO = REPO
        self.study_bot = study_bot

    def test_bot_state_schema(self) -> None:
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertIn("current_study", state)
        self.assertIn("queue", state)
        self.assertIn("studies", state)
        for sid in state["queue"]:
            self.assertIn(sid, state["studies"])
            study = state["studies"][sid]
            for key in ("rounds_completed", "candidates_found", "submissions_made"):
                self.assertIn(key, study)

    def test_round_done_increments(self) -> None:
        self.patch_state_path()
        before = self.study_bot.load_state()
        sid = before["current_study"]
        rounds_before = before["studies"][sid]["rounds_completed"]
        with contextlib.redirect_stdout(io.StringIO()):
            self.study_bot.cmd_round_done(before)
        after = self.study_bot.load_state()
        self.assertEqual(after["studies"][sid]["rounds_completed"], rounds_before + 1)
        self.assertEqual(self.study_bot.load_state()["studies"][sid]["rounds_completed"], rounds_before + 1)

    def test_status_cli(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(self.bot_script), "status"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("26052", proc.stdout)
        self.assertIn("25974", proc.stdout)

    def test_no_study_blocked(self) -> None:
        self.patch_state_path()
        self.assertFalse(self.study_bot.is_blocked("26052"))
        self.assertFalse(self.study_bot.is_blocked("25974"))


if __name__ == "__main__":
    unittest.main()