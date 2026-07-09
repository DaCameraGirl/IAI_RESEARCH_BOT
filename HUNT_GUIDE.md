# Automated Hunt Guide - Deep Hunt with Product Evidence

Your bot now runs **8-lane deep hunts** including product evidence search:

## Hunt Lanes (L1-L7)

### Patent Citation Lanes (L1-L4b)
- **L1**: Study patent backward citations (200 patents)
- **L2**: 2-hop citation graph (100 parents → 40 cites each)
- **L2b**: 3-hop citation graph (50 deeper hops)
- **L3**: Assignee sweep (Google Patents search)
- **L4**: Synonym lattice (20+ keyword queries)
- **L4b**: CPC/classification searches

### Non-Patent Literature (L5)
- **L5**: NPL Crossref (academic papers pre-dating critical date)

### Product Evidence (L7) - NEW! (11 Sources)
- **Archive.org**: Product manuals, catalogs, datasheets
- **YouTube**: Teardown/repair videos (requires YOUTUBE_API_KEY)
- **Reddit**: Product discussions with photos (requires REDDIT_API_KEY)
- **Wayback Machine**: Archived manufacturer websites (2010-2019)
- **Wikipedia**: Technical articles with references + revision history
- **Google Custom Search**: Web-wide + domain-specific (requires GOOGLE_API_KEY + GOOGLE_SEARCH_ENGINE_ID)
- **Bing Search**: Web search (requires BING_API_KEY)
- **DuckDuckGo**: Instant answers (no API key needed)
- **Semantic Scholar**: Academic papers with citations
- **OpenAlex**: Academic papers (better coverage than Crossref)
- **MusicBrainz**: Music recordings with release dates (no API key needed) - Perfect for hymn research!
- **Discogs**: Album releases with formats and labels (requires DISCOGS_API_KEY)

### Known Citation Mining (L6)
- **L6**: Backward cites from all burned patents (finds NEW art via old seeds)

## Filtering Rules
- ✅ **NO known citations** - automatically filtered from known_citations.csv
- ✅ **NO paywalls** - only open access or school-accessible documents
- ✅ **Date filtering** - only documents before critical date

---

## Product Evidence Search (L7)

The bot now searches **real-world product sources** where actual products exist:

### What Gets Searched

1. **Archive.org** - Product manuals, catalogs, technical documentation
   - Example: "blender manual offset blade" → finds old Vitamix/Blendtec manuals
   - Searches: texts, movies (product demos), audio (product reviews)

2. **YouTube** - Teardown and repair videos (requires YOUTUBE_API_KEY)
   - Example: "blender teardown repair" → finds disassembly videos showing blade design
   - Filters: Only videos published before critical date

3. **Reddit** - Product discussions with photos and technical details
   - Example: "blender blade offset" in r/BuyItForLife, r/engineering
   - Searches: Pushshift API for historical posts before critical date

4. **Wayback Machine** - Archived manufacturer websites
   - Example: vitamix.com snapshots from 2010-2019
   - Finds: Old product pages, datasheets, press releases

### How It Works

```python
# Automatically extracts keywords from study
product_keywords = ["blender", "food processor", "mixer"]
technical_terms = ["offset blade", "eccentric rotor", "tornado effect"]

# Searches all 4 sources
results = search_product_evidence(
    product_keywords=product_keywords,
    technical_terms=technical_terms,
    before_date="2019-10-28",  # Critical date
    max_per_source=10
)

# Writes candidates to: study_folder/candidates/PRODUCT_*.txt
```

### Output Format

Each product candidate is written as:

```
Type: Product Evidence / NPL
Source: Archive.org
Title: Vitamix Professional Series 750 Manual
URL: https://archive.org/details/vitamix_750_manual
Date: 2015
Critical Date: ≤ 2019-10-28

Status: UNVERIFIED — manually review source, verify date, extract technical details, take screenshots

Description:
Product manual showing blade assembly with offset design...

Next Steps:
1. Visit URL and verify content is accessible
2. Confirm publication/creation date is before critical date
3. Extract technical specifications (blade offset, dimensions, etc.)
4. Take screenshots showing relevant technical details
5. Map to study requirements
6. If valid, format as proper RWS submission with screenshots
```

