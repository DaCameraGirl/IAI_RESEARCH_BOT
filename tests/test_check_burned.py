"""Tests for scripts/check_burned.py"""

from __future__ import annotations

import csv
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import check_burned  # noqa: E402

STUDIES = ("25867", "25854", "25853")


class TestNormalize(unittest.TestCase):
    def test_strips_and_uppercases(self) -> None:
        self.assertEqual(check_burned.normalize(" us-5613071 "), "US5613071")

    def test_removes_dashes(self) -> None:
        self.assertEqual(check_burned.normalize("US-770-2742"), "US7702742")

    def test_strips_kind_codes(self) -> None:
        self.assertEqual(check_burned.patent_key("US7702742B2"), "US7702742")
        self.assertEqual(check_burned.patent_key("US5613071A"), "US5613071")

    def test_normalizes_application_numbers(self) -> None:
        self.assertEqual(check_burned.patent_key("US20090319634A1"), "US2009319634")
        self.assertEqual(check_burned.patent_key("US20100205502A1"), "US2010205502")


class TestLoadBurned(unittest.TestCase):
    def test_all_study_csvs_load(self) -> None:
        for study_id in STUDIES:
            burned = check_burned.load_burned(study_id)
            self.assertGreater(len(burned), 0, f"{study_id} burn list empty")

    def test_25867_has_expected_size(self) -> None:
        burned = check_burned.load_burned("25867")
        self.assertGreaterEqual(len(burned), 160)

    def test_study_patents_are_burned(self) -> None:
        expected = {
            "25867": "US7702742",
            "25854": "US8728916",
            "25853": "US8530250",
        }
        for study_id, patent in expected.items():
            burned = check_burned.load_burned(study_id)
            self.assertIn(
                check_burned.normalize(patent),
                burned,
                f"{patent} should be burned for {study_id}",
            )

    def test_csv_has_required_columns(self) -> None:
        for study_id in STUDIES:
            folder = check_burned.STUDY_DIRS[study_id]
            csv_path = folder / "known_art" / "known_citations.csv"
            with csv_path.open(newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                self.assertIn("Citation/Document Number", reader.fieldnames)
                self.assertIn("Relation", reader.fieldnames)


class TestCheckBurnedCLI(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(REPO / "scripts" / "check_burned.py"), *args],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_burned_citation(self) -> None:
        proc = self.run_cli("25867", "US5613071")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("BURNED", proc.stdout)

    def test_study_patent_with_kind_code_burned(self) -> None:
        proc = self.run_cli("25867", "US7702742B2")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("BURNED", proc.stdout)

    def test_family_member_application_burned(self) -> None:
        proc = self.run_cli("25867", "US20090319634A1", "US20100205502A1")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.count("BURNED"), 2)

    def test_clear_candidate(self) -> None:
        proc = self.run_cli("25867", "US6718392")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("CLEAR", proc.stdout)

    def test_unknown_study_fails(self) -> None:
        proc = self.run_cli("99999", "US0000000")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Unknown study", proc.stderr + proc.stdout)

    def test_usage_without_args(self) -> None:
        proc = self.run_cli()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Usage", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()