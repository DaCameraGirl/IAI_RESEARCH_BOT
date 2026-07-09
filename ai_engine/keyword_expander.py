"""
Keyword Expander - Smart keyword expansion based on search results
Automatically discovers related terms and expands search coverage
"""

from typing import List, Dict, Set, Optional
from collections import Counter
import re
from pathlib import Path


class KeywordExpander:
    """
    Expand keywords based on search results and domain knowledge
    Features:
    - Synonym discovery
    - Related term extraction
    - Technical term expansion
    - Acronym expansion
    - Frequency analysis
    """
    
    # Common technical synonyms
    SYNONYM_MAP = {
        'device': ['apparatus', 'system', 'unit', 'equipment'],
        'method': ['process', 'procedure', 'technique', 'approach'],
        'circuit': ['circuitry', 'network', 'path'],
        'component': ['element', 'part', 'module'],
        'signal': ['waveform', 'pulse', 'transmission'],
        'data': ['information', 'content', 'payload'],
        'memory': ['storage', 'buffer', 'cache'],
        'processor': ['CPU', 'controller', 'unit'],
        'interface': ['connection', 'port', 'link'],
        'display': ['screen', 'monitor', 'panel']
    }
    
    # Common technical prefixes/suffixes
    TECHNICAL_AFFIXES = {
        'prefixes': ['micro', 'nano', 'multi', 'semi', 'ultra', 'super', 'sub'],
        'suffixes': ['based', 'enabled', 'driven', 'controlled', 'assisted']
    }
    
    def __init__(self, min_frequency: int = 3):
        """
        Initialize keyword expander
        
        Args:
            min_frequency: Minimum frequency for term to be considered
        """
        self.min_frequency = min_frequency
        self.discovered_terms: Set[str] = set()
        self.term_frequencies: Counter = Counter()
    
    def expand_keywords(
        self,
        base_keywords: List[str],
        search_results: List[Dict] = None,
        max_expansions: int = 10
    ) -> List[str]:
        """
        Expand keywords using multiple strategies
        
        Args:
            base_keywords: Original keywords
            search_results: Optional search results for context
            max_expansions: Maximum number of expanded keywords
            
        Returns:
            Expanded keyword list
        """
        expanded = set(base_keywords)
        
        # 1. Add synonyms
        for keyword in base_keywords:
            synonyms = self._get_synonyms(keyword)
            expanded.update(synonyms[:2])  # Add top 2 synonyms
        
        # 2. Add technical variations
        for keyword in base_keywords:
            variations = self._get_technical_variations(keyword)
            expanded.update(variations[:2])
        
        # 3. Extract from search results
        if search_results:
            extracted = self._extract_from_results(search_results, base_keywords)
            expanded.update(extracted[:max_expansions])
        
        # 4. Add compound terms
        if len(base_keywords) >= 2:
            compounds = self._generate_compounds(base_keywords)
            expanded.update(compounds[:3])
        
        return list(expanded)
    
    def _get_synonyms(self, keyword: str) -> List[str]:
        """Get synonyms for keyword"""
        keyword_lower = keyword.lower()
        
        # Check synonym map
        if keyword_lower in self.SYNONYM_MAP:
            return self.SYNONYM_MAP[keyword_lower]
        
        # Check if keyword is a synonym
        for base, synonyms in self.SYNONYM_MAP.items():
            if keyword_lower in synonyms:
                return [base] + [s for s in synonyms if s != keyword_lower]
        
        return []
    
    def _get_technical_variations(self, keyword: str) -> List[str]:
        """Generate technical variations of keyword"""
        variations = []
        keyword_lower = keyword.lower()
        
        # Add prefix variations
        for prefix in self.TECHNICAL_AFFIXES['prefixes']:
            if not keyword_lower.startswith(prefix):
                variations.append(f"{prefix}-{keyword}")
                variations.append(f"{prefix}{keyword}")
        
        # Add suffix variations
        for suffix in self.TECHNICAL_AFFIXES['suffixes']:
            if not keyword_lower.endswith(suffix):
                variations.append(f"{keyword}-{suffix}")
                variations.append(f"{keyword} {suffix}")
        
        return variations[:5]
    
    def _extract_from_results(
        self,
        search_results: List[Dict],
        base_keywords: List[str]
    ) -> List[str]:
        """Extract related terms from search results"""
        # Combine all text from results
        all_text = []
        for result in search_results:
            all_text.append(result.get('title', ''))
            all_text.append(result.get('snippet', ''))
        
        combined_text = ' '.join(all_text).lower()
        
        # Extract technical terms (capitalized words, hyphenated, etc.)
        technical_pattern = r'\b[A-Z][a-z]+(?:-[A-Z][a-z]+)*\b|\b[a-z]+-[a-z]+\b'
        technical_terms = re.findall(technical_pattern, ' '.join(all_text))
        
        # Count frequencies
        term_counter = Counter(technical_terms)
        
        # Filter by frequency and relevance
        related_terms = []
        for term, count in term_counter.most_common(20):
            term_lower = term.lower()
            
            # Skip if already in base keywords
            if term_lower in [k.lower() for k in base_keywords]:
                continue
            
            # Skip common words
            if term_lower in ['the', 'and', 'for', 'with', 'from', 'this', 'that']:
                continue
            
            # Must appear at least min_frequency times
            if count >= self.min_frequency:
                related_terms.append(term)
        
        return related_terms
    
    def _generate_compounds(self, keywords: List[str]) -> List[str]:
        """Generate compound terms from keywords"""
        compounds = []
        
        # Generate 2-word compounds
        for i, kw1 in enumerate(keywords):
            for kw2 in keywords[i+1:]:
                compounds.append(f"{kw1} {kw2}")
                compounds.append(f"{kw2} {kw1}")
        
        return compounds
    
    def analyze_keyword_effectiveness(
        self,
        keywords: List[str],
        search_results: List[Dict]
    ) -> Dict:
        """
        Analyze which keywords are most effective
        
        Args:
            keywords: List of keywords
            search_results: Search results
            
        Returns:
            Effectiveness analysis
        """
        keyword_stats = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Count appearances in results
            title_count = 0
            snippet_count = 0
            
            for result in search_results:
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                
                if keyword_lower in title:
                    title_count += 1
                if keyword_lower in snippet:
                    snippet_count += 1
            
            keyword_stats[keyword] = {
                'title_appearances': title_count,
                'snippet_appearances': snippet_count,
                'total_appearances': title_count + snippet_count,
                'effectiveness': (title_count * 2 + snippet_count) / max(len(search_results), 1)
            }
        
        # Sort by effectiveness
        sorted_keywords = sorted(
            keyword_stats.items(),
            key=lambda x: x[1]['effectiveness'],
            reverse=True
        )
        
        return {
            'keyword_stats': dict(sorted_keywords),
            'most_effective': sorted_keywords[0][0] if sorted_keywords else None,
            'least_effective': sorted_keywords[-1][0] if sorted_keywords else None
        }
    
    def suggest_new_keywords(
        self,
        base_keywords: List[str],
        search_results: List[Dict],
        max_suggestions: int = 5
    ) -> List[Dict]:
        """
        Suggest new keywords based on analysis
        
        Args:
            base_keywords: Current keywords
            search_results: Search results
            max_suggestions: Maximum suggestions
            
        Returns:
            List of keyword suggestions with rationale
        """
        suggestions = []
        
        # Extract frequent terms
        extracted = self._extract_from_results(search_results, base_keywords)
        
        for term in extracted[:max_suggestions]:
            # Calculate relevance score
            appearances = sum(
                1 for result in search_results
                if term.lower() in result.get('title', '').lower() or
                   term.lower() in result.get('snippet', '').lower()
            )
            
            relevance = appearances / len(search_results) if search_results else 0
            
            suggestions.append({
                'keyword': term,
                'relevance_score': relevance,
                'appearances': appearances,
                'rationale': f"Appears in {appearances} results ({relevance:.1%} of total)"
            })
        
        # Sort by relevance
        suggestions.sort(key=lambda s: s['relevance_score'], reverse=True)
        
        return suggestions[:max_suggestions]
    
    def expand_acronyms(self, text: str) -> Dict[str, List[str]]:
        """
        Find and expand acronyms in text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict of acronym -> possible expansions
        """
        acronyms = {}
        
        # Find potential acronyms (2-5 uppercase letters)
        acronym_pattern = r'\b[A-Z]{2,5}\b'
        found_acronyms = re.findall(acronym_pattern, text)
        
        for acronym in set(found_acronyms):
            # Look for expansion in surrounding text
            # Pattern: "Full Name (ACRONYM)" or "ACRONYM (Full Name)"
            expansion_pattern = rf'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\({acronym}\)'
            expansions = re.findall(expansion_pattern, text)
            
            if expansions:
                acronyms[acronym] = expansions
        
        return acronyms


