#!/usr/bin/env python3
"""Google Patents search via XHR API."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _extract_ids_from_results(data: dict) -> list[str]:
    text = json.dumps(data)
    raw = re.findall(r"([A-Z]{2}\d{4,}[A-Z]?\d?)", text)
    out: list[str] = []
    seen: set[str] = set()
    for rid in raw:
        if rid.startswith("US0") and len(rid) > 10 and not rid[-2:].startswith(("A", "B")):
            rid = "US" + rid.lstrip("US").lstrip("0")
        if len(rid) < 6:
            continue
        # prefer kind-coded publication ids
        if rid in seen:
            continue
        base = re.sub(r"(\d)[A-Z]\d+$", r"\1", rid)
        if any(x.endswith(("A1", "B1", "B2")) for x in seen if re.sub(r"(\d)[A-Z]\d+$", r"\1", x) == base):
            continue
        seen.add(rid)
        out.append(rid)
    return out


def google_patents_search(
    query: str,
    before_priority: str | None = None,
    num: int = 25,
) -> list[str]:
    """Search Google Patents; returns publication IDs."""
    q = query.replace(" ", "+")
    inner = f"q={q}&num={num}"
    if before_priority:
        inner += f"&before=priority:{before_priority.replace('-', '')}"
    url = f"https://patents.google.com/xhr/query?url={urllib.parse.quote(inner)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    return _extract_ids_from_results(data)


def search_queries(
    queries: list[str],
    before_priority: str | None = None,
    per_query: int = 15,
    pause: float = 0.5,
) -> list[tuple[str, str]]:
    """Run multiple queries; returns (pub_id, query) pairs."""
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for q in queries:
        ids = google_patents_search(q, before_priority=before_priority, num=per_query)
        for pub in ids:
            if pub not in seen:
                seen.add(pub)
                found.append((pub, q))
        time.sleep(pause)
    return found