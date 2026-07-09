# Where Your Golden Submissions Go 🎯

## 📁 Output Location

When the bot finds worthy candidates, it writes them to:

```
<STUDY_FOLDER>/candidates/
```

### Example for Study 26052 (Blender):
```
26052_Rechargeable_Blender_Offset_Blades/
└── candidates/
    ├── READY_SUBMIT_Blender_Datasheet_2018.txt
    ├── READY_SUBMIT_FCC_Exhibit_2019.txt
    ├── HOLD_USENET_Discussion_2017.txt
    └── HOLD_GitHub_Documentation_2018.txt
```

---

## 📊 File Naming Convention

### READY_SUBMIT Files (Golden Stuff!)
```
READY_SUBMIT_<source>_<short_title>_<date>.txt
```

**These are ready to paste into RWS portal immediately**
- Self-rank: 2 or 3
- In-scope confidence: high or med
- All requirements matched
- PDF verified and accessible
- Burn-checked (not in known_citations.csv)

### HOLD Files (Needs Review)
```
HOLD_<source>_<short_title>_<date>.txt
```

**These need your review before submitting**
- Self-rank: 1 or 2
- In-scope confidence: med or low
- Some requirements matched
- May need additional verification

---

## 📋 File Contents

Each file contains a **complete RWS submission block** ready to paste:

```
Title:          Rechargeable Blender with Offset Blade Assembly
Author(s):      John Smith, Jane Doe
Publisher:      Acme Corporation
Journal/Venue:  n/a
Date published: 2018-03-15
DOI:            not found
ISSN:           not found
URL:            https://web.archive.org/web/20180315/acme.com/datasheet.pdf
PDF verified:   yes + Wayback Machine 2026-07-09

Self-rank: 3
In-scope confidence: high

Select these requirements:

| Select? | Why |
|---------|-----|
| RR1.1 | Document explicitly describes blade offset from rotational axis |
| RR1.2 | Shows rechargeable battery configuration |

Ctrl+F phrases:
  - "blade offset 2.5mm from center axis"
  - "rechargeable lithium-ion battery"

Highlight only this:

**RR1.1:**
> The blade assembly is positioned 2.5mm offset from the central 
> rotational axis to improve blending efficiency...

**RR1.2:**
> Powered by a 3.7V rechargeable lithium-ion battery pack...

Do NOT select:

**RR1.3:** Document does not mention blade angle specifications

Notes:
- Date: 2018-03-15 (before critical date 2019-10-28) ✓
- Burn check: Not in known_citations.csv ✓
- Access: Open access via Wayback Machine ✓
- ML score: 0.87 (high confidence)
- Source: Wayback Machine archive
```

---

## 🎯 How to Access Files

### Option 1: Windows Explorer
1. Open study folder (e.g., `26052_Rechargeable_Blender_Offset_Blades`)
2. Open `candidates` subfolder
3. Look for `READY_SUBMIT_*.txt` files
4. Open in Notepad or your text editor

### Option 2: From Bot GUI
The bot GUI shows:
```
✅ READY_SUBMIT Candidates (3):
  • Blender Datasheet 2018
    File: candidates/READY_SUBMIT_Blender_Datasheet_2018.txt
    Score: 0.87
```

Click the filename to open it.

### Option 3: Command Line
```bash
# List all READY_SUBMIT files
dir "26052_Rechargeable_Blender_Offset_Blades\candidates\READY_SUBMIT_*.txt"

# Open specific file
notepad "26052_Rechargeable_Blender_Offset_Blades\candidates\READY_SUBMIT_Blender_Datasheet_2018.txt"
```

---

## 📊 What You'll See After a Hunt

