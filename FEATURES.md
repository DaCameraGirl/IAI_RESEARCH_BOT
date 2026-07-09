# RWS Research Bot - Feature Documentation

## Overview

This document describes all AI-powered features available in the RWS Research Bot.

---

## ✅ Phase 1: Quick Wins (IMPLEMENTED)

### 1. Dashboard Auto-Update
**File:** `ai_engine/dashboard_updater.py`

Automatically updates `_DASHBOARD.md` after each hunt with:
- Hunt completion dates
- Candidate counts (READY_SUBMIT vs HOLD)
- Success rates
- Next actions

**Usage:**
```python
from ai_engine.dashboard_updater import DashboardUpdater

updater = DashboardUpdater(Path("."))
updater.update_after_hunt(hunt_report)
```

### 2. Email Notifications
**File:** `ai_engine/email_notifier.py`

Sends email notifications when READY_SUBMIT candidates are found.

**Setup:**
1. Edit `config/email_config.json`
2. Set `enabled: true`
3. Configure SMTP settings (Gmail, Outlook, etc.)
4. For Gmail: Use App Password (not regular password)

**Usage:**
```python
from ai_engine.email_notifier import EmailNotifier

notifier = EmailNotifier()
notifier.notify_hunt_complete(hunt_report)
```

### 3. Batch Processing
**File:** `ai_engine/batch_processor.py`

Hunt multiple studies in parallel with progress tracking.

**Features:**
- Parallel execution (configurable workers)
- Progress tracking
- Error handling and retry
- Dashboard updates
- Email notifications
- Summary report

**Usage:**
```python
from ai_engine.batch_processor import BatchProcessor
from config.study_loader import StudyLoader

loader = StudyLoader(Path("."))
processor = BatchProcessor(Path("."), max_workers=3)

# Hunt all active studies
batch_report = processor.hunt_all_active_studies(loader)

# Or hunt specific studies
batch_report = processor.hunt_studies(['26052', '25974'], loader)
```

### 4. Smart Retry
**File:** `ai_engine/smart_retry.py`

Intelligent retry logic with exponential backoff and strategy adaptation.

**Features:**
- Exponential backoff
- Jitter to avoid thundering herd
- Adaptive strategy (learns from failure patterns)
- Automatic retry for transient errors
- Skip non-retryable errors (404, 401, etc.)

**Usage:**
```python
from ai_engine.smart_retry import retry, adaptive_retry_decorator

# Simple retry
@retry(max_retries=3)
def fetch_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

# Adaptive retry (learns and adapts)
@adaptive_retry_decorator(max_retries=5)
def fetch_api(endpoint):
    response = requests.get(f"https://api.example.com/{endpoint}")
    response.raise_for_status()
    return response.json()
```

### 5. PDF Preview
**File:** `ai_engine/pdf_previewer.py`

Generate preview images from PDF first page for quality verification.

**Features:**
- First page thumbnail generation
- Text extraction from first page
- Metadata extraction
- Quality assessment
- HTML preview generation

**Usage:**
```python
from ai_engine.pdf_previewer import PDFPreviewer

previewer = PDFPreviewer()

# From URL
preview = previewer.generate_preview(pdf_url="https://example.com/doc.pdf")

# From local file
preview = previewer.generate_preview(pdf_path=Path("document.pdf"))

# Save as HTML
previewer.save_preview_html(preview, Path("preview.html"))
```

---

## ✅ Phase 2: Power Features (IMPLEMENTED)

### 6. Citation Graph Crawler
**File:** `ai_engine/citation_crawler.py`

Crawl citation networks to discover related prior art.

**Features:**
- Backward citations (references)
- Forward citations (cited by)
- Multi-hop crawling (configurable depth)
- Date filtering (critical date)
- Duplicate detection
- Works with patents and NPL

