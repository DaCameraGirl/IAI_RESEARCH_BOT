"""
RWS Research Bot - AI Enhancement Engine
Intelligent automation layer for 1000x better prior art hunting
"""

__version__ = "2.0.0"
__author__ = "Angela Hudson"

from .semantic_matcher import SemanticMatcher
from .relevance_scorer import RelevanceScorer
from .submission_generator import SubmissionGenerator
from .duplicate_detector import DuplicateDetector
from .citation_analyzer import CitationAnalyzer
from .research_pipeline import ResearchPipeline
from .advanced_search import AdvancedSearchEngine, SearchResult
from .hunt_orchestrator import HuntOrchestrator, HuntConfig

__all__ = [
    'SemanticMatcher',
    'RelevanceScorer',
    'SubmissionGenerator',
    'DuplicateDetector',
    'CitationAnalyzer',
    'ResearchPipeline',
    'AdvancedSearchEngine',
    'SearchResult',
    'HuntOrchestrator',
    'HuntConfig'
]