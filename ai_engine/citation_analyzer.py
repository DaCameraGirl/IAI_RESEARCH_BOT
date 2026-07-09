"""
Citation Analyzer - Automated citation graph crawling and analysis
Finds related prior art through backward/forward citation traversal
"""

import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import re


@dataclass
class CitationNode:
    """Node in citation graph"""
    id: str  # DOI, patent number, or unique identifier
    title: str
    authors: str
    date: str
    document_type: str  # "patent" | "article" | "thesis" | "conference"
    url: Optional[str] = None
    abstract: Optional[str] = None
    citations_backward: List[str] = None  # What this cites
    citations_forward: List[str] = None   # What cites this
    
    def __post_init__(self):
        if self.citations_backward is None:
            self.citations_backward = []
        if self.citations_forward is None:
            self.citations_forward = []


@dataclass
class CitationPath:
    """Path through citation graph"""
    nodes: List[CitationNode]
    path_type: str  # "backward" | "forward" | "mixed"
    relevance_score: float
    reasoning: str


class CitationAnalyzer:
    """
    Citation graph analysis using:
    - Backward citation crawling (what the paper cites)
    - Forward citation crawling (what cites the paper)
    - Multi-hop traversal with depth limits
    - Relevance scoring for prioritization
    - Critical date filtering
    """
    
    def __init__(self, max_depth: int = 2, max_nodes_per_level: int = 20):
        """
        Initialize citation analyzer
        
        Args:
            max_depth: Maximum hops from seed document
            max_nodes_per_level: Max documents to explore per level
        """
        self.max_depth = max_depth
        self.max_nodes_per_level = max_nodes_per_level
        self.graph: Dict[str, CitationNode] = {}
        self.visited: Set[str] = set()
    
    def load_seed_documents(self, known_citations: List[Dict]):
        """
        Load seed documents from known citations CSV
        
        Args:
            known_citations: List of known citation dicts
        """
        for citation in known_citations:
            node = CitationNode(
                id=self._get_citation_id(citation),
                title=citation.get('title', ''),
                authors=citation.get('authors', ''),
                date=citation.get('date', ''),
                document_type=self._classify_document_type(citation),
                url=citation.get('url', ''),
                abstract=citation.get('abstract', '')
            )
            self.graph[node.id] = node
    
    def crawl_backward(
        self,
        seed_id: str,
        critical_date: str,
        depth: int = 2
    ) -> List[CitationNode]:
        """
        Crawl backward citations (what the seed cites)
        
        Args:
            seed_id: Starting document ID
            critical_date: Only return documents before this date
            depth: Maximum hops backward
            
        Returns:
            List of discovered citation nodes before critical date
        """
        if seed_id not in self.graph:
            raise ValueError(f"Seed document {seed_id} not in graph")
        
        discovered = []
        queue = deque([(seed_id, 0)])  # (node_id, current_depth)
        visited = {seed_id}
        
        while queue:
            current_id, current_depth = queue.popleft()
            
            if current_depth >= depth:
                continue
            
            current_node = self.graph.get(current_id)
            if not current_node:
                continue
            
            # Fetch backward citations if not already loaded
            if not current_node.citations_backward:
                self._fetch_citations(current_node, direction='backward')
            
            # Process each backward citation
            for cited_id in current_node.citations_backward[:self.max_nodes_per_level]:
                if cited_id in visited:
                    continue
                
                visited.add(cited_id)
                
                # Fetch or create node
                if cited_id not in self.graph:
                    cited_node = self._fetch_document_metadata(cited_id)
                    if cited_node:
                        self.graph[cited_id] = cited_node
                else:
                    cited_node = self.graph[cited_id]
                
                if not cited_node:
                    continue
                
                # Check critical date
                if cited_node.date and cited_node.date <= critical_date:
                    discovered.append(cited_node)
                
                # Add to queue for next level
                queue.append((cited_id, current_depth + 1))
        
        return discovered
    
    def crawl_forward(
        self,
        seed_id: str,
        critical_date: str,
        depth: int = 2
    ) -> List[CitationNode]:
        """
        Crawl forward citations (what cites the seed)
        
        Args:
            seed_id: Starting document ID
            critical_date: Only return documents before this date
            depth: Maximum hops forward
            
        Returns:
            List of discovered citation nodes before critical date
        """
        if seed_id not in self.graph:
            raise ValueError(f"Seed document {seed_id} not in graph")
        
        discovered = []
        queue = deque([(seed_id, 0)])
        visited = {seed_id}
        
        while queue:
            current_id, current_depth = queue.popleft()
            
            if current_depth >= depth:
                continue
            
            current_node = self.graph.get(current_id)
            if not current_node:
                continue
            
            # Fetch forward citations if not already loaded
            if not current_node.citations_forward:
                self._fetch_citations(current_node, direction='forward')
            
            # Process each forward citation
            for citing_id in current_node.citations_forward[:self.max_nodes_per_level]:
                if citing_id in visited:
                    continue
                
                visited.add(citing_id)
                
                # Fetch or create node
                if citing_id not in self.graph:
                    citing_node = self._fetch_document_metadata(citing_id)
                    if citing_node:
                        self.graph[citing_id] = citing_node
                else:
                    citing_node = self.graph[citing_id]
                
                if not citing_node:
                    continue
                
                # Check critical date
                if citing_node.date and citing_node.date <= critical_date:
                    discovered.append(citing_node)
                
                # Add to queue for next level
                queue.append((citing_id, current_depth + 1))
        
        return discovered
    
    def find_citation_paths(
        self,
        from_id: str,
        to_id: str,
        max_path_length: int = 3
    ) -> List[CitationPath]:
        """
        Find citation paths between two documents
        
        Args:
            from_id: Starting document ID
            to_id: Target document ID
            max_path_length: Maximum path length
            
        Returns:
            List of CitationPath objects
        """
        paths = []
        
        # BFS to find all paths
        queue = deque([([from_id], 'start')])
        
        while queue:
            path, direction = queue.popleft()
            current_id = path[-1]
            
            if len(path) > max_path_length:
                continue
            
            if current_id == to_id:
                # Found a path
                nodes = [self.graph[node_id] for node_id in path if node_id in self.graph]
                if nodes:
                    citation_path = CitationPath(
                        nodes=nodes,
                        path_type=direction,
                        relevance_score=self._score_path(nodes),
                        reasoning=self._explain_path(nodes)
                    )
                    paths.append(citation_path)
                continue
            
            current_node = self.graph.get(current_id)
            if not current_node:
                continue
            
            # Explore backward citations
            if not current_node.citations_backward:
                self._fetch_citations(current_node, 'backward')
            
            for cited_id in current_node.citations_backward:
                if cited_id not in path:  # Avoid cycles
                    new_path = path + [cited_id]
                    new_direction = 'backward' if direction == 'start' else direction
                    queue.append((new_path, new_direction))
            
            # Explore forward citations
            if not current_node.citations_forward:
                self._fetch_citations(current_node, 'forward')
            
            for citing_id in current_node.citations_forward:
                if citing_id not in path:
                    new_path = path + [citing_id]
                    new_direction = 'forward' if direction == 'start' else 'mixed'
                    queue.append((new_path, new_direction))
        
        # Sort by relevance
        paths.sort(key=lambda p: p.relevance_score, reverse=True)
        return paths
    
    def get_highly_cited_neighbors(
        self,
        seed_id: str,
        critical_date: str,
        min_citations: int = 10
    ) -> List[CitationNode]:
        """
        Find highly-cited documents near seed in citation graph
        
        Args:
            seed_id: Starting document ID
            critical_date: Only return documents before this date
            min_citations: Minimum citation count
            
        Returns:
            List of highly-cited nodes
        """
        # Crawl 1-hop in both directions
        backward = self.crawl_backward(seed_id, critical_date, depth=1)
        forward = self.crawl_forward(seed_id, critical_date, depth=1)
        
        neighbors = backward + forward
        
        # Filter by citation count
        highly_cited = []
        for node in neighbors:
            if not node.citations_forward:
                self._fetch_citations(node, 'forward')
            
            if len(node.citations_forward) >= min_citations:
                highly_cited.append(node)
        
        # Sort by citation count
        highly_cited.sort(key=lambda n: len(n.citations_forward), reverse=True)
        return highly_cited
    
    def _fetch_citations(self, node: CitationNode, direction: str):
        """
        Fetch citations for a node (backward or forward)
        
        Args:
            node: CitationNode to fetch citations for
            direction: "backward" or "forward"
        """
        # This would integrate with external APIs:
        # - Google Scholar API
        # - Semantic Scholar API
        # - CrossRef API
        # - USPTO Patent API
        # - OpenCitations API
        
        # For now, stub implementation
        # In production, this would make API calls
        
        if direction == 'backward':
            # Fetch what this document cites
            node.citations_backward = self._api_fetch_backward(node.id)
        else:
            # Fetch what cites this document
            node.citations_forward = self._api_fetch_forward(node.id)
    
    def _fetch_document_metadata(self, doc_id: str) -> Optional[CitationNode]:
        """
        Fetch metadata for a document by ID
        
        Args:
            doc_id: Document identifier (DOI, patent number, etc.)
            
        Returns:
            CitationNode or None if not found
        """
        # This would integrate with external APIs
        # For now, stub implementation
        
        metadata = self._api_fetch_metadata(doc_id)
        if not metadata:
            return None
        
        return CitationNode(
            id=doc_id,
            title=metadata.get('title', ''),
            authors=metadata.get('authors', ''),
            date=metadata.get('date', ''),
            document_type=metadata.get('type', 'article'),
            url=metadata.get('url', ''),
            abstract=metadata.get('abstract', '')
        )
    
    def _api_fetch_backward(self, doc_id: str) -> List[str]:
        """Stub for API call to fetch backward citations"""
        # TODO: Implement actual API integration
        # - Semantic Scholar: https://api.semanticscholar.org/
        # - CrossRef: https://api.crossref.org/
        # - OpenCitations: https://opencitations.net/
        return []
    
    def _api_fetch_forward(self, doc_id: str) -> List[str]:
        """Stub for API call to fetch forward citations"""
        # TODO: Implement actual API integration
        return []
    
    def _api_fetch_metadata(self, doc_id: str) -> Optional[Dict]:
        """Stub for API call to fetch document metadata"""
        # TODO: Implement actual API integration
        return None
    
    def _get_citation_id(self, citation: Dict) -> str:
        """Generate unique ID for citation"""
        if citation.get('doi'):
            return f"doi:{citation['doi']}"
        elif citation.get('patent_number'):
            return f"patent:{citation['patent_number']}"
        elif citation.get('title'):
            # Use normalized title as fallback
            title_norm = re.sub(r'\W+', '_', citation['title'].lower())[:50]
            return f"title:{title_norm}"
        else:
            return f"unknown:{hash(str(citation))}"
    
    def _classify_document_type(self, citation: Dict) -> str:
        """Classify document type from citation"""
        if citation.get('patent_number'):
            return 'patent'
        elif citation.get('journal'):
            return 'article'
        elif 'thesis' in citation.get('title', '').lower():
            return 'thesis'
        elif citation.get('conference'):
            return 'conference'
        return 'article'
    
    def _score_path(self, nodes: List[CitationNode]) -> float:
        """Score relevance of citation path"""
        if not nodes:
            return 0.0
        
        # Shorter paths are better
        length_score = 1.0 / len(nodes)
        
        # Paths through highly-cited papers are better
        citation_score = sum(len(n.citations_forward) for n in nodes) / len(nodes)
        citation_score = min(1.0, citation_score / 100.0)  # Normalize
        
        # Recent papers are better (within reason)
        dates = [n.date for n in nodes if n.date]
        if dates:
            avg_year = sum(int(d[:4]) for d in dates) / len(dates)
            recency_score = min(1.0, (avg_year - 1990) / 30.0)
        else:
            recency_score = 0.5
        
        # Weighted combination
        return 0.4 * length_score + 0.4 * citation_score + 0.2 * recency_score
    
    def _explain_path(self, nodes: List[CitationNode]) -> str:
        """Generate explanation for citation path"""
        if not nodes:
            return "Empty path"
        
        if len(nodes) == 1:
            return f"Direct reference: {nodes[0].title}"
        
        path_desc = " → ".join(n.title[:50] for n in nodes)
        return f"Citation path ({len(nodes)} hops): {path_desc}"


# Example usage
if __name__ == "__main__":
    analyzer = CitationAnalyzer(max_depth=2, max_nodes_per_level=20)
    
    # Load known citations
    known_citations = [
        {
            'title': 'Remote Memory Access over Ethernet',
            'authors': 'Smith J',
            'doi': '10.1234/example1',
            'date': '2004-01-15'
        }
    ]
    
    analyzer.load_seed_documents(known_citations)
    
    # Crawl backward citations
    seed_id = 'doi:10.1234/example1'
    critical_date = '2005-01-18'
    
    backward_citations = analyzer.crawl_backward(seed_id, critical_date, depth=2)
    
    print(f"Found {len(backward_citations)} backward citations before {critical_date}")
    for node in backward_citations[:5]:
        print(f"  - {node.title} ({node.date})")
