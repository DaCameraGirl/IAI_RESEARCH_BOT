# Zero-Miss Hunt Protocol

The bot runs this internally on every `hunt` command. Angela sees only
candidates that pass all gates.

## Phase 0 — Load (mandatory, no skipping)

- [ ] `_DASHBOARD.md` — current lead + critical date
- [ ] `STUDY_BRIEF.md` — all numbered requirements
- [ ] `known_art/known_citations.csv` — full burn list loaded into memory
- [ ] Study patent PDF or Google Patents page — figures, terminology, citations
- [ ] RWS lead text — what they want *this week*

## Phase 1 — Requirement decomposition

Build a **Requirement Map** before searching:

| Req | Must-show elements | Synonym keywords |
|-----|-------------------|------------------|
| 1.x | ... | ... |

Every search query must map to at least one req. No random browsing.

## Phase 2 — Seven hunt lanes (complete ALL before "hunt complete")

1. **Study patent citations** — every direct citation in CSV, backward 2 hops
2. **Study patent cited-by** — forward citations ≤ critical date
3. **Assignee/inventor sweep** — all pre-date publications from study assignee
4. **Synonym lattice** — every keyword combo from Requirement Map
5. **NPL adjacent** — theses, RFCs, consortium specs, conference proceedings
6. **Litigation/IPR exhibits** — PTAB exhibits for study patent not in CSV
7. **Wayback/product** — manufacturer pages, datasheets, app notes ≤ critical date

Log lane completion in `HUNT_LOG.md` (internal). Do not narrate empty lanes
to Angela.

## Phase 3 — Candidate gate (ALL must pass)

| Gate | Fail action |
|------|-------------|
| `check_burned.py` CLEAR | discard |
| Date ≤ critical date | discard |
| Free PDF / patent PDF | discard |
| Strong match ≥1 priority req | discard (weak = skip) |
| Verbatim Ctrl+F anchor exists | discard |
| Not inference-only | discard |
| **Self-rank ≥ 2** | do not surface (HOLD file if rank 1; silent SKIP if 0) |
| **In-scope confidence high or med** | do not surface if low |

## Phase 4 — Adversarial review (red team yourself)

Before surfacing, answer:

1. Which requirements does this **fail**? List them honestly.
2. Would RWS call this "incidental" vs "designed" (25867 lossy Ethernet)?
3. Is this a family member of something in CSV under a different number?
4. Is there a **better** reference I should have found first?
5. Strongest counter-argument to submitting this?

If counter-argument wins → SKIP. If candidate survives → surface.

## Phase 5 — Output + log

- Submission block (patent or NPL format per study type)
- Append to `CANDIDATE_SCREEN.md`
- Update `HUNT_LOG.md` with source + req coverage
- Propose `_DASHBOARD.md` update