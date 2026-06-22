# RWS Study Bot — One Project at a Time

Three studies. Bot does them **in order**, not all at once.

## Step 1 — Run the bot

Double-click `RUN_BOT.ps1` or in terminal:

```
python scripts/study_bot.py
```

It prints which study is active and the exact command to give the agent.

## Step 2 — Hunt (in Cursor chat)

```
hunt 25867 deep
```

(Use whatever study ID the bot printed.)

## Step 3 — Next project when ready

```
python scripts/study_bot.py round-done
python scripts/study_bot.py advance
```

## Queue order

1. **25867** — Remote memory / lossy Ethernet (US7702742) ← **starts here**
2. **25854** — Wafer fissure (US8728916)
3. **25853** — LED resin (US8530250) — blocked until you paste RWS brief

## Files

| File | Purpose |
|------|---------|
| `bot_state.json` | Which study is active |
| `BOT_QUEUE.md` | Human-readable queue |
| `system_prompt.md` | Bot brain |
| `ZERO_MISS_PROTOCOL.md` | Exhaustive hunt rules |
| `scripts/study_bot.py` | One-at-a-time runner |
| `scripts/check_burned.py` | Duplicate checker |