### API Setup (Optional - Expands L7 from 4 to 10 sources)

**Free APIs (No Key Needed):**
- ✅ Archive.org - Already working
- ✅ Wayback Machine - Already working
- ✅ Wikipedia - Already working
- ✅ DuckDuckGo - Already working
- ✅ OpenAlex - Already working

**Free APIs (Key Required):**

1. **YouTube Data API v3** (10,000 queries/day free)
   - Get key: https://console.cloud.google.com/apis/library/youtube.googleapis.com
   - Set: `set YOUTUBE_API_KEY=your_key_here`

2. **Reddit API** (60 requests/minute free)
   - Get key: https://www.reddit.com/prefs/apps → "create app" → choose "script"
   - Set: `set REDDIT_CLIENT_ID=your_client_id`
   - Set: `set REDDIT_CLIENT_SECRET=your_client_secret`

3. **Google Custom Search** (100 queries/day free)
   - Get API key: https://console.cloud.google.com/apis/library/customsearch.googleapis.com
   - Create search engine: https://programmablesearchengine.google.com/
   - Set: `set GOOGLE_API_KEY=your_api_key`
   - Set: `set GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id`

4. **Bing Search API** (1,000 queries/month free)
   - Get key: https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
   - Set: `set BING_API_KEY=your_key_here`

5. **Semantic Scholar** (Rate limited but no key needed for basic use)
   - No setup required - works out of the box
   - For higher limits: https://www.semanticscholar.org/product/api

6. **MusicBrainz** (No API key needed! Perfect for hymn research)
   - No setup required - works out of the box
   - Searches music recordings with release dates
   - Ideal for finding hymn recordings in different languages
   - API docs: https://musicbrainz.org/doc/MusicBrainz_API

7. **Discogs** (Free API key, 60 requests/minute)
   - Get key: https://www.discogs.com/settings/developers → "Generate new token"
   - Set: `setx DISCOGS_API_KEY "your_token_here"`
   - Searches album releases with formats (vinyl, CD, cassette) and labels
   - Great for finding hymnal albums and historical recordings

**Without API keys:** Bot searches 8 sources (Archive.org, Wayback, Wikipedia, DuckDuckGo, OpenAlex, Semantic Scholar, MusicBrainz, YouTube if key set)
**With all API keys:** Bot searches 11 sources (adds Reddit, Google, Bing, Discogs)

---

## Quick Start - Run Deep Hunt

### 1. Configure Your Hunt

```python
from pathlib import Path
from ai_engine import HuntOrchestrator, HuntConfig

# Configure hunt for your study
hunt_config = HuntConfig(
    study_id="25974",  # Your study ID
    study_folder=Path("25974_Oximidol"),
    critical_date="2024-03-26",
    
    # What to search for
    keywords=["Oximidol", "tyrosinase inhibitor", "Isopropyl Lauroyl Sarcosinate"],
    part_numbers=["Oximidol"],
    manufacturers=["Beiersdorf"],
    target_domains=["beiersdorf.com", "eucerin.com"],
    
    # Enable all unconventional sources
    enable_wayback=True,        # Wayback Machine archives
    enable_fcc=True,            # FCC equipment database
    enable_ptab=True,           # USPTO PTAB IPR exhibits
    enable_usenet=True,         # Google Groups (USENET)
    enable_university=True,     # University archives
    enable_distributor=True,    # Distributor datasheets
    enable_archive_texts=True,  # Internet Archive texts
    enable_github=True,         # GitHub/GitLab repos
    enable_forums=True,         # Technical forums
    
    max_results_per_source=20,
    min_confidence=0.6
)
```

### 2. Execute Hunt

```python
# Run automated hunt
orchestrator = HuntOrchestrator(hunt_config)
report = orchestrator.execute_hunt()

# Results automatically written to:
# 25974_Oximidol/candidates/READY_SUBMIT_*.txt
# 25974_Oximidol/candidates/HOLD_*.txt
```

### 3. Review Results

