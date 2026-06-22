# RWS Study Bot

## Open it

Double-click **RWS Research Bot** on Desktop, or `Launch RWS Research Bot.bat`.

Your browser opens to **http://127.0.0.1:7842** — a research command center that actually runs hunts.

## What it does

1. Click **Run Deep Hunt** on study 25867
2. The engine crawls Google Patents citations, burn-checks each hit, scores against your RWS keywords
3. READY candidates auto-write to `candidates/*_RWS_format.txt`
4. You review drafts in the Candidates tab before submitting

No clipboard. No terminal. No "paste this into Cursor."

## Queue

1. **25867** — Remote memory / lossy Ethernet ← active
2. **25854** — Wafer fissure
3. **25853** — blocked until RWS brief pasted

## Files

| File | Purpose |
|------|---------|
| `scripts/rws_web.py` | Web app (this is the bot) |
| `scripts/patent_hunter.py` | Hunt engine |
| `scripts/study_bot.py` | Queue state |
| `bot_state.json` | Active study tracker |