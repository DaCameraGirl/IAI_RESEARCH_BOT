#!/usr/bin/env python3
"""Autonomous patent hunt engine — citations, burn-check, score, draft candidates."""

from __future__ import annotations

import html as html_module
import re
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(REPO / "scripts"))
from check_burned import is_burned, load_burned, load_citation_seeds, patent_key  # noqa: E402
from link_builder import crossref_lookup, patent_links  # noqa: E402
from patent_search import search_queries  # noqa: E402
from study_bot import STUDY_META  # noqa: E402
from study_requirements import ctrl_f_phrases, map_requirements  # noqa: E402
from product_search import search_product_evidence  # noqa: E402

LogFn = Callable[[str, str], None]  # message, level

MAX_INSPECT = 500
HOLD_MIN_RANK = 1

# Lane depth — tuned for ULTRA-DEEP hunts
L1_CITE_LIMIT = 200
L2_HOP1_LIMIT = 100
L2_CITES_PER = 40
L2_HOP3_LIMIT = 50
L3_PER_QUERY = 50
L4_PER_QUERY = 35
L6_SEED_LIMIT = 80
L6_CITES_PER = 25

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_cache: dict[str, "PatentRecord"] = {}
_cache_lock = threading.Lock()


@dataclass
class PatentRecord:
    pub_id: str
    title: str = ""
    assignee: str = ""
    inventors: str = ""
    priority_date: str = ""
    publication_date: str = ""
    abstract: str = ""
    url: str = ""
    pdf_url: str = ""
    uspto_url: str = ""
    uspto_pdf_url: str = ""
    espacenet_url: str = ""
    doi: str = "n/a"
    cpc: str = ""
    source_lane: str = ""
    req_rows: list[dict] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    score: int = 0
    matched_keywords: list[str] = field(default_factory=list)
    burned: bool = False
    burn_relation: str = ""
    self_rank: int = 0
    confidence: str = "low"
    ready: bool = False


def _fetch_html(url: str) -> str:
    # Rate limit: 1.5 second delay between requests to avoid 503 errors
    time.sleep(1.5)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", "replace")


def _normalize_pub(pub: str) -> str:
    pub = pub.strip().upper()
    if not pub.startswith(("US", "EP", "WO", "CN", "JP", "KR")):
        pub = "US" + pub
    return pub


def _extract_patent_ids(html: str) -> list[str]:
    ids = re.findall(r"/patent/([A-Z]{2}\d+[A-Z]?\d?)/", html)
    return list(dict.fromkeys(ids))


def fetch_patent(pub_id: str) -> PatentRecord:
    pub_id = _normalize_pub(pub_id)
    with _cache_lock:
        if pub_id in _cache:
            return _cache[pub_id]

    url = f"https://patents.google.com/patent/{pub_id}"
    rec = PatentRecord(pub_id=pub_id, url=url)
    try:
        html = _fetch_html(url)
    except (urllib.error.URLError, TimeoutError) as exc:
        rec.title = f"(fetch failed: {exc})"
        return rec

    title_m = re.search(r'<meta name="DC.title" content="([^"]+)"', html)
    if title_m:
        rec.title = re.sub(r"\s+", " ", title_m.group(1)).strip()

    pri_m = re.search(r'<time itemprop="priorityDate" datetime="([^"]+)"', html)
    if pri_m:
        rec.priority_date = pri_m.group(1)[:10]

    pub_m = re.search(r'<time itemprop="publicationDate" datetime="([^"]+)"', html)
    if pub_m:
        rec.publication_date = pub_m.group(1)[:10]

    abs_m = re.search(
        r'<meta name="DC.description" content="([^"]+)"', html
    ) or re.search(r'itemprop="description"[^>]*>([^<]{40,})', html)
    if abs_m:
        rec.abstract = re.sub(r"\s+", " ", abs_m.group(1)).strip()[:1200]

    inv_m = re.findall(r'itemprop="inventor"[^>]*>.*?itemprop="name"[^>]*>([^<]+)', html, re.S)
    if inv_m:
        rec.inventors = html_module.unescape(
            ", ".join(dict.fromkeys(i.strip() for i in inv_m[:8]))
        )

    rec.assignee = _extract_assignee(html)
    cpc_parts = re.findall(r'itemprop="Code"[^>]*>([^<]+)', html)
    if cpc_parts:
        rec.cpc = " / ".join(cpc_parts[-4:])

    rec.citations = _extract_patent_ids(html)
    links = patent_links(pub_id, html=html)
    rec.url = links["google"]
    rec.pdf_url = links["pdf"]
    rec.uspto_url = links["uspto"]
    rec.uspto_pdf_url = links["uspto_pdf"]
    rec.espacenet_url = links["espacenet"]
    rec.doi = links["doi"]
    with _cache_lock:
        _cache[pub_id] = rec
    return rec


