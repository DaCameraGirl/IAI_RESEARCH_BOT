# Study Bot Queue — One at a Time

The bot works **one study only** until you advance. Order:

| # | Study | Patent | Status |
|---|-------|--------|--------|
| 1 | **25867** Remote Memory / Lossy Ethernet | US7702742 | **ACTIVE NOW** |
| 2 | 25854 Wafer Dividing (fissure) | US8728916 | Queued |
| 3 | 25853 LED Resin Package | US8530250 | Blocked (paste RWS brief) |

## Your commands (3 lines total)

**Start / see current study:**
```
python scripts/study_bot.py
```

**Tell the agent to hunt (copy from bot output):**
```
hunt 25867 deep
```

**When round is done, next study:**
```
python scripts/study_bot.py round-done
python scripts/study_bot.py advance
```

## Rules

- Agent hunts **only** `bot_state.json` → `current_study`
- 25853 auto-skips until `STUDY_BRIEF.md` has RWS requirements pasted
- State file: `bot_state.json`