# Example usage
if __name__ == "__main__":
    expander = KeywordExpander(min_frequency=2)
    
    # Base keywords
    base_keywords = ['blender', 'offset', 'blade']
    
    # Example search results
    search_results = [
        {
            'title': 'Rechargeable Blender with Offset Blade Design',
            'snippet': 'A portable blender featuring offset blade configuration for improved mixing...'
        },
        {
            'title': 'Multi-blade Blender System',
            'snippet': 'Advanced blending apparatus with multiple offset cutting blades...'
        },
        {
            'title': 'Portable Mixing Device',
            'snippet': 'Compact rechargeable mixing device with asymmetric blade arrangement...'
        }
    ]
    
    # Expand keywords
    expanded = expander.expand_keywords(base_keywords, search_results, max_expansions=10)
    print(f"Expanded keywords: {expanded}")
    
    # Analyze effectiveness
    effectiveness = expander.analyze_keyword_effectiveness(base_keywords, search_results)
    print(f"\nMost effective keyword: {effectiveness['most_effective']}")
    
    # Get suggestions
    suggestions = expander.suggest_new_keywords(base_keywords, search_results)
    print(f"\nSuggested new keywords:")
    for suggestion in suggestions:
        print(f"  • {suggestion['keyword']} - {suggestion['rationale']}")
