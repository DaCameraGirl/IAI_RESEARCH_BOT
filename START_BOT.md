# RWS Research Bot — Start Here

Exhaustive prior-art agent — runs **7 hunt lanes**, **burn-checks every
candidate**, **red-teams itself**, and only shows you what would pass RWS
review. Config: `system_prompt.md` + `ZERO_MISS_PROTOCOL.md`.

In **Cursor**, rules auto-load from `.cursor/rules/rws-research-bot.mdc`.

## 1. Open the workspace

Open folder: `C:\Users\enter\OneDrive\Desktop\RWS_RESEARCHER`

## 2. Load the bot brain

In Cursor: the agent should read `system_prompt.md` (paste into Rules or tell
the agent to follow it).

In Claude.ai Projects: paste entire `system_prompt.md` into project instructions.

## 3. Start a hunt (copy-paste one line)

```
hunt 25867
```

```
hunt 25854
```

```
hunt 25853
```
(25853 blocked until you paste the RWS brief into `25853_.../STUDY_BRIEF.md`)

## 4. What the bot does (zero-miss mode)

- Loads dashboard + brief + full burn CSV
- Runs **all 7 hunt lanes** before saying "hunt complete"
- Inspects minimum 20 patents per round (citation graph 2-hop)
- Runs `check_burned.py` + adversarial self-review on every candidate
- Shows only strong matches with verbatim Ctrl+F highlights
- Logs to `CANDIDATE_SCREEN.md` and `HUNT_LOG.md`

**Deep hunt:** `hunt 25867 deep` — bot does not stop until all lanes checked.

## 5. Quick duplicate check (terminal)

```
python scripts/check_burned.py 25867 US5613071
```

Returns `BURNED` or `CLEAR`.

## Studies

| ID | Desktop folder | Patent | Critical date |
|----|----------------|--------|---------------|
| 25867 | 25867 Remote Memory (purple) | US7702742 | 2005-01-18 |
| 25854 | 25854 Wafer Dividing (blue) | US8728916 | 2009-02-25 |
| 25853 | 25853 LED Resin (green) | US8530250 | TBD |