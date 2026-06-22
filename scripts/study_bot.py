#!/usr/bin/env python3
"""
One-at-a-time study bot runner for RWS_RESEARCHER.

Usage:
  python scripts/study_bot.py              # show current study + agent orders
  python scripts/study_bot.py status       # queue overview
  python scripts/study_bot.py advance      # finish current, move to next
  python scripts/study_bot.py goto 25854     # jump to a study (resets it active)
  python scripts/study_bot.py round-done     # increment hunt round on current study
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE_PATH = REPO / "bot_state.json"


def _is_25853_blocked() -> bool:
    brief = REPO / "25853_Light_Emitting_Device_Resin_Package" / "STUDY_BRIEF.md"
    text = brief.read_text(encoding="utf-8")
    return "TBD — paste from RWS portal" in text or "brief incomplete" in text.lower()


STUDY_META = {
    "25867": {
        "folder": "25867_Remote_Memory_Transactions",
        "title": "Remote Memory Transactions (Lossy Ethernet)",
        "patent": "US7702742B2",
        "critical_date": "2005-01-18",
        "focus": "RR 1.7, 1.8, 1.13 + priority queues, Ethernet congestion drops, ACK/retransmit",
        "blocked_check": lambda: True,
    },
    "25854": {
        "folder": "25854_Semiconductor_Wafer_Dividing",
        "title": "Semiconductor Wafer Dividing (Laser Fissure)",
        "patent": "US8728916B2",
        "critical_date": "2009-02-25 (preferred)",
        "focus": "RR 1.2 fissure linking adjacent processed portions; then 1.1, 1.3",
        "blocked_check": lambda: True,
    },
    "25853": {
        "folder": "25853_Light_Emitting_Device_Resin_Package",
        "title": "Light Emitting Device Resin Package",
        "patent": "US8530250B2",
        "critical_date": "TBD",
        "focus": "Blocked until RWS brief pasted into STUDY_BRIEF.md",
        "blocked_check": _is_25853_blocked,
    },
}


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def current_id(state: dict) -> str:
    return state["current_study"]


def is_blocked(study_id: str) -> bool:
    if study_id == "25853":
        return _is_25853_blocked()
    return False


def agent_orders(study_id: str) -> str:
    meta = STUDY_META[study_id]
    folder = REPO / meta["folder"]
    return f"""
╔══════════════════════════════════════════════════════════════╗
║  ACTIVE STUDY: {study_id} — {meta['title']:<33} ║
╚══════════════════════════════════════════════════════════════╝

WORK ONLY THIS STUDY. Do not hunt other studies until advance.

1. Read: {folder / 'STUDY_BRIEF.md'}
2. Read: {folder / 'known_art' / 'known_citations.csv'}
3. Run ZERO_MISS_PROTOCOL.md — all 7 lanes
4. Log: {folder / 'HUNT_LOG.md'} and {folder / 'CANDIDATE_SCREEN.md'}
5. Burn-check: python scripts/check_burned.py {study_id} <pub>

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
        status = st.get("status", "queued")
        if blocked and sid == "25853":
            status = "BLOCKED"
        print(f"{marker} {sid}  {meta['title']}")
        print(f"      status={status}  rounds={st.get('rounds_completed', 0)}  "
              f"candidates={st.get('candidates_found', 0)}")
        if blocked and sid == "25853":
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