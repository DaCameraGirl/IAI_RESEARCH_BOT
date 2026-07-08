#!/usr/bin/env python3
"""
One-at-a-time study bot runner for RWS_RESEARCHER.

Usage:
  python scripts/study_bot.py              # show current study + agent orders
  python scripts/study_bot.py status       # queue overview
  python scripts/study_bot.py advance      # finish current, move to next
  python scripts/study_bot.py goto 25974     # jump to a study (resets it active)
  python scripts/study_bot.py round-done     # increment hunt round on current study
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

REPO = Path(__file__).resolve().parents[1]
STATE_PATH = REPO / "bot_state.json"


STUDY_META = {
    "26052": {
        "folder": "26052_Rechargeable_Blender_Offset_Blades",
        "title": "Rechargeable Blender With Offset Blades",
        "patent": "US11229891",
        "critical_date": "2019-10-28",
        "focus": "RR 1.1-1.3: blade rotational axis offset 5-15% of blade diameter from container's longitudinal axis",
        "blocked_check": lambda: False,
    },
    "25974": {
        "folder": "25974_Oximidol",
        "title": "Oximidol (Tyrosinase Inhibitor)",
        "patent": "WO2025201324",
        "critical_date": "2024-03-26",
        "focus": "RR1/RR2 exact Oximidol molecule; RR3 Oximidol (or broader alkylamidothiazoles) with Isopropyl Lauroyl Sarcosinate, priority < 2023-08-18",
        "blocked_check": lambda: False,
    },
    "26005": {
        "folder": "26005_Hymn_Research_Cebuano",
        "title": "Hymn Research - Cebuano",
        "patent": "N/A (copyright research)",
        "critical_date": "N/A",
        "focus": "Find existing Cebuano hymn translations per HymnResearch_English.zip list",
        "blocked_check": lambda: False,
    },
    "26006": {
        "folder": "26006_Hymn_Research_Russian",
        "title": "Hymn Research - Russian",
        "patent": "N/A (copyright research)",
        "critical_date": "N/A",
        "focus": "Find existing Russian hymn translations per HymnResearch_English.zip list",
        "blocked_check": lambda: False,
    },
    "26016": {
        "folder": "26016_Hymn_Research_Italian",
        "title": "Hymn Research - Italian",
        "patent": "N/A (copyright research)",
        "critical_date": "N/A",
        "focus": "Find existing Italian hymn translations per HymnResearch_English.zip list",
        "blocked_check": lambda: False,
    },
}


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def current_id(state: dict) -> str:
    return state["current_study"]


def is_blocked(study_id: str) -> bool:
    return STUDY_META[study_id]["blocked_check"]()


def agent_orders(study_id: str) -> str:
    meta = STUDY_META[study_id]
    folder = REPO / meta["folder"]
    is_patent_study = (folder / "known_art").exists()

    if is_patent_study:
        steps = f"""1. Read: {folder / 'STUDY_BRIEF.md'}
