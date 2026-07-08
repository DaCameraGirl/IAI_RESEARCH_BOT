#!/usr/bin/env python3
"""Check if a document is in a study's known_citations.csv — NEVER surface duplicates."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from study_bot import STUDY_META  # noqa: E402

STUDY_DIRS = {sid: REPO / meta["folder"] for sid, meta in STUDY_META.items()}

_PATENT_PREFIXES = ("US", "EP", "WO", "CN", "JP", "KR", "DE", "GB", "FR")


def patent_key(doc: str) -> str:
    """Canonical key for burn matching — strips kind codes, normalizes US app numbers."""
    s = doc.strip().upper().replace("-", "").replace(" ", "")
    s = re.sub(r"(\d)(?:[A-Z]\d+|[A-Z])$", r"\1", s)

    m = re.match(r"^(US)(19\d{2}|20\d{2})(\d+)$", s)
    if m:
        year = m.group(2)
        serial = str(int(m.group(3)))
        return f"US{year}{serial}"

    m = re.match(r"^(US)(\d+)$", s)
    if m:
        return f"US{int(m.group(2))}"

    return s


def npl_key(doc: str) -> str:
    """Normalize NPL citation text for duplicate matching."""
    s = doc.strip().lower()
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:240]


def _looks_like_patent(doc: str) -> bool:
    s = doc.strip().upper()
    return any(s.startswith(p) for p in _PATENT_PREFIXES) and bool(re.search(r"\d", s))


def normalize(doc: str) -> str:
    """Alias — patent numbers use patent_key; NPL uses npl_key."""
    if _looks_like_patent(doc):
        return patent_key(doc)
    return npl_key(doc)


def load_burned(study_id: str) -> dict[str, str]:
    """All known art — every CSV row is BURNED for surfacing to Angela.

    Copyright-research studies (hymn translations, etc.) have no patent
    known-art list, so they burn-check as empty rather than erroring.
    """
    folder = STUDY_DIRS.get(study_id)
    if not folder:
        raise SystemExit(f"Unknown study {study_id}. Use: {', '.join(STUDY_DIRS)}")
    known_art_dir = folder / "known_art"
    if not known_art_dir.exists():
        return {}
    csv_path = known_art_dir / "known_citations.csv"
    if not csv_path.exists():
        raise SystemExit(f"Missing {csv_path}")

    burned: dict[str, str] = {}
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            raw = row["Citation/Document Number"].strip()
            relation = row.get("Relation", "unknown")
            typ = row.get("Type", "")
            if typ == "NPL" or not _looks_like_patent(raw):
                key = npl_key(raw)
            else:
                key = patent_key(raw)
            burned[key] = relation
    return burned


def load_citation_seeds(study_id: str) -> list[str]:
    """Known citations to use as graph seeds (backward cite expansion) — not for surfacing."""
    folder = STUDY_DIRS[study_id]
    csv_path = folder / "known_art" / "known_citations.csv"
    seeds: list[str] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            raw = row["Citation/Document Number"].strip()
            rel = row.get("Relation", "")
            typ = row.get("Type", "")
            if typ != "Patent" or not _looks_like_patent(raw):
                continue
            if "Citation" in rel:
                seeds.append(raw)
    return list(dict.fromkeys(seeds))


def is_burned(doc: str, burned: dict[str, str]) -> tuple[bool, str]:
    """Return (True, relation) if doc matches ANY known-art entry."""
    if _looks_like_patent(doc):
        key = patent_key(doc)
        if key in burned:
            return True, burned[key]
        return False, ""

    key = npl_key(doc)
    if key in burned:
        return True, burned[key]

    # Title fuzzy: known NPL substring match
    doc_n = npl_key(doc)
    if len(doc_n) >= 20:
        for bkey, rel in burned.items():
            if len(bkey) >= 20 and (doc_n in bkey or bkey in doc_n):
                return True, rel
    return False, ""


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scripts/check_burned.py <study_id> <doc_number> [doc_number ...]")
        print("Example: python scripts/check_burned.py 26052 US11229891")
        raise SystemExit(1)

    study_id = sys.argv[1]
    burned = load_burned(study_id)

    for raw in sys.argv[2:]:
        hit, relation = is_burned(raw, burned)
        if hit:
            print(f"BURNED  {raw}  ({relation})")
        else:
            print(f"CLEAR   {raw}")


if __name__ == "__main__":
    main()