#!/usr/bin/env python3
"""Quick smoke tests for RWS_RESEARCHER bot scripts and gate wiring."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def ok(name: str) -> None:
    print(f"PASS  {name}")


def fail(name: str, detail: str) -> None:
    print(f"FAIL  {name}: {detail}")
    FAILURES.append(name)


FAILURES: list[str] = []


def test_scripts_compile() -> None:
    for script in ("check_burned.py", "study_bot.py"):
        code, out = run([sys.executable, "-m", "py_compile", f"scripts/{script}"])
        if code != 0:
            fail(f"compile {script}", out)
        else:
            ok(f"compile {script}")


def test_bot_state() -> None:
    state = json.loads((REPO / "bot_state.json").read_text(encoding="utf-8"))
    if state.get("current_study") != "25867":
        fail("bot_state current_study", f"expected 25867, got {state.get('current_study')}")
    else:
        ok("bot_state current_study=25867")


def test_check_burned() -> None:
    cases = [
        (["25867", "US5613071"], "BURNED"),
        (["25867", "US6718392"], "CLEAR"),
        (["25867", "US7702742"], "BURNED"),
        (["25854", "US8728916"], "BURNED"),
    ]
    for args, want in cases:
        code, out = run([sys.executable, "scripts/check_burned.py", *args])
        if code != 0:
            fail(f"check_burned {' '.join(args)}", out)
        elif want not in out:
            fail(f"check_burned {' '.join(args)}", f"expected {want}, got: {out}")
        else:
            ok(f"check_burned {' '.join(args)} -> {want}")


def test_check_burned_unknown_study() -> None:
    code, out = run([sys.executable, "scripts/check_burned.py", "99999", "US0000000"])
    if code == 0 or "Unknown study" not in out:
        fail("check_burned unknown study", out)
    else:
        ok("check_burned unknown study exits nonzero")


def test_study_bot_status() -> None:
    code, out = run([sys.executable, "scripts/study_bot.py", "status"])
    if code != 0 or "25867" not in out:
        fail("study_bot status", out)
    else:
        ok("study_bot status")


def test_self_rank_gate_wiring() -> None:
    required = REPO / "templates" / "PATENT_SUBMISSION_TEMPLATE.txt"
    text = required.read_text(encoding="utf-8")
    for needle in ("Self-rank:", "In-scope confidence:", "Self-rank ≥ 2"):
        if needle not in text:
            fail("self-rank template", f"missing {needle!r} in PATENT_SUBMISSION_TEMPLATE.txt")
            return
    for rel in (
        "system_prompt.md",
        "ZERO_MISS_PROTOCOL.md",
        "templates/RWS_SUBMISSION_PLAYBOOK.md",
        ".cursor/rules/rws-research-bot.mdc",
    ):
        if "Self-rank" not in (REPO / rel).read_text(encoding="utf-8"):
            fail("self-rank wiring", f"missing Self-rank in {rel}")
            return
    ok("self-rank gate wired in templates + protocol")


def main() -> int:
    print("RWS_RESEARCHER smoke tests\n")
    test_scripts_compile()
    test_bot_state()
    test_check_burned()
    test_check_burned_unknown_study()
    test_study_bot_status()
    test_self_rank_gate_wiring()
    print()
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} failure(s)")
        return 1
    print("RESULT: all smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())