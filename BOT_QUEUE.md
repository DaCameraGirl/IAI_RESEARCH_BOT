# Study Bot Queue — One at a Time

The bot works **one study only** until you advance. Order:

| # | Study | Patent | Status |
|---|-------|--------|--------|
| 1 | **26052** Blender Offset Blades | US11229891 | **ACTIVE NOW** |
| 2 | 25974 Oximidol | WO2025201324 | Queued |
| 3 | 26005 Hymn Research - Cebuano | N/A (copyright) | Queued |
| 4 | 26006 Hymn Research - Russian | N/A (copyright) | Queued |
| 5 | 26016 Hymn Research - Italian | N/A (copyright) | Queued |

## Your commands (3 lines total)

**Start / see current study:**
```
python scripts/study_bot.py
```

**Tell the agent to hunt (copy from bot output):**
```
hunt 26052 deep
```

**When round is done, next study:**
```
python scripts/study_bot.py round-done
python scripts/study_bot.py advance
```

## Rules

- Agent hunts **only** `bot_state.json` → `current_study`
- State file: `bot_state.json`