**Usage:**
```python
from ai_engine.citation_crawler import CitationCrawler

crawler = CitationCrawler(
    max_depth=2,
    max_citations_per_doc=20,
    critical_date="2019-10-28"
)

# Crawl from patent
discovered = crawler.crawl_from_patent(
    patent_number="US7373531",
    direction="both"  # or "backward" or "forward"
)

# Crawl from NPL
discovered = crawler.crawl_from_npl(
    doi="10.1234/example",
    direction="both"
)
```

### 7. Patent Family Analysis
**File:** `ai_engine/patent_family_analyzer.py`

Find related patents (continuations, divisionals, foreign equivalents).

**Features:**
- Continuations (CON)
- Continuations-in-part (CIP)
- Divisionals (DIV)
- Provisional applications
- Foreign equivalents (PCT, EP, JP, etc.)
- Priority claims
- Family tree visualization

**Usage:**
```python
from ai_engine.patent_family_analyzer import PatentFamilyAnalyzer

analyzer = PatentFamilyAnalyzer(critical_date="2019-10-28")

# Analyze patent family
family_data = analyzer.analyze_patent_family("US7373531")

# Find parent patents
parents = analyzer.find_parent_patents("US7373531")

# Find child patents
children = analyzer.find_child_patents("US7373531")

# Visualize family tree
tree = analyzer.visualize_family_tree("US7373531")
print(tree)
```

### 8. Duplicate Detection
**File:** `ai_engine/duplicate_detector.py`

Detect duplicate candidates across studies to prevent submitting the same prior art multiple times.

**Features:**
- Exact match detection (URL, DOI, patent number)
- Fuzzy title matching (configurable threshold)
- Content similarity detection
- Cross-study duplicate tracking
- Deduplication recommendations

**Usage:**
```python
from ai_engine.duplicate_detector import DuplicateDetector

detector = DuplicateDetector(
    workspace_root=Path("."),
    title_similarity_threshold=0.85,
    content_similarity_threshold=0.90
)

# Check candidate
result = detector.check_candidate(candidate, study_id="26052")

if result['is_duplicate']:
    print(f"Duplicate found: {result['duplicate_type']}")
    print(f"Recommendation: {result['recommendation']}")

# Get duplicate report
report = detector.get_duplicate_report()

# Clear study candidates after submission
detector.clear_study_candidates("26052")
```

---

## ✅ Phase 3: AI Enhancements (IMPLEMENTED)

### 9. Timeline Visualization
**File:** `ai_engine/timeline_visualizer.py`

Generate visual timelines showing prior art dates vs critical date.

**Features:**
- ASCII timeline for terminal
- Interactive HTML timeline
- Critical date highlighting
- Date gap analysis
- Temporal clustering

**Usage:**
```python
from ai_engine.timeline_visualizer import TimelineVisualizer

visualizer = TimelineVisualizer(critical_date="2019-10-28")

# Generate ASCII timeline
ascii_timeline = visualizer.generate_ascii_timeline(candidates)
print(ascii_timeline)

# Generate HTML timeline
visualizer.generate_html_timeline(candidates, Path("timeline.html"))

# Analyze date gaps
gap_analysis = visualizer.analyze_date_gaps(candidates)
```

### 10. Confidence Scoring
**File:** `ai_engine/confidence_scorer.py`

Calculate confidence scores for candidates based on multiple factors.

**Features:**
- Multi-factor scoring (date, source, content, keywords, document type, accessibility)
- Weighted scoring algorithm
- Tier determination (READY_SUBMIT, HOLD, REJECT)
- Batch scoring
- Confidence reports

**Usage:**
```python
from ai_engine.confidence_scorer import ConfidenceScorer

scorer = ConfidenceScorer(critical_date="2019-10-28")

# Score single candidate
scoring = scorer.score_candidate(candidate, keywords=['blender', 'offset'])
print(f"Score: {scoring['total_score']:.2f}, Tier: {scoring['tier']}")

# Batch score and sort
scored_candidates = scorer.batch_score(candidates, keywords)

# Generate report
report = scorer.generate_confidence_report(scored_candidates)
```

