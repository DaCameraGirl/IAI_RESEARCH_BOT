# RWS Submission Playbook — Angela's Proven Formats

Source examples live in:
- `25657_IC_CHIP_CANDIDATES_READY/25657_READY_RWS_FORMAT_ONLY/` — **gold standard**
- `25657_IC_CHIP_CANDIDATES_READY/Philips_Identification_Product_Range_2004-10/SUBMISSION.md`
- `MEMO_Study25774_2026-05-23.md` — accepted-style memo with dead-ends table
- `Yes. For this new inhaler study, th.txt` — requirement mapping + highlight sections

The bot MUST output submissions in these exact shapes.

---

## READY vs HOLD (folder discipline)

| Tier | Meaning | Action |
|------|---------|--------|
| **READY_SUBMIT** | Passes all 4 gates below | Angela can paste into RWS portal today |
| **HOLD_NOT_READY** | Interesting but date/PDF/req gap | Log in `CANDIDATE_SCREEN.md`, do not show Angela unless asked |
| **SKIP** | Weak, burned, or post-date | Silent discard |

### Four gates (from 25657 FILTERED_NEXT_SUBMISSIONS)

1. Free/public — downloadable PDF or official page printable to PDF
2. Explicit technical anchor — names the thing the requirement asks for (no inference)
3. Date ≤ critical date — verbatim date on document, not page migration date
4. Burn check CLEAR — `python scripts/check_burned.py <study> <pub>`

### Fifth gate — 90% in-scope scorecard (mandatory on every block)

Every candidate block MUST include these two lines immediately after
`Downloadable PDF:`:

```
Self-rank: <0–3>
In-scope confidence: high | med | low
```

| Self-rank | Meaning | Show Angela? |
|-----------|---------|--------------|
| **3** | Verbatim proof on **≥2 priority reqs**; highlights pre-tested Ctrl+F | Yes, if confidence high/med |
| **2** | Verbatim proof on **1 priority req** + 1 strong supporting req | Yes, if confidence high/med |
| **1** | Topical overlap; inference needed; or only optional reqs | **No** — write `HOLD_*_RWS_format.txt` only |
| **0** | Duplicate, wrong study, post-date, or no verbatim anchor | **No** — SKIP silently |

| In-scope confidence | Meaning | Show Angela? |
|---------------------|---------|--------------|
| **high** | Would expect RWS rank 2–3; no duplicate risk; reqs explicit in source | Yes, if Self-rank ≥ 2 |
| **med** | Solid mapping but one req is borderline; note in `Do NOT select` | Yes, if Self-rank ≥ 2 |
| **low** | Duplicate risk, weak highlights, or “interesting but not on-brief” | **Never surface** |

**Angela target: 90% in-scope.** Bot surfaces **0–3** candidates per hunt,
each at Self-rank **2–3** and confidence **high** or **med** only.
An empty hunt round beats a rank-0 paste.

---

## NPL submission block (copy this shape exactly)

```
Dropdown: NPL -> <Article|Catalog|Research Memo|...>
Downloadable PDF: yes + <direct URL>   OR   no + <reason + best URL>

Self-rank: <0–3>
In-scope confidence: high | med | low

Form fields:
  title: <verbatim>
  authors: <verbatim or not found>
  journal: <verbatim or n/a>
  DOI: <DOI or not found>
  ISSN: <ISSN or not found>
  publisher: <verbatim>
  date: <YYYY-MM-DD or Month YYYY — explain which date field on doc>
  URL: <direct link>

Select these requirements:
| Requirement | Select? | Why |
|---|---|---|
| 1.x <name> | yes/no/maybe | <one line — must cite explicit doc language> |
| 2 Date of document | yes/no | <which date string proves it> |

Ctrl+F phrases:
  - "<verbatim phrase 1>"
  - "<verbatim phrase 2>"

Highlight only this:
  - Requirement X.X: "<shortest verbatim quote proving match>"
  - Requirement Y.Y: "<shortest verbatim quote>"

Do NOT select:
  - <req> — <specific gap in one line>

Notes:
  - <date caveat, duplicate risk, or why this beats alternatives>
```

### Angela rules baked in from wins/losses

- **Cyclone Prototype Spacer (25671)** — Accepted, rank 3: highlights were specific and verbatim.
- **Air Classifier Technology (25671)** — Accepted but **Unacceptable**: highlights too weak/generic. Never submit framing-only text.
- **Philips Oct 2004 catalog (25657)** — Clean READY: one highlight line per req, Ctrl+F phrases pre-tested.
- **ETN article** — HOLD: date caveat (2004 created vs 2005 published field) + no native PDF.
- **BPAC 25774 memo** — Include **DEAD ENDS** table so Angela does not re-hunt burned paths.

---

## Patent submission block (25867, 25854, 25853)

```
Dropdown: Patent
Downloadable PDF: yes + <Google Patents or Espacenet PDF URL>

Form fields:
  publication: <USxxxxxxxA1/B2 or EP/JP/WO>
  title: <verbatim from patent>
  assignee: <verbatim>
  inventors: <verbatim>
  publication date: <YYYY-MM-DD>
  URL: <Google Patents link>

Select these requirements:
| Requirement | Select? | Why |
|---|---|---|
| 1.x | yes/no | <explicit claim/paragraph support> |

Ctrl+F phrases:
  - "<verbatim from patent PDF>"

Highlight only this:
  - Requirement 1.x: "<verbatim claim or description sentence>"

Do NOT select:
  - <req> — <gap>

Self-rank: <0–3>
In-scope confidence: high | med | low

Coverage score: <n> of <m> priority reqs with verbatim proof
Adversarial note: <strongest decline reason>
```

---

## Research memo shape (multi-source hunts)

Use when one submission wraps several corroborating URLs (see 25657 NFC memo).

```
Title: <memo title>
...
## Bottom Line
<2-3 sentences — what was found, what was NOT found>

## Best Evidence Found
### <Source name>
- URL, date, evidence, limitation

## DEAD ENDS — Do NOT re-pursue
| Source | Status |

## KNOWN ART CHECK
<confirm CSV searched, CLEAR result>

## Recommended Submission Strategy
<which single doc to submit first vs context-only>
```

---

## Highlight discipline

1. Shortest sentence that still contains a **named entity** or **measured value**
2. Must Ctrl+F in the attached PDF — agent verifies before output
3. One highlight per selected requirement (two max)
4. If you need a whole paragraph to explain → requirement is **not** selected

---

## Study-type output files

When candidate is READY, also write:
`candidates/<short_name>_RWS_format.txt` — portal-paste block
`candidates/<short_name>.md` — longer screening notes (optional)

When HOLD:
`candidates/HOLD_<short_name>_RWS_format.txt`