# RWS Research Bot — Start Here

This is **not** a self-running app. It is an **AI research agent** you spin up
in Cursor or Claude. It hunts prior art, screens duplicates, and drafts
submission blocks for your 3 active patent studies.

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

## 4. What the bot does

- Reads `_DASHBOARD.md` + study `STUDY_BRIEF.md`
- Checks candidates against `known_art/known_citations.csv`
- Surfaces only strong, pre-2005/2009/2010 matches (per study)
- Outputs ready-to-paste RWS submission blocks with verbatim highlights
- Logs candidates in `CANDIDATE_SCREEN.md`

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