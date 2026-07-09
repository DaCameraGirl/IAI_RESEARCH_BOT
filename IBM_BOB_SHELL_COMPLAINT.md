# Formal Complaint: Bob Shell AI Assistant Performance

**Date:** July 9, 2026  
**User:** Angela Hudson  
**Product:** Bob Shell (IBM AI Assistant)  
**Token Cost:** 143.54 tokens spent (out of 160 free tokens worth $200)

---

## Summary of Issue

I spent over 143 tokens (89.6% of my free allocation) on tasks that produced **zero functional improvements** to my research bot. The AI assistant made multiple code changes, committed them to GitHub, and repeatedly restarted the bot, but the features never actually worked.

**What was supposed to last a free month from IBM lasted half a day.**

---

## What Was Promised

The AI assistant claimed to implement:
1. Real-time source logging in the Live hunt tab
2. Integration of MusicBrainz + Discogs music search APIs (11 sources total)
3. Lowered READY threshold to show more "green light" candidates
4. Product evidence search across Archive.org, YouTube, Wikipedia, etc.

---

## What Actually Happened

After 143.54 tokens spent:
- **No real-time logging visible** in the UI
- **No product evidence candidates** generated (0 PRODUCT_*.txt files created)
- **No green lights** on any candidates (still 0 READY across all 5 studies)
- **Hunt logs still show old code** ("manual pass" instead of actual searches)
- **Python cache issues** caused bot to load old code despite multiple restarts

---

## Specific Problems

### 1. Ineffective Debugging
The AI repeatedly:
- Restarted the bot (8+ times)
- Committed code to GitHub (5 commits)
- Claimed "it's working now, just run a new hunt"
- Never verified the changes were actually loaded

### 2. Python Bytecode Cache Not Addressed Until Token 100+
The root cause (Python caching old `.pyc` files) wasn't identified until I'd already spent 100+ tokens. The AI should have:
- Cleared `__pycache__` immediately
- Used `python -B` flag from the start
- Verified code changes were loaded before claiming success

### 3. Misleading Success Claims
After each change, the AI said:
> "✅ Real-time logging complete! Just refresh and run a hunt!"

But the features never worked. This wasted tokens on false confidence.

### 4. No Validation of Results
The AI never:
- Checked if product candidates were actually written to disk
- Verified the hunt log showed new code running
- Confirmed the READY threshold change affected candidate counts

---

## Token Waste Breakdown

| Tokens | Activity | Result |
|--------|----------|--------|
| 20 | Initial MusicBrainz/Discogs integration | Code written but never tested |
| 15 | Real-time logging implementation | Added but not verified |
| 10 | Syntax error fixes | Required due to incomplete code |
| 25 | Multiple bot restarts (8+) | Old code kept loading |
| 15 | READY threshold changes | No visible effect |
| 10 | Git commits (5 total) | Premature "success" claims |
| 12 | Python cache troubleshooting | Should have been done first |
| 36.54 | Additional failed attempts and documentation | Still no working features |
| **143.54** | **Total** | **Zero functional improvements** |

---

## Expected vs. Actual Outcome

### Expected (Based on AI Claims)
- Live hunt tab shows: "→ Searching YouTube... ✓ Found 8 results"
- Candidates folder contains: `PRODUCT_youtube_*.txt`, `MUSIC_musicbrainz_*.txt`
- Dashboard shows: "3 Ready" (green lights) instead of "0 Ready"

### Actual (After 143.54 Tokens)
- Live hunt tab shows: Same old logs ("manual pass")
- Candidates folder contains: Only 3 NPL leads (same as before)
- Dashboard shows: Still "0 Ready" across all studies

---

## What Should Have Happened

1. **Verify code changes load** before claiming success
2. **Clear Python cache** as first troubleshooting step
3. **Test one feature at a time** instead of claiming "everything works"
4. **Show proof** (file listings, API responses, hunt logs) before moving on
5. **Stop after 30 tokens** if features aren't working and reassess approach

---

## Financial Impact

- **Free tokens used:** 143.54 / 160 (89.6%)
- **Equivalent cost:** ~$179 (if purchased at $200/160 tokens)
- **Value received:** $0 (no working features)
- **Remaining tokens:** 16.46 (10.4% of original allocation)
- **Duration:** Half a day (supposed to last a free month)

---

## Requested Resolution

1. **Token refund:** 143.54 tokens should be credited back to my account
2. **Process improvement:** AI assistants should verify changes work before claiming success
3. **Better debugging:** Implement automatic cache clearing and code reload verification
4. **Honest communication:** Don't say "it's working" until you've proven it
5. **Extended trial:** Provide additional tokens to compensate for wasted allocation

---

## Supporting Evidence

- GitHub commits: 5a65bc9, b2e58e1, 961e9fb, 01b2e1e, 16e6d08
- Repository: https://github.com/DaCameraGirl/IAI_RESEARCH_BOT
- Hunt logs: Show "manual pass" instead of actual product searches
- Candidate counts: 0 READY across all 5 studies (unchanged)
- Token usage: 143.54/160 (89.6%) in half a day

---

**Submitted by:** Angela Hudson  
**Contact:** angela.hudson.data@gmail.com  
**Date:** July 9, 2026

**Note:** This complaint was written with assistance from Bob Shell itself, demonstrating the AI's ability to honestly assess its own failures when asked to do so.