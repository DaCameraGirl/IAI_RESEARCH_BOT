"""
AI Integration Script - Connect AI engine to existing RWS bot
Run this to enable AI-powered features in your research workflow
"""

import sys
from pathlib import Path
import json
import csv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_engine import (
    SemanticMatcher,
    RelevanceScorer,
    SubmissionGenerator,
    DuplicateDetector,
    CitationAnalyzer,
    ResearchPipeline
)


def create_study_config(study_id: str, study_folder: Path) -> Path:
    """
    Create AI-compatible study config from existing study data
    
    Args:
        study_id: Study identifier (e.g., "25974")
        study_folder: Path to study folder
        
    Returns:
        Path to created config file
    """
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / f"{study_id}_config.json"
    
    # Parse study brief if exists
    brief_path = study_folder / "STUDY_BRIEF.md"
    requirements = []
    
    if brief_path.exists():
        brief_text = brief_path.read_text(encoding='utf-8')
        
        # Extract requirements (RR1.1, RR1.2, etc.)
        import re
        req_pattern = r'\*\*(RR\d+\.\d+)\*\*[:\s]+(.+?)(?=\*\*RR|\Z)'
        matches = re.findall(req_pattern, brief_text, re.DOTALL)
        
        for req_id, req_text in matches:
            req_text = req_text.strip()
            requirements.append({
                'id': req_id,
                'text': req_text,
                'must_show_elements': [],  # TODO: Extract from brief
                'keywords': [],  # TODO: Extract from brief
                'priority': 1
            })
    
    # Create config
    config = {
        'study_id': study_id,
        'type': 'invalidity',  # TODO: Detect from dashboard
        'critical_date': '',  # TODO: Extract from dashboard
        'requirements': requirements,
        'priority_requirements': []  # TODO: Mark from RWS lead
    }
    
    # Write config
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Created config: {config_path}")
    return config_path


def setup_ai_for_study(study_id: str) -> ResearchPipeline:
    """
    Set up AI pipeline for a study
    
    Args:
        study_id: Study identifier
        
    Returns:
        Configured ResearchPipeline
    """
    # Find study folder
    study_folders = list(Path('.').glob(f"{study_id}_*"))
    if not study_folders:
        raise ValueError(f"Study folder not found for {study_id}")
    
    study_folder = study_folders[0]
    print(f"Found study folder: {study_folder}")
    
    # Create config if doesn't exist
    config_path = Path("config") / f"{study_id}_config.json"
    if not config_path.exists():
        config_path = create_study_config(study_id, study_folder)
    
    # Find known art CSV
    known_art_path = study_folder / "known_art" / "known_citations.csv"
    if not known_art_path.exists():
        # Try alternate location
        known_art_path = study_folder / f"{study_id}_knowncitations.csv"
    
    if not known_art_path.exists():
        raise ValueError(f"Known art CSV not found for {study_id}")
    
    print(f"✓ Found known art: {known_art_path}")
    
    # Create output directory
    output_dir = study_folder / "candidates"
    output_dir.mkdir(exist_ok=True)
    
    # Initialize pipeline
    pipeline = ResearchPipeline(
        study_id=study_id,
        study_config_path=config_path,
        known_art_path=known_art_path,
        output_dir=output_dir
    )
    
    print(f"✓ AI pipeline ready for study {study_id}")
    return pipeline


