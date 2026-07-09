"""
Quality Predictor - Predict RWS acceptance rate based on historical data
Uses machine learning to predict candidate quality
"""

from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime
from collections import Counter


class QualityPredictor:
    """
    Predict RWS acceptance likelihood for candidates
    Features:
    - Historical acceptance rate tracking
    - Feature-based prediction
    - Study-specific learning
    - Confidence calibration
    """
    
    def __init__(self, workspace_root: Path):
        """
        Initialize quality predictor
        
        Args:
            workspace_root: Root directory of workspace
        """
        self.workspace_root = Path(workspace_root)
        self.history_path = self.workspace_root / ".bob" / "tmp" / "acceptance_history.json"
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load historical data
        self.history = self._load_history()
        
        # Feature weights (learned from historical data)
        self.feature_weights = self._calculate_feature_weights()
    
    def _load_history(self) -> Dict:
        """Load historical acceptance data"""
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠ Error loading history: {e}")
        
        return {
            'submissions': [],  # List of submitted candidates with outcomes
            'acceptance_rate': 0.0,
            'by_source': {},
            'by_study': {},
            'last_updated': datetime.now().isoformat()
        }
    
    def _save_history(self):
        """Save historical data"""
        self.history['last_updated'] = datetime.now().isoformat()
        
        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2)
    
    def predict_acceptance(self, candidate: Dict) -> Dict:
        """
        Predict RWS acceptance likelihood
        
        Args:
            candidate: Candidate dict
            
        Returns:
            Prediction dict with probability and factors
        """
        # Extract features
        features = self._extract_features(candidate)
        
        # Calculate base probability from historical data
        base_probability = self._calculate_base_probability(candidate)
        
        # Adjust based on features
        adjusted_probability = self._adjust_probability(base_probability, features)
        
        # Identify key factors
        key_factors = self._identify_key_factors(features)
        
        return {
            'acceptance_probability': adjusted_probability,
            'confidence': self._calculate_confidence(candidate),
            'key_factors': key_factors,
            'recommendation': self._get_recommendation(adjusted_probability),
            'historical_context': {
                'overall_acceptance_rate': self.history.get('acceptance_rate', 0.0),
                'source_acceptance_rate': self._get_source_acceptance_rate(candidate.get('source')),
                'similar_submissions': self._count_similar_submissions(candidate)
            }
        }
    
    def _extract_features(self, candidate: Dict) -> Dict:
        """Extract predictive features from candidate"""
        return {
            'has_date': bool(candidate.get('date')),
            'date_before_critical': self._is_before_critical_date(candidate.get('date')),
            'source_credibility': self._get_source_credibility(candidate.get('source')),
            'has_patent_number': bool(candidate.get('patent_number')),
            'has_doi': bool(candidate.get('doi')),
            'title_length': len(candidate.get('title', '')),
            'has_snippet': bool(candidate.get('snippet')),
            'open_access': candidate.get('open_access', True),
            'confidence_score': candidate.get('confidence', 0.5),
            'has_metadata': bool(candidate.get('metadata'))
        }
    
    def _calculate_base_probability(self, candidate: Dict) -> float:
        """Calculate base acceptance probability from historical data"""
        # Overall acceptance rate
        overall_rate = self.history.get('acceptance_rate', 0.5)
        
        # Source-specific rate
        source = candidate.get('source', 'unknown')
        source_rate = self.history.get('by_source', {}).get(source, {}).get('acceptance_rate', overall_rate)
        
        # Weighted average
        return (overall_rate * 0.3) + (source_rate * 0.7)
    
    def _adjust_probability(self, base_prob: float, features: Dict) -> float:
        """Adjust probability based on features"""
        adjusted = base_prob
        
        # Positive factors
        if features['has_date'] and features['date_before_critical']:
            adjusted += 0.15
        
        if features['has_patent_number']:
            adjusted += 0.10
        
        if features['has_doi']:
            adjusted += 0.08
        
        if features['open_access']:
            adjusted += 0.05
        
        if features['confidence_score'] > 0.8:
            adjusted += 0.10
        
        # Negative factors
        if not features['has_date']:
            adjusted -= 0.10
        
        if not features['date_before_critical']:
            adjusted -= 0.20
        
        if features['title_length'] < 10:
            adjusted -= 0.05
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, adjusted))
    
    def _identify_key_factors(self, features: Dict) -> List[str]:
        """Identify key factors affecting prediction"""
        factors = []
        
        if features['date_before_critical']:
            factors.append("✓ Date before critical date")
        elif features['has_date']:
            factors.append("✗ Date after critical date")
        else:
            factors.append("⚠ No date information")
        
        if features['has_patent_number']:
            factors.append("✓ Has patent number")
        
        if features['has_doi']:
            factors.append("✓ Has DOI")
        
        if features['open_access']:
            factors.append("✓ Open access")
        
        if features['source_credibility'] > 0.8:
            factors.append("✓ High credibility source")
        
        if features['confidence_score'] > 0.8:
            factors.append("✓ High confidence score")
        
        return factors
    
    def _calculate_confidence(self, candidate: Dict) -> float:
        """Calculate confidence in prediction"""
        # More historical data = higher confidence
        total_submissions = len(self.history.get('submissions', []))
        
        if total_submissions == 0:
            return 0.3  # Low confidence with no history
        elif total_submissions < 10:
            return 0.5
        elif total_submissions < 50:
            return 0.7
        else:
            return 0.9
    
    def _get_recommendation(self, probability: float) -> str:
        """Get recommendation based on probability"""
        if probability >= 0.8:
            return "Strong candidate - High acceptance likelihood"
        elif probability >= 0.6:
            return "Good candidate - Moderate acceptance likelihood"
        elif probability >= 0.4:
            return "Marginal candidate - Review carefully"
        else:
            return "Weak candidate - Low acceptance likelihood"
    
    def _is_before_critical_date(self, date_str: Optional[str]) -> bool:
        """Check if date is before critical date"""
        # Simplified - would need actual critical date
        return bool(date_str)
    
    def _get_source_credibility(self, source: Optional[str]) -> float:
        """Get source credibility score"""
        credibility_map = {
            'uspto': 1.0,
            'wayback': 0.9,
            'fcc': 0.95,
            'ptab': 0.95,
            'ieee': 0.9,
            'university': 0.85,
            'distributor': 0.8,
            'github': 0.75,
            'usenet': 0.7,
            'forum': 0.6
        }
        
        return credibility_map.get(source, 0.5)
    
    def _get_source_acceptance_rate(self, source: Optional[str]) -> float:
        """Get acceptance rate for source"""
        if not source:
            return self.history.get('acceptance_rate', 0.5)
        
        source_data = self.history.get('by_source', {}).get(source, {})
        return source_data.get('acceptance_rate', self.history.get('acceptance_rate', 0.5))
    
    def _count_similar_submissions(self, candidate: Dict) -> int:
        """Count similar historical submissions"""
        source = candidate.get('source')
        
        count = 0
        for submission in self.history.get('submissions', []):
            if submission.get('source') == source:
                count += 1
        
        return count
    
    def record_submission(
        self,
        candidate: Dict,
        accepted: bool,
        study_id: str
    ):
        """
        Record submission outcome for learning
        
        Args:
            candidate: Submitted candidate
            accepted: Whether RWS accepted it
            study_id: Study ID
        """
        submission = {
            'candidate': {
                'title': candidate.get('title'),
                'source': candidate.get('source'),
                'date': candidate.get('date'),
                'has_patent_number': bool(candidate.get('patent_number')),
                'has_doi': bool(candidate.get('doi'))
            },
            'accepted': accepted,
            'study_id': study_id,
            'submitted_date': datetime.now().isoformat()
        }
        
        self.history['submissions'].append(submission)
        
        # Update statistics
        self._update_statistics()
        
        # Save history
        self._save_history()
        
        print(f"✓ Recorded submission: {'Accepted' if accepted else 'Rejected'}")
    
    def _update_statistics(self):
        """Update acceptance statistics"""
        submissions = self.history['submissions']
        
        if not submissions:
            return
        
        # Overall acceptance rate
        accepted_count = sum(1 for s in submissions if s['accepted'])
        self.history['acceptance_rate'] = accepted_count / len(submissions)
        
        # By source
        by_source = {}
        for submission in submissions:
            source = submission['candidate'].get('source', 'unknown')
            
            if source not in by_source:
                by_source[source] = {'total': 0, 'accepted': 0}
            
            by_source[source]['total'] += 1
            if submission['accepted']:
                by_source[source]['accepted'] += 1
        
        # Calculate rates
        for source, data in by_source.items():
            data['acceptance_rate'] = data['accepted'] / data['total']
        
        self.history['by_source'] = by_source
        
        # By study
        by_study = {}
        for submission in submissions:
            study_id = submission.get('study_id', 'unknown')
            
            if study_id not in by_study:
                by_study[study_id] = {'total': 0, 'accepted': 0}
            
            by_study[study_id]['total'] += 1
            if submission['accepted']:
                by_study[study_id]['accepted'] += 1
        
        # Calculate rates
        for study_id, data in by_study.items():
            data['acceptance_rate'] = data['accepted'] / data['total']
        
        self.history['by_study'] = by_study
    
    def _calculate_feature_weights(self) -> Dict:
        """Calculate feature importance from historical data"""
        # Simplified - would use actual ML in production
        return {
            'date_before_critical': 0.30,
            'has_patent_number': 0.20,
            'source_credibility': 0.20,
            'has_doi': 0.15,
            'open_access': 0.10,
            'confidence_score': 0.05
        }
    
    def generate_quality_report(self) -> Dict:
        """Generate quality prediction report"""
        submissions = self.history.get('submissions', [])
        
        if not submissions:
            return {
                'total_submissions': 0,
                'message': 'No historical data available'
            }
        
        return {
            'total_submissions': len(submissions),
            'overall_acceptance_rate': self.history.get('acceptance_rate', 0.0),
            'by_source': self.history.get('by_source', {}),
            'by_study': self.history.get('by_study', {}),
            'last_updated': self.history.get('last_updated')
        }


# Example usage
if __name__ == "__main__":
    predictor = QualityPredictor(Path("."))
    
    # Example candidate
    candidate = {
        'title': 'Blender Datasheet 2018',
        'source': 'wayback',
        'date': '2018-03-15',
        'patent_number': None,
        'doi': None,
        'snippet': 'Technical specifications...',
        'open_access': True,
        'confidence': 0.85
    }
    
    # Predict acceptance
    prediction = predictor.predict_acceptance(candidate)
    
    print(f"Acceptance Probability: {prediction['acceptance_probability']:.1%}")
    print(f"Confidence: {prediction['confidence']:.1%}")
    print(f"Recommendation: {prediction['recommendation']}")
    print(f"\nKey Factors:")
    for factor in prediction['key_factors']:
        print(f"  {factor}")
    
    # Record outcome (for learning)
    # predictor.record_submission(candidate, accepted=True, study_id='26052')
