"""
Hunt with Auto-Detected Search Strategy
No more hardcoded studies - each study gets its own strategy!
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.study_loader import StudyLoader
from ai_engine.hunt_orchestrator import HuntOrchestrator, HuntConfig


def hunt_study(study_id: str, workspace_root: Path = Path(".")):
    """
    Hunt for prior art using study-specific search strategy
    
    Args:
        study_id: Study ID (e.g., "26052")
        workspace_root: Root directory of workspace
    """
    print(f"\n{'='*60}")
    print(f"Starting hunt for study {study_id}")
    print(f"{'='*60}\n")
    
    # Load study configuration
    loader = StudyLoader(workspace_root)
    study = loader.get_study(study_id)
    
    if not study:
        print(f"❌ Study {study_id} not found!")
        print(f"Available studies: {list(loader.active_studies.keys())}")
        return
    
    print(f"Study: {study['study_name']}")
    print(f"Type: {study['type']}")
    print(f"Critical Date: {study.get('critical_date', 'Not set')}")
    print(f"Known Citations: {study.get('known_citations_count', 0)}")
    
    # Load search strategy
    strategy = loader.get_search_strategy(study_id)
    
    if not strategy:
        print(f"⚠ No search strategy found, using default")
        strategy = {
            'name': 'Default',
            'sources': {
                'wayback': {'enabled': True, 'priority': 1},
                'ptab': {'enabled': True, 'priority': 1}
            }
        }
    
    print(f"\nSearch Strategy: {strategy.get('name', 'Unknown')}")
    print(f"Description: {strategy.get('description', 'N/A')}")
    
    # Show enabled sources
    enabled_sources = []
    for source_name, source_config in strategy.get('sources', {}).items():
        if source_config.get('enabled', False):
            priority = source_config.get('priority', 3)
            enabled_sources.append((priority, source_name))
    
    enabled_sources.sort()  # Sort by priority
    
    print(f"\nEnabled Sources ({len(enabled_sources)}):")
    for priority, source_name in enabled_sources:
        print(f"  [{priority}] {source_name}")
    
    # Configure hunt based on strategy
    hunt_config = HuntConfig(
        study_id=study['study_id'],
        study_folder=Path(study['study_folder']),
        critical_date=study.get('critical_date', ''),
        keywords=study.get('keywords', []),
        patent_number=study.get('patent_number', ''),
        
        # Apply strategy - enable only sources in strategy
        enable_wayback=strategy['sources'].get('wayback', {}).get('enabled', False),
        enable_fcc=strategy['sources'].get('fcc', {}).get('enabled', False),
        enable_ptab=strategy['sources'].get('ptab', {}).get('enabled', False),
        enable_usenet=strategy['sources'].get('usenet', {}).get('enabled', False),
        enable_university=strategy['sources'].get('university', {}).get('enabled', False),
        enable_distributor=strategy['sources'].get('distributor', {}).get('enabled', False),
        enable_archive_texts=strategy['sources'].get('archive_texts', {}).get('enabled', False),
        enable_github=strategy['sources'].get('github', {}).get('enabled', False),
        enable_forums=strategy['sources'].get('forums', {}).get('enabled', False),
        
        # Rate limiting to prevent HTTP 503
        max_results_per_source=10
    )
    
    print(f"\n{'='*60}")
    print(f"Executing hunt with rate limiting...")
    print(f"{'='*60}\n")
    
    # Execute hunt
    orchestrator = HuntOrchestrator(hunt_config)
    report = orchestrator.execute_hunt()
    
    # Display results
    print(f"\n{'='*60}")
    print(f"Hunt Complete!")
    print(f"{'='*60}\n")
    
    print(f"Total Found: {report['statistics']['total_found']}")
    print(f"Filtered (known): {report['statistics']['filtered_known']}")
    print(f"Filtered (paywall): {report['statistics']['filtered_paywall']}")
    print(f"Rate Limit Hits: {report['statistics'].get('rate_limit_hits', 0)}")
    print(f"Final Candidates: {len(report['candidates'])}")
    
    # Show READY_SUBMIT candidates
    ready_submit = [c for c in report['candidates'] if c['tier'] == 'READY_SUBMIT']
    
    if ready_submit:
        print(f"\n✅ READY_SUBMIT Candidates ({len(ready_submit)}):")
        for candidate in ready_submit:
            print(f"  • {candidate['title']}")
            print(f"    File: {candidate['filename']}")
            print(f"    Score: {candidate.get('ml_score', 0):.2f}")
    else:
        print(f"\n⚠ No READY_SUBMIT candidates found")
    
    # Show HOLD candidates
    hold = [c for c in report['candidates'] if c['tier'] == 'HOLD']
    
    if hold:
        print(f"\n📋 HOLD Candidates ({len(hold)}):")
        for candidate in hold[:5]:  # Show first 5
            print(f"  • {candidate['title']}")
            print(f"    File: {candidate['filename']}")
    
    print(f"\n{'='*60}")
    print(f"Results saved to: {study['study_folder']}/candidates/")
    print(f"{'='*60}\n")


def show_all_studies(workspace_root: Path = Path(".")):
    """Show all active studies and their strategies"""
    loader = StudyLoader(workspace_root)
    
    print(f"\n{'='*60}")
    print(f"Active Studies")
    print(f"{'='*60}\n")
    
    for study in loader.get_active_studies():
        print(f"Study {study['study_id']}: {study['study_name']}")
        print(f"  Type: {study['type']}")
        print(f"  Critical Date: {study.get('critical_date', 'Not set')}")
        print(f"  Known Citations: {study.get('known_citations_count', 0)}")
        
        strategy = loader.get_search_strategy(study['study_id'])
        if strategy:
            print(f"  Strategy: {strategy.get('name', 'Unknown')}")
            enabled = [
                name for name, cfg in strategy.get('sources', {}).items()
                if cfg.get('enabled', False)
            ]
            print(f"  Sources: {', '.join(enabled)}")
        
        print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Hunt for prior art using study-specific search strategies"
    )
    parser.add_argument(
        "study_id",
        nargs="?",
        help="Study ID to hunt (e.g., 26052)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all active studies and their strategies"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("."),
        help="Workspace root directory"
    )
    
    args = parser.parse_args()
    
    if args.list:
        show_all_studies(args.workspace)
    elif args.study_id:
        hunt_study(args.study_id, args.workspace)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python hunt_with_strategy.py 26052")
        print("  python hunt_with_strategy.py --list")
