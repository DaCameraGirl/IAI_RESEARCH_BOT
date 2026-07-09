# Migration Guide - Remove Hardcoded Studies

Your bot had **5 hardcoded studies** in `system_prompt.md`. This caused:
- ❌ HTTP 503 errors (rate limiting)
- ❌ Queue full of old projects
- ❌ Manual updates needed for each study

**New system**: Studies loaded dynamically from folder structure.

---

## What Changed

### Before (Old system_prompt.md)
```markdown
## ACTIVE STUDY: 25867 — REMOTE MEMORY TRANSACTIONS
- **Type**: Prior art search
- **Critical date**: 18 January 2005
- **Known-art file**: 25867_Remote_Memory_Transactions/known_art/known_citations.csv
... (500+ lines of hardcoded study data)

## ACTIVE STUDY: 25854 — SEMICONDUCTOR WAFER
... (another 100+ lines)

## ACTIVE STUDY: 25853 — LED RESIN PACKAGE
... (another 100+ lines)
```

### After (New system_prompt_v2.md)
```markdown
## DYNAMIC STUDY LOADING

Studies loaded automatically from workspace:
- Scan folders: NNNNN_Study_Name/
- Load configs: config/NNNNN_config.json
- Read dashboard: _DASHBOARD.md
- Load known citations: known_art/known_citations.csv
```

**Result**: No hardcoded studies, no manual updates needed.

---

## Migration Steps

### Step 1: Switch to New System Prompt

**Option A: Replace system_prompt.md**
```bash
# Backup old version
cp system_prompt.md system_prompt_old.md

# Use new version
cp system_prompt_v2.md system_prompt.md
```

**Option B: Use v2 alongside old (safer)**
- Keep `system_prompt.md` for reference
- Use `system_prompt_v2.md` in your AI tool
- Test with one study first

### Step 2: Initialize Study Loader

Run this at the start of each session:

```python
from pathlib import Path
from config.study_loader import StudyLoader

# Initialize loader
loader = StudyLoader(Path("."))

# Update from dashboard
dashboard_path = Path("_DASHBOARD.md")
if dashboard_path.exists():
    loader.update_study_from_dashboard(dashboard_path)

# Show active studies
print("Active Studies:")
for study in loader.get_active_studies():
    print(f"  {study['study_id']}: {study['study_name']}")
    if study.get('deadline'):
        print(f"    Deadline: {study['deadline']}")
```

### Step 3: Fix HTTP 503 Errors

The rate limiter is now integrated. Update your hunt commands:

```python
from ai_engine import HuntOrchestrator, HuntConfig

# Configure with rate limiting
hunt_config = HuntConfig(
    study_id="26052",
    study_folder=Path("26052_Rechargeable_Blender_Offset_Blades"),
    critical_date="2019-10-28",
    keywords=["blade", "offset", "rotational axis", "blender"],
    
    # Reduce parallel load to avoid 503 errors
    max_results_per_source=10,  # Reduced from 20
    
    # Enable sources selectively (not all at once)
    enable_wayback=True,
    enable_ptab=True,
    enable_university=True,
    
    # Disable high-traffic sources temporarily
    enable_fcc=False,
    enable_usenet=False,
    enable_github=False
)

orchestrator = HuntOrchestrator(hunt_config)
report = orchestrator.execute_hunt()
```

---

## How It Works Now

### 1. Automatic Study Detection

Bot scans workspace for folders matching `NNNNN_Study_Name/`:

```
RWS_RESEARCH_BOT/
├── 25974_Oximidol/
├── 26005_Hymn_Research_Cebuano/
├── 26006_Hymn_Research_Russian/
├── 26016_Hymn_Research_Italian/
└── 26052_Rechargeable_Blender_Offset_Blades/
```

### 2. Auto-Create Configs

First time bot sees a study folder, it creates `config/NNNNN_config.json`:

```json
{
  "study_id": "26052",
  "study_folder": "26052_Rechargeable_Blender_Offset_Blades",
  "study_name": "Rechargeable Blender Offset Blades",
  "type": "invalidity",
  "critical_date": "2019-10-28",
  "patent_number": "US11229891",
  "requirements": [...],
  "known_citations_path": "26052_Rechargeable_Blender_Offset_Blades/known_art/known_citations.csv",
  "known_citations_count": 42,
  "status": "active"
}
```

### 3. Load on Demand

When you say `hunt 26052`, bot:
1. Loads `config/26052_config.json`
2. Loads `known_citations.csv` from that study
3. Runs hunt with rate limiting
4. Filters results against that study's known citations

**No other studies loaded** - only what you're working on.

---

## Benefits

### ✅ No More HTTP 503 Errors
- Rate limiter prevents overwhelming APIs
- Exponential backoff on failures
- Configurable per-API limits

### ✅ No More Hardcoded Studies
- Studies loaded dynamically
- Add new study = just create folder
- Remove study = just delete folder

### ✅ Clean Queue
- Only active studies shown
- Closed studies in `_DASHBOARD.md` ignored
- No manual cleanup needed

### ✅ Easy Updates
- Edit `config/NNNNN_config.json` directly
- Or update `_DASHBOARD.md` and reload
- Changes take effect immediately

---

## Example: Working on Study 26052

### Old Way (Hardcoded)
```markdown
# In system_prompt.md (line 450)
## ACTIVE STUDY: 26052 — RECHARGEABLE BLENDER
- **Type**: Invalidity ($7,000)
- **Critical date**: 2019-10-28
- **Known-art file**: 26052_Rechargeable_Blender_Offset_Blades/known_art/known_citations.csv
... (50 more lines)
```

**Problems:**
- Had to edit 500-line prompt file
- Other studies loaded too (memory waste)
- HTTP 503 from too many parallel requests

### New Way (Dynamic)
```python
# Just say: hunt 26052
study = loader.get_study("26052")
# Auto-loads only this study's config and known citations
# Rate-limited API calls prevent 503 errors
```

**Benefits:**
- No prompt editing
- Only loads what you need
- No HTTP errors

---

## Troubleshooting

### "Study not found"
```python
# Check available studies
loader = StudyLoader(Path("."))
print(loader.active_studies.keys())
# Output: dict_keys(['25974', '26005', '26006', '26016', '26052'])
```

### "Known citations not loading"
```python
# Check CSV path
study = loader.get_study("26052")
print(study['known_citations_path'])
# Verify file exists at that path
```

### "Still getting HTTP 503"
```python
# Reduce parallel load
hunt_config = HuntConfig(
    ...
    max_results_per_source=5,  # Lower limit
    enable_wayback=True,       # Enable fewer sources
    enable_ptab=True,
    enable_fcc=False,          # Disable others
    enable_usenet=False,
    enable_github=False
)
```

---

## Next Steps

1. **Backup old system_prompt.md**: `cp system_prompt.md system_prompt_old.md`
2. **Switch to v2**: Use `system_prompt_v2.md` in your AI tool
3. **Test with one study**: `hunt 26052`
4. **Verify no 503 errors**: Check rate limiting works
5. **Add new studies**: Just create folder, bot auto-detects

Your bot is now **dynamic** and **rate-limited**! 🚀
