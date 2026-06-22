"""Tests for submission templates and 90% in-scope gate wiring."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

TEMPLATE_FILES = (
    "templates/PATENT_SUBMISSION_TEMPLATE.txt",
    "templates/NPL_SUBMISSION_TEMPLATE.txt",
)

GATE_FILES = (
    "system_prompt.md",
    "ZERO_MISS_PROTOCOL.md",
    "templates/RWS_SUBMISSION_PLAYBOOK.md",
    ".cursor/rules/rws-research-bot.mdc",
)

REQUIRED_TEMPLATE_LINES = (
    "Self-rank:",
    "In-scope confidence:",
    "Do NOT select:",
    "Highlight only this:",
    "Ctrl+F phrases:",
)


class TestSubmissionTemplates(unittest.TestCase):
    def test_templates_exist_and_include_gate(self) -> None:
        for rel in TEMPLATE_FILES:
            text = (REPO / rel).read_text(encoding="utf-8")
            for line in REQUIRED_TEMPLATE_LINES:
                self.assertIn(line, text, f"{rel} missing {line!r}")
            self.assertIn("Self-rank ≥ 2", text, f"{rel} missing surface rule")

    def test_playbook_defines_rank_table(self) -> None:
        text = (REPO / "templates/RWS_SUBMISSION_PLAYBOOK.md").read_text(encoding="utf-8")
        self.assertIn("90% in-scope", text)
        self.assertIn("| **3** |", text)
        self.assertIn("| **0** |", text)
        self.assertIn("confidence **high** or **med**", text)

    def test_gate_wired_everywhere(self) -> None:
        for rel in GATE_FILES:
            self.assertIn(
                "Self-rank",
                (REPO / rel).read_text(encoding="utf-8"),
                f"{rel} missing Self-rank gate",
            )


if __name__ == "__main__":
    unittest.main()