```python
print(f"Sources searched: {report['summary']['sources_searched']}")
print(f"Total found: {report['summary']['total_found']}")
print(f"Filtered (known): {report['statistics']['filtered_known']}")
print(f"Filtered (paywall): {report['statistics']['filtered_paywall']}")
print(f"Ready to submit: {report['summary']['ready_to_submit']}")
```

---

## What Gets Searched

### 1. **Wayback Machine** (archive.org)
- Old manufacturer websites
- Archived datasheets, brochures, press releases
- Product pages from before critical date
- **Example**: `semiconductors.philips.com` snapshots from 2003-2004

### 2. **FCC OET Database**
- Equipment authorization exhibits
- Datasheets attached to FCC filings
- Technical specifications
- **Example**: Philips NFC devices with PN511/PN531 chips

### 3. **USPTO PTAB E2E**
- IPR exhibit lists for target patent
- NPL citations from other IPRs
- Expert declarations with references
- **Example**: Google v. RFCyber IPR exhibits

### 4. **USENET Archives** (Google Groups)
- Engineer discussions with timestamps
- Product mentions before release
- Technical Q&A with dates
- **Example**: `comp.arch.embedded` posts about PN511

### 5. **University Archives**
- Course materials (MIT, Stanford, etc.)
- Lab pages with equipment lists
- Thesis repositories
- **Example**: `site:mit.edu "PN511" filetype:pdf`

### 6. **Distributor Archives**
- Old datasheets from Digi-Key, Mouser, Arrow
- Product catalogs via Wayback
- Findchips.com aggregation
- **Example**: PN511 datasheet from 2003

### 7. **Internet Archive Texts**
- Trade magazines (Electronics Weekly, EDN, etc.)
- Technical books
- Conference proceedings
- **Example**: NFC articles from 2003-2004

### 8. **GitHub/GitLab**
- Open source project documentation
- Datasheets in repos
- Technical wikis
- **Example**: NFC reader projects using PN511

### 9. **Technical Forums**
- Stack Overflow, EE StackExchange
- Reddit (r/embedded, r/electronics)
- Dated technical discussions
- **Example**: PN511 implementation questions

---

## Strict Filtering Rules

### ❌ Automatically Filtered Out

1. **Known Citations** - Anything in your `known_citations.csv`:
   - Exact DOI match
   - Exact patent number match
   - Fuzzy title match (>85% similar)
   - Same authors + same year

2. **Paywalled Documents** - No exceptions:
   - Must be open access OR
   - Must be available via school library (tagged `Access: school`)
   - Unpaywall verification required

3. **Low Quality** - ML scoring filters:
   - Predicted rank 0 (no value)
   - Low semantic confidence (<0.6)
   - No explicit anchors
   - Weak requirement matches

### ✅ What Gets Through

- **Open access** documents only
- **NOT in known_citations.csv**
- **Before critical date**
- **Strong semantic match** to requirements
- **Explicit anchors** (part numbers, technical terms)
- **ML score ≥ 2** (predicted rank)

---

## Example: Hunt for Study 25657 (Philips PN511)

```python
from pathlib import Path
from ai_engine import HuntOrchestrator, HuntConfig

hunt_config = HuntConfig(
    study_id="25657",
    study_folder=Path("25657_Integrated_Circuit_Chips"),
    critical_date="2005-01-10",
    
    keywords=[
        "PN511", "PN531", "PN512", 
        "NFC", "near field communication",
        "contactless", "RFID", "13.56 MHz",
        "ISO 14443", "Philips Semiconductors"
    ],
    part_numbers=["PN511", "PN531", "PN512"],
    manufacturers=["Philips", "NXP"],
    target_domains=[
        "semiconductors.philips.com",
        "nxp.com",
        "philips.com"
    ],
    patent_number="7373531",  # For PTAB search
    
    # Enable all sources
    enable_wayback=True,
    enable_fcc=True,
    enable_ptab=True,
    enable_usenet=True,
    enable_university=True,
    enable_distributor=True,
    enable_archive_texts=True,
    enable_github=True,
    enable_forums=True,
    
    max_results_per_source=20
)

orchestrator = HuntOrchestrator(hunt_config)
report = orchestrator.execute_hunt()

# Check results
print(f"\nHunt Results:")
print(f"  Searched {report['summary']['sources_searched']} sources")
print(f"  Found {report['summary']['total_found']} documents")
print(f"  Filtered {report['statistics']['filtered_known']} known citations")
print(f"  Filtered {report['statistics']['filtered_paywall']} paywalled docs")
print(f"  Generated {report['summary']['ready_to_submit']} READY_SUBMIT candidates")

# Files written to: 25657_Integrated_Circuit_Chips/candidates/
```

