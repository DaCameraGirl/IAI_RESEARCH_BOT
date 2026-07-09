# Quick Start - Where Your Golden Submissions Go

## 🎯 TL;DR

**Golden submissions** go here:
```
26052_Rechargeable_Blender_Offset_Blades/
└── candidates/
    └── READY_SUBMIT_*.txt  ← THESE ARE YOUR GOLDEN FILES
```

**Just open and paste into RWS portal!**

---

## 📸 What You'll See

### Before Hunt
```
26052_Rechargeable_Blender_Offset_Blades/
├── known_art/
│   └── known_citations.csv
├── STUDY_BRIEF.md
└── CANDIDATE_SCREEN.md
```

### After Hunt
```
26052_Rechargeable_Blender_Offset_Blades/
├── candidates/  ← NEW FOLDER CREATED
│   ├── READY_SUBMIT_Blender_Datasheet_2018.txt     ← GOLDEN! 🏆
│   ├── READY_SUBMIT_FCC_Exhibit_2019.txt           ← GOLDEN! 🏆
│   ├── READY_SUBMIT_PTAB_NPL_2017.txt              ← GOLDEN! 🏆
│   ├── HOLD_USENET_Discussion_2017.txt             ← Review first
│   └── hunt_report_2026-07-09.json                 ← Statistics
├── known_art/
│   └── known_citations.csv
├── STUDY_BRIEF.md
└── CANDIDATE_SCREEN.md
```

---

## 🚀 3-Step Workflow

### Step 1: Run Hunt
```bash
python scripts/hunt_with_strategy.py 26052
```

Console shows:
```
✅ READY_SUBMIT Candidates (3):
  • Blender Datasheet 2018
    File: candidates/READY_SUBMIT_Blender_Datasheet_2018.txt
    Score: 0.87
```

### Step 2: Open Study Folder
```
Windows Explorer → 26052_Rechargeable_Blender_Offset_Blades → candidates
```

You'll see:
```
📁 candidates/
  📄 READY_SUBMIT_Blender_Datasheet_2018.txt
  📄 READY_SUBMIT_FCC_Exhibit_2019.txt
  📄 READY_SUBMIT_PTAB_NPL_2017.txt
```

### Step 3: Copy & Paste to RWS Portal
1. Open `READY_SUBMIT_Blender_Datasheet_2018.txt`
2. Select all (Ctrl+A)
3. Copy (Ctrl+C)
4. Paste into RWS portal
5. Submit! ✅

---

## 📄 What's Inside Each File

Each `READY_SUBMIT_*.txt` file contains a **complete RWS submission**:

```
Title:          Rechargeable Blender with Offset Blade Assembly
Author(s):      John Smith, Jane Doe
Publisher:      Acme Corporation
Date published: 2018-03-15
URL:            https://web.archive.org/web/20180315/acme.com/datasheet.pdf
PDF verified:   yes + Wayback Machine

Self-rank: 3
In-scope confidence: high

Select these requirements:

| Select? | Why |
|---------|-----|
| RR1.1 | Explicitly describes blade offset from rotational axis |
| RR1.2 | Shows rechargeable battery configuration |

Ctrl+F phrases:
  - "blade offset 2.5mm from center axis"
  - "rechargeable lithium-ion battery"

Highlight only this:

**RR1.1:**
> The blade assembly is positioned 2.5mm offset from the central 
> rotational axis to improve blending efficiency...

Do NOT select:

**RR1.3:** Document does not mention blade angle specifications

Notes:
- Date: 2018-03-15 (before critical date 2019-10-28) ✓
- Burn check: Not in known_citations.csv ✓
- Access: Open access via Wayback Machine ✓
- ML score: 0.87 (high confidence)
```

**Just copy this entire block and paste into RWS portal!**

---

## 🎯 File Types Explained

### READY_SUBMIT (Golden! 🏆)
- **Self-rank**: 2 or 3
- **Confidence**: High or med
- **Status**: Ready to paste immediately
- **Action**: Copy → Paste → Submit

### HOLD (Review First 📋)
- **Self-rank**: 1 or 2
- **Confidence**: Med or low
- **Status**: Needs your review
- **Action**: Read → Verify → Submit if good

---

## 📊 Where to Find Files

### In Windows Explorer
```
Desktop → RWS_RESEARCH_BOT → 26052_Rechargeable_Blender_Offset_Blades → candidates
```

### In Bot GUI
The bot shows clickable links:
```
✅ READY_SUBMIT Candidates (3):
  • Blender Datasheet 2018
    File: candidates/READY_SUBMIT_Blender_Datasheet_2018.txt  ← Click to open
```

### In Command Line
```bash
# List all golden files
dir "26052_Rechargeable_Blender_Offset_Blades\candidates\READY_SUBMIT_*.txt"

# Open specific file
notepad "26052_Rechargeable_Blender_Offset_Blades\candidates\READY_SUBMIT_Blender_Datasheet_2018.txt"
```

---

## ✨ Summary

| Question | Answer |
|----------|--------|
| **Where do golden submissions go?** | `<study_folder>/candidates/READY_SUBMIT_*.txt` |
| **How many files?** | Depends on hunt results (typically 0-5 per hunt) |
| **What's in each file?** | Complete RWS submission block ready to paste |
| **Do I need to format?** | No! Just copy and paste |
| **Which files to submit?** | All `READY_SUBMIT_*.txt` files |
| **What about HOLD files?** | Review first, submit if good |

---

## 🎯 Example: Study 26052

After running:
```bash
python scripts/hunt_with_strategy.py 26052
```

You get:
```
26052_Rechargeable_Blender_Offset_Blades/
└── candidates/
    ├── READY_SUBMIT_Blender_Datasheet_2018.txt     ← Open this
    ├── READY_SUBMIT_FCC_Exhibit_2019.txt           ← Open this
    └── READY_SUBMIT_PTAB_NPL_2017.txt              ← Open this
```

**3 golden submissions ready to paste!** 🏆

---

## 🚀 Next Steps

1. **Run your first hunt**: `python scripts/hunt_with_strategy.py 26052`
2. **Check the candidates folder**: `26052_Rechargeable_Blender_Offset_Blades/candidates/`
3. **Open READY_SUBMIT files**: Double-click to open in Notepad
4. **Copy & paste to RWS portal**: Ctrl+A → Ctrl+C → Paste → Submit

**That's it!** The bot does all the formatting for you. 🎉