### 11. Smart Keyword Expansion
**File:** `ai_engine/keyword_expander.py`

Automatically expand keywords based on search results and domain knowledge.

**Features:**
- Synonym discovery
- Technical term extraction
- Compound term generation
- Keyword effectiveness analysis
- Acronym expansion

**Usage:**
```python
from ai_engine.keyword_expander import KeywordExpander

expander = KeywordExpander(min_frequency=2)

# Expand keywords
expanded = expander.expand_keywords(
    base_keywords=['blender', 'offset', 'blade'],
    search_results=results,
    max_expansions=10
)

# Analyze effectiveness
effectiveness = expander.analyze_keyword_effectiveness(keywords, results)

# Get suggestions
suggestions = expander.suggest_new_keywords(keywords, results)
```

### 12. Auto-Requirement Extraction
**File:** `ai_engine/requirement_extractor.py`

Extract requirements from study brief documents automatically.

**Features:**
- Critical date extraction
- Keyword extraction
- Part number extraction
- Manufacturer extraction
- Patent number extraction
- Technical requirement parsing
- Search strategy determination

**Usage:**
```python
from ai_engine.requirement_extractor import RequirementExtractor

extractor = RequirementExtractor()

# Extract from file
requirements = extractor.extract_from_file(Path("STUDY_BRIEF.md"))

# Generate search config
config = extractor.generate_search_config(requirements)

# Validate requirements
validation = extractor.validate_requirements(requirements)
```

### 13. Quality Prediction
**File:** `ai_engine/quality_predictor.py`

Predict RWS acceptance rate based on historical data.

**Features:**
- Historical acceptance tracking
- Feature-based prediction
- Study-specific learning
- Source credibility analysis
- Confidence calibration

**Usage:**
```python
from ai_engine.quality_predictor import QualityPredictor

predictor = QualityPredictor(Path("."))

# Predict acceptance
prediction = predictor.predict_acceptance(candidate)
print(f"Acceptance probability: {prediction['acceptance_probability']:.1%}")

# Record outcome (for learning)
predictor.record_submission(candidate, accepted=True, study_id='26052')

# Generate report
report = predictor.generate_quality_report()
```

### 14. Audit Trail
**File:** `ai_engine/audit_logger.py`

Log all bot activities for compliance and audit trail.

**Features:**
- Hunt logging
- Decision logging
- User action logging
- Compliance tracking
- Export capabilities
- Session tracking

**Usage:**
```python
from ai_engine.audit_logger import AuditLogger

logger = AuditLogger(Path("."))

# Log hunt
logger.log_hunt_start(study_id='26052', config=hunt_config)
logger.log_hunt_complete(study_id='26052', statistics=stats, duration_seconds=45.2)

# Log candidate
logger.log_candidate_generated(study_id='26052', candidate=candidate, tier='READY_SUBMIT', reasoning='High confidence')

# Generate compliance report
report = logger.generate_compliance_report('26052')

# Export logs
logger.export_logs(start_date='2026-01-01', study_id='26052')
```

---

## Integration Examples

### Complete Hunt with All Features