### Console Output
```
Hunt Complete!
============================================================

Total Found: 25
Filtered (known): 8      ← Removed (in known_citations.csv)
Filtered (paywall): 5    ← Removed (not open access)
Rate Limit Hits: 0       ← No HTTP 503 errors
Final Candidates: 12

✅ READY_SUBMIT Candidates (3):
  • Blender Datasheet 2018
    File: candidates/READY_SUBMIT_Blender_Datasheet_2018.txt
    Score: 0.87
  
  • FCC Equipment Authorization 2019
    File: candidates/READY_SUBMIT_FCC_Exhibit_2019.txt
    Score: 0.82
  
  • PTAB IPR Exhibit 2017
    File: candidates/READY_SUBMIT_PTAB_NPL_2017.txt
    Score: 0.79

📋 HOLD Candidates (9):
  • USENET Discussion 2017
    File: candidates/HOLD_USENET_Discussion_2017.txt
  
  • GitHub Documentation 2018
    File: candidates/HOLD_GitHub_Documentation_2018.txt
  
  ... (7 more)

============================================================
Results saved to: 26052_Rechargeable_Blender_Offset_Blades/candidates/
============================================================
```

### File System
```
26052_Rechargeable_Blender_Offset_Blades/
├── candidates/
│   ├── READY_SUBMIT_Blender_Datasheet_2018.txt       ← PASTE THIS
│   ├── READY_SUBMIT_FCC_Exhibit_2019.txt             ← PASTE THIS
│   ├── READY_SUBMIT_PTAB_NPL_2017.txt                ← PASTE THIS
│   ├── HOLD_USENET_Discussion_2017.txt               ← Review first
│   ├── HOLD_GitHub_Documentation_2018.txt            ← Review first
│   └── ... (7 more HOLD files)
├── known_art/
│   └── known_citations.csv
└── STUDY_BRIEF.md
```

---

## 🚀 Workflow

### 1. Run Hunt
```bash
python scripts/hunt_with_strategy.py 26052
```

### 2. Check Output
```
Results saved to: 26052_Rechargeable_Blender_Offset_Blades/candidates/
```

### 3. Open READY_SUBMIT Files
```
26052_Rechargeable_Blender_Offset_Blades/candidates/
  READY_SUBMIT_Blender_Datasheet_2018.txt  ← Open this
  READY_SUBMIT_FCC_Exhibit_2019.txt        ← Open this
  READY_SUBMIT_PTAB_NPL_2017.txt           ← Open this
```

### 4. Copy & Paste to RWS Portal
- Open file in Notepad
- Select all (Ctrl+A)
- Copy (Ctrl+C)
- Paste into RWS portal submission form
- Submit!

### 5. Review HOLD Files (Optional)
- Open HOLD files
- Verify quality
- If good, submit
- If not, discard

---

## 📈 Statistics Tracking

Each hunt also creates a summary JSON:

```
26052_Rechargeable_Blender_Offset_Blades/candidates/
└── hunt_report_2026-07-09.json
```

Contains:
```json
{
  "study_id": "26052",
  "timestamp": "2026-07-09T15:00:00",
  "statistics": {
    "sources_searched": 6,
    "total_found": 25,
    "filtered_known": 8,
    "filtered_paywall": 5,
    "candidates_generated": 12,
    "ready_submit": 3,
    "hold": 9
  },
  "candidates": [
    {
      "title": "Blender Datasheet 2018",
      "source": "wayback",
      "tier": "READY_SUBMIT",
      "rank": 3,
      "confidence": 0.87,
      "filename": "READY_SUBMIT_Blender_Datasheet_2018.txt"
    }
  ]
}
```

---

## 🎯 Quick Reference

| File Type | Location | Action |
|-----------|----------|--------|
| **READY_SUBMIT** | `<study>/candidates/READY_SUBMIT_*.txt` | **Paste to RWS portal immediately** |
| **HOLD** | `<study>/candidates/HOLD_*.txt` | Review first, then submit if good |
| **Hunt Report** | `<study>/candidates/hunt_report_*.json` | Statistics and metadata |

---

## ✨ Summary

**Golden submissions** (READY_SUBMIT files) go to:
```
<STUDY_FOLDER>/candidates/READY_SUBMIT_*.txt
```

**Just open the file and paste into RWS portal!** 🚀

No manual formatting needed - the bot generates perfect RWS submission blocks.
