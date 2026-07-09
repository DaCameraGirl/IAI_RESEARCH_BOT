# Search Strategy Guide - Different Searches for Different Studies

Your bot now uses **study-specific search strategies**. The system prompt stays the same, but each study gets its own search configuration.

---

## 🎯 The Problem You Had

**Before**: System prompt had 5 hardcoded studies with identical search instructions
- Every study searched the same 9 sources
- No customization for study type
- Wasted time on irrelevant sources

**Now**: Each study auto-detects its type and gets the right search strategy
- Product studies → Search Wayback, FCC, distributors
- NPL studies → Search universities, journals, conferences
- Copyright studies → Search archives, translations, recordings

---

## 📋 Three Search Strategies

### 1. **Invalidity - Product Prior Art**
**For**: Physical devices, chips, blenders, packages, wafers

**Enabled Sources** (Priority 1-3):
- ✅ [1] Wayback Machine - Archived manufacturer sites
- ✅ [1] FCC OET - Equipment authorization exhibits
- ✅ [1] PTAB - IPR exhibit lists
- ✅ [1] Distributor Archives - Old datasheets
- ✅ [2] USENET - Engineer discussions
- ✅ [2] University - Lab equipment mentions
- ✅ [2] Archive Texts - Trade magazines
- ✅ [3] GitHub - Open source datasheets
- ✅ [3] Forums - Product discussions

**Example Studies**:
- 26052 - Rechargeable Blender (product)
- 25853 - LED Resin Package (product)
- 25854 - Semiconductor Wafer (product)

### 2. **Invalidity - NPL (Academic)**
**For**: Chemical compounds, methods, processes, algorithms

**Enabled Sources** (Priority 1-3):
- ✅ [1] PTAB - NPL exhibits from IPRs
- ✅ [1] University - Thesis repositories
- ✅ [2] Archive Texts - Conference proceedings
- ✅ [2] GitHub - Research code repositories
- ❌ Wayback - Not relevant for academic papers
- ❌ FCC - Not relevant for academic papers
- ❌ Distributors - Not relevant for academic papers

**Example Studies**:
- 25974 - Oximidol (chemical compound)

### 3. **Copyright Research**
**For**: Translations, hymns, recordings, publications

**Enabled Sources** (Priority 1-3):
- ✅ [1] Wayback - Archived translation sites
- ✅ [1] University - Digital library collections
- ✅ [1] Archive Texts - Books, hymnals, recordings
- ✅ [2] USENET - Translation discussions
- ✅ [2] GitHub - Translation projects
- ✅ [2] Forums - Translation communities
- ❌ FCC - Not relevant for copyright
- ❌ PTAB - Not relevant for copyright
- ❌ Distributors - Not relevant for copyright

**Example Studies**:
- 26005 - Hymn Research Cebuano
- 26006 - Hymn Research Russian
- 26016 - Hymn Research Italian

---

## 🤖 How Auto-Detection Works

When you create a study folder, the bot automatically detects the strategy:

```python
# Study: 26052_Rechargeable_Blender_Offset_Blades
# Detection logic:
# - Name contains "Blender" (product indicator)
# - Type: "invalidity"
# → Strategy: invalidity_product

# Study: 25974_Oximidol
# Detection logic:
# - Name contains "Oximidol" (compound name)
# - Type: "invalidity"
# → Strategy: invalidity_npl

# Study: 26005_Hymn_Research_Cebuano
# Detection logic:
# - Name contains "Hymn" (copyright indicator)
# → Strategy: copyright
```

---

## 📊 Example: Study 26052 (Blender)

### Auto-Generated Config
```json
{
  "study_id": "26052",
  "study_name": "Rechargeable_Blender_Offset_Blades",
  "type": "invalidity",
  "search_strategy": "invalidity_product",
  "critical_date": "2019-10-28",
  "keywords": ["blade", "offset", "rotational axis", "blender"]
}
```

### Search Strategy Applied
```json
{
  "name": "Invalidity - Product Prior Art",
  "sources": {
    "wayback": {"enabled": true, "priority": 1},
    "fcc": {"enabled": true, "priority": 1},
    "ptab": {"enabled": true, "priority": 1},
    "distributor": {"enabled": true, "priority": 1},
    "usenet": {"enabled": true, "priority": 2},
    "university": {"enabled": true, "priority": 2}
  }
}
```

