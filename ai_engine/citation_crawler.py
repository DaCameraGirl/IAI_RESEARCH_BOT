"""
Citation Graph Crawler - Follow references to discover more prior art
Crawls citation networks to find related documents
"""

from typing import List, Dict, Set, Optional
from pathlib import Path
from datetime import datetime
import requests
from collections import deque
import time


class CitationCrawler:
    """
    Crawl citation graphs to discover related prior art
    Features:
    - Backward citations (references)
    - Forward citations (cited by)
    - Multi-hop crawling
    - Duplicate detection
    - Date filtering
    """
    
    def __init__(
        self,
        max_depth: int = 2,
        max_citations_per_doc: int = 20,
        critical_date: Optional[str] = None
    ):
        """
        Initialize citation crawler
        
        Args:
            max_depth: Maximum crawl depth (hops)
            max_citations_per_doc: Max citations to follow per document
            critical_date: Critical date for filtering (YYYY-MM-DD)
        """
        self.max_depth = max_depth
        self.max_citations_per_doc = max_citations_per_doc
        self.critical_date = critical_date
        
        # Track visited documents
        self.visited: Set[str] = set()
        
        # Statistics
        self.stats = {
            'documents_crawled': 0,
            'citations_found': 0,
            'citations_filtered': 0,
            'depth_reached': 0
        }
    
    def crawl_from_patent(
        self,
        patent_number: str,
        direction: str = 'both'
    ) -> List[Dict]:
        """
        Crawl citations from a patent
        
        Args:
            patent_number: Starting patent number
            direction: 'backward' (references), 'forward' (cited by), or 'both'
            
        Returns:
            List of discovered documents
        """
        print(f"\n{'='*60}")
        print(f"Citation Crawl: {patent_number}")
        print(f"Direction: {direction}, Max depth: {self.max_depth}")
        print(f"{'='*60}\n")
        
        discovered = []
        
        # BFS queue: (doc_id, depth)
        queue = deque([(patent_number, 0)])
        self.visited.add(patent_number)
        
        while queue:
            current_id, depth = queue.popleft()
            
            if depth > self.max_depth:
                continue
            
            self.stats['depth_reached'] = max(self.stats['depth_reached'], depth)
            
            print(f"[Depth {depth}] Crawling {current_id}...")
            
            # Get citations
            citations = self._get_patent_citations(current_id, direction)
            
            self.stats['documents_crawled'] += 1
            self.stats['citations_found'] += len(citations)
            
            # Process citations
            for citation in citations[:self.max_citations_per_doc]:
                citation_id = citation.get('patent_number') or citation.get('doi')
                
                if not citation_id or citation_id in self.visited:
                    continue
                
                # Filter by critical date
                if self.critical_date and citation.get('date'):
                    if citation['date'] > self.critical_date:
                        self.stats['citations_filtered'] += 1
                        continue
                
                self.visited.add(citation_id)
                discovered.append({
                    **citation,
                    'discovered_from': current_id,
                    'depth': depth + 1
                })
                
                # Add to queue for further crawling
                if depth + 1 < self.max_depth:
                    queue.append((citation_id, depth + 1))
            
            # Rate limiting
            time.sleep(0.5)
        
        print(f"\n✓ Crawl complete:")
        print(f"  Documents crawled: {self.stats['documents_crawled']}")
        print(f"  Citations found: {self.stats['citations_found']}")
        print(f"  Filtered (date): {self.stats['citations_filtered']}")
        print(f"  Discovered: {len(discovered)}")
        print(f"  Max depth reached: {self.stats['depth_reached']}")
        
        return discovered
    
    def crawl_from_npl(
        self,
        doi: str,
        direction: str = 'both'
    ) -> List[Dict]:
        """
        Crawl citations from NPL (journal article)
        
        Args:
            doi: Starting DOI
            direction: 'backward' (references), 'forward' (cited by), or 'both'
            
        Returns:
            List of discovered documents
        """
        print(f"\n{'='*60}")
        print(f"Citation Crawl: {doi}")
        print(f"Direction: {direction}, Max depth: {self.max_depth}")
        print(f"{'='*60}\n")
        
        discovered = []
        
        # BFS queue
        queue = deque([(doi, 0)])
        self.visited.add(doi)
        
        while queue:
            current_doi, depth = queue.popleft()
            
            if depth > self.max_depth:
                continue
            
            self.stats['depth_reached'] = max(self.stats['depth_reached'], depth)
            
            print(f"[Depth {depth}] Crawling {current_doi}...")
            
            # Get citations
            citations = self._get_npl_citations(current_doi, direction)
            
            self.stats['documents_crawled'] += 1
            self.stats['citations_found'] += len(citations)
            
            # Process citations
            for citation in citations[:self.max_citations_per_doc]:
                citation_doi = citation.get('doi')
                
                if not citation_doi or citation_doi in self.visited:
                    continue
                
                # Filter by critical date
                if self.critical_date and citation.get('date'):
                    if citation['date'] > self.critical_date:
                        self.stats['citations_filtered'] += 1
                        continue
                
                self.visited.add(citation_doi)
                discovered.append({
                    **citation,
                    'discovered_from': current_doi,
                    'depth': depth + 1
                })
                
                # Add to queue
                if depth + 1 < self.max_depth:
                    queue.append((citation_doi, depth + 1))
            
            # Rate limiting
            time.sleep(0.5)
        
        print(f"\n✓ Crawl complete:")
        print(f"  Documents crawled: {self.stats['documents_crawled']}")
        print(f"  Citations found: {self.stats['citations_found']}")
        print(f"  Discovered: {len(discovered)}")
        
        return discovered
    
    def _get_patent_citations(
        self,
        patent_number: str,
        direction: str
    ) -> List[Dict]:
        """Get citations for a patent"""
        citations = []
        
        try:
            # Use Google Patents API or USPTO API
            # For now, return structure showing how it would work
            
            if direction in ['backward', 'both']:
                # Get references (backward citations)
                # API call: GET /patent/{patent_number}/references
                pass
            
            if direction in ['forward', 'both']:
                # Get cited-by (forward citations)
                # API call: GET /patent/{patent_number}/cited-by
                pass
            
            # Example structure:
            # citations.append({
            #     'patent_number': 'US1234567',
            #     'title': 'Related Patent',
            #     'date': '2018-01-15',
            #     'assignee': 'Company Name',
            #     'type': 'patent'
            # })
        
        except Exception as e:
            print(f"  ⚠ Error getting citations: {e}")
        
        return citations
    
    def _get_npl_citations(
        self,
        doi: str,
        direction: str
    ) -> List[Dict]:
        """Get citations for NPL document"""
        citations = []
        
        try:
            # Use Semantic Scholar API or OpenCitations
            if direction in ['backward', 'both']:
                # Get references
                citations.extend(self._get_semantic_scholar_references(doi))
            
            if direction in ['forward', 'both']:
                # Get cited-by
                citations.extend(self._get_semantic_scholar_citations(doi))
        
        except Exception as e:
            print(f"  ⚠ Error getting citations: {e}")
        
        return citations
    
    def _get_semantic_scholar_references(self, doi: str) -> List[Dict]:
        """Get references from Semantic Scholar"""
        try:
            # Semantic Scholar API
            url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}/references"
            params = {
                'fields': 'title,authors,year,externalIds,publicationDate',
                'limit': self.max_citations_per_doc
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                references = []
                for ref in data.get('data', []):
                    paper = ref.get('citedPaper', {})
                    
                    # Extract DOI
                    external_ids = paper.get('externalIds', {})
                    ref_doi = external_ids.get('DOI')
                    
                    if ref_doi:
                        references.append({
                            'doi': ref_doi,
                            'title': paper.get('title', ''),
                            'authors': ', '.join([a.get('name', '') for a in paper.get('authors', [])]),
                            'date': paper.get('publicationDate', ''),
                            'year': paper.get('year'),
                            'type': 'npl'
                        })
                
                return references
        
        except Exception as e:
            print(f"  ⚠ Semantic Scholar error: {e}")
        
        return []
    
    def _get_semantic_scholar_citations(self, doi: str) -> List[Dict]:
        """Get citations from Semantic Scholar"""
        try:
            # Semantic Scholar API
            url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}/citations"
            params = {
                'fields': 'title,authors,year,externalIds,publicationDate',
                'limit': self.max_citations_per_doc
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                citations = []
                for cit in data.get('data', []):
                    paper = cit.get('citingPaper', {})
                    
                    # Extract DOI
                    external_ids = paper.get('externalIds', {})
                    cit_doi = external_ids.get('DOI')
                    
                    if cit_doi:
                        citations.append({
                            'doi': cit_doi,
                            'title': paper.get('title', ''),
                            'authors': ', '.join([a.get('name', '') for a in paper.get('authors', [])]),
                            'date': paper.get('publicationDate', ''),
                            'year': paper.get('year'),
                            'type': 'npl'
                        })
                
                return citations
        
        except Exception as e:
            print(f"  ⚠ Semantic Scholar error: {e}")
        
        return []


# Example usage
if __name__ == "__main__":
    crawler = CitationCrawler(
        max_depth=2,
        max_citations_per_doc=10,
        critical_date="2019-10-28"
    )
    
    # Example: Crawl from patent
    discovered = crawler.crawl_from_patent(
        patent_number="US7373531",
        direction="both"
    )
    
    print(f"\nDiscovered {len(discovered)} related documents")
    
    for doc in discovered[:5]:
        print(f"  • {doc.get('title', 'Untitled')}")
        print(f"    From: {doc['discovered_from']}, Depth: {doc['depth']}")