```python
from pathlib import Path
from config.study_loader import StudyLoader
from ai_engine.hunt_orchestrator import HuntOrchestrator, HuntConfig
from ai_engine.dashboard_updater import DashboardUpdater
from ai_engine.email_notifier import EmailNotifier
from ai_engine.duplicate_detector import DuplicateDetector
from ai_engine.citation_crawler import CitationCrawler
from ai_engine.patent_family_analyzer import PatentFamilyAnalyzer

# Initialize components
workspace_root = Path(".")
loader = StudyLoader(workspace_root)
dashboard = DashboardUpdater(workspace_root)
notifier = EmailNotifier()
dup_detector = DuplicateDetector(workspace_root)

# Load study
study = loader.get_study("26052")
strategy = loader.get_search_strategy("26052")

# Configure hunt
hunt_config = HuntConfig(
    study_id=study['study_id'],
    study_folder=Path(study['study_folder']),
    critical_date=study.get('critical_date', ''),
    keywords=study.get('keywords', []),
    # ... other config
)

# Execute hunt
orchestrator = HuntOrchestrator(hunt_config)
report = orchestrator.execute_hunt()

# Check for duplicates
for candidate in report['candidates']:
    dup_result = dup_detector.check_candidate(candidate, study['study_id'])
    if dup_result['is_duplicate']:
        print(f"⚠ Duplicate: {candidate['title']}")

# Crawl citations for top candidates
crawler = CitationCrawler(max_depth=2, critical_date=study.get('critical_date'))
for candidate in report['candidates'][:3]:
    if candidate.get('patent_number'):
        discovered = crawler.crawl_from_patent(candidate['patent_number'])
        print(f"Found {len(discovered)} related patents")

# Analyze patent families
analyzer = PatentFamilyAnalyzer(critical_date=study.get('critical_date'))
for candidate in report['candidates'][:3]:
    if candidate.get('patent_number'):
        family = analyzer.analyze_patent_family(candidate['patent_number'])
        print(f"Found {len(family['family_members'])} family members")

# Update dashboard
dashboard.update_after_hunt(report)

# Send notification
notifier.notify_hunt_complete(report)

print("✓ Hunt complete with all features!")
```

### Batch Hunt with All Features

```python
from ai_engine.batch_processor import BatchProcessor

processor = BatchProcessor(
    workspace_root=Path("."),
    max_workers=3,
    enable_notifications=True
)

# Hunt all active studies
batch_report = processor.hunt_all_active_studies(loader)

print(f"✓ Batch complete!")
print(f"  Total READY_SUBMIT: {batch_report['statistics']['total_ready_submit']}")
```

---

## Configuration Files

### Email Configuration
**File:** `config/email_config.json`

```json
{
  "enabled": true,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "use_tls": true,
  "sender_email": "your-email@gmail.com",
  "sender_password": "your-app-password",
  "recipient_email": "your-email@gmail.com",
  "notify_on_ready_submit": true,
  "notify_on_hold": false,
  "min_candidates_to_notify": 1,
  "subject_template": "[RWS Bot] {count} READY_SUBMIT candidates found for study {study_id}",
  "include_candidate_details": true
}
```

---

## Performance Tips

1. **Batch Processing**: Use `max_workers=3` for optimal performance
2. **Rate Limiting**: Already built-in to prevent HTTP 503 errors
3. **Smart Retry**: Automatically handles transient failures
4. **Duplicate Detection**: Runs in O(1) time using indexes
5. **Citation Crawling**: Limit `max_depth=2` to avoid excessive API calls

---

## Troubleshooting

### Email Notifications Not Working
1. Check `config/email_config.json` has `enabled: true`
2. For Gmail: Use App Password (Settings → Security → App Passwords)
3. Check firewall/antivirus settings
4. Test with: `python -m ai_engine.email_notifier`

### Batch Processing Slow
1. Increase `max_workers` (default: 3, max: 5)
2. Check network connection
3. Review rate limiting settings

### Duplicate Detection False Positives
1. Adjust `title_similarity_threshold` (default: 0.85)
2. Adjust `content_similarity_threshold` (default: 0.90)
3. Clear database: Delete `.bob/tmp/duplicates.json`

---

## API Rate Limits

- **Semantic Scholar**: 100 requests/5 minutes
- **USPTO**: No official limit (use rate_limiter)
- **Google Patents**: No official limit (use rate_limiter)
- **Wayback Machine**: 15 requests/minute

All features use built-in rate limiting to stay within limits.

---

## Future Enhancements

See todo list for planned features:
- Timeline visualization
- Confidence scoring dashboard
- Smart keyword expansion
- Auto-requirement extraction
- Quality prediction
- Audit trail

---

## Support

For issues or questions:
1. Check this documentation
2. Review example usage in each module's `__main__` section
3. Check GitHub issues: https://github.com/DaCameraGirl/RWS_RESEARCHER/issues