_BAD_ASSIGNEE = {"engineering & computer science", "engineering and computer science"}


def _extract_assignee(html: str) -> str:
    candidates: list[str] = []
    for pat in (
        r'itemprop="assignee[^"]*"[^>]*>.*?itemprop="name"[^>]*>([^<]+)',
        r'>([A-Z][^<]{2,60}(?:Corp\.?|Inc\.?|Ltd\.?|LLC|GmbH|Systems|Corporation)[^<]*)</',
    ):
        for m in re.findall(pat, html, re.S | re.I):
            clean = html_module.unescape(re.sub(r"\s+", " ", m).strip())
            if clean.lower() not in _BAD_ASSIGNEE and len(clean) > 2:
                candidates.append(clean)
    return candidates[0] if candidates else "(verify assignee in PDF)"


def _parse_critical_date(study_id: str) -> str | None:
    raw = STUDY_META[study_id]["critical_date"]
    m = re.search(r"(\d{4}-\d{2}-\d{2})", raw)
    return m.group(1) if m else None


def score_record(rec: PatentRecord, study_id: str) -> PatentRecord:
    keywords = STUDY_META[study_id]["keywords"]
    text = f"{rec.title} {rec.abstract}"
    text_l = text.lower()
    matched = [k for k in keywords if k.lower() in text_l]
    rec.matched_keywords = matched
    rec.req_rows = map_requirements(study_id, text)
    yes_count = sum(1 for r in rec.req_rows if r["select"] == "yes")
    maybe_count = sum(1 for r in rec.req_rows if r["select"] == "maybe")
    rec.score = yes_count * 3 + maybe_count

    priority_ids = STUDY_META[study_id]["priority_req_ids"]
    priority_yes = sum(
        1 for r in rec.req_rows if r["id"] in priority_ids and r["select"] == "yes"
    )

    if yes_count >= 4:
        rec.self_rank = 3
    elif yes_count >= 2:
        rec.self_rank = 2
    elif yes_count >= 1 or maybe_count >= 4:
        rec.self_rank = 1
    else:
        rec.self_rank = 0

    if yes_count >= 3:
        rec.confidence = "high"
    elif yes_count >= 1:
        rec.confidence = "med"
    else:
        rec.confidence = "low"

    rec.ready = (
        not rec.burned
        and rec.self_rank >= 1
        and (yes_count >= 1 or maybe_count >= 2)
        and rec.confidence in ("high", "med")
    )
    return rec


def burn_check(rec: PatentRecord, study_id: str, burned: dict[str, str]) -> PatentRecord:
    for probe in (rec.pub_id, rec.title):
        if not probe:
            continue
        hit, relation = is_burned(probe, burned)
        if hit:
            rec.burned = True
            rec.burn_relation = relation
            rec.ready = False
            break
    return rec


def is_study_patent(rec: PatentRecord, study_id: str) -> bool:
    study_pub = patent_key(STUDY_META[study_id]["patent"])
    return patent_key(rec.pub_id) == study_pub


def date_ok(rec: PatentRecord, critical: str | None) -> bool:
    if not critical:
        return True
    d = rec.priority_date or rec.publication_date
    if not d:
        return True
    return d <= critical


def _req_table(rows: list[dict]) -> str:
    lines = ["| Requirement | Select? | Why |", "|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} {r['name'][:42]} | {r['select']} | {r['why']} |")
    return "\n".join(lines)


