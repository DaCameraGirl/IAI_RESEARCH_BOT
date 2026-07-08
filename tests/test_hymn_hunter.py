"""Tests for scripts/hymn_hunter.py."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import hymn_hunter  # noqa: E402
import study_bot  # noqa: E402

IA_RESPONSE = {
    "response": {
        "docs": [
            {"identifier": "russian-hymnal-1911"},
            {"identifier": "sda-himny-collection"},
        ]
    }
}

GB_RESPONSE = {
    "items": [
        {
            "volumeInfo": {
                "title": "Sbornik Gimnov",
                "publishedDate": "1998-01-01",
                "infoLink": "https://books.google.com/books?id=abc123",
            }
        },
        {"volumeInfo": {"title": "No link here"}},
    ]
}


class TestSearchFunctions(unittest.TestCase):
    def test_internet_archive_parses_docs(self) -> None:
        with patch.object(hymn_hunter, "_get_json", return_value=IA_RESPONSE):
            hits = hymn_hunter.search_internet_archive("Amazing Grace", "Russian")
        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0]["source"], "archive.org")
        self.assertIn("archive.org/details/russian-hymnal-1911", hits[0]["url"])

    def test_google_books_skips_items_without_link(self) -> None:
        with patch.object(hymn_hunter, "_get_json", return_value=GB_RESPONSE):
            hits = hymn_hunter.search_google_books("Amazing Grace", "Russian", "ru")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["source"], "google_books")
        self.assertIn("1998", hits[0]["title"])

    def test_network_errors_return_empty_not_raise(self) -> None:
        with patch.object(hymn_hunter, "_get_json", side_effect=TimeoutError()):
            self.assertEqual(hymn_hunter.search_internet_archive("X", "Russian"), [])
            self.assertEqual(hymn_hunter.search_google_books("X", "Russian", "ru"), [])

    def test_hymnal_sources_dedupes_across_queries(self) -> None:
        with patch.object(hymn_hunter, "_get_json", return_value=IA_RESPONSE):
            hits = hymn_hunter.search_hymnal_sources("Russian")
        # Two queries hit the same two docs — dedup should collapse to 2, not 4
        self.assertEqual(len(hits), 2)

    def test_per_hymn_query_requires_mediatype_texts(self) -> None:
        captured = {}

        def fake_get_json(url):
            captured["url"] = url
            return {"response": {"docs": []}}

        with patch.object(hymn_hunter, "_get_json", side_effect=fake_get_json):
            hymn_hunter.search_internet_archive("Amazing Grace", "Russian")
        self.assertIn("mediatype", captured["url"])


class TestHymnHuntEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        state = {
            "mode": "one_at_a_time",
            "current_study": "26006",
            "queue": ["26006"],
            "studies": {
                "26006": {
                    "folder": "26006_Test",
                    "status": "active",
                    "rounds_completed": 0,
                    "candidates_found": 0,
                    "submissions_made": 0,
                    "lanes_complete": [],
                }
            },
        }
        (self.tmp_path / "bot_state.json").write_text(json.dumps(state), encoding="utf-8")
        folder = self.tmp_path / "26006_Test"
        folder.mkdir()
        (folder / "STUDY_META.json").write_text(
            json.dumps(
                {
                    "title": "Hymn Research - Russian",
                    "type": "copyright",
                    "patent": None,
                    "critical_date": None,
                    "focus": "test",
                    "language": "Russian",
                    "language_code": "ru",
                }
            ),
            encoding="utf-8",
        )
        (folder / "HYMN_LIST.txt").write_text("Amazing Grace\nBe Thou My Vision\n", encoding="utf-8")

        study_bot.REPO = self.tmp_path
        study_bot.STATE_PATH = self.tmp_path / "bot_state.json"
        hymn_hunter.REPO = self.tmp_path

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_run_writes_candidate_screen_and_hunt_log(self) -> None:
        with patch.object(hymn_hunter, "search_hymnal_sources", return_value=[
            {"source": "archive.org", "title": "Russian Hymnal Collection", "url": "https://archive.org/details/y"}
        ]), patch.object(hymn_hunter, "search_internet_archive", return_value=[
            {"source": "archive.org", "title": "Russian Hymnal", "url": "https://archive.org/details/x"}
        ]), patch.object(hymn_hunter, "search_google_books", return_value=[]), \
             patch("time.sleep", return_value=None):
            engine = hymn_hunter.HymnHuntEngine("26006", on_log=lambda m, l: None)
            result = engine.run()

        self.assertEqual(result["hymns_searched"], 2)
        self.assertEqual(result["leads_found"], 2)
        self.assertEqual(result["hymnal_sources"], 1)

        folder = self.tmp_path / "26006_Test"
        screen = (folder / "CANDIDATE_SCREEN.md").read_text(encoding="utf-8")
        self.assertIn("Amazing Grace", screen)
        self.assertIn("Russian Hymnal Collection", screen)
        self.assertIn("archive.org", screen)
        log = (folder / "HUNT_LOG.md").read_text(encoding="utf-8")
        self.assertIn("2/2", log)

    def test_missing_hymn_list_logs_warning_no_crash(self) -> None:
        (self.tmp_path / "26006_Test" / "HYMN_LIST.txt").unlink()
        logs = []
        engine = hymn_hunter.HymnHuntEngine("26006", on_log=lambda m, l: logs.append((m, l)))
        result = engine.run()
        self.assertEqual(result["hymns_searched"], 0)
        self.assertTrue(any("No" in m and "HYMN_LIST" in m for m, l in logs))

    def test_stop_halts_early(self) -> None:
        with patch.object(hymn_hunter, "search_hymnal_sources", return_value=[]), \
             patch.object(hymn_hunter, "search_internet_archive", return_value=[]), \
             patch.object(hymn_hunter, "search_google_books", return_value=[]), \
             patch("time.sleep", return_value=None):
            engine = hymn_hunter.HymnHuntEngine("26006", on_log=lambda m, l: None)
            engine.stop()
            result = engine.run()
        self.assertEqual(result["hymns_searched"], 0)


if __name__ == "__main__":
    unittest.main()