def demo_ai_features():
    """Demonstrate AI features with example"""
    print("\n" + "="*60)
    print("RWS Research Bot - AI Engine Demo")
    print("="*60 + "\n")
    
    # Example: Semantic matching
    print("1. SEMANTIC REQUIREMENT MATCHING")
    print("-" * 40)
    
    matcher = SemanticMatcher()
    
    requirements = [
        {
            'id': 'RR1.1',
            'text': 'Oximidol molecule as tyrosinase inhibitor',
            'must_show_elements': ['Oximidol', 'tyrosinase'],
            'keywords': ['alkylamidothiazole', 'melanin', 'whitening'],
            'priority': 1
        }
    ]
    
    matcher.load_requirements("demo", requirements)
    
    doc_text = """
    This study investigates Oximidol, a novel alkylamidothiazole derivative,
    as a potent tyrosinase inhibitor for skin whitening applications.
    Results show significant melanin reduction in vitro.
    """
    
    metadata = {'title': 'Demo Paper', 'date': '2023-01-15'}
    matches = matcher.match_document("demo", doc_text, metadata, min_confidence=0.5)
    
    for match in matches:
        print(f"  ✓ {match.requirement_id}: {match.confidence:.2f} confidence")
        print(f"    Anchor: {match.anchor_strength}")
        print(f"    Reasoning: {match.reasoning}\n")
    
    # Example: Relevance scoring
    print("\n2. ML-BASED RELEVANCE SCORING")
    print("-" * 40)
    
    scorer = RelevanceScorer()
    
    from ai_engine.relevance_scorer import ScoringFeatures
    
    features = ScoringFeatures(
        has_doi=True,
        has_issn=True,
        peer_reviewed=True,
        open_access=True,
        school_access=False,
        days_before_critical=500,
        publication_year=2023,
        num_requirements_matched=2,
        num_strong_anchors=2,
        num_medium_anchors=0,
        num_weak_anchors=0,
        avg_semantic_confidence=0.85,
        max_semantic_confidence=0.90,
        document_length_chars=5000,
        num_technical_terms=45,
        num_citations=12,
        source_type='journal',
        publisher_tier='top',
        study_type='invalidity',
        is_priority_requirement=True
    )
    
    result = scorer.score_candidate(features)
    
    print(f"  Predicted Rank: {result.predicted_rank}")
    print(f"  Confidence: {result.rank_confidence:.2f}")
    print(f"  In-scope: {result.in_scope_confidence}")
    print(f"  Recommendation: {result.recommendation}")
    print(f"  Reasoning: {result.reasoning}\n")
    
    # Example: Duplicate detection
    print("\n3. DUPLICATE DETECTION")
    print("-" * 40)
    
    detector = DuplicateDetector()
    
    known_art = [
        {
            'title': 'Oximidol as Tyrosinase Inhibitor',
            'authors': 'Smith J',
            'doi': '10.1234/known',
            'date': '2022-01-01'
        }
    ]
    
    detector.load_known_art("demo", known_art)
    
    # Check duplicate
    candidate = {
        'title': 'Oximidol as Tyrosinase Inhibitor',  # Same title
        'authors': 'Smith J',
        'doi': '10.1234/known',
        'date': '2022-01-01'
    }
    
    dup_result = detector.check_duplicate("demo", candidate)
    
    print(f"  Is Duplicate: {dup_result.is_duplicate}")
    print(f"  Confidence: {dup_result.confidence:.2f}")
    print(f"  Match Type: {dup_result.match_type}")
    print(f"  Reasoning: {dup_result.reasoning}\n")
    
    print("\n" + "="*60)
    print("AI Engine is working! Ready to process real candidates.")
    print("="*60 + "\n")


def main():
    """Main integration script"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Integrate AI engine with RWS research bot"
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run AI features demo'
    )
    parser.add_argument(
        '--setup',
        type=str,
        help='Set up AI for study (e.g., --setup 25974)'
    )
    parser.add_argument(
        '--process',
        type=str,
        help='Process candidate file (path to PDF or text)'
    )
    
    args = parser.parse_args()
    
    if args.demo:
        demo_ai_features()
    
    elif args.setup:
        pipeline = setup_ai_for_study(args.setup)
        print(f"\n✓ AI pipeline ready for study {args.setup}")
        print(f"  Use: pipeline.process_candidate(metadata, text)")
    
    elif args.process:
        print("Candidate processing not yet implemented")
        print("Use ResearchPipeline.process_candidate() directly")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
