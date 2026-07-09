#!/usr/bin/env python3
"""Automated search engine for copyright-research (hymn translation) studies.

Patent studies have citation-graph APIs to crawl (patent_hunter.py). Hymn
translation studies don't have an equivalent structured graph — finding an
existing Russian/Italian/Cebuano translation of a named hymn means searching
real archives. This hits two keyless, real APIs (Internet Archive full-text
search, Google Books) per hymn and surfaces candidate sources.

It does NOT auto-verify a hit actually contains the correct translation,
the translator's name, or a usable date — that requires reading the actual
source, which is exactly what RWS's submission rules require a human/agent
to confirm anyway (real screenshots, real bibliographic details, no
guessing). This engine's job is to turn "manually search 125 hymns one at
a time" into "review N pre-queried candidate sources per hymn."
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Callable

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from study_bot import STUDY_META  # noqa: E402

LogFn = Callable[[str, str], None]

IA_SEARCH_URL = "https://archive.org/advancedsearch.php"
GB_SEARCH_URL = "https://www.googleapis.com/books/v1/volumes"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_PAUSE = 0.3
MAX_HYMNS_PER_ROUND = 125


def _get_json(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _ia_search(query: str, rows: int) -> list[dict]:
    params = {
        "q": query,
        "fl[]": ["identifier", "title"],
        "rows": str(rows),
        "page": "1",
        "output": "json",
    }
    url = IA_SEARCH_URL + "?" + urllib.parse.urlencode(params, doseq=True)
    try:
        data = _get_json(url)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return []
    out = []
    for d in data.get("response", {}).get("docs", []):
        ident = d.get("identifier")
        if not ident:
            continue
        out.append(
            {
                "source": "archive.org",
                "title": d.get("title") or ident.replace("-", " ").replace("_", " "),
                "url": f"https://archive.org/details/{ident}",
            }
        )
    return out


def search_hymnal_sources(language: str, rows: int = 8) -> list[dict]:
    """One broad search per language for actual hymnal books — this is the
    highest-signal query: restricting to mediatype:(texts) (verified live —
    excludes the radio/sermon-audio noise that dominates plain full-text
    search) and searching for the hymnal itself rather than one English
    title, which foreign-language hymnal metadata won't usually contain.
    """
    seen_urls: set[str] = set()
    out: list[dict] = []
    queries = (
        f'{language} AND hymnal AND mediatype:(texts)',
        f'{language} AND "hymn book" AND mediatype:(texts)',
    )
    for q in queries:
        for hit in _ia_search(q, rows):
            if hit["url"] not in seen_urls:
                seen_urls.add(hit["url"])
                out.append(hit)
    return out


def search_internet_archive(hymn_title: str, language: str, rows: int = 5) -> list[dict]:
    """Per-hymn search — lower yield than search_hymnal_sources() since a
    foreign hymnal's own metadata rarely contains the English title, but
    occasionally surfaces a direct hit (verified live against real hymn
    titles). mediatype:(texts) is required — without it, results are
    dominated by radio broadcast / sermon audio transcripts that merely
    co-mention the title and the language name.
    """
    # Add language-specific keywords to filter out English sources
    lang_keywords = {
        "Italian": "inno OR innario OR canto",
        "Russian": "гимн OR песня",
        "Cebuano": "awit OR himno"
    }
    extra = lang_keywords.get(language, "")
    if extra:
        query = f'"{hymn_title}" AND ({extra}) AND mediatype:(texts)'
    else:
        query = f'"{hymn_title}" AND {language} AND mediatype:(texts)'
    return _ia_search(query, rows)


def search_google_books(hymn_title: str, language: str, language_code: str | None, rows: int = 5) -> list[dict]:
    """Real, keyless (free-tier) search against the Google Books API."""
    # Add language-specific keywords to improve relevance
    lang_keywords = {
        "Italian": "inno OR innario",
        "Russian": "гимн",
        "Cebuano": "awit OR himno"
    }
    extra = lang_keywords.get(language, "hymnal")
    query = f'"{hymn_title}" {language} {extra}'
    params = {"q": query, "maxResults": str(rows)}
    if language_code:
        params["langRestrict"] = language_code
    url = GB_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    try:
        data = _get_json(url)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return []
    out = []
    for item in data.get("items", []) or []:
        info = item.get("volumeInfo", {})
        title = info.get("title", "")
        link = info.get("infoLink") or info.get("canonicalVolumeLink") or ""
        if not title or not link:
            continue
        year = (info.get("publishedDate") or "")[:4]
        out.append(
            {
                "source": "google_books",
                "title": f"{title} ({year})" if year else title,
                "url": link,
            }
        )
    return out


class HymnHuntEngine:
    def __init__(self, study_id: str, on_log: LogFn | None = None) -> None:
        self.study_id = study_id
        self.on_log = on_log or (lambda m, l: None)
        self.stopped = False
        self.hymns_searched = 0
        self.leads_found = 0

    def log(self, msg: str, level: str = "info") -> None:
        self.on_log(msg, level)

    def stop(self) -> None:
        self.stopped = True

    def _load_hymn_list(self, folder: Path) -> list[str]:
        path = folder / "HYMN_LIST.txt"
        if not path.exists():
            return []
        return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def run(self) -> dict:
        meta = STUDY_META[self.study_id]
        folder = REPO / meta["folder"]
        language = meta.get("language") or meta["title"]
        language_code = meta.get("language_code")

        hymns = self._load_hymn_list(folder)
        if not hymns:
            self.log(
                f"No {folder / 'HYMN_LIST.txt'} found — nothing to search. "
                "Add the hymn list from the RWS brief's zip file to this folder.",
                "warn",
            )
            return {"hymns_searched": 0, "leads_found": 0}

        self.log(f"Starting hymn search for {self.study_id} — {meta['title']}", "phase")

        self.log(f"Lane 1: searching for {language} hymnal sources (highest-signal query)", "lane")
        hymnal_sources = search_hymnal_sources(language)
        self.log(f"  Found {len(hymnal_sources)} candidate hymnal source(s)", "info")
        time.sleep(REQUEST_PAUSE)

        self.log(f"Lane 2: searching each of {len(hymns)} hymns individually", "lane")
        leads: list[dict] = []
        for hymn in hymns[:MAX_HYMNS_PER_ROUND]:
            if self.stopped:
                self.log("Hunt stopped by user", "warn")
                break
            hits = search_internet_archive(hymn, language)
            time.sleep(REQUEST_PAUSE)
            hits += search_google_books(hymn, language, language_code)
            time.sleep(REQUEST_PAUSE)
            self.hymns_searched += 1
            if hits:
                leads.append({"hymn": hymn, "hits": hits})
                self.leads_found += len(hits)
                self.log(f"  {hymn}: {len(hits)} candidate source(s)", "info")
            if self.hymns_searched % 10 == 0:
                self.log(f"Searched {self.hymns_searched}/{len(hymns)} hymns…", "info")

        self._write_candidate_screen(folder, hymnal_sources, leads)
        self._write_candidate_files(folder, language, hymnal_sources, leads)
        self._update_hunt_log(folder, len(hymns))

        self.log(
            f"Done — {len(hymnal_sources)} hymnal source(s) + {self.leads_found} per-hymn "
            f"candidate(s) across {len(leads)}/{self.hymns_searched} hymns searched. "
            "Every lead needs manual verification before submission — translator, date, and "
            "copyright info can't be auto-confirmed, and RWS requires real screenshots anyway.",
            "phase",
        )
        return {
            "hymns_searched": self.hymns_searched,
            "leads_found": self.leads_found,
            "hymnal_sources": len(hymnal_sources),
        }

    def _write_candidate_screen(self, folder: Path, hymnal_sources: list[dict], leads: list[dict]) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        lines = [
            f"# Candidate Screen — updated {today}",
            "",
            f"Inspected: {self.hymns_searched} · Hymns with leads: {len(leads)} · "
            f"Total per-hymn candidates: {self.leads_found} · Hymnal sources: {len(hymnal_sources)}",
            "",
            "## Candidate hymnal sources (search WITHIN these for the full hymn list — "
            "highest-value lead type, verified to beat per-hymn search)",
            "",
        ]
        if hymnal_sources:
            for hit in hymnal_sources:
                lines.append(f"- [{hit['source']}] {hit['title']} — {hit['url']}")
        else:
            lines.append("- (none found — try broadening the language name or check manually)")
        lines += [
            "",
            "## Per-hymn leads found this round (unverified — read source before submitting)",
            "",
        ]
        if leads:
            for lead in leads:
                lines.append(f"### {lead['hymn']}")
                for hit in lead["hits"]:
                    lines.append(f"- [{hit['source']}] {hit['title']} — {hit['url']}")
                lines.append("")
        else:
            lines.append("- (none this round)")
            lines.append("")
        lines += ["## HOLD (rank 1 — verify before surfacing)", "", "- (none)"]
        (folder / "CANDIDATE_SCREEN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_candidate_files(
        self, folder: Path, language: str, hymnal_sources: list[dict], leads: list[dict]
    ) -> None:
        """Write one file per lead into candidates/ so the web app's Candidates
        tab (which reads candidates/*.txt) actually shows hymn leads — writing
        only to CANDIDATE_SCREEN.md left that tab empty for these studies.
        """
        cand_dir = folder / "candidates"
        cand_dir.mkdir(parents=True, exist_ok=True)
        for old in cand_dir.glob("*_hymn_lead.txt"):
            old.unlink(missing_ok=True)

        def _slug(text: str, limit: int = 60) -> str:
            keep = "".join(c if c.isalnum() or c in " -_" else "" for c in text)
            return "_".join(keep.split())[:limit] or "item"

        for hit in hymnal_sources:
            fname = f"HYMNAL_SOURCE_{_slug(hit['title'])}_hymn_lead.txt"
            (cand_dir / fname).write_text(
                "Type: Candidate hymnal source (search within for the full hymn list)\n"
                f"Language: {language}\n"
                f"Source: {hit['source']}\n"
                f"Title: {hit['title']}\n"
                f"URL: {hit['url']}\n"
                "Status: UNVERIFIED — open and search within before submitting anything from it\n",
                encoding="utf-8",
            )

        for lead in leads:
            for i, hit in enumerate(lead["hits"]):
                fname = f"{_slug(lead['hymn'])}_{i}_hymn_lead.txt"
                (cand_dir / fname).write_text(
                    "Type: Hymn translation lead\n"
                    f"Hymn: {lead['hymn']}\n"
                    f"Language: {language}\n"
                    f"Source: {hit['source']}\n"
                    f"Title: {hit['title']}\n"
                    f"URL: {hit['url']}\n"
                    "Status: UNVERIFIED — read the source and confirm translator/date/copyright "
                    "before submitting; RWS requires a real screenshot attachment\n",
                    encoding="utf-8",
                )

    def _update_hunt_log(self, folder: Path, total_hymns: int) -> None:
        log_path = folder / "HUNT_LOG.md"
        today = datetime.now().strftime("%Y-%m-%d")
        row = f"| {today} | {self.hymns_searched}/{total_hymns} | {self.leads_found} | archive.org + Google Books |"
        header = (
            f"# {self.study_id} Hunt Log\n\n"
            "Bot updates this after each hunt round. Angela can ignore unless auditing coverage.\n\n"
            "| Date | Hymns searched | Candidate sources found | Engines |\n"
            "|------|-----------------|--------------------------|---------|\n"
        )
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8")
            if "| Date | Hymns searched |" in text:
                text = text.rstrip() + "\n" + row + "\n"
            else:
                text = header + row + "\n"
        else:
            text = header + row + "\n"
        log_path.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/hymn_hunter.py <study_id>")
        raise SystemExit(1)
    engine = HymnHuntEngine(sys.argv[1], on_log=lambda m, l: print(f"[{l}] {m}"))
    engine.run()


if __name__ == "__main__":
    main()
