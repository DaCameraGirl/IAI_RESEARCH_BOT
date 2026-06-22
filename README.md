# RWS_RESEARCHER

Angela's project section for **RWS IP Research NPL submission work**.
This is the canonical folder — all RWS-related agent prompts, study
working files, and outputs live here.

## What this project does

Angela contributes to RWS IP Research as an NPL (Non-Patent Literature)
hunter. She finds journal articles, datasheets, brochures, press releases,
and other dated documents that count as prior art for active RWS
CrowdSearch / CrowdSearch Plus studies, then submits them through the
RWS portal for scoring (Accepted/Declined, New/Duplicate, rank 0–3,
Acceptable/Unacceptable).

`system_prompt.md` contains the tuned agent system prompt that runs the
research workflow — drop it into Claude Code, Claude.ai Projects, a
Custom GPT, or any other LLM tool to spin up the RWS Researcher agent.

## Folder layout

```
RWS_RESEARCHER/
  system_prompt.md                       ← the agent's brain (paste into tool)
  README.md                              ← this file
  outputs/                               ← agent findings, hunt logs, candidate lists
  templates/                             ← reusable submission templates per study type
  25657_Integrated_Circuit_Chips/
    known_art/                           ← PDFs RWS has provided (do NOT submit)
    candidates/                          ← PDFs we found and are evaluating
    reference/                           ← supporting docs (revision histories, etc.)
    submitted/                           ← PDFs we actually submitted
  25696_Battery_Module/
    (same subfolder structure when active)
```

## How to use the agent

1. Open whichever tool you're spinning the agent up in (Claude Code /
   Claude.ai Project / Custom GPT / etc.).
2. Paste the entire contents of `system_prompt.md` into the system /
   custom-instructions slot.
3. Start a conversation by either:
   - Pasting a candidate document or DOI ("evaluate this for 25657")
   - Asking for a hunt ("find PN511 mentions on Wayback from 2003")
   - Pasting a new study brief ("here's the 25696 brief, ingest it")

## Active studies (as of 2026-06-22)

- **25867 — Remote Memory Transactions** (prior art search). Study patent
  US7702742B2. Critical date 2005-01-18. Focus: lossy **Ethernet** congestion
  drops, priority queues, per-priority sequencing/ACK/retransmit (RR 1.7, 1.8,
  1.13). Desktop folder: `25867 Remote Memory` (purple).
- **25854 — Semiconductor Wafer Dividing** (prior art search). Study patent
  US8728916B2. Critical date preferred 2009-02-25. Current RWS focus: RR 1.2
  (fissure linking adjacent laser-formed processed portions). Desktop folder:
  `25854 Wafer Dividing` (blue).
- **25853 — Light Emitting Device Resin Package** (prior art search). Study
  patent US8530250B2. RWS portal brief not yet pasted. Desktop folder:
  `25853 LED Resin` (green).
- **25657 — Integrated Circuit Chips** ($5,000 invalidity study,
  deadline 2026-05-27). Target patent US7373531B2 (RFCyber Corp). Hunt
  Philips/NXP NFC chips PN511/PN512/PN531 dated ≤ Jan 10, 2005. Full
  brief baked into `system_prompt.md`.
- **25696 — Battery Module** (CrowdSearch Plus, deadline 2026-05-26).
  Brief not yet pasted into `system_prompt.md` — the agent will refuse
  to generate 25696 submissions until it is.

## Closed / historical studies

- 25671 Inhalers (Final Review), 25576 Smoking System (Final Review),
  25429 Wireless Devices (Completed). Submission windows over.

## Key learnings baked into the prompt

- **Skip weak matches** — rank-0 Declines hurt more than missing
  submissions help.
- **Free downloadable PDFs only** — no paywalls. Filter through
  Unpaywall before reading.
- **Verbatim highlights only** — never paraphrase. Highlight must
  contain a specific technical anchor (part number, named device,
  measured value, named person, dated event).
- **Invalidity studies need different sources than research-paper NPL
  studies** — PubMed is useless for invalidity; Wayback Machine, FCC
  OET, USPTO PTAB, and USENET archives are the goldmines.

See `system_prompt.md` for the full ruleset.
