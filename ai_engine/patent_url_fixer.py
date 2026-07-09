"""
Patent URL Generator - Correct URLs for USPTO, WIPO, EPO, JPO, etc.
Fixes 404 errors from incorrect patent office URLs
"""

import re
from typing import Optional, Dict


class PatentURLGenerator:
    """
    Generates correct URLs for patents from different patent offices
    Handles: USPTO (US), WIPO (WO), EPO (EP), JPO (JP), KIPO (KR), etc.
    """
    
    # Patent office URL templates
    OFFICE_URLS = {
        'US': {
            'pdf': 'https://patentimages.storage.googleapis.com/pdfs/{patent_number}.pdf',
            'html': 'https://patents.google.com/patent/{patent_number}',
            'official': 'https://ppubs.uspto.gov/dirsearch-public/print/downloadPdf/{patent_number}'
        },
        'WO': {
            'pdf': 'https://patentscope.wipo.int/search/en/download.jsf?docId={patent_number}&recNum=1&maxRec=&office=&prevFilter=&sortOption=&queryString=&tab=PCTDescription',
            'html': 'https://patentscope.wipo.int/search/en/detail.jsf?docId={patent_number}',
            'official': 'https://patentscope.wipo.int/search/en/detail.jsf?docId={patent_number}'
        },
        'EP': {
            'pdf': 'https://data.epo.org/publication-server/pdf-document?pn={patent_number}&ki=A1',
            'html': 'https://worldwide.espacenet.com/patent/search?q=pn%3D{patent_number}',
            'official': 'https://register.epo.org/application?number={patent_number_clean}'
        },
        'JP': {
            'pdf': 'https://patents.google.com/patent/{patent_number}',
            'html': 'https://patents.google.com/patent/{patent_number}',
            'official': 'https://www.j-platpat.inpit.go.jp/c1800/PU/JP-{patent_number_clean}/11/en'
        },
        'KR': {
            'pdf': 'https://patents.google.com/patent/{patent_number}',
            'html': 'https://patents.google.com/patent/{patent_number}',
            'official': 'http://engpat.kipris.or.kr/engpat/biblioa.do?method=biblioFrame&applno={patent_number_clean}'
        },
        'CN': {
            'pdf': 'https://patents.google.com/patent/{patent_number}',
            'html': 'https://patents.google.com/patent/{patent_number}',
            'official': 'https://patents.google.com/patent/{patent_number}'
        }
    }
    
    @staticmethod
    def detect_patent_office(patent_number: str) -> Optional[str]:
        """
        Detect patent office from patent number
        
        Args:
            patent_number: Patent number (e.g., "US7373531", "WO2021086553")
            
        Returns:
            Office code (US, WO, EP, JP, KR, CN) or None
        """
        patent_number = patent_number.upper().strip()
        
        # Remove common prefixes/suffixes
        patent_number = re.sub(r'^(PAT|PATENT|NO\.?|#)\s*', '', patent_number, flags=re.IGNORECASE)
        
        # Check for office codes
        if re.match(r'^US\d+', patent_number):
            return 'US'
        elif re.match(r'^WO\d{4}', patent_number):
            return 'WO'
        elif re.match(r'^EP\d+', patent_number):
            return 'EP'
        elif re.match(r'^JP\d+', patent_number):
            return 'JP'
        elif re.match(r'^KR\d+', patent_number):
            return 'KR'
        elif re.match(r'^CN\d+', patent_number):
            return 'CN'
        
        # If no prefix, assume US if all digits
        if re.match(r'^\d{7,8}$', patent_number):
            return 'US'
        
        return None
    
    @staticmethod
    def normalize_patent_number(patent_number: str, office: str) -> str:
        """
        Normalize patent number for URL generation
        
        Args:
            patent_number: Raw patent number
            office: Office code (US, WO, EP, etc.)
            
        Returns:
            Normalized patent number
        """
        patent_number = patent_number.upper().strip()
        
        # Remove spaces and hyphens
        patent_number = re.sub(r'[\s\-]', '', patent_number)
        
        if office == 'US':
            # US patents: US7373531 or 7373531
            match = re.search(r'(US)?(\d{7,8})', patent_number)
            if match:
                return f"US{match.group(2)}"
        
        elif office == 'WO':
            # WIPO patents: WO2021086553
            match = re.search(r'(WO)?(\d{4}\d+)', patent_number)
            if match:
                return f"WO{match.group(2)}"
        
        elif office == 'EP':
            # European patents: EP1234567
            match = re.search(r'(EP)?(\d+)', patent_number)
            if match:
                return f"EP{match.group(2)}"
        
        elif office == 'JP':
            # Japanese patents: JP2021123456
            match = re.search(r'(JP)?(\d+)', patent_number)
            if match:
                return f"JP{match.group(2)}"
        
        elif office == 'KR':
            # Korean patents: KR1020210123456
            match = re.search(r'(KR)?(\d+)', patent_number)
            if match:
                return f"KR{match.group(2)}"
        
        elif office == 'CN':
            # Chinese patents: CN112345678
            match = re.search(r'(CN)?(\d+)', patent_number)
            if match:
                return f"CN{match.group(2)}"
        
        return patent_number
    
    @staticmethod
    def get_patent_number_clean(patent_number: str) -> str:
        """Get patent number without office prefix"""
        return re.sub(r'^[A-Z]{2}', '', patent_number)
    
    @classmethod
    def generate_urls(cls, patent_number: str) -> Dict[str, str]:
        """
        Generate all URLs for a patent
        
        Args:
            patent_number: Patent number (e.g., "US7373531", "WO2021086553")
            
        Returns:
            Dict with 'pdf', 'html', 'official' URLs
        """
        # Detect office
        office = cls.detect_patent_office(patent_number)
        
        if not office:
            return {
                'pdf': None,
                'html': f"https://patents.google.com/patent/{patent_number}",
                'official': None,
                'error': f"Unknown patent office for: {patent_number}"
            }
        
        # Normalize patent number
        normalized = cls.normalize_patent_number(patent_number, office)
        clean = cls.get_patent_number_clean(normalized)
        
        # Get URL templates
        templates = cls.OFFICE_URLS.get(office, {})
        
        # Generate URLs
        urls = {}
        for url_type, template in templates.items():
            if template:
                url = template.format(
                    patent_number=normalized,
                    patent_number_clean=clean
                )
                urls[url_type] = url
            else:
                urls[url_type] = None
        
        urls['office'] = office
        urls['normalized'] = normalized
        
        return urls
    
    @classmethod
    def get_best_pdf_url(cls, patent_number: str) -> Optional[str]:
        """
        Get the best PDF URL for a patent
        
        Args:
            patent_number: Patent number
            
        Returns:
            Best PDF URL or None
        """
        urls = cls.generate_urls(patent_number)
        
        # Try in order: official PDF, Google Patents, HTML
        return urls.get('pdf') or urls.get('html')
    
    @classmethod
    def fix_patent_url(cls, url: str) -> str:
        """
        Fix incorrect patent URL
        
        Args:
            url: Potentially incorrect URL
            
        Returns:
            Corrected URL
        """
        # Extract patent number from URL
        patent_match = re.search(r'(US|WO|EP|JP|KR|CN)?\d{7,}[A-Z]?\d*', url, re.IGNORECASE)
        
        if not patent_match:
            return url
        
        patent_number = patent_match.group(0)
        
        # Generate correct URL
        return cls.get_best_pdf_url(patent_number) or url


# Example usage and tests
if __name__ == "__main__":
    generator = PatentURLGenerator()
    
    test_patents = [
        "US7373531",
        "WO2021086553",
        "EP1234567",
        "JP2021123456",
        "KR1020210123456",
        "7373531",  # US patent without prefix
    ]
    
    print("Patent URL Generator Test\n" + "="*60)
    
    for patent in test_patents:
        print(f"\nPatent: {patent}")
        urls = generator.generate_urls(patent)
        
        print(f"  Office: {urls.get('office', 'Unknown')}")
        print(f"  Normalized: {urls.get('normalized', 'N/A')}")
        print(f"  PDF: {urls.get('pdf', 'N/A')}")
        print(f"  HTML: {urls.get('html', 'N/A')}")
        print(f"  Official: {urls.get('official', 'N/A')}")
    
    # Test URL fixing
    print("\n" + "="*60)
    print("URL Fixing Test\n")
    
    bad_url = "https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/WO2021086553"
    print(f"Bad URL: {bad_url}")
    fixed_url = generator.fix_patent_url(bad_url)
    print(f"Fixed URL: {fixed_url}")