### What Gets Searched
1. **Wayback Machine** - Archived blender manufacturer sites
2. **FCC OET** - Blender equipment authorizations
3. **PTAB** - IPRs against similar blender patents
4. **Distributors** - Old blender datasheets
5. **USENET** - Engineer discussions about blenders
6. **Universities** - Lab equipment mentions

**NOT searched**: Academic journals (not relevant for product)

---

## 📊 Example: Study 25974 (Oximidol)

### Auto-Generated Config
```json
{
  "study_id": "25974",
  "study_name": "Oximidol",
  "type": "invalidity",
  "search_strategy": "invalidity_npl",
  "critical_date": "2005-01-18",
  "keywords": ["oximidol", "synthesis", "compound"]
}
```

### Search Strategy Applied
```json
{
  "name": "Invalidity - NPL (Journal Articles)",
  "sources": {
    "ptab": {"enabled": true, "priority": 1},
    "university": {"enabled": true, "priority": 1},
    "archive_texts": {"enabled": true, "priority": 2},
    "github": {"enabled": true, "priority": 2},
    "wayback": {"enabled": false},
    "fcc": {"enabled": false},
    "distributor": {"enabled": false}
  }
}
```

### What Gets Searched
1. **PTAB** - NPL exhibits from pharmaceutical IPRs
2. **Universities** - Chemistry thesis repositories
3. **Archive Texts** - Journal of Pharmaceutical Sciences
4. **GitHub** - Research code for synthesis methods

**NOT searched**: Wayback, FCC, distributors (not relevant for compounds)

---

## 🎯 Benefits

### ✅ Faster Searches
- Only searches relevant sources
- No wasted time on irrelevant APIs
- Fewer HTTP 503 errors

### ✅ Better Results
- Product studies get product evidence
- NPL studies get academic papers
- Copyright studies get translations

### ✅ No Manual Configuration
- Auto-detects from study name/type
- Can override in config file if needed
- Updates automatically

---

## 🔧 Customizing Strategies

### Option 1: Edit Study Config
```json
// config/26052_config.json
{
  "study_id": "26052",
  "search_strategy": "invalidity_npl"  // Override to NPL strategy
}
```

### Option 2: Edit Strategy File
```json
// config/search_strategies.json
{
  "invalidity_product": {
    "sources": {
      "wayback": {"enabled": false},  // Disable Wayback
      "fcc": {"enabled": true, "priority": 1}
    }
  }
}
```

### Option 3: Create Custom Strategy
```json
// config/search_strategies.json
{
  "custom_blender": {
    "name": "Custom Blender Strategy",
    "sources": {
      "wayback": {"enabled": true, "priority": 1},
      "distributor": {"enabled": true, "priority": 1},
      // Only these two sources
    }
  }
}
```

Then set in study config:
```json
{
  "study_id": "26052",
  "search_strategy": "custom_blender"
}
```

---

## 📝 How to Use

### Check Current Strategy
```python
from config.study_loader import StudyLoader

loader = StudyLoader(Path("."))
strategy = loader.get_search_strategy("26052")

print(f"Strategy: {strategy['name']}")
print(f"Description: {strategy['description']}")

# Show enabled sources
for source, config in strategy['sources'].items():
    if config['enabled']:
        print(f"  [{config['priority']}] {source}")
```

### Run Hunt with Strategy
```python
from ai_engine import HuntOrchestrator, HuntConfig

# Load study
study = loader.get_study("26052")
strategy = loader.get_search_strategy("26052")

# Configure hunt using strategy
hunt_config = HuntConfig(
    study_id=study['study_id'],
    study_folder=Path(study['study_folder']),
    critical_date=study['critical_date'],
    keywords=study['keywords'],
    
    # Apply strategy (only enabled sources)
    enable_wayback=strategy['sources']['wayback']['enabled'],
    enable_fcc=strategy['sources']['fcc']['enabled'],
    enable_ptab=strategy['sources']['ptab']['enabled'],
    # ... etc
)

orchestrator = HuntOrchestrator(hunt_config)
report = orchestrator.execute_hunt()
```

---

## 🎯 Summary

**Old Way**: Same instructions for every study
```
System Prompt (500 lines):
- Study 26052: Search all 9 sources
- Study 25974: Search all 9 sources
- Study 26005: Search all 9 sources
```

**New Way**: Different strategy per study
```
System Prompt (100 lines):
- Load study config
- Apply search strategy
- Search only relevant sources

Study 26052 → invalidity_product → 6 sources
Study 25974 → invalidity_npl → 4 sources
Study 26005 → copyright → 6 sources
```

**Result**: Faster, smarter, more relevant searches! 🚀