2. Read: {folder / 'known_art' / 'known_citations.csv'}
3. Read: templates/RWS_SUBMISSION_PLAYBOOK.md + templates/examples/INDEX.md
4. Run ZERO_MISS_PROTOCOL.md — all 7 lanes
5. Log: {folder / 'HUNT_LOG.md'} and {folder / 'CANDIDATE_SCREEN.md'}
6. Write READY candidates to {folder / 'candidates'}/*_RWS_format.txt
7. Burn-check: python scripts/check_burned.py {study_id} <pub>"""
    else:
        steps = f"""1. Read: {folder / 'STUDY_BRIEF.md'}
2. Read: templates/RWS_SUBMISSION_PLAYBOOK.md + templates/examples/INDEX.md
3. Log: {folder / 'CANDIDATE_SCREEN.md'}
4. Write READY candidates to {folder / 'candidates'}/*_RWS_format.txt
5. Do not submit machine/AI-translated hymns — verified existing translations only"""

    return f"""
╔══════════════════════════════════════════════════════════════╗
║  ACTIVE STUDY: {study_id} — {meta['title']:<33} ║
╚══════════════════════════════════════════════════════════════╝

WORK ONLY THIS STUDY. Do not hunt other studies until advance.

{steps}

Study patent: {meta['patent']}
Critical date: {meta['critical_date']}
RWS focus: {meta['focus']}

AGENT COMMAND: hunt {study_id} deep

When this round is done, Angela runs:
  python scripts/study_bot.py round-done
  python scripts/study_bot.py advance
""".strip()


def cmd_status(state: dict) -> None:
    cur = current_id(state)
    print("RWS Study Bot — one at a time\n")
    for sid in state["queue"]:
        meta = STUDY_META[sid]
        st = state["studies"][sid]
        marker = ">>>" if sid == cur else "   "
        blocked = is_blocked(sid)
        status = "BLOCKED" if blocked else st.get("status", "queued")
        print(f"{marker} {sid}  {meta['title']}")
        print(f"      status={status}  rounds={st.get('rounds_completed', 0)}  "
              f"candidates={st.get('candidates_found', 0)}")
        if blocked:
            print(f"      ⚠ paste RWS brief into {meta['folder']}/STUDY_BRIEF.md")
    print(f"\nCurrent: {cur}")


def cmd_start(state: dict) -> None:
    sid = current_id(state)
    if is_blocked(sid):
        print(f"Study {sid} is BLOCKED.")
        print(STUDY_META[sid]["focus"])
        print("\nFix the blocker, then: python scripts/study_bot.py advance")
        return
    state["studies"][sid]["status"] = "active"
    save_state(state)
    print(agent_orders(sid))


def cmd_round_done(state: dict) -> None:
    sid = current_id(state)
    state["studies"][sid]["rounds_completed"] = state["studies"][sid].get("rounds_completed", 0) + 1
    save_state(state)
    print(f"Recorded hunt round complete for {sid} (round {state['studies'][sid]['rounds_completed']})")


def cmd_advance(state: dict) -> None:
    queue = state["queue"]
    cur = current_id(state)
    state["studies"][cur]["status"] = "done"

    idx = queue.index(cur)
    for nxt in queue[idx + 1 :]:
        if is_blocked(nxt):
            state["current_study"] = nxt
            state["studies"][nxt]["status"] = "blocked"
            save_state(state)
            print(f"Finished {cur}. Next is {nxt} but BLOCKED — paste brief first.")
            return
        state["current_study"] = nxt
        state["studies"][nxt]["status"] = "active"
        save_state(state)
        print(f"Finished {cur}. Now active: {nxt}\n")
        print(agent_orders(nxt))
        return

    save_state(state)
    print(f"All studies in queue complete. Last finished: {cur}")


def cmd_goto(state: dict, study_id: str) -> None:
    if study_id not in STUDY_META:
        raise SystemExit(f"Unknown study {study_id}")
    for sid in state["queue"]:
        if sid != study_id and state["studies"][sid].get("status") == "active":
            state["studies"][sid]["status"] = "paused"
    state["current_study"] = study_id
    if is_blocked(study_id):
        state["studies"][study_id]["status"] = "blocked"
    else:
        state["studies"][study_id]["status"] = "active"
    save_state(state)
    cmd_start(state)


def main() -> None:
    if not STATE_PATH.exists():
        raise SystemExit("Missing bot_state.json")

    state = load_state()
    args = sys.argv[1:]

    if not args or args[0] == "start":
        cmd_start(state)
    elif args[0] == "status":
        cmd_status(state)
    elif args[0] == "advance":
        cmd_advance(state)
    elif args[0] == "round-done":
        cmd_round_done(state)
    elif args[0] == "goto" and len(args) >= 2:
        cmd_goto(state, args[1])
    else:
        print(__doc__)
        raise SystemExit(1)


if __name__ == "__main__":
    main()