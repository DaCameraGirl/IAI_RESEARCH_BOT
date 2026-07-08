"""Tests for scripts/add_study.py — the self-service study onboarding tool."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import add_study  # noqa: E402
import study_bot  # noqa: E402

REAL_OXIMIDOL_BRIEF = """Study ID
25974
Category
Chemistry
Research Type
Invalidity
Expiration Date
15 July 2026

This Study relates to a tyrosinase inhibitor, specifically oximidol.

 Description
This Study is directed to previously unidentified prior art references, including patent and non-patent literature.

The objective of this Study is to find a disclosure of the following molecule:

Common Name: Oximidol

 Study Patents
WO2025201324
CPC Class: A61K
Download
 Research Requirements
Latest Date for Responses
26 March 2024
Relevant Patent Dates:
1
Oximidol (structure as shown above).
"""

REAL_CSV = """Citation/Document Number,Type,Relation
"WO2025201324","Patent","Study Patent"
"WO25201324A1","Patent","Family Member"
"CN105007991","Patent","Citation"
"""

HYMN_BRIEF = """Hymn Research - Russian
Closes in 22 days
Study ID
26006
Category
Other/Miscellaneous
Research Type
Copyright Research
Expiration Date
30 July 2026
This Study is directed to finding Russian translations of various hymns.
"""


class TestAddStudy(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        seed_state = {
            "mode": "one_at_a_time",
            "current_study": "EXIST1",
            "queue": ["EXIST1"],
            "studies": {
                "EXIST1": {
                    "folder": "EXIST1_Placeholder",
                    "status": "active",
                    "rounds_completed": 0,
                    "candidates_found": 0,
                    "submissions_made": 0,
                    "lanes_complete": [],
                }
            },
        }
        (self.tmp_path / "bot_state.json").write_text(json.dumps(seed_state), encoding="utf-8")
        (self.tmp_path / "EXIST1_Placeholder").mkdir()

        study_bot.REPO = self.tmp_path
        study_bot.STATE_PATH = self.tmp_path / "bot_state.json"
        add_study.REPO = self.tmp_path

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_patent_study_end_to_end(self) -> None:
        result = add_study.add_study("25974", REAL_OXIMIDOL_BRIEF, REAL_CSV)

        self.assertEqual(result["type"], "patent")
        self.assertEqual(result["patent"], "WO2025201324")
        self.assertEqual(result["critical_date"], "2024-03-26")
        self.assertFalse(result["blocked"])

        folder = self.tmp_path / result["folder"]
        self.assertTrue((folder / "STUDY_BRIEF.md").exists())
        self.assertTrue((folder / "CANDIDATE_SCREEN.md").exists())
        self.assertTrue((folder / "HUNT_LOG.md").exists())
        self.assertTrue((folder / "known_art" / "known_citations.csv").exists())
        self.assertTrue((folder / "known_art" / "KNOWN_CITATIONS.md").exists())
        self.assertTrue((folder / "candidates" / ".gitkeep").exists())
        self.assertTrue((folder / "reference" / ".gitkeep").exists())
        self.assertTrue((folder / "submitted" / ".gitkeep").exists())

        meta = json.loads((folder / "STUDY_META.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["patent"], "WO2025201324")
        self.assertEqual(meta["critical_date"], "2024-03-26")

        state = study_bot.load_state()
        self.assertIn("25974", state["queue"])
        self.assertEqual(state["studies"]["25974"]["folder"], result["folder"])
        self.assertFalse(study_bot.is_blocked("25974"))

    def test_copyright_study_no_csv(self) -> None:
        result = add_study.add_study("26006", HYMN_BRIEF, None)

        self.assertEqual(result["type"], "copyright")
        self.assertIsNone(result["patent"])
        self.assertFalse(result["blocked"])

        folder = self.tmp_path / result["folder"]
        self.assertFalse((folder / "known_art").exists())
        self.assertFalse((folder / "HUNT_LOG.md").exists())
        self.assertTrue((folder / "sources" / ".gitkeep").exists())
        self.assertFalse(study_bot.is_blocked("26006"))

    def test_unparseable_patent_study_is_blocked(self) -> None:
        result = add_study.add_study("99999", "No structured info here at all.", REAL_CSV)
        self.assertTrue(result["blocked"])
        self.assertTrue(study_bot.is_blocked("99999"))
        folder = self.tmp_path / result["folder"]
        text = (folder / "STUDY_BRIEF.md").read_text(encoding="utf-8")
        self.assertIn(study_bot.BLOCKED_SENTINEL, text)

    def test_duplicate_study_id_rejected(self) -> None:
        with self.assertRaises(add_study.AddStudyError):
            add_study.add_study("EXIST1", "irrelevant", None)


if __name__ == "__main__":
    unittest.main()