def draft_candidate(rec: PatentRecord, study_id: str) -> str:
    pdf_line = rec.pdf_url or rec.uspto_pdf_url or rec.url
    phrases = ctrl_f_phrases(rec.abstract or rec.title, rec.matched_keywords, limit=6)
    yes_reqs = [r for r in rec.req_rows if r["select"] == "yes"]
    no_reqs = [r for r in rec.req_rows if r["select"] == "no"][:5]
    highlights = yes_reqs[:3] if yes_reqs else rec.req_rows[:2]

    req_table = _req_table(rec.req_rows)
    req_table += (
        f"\n| 2 Date of document | yes | Priority {rec.priority_date or '?'} — confirm on PDF |"
    )

    phrase_block = "\n".join(f'  - "{p}"' for p in phrases)
    highlight_block = "\n".join(
        f"  - Requirement {h['id']}: \"(open PDF — search: {h['hits'][0] if h['hits'] else 'keyword'})\""
        for h in highlights
    )
    dont_block = "\n".join(
        f"  - {r['id']} — {r['why']}" for r in no_reqs
    ) or "  - (none flagged — still verify each req in claims)"

    adversarial = (
        f"Verify verbatim anchors in PDF before submit. "
        f"{len(yes_reqs)} requirements auto-yes from abstract keywords."
    )

    return f"""Dropdown: Patent
Downloadable PDF: yes + {pdf_line}

Self-rank: {rec.self_rank}/3
In-scope confidence: {rec.confidence}
(Bot: surface to Angela only if Self-rank ≥ 2, confidence high, ≥2 req-yes, priority RR hit.)

Form fields:
  publication: {rec.pub_id}
  title: {rec.title}
  assignee: {rec.assignee}
  inventors: {rec.inventors}
  publication date: {rec.publication_date}
  priority date: {rec.priority_date or 'not found'}
  CPC: {rec.cpc or 'not found'}
  DOI: {rec.doi}
  URL: {rec.url}
  PDF URL: {rec.pdf_url or 'not found'}
  USPTO URL: {rec.uspto_url or 'not found'}
  USPTO PDF: {rec.uspto_pdf_url or 'not found'}
  Espacenet URL: {rec.espacenet_url or 'not found'}

Select these requirements:
{req_table}

Ctrl+F phrases (test in PDF before submit):
{phrase_block}

Highlight only this:
{highlight_block}

Do NOT select:
{dont_block}

Coverage score: {len(yes_reqs)} of {len(rec.req_rows)} reqs auto-yes from abstract (verify claims)
Adversarial note: {adversarial}
Notes:
  - Burn check: python scripts/check_burned.py {study_id} {rec.pub_id} → {'BURNED' if rec.burned else 'CLEAR'}
  - Source lane: {rec.source_lane or 'unknown'}
  - Matched keywords: {', '.join(rec.matched_keywords) or 'none'}
  - Hunt engine draft {datetime.now().strftime('%Y-%m-%d %H:%M')} — Angela must verify all PDF anchors
"""


def regrade_stored_candidates(study_id: str, burned: dict[str, str] | None = None) -> int:
    """Demote on-disk READY files that fail the stricter gate → HOLD."""
    burned = burned or load_burned(study_id)
    folder = REPO / STUDY_META[study_id]["folder"] / "candidates"
    if not folder.exists():
        return 0
    demoted = 0
    for path in list(folder.glob("*_RWS_format.txt")):
        if path.name.startswith("HOLD_") or path.name.startswith("NPL_"):
            continue
        pub_id = path.name.replace("_RWS_format.txt", "")
        try:
            rec = fetch_patent(pub_id)
        except Exception:
            continue
        rec = burn_check(rec, study_id, burned)
        if rec.burned:
            path.unlink(missing_ok=True)
            demoted += 1
            continue
        rec = score_record(rec, study_id)
        if rec.ready:
            path.write_text(draft_candidate(rec, study_id), encoding="utf-8")
            continue
        hold_path = folder / f"HOLD_{patent_key(rec.pub_id)}_RWS_format.txt"
        if hold_path.exists():
            path.unlink(missing_ok=True)
        else:
            path.rename(hold_path)
        hold_path.write_text(draft_candidate(rec, study_id), encoding="utf-8")
        demoted += 1
    return demoted


