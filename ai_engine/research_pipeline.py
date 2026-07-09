"""
Research Pipeline - Integrated AI workflow for RWS prior art hunting
Orchestrates all AI components for end-to-end automation
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

from .semantic_matcher import SemanticMatcher, Requirement
from .relevance_scorer import RelevanceScorer, ScoringFeatures
from .submission_generator import SubmissionGenerator
from .duplicate_detector import DuplicateDetector
from .citation_analyzer import CitationAnalyzer


class ResearchPipeline:
    """
    End-to-end AI research pipeline:
    1. Load study configuration and known art
    2. Process candidate documents
    3. Semantic requirement matching
    4. ML-based relevance scoring
    5. Duplicate detection
    6. Automated submission generation
    7. Citation graph analysis
    """
    
    def __init__(
        self,
        study_id: str,
        study_config_path: Path,
        known_art_path: Path,
        output_dir: Path
    ):
        """
        Initialize research pipeline
        
        Args:
            study_id: Study identifier (e.g., "25974")
            study_config_path: Path to study config JSON
            known_art_path: Path to known_citations.csv
            output_dir: Output directory for submissions
        """
        self.study_id = study_id
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load study configuration
        with open(study_config_path) as f:
            self.study_config = json.load(f)
        
        # Initialize AI components
        self.semantic_matcher = SemanticMatcher()
        self.relevance_scorer = RelevanceScorer()
        self.submission_generator = SubmissionGenerator()
        self.duplicate_detector = DuplicateDetector()
        self.citation_analyzer = CitationAnalyzer()
        
        # Load study data
        self._load_study_data(known_art_path)
        
        # Statistics
        self.stats = {
            'processed': 0,
            'duplicates': 0,
            'skipped': 0,
            'hold': 0,
            'ready_submit': 0
        }
    
    def _load_study_data(self, known_art_path: Path):
        """Load study requirements and known art"""
        # Load requirements into semantic matcher
        requirements = self.study_config.get('requirements', [])
        self.semantic_matcher.load_requirements(self.study_id, requirements)
        
        # Load known art into duplicate detector
        known_art = self._load_known_art_csv(known_art_path)
        self.duplicate_detector.load_known_art(self.study_id, known_art)
        
        # Load known art into citation analyzer
        self.citation_analyzer.load_seed_documents(known_art)
    
    def _load_known_art_csv(self, csv_path: Path) -> List[Dict]:
        """Load known art from CSV file"""
        import csv
        
        known_art = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                known_art.append(row)
        
        return known_art
    
    def process_candidate(
        self,
        document_metadata: Dict,
        document_text: str,
        auto_submit: bool = False
    ) -> Dict:
        """
        Process a single candidate document through full pipeline
        
        Args:
            document_metadata: Document metadata dict
            document_text: Full document text
            auto_submit: If True, auto-write READY_SUBMIT to file
            
        Returns:
            Processing result dict with all analysis
        """
        self.stats['processed'] += 1
        
        result = {
            'candidate_id': document_metadata.get('title', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'status': 'processing'
        }
        
        # Step 1: Duplicate detection
        print(f"[1/5] Checking for duplicates...")
        duplicate_check = self.duplicate_detector.check_duplicate(
            self.study_id,
            document_metadata,
            document_text
        )
        
        result['duplicate_check'] = {
            'is_duplicate': duplicate_check.is_duplicate,
            'confidence': duplicate_check.confidence,
            'match_type': duplicate_check.match_type,
            'reasoning': duplicate_check.reasoning
        }
        
        if duplicate_check.is_duplicate:
            self.stats['duplicates'] += 1
            result['status'] = 'duplicate'
            result['recommendation'] = 'SKIP - Duplicate of known art'
            return result
        
        # Step 2: Semantic requirement matching
        print(f"[2/5] Matching requirements...")
        match_results = self.semantic_matcher.match_document(
            self.study_id,
            document_text,
            document_metadata,
            min_confidence=0.6
        )
        
        result['matches'] = [
            {
                'requirement_id': m.requirement_id,
                'confidence': m.confidence,
                'anchor_strength': m.anchor_strength,
                'reasoning': m.reasoning
            }
            for m in match_results
        ]
        
        if not match_results:
            self.stats['skipped'] += 1
            result['status'] = 'no_match'
            result['recommendation'] = 'SKIP - No requirements matched'
            return result
        
        # Step 3: ML-based relevance scoring
        print(f"[3/5] Scoring relevance...")
        features = self.relevance_scorer.extract_features(
            document_metadata,
            match_results,
            self.study_config
        )
        
        scoring_result = self.relevance_scorer.score_candidate(features)
        
        result['scoring'] = {
            'predicted_rank': scoring_result.predicted_rank,
            'rank_confidence': scoring_result.rank_confidence,
            'in_scope_confidence': scoring_result.in_scope_confidence,
            'recommendation': scoring_result.recommendation,
            'reasoning': scoring_result.reasoning
        }
        
        if scoring_result.recommendation == 'SKIP':
            self.stats['skipped'] += 1
            result['status'] = 'low_score'
            result['recommendation'] = f'SKIP - Rank {scoring_result.predicted_rank}'
            return result
        
        # Step 4: Generate submission block
        print(f"[4/5] Generating submission...")
        submission = self.submission_generator.generate_submission(
            document_metadata,
            match_results,
            scoring_result,
            self.study_config,
            document_text
        )
        
        result['submission'] = {
            'tier': submission.tier,
            'filename': submission.filename,
            'self_rank': submission.self_rank,
            'in_scope_confidence': submission.in_scope_confidence,
            'num_requirements': len(submission.selected_requirements)
        }
        
        # Step 5: Write to file
        print(f"[5/5] Writing submission...")
        submission_text = self.submission_generator.format_for_portal(submission)
        
        output_path = self.output_dir / submission.filename
        output_path.write_text(submission_text, encoding='utf-8')
        
        result['output_file'] = str(output_path)
        result['status'] = 'complete'
        result['recommendation'] = submission.tier
        
        # Update stats
        if submission.tier == 'READY_SUBMIT':
            self.stats['ready_submit'] += 1
        elif submission.tier == 'HOLD':
            self.stats['hold'] += 1
        
        return result
    
    def batch_process_candidates(
        self,
        candidates: List[Tuple[Dict, str]],
        max_workers: int = 4
    ) -> List[Dict]:
        """
        Process multiple candidates in parallel
        
        Args:
            candidates: List of (metadata, text) tuples
            max_workers: Number of parallel workers
            
        Returns:
            List of processing results
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self.process_candidate,
                    metadata,
                    text
                ): (metadata, text)
                for metadata, text in candidates
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    metadata, _ = futures[future]
                    results.append({
                        'candidate_id': metadata.get('title', 'unknown'),
                        'status': 'error',
                        'error': str(e)
                    })
        
        return results
    
    def analyze_citation_network(
        self,
        seed_document_id: str,
        depth: int = 2
    ) -> Dict:
        """
        Analyze citation network around a seed document
        
        Args:
            seed_document_id: Starting document ID
            depth: Citation graph depth
            
        Returns:
            Analysis results with discovered documents
        """
        critical_date = self.study_config.get('critical_date', '')
        
        # Crawl backward citations
        backward = self.citation_analyzer.crawl_backward(
            seed_document_id,
            critical_date,
            depth
        )
        
        # Crawl forward citations
        forward = self.citation_analyzer.crawl_forward(
            seed_document_id,
            critical_date,
            depth
        )
        
        # Find highly cited neighbors
        highly_cited = self.citation_analyzer.get_highly_cited_neighbors(
            seed_document_id,
            critical_date,
            min_citations=10
        )
        
        return {
            'seed_id': seed_document_id,
            'backward_citations': len(backward),
            'forward_citations': len(forward),
            'highly_cited': len(highly_cited),
            'discovered_documents': backward + forward,
            'priority_documents': highly_cited[:10]  # Top 10
        }
    
    def get_statistics(self) -> Dict:
        """Get pipeline statistics"""
        return {
            **self.stats,
            'success_rate': (
                self.stats['ready_submit'] / self.stats['processed']
                if self.stats['processed'] > 0 else 0.0
            )
        }
    
    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """
        Generate processing report
        
        Args:
            output_path: Optional path to write report
            
        Returns:
            Report text
        """
        stats = self.get_statistics()
        
        report_lines = [
            f"# RWS Research Pipeline Report",
            f"Study: {self.study_id}",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Statistics",
            f"- Total processed: {stats['processed']}",
            f"- Duplicates: {stats['duplicates']}",
            f"- Skipped (low score): {stats['skipped']}",
            f"- HOLD tier: {stats['hold']}",
            f"- READY_SUBMIT: {stats['ready_submit']}",
            f"- Success rate: {stats['success_rate']:.1%}",
            "",
            "## Output Files",
            f"Location: {self.output_dir}",
            ""
        ]
        
        report = "\n".join(report_lines)
        
        if output_path:
            output_path.write_text(report, encoding='utf-8')
        
        return report


# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = ResearchPipeline(
        study_id="25974",
        study_config_path=Path("config/25974_config.json"),
        known_art_path=Path("25974_Oximidol/known_art/known_citations.csv"),
        output_dir=Path("25974_Oximidol/candidates")
    )
    
    # Process a candidate
    candidate_metadata = {
        'title': 'Novel Tyrosinase Inhibitors',
        'authors': 'Smith J, Johnson A',
        'date': '2023-01-15',
        'doi': '10.1234/example',
        'journal': 'J Pharm Sci',
        'url': 'https://example.com/paper.pdf',
        'open_access': True
    }
    
    candidate_text = """
    This study investigates Oximidol as a tyrosinase inhibitor
    combined with Isopropyl Lauroyl Sarcosinate surfactant...
    """
    
    result = pipeline.process_candidate(candidate_metadata, candidate_text)
    
    print(f"Status: {result['status']}")
    print(f"Recommendation: {result['recommendation']}")
    
    if result.get('output_file'):
        print(f"Submission written to: {result['output_file']}")
    
    # Generate report
    report = pipeline.generate_report()
    print("\n" + report)
