"""
Confidence Scorer - Calculate confidence scores for candidates
Predicts likelihood of RWS acceptance based on multiple factors
"""

from typing import Dict, List, Optional
from datetime import datetime
import re


class ConfidenceScorer:
    """
    Calculate confidence scores for prior art candidates
    Factors:
    - Date relevance (proximity to critical date)
    - Source credibility
    - Content quality indicators
    - Keyword match strength
    - Document type
    - Accessibility (open access vs paywall)
    """
    
    # Scoring weights
    WEIGHTS = {
        'date_relevance': 0.25,
        'source_credibility': 0.20,
        'content_quality': 0.20,
        'keyword_match': 0.15,
        'document_type': 0.10,
        'accessibility': 0.10
    }
    
    # Source credibility scores
    SOURCE_SCORES = {
        'uspto': 1.0,
        'wayback': 0.9,
        'fcc': 0.95,
        'ptab': 0.95,
        'ieee': 0.9,
        'university': 0.85,
        'distributor': 0.8,
        'github': 0.75,
        'usenet': 0.7,
        'forum': 0.6,
        'unknown': 0.5
    }
    
    # Document type scores
    DOC_TYPE_SCORES = {
        'patent': 1.0,
        'datasheet': 0.95,
        'technical_manual': 0.9,
        'academic_paper': 0.85,
        'standard': 0.9,
        'whitepaper': 0.8,
        'presentation': 0.7,
        'forum_post': 0.5,
        'blog': 0.4,
        'unknown': 0.6
    }
    
    def __init__(self, critical_date: Optional[str] = None):
        """
        Initialize confidence scorer
        
        Args:
            critical_date: Critical date in YYYY-MM-DD format
        """
        self.critical_date = None
        if critical_date:
            try:
                self.critical_date = datetime.strptime(critical_date, '%Y-%m-%d')
            except ValueError:
                pass
    
    def score_candidate(
        self,
        candidate: Dict,
        keywords: List[str] = None
    ) -> Dict:
        """
        Calculate confidence score for a candidate
        
        Args:
            candidate: Candidate dict with title, date, source, etc.
            keywords: List of search keywords
            
        Returns:
            Scoring breakdown dict
        """
        scores = {}
        
        # 1. Date relevance
        scores['date_relevance'] = self._score_date_relevance(candidate.get('date'))
        
        # 2. Source credibility
        scores['source_credibility'] = self._score_source_credibility(candidate.get('source'))
        
        # 3. Content quality
        scores['content_quality'] = self._score_content_quality(candidate)
        
        # 4. Keyword match
        scores['keyword_match'] = self._score_keyword_match(candidate, keywords or [])
        
        # 5. Document type
        scores['document_type'] = self._score_document_type(candidate)
        
        # 6. Accessibility
        scores['accessibility'] = self._score_accessibility(candidate)
        
        # Calculate weighted total
        total_score = sum(
            scores[factor] * self.WEIGHTS[factor]
            for factor in self.WEIGHTS
        )
        
        # Determine tier
        tier = self._determine_tier(total_score)
        
        return {
            'total_score': total_score,
            'tier': tier,
            'breakdown': scores,
            'weights': self.WEIGHTS,
            'recommendation': self._get_recommendation(total_score, tier)
        }
    
    def _score_date_relevance(self, date_str: Optional[str]) -> float:
        """Score based on date proximity to critical date"""
        if not date_str or not self.critical_date:
            return 0.5  # Neutral if no date info
        
        try:
            # Parse date
            date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y', '%B %d, %Y']
            candidate_date = None
            
            for fmt in date_formats:
                try:
                    candidate_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not candidate_date:
                return 0.5
            
            # After critical date = invalid
            if candidate_date >= self.critical_date:
                return 0.0
            
            # Calculate years before critical date
            years_before = (self.critical_date - candidate_date).days / 365.25
            
            # Scoring curve: closer to critical date = higher score
            # But not too close (need some gap)
            if years_before < 0.5:
                return 0.6  # Very close, might be questioned
            elif years_before < 2:
                return 1.0  # Sweet spot
            elif years_before < 5:
                return 0.9
            elif years_before < 10:
                return 0.8
            else:
                return 0.7  # Very old, still valid but less relevant
        
        except Exception:
            return 0.5
    
    def _score_source_credibility(self, source: Optional[str]) -> float:
        """Score based on source credibility"""
        if not source:
            return self.SOURCE_SCORES['unknown']
        
        source_lower = source.lower()
        
        for key, score in self.SOURCE_SCORES.items():
            if key in source_lower:
                return score
        
        return self.SOURCE_SCORES['unknown']
    
    def _score_content_quality(self, candidate: Dict) -> float:
        """Score based on content quality indicators"""
        score = 0.5  # Base score
        
        title = candidate.get('title', '')
        snippet = candidate.get('snippet', '')
        metadata = candidate.get('metadata', {})
        
        # Has detailed title
        if len(title) > 20:
            score += 0.1
        
        # Has snippet/description
        if len(snippet) > 50:
            score += 0.1
        
        # Has metadata (authors, DOI, etc.)
        if metadata.get('authors'):
            score += 0.1
        if metadata.get('doi'):
            score += 0.1
        if metadata.get('patent_number'):
            score += 0.1
        
        # Technical indicators in title
        technical_terms = ['system', 'method', 'apparatus', 'device', 'circuit', 'process']
        if any(term in title.lower() for term in technical_terms):
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_keyword_match(self, candidate: Dict, keywords: List[str]) -> float:
        """Score based on keyword match strength"""
        if not keywords:
            return 0.5
        
        title = candidate.get('title', '').lower()
        snippet = candidate.get('snippet', '').lower()
        combined_text = f"{title} {snippet}"
        
        # Count keyword matches
        matches = sum(1 for kw in keywords if kw.lower() in combined_text)
        
        # Calculate match ratio
        match_ratio = matches / len(keywords)
        
        # Bonus for exact phrase matches
        if any(kw.lower() in title for kw in keywords):
            match_ratio += 0.2
        
        return min(match_ratio, 1.0)
    
    def _score_document_type(self, candidate: Dict) -> float:
        """Score based on document type"""
        title = candidate.get('title', '').lower()
        url = candidate.get('url', '').lower()
        metadata = candidate.get('metadata', {})
        
        # Check for patent
        if metadata.get('patent_number') or 'patent' in url:
            return self.DOC_TYPE_SCORES['patent']
        
        # Check for datasheet
        if 'datasheet' in title or 'datasheet' in url:
            return self.DOC_TYPE_SCORES['datasheet']
        
        # Check for manual
        if 'manual' in title or 'specification' in title:
            return self.DOC_TYPE_SCORES['technical_manual']
        
        # Check for academic paper
        if metadata.get('doi') or 'ieee' in url or 'acm' in url:
            return self.DOC_TYPE_SCORES['academic_paper']
        
        # Check for standard
        if 'standard' in title or 'specification' in title:
            return self.DOC_TYPE_SCORES['standard']
        
        # Check for whitepaper
        if 'whitepaper' in title or 'white paper' in title:
            return self.DOC_TYPE_SCORES['whitepaper']
        
        # Check for presentation
        if 'presentation' in title or '.ppt' in url:
            return self.DOC_TYPE_SCORES['presentation']
        
        # Check for forum/blog
        if 'forum' in url or 'blog' in url:
            return self.DOC_TYPE_SCORES['forum_post']
        
        return self.DOC_TYPE_SCORES['unknown']
    
    def _score_accessibility(self, candidate: Dict) -> float:
        """Score based on accessibility (open access vs paywall)"""
        open_access = candidate.get('open_access', True)
        url = candidate.get('url', '').lower()
        
        # Open access = full score
        if open_access:
            return 1.0
        
        # Known open sources
        open_sources = ['archive.org', 'github.com', 'fcc.gov', 'uspto.gov']
        if any(source in url for source in open_sources):
            return 1.0
        
        # Paywall indicators
        paywall_indicators = ['ieee.org', 'sciencedirect.com', 'springer.com']
        if any(indicator in url for indicator in paywall_indicators):
            return 0.3
        
        # Unknown = assume accessible
        return 0.8
    
    def _determine_tier(self, score: float) -> str:
        """Determine candidate tier based on score"""
        if score >= 0.8:
            return 'READY_SUBMIT'
        elif score >= 0.6:
            return 'HOLD'
        else:
            return 'REJECT'
    
    def _get_recommendation(self, score: float, tier: str) -> str:
        """Get recommendation based on score and tier"""
        if tier == 'READY_SUBMIT':
            return "High confidence - Ready for submission"
        elif tier == 'HOLD':
            return "Medium confidence - Review before submission"
        else:
            return "Low confidence - Consider rejecting"
    
    def batch_score(
        self,
        candidates: List[Dict],
        keywords: List[str] = None
    ) -> List[Dict]:
        """
        Score multiple candidates and sort by confidence
        
        Args:
            candidates: List of candidate dicts
            keywords: Search keywords
            
        Returns:
            List of candidates with scores, sorted by confidence
        """
        scored_candidates = []
        
        for candidate in candidates:
            scoring = self.score_candidate(candidate, keywords)
            
            scored_candidates.append({
                **candidate,
                'confidence_score': scoring['total_score'],
                'tier': scoring['tier'],
                'scoring_breakdown': scoring['breakdown'],
                'recommendation': scoring['recommendation']
            })
        
        # Sort by confidence score (descending)
        scored_candidates.sort(key=lambda c: c['confidence_score'], reverse=True)
        
        return scored_candidates
    
    def generate_confidence_report(
        self,
        candidates: List[Dict]
    ) -> Dict:
        """Generate confidence scoring report"""
        if not candidates:
            return {
                'total_candidates': 0,
                'tier_distribution': {},
                'average_score': 0.0
            }
        
        # Count by tier
        tier_counts = {}
        total_score = 0.0
        
        for candidate in candidates:
            tier = candidate.get('tier', 'UNKNOWN')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            total_score += candidate.get('confidence_score', 0.0)
        
        return {
            'total_candidates': len(candidates),
            'tier_distribution': tier_counts,
            'average_score': total_score / len(candidates),
            'ready_submit_count': tier_counts.get('READY_SUBMIT', 0),
            'hold_count': tier_counts.get('HOLD', 0),
            'reject_count': tier_counts.get('REJECT', 0)
        }


# Example usage
if __name__ == "__main__":
    scorer = ConfidenceScorer(critical_date="2019-10-28")
    
    # Example candidate
    candidate = {
        'title': 'Blender with Offset Blades - Technical Datasheet',
        'url': 'https://web.archive.org/web/20180315/example.com/datasheet.pdf',
        'source': 'wayback',
        'date': '2018-03-15',
        'snippet': 'Technical specifications for rechargeable blender with offset blade design...',
        'metadata': {
            'authors': 'Engineering Team',
            'pages': 12
        },
        'open_access': True
    }
    
    keywords = ['blender', 'offset', 'blade', 'rechargeable']
    
    # Score candidate
    scoring = scorer.score_candidate(candidate, keywords)
    
    print(f"Confidence Score: {scoring['total_score']:.2f}")
    print(f"Tier: {scoring['tier']}")
    print(f"Recommendation: {scoring['recommendation']}")
    print(f"\nBreakdown:")
    for factor, score in scoring['breakdown'].items():
        weight = scoring['weights'][factor]
        print(f"  {factor}: {score:.2f} (weight: {weight:.2f})")