class HuntEngine:
    def __init__(self, study_id: str, on_log: LogFn | None = None) -> None:
        self.study_id = study_id
        self.on_log = on_log or (lambda m, l: None)
        self.stopped = False
        self.results: list[PatentRecord] = []
        self.inspected = 0
        self.lanes_done: list[str] = []

    def log(self, msg: str, level: str = "info") -> None:
        self.on_log(msg, level)

    def stop(self) -> None:
        self.stopped = True

    def _queue_add(
        self,
        queue: list[tuple[str, str]],
        seen: set[str],
        pub: str,
        source: str,
        burned: dict[str, str],
    ) -> bool:
        """Add to inspect queue only if NOT already known art."""
        key = patent_key(pub)
        if key in seen:
            return False
        hit, _rel = is_burned(pub, burned)
        if hit:
            return False
        seen.add(key)
        queue.append((pub, source))
        return True

    def run_deep(self) -> dict:
        meta = STUDY_META[self.study_id]
        folder = REPO / meta["folder"]

        if meta.get("type") == "copyright" or not meta.get("patent"):
            self.log(
                f"{self.study_id} is a copyright-research study (no study patent) — "
                "the patent citation-graph hunt doesn't apply here. Work this study "
                "manually per its STUDY_BRIEF.md.",
                "warn",
            )
            return {"ready": 0, "inspected": 0, "note": "copyright-research study — no patent hunt to run"}

        critical = _parse_critical_date(self.study_id)
        critical_compact = critical.replace("-", "") if critical else None
        burned = load_burned(self.study_id)
        study_patent = meta["patent"]
        if not study_patent.startswith(("US", "EP", "WO")):
            study_patent = "US" + study_patent

        self.log(f"Starting DEEP hunt for {self.study_id} — {meta['title']}", "phase")
        self.log(
            f"Critical date ≤ {critical or 'unknown'} · {len(burned)} burned keys · "
            f"max inspect {MAX_INSPECT} · burn gate ON · strict READY (high + ≥2 req-yes)",
            "info",
        )

        seen: set[str] = set()  # patent_key dedupe
        queue: list[tuple[str, str]] = []
        burned_skipped = 0

        # L1 — study patent backward citations (full list)
        self.log("L1: Study patent backward citations", "lane")
        root = fetch_patent(study_patent)
        time.sleep(0.35)
        for cite in root.citations[:L1_CITE_LIMIT]:
            if is_burned(cite, burned)[0]:
                burned_skipped += 1
            elif not self._queue_add(queue, seen, cite, "L1-backward-cite", burned):
                burned_skipped += 1
        self.lanes_done.append("L1")

        # L2 — 2-hop citation expansion
        self.log("L2: Citation graph 2-hop", "lane")
        hop1 = [p for p, s in queue if s.startswith("L1")][:L2_HOP1_LIMIT]
        hop2: list[str] = []
        for pub in hop1:
            if self.stopped:
                break
            rec = fetch_patent(pub)
            time.sleep(0.25)
            for cite in rec.citations[:L2_CITES_PER]:
                if self._queue_add(queue, seen, cite, f"L2-via-{pub}", burned):
                    hop2.append(cite)
        self.log(f"  L2 hop-1: {len(hop1)} parents · {len(hop2)} new cites queued", "info")
        self.lanes_done.append("L2")

        # L2b — 3-hop citation graph (deeper backward expansion)
        self.log("L2b: Citation graph 3-hop", "lane")
        for pub in hop2[:L2_HOP3_LIMIT]:
            if self.stopped:
                break
            rec = fetch_patent(pub)
            time.sleep(0.2)
            for cite in rec.citations[:12]:
                self._queue_add(queue, seen, cite, f"L2b-via-{pub}", burned)
        self.lanes_done.append("L2b")

        # L3 — assignee pre-date search
        self.log("L3: Assignee sweep (Google Patents search)", "lane")
        for asn in STUDY_META[self.study_id]["assignees"]:
            q = f'assignee:"{asn}"'
            hits = search_queries([q], before_priority=critical_compact, per_query=L3_PER_QUERY, pause=0.55)
            self.log(f"  {asn}: {len(hits)} pre-date hits", "info")
            for pub, _ in hits:
                self._queue_add(queue, seen, pub, f"L3-assignee-{asn}", burned)
        self.lanes_done.append("L3")

        # L4 — synonym lattice (12 queries)
        self.log("L4: Synonym lattice searches", "lane")
        queries = STUDY_META[self.study_id]["synonym_queries"]
        syn_hits = search_queries(queries, before_priority=critical_compact, per_query=L4_PER_QUERY, pause=0.4)
        self.log(f"  Synonym lattice: {len(syn_hits)} unique hits", "info")
        for pub, q in syn_hits:
            self._queue_add(queue, seen, pub, f"L4-syn:{q[:30]}", burned)
        self.lanes_done.append("L4")

        # L4b — CPC / classification targeted searches
        cpc_queries = STUDY_META[self.study_id]["cpc_queries"]
        if cpc_queries:
            self.log("L4b: CPC / classification searches", "lane")
            cpc_hits = search_queries(cpc_queries, before_priority=critical_compact, per_query=15, pause=0.45)
            self.log(f"  CPC lattice: {len(cpc_hits)} unique hits", "info")
            for pub, q in cpc_hits:
                self._queue_add(queue, seen, pub, f"L4b-cpc:{q[:24]}", burned)
            self.lanes_done.append("L4b")

        # L5 — NPL Crossref adjacent
        self.log("L5: NPL adjacent (Crossref)", "lane")
        npl_written = self._hunt_npl(folder, critical, burned)
        self.lanes_done.append("L5")

        # L6 — expand backward cites FROM known citations (seeds only — never resurface)
        self.log("L6: Known-citation graph seeds (find NEW art via old cites)", "lane")
        burned_skipped += self._expand_known_citation_seeds(queue, seen, burned)
        self.lanes_done.append("L6")

        # L7 — Product evidence search (Archive.org, YouTube, Reddit, Wayback)
        self.log("L7: Product evidence (Archive.org, YouTube, Reddit, Wayback)", "lane")
        product_hits = self._hunt_product_evidence(folder, critical, burned)
        self.log(f"  Product search: {product_hits} candidate sources found", "info")
        self.lanes_done.append("L7")

        self.log(
            f"Burn filter: {burned_skipped} known citations blocked from queue · "
            f"{len(queue)} NEW docs to inspect",
            "info",
        )
        self.log(f"Inspecting {len(queue)} queued patent documents…", "phase")
        ready: list[PatentRecord] = []
        hold: list[PatentRecord] = []

        queue.sort(key=lambda x: (0 if x[1].startswith("L4") else 1, x[1]))
        self.log(f"Queue sorted — inspecting up to {min(len(queue), MAX_INSPECT)} of {len(queue)} docs", "info")

        for pub, source in queue:
            if self.stopped:
                self.log("Hunt stopped by user", "warn")
                break
            if self.inspected >= MAX_INSPECT:
                self.log(f"Inspection cap {MAX_INSPECT} reached", "warn")
                break

            rec = fetch_patent(pub)
            time.sleep(0.2)
            rec.source_lane = source
            rec = burn_check(rec, self.study_id, burned)
            self.inspected += 1
            if self.inspected % 25 == 0:
                self.log(
                    f"… progress {self.inspected}/{min(len(queue), MAX_INSPECT)} inspected · "
                    f"{len(ready)} READY · {len(hold)} HOLD so far",
                    "info",
                )

            if is_study_patent(rec, self.study_id):
                self.log(f"SKIP {pub} — study patent", "skip")
                continue
            if rec.burned:
                self.log(f"SKIP {pub} — burned ({rec.burn_relation})", "skip")
                continue
            if not date_ok(rec, critical):
                self.log(f"SKIP {pub} — after critical date ({rec.priority_date})", "skip")
                continue

            rec = score_record(rec, self.study_id)
            self.results.append(rec)

            status = "READY" if rec.ready else f"rank {rec.self_rank}/{rec.confidence}"
            self.log(
                f"{'★' if rec.ready else '·'} {pub} — {rec.title[:50]}… [{status}] "
                f"req_yes={sum(1 for r in rec.req_rows if r['select']=='yes')} via {source}",
                "hit" if rec.ready else "info",
            )

            if rec.ready:
                if self._safe_to_surface(rec, burned):
                    ready.append(rec)
                    self._write_candidate(folder, rec, ready=True, burned=burned)
                else:
                    self.log(f"BLOCKED write {pub} — known art (hard gate)", "skip")
            elif rec.self_rank >= HOLD_MIN_RANK or (rec.confidence == "med" and rec.self_rank >= 1):
                if self._safe_to_surface(rec, burned):
                    hold.append(rec)
                    self._write_candidate(folder, rec, ready=False, burned=burned)
                else:
                    self.log(f"BLOCKED hold {pub} — known art (hard gate)", "skip")
            elif rec.score > 0:
                self.log(
                    f"  ↳ {pub} — weak ({rec.self_rank}/{rec.confidence}, "
                    f"yes={sum(1 for r in rec.req_rows if r['select']=='yes')})",
                    "skip",
                )

        demoted = regrade_stored_candidates(self.study_id, burned)
        if demoted:
            self.log(f"Regraded {demoted} prior READY file(s) → HOLD (stricter gate)", "info")

        self._update_candidate_screen(folder, ready, hold)
        self._update_hunt_log(folder)
        self.log(
            f"Hunt complete — inspected {self.inspected}, "
            f"{len(ready)} READY, {len(hold)} HOLD, {npl_written} NPL leads",
            "done" if ready else "phase",
        )
        return {
            "inspected": self.inspected,
            "ready": len(ready),
            "hold": len(hold),
            "npl": npl_written,
            "results": [self._rec_dict(r) for r in sorted(self.results, key=lambda x: -x.score)],
        }

    def _safe_to_surface(self, rec: PatentRecord, burned: dict[str, str] | None = None) -> bool:
        """Hard gate: never write a known citation to Angela's inbox."""
        burned = burned or load_burned(self.study_id)
        if rec.burned or is_burned(rec.pub_id, burned)[0]:
            return False
        if is_burned(rec.title, burned)[0]:
            return False
        if is_study_patent(rec, self.study_id):
            return False
        return True

    def _expand_known_citation_seeds(
        self,
        queue: list[tuple[str, str]],
        seen: set[str],
        burned: dict[str, str],
    ) -> int:
        """Use known citations as graph seeds; only NEW backward cites enter queue."""
        skipped = 0
        seeds = load_citation_seeds(self.study_id)
        self.log(f"  {len(seeds)} known citations as seeds — mining their backward cites", "info")
        for raw in seeds[:L6_SEED_LIMIT]:
            pub = _normalize_pub(raw)
            try:
                rec = fetch_patent(pub)
                time.sleep(0.2)
            except Exception:
                continue
            for cite in rec.citations[:L6_CITES_PER]:
                if is_burned(cite, burned)[0]:
                    skipped += 1
                elif not self._queue_add(queue, seen, cite, f"L6-seed-{pub}", burned):
                    skipped += 1
        return skipped

    def _hunt_npl(self, folder: Path, critical: str | None, burned: dict[str, str]) -> int:
        queries = STUDY_META[self.study_id]["npl_queries"]
        if not queries:
            return 0
        year = critical[:4] if critical else None
        cand_dir = folder / "candidates"
        cand_dir.mkdir(exist_ok=True)
        written = 0
        for q in queries:
            if self.stopped:
                break
            meta = crossref_lookup(q, year=year, before=critical)
            if meta.get("doi") in ("not found", "", None):
                continue
            doi = meta.get("doi", "")
            if is_burned(doi, burned)[0]:
                self.log(f"  SKIP NPL DOI burned: {doi}", "skip")
                continue
            if is_burned(q, burned)[0]:
                continue
            safe = re.sub(r"[^A-Za-z0-9]+", "_", q)[:40]
            path = cand_dir / f"NPL_{safe}_RWS_format.txt"
            text = f"""Dropdown: NPL -> Article
Downloadable PDF: yes + {meta.get('url') or 'check Unpaywall / school login'}
Access: open | school

Self-rank: 1/3
In-scope confidence: med
(Bot: NPL lead — verify PDF + in-scope before surfacing to Angela.)

Form fields:
  title: (Crossref lead for query: {q})
  authors: not found
  journal: {meta.get('journal') or 'not found'}
  DOI: {meta.get('doi')}
  ISSN: not found
  publisher: not found
  date: ≤ {critical or 'critical date'}
  URL: {meta.get('url') or 'not found'}

Select these requirements:
| Requirement | Select? | Why |
|---|---|---|
| (map after PDF read) | maybe | NPL lead only — read full text |

Ctrl+F phrases:
  - (search PDF after download)

Highlight only this:
  - Requirement : (anchor after PDF read)

Do NOT select:
  - All reqs until PDF verified

Notes:
  - NPL adjacent lead from Crossref query: {q}
  - Hunt engine {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
            path.write_text(text, encoding="utf-8")
            written += 1
            self.log(f"  NPL lead: {meta['doi']} ({q[:40]})", "info")
            time.sleep(0.3)
        return written


    def _hunt_product_evidence(self, folder: Path, critical: str | None, burned: dict[str, str]) -> int:
        """Search Archive.org, YouTube, Reddit, Wayback for product evidence."""
        if not critical:
            return 0
        
        # Extract keywords from study metadata
        meta = STUDY_META[self.study_id]
        product_keywords = []
        technical_terms = []
        
        # Extract from title and description
        title_lower = meta["title"].lower()
        if "blender" in title_lower:
            product_keywords.extend(["blender", "food processor", "mixer"])
            technical_terms.extend(["offset blade", "eccentric rotor", "tornado effect", "vortex mixing"])
        elif "battery" in title_lower or "rechargeable" in title_lower:
            product_keywords.append("rechargeable")
        
        # Add generic terms from synonym queries
        for q in meta.get("synonym_queries", [])[:5]:
            terms = q.lower().split()
            for term in terms:
                if len(term) > 4 and term not in ["patent", "prior", "device"]:
                    if term not in technical_terms:
                        technical_terms.append(term)
        
        if not product_keywords:
            product_keywords = ["product", "device"]
        
        # Search product sources
        try:
            results = search_product_evidence(
                product_keywords=product_keywords[:3],
                technical_terms=technical_terms[:5],
                before_date=critical,
                max_per_source=10,
                log_fn=self.log,
            )
        except Exception as e:
            self.log(f"Product search error: {e}", "warn")
            return 0
        
        # Write candidates
        cand_dir = folder / "candidates"
        cand_dir.mkdir(exist_ok=True)
        written = 0
        
        # Archive.org results
        for item in results.get("archive_org", [])[:15]:
            if is_burned(item["identifier"], burned)[0]:
                continue
            safe_title = re.sub(r"[^\w]+", "_", item["title"][:40])
            path = cand_dir / f"PRODUCT_archive_{safe_title}_RWS_format.txt"
            content = self._draft_product_candidate(item, "Archive.org", critical)
            path.write_text(content, encoding="utf-8")
            written += 1
            self.log(f"  Product: {item['title'][:50]} (Archive.org {item['year']})", "info")
        
        # YouTube results
        for item in results.get("youtube", [])[:10]:
            if is_burned(item["video_id"], burned)[0]:
                continue
            safe_title = re.sub(r"[^\w]+", "_", item["title"][:40])
            path = cand_dir / f"PRODUCT_youtube_{safe_title}_RWS_format.txt"
            content = self._draft_product_candidate(item, "YouTube", critical)
            path.write_text(content, encoding="utf-8")
            written += 1
            self.log(f"  Product: {item['title'][:50]} (YouTube {item['published_date']})", "info")
        
        # Reddit results
        for item in results.get("reddit", [])[:10]:
            if is_burned(item["url"], burned)[0]:
                continue
            safe_title = re.sub(r"[^\w]+", "_", item["title"][:40])
            path = cand_dir / f"PRODUCT_reddit_{safe_title}_RWS_format.txt"
            content = self._draft_product_candidate(item, "Reddit", critical)
            path.write_text(content, encoding="utf-8")
            written += 1
            self.log(f"  Product: {item['title'][:50]} (Reddit {item['created_date']})", "info")
        
        # Wayback results (sample only - too many snapshots)
        wayback_items = results.get("wayback", [])
        if wayback_items:
            # Group by domain and take earliest snapshot per domain
            by_domain = {}
            for item in wayback_items:
                domain = item["original_url"].split("/")[0]
                if domain not in by_domain or item["date"] < by_domain[domain]["date"]:
                    by_domain[domain] = item
            
            for domain, item in list(by_domain.items())[:5]:
                safe_domain = re.sub(r"[^\w]+", "_", domain)
                path = cand_dir / f"PRODUCT_wayback_{safe_domain}_{item['date']}_RWS_format.txt"
                content = self._draft_product_candidate(item, "Wayback Machine", critical)
                path.write_text(content, encoding="utf-8")
                written += 1
                self.log(f"  Product: {domain} snapshot ({item['date']})", "info")
        
        # MusicBrainz results (recordings - perfect for hymns)
        for item in results.get("musicbrainz", [])[:10]:
            if is_burned(item["recording_id"], burned)[0]:
                continue
            safe_title = re.sub(r"[^\w]+", "_", item["title"][:40])
            path = cand_dir / f"MUSIC_musicbrainz_{safe_title}_RWS_format.txt"
            content = self._draft_music_candidate(item, "MusicBrainz", critical)
            path.write_text(content, encoding="utf-8")
            written += 1
            self.log(f"  Music: {item['title'][:50]} by {item['artist']} ({item['release_date']})", "info")
        
        # Discogs results (album releases)
        for item in results.get("discogs", [])[:10]:
            if is_burned(item["url"], burned)[0]:
                continue
            safe_title = re.sub(r"[^\w]+", "_", item["title"][:40])
            path = cand_dir / f"MUSIC_discogs_{safe_title}_RWS_format.txt"
            content = self._draft_music_candidate(item, "Discogs", critical)
            path.write_text(content, encoding="utf-8")
            written += 1
            self.log(f"  Music: {item['title'][:50]} ({item['year']}, {item['format']})", "info")
        
        return written

    def _draft_product_candidate(self, item: dict, source: str, critical: str) -> str:
        """Draft a product evidence candidate in RWS format."""
        lines = [
            "Type: Product Evidence / NPL",
            f"Source: {source}",
            f"Title: {item.get('title', 'Unknown')}",
            f"URL: {item.get('url', 'N/A')}",
            f"Date: {item.get('year', item.get('date', item.get('published_date', item.get('created_date', 'unknown'))))}",
            f"Critical Date: ≤ {critical}",
            "",
            "Status: UNVERIFIED — manually review source, verify date, extract technical details, take screenshots",
            "",
            "Description:",
            item.get("description", item.get("selftext", "No description available"))[:300],
            "",
            "Next Steps:",
            "1. Visit URL and verify content is accessible",
            "2. Confirm publication/creation date is before critical date",
            "3. Extract technical specifications (blade offset, dimensions, etc.)",
            "4. Take screenshots showing relevant technical details",
            "5. Map to study requirements",
            "6. If valid, format as proper RWS submission with screenshots",
            "",
            f"Hunt engine {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ]
        return "\n".join(lines)

    def _draft_music_candidate(self, item: dict, source: str, critical: str) -> str:
        """Draft a music recording candidate in RWS format (for hymn research)."""
        lines = [
            "Type: Music Recording / NPL",
            f"Source: {source}",
            f"Title: {item.get('title', 'Unknown')}",
            f"Artist: {item.get('artist', 'Unknown')}",
            f"URL: {item.get('url', 'N/A')}",
            f"Release Date: {item.get('release_date', item.get('year', 'unknown'))}",
            f"Critical Date: ≤ {critical}",
            "",
        ]
        
        # Add source-specific details
        if source == "MusicBrainz":
            lines.append(f"Recording ID: {item.get('recording_id', 'N/A')}")
        elif source == "Discogs":
            lines.extend([
                f"Format: {item.get('format', 'Unknown')}",
                f"Label: {item.get('label', 'Unknown')}",
            ])
        
        lines.extend([
            "",
            "Status: UNVERIFIED — manually review recording, verify release date, confirm hymn matches study",
            "",
            "Next Steps:",
            "1. Visit URL and listen to recording (if available)",
            "2. Confirm release date is before critical date",
            "3. Verify hymn title and language match study requirements",
            "4. Check for lyrics/sheet music in description or linked resources",
            "5. Take screenshots of recording metadata (title, artist, date)",
            "6. If valid, format as proper RWS submission with evidence",
            "",
            f"Hunt engine {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ])
        return "\n".join(lines)

    def _rec_dict(self, rec: PatentRecord) -> dict:
        return {
            "pub_id": rec.pub_id,
            "title": rec.title,
            "assignee": rec.assignee,
            "priority_date": rec.priority_date,
            "score": rec.score,
            "self_rank": rec.self_rank,
            "confidence": rec.confidence,
            "ready": rec.ready,
            "burned": rec.burned,
            "keywords": rec.matched_keywords,
            "url": rec.url,
        }

    def _write_candidate(
        self, folder: Path, rec: PatentRecord, ready: bool = True, burned: dict[str, str] | None = None
    ) -> None:
        if not self._safe_to_surface(rec, burned):
            self.log(f"REFUSED write {rec.pub_id} — known art", "error")
            return
        cand_dir = folder / "candidates"
        cand_dir.mkdir(exist_ok=True)
        safe = patent_key(rec.pub_id)
        prefix = "" if ready else "HOLD_"
        path = cand_dir / f"{prefix}{safe}_RWS_format.txt"
        path.write_text(draft_candidate(rec, self.study_id), encoding="utf-8")
        tier = "READY" if ready else "HOLD"
        self.log(f"Wrote {tier} → {path.name}", "success")

    def _update_candidate_screen(
        self, folder: Path, ready: list[PatentRecord], hold: list[PatentRecord]
    ) -> None:
        screen = folder / "CANDIDATE_SCREEN.md"
        today = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"# Candidate Screen — updated {today}",
            "",
            f"Inspected: {self.inspected} · READY: {len(ready)} · HOLD: {len(hold)}",
            "",
            "## READY (Self-rank ≥2, high/med)",
            "",
        ]
        if ready:
            for r in sorted(ready, key=lambda x: -x.score):
                lines.append(
                    f"- **{r.pub_id}** — {r.title[:70]} · "
                    f"[PDF]({r.pdf_url}) · [Google]({r.url}) · lane {r.source_lane}"
                )
        else:
            lines.append("- (none this round)")
        lines += ["", "## HOLD (rank 1 — verify before surfacing)", ""]
        if hold:
            for r in sorted(hold, key=lambda x: -x.score)[:15]:
                lines.append(f"- {r.pub_id} — {r.title[:60]} · rank {r.self_rank}")
        else:
            lines.append("- (none)")
        screen.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _update_hunt_log(self, folder: Path) -> None:
        log_path = folder / "HUNT_LOG.md"
        today = datetime.now().strftime("%Y-%m-%d")
        ready = sum(1 for r in self.results if r.ready)
        row = (
            f"| {today} | {', '.join(self.lanes_done[:4])} | {self.inspected} | "
            f"{ready} | continue |"
        )
        if log_path.exists():
            text = log_path.read_text(encoding="utf-8")
            if "— | — | — | — | — |" in text:
                text = text.replace(
                    "| — | — | — | — | — |",
                    row,
                    1,
                )
            else:
                text = text.replace(
                    "|------|-----------------|----------------|---------------------|-----------|",
                    "|------|-----------------|----------------|---------------------|-----------|\n" + row,
                    1,
                )
            # tick lanes — match by lane number only, so wording can differ per study
            for i in range(1, 8):
                if f"L{i}" in str(self.lanes_done):
                    text = re.sub(rf"(?m)^- \[ \] (L{i}\b.*)$", r"- [x] \1", text, count=1)
            log_path.write_text(text, encoding="utf-8")