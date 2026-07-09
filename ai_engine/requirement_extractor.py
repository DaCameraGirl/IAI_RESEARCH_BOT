"""
Requirement Extractor - Auto-extract requirements from study brief
Parses study briefs to identify key requirements and search parameters
"""

from typing import List, Dict, Optional, Set
from pathlib import Path
import re
from datetime import datetime


class RequirementExtractor:
    """
    Extract requirements from study brief documents
    Features:
    - Critical date extraction
    - Keyword extraction
    - Part number extraction
    - Manufacturer extraction
    - Technical requirement parsing
    - Claim element identification
    """
    
    # Date patterns
    DATE_PATTERNS = [
        r'critical date[:\s]+(\d{4}-\d{2}-\d{2})',
        r'filing date[:\s]+(\d{4}-\d{2}-\d{2})',
        r'priority date[:\s]+(\d{4}-\d{2}-\d{2})',
        r'(\d{4}-\d{2}-\d{2})',  # Generic YYYY-MM-DD
        r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
    ]
    
    # Part number patterns
    PART_NUMBER_PATTERNS = [
        r'\b[A-Z]{2,4}[-\s]?\d{3,6}[A-Z]?\b',  # ABC-1234, ABC1234A
        r'\b\d{3,6}[-\s]?[A-Z]{2,4}\b',  # 1234-ABC
        r'\bP/N[:\s]+([A-Z0-9-]+)\b',  # P/N: ABC-1234
        r'\bpart number[:\s]+([A-Z0-9-]+)\b',
    ]
    
    # Manufacturer patterns
    MANUFACTURER_KEYWORDS = [
        'manufacturer', 'vendor', 'supplier', 'company', 'corporation',
        'made by', 'produced by', 'manufactured by'
    ]
    
    def __init__(self):
        """Initialize requirement extractor"""
        self.extracted_data = {}
    
    def extract_from_file(self, study_brief_path: Path) -> Dict:
        """
        Extract requirements from study brief file
        
        Args:
            study_brief_path: Path to STUDY_BRIEF.md or similar
            
        Returns:
            Extracted requirements dict
        """
        if not study_brief_path.exists():
            return {
                'error': f'Study brief not found: {study_brief_path}'
            }
        
        # Read file
        content = study_brief_path.read_text(encoding='utf-8')
        
        return self.extract_from_text(content)
    
    def extract_from_text(self, text: str) -> Dict:
        """
        Extract requirements from text
        
        Args:
            text: Study brief text
            
        Returns:
            Extracted requirements dict
        """
        requirements = {
            'critical_date': self._extract_critical_date(text),
            'keywords': self._extract_keywords(text),
            'part_numbers': self._extract_part_numbers(text),
            'manufacturers': self._extract_manufacturers(text),
            'patent_number': self._extract_patent_number(text),
            'technical_requirements': self._extract_technical_requirements(text),
            'claim_elements': self._extract_claim_elements(text),
            'target_domains': self._extract_target_domains(text)
        }
        
        # Store for later reference
        self.extracted_data = requirements
        
        return requirements
    
    def _extract_critical_date(self, text: str) -> Optional[str]:
        """Extract critical date from text"""
        text_lower = text.lower()
        
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                # Return first match, try to normalize to YYYY-MM-DD
                date_str = matches[0]
                
                # Try to parse and normalize
                try:
                    # Handle MM/DD/YYYY
                    if '/' in date_str:
                        parts = date_str.split('/')
                        if len(parts) == 3:
                            return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                    
                    # Already YYYY-MM-DD
                    if '-' in date_str and len(date_str) == 10:
                        return date_str
                
                except Exception:
                    pass
        
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        keywords = set()
        
        # Look for explicit keyword sections
        keyword_section_pattern = r'(?:keywords?|search terms?)[:\s]+([^\n]+)'
        matches = re.findall(keyword_section_pattern, text, re.IGNORECASE)
        
        for match in matches:
            # Split by comma, semicolon, or pipe
            terms = re.split(r'[,;|]', match)
            keywords.update(term.strip() for term in terms if term.strip())
        
        # Extract technical terms (capitalized, hyphenated)
        technical_pattern = r'\b[A-Z][a-z]+(?:-[A-Z][a-z]+)*\b'
        technical_terms = re.findall(technical_pattern, text)
        
        # Filter and add significant technical terms
        for term in technical_terms:
            if len(term) > 3 and term.lower() not in ['the', 'and', 'for']:
                keywords.add(term)
        
        # Extract quoted terms (likely important)
        quoted_pattern = r'"([^"]+)"'
        quoted_terms = re.findall(quoted_pattern, text)
        keywords.update(quoted_terms)
        
        return sorted(list(keywords))[:20]  # Limit to top 20
    
    def _extract_part_numbers(self, text: str) -> List[str]:
        """Extract part numbers from text"""
        part_numbers = set()
        
        for pattern in self.PART_NUMBER_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            part_numbers.update(matches)
        
        return sorted(list(part_numbers))
    
    def _extract_manufacturers(self, text: str) -> List[str]:
        """Extract manufacturer names from text"""
        manufacturers = set()
        
        # Look for manufacturer sections
        for keyword in self.MANUFACTURER_KEYWORDS:
            pattern = rf'{keyword}[:\s]+([A-Z][a-zA-Z\s&,]+?)(?:\.|,|\n|$)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Clean up
                manufacturer = match.strip()
                if len(manufacturer) > 2 and len(manufacturer) < 50:
                    manufacturers.add(manufacturer)
        
        # Look for common manufacturer patterns
        # "by [Manufacturer]", "[Manufacturer] Inc.", etc.
        company_pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:Inc\.|Corp\.|Ltd\.|LLC|GmbH)\b'
        companies = re.findall(company_pattern, text)
        manufacturers.update(companies)
        
        return sorted(list(manufacturers))
    
    def _extract_patent_number(self, text: str) -> Optional[str]:
        """Extract patent number from text"""
        # US patent pattern
        us_pattern = r'\bUS\s*(\d{7,8})\b'
        matches = re.findall(us_pattern, text, re.IGNORECASE)
        
        if matches:
            return f"US{matches[0]}"
        
        # Generic patent pattern
        patent_pattern = r'\b([A-Z]{2}\d{7,10})\b'
        matches = re.findall(patent_pattern, text)
        
        if matches:
            return matches[0]
        
        return None
    
    def _extract_technical_requirements(self, text: str) -> List[str]:
        """Extract technical requirements from text"""
        requirements = []
        
        # Look for requirement sections
        req_section_pattern = r'(?:requirements?|specifications?|features?)[:\s]+([^\n]+(?:\n(?!\n)[^\n]+)*)'
        matches = re.findall(req_section_pattern, text, re.IGNORECASE)
        
        for match in matches:
            # Split into individual requirements
            lines = match.split('\n')
            for line in lines:
                line = line.strip()
                # Remove bullet points, numbers
                line = re.sub(r'^[-*•\d.)\s]+', '', line)
                if len(line) > 10:
                    requirements.append(line)
        
        return requirements[:10]  # Limit to top 10
    
    def _extract_claim_elements(self, text: str) -> List[str]:
        """Extract claim elements from text"""
        elements = []
        
        # Look for claim sections
        claim_pattern = r'(?:claim|element)[:\s]+([^\n]+)'
        matches = re.findall(claim_pattern, text, re.IGNORECASE)
        
        for match in matches:
            elements.append(match.strip())
        
        # Look for "comprising" clauses (common in claims)
        comprising_pattern = r'comprising[:\s]+([^.]+)'
        matches = re.findall(comprising_pattern, text, re.IGNORECASE)
        
        for match in matches:
            elements.append(match.strip())
        
        return elements[:10]
    
    def _extract_target_domains(self, text: str) -> List[str]:
        """Extract target domains/websites from text"""
        domains = set()
        
        # URL pattern
        url_pattern = r'https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        matches = re.findall(url_pattern, text)
        domains.update(matches)
        
        # Domain pattern (without http)
        domain_pattern = r'\b([a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        matches = re.findall(domain_pattern, text)
        domains.update(matches)
        
        return sorted(list(domains))
    
    def generate_search_config(self, requirements: Dict) -> Dict:
        """
        Generate search configuration from extracted requirements
        
        Args:
            requirements: Extracted requirements dict
            
        Returns:
            Search configuration dict
        """
        return {
            'study_id': 'auto_extracted',
            'critical_date': requirements.get('critical_date', ''),
            'keywords': requirements.get('keywords', []),
            'part_numbers': requirements.get('part_numbers', []),
            'manufacturers': requirements.get('manufacturers', []),
            'patent_number': requirements.get('patent_number'),
            'target_domains': requirements.get('target_domains', []),
            'search_strategy': self._determine_search_strategy(requirements)
        }
    
    def _determine_search_strategy(self, requirements: Dict) -> str:
        """Determine appropriate search strategy based on requirements"""
        # If patent number exists, likely invalidity search
        if requirements.get('patent_number'):
            # Check if product-related
            keywords = requirements.get('keywords', [])
            product_indicators = ['product', 'device', 'apparatus', 'system', 'datasheet']
            
            if any(indicator in ' '.join(keywords).lower() for indicator in product_indicators):
                return 'invalidity_product'
            else:
                return 'invalidity_npl'
        
        # Check for copyright indicators
        copyright_indicators = ['hymn', 'song', 'music', 'lyrics', 'composition']
        keywords_text = ' '.join(requirements.get('keywords', [])).lower()
        
        if any(indicator in keywords_text for indicator in copyright_indicators):
            return 'copyright'
        
        # Default to product search
        return 'invalidity_product'
    
    def validate_requirements(self, requirements: Dict) -> Dict:
        """
        Validate extracted requirements
        
        Args:
            requirements: Extracted requirements dict
            
        Returns:
            Validation result with warnings
        """
        warnings = []
        
        # Check critical date
        if not requirements.get('critical_date'):
            warnings.append('No critical date found')
        
        # Check keywords
        if not requirements.get('keywords'):
            warnings.append('No keywords found')
        elif len(requirements['keywords']) < 3:
            warnings.append('Very few keywords found (< 3)')
        
        # Check if we have any identifiers
        has_identifiers = any([
            requirements.get('part_numbers'),
            requirements.get('manufacturers'),
            requirements.get('patent_number')
        ])
        
        if not has_identifiers:
            warnings.append('No part numbers, manufacturers, or patent numbers found')
        
        return {
            'is_valid': len(warnings) == 0,
            'warnings': warnings,
            'completeness': self._calculate_completeness(requirements)
        }
    
    def _calculate_completeness(self, requirements: Dict) -> float:
        """Calculate completeness score (0-1)"""
        score = 0.0
        max_score = 7.0
        
        if requirements.get('critical_date'):
            score += 1.0
        if requirements.get('keywords'):
            score += 1.0
        if requirements.get('part_numbers'):
            score += 1.0
        if requirements.get('manufacturers'):
            score += 1.0
        if requirements.get('patent_number'):
            score += 1.0
        if requirements.get('technical_requirements'):
            score += 1.0
        if requirements.get('target_domains'):
            score += 1.0
        
        return score / max_score


