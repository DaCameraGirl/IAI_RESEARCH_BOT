#!/usr/bin/env python3
"""Requirement mapping helpers for thorough candidate drafting.

Per-study keyword/requirement data lives in each study's own
STUDY_META.json (see study_bot.py), not hardcoded here — that's what lets
add_study.py onboard a new study without touching this file.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from study_bot import STUDY_META  # noqa: E402


def map_requirements(study_id: str, text: str) -> list[dict[str, str]]:
    """Return requirement rows with select/why for drafting."""
    text_l = text.lower()
    rows = []
    for req in STUDY_META[study_id]["requirements"]:
        hits = [k for k in req["keywords"] if k.lower() in text_l]
        if len(hits) >= 2:
            select, why = "yes", f"Abstract/title mentions: {', '.join(hits[:3])}"
        elif len(hits) == 1:
            select, why = "maybe", f"Weak signal — verify in PDF: {hits[0]}"
        else:
            select, why = "no", "No keyword hit in title/abstract — check claims manually"
        rows.append({"id": req["id"], "name": req["name"], "select": select, "why": why, "hits": hits})
    return rows


def ctrl_f_phrases(text: str, keywords: list[str], limit: int = 6) -> list[str]:
    """Pull Ctrl+F phrases from abstract sentences containing keywords."""
    phrases: list[str] = []
    sentences = re_split_sentences(text)
    for sent in sentences:
        sl = sent.lower()
        if any(k.lower() in sl for k in keywords):
            clean = " ".join(sent.split())
            if 20 <= len(clean) <= 220:
                phrases.append(clean)
        if len(phrases) >= limit:
            break
    if not phrases and text:
        phrases.append(text[:180].strip() + ("…" if len(text) > 180 else ""))
    return phrases[:limit]


def re_split_sentences(text: str) -> list[str]:
    import re

    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) > 15]
