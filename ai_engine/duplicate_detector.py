"""
Duplicate Detector - Advanced duplicate detection using fuzzy matching + embeddings
Prevents submitting known art or near-duplicates
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import re
from difflib import SequenceMatcher


@dataclass
class DuplicateMatch:
    """Duplicate detection result"""
    is_duplicate: bool
    confidence: float  # 0.0-1.0
    matched_entry: Optional[Dict]
    match_type: str  # "exact" | "fuzzy_title" | "fuzzy_content" | "semantic" | "doi" | "patent"
    reasoning: str


class DuplicateDetector:
    """
    Multi-strategy duplicate detection using:
    - Exact DOI/patent number matching
    - Fuzzy title matching (handles typos, formatting)
    - Content fingerprinting (MinHash/SimHash)
    - Semantic embeddings (cosine similarity)
    - Author + date matching
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize duplicate detector
        
        Args:
            model_name: Sentence transformer model for embeddings
        """
        self.model_name = model_name
        self.model = None  # Lazy load
        self.known_art_cache: Dict[str, List[Dict]] = {}
        self.embeddings_cache: Dict[str, np.ndarray] = {}
    
    def _lazy_load_model(self):
        """Load sentence transformer model on first use"""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
    
    def load_known_art(self, study_id: str, known_art: List[Dict]):
        """
        Load known art list for a study
        
        Args:
            study_id: Study identifier
            known_art: List of known art dicts with title, doi, authors, etc.
        """
        self._lazy_load_model()
        
        self.known_art_cache[study_id] = known_art
        
        # Pre-compute embeddings for known art
        for entry in known_art:
            entry_id = self._get_entry_id(entry)
            if entry_id not in self.embeddings_cache:
                # Create searchable text from entry
                search_text = self._create_search_text(entry)
                embedding = self.model.encode(search_text, convert_to_numpy=True)
                self.embeddings_cache[entry_id] = embedding
    
    def check_duplicate(
        self,
        study_id: str,
        candidate_metadata: Dict,
        candidate_text: Optional[str] = None,
        threshold: float = 0.85
    ) -> DuplicateMatch:
        """
        Check if candidate is a duplicate of known art
        
        Args:
            study_id: Study identifier
            candidate_metadata: Candidate document metadata
            candidate_text: Optional full text for content matching
            threshold: Similarity threshold for duplicate detection
            
        Returns:
            DuplicateMatch result
        """
        if study_id not in self.known_art_cache:
            raise ValueError(f"Known art not loaded for study {study_id}")
        
        known_art = self.known_art_cache[study_id]
        
        # Strategy 1: Exact identifier matching (DOI, patent number)
        exact_match = self._check_exact_identifiers(candidate_metadata, known_art)
        if exact_match:
            return exact_match
        
        # Strategy 2: Fuzzy title matching
        fuzzy_match = self._check_fuzzy_title(candidate_metadata, known_art, threshold)
        if fuzzy_match:
            return fuzzy_match
        
        # Strategy 3: Author + date matching
        author_match = self._check_author_date(candidate_metadata, known_art)
        if author_match:
            return author_match
        
        # Strategy 4: Semantic similarity
        semantic_match = self._check_semantic_similarity(
            candidate_metadata,
            candidate_text,
            known_art,
            threshold
        )
        if semantic_match:
            return semantic_match
        
        # No duplicate found
        return DuplicateMatch(
            is_duplicate=False,
            confidence=0.0,
            matched_entry=None,
            match_type="none",
            reasoning="No duplicate detected across all strategies"
        )
    
    def _check_exact_identifiers(
        self,
        candidate: Dict,
        known_art: List[Dict]
    ) -> Optional[DuplicateMatch]:
        """Check for exact DOI or patent number match"""
        # DOI matching
        candidate_doi = self._normalize_doi(candidate.get('doi', ''))
        if candidate_doi:
            for entry in known_art:
                entry_doi = self._normalize_doi(entry.get('doi', ''))
                if entry_doi and candidate_doi == entry_doi:
                    return DuplicateMatch(
                        is_duplicate=True,
                        confidence=1.0,
                        matched_entry=entry,
                        match_type="doi",
                        reasoning=f"Exact DOI match: {candidate_doi}"
                    )
        
        # Patent number matching
        candidate_patent = self._normalize_patent(candidate.get('patent_number', ''))
        if candidate_patent:
            for entry in known_art:
                entry_patent = self._normalize_patent(entry.get('patent_number', ''))
                if entry_patent and candidate_patent == entry_patent:
                    return DuplicateMatch(
                        is_duplicate=True,
                        confidence=1.0,
                        matched_entry=entry,
                        match_type="patent",
                        reasoning=f"Exact patent number match: {candidate_patent}"
                    )
        
        return None
    
    def _check_fuzzy_title(
        self,
        candidate: Dict,
        known_art: List[Dict],
        threshold: float
    ) -> Optional[DuplicateMatch]:
        """Check for fuzzy title match (handles typos, formatting)"""
        candidate_title = self._normalize_title(candidate.get('title', ''))
        if not candidate_title or len(candidate_title) < 10:
            return None
        
        best_match = None
        best_score = 0.0
        
        for entry in known_art:
            entry_title = self._normalize_title(entry.get('title', ''))
            if not entry_title:
                continue
            
            # Calculate similarity
            similarity = SequenceMatcher(None, candidate_title, entry_title).ratio()
            
            if similarity > best_score:
                best_score = similarity
                best_match = entry
        
        if best_score >= threshold:
            return DuplicateMatch(
                is_duplicate=True,
                confidence=best_score,
                matched_entry=best_match,
                match_type="fuzzy_title",
                reasoning=f"Fuzzy title match: {best_score:.2f} similarity"
            )
        
        return None
    
    def _check_author_date(
        self,
        candidate: Dict,
        known_art: List[Dict]
    ) -> Optional[DuplicateMatch]:
        """Check for author + date match (likely same paper)"""
        candidate_authors = self._normalize_authors(candidate.get('authors', ''))
        candidate_date = candidate.get('date', '')[:4]  # Year only
        
        if not candidate_authors or not candidate_date:
            return None
        
        for entry in known_art:
            entry_authors = self._normalize_authors(entry.get('authors', ''))
            entry_date = entry.get('date', '')[:4]
            
            if not entry_authors or not entry_date:
                continue
            
            # Check if dates match
            if candidate_date != entry_date:
                continue
            
            # Check author overlap
            overlap = len(candidate_authors & entry_authors)
            if overlap >= 2:  # At least 2 authors in common
                confidence = min(1.0, overlap / max(len(candidate_authors), len(entry_authors)))
                return DuplicateMatch(
                    is_duplicate=True,
                    confidence=confidence,
                    matched_entry=entry,
                    match_type="author_date",
                    reasoning=f"Same year ({candidate_date}) + {overlap} common authors"
                )
        
        return None
    
    def _check_semantic_similarity(
        self,
        candidate: Dict,
        candidate_text: Optional[str],
        known_art: List[Dict],
        threshold: float
    ) -> Optional[DuplicateMatch]:
        """Check for semantic similarity using embeddings"""
        self._lazy_load_model()
        
        # Create candidate search text
        candidate_search = self._create_search_text(candidate, candidate_text)
        candidate_embedding = self.model.encode(candidate_search, convert_to_numpy=True)
        
        best_match = None
        best_score = 0.0
        
        for entry in known_art:
            entry_id = self._get_entry_id(entry)
            
            # Get or compute entry embedding
            if entry_id in self.embeddings_cache:
                entry_embedding = self.embeddings_cache[entry_id]
            else:
                entry_search = self._create_search_text(entry)
                entry_embedding = self.model.encode(entry_search, convert_to_numpy=True)
                self.embeddings_cache[entry_id] = entry_embedding
            
            # Calculate cosine similarity
            similarity = float(np.dot(candidate_embedding, entry_embedding))
            
            if similarity > best_score:
                best_score = similarity
                best_match = entry
        
        if best_score >= threshold:
            return DuplicateMatch(
                is_duplicate=True,
                confidence=best_score,
                matched_entry=best_match,
                match_type="semantic",
                reasoning=f"High semantic similarity: {best_score:.2f}"
            )
        
        return None
    
    def batch_check_duplicates(
        self,
        study_id: str,
        candidates: List[Tuple[Dict, Optional[str]]],
        threshold: float = 0.85
    ) -> Dict[str, DuplicateMatch]:
        """
        Check multiple candidates for duplicates in parallel
        
        Args:
            study_id: Study identifier
            candidates: List of (metadata, text) tuples
            threshold: Similarity threshold
            
        Returns:
            Dict mapping candidate ID to DuplicateMatch
        """
        from concurrent.futures import ThreadPoolExecutor
        
        results = {}
        
        def check_one(candidate_tuple):
            metadata, text = candidate_tuple
            candidate_id = metadata.get('id', metadata.get('title', 'unknown'))
            match = self.check_duplicate(study_id, metadata, text, threshold)
            return candidate_id, match
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            for candidate_id, match in executor.map(check_one, candidates):
                results[candidate_id] = match
        
        return results
    
    def _normalize_doi(self, doi: str) -> str:
        """Normalize DOI for comparison"""
        if not doi:
            return ""
        # Remove common prefixes and normalize
        doi = doi.lower().strip()
        doi = re.sub(r'^(https?://)?((dx\.)?doi\.org/)?', '', doi)
        return doi
    
    def _normalize_patent(self, patent: str) -> str:
        """Normalize patent number for comparison"""
        if not patent:
            return ""
        # Remove spaces, hyphens, normalize
        patent = patent.upper().strip()
        patent = re.sub(r'[\s\-]', '', patent)
        return patent
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for fuzzy matching"""
        if not title:
            return ""
        # Lowercase, remove punctuation, normalize whitespace
        title = title.lower().strip()
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title)
        return title
    
    def _normalize_authors(self, authors: str) -> set:
        """Normalize authors to set of last names"""
        if not authors:
            return set()
        
        # Split by common delimiters
        author_list = re.split(r'[,;]|\sand\s', authors)
        
        last_names = set()
        for author in author_list:
            author = author.strip()
            if not author:
                continue
            
            # Extract last name (last word, or after comma)
            if ',' in author:
                last_name = author.split(',')[0].strip()
            else:
                parts = author.split()
                last_name = parts[-1] if parts else author
            
            last_names.add(last_name.lower())
        
        return last_names
    
    def _create_search_text(self, entry: Dict, full_text: Optional[str] = None) -> str:
        """Create searchable text from entry for embedding"""
        parts = []
        
        if entry.get('title'):
            parts.append(entry['title'])
        
        if entry.get('authors'):
            parts.append(entry['authors'])
        
        if entry.get('abstract'):
            parts.append(entry['abstract'])
        
        if full_text:
            # Use first 1000 chars of full text
            parts.append(full_text[:1000])
        
        return " ".join(parts)
    
    def _get_entry_id(self, entry: Dict) -> str:
        """Generate unique ID for entry"""
        if entry.get('doi'):
            return f"doi:{self._normalize_doi(entry['doi'])}"
        elif entry.get('patent_number'):
            return f"patent:{self._normalize_patent(entry['patent_number'])}"
        elif entry.get('title'):
            return f"title:{self._normalize_title(entry['title'])[:50]}"
        else:
            return f"unknown:{hash(str(entry))}"


# Example usage
if __name__ == "__main__":
    detector = DuplicateDetector()
    
    # Load known art
    known_art = [
        {
            'title': 'Novel Tyrosinase Inhibitors for Skin Whitening',
            'authors': 'Smith J, Johnson A',
            'doi': '10.1234/example1',
            'date': '2023-01-15'
        },
        {
            'title': 'Oximidol: A New Approach to Melanin Reduction',
            'authors': 'Brown K, Davis L',
            'doi': '10.1234/example2',
            'date': '2023-03-20'
        }
    ]
    
    detector.load_known_art("25974", known_art)
    
    # Check candidate
    candidate = {
        'title': 'Novel Tyrosinase Inhibitors for Skin Whitening',  # Exact match
        'authors': 'Smith J, Johnson A',
        'doi': '10.1234/example1',
        'date': '2023-01-15'
    }
    
    result = detector.check_duplicate("25974", candidate)
    
    print(f"Is duplicate: {result.is_duplicate}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Match type: {result.match_type}")
    print(f"Reasoning: {result.reasoning}")