---

## Integration with Existing Bot

Add to your `system_prompt.md`:

```markdown
## AUTOMATED HUNT COMMAND

When user says `hunt <study_id> deep`, execute:

```python
from ai_engine import HuntOrchestrator, HuntConfig

# Load study config
config = HuntConfig(
    study_id=study_id,
    study_folder=Path(f"{study_id}_*/"),
    critical_date=critical_date,
    keywords=keywords_from_brief,
    part_numbers=part_numbers_from_brief,
    manufacturers=manufacturers_from_brief,
    target_domains=domains_from_brief,
    patent_number=patent_from_brief,
    enable_wayback=True,
    enable_fcc=True,
    enable_ptab=True,
    enable_usenet=True,
    enable_university=True,
    enable_distributor=True,
    enable_archive_texts=True,
    enable_github=True,
    enable_forums=True
)

orchestrator = HuntOrchestrator(config)
report = orchestrator.execute_hunt()

# Surface READY_SUBMIT candidates to Angela
for candidate in report['candidates']:
    if candidate['tier'] == 'READY_SUBMIT':
        print(f"✓ {candidate['title']}")
        print(f"  Source: {candidate['source']}")
        print(f"  File: {candidate['filename']}")
```
```

---

## Statistics & Performance

After each hunt, you get detailed statistics:

```python
{
    'sources_searched': 9,
    'total_found': 156,
    'filtered_known': 42,      # Matched known_citations.csv
    'filtered_paywall': 38,    # Behind paywall
    'filtered_low_score': 51,  # ML scored too low
    'candidates_generated': 25,
    'ready_submit': 8,
    'hold': 17,
    'success_rate': 0.051      # 5.1% of raw finds become submissions
}
```

**Typical Performance:**
- **9 sources** searched in parallel
- **100-200 raw finds** per hunt
- **30-50% filtered** as known citations
- **20-30% filtered** as paywalled
- **20-40% filtered** as low quality
- **5-10% become** READY_SUBMIT candidates

---

## Advanced: Custom Source Configuration

Search specific sources only:

```python
hunt_config = HuntConfig(
    study_id="25974",
    study_folder=Path("25974_Oximidol"),
    critical_date="2024-03-26",
    keywords=["Oximidol"],
    
    # Only search these sources
    enable_wayback=True,
    enable_ptab=True,
    enable_university=True,
    
    # Disable others
    enable_fcc=False,
    enable_usenet=False,
    enable_distributor=False,
    enable_archive_texts=False,
    enable_github=False,
    enable_forums=False
)
```

---

## Troubleshooting

### No results found?
- Check `known_citations.csv` is loaded correctly
- Verify keywords match actual terminology
- Try broader date range
- Enable more sources

### Too many low-quality results?
- Increase `min_confidence` (default 0.6)
- Reduce `max_results_per_source`
- Train ML model on your past submissions

### Known citations getting through?
- Verify `known_citations.csv` path
- Check CSV has `title`, `doi`, `patent_number` columns
- Run duplicate detector test

---

## Next Steps

1. **Run first hunt**: `python -c "from ai_engine import HuntOrchestrator, HuntConfig; ..."`
2. **Review candidates**: Check `candidates/READY_SUBMIT_*.txt`
3. **Submit best ones**: Copy to RWS portal
4. **Train ML model**: Feed back RWS scores to improve predictions
5. **Iterate**: Adjust keywords, enable/disable sources based on results

Your bot now searches **high and low** in places people never think to look! 🚀
