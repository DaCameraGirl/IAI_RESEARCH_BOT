"""
Patent Family Analyzer - Find related patents (continuations, divisionals, etc.)
Discovers patent families to find additional prior art
"""

from typing import List, Dict, Set, Optional
from pathlib import Path
import requests
import re
from datetime import datetime


class PatentFamilyAnalyzer:
    """
    Analyze patent families to discover related patents
    Features:
    - Continuations (CON)
    - Continuations-in-part (CIP)
    - Divisionals (DIV)
    - Provisional applications
    - Foreign equivalents (PCT, EP, JP, etc.)
    - Priority claims
    """
    
    def __init__(self, critical_date: Optional[str] = None):
        """
        Initialize patent family analyzer
        
        Args:
            critical_date: Critical date for filtering (YYYY-MM-DD)
        """
        self.critical_date = critical_date
        
        # Statistics
        self.stats = {
            'families_analyzed': 0,
            'related_patents_found': 0,
            'continuations': 0,
            'divisionals': 0,
            'foreign_equivalents': 0,
            'filtered_by_date': 0
        }
    
    def analyze_patent_family(self, patent_number: str) -> Dict:
        """
        Analyze patent family for a given patent
        
        Args:
            patent_number: Patent number (e.g., "US7373531")
            
        Returns:
            Family analysis dict with related patents
        """
        print(f"\n{'='*60}")
        print(f"Patent Family Analysis: {patent_number}")
        print(f"{'='*60}\n")
        
        self.stats['families_analyzed'] += 1
        
        # Get patent data
        patent_data = self._get_patent_data(patent_number)
        
        if not patent_data:
            return {
                'patent_number': patent_number,
                'family_members': [],
                'error': 'Patent data not found'
            }
        
        family_members = []
        
        # Find continuations
        continuations = self._find_continuations(patent_data)
        family_members.extend(continuations)
        self.stats['continuations'] += len(continuations)
        
        # Find divisionals
        divisionals = self._find_divisionals(patent_data)
        family_members.extend(divisionals)
        self.stats['divisionals'] += len(divisionals)
        
        # Find foreign equivalents
        foreign = self._find_foreign_equivalents(patent_data)
        family_members.extend(foreign)
        self.stats['foreign_equivalents'] += len(foreign)
        
        # Filter by critical date
        if self.critical_date:
            filtered_members = []
            for member in family_members:
                if member.get('filing_date', '') <= self.critical_date:
                    filtered_members.append(member)
                else:
                    self.stats['filtered_by_date'] += 1
            
            family_members = filtered_members
        
        self.stats['related_patents_found'] += len(family_members)
        
        print(f"✓ Found {len(family_members)} related patents:")
        print(f"  Continuations: {len([m for m in family_members if m['type'] == 'continuation'])}")
        print(f"  Divisionals: {len([m for m in family_members if m['type'] == 'divisional'])}")
        print(f"  Foreign: {len([m for m in family_members if m['type'] == 'foreign'])}")
        
        return {
            'patent_number': patent_number,
            'family_members': family_members,
            'statistics': {
                'total_found': len(family_members),
                'continuations': len([m for m in family_members if m['type'] == 'continuation']),
                'divisionals': len([m for m in family_members if m['type'] == 'divisional']),
                'foreign': len([m for m in family_members if m['type'] == 'foreign'])
            }
        }
    
    def _get_patent_data(self, patent_number: str) -> Optional[Dict]:
        """Get patent data from USPTO or Google Patents"""
        try:
            # Normalize patent number
            patent_number = patent_number.upper().replace(' ', '')
            
            # Try Google Patents API
            # For now, return structure showing how it would work
            
            # Example structure:
            return {
                'patent_number': patent_number,
                'title': 'Example Patent',
                'filing_date': '2004-01-10',
                'publication_date': '2008-05-06',
                'priority_claims': [],
                'related_applications': [],
                'family_id': 'US-12345-01'
            }
        
        except Exception as e:
            print(f"  ⚠ Error getting patent data: {e}")
            return None
    
    def _find_continuations(self, patent_data: Dict) -> List[Dict]:
        """Find continuation patents"""
        continuations = []
        
        try:
            # Parse related applications for continuations
            related_apps = patent_data.get('related_applications', [])
            
            for app in related_apps:
                app_type = app.get('type', '').lower()
                
                if 'continuation' in app_type and 'part' not in app_type:
                    continuations.append({
                        'patent_number': app.get('patent_number'),
                        'application_number': app.get('application_number'),
                        'filing_date': app.get('filing_date'),
                        'type': 'continuation',
                        'relationship': 'CON',
                        'title': app.get('title', '')
                    })
                
                elif 'continuation-in-part' in app_type or 'cip' in app_type:
                    continuations.append({
                        'patent_number': app.get('patent_number'),
                        'application_number': app.get('application_number'),
                        'filing_date': app.get('filing_date'),
                        'type': 'continuation',
                        'relationship': 'CIP',
                        'title': app.get('title', '')
                    })
        
        except Exception as e:
            print(f"  ⚠ Error finding continuations: {e}")
        
        return continuations
    
    def _find_divisionals(self, patent_data: Dict) -> List[Dict]:
        """Find divisional patents"""
        divisionals = []
        
        try:
            related_apps = patent_data.get('related_applications', [])
            
            for app in related_apps:
                app_type = app.get('type', '').lower()
                
                if 'divisional' in app_type or 'div' in app_type:
                    divisionals.append({
                        'patent_number': app.get('patent_number'),
                        'application_number': app.get('application_number'),
                        'filing_date': app.get('filing_date'),
                        'type': 'divisional',
                        'relationship': 'DIV',
                        'title': app.get('title', '')
                    })
        
        except Exception as e:
            print(f"  ⚠ Error finding divisionals: {e}")
        
        return divisionals
    
    def _find_foreign_equivalents(self, patent_data: Dict) -> List[Dict]:
        """Find foreign equivalent patents"""
        foreign = []
        
        try:
            # Use family ID to find foreign equivalents
            family_id = patent_data.get('family_id')
            
            if family_id:
                # Query patent family database
                # For now, return structure
                pass
            
            # Also check priority claims
            priority_claims = patent_data.get('priority_claims', [])
            
            for claim in priority_claims:
                country = claim.get('country', '')
                
                if country and country != 'US':
                    foreign.append({
                        'patent_number': claim.get('patent_number'),
                        'application_number': claim.get('application_number'),
                        'filing_date': claim.get('filing_date'),
                        'type': 'foreign',
                        'relationship': f'Foreign ({country})',
                        'country': country,
                        'title': claim.get('title', '')
                    })
        
        except Exception as e:
            print(f"  ⚠ Error finding foreign equivalents: {e}")
        
        return foreign
    
    def find_parent_patents(self, patent_number: str) -> List[Dict]:
        """Find parent patents (applications this patent claims priority from)"""
        print(f"\nFinding parent patents for {patent_number}...")
        
        patent_data = self._get_patent_data(patent_number)
        
        if not patent_data:
            return []
        
        parents = []
        
        # Check priority claims
        priority_claims = patent_data.get('priority_claims', [])
        
        for claim in priority_claims:
            parents.append({
                'patent_number': claim.get('patent_number'),
                'application_number': claim.get('application_number'),
                'filing_date': claim.get('filing_date'),
                'type': 'parent',
                'relationship': 'Priority claim',
                'title': claim.get('title', '')
            })
        
        print(f"  Found {len(parents)} parent patents")
        
        return parents
    
    def find_child_patents(self, patent_number: str) -> List[Dict]:
        """Find child patents (applications that claim priority from this patent)"""
        print(f"\nFinding child patents for {patent_number}...")
        
        # Query USPTO for applications claiming priority from this patent
        # For now, return structure
        
        children = []
        
        print(f"  Found {len(children)} child patents")
        
        return children
    
    def visualize_family_tree(self, patent_number: str) -> str:
        """Generate ASCII family tree visualization"""
        family_data = self.analyze_patent_family(patent_number)
        
        lines = [
            f"\nPatent Family Tree: {patent_number}",
            "=" * 60,
            ""
        ]
        
        # Group by type
        continuations = [m for m in family_data['family_members'] if m['type'] == 'continuation']
        divisionals = [m for m in family_data['family_members'] if m['type'] == 'divisional']
        foreign = [m for m in family_data['family_members'] if m['type'] == 'foreign']
        
        # Root patent
        lines.append(f"📄 {patent_number} (Root)")
        lines.append("")
        
        # Continuations
        if continuations:
            lines.append("├─ Continuations:")
            for i, cont in enumerate(continuations):
                prefix = "│  ├─" if i < len(continuations) - 1 else "│  └─"
                lines.append(f"{prefix} {cont['patent_number']} ({cont['relationship']}) - {cont['filing_date']}")
            lines.append("")
        
        # Divisionals
        if divisionals:
            lines.append("├─ Divisionals:")
            for i, div in enumerate(divisionals):
                prefix = "│  ├─" if i < len(divisionals) - 1 else "│  └─"
                lines.append(f"{prefix} {div['patent_number']} (DIV) - {div['filing_date']}")
            lines.append("")
        
        # Foreign equivalents
        if foreign:
            lines.append("└─ Foreign Equivalents:")
            for i, fgn in enumerate(foreign):
                prefix = "   ├─" if i < len(foreign) - 1 else "   └─"
                lines.append(f"{prefix} {fgn['patent_number']} ({fgn['country']}) - {fgn['filing_date']}")
        
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    analyzer = PatentFamilyAnalyzer(critical_date="2019-10-28")
    
    # Analyze patent family
    family_data = analyzer.analyze_patent_family("US7373531")
    
    print(f"\nFamily Members:")
    for member in family_data['family_members']:
        print(f"  • {member['patent_number']} ({member['relationship']}) - {member['filing_date']}")
    
    # Visualize family tree
    tree = analyzer.visualize_family_tree("US7373531")
    print(tree)