# Example usage
if __name__ == "__main__":
    extractor = RequirementExtractor()
    
    # Example study brief text
    study_brief = """
    Study Brief: Rechargeable Blender with Offset Blades
    
    Critical Date: 2019-10-28
    Patent Number: US10123456
    
    Keywords: blender, offset, blade, rechargeable, portable
    
    Manufacturer: BlendTech Inc.
    Part Numbers: BT-5000, BT-5001A
    
    Requirements:
    - Rechargeable battery system
    - Offset blade configuration
    - Portable design
    - Safety interlock mechanism
    
    Target domains: blendtech.com, archive.org
    """
    
    # Extract requirements
    requirements = extractor.extract_from_text(study_brief)
    
    print("Extracted Requirements:")
    print(f"  Critical Date: {requirements['critical_date']}")
    print(f"  Keywords: {requirements['keywords']}")
    print(f"  Part Numbers: {requirements['part_numbers']}")
    print(f"  Manufacturers: {requirements['manufacturers']}")
    print(f"  Patent: {requirements['patent_number']}")
    
    # Generate search config
    config = extractor.generate_search_config(requirements)
    print(f"\nSearch Strategy: {config['search_strategy']}")
    
    # Validate
    validation = extractor.validate_requirements(requirements)
    print(f"\nValidation:")
    print(f"  Valid: {validation['is_valid']}")
    print(f"  Completeness: {validation['completeness']:.1%}")
    if validation['warnings']:
        print(f"  Warnings: {', '.join(validation['warnings'])}")
