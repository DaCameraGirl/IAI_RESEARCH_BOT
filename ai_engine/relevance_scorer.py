"""
Relevance Scorer - ML-based candidate ranking trained on past submissions
Predicts RWS reviewer scores (0-3) and in-scope confidence (high/med/low)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from datetime import datetime


@dataclass
class ScoringFeatures:
    """Features extracted from a candidate for ML scoring"""
    # Document quality signals
    has_doi: bool
    has_issn: bool
    peer_reviewed: bool
    open_access: bool
    school_access: bool
    
    # Date signals
    days_before_critical: int
    publication_year: int
    
    # Content signals
    num_requirements_matched: int
    num_strong_anchors: int
    num_medium_anchors: int
    num_weak_anchors: int
    avg_semantic_confidence: float
    max_semantic_confidence: float
    
    # Text quality
    document_length_chars: int
    num_technical_terms: int
    num_citations: int
    
    # Source signals
    source_type: str  # "journal" | "patent" | "datasheet" | "thesis" | "conference"
    publisher_tier: str  # "top" | "mid" | "low" | "unknown"
    
    # Study-specific
    study_type: str  # "invalidity" | "research" | "copyright"
    is_priority_requirement: bool


@dataclass
class ScoringResult:
    """ML-based scoring prediction"""
    predicted_rank: int  # 0-3
    rank_confidence: float  # 0.0-1.0
    in_scope_confidence: str  # "high" | "med" | "low"
    feature_importance: Dict[str, float]
    reasoning: str
    recommendation: str  # "SUBMIT" | "HOLD" | "SKIP"


class RelevanceScorer:
    """
    ML-based relevance scoring using:
    - Historical submission data (Angela's past work)
    - Feature engineering from document metadata + content
    - Ensemble model (Random Forest + Gradient Boosting)
    - Explainable predictions with feature importance
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize relevance scorer
        
        Args:
            model_path: Path to saved model (if None, uses default)
        """
        self.model_path = model_path or Path("models/relevance_scorer.pkl")
        self.model = None
        self.feature_scaler = None
        self.training_history = []
        
        # Load model if exists
        if self.model_path.exists():
            self._load_model()
    
    def extract_features(
        self,
        document_metadata: Dict,
        match_results: List,  # From SemanticMatcher
        study_config: Dict
    ) -> ScoringFeatures:
        """
        Extract ML features from candidate document
        
        Args:
            document_metadata: Document metadata dict
            match_results: List of MatchResult objects from semantic matcher
            study_config: Study configuration dict
            
        Returns:
            ScoringFeatures object
        """
        # Document quality
        has_doi = bool(document_metadata.get('doi'))
        has_issn = bool(document_metadata.get('issn'))
        peer_reviewed = document_metadata.get('peer_reviewed', False)
        open_access = document_metadata.get('open_access', False)
        school_access = document_metadata.get('access') == 'school'
        
        # Date calculations
        pub_date = document_metadata.get('date', '')
        critical_date = study_config.get('critical_date', '')
        days_before = self._calculate_days_before(pub_date, critical_date)
        pub_year = int(pub_date[:4]) if pub_date and len(pub_date) >= 4 else 0
        
        # Match quality from semantic matcher
        num_matched = len(match_results)
        strong_anchors = sum(1 for m in match_results if m.anchor_strength == 'strong')
        medium_anchors = sum(1 for m in match_results if m.anchor_strength == 'medium')
        weak_anchors = sum(1 for m in match_results if m.anchor_strength == 'weak')
        
        confidences = [m.confidence for m in match_results]
        avg_conf = np.mean(confidences) if confidences else 0.0
        max_conf = max(confidences) if confidences else 0.0
        
        # Content analysis
        doc_length = len(document_metadata.get('text', ''))
        num_tech_terms = self._count_technical_terms(document_metadata.get('text', ''))
        num_citations = document_metadata.get('num_citations', 0)
        
        # Source classification
        source_type = self._classify_source_type(document_metadata)
        publisher_tier = self._classify_publisher_tier(
            document_metadata.get('publisher', ''),
            document_metadata.get('journal', '')
        )
        
        # Study context
        study_type = study_config.get('type', 'research')
        priority_reqs = study_config.get('priority_requirements', [])
        is_priority = any(
            m.requirement_id in priority_reqs for m in match_results
        )
        
        return ScoringFeatures(
            has_doi=has_doi,
            has_issn=has_issn,
            peer_reviewed=peer_reviewed,
            open_access=open_access,
            school_access=school_access,
            days_before_critical=days_before,
            publication_year=pub_year,
            num_requirements_matched=num_matched,
            num_strong_anchors=strong_anchors,
            num_medium_anchors=medium_anchors,
            num_weak_anchors=weak_anchors,
            avg_semantic_confidence=avg_conf,
            max_semantic_confidence=max_conf,
            document_length_chars=doc_length,
            num_technical_terms=num_tech_terms,
            num_citations=num_citations,
            source_type=source_type,
            publisher_tier=publisher_tier,
            study_type=study_type,
            is_priority_requirement=is_priority
        )
    
    def score_candidate(
        self,
        features: ScoringFeatures,
        explain: bool = True
    ) -> ScoringResult:
        """
        Score a candidate using ML model
        
        Args:
            features: ScoringFeatures object
            explain: Whether to generate feature importance explanation
            
        Returns:
            ScoringResult with prediction and reasoning
        """
        # If no trained model, use rule-based fallback
        if self.model is None:
            return self._rule_based_scoring(features)
        
        # Convert features to numpy array
        feature_vector = self._features_to_vector(features)
        
        # Scale features
        if self.feature_scaler:
            feature_vector = self.feature_scaler.transform([feature_vector])[0]
        
        # Predict rank (0-3)
        predicted_rank = int(self.model.predict([feature_vector])[0])
        
        # Get prediction probability for confidence
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba([feature_vector])[0]
            rank_confidence = float(proba[predicted_rank])
        else:
            rank_confidence = 0.7  # Default for models without proba
        
        # Determine in-scope confidence
        in_scope_conf = self._calculate_in_scope_confidence(features, predicted_rank)
        
        # Feature importance (if explainable model)
        feature_importance = {}
        if explain and hasattr(self.model, 'feature_importances_'):
            feature_names = self._get_feature_names()
            importances = self.model.feature_importances_
            feature_importance = dict(zip(feature_names, importances))
            # Sort by importance
            feature_importance = dict(
                sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            features, predicted_rank, rank_confidence, feature_importance
        )
        
        # Recommendation
        recommendation = self._make_recommendation(
            predicted_rank, rank_confidence, in_scope_conf
        )
        
        return ScoringResult(
            predicted_rank=predicted_rank,
            rank_confidence=rank_confidence,
            in_scope_confidence=in_scope_conf,
            feature_importance=feature_importance,
            reasoning=reasoning,
            recommendation=recommendation
        )
    
    def _rule_based_scoring(self, features: ScoringFeatures) -> ScoringResult:
        """
        Fallback rule-based scoring when no ML model available
        
        Args:
            features: ScoringFeatures object
            
        Returns:
            ScoringResult based on heuristic rules
        """
        score = 0
        reasoning_parts = []
        
        # Strong anchor bonus
        if features.num_strong_anchors >= 2:
            score += 2
            reasoning_parts.append(f"{features.num_strong_anchors} strong anchors")
        elif features.num_strong_anchors >= 1:
            score += 1
            reasoning_parts.append(f"{features.num_strong_anchors} strong anchor")
        
        # Semantic confidence
        if features.max_semantic_confidence >= 0.8:
            score += 1
            reasoning_parts.append("high semantic match")
        
        # Document quality
        if features.peer_reviewed and features.has_doi:
            score += 1
            reasoning_parts.append("peer-reviewed with DOI")
        
        # Multiple requirements
        if features.num_requirements_matched >= 3:
            score += 1
            reasoning_parts.append(f"matches {features.num_requirements_matched} requirements")
        
        # Priority requirement
        if features.is_priority_requirement:
            score += 1
            reasoning_parts.append("matches priority requirement")
        
        # Cap at 3
        predicted_rank = min(3, score)
        
        # Confidence based on number of positive signals
        rank_confidence = min(1.0, len(reasoning_parts) / 5.0)
        
        # In-scope confidence
        if features.num_strong_anchors >= 1 and features.max_semantic_confidence >= 0.7:
            in_scope_conf = "high"
        elif features.num_strong_anchors >= 1 or features.max_semantic_confidence >= 0.6:
            in_scope_conf = "med"
        else:
            in_scope_conf = "low"
        
        reasoning = "Rule-based scoring: " + " | ".join(reasoning_parts)
        
        recommendation = self._make_recommendation(
            predicted_rank, rank_confidence, in_scope_conf
        )
        
        return ScoringResult(
            predicted_rank=predicted_rank,
            rank_confidence=rank_confidence,
            in_scope_confidence=in_scope_conf,
            feature_importance={},
            reasoning=reasoning,
            recommendation=recommendation
        )
    
    def train_from_history(
        self,
        training_data: List[Dict],
        validation_split: float = 0.2
    ) -> Dict:
        """
        Train ML model from historical submission data
        
        Args:
            training_data: List of dicts with features + actual_rank
            validation_split: Fraction of data for validation
            
        Returns:
            Training metrics dict
        """
        try:
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, classification_report
        except ImportError:
            raise ImportError(
                "scikit-learn not installed. Run: pip install scikit-learn"
            )
        
        # Extract features and labels
        X = []
        y = []
        
        for item in training_data:
            features = item['features']
            actual_rank = item['actual_rank']
            
            feature_vector = self._features_to_vector(features)
            X.append(feature_vector)
            y.append(actual_rank)
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )
        
        # Scale features
        self.feature_scaler = StandardScaler()
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_val_scaled = self.feature_scaler.transform(X_val)
        
        # Train ensemble model
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        gb_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        
        # Train both models
        rf_model.fit(X_train_scaled, y_train)
        gb_model.fit(X_train_scaled, y_train)
        
        # Evaluate
        rf_pred = rf_model.predict(X_val_scaled)
        gb_pred = gb_model.predict(X_val_scaled)
        
        rf_acc = accuracy_score(y_val, rf_pred)
        gb_acc = accuracy_score(y_val, gb_pred)
        
        # Use better model
        if rf_acc >= gb_acc:
            self.model = rf_model
            best_acc = rf_acc
            model_type = "RandomForest"
        else:
            self.model = gb_model
            best_acc = gb_acc
            model_type = "GradientBoosting"
        
        # Save model
        self._save_model()
        
        # Training history
        history = {
            'timestamp': datetime.now().isoformat(),
            'model_type': model_type,
            'accuracy': best_acc,
            'num_samples': len(training_data),
            'validation_split': validation_split
        }
        
        self.training_history.append(history)
        
        return history
    
    def _features_to_vector(self, features: ScoringFeatures) -> np.ndarray:
        """Convert ScoringFeatures to numpy array"""
        # Encode categorical features
        source_encoding = {
            'journal': 0, 'patent': 1, 'datasheet': 2, 
            'thesis': 3, 'conference': 4
        }
        publisher_encoding = {'top': 2, 'mid': 1, 'low': 0, 'unknown': 0}
        study_encoding = {'invalidity': 2, 'research': 1, 'copyright': 0}
        
        vector = [
            int(features.has_doi),
            int(features.has_issn),
            int(features.peer_reviewed),
            int(features.open_access),
            int(features.school_access),
            features.days_before_critical,
            features.publication_year,
            features.num_requirements_matched,
            features.num_strong_anchors,
            features.num_medium_anchors,
            features.num_weak_anchors,
            features.avg_semantic_confidence,
            features.max_semantic_confidence,
            features.document_length_chars,
            features.num_technical_terms,
            features.num_citations,
            source_encoding.get(features.source_type, 0),
            publisher_encoding.get(features.publisher_tier, 0),
            study_encoding.get(features.study_type, 1),
            int(features.is_priority_requirement)
        ]
        
        return np.array(vector, dtype=float)
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names for explainability"""
        return [
            'has_doi', 'has_issn', 'peer_reviewed', 'open_access', 'school_access',
            'days_before_critical', 'publication_year', 'num_requirements_matched',
            'num_strong_anchors', 'num_medium_anchors', 'num_weak_anchors',
            'avg_semantic_confidence', 'max_semantic_confidence',
            'document_length_chars', 'num_technical_terms', 'num_citations',
            'source_type', 'publisher_tier', 'study_type', 'is_priority_requirement'
        ]
    
    def _calculate_days_before(self, pub_date: str, critical_date: str) -> int:
        """Calculate days before critical date"""
        try:
            from dateutil import parser
            pub = parser.parse(pub_date)
            crit = parser.parse(critical_date)
            return (crit - pub).days
        except:
            return 0
    
    def _count_technical_terms(self, text: str) -> int:
        """Count technical terms in text"""
        # Simple heuristic: words with numbers, acronyms, chemical formulas
        import re
        patterns = [
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\w*\d+\w*\b',  # Words with numbers
            r'\b[A-Z][a-z]+[A-Z]\w*\b'  # CamelCase
        ]
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text))
        return count
    
    def _classify_source_type(self, metadata: Dict) -> str:
        """Classify document source type"""
        if metadata.get('patent_number'):
            return 'patent'
        elif metadata.get('journal'):
            return 'journal'
        elif 'thesis' in metadata.get('title', '').lower():
            return 'thesis'
        elif metadata.get('conference'):
            return 'conference'
        elif 'datasheet' in metadata.get('title', '').lower():
            return 'datasheet'
        return 'journal'  # Default
    
    def _classify_publisher_tier(self, publisher: str, journal: str) -> str:
        """Classify publisher tier"""
        top_publishers = [
            'nature', 'science', 'cell', 'lancet', 'nejm', 'ieee', 'acm',
            'springer', 'elsevier', 'wiley', 'oxford', 'cambridge'
        ]
        
        text = (publisher + ' ' + journal).lower()
        
        for top in top_publishers:
            if top in text:
                return 'top'
        
        if publisher:
            return 'mid'
        
        return 'unknown'
    
    def _calculate_in_scope_confidence(
        self, 
        features: ScoringFeatures, 
        predicted_rank: int
    ) -> str:
        """Calculate in-scope confidence level"""
        if predicted_rank >= 2 and features.num_strong_anchors >= 1:
            return 'high'
        elif predicted_rank >= 1 and (features.num_strong_anchors >= 1 or 
                                      features.max_semantic_confidence >= 0.7):
            return 'med'
        else:
            return 'low'
    
    def _generate_reasoning(
        self,
        features: ScoringFeatures,
        predicted_rank: int,
        confidence: float,
        feature_importance: Dict
    ) -> str:
        """Generate human-readable reasoning"""
        parts = [f"Predicted rank {predicted_rank} ({confidence:.2f} confidence)"]
        
        # Top contributing factors
        if feature_importance:
            top_features = list(feature_importance.items())[:3]
            parts.append(
                "Top factors: " + ", ".join(f"{k}={v:.2f}" for k, v in top_features)
            )
        
        # Key signals
        signals = []
        if features.num_strong_anchors > 0:
            signals.append(f"{features.num_strong_anchors} strong anchors")
        if features.max_semantic_confidence >= 0.8:
            signals.append("high semantic match")
        if features.peer_reviewed:
            signals.append("peer-reviewed")
        
        if signals:
            parts.append("Signals: " + ", ".join(signals))
        
        return " | ".join(parts)
    
    def _make_recommendation(
        self,
        predicted_rank: int,
        confidence: float,
        in_scope_conf: str
    ) -> str:
        """Make submission recommendation"""
        if predicted_rank >= 2 and in_scope_conf in ['high', 'med']:
            return 'SUBMIT'
        elif predicted_rank >= 1:
            return 'HOLD'
        else:
            return 'SKIP'
    
    def _save_model(self):
        """Save trained model to disk"""
        import pickle
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.feature_scaler,
                'history': self.training_history
            }, f)
    
    def _load_model(self):
        """Load trained model from disk"""
        import pickle
        with open(self.model_path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.feature_scaler = data['scaler']
            self.training_history = data.get('history', [])


# Example usage
if __name__ == "__main__":
    scorer = RelevanceScorer()
    
    # Example features
    features = ScoringFeatures(
        has_doi=True,
        has_issn=True,
        peer_reviewed=True,
        open_access=True,
        school_access=False,
        days_before_critical=500,
        publication_year=2023,
        num_requirements_matched=3,
        num_strong_anchors=2,
        num_medium_anchors=1,
        num_weak_anchors=0,
        avg_semantic_confidence=0.75,
        max_semantic_confidence=0.85,
        document_length_chars=5000,
        num_technical_terms=45,
        num_citations=12,
        source_type='journal',
        publisher_tier='top',
        study_type='invalidity',
        is_priority_requirement=True
    )
    
    result = scorer.score_candidate(features)
    
    print(f"Predicted Rank: {result.predicted_rank}")
    print(f"Confidence: {result.rank_confidence:.2f}")
    print(f"In-scope: {result.in_scope_confidence}")
    print(f"Recommendation: {result.recommendation}")
    print(f"Reasoning: {result.reasoning}")
