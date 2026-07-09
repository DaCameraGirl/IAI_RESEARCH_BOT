"""
Dynamic Study Loader - No more hardcoded studies in system_prompt.md
Automatically loads active studies from folder structure
Each study gets its own search strategy based on type
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def load_search_strategies() -> Dict:
    """Load search strategies from config file"""
    strategies_path = Path(__file__).parent / "search_strategies.json"
    if strategies_path.exists():
        with open(strategies_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


class StudyLoader:
    """
    Dynamically loads study configurations from folder structure
    No hardcoding in system_prompt.md - everything loaded from files
    """
    
    def __init__(self, workspace_root: Path):
        """
        Initialize study loader
        
        Args:
            workspace_root: Root directory containing study folders
        """
        self.workspace_root = Path(workspace_root)
        self.config_dir = self.workspace_root / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        self.active_studies: Dict[str, Dict] = {}
        self._scan_studies()
    
    def _scan_studies(self):
        """Scan workspace for study folders and load their configs"""
        # Find all study folders (pattern: NNNNN_Study_Name)
        study_folders = [
            f for f in self.workspace_root.iterdir()
            if f.is_dir() and f.name[0].isdigit() and '_' in f.name
        ]
        
        for folder in study_folders:
            study_id = folder.name.split('_')[0]
            
            # Try to load or create config
            config = self._load_or_create_config(study_id, folder)
            if config:
                self.active_studies[study_id] = config
    
    def _load_or_create_config(self, study_id: str, study_folder: Path) -> Optional[Dict]:
        """Load existing config or create from folder structure"""
        config_path = self.config_dir / f"{study_id}_config.json"
        
        # Load existing config
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                config['_loaded_from'] = str(config_path)
                # Add search strategy if missing
                if 'search_strategy' not in config:
                    config['search_strategy'] = self._detect_search_strategy(config)
                return config
        
        # Create new config from folder structure
        print(f"Creating config for study {study_id}...")
        
        config = {
            'study_id': study_id,
            'study_folder': str(study_folder),
            'study_name': study_folder.name,
            'type': 'unknown',  # Will be updated from dashboard
            'critical_date': '',
            'patent_number': '',
            'requirements': [],
            'keywords': [],
            'known_citations_path': '',
            'status': 'active',
            'created': datetime.now().isoformat(),
            'search_strategy': 'invalidity_product'  # Default
        }
        
        # Try to find known citations CSV
        possible_csv_paths = [
            study_folder / "known_art" / "known_citations.csv",
            study_folder / f"{study_id}_knowncitations.csv",
            study_folder / "known_citations.csv"
        ]
        
        for csv_path in possible_csv_paths:
            if csv_path.exists():
                config['known_citations_path'] = str(csv_path)
                config['known_citations_count'] = self._count_csv_rows(csv_path)
                break
        
        # Try to parse study brief
        brief_path = study_folder / "STUDY_BRIEF.md"
        if brief_path.exists():
            brief_data = self._parse_study_brief(brief_path)
            config.update(brief_data)
        
        # Save config
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Created config: {config_path}")
        return config
    
    def _count_csv_rows(self, csv_path: Path) -> int:
        """Count rows in CSV file"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in csv.DictReader(f))
        except:
            return 0
    
    def _parse_study_brief(self, brief_path: Path) -> Dict:
        """Parse study brief for key information"""
        import re
        
        brief_text = brief_path.read_text(encoding='utf-8')
        
        data = {}
        
        # Extract critical date
        date_match = re.search(r'critical date[:\s]+(\d{4}-\d{2}-\d{2})', brief_text, re.IGNORECASE)
        if date_match:
            data['critical_date'] = date_match.group(1)
        
        # Extract patent number
        patent_match = re.search(r'patent[:\s]+(US\d+|WO\d+|EP\d+)', brief_text, re.IGNORECASE)
        if patent_match:
            data['patent_number'] = patent_match.group(1)
        
        # Extract study type
        if 'invalidity' in brief_text.lower():
            data['type'] = 'invalidity'
        elif 'copyright' in brief_text.lower():
            data['type'] = 'copyright'
        else:
            data['type'] = 'research'
        
        # Extract requirements (RR1.1, RR1.2, etc.)
        req_pattern = r'\*\*(RR\d+\.\d+)\*\*[:\s]+(.+?)(?=\*\*RR|\Z)'
        matches = re.findall(req_pattern, brief_text, re.DOTALL)
        
        requirements = []
        for req_id, req_text in matches:
            req_text = req_text.strip()
            requirements.append({
                'id': req_id,
                'text': req_text[:200],  # First 200 chars
                'priority': 1
            })
        
        data['requirements'] = requirements
        
        return data
    
    def _detect_search_strategy(self, config: Dict) -> str:
        """Detect appropriate search strategy based on study type"""
        study_type = config.get('type', '').lower()
        study_name = config.get('study_name', '').lower()
        
        # Copyright/hymn research
        if 'copyright' in study_type or 'hymn' in study_name:
            return 'copyright'
        
        # Invalidity - check if product-focused or NPL-focused
        if 'invalidity' in study_type:
            # Look for product indicators in name/requirements
            product_indicators = ['device', 'product', 'blender', 'chip', 'wafer', 'package']
            npl_indicators = ['compound', 'method', 'process', 'synthesis']
            
            has_product = any(ind in study_name for ind in product_indicators)
            has_npl = any(ind in study_name for ind in npl_indicators)
            
            if has_product and not has_npl:
                return 'invalidity_product'
            elif has_npl and not has_product:
                return 'invalidity_npl'
            else:
                # Default to product for invalidity
                return 'invalidity_product'
        
        # Default
        return 'invalidity_product'
    
    def get_search_strategy(self, study_id: str) -> Dict:
        """Get search strategy configuration for a study"""
        study = self.get_study(study_id)
        if not study:
            return {}
        
        strategy_name = study.get('search_strategy', 'invalidity_product')
        strategies = load_search_strategies()
        
        return strategies.get(strategy_name, {})
    
    def get_study(self, study_id: str) -> Optional[Dict]:
        """Get study configuration by ID"""
        return self.active_studies.get(study_id)
    
    def get_active_studies(self) -> List[Dict]:
        """Get all active studies"""
        return list(self.active_studies.values())
    
    def get_study_summary(self, study_id: str) -> str:
        """Get human-readable study summary"""
        study = self.get_study(study_id)
        if not study:
            return f"Study {study_id} not found"
        
        lines = [
            f"Study {study_id}: {study['study_name']}",
            f"Type: {study['type']}",
            f"Critical Date: {study.get('critical_date', 'Not set')}",
            f"Patent: {study.get('patent_number', 'Not set')}",
            f"Requirements: {len(study.get('requirements', []))}",
            f"Known Citations: {study.get('known_citations_count', 0)}"
        ]
        
        return "\n".join(lines)
    
    def update_study_from_dashboard(self, dashboard_path: Path):
        """Update study configs from _DASHBOARD.md"""
        import re
        
        if not dashboard_path.exists():
            return
        
        dashboard_text = dashboard_path.read_text(encoding='utf-8')
        
        # Parse active studies from dashboard
        # Pattern: ## ACTIVE — NNNNN Study Name
        active_pattern = r'## ACTIVE — (\d+)\s+(.+?)$'
        
        for match in re.finditer(active_pattern, dashboard_text, re.MULTILINE):
            study_id = match.group(1)
            study_name = match.group(2).strip()
            
            if study_id in self.active_studies:
                # Extract study block
                study_block_pattern = rf'## ACTIVE — {study_id}.+?(?=##|\Z)'
                study_block = re.search(study_block_pattern, dashboard_text, re.DOTALL)
                
                if study_block:
                    block_text = study_block.group(0)
                    
                    # Update config with dashboard info
                    config = self.active_studies[study_id]
                    
                    # Extract critical date
                    date_match = re.search(r'Critical date[:\s]+(\d{4}-\d{2}-\d{2})', block_text)
                    if date_match:
                        config['critical_date'] = date_match.group(1)
                    
                    # Extract deadline
                    deadline_match = re.search(r'Expiration[:\s]+(\d{4}-\d{2}-\d{2})', block_text)
                    if deadline_match:
                        config['deadline'] = deadline_match.group(1)
                    
                    # Extract type
                    type_match = re.search(r'Type[:\s]+(\w+)', block_text)
                    if type_match:
                        config['type'] = type_match.group(1).lower()
                    
                    # Save updated config
                    config_path = self.config_dir / f"{study_id}_config.json"
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2)
    
    def refresh(self):
        """Refresh study list from workspace"""
        self.active_studies.clear()
        self._scan_studies()


# Example usage
if __name__ == "__main__":
    loader = StudyLoader(Path("."))
    
    print("Active Studies:")
    print("=" * 60)
    
    for study in loader.get_active_studies():
        print(f"\n{loader.get_study_summary(study['study_id'])}")
        
        # Show search strategy
        strategy = loader.get_search_strategy(study['study_id'])
        if strategy:
            print(f"Search Strategy: {strategy.get('name', 'Unknown')}")
            enabled_sources = [
                name for name, config in strategy.get('sources', {}).items()
                if config.get('enabled', False)
            ]
            print(f"Enabled Sources: {', '.join(enabled_sources)}")
        
        print("-" * 60)
    
    # Update from dashboard
    dashboard_path = Path("_DASHBOARD.md")
    if dashboard_path.exists():
        loader.update_study_from_dashboard(dashboard_path)
        print("\n✓ Updated from _DASHBOARD.md")
    
    # Example: Get strategy for specific study
    print("\n" + "=" * 60)
    print("Example: Study 26052 Search Strategy")
    print("=" * 60)
    strategy = loader.get_search_strategy("26052")
    if strategy:
        print(f"Name: {strategy.get('name')}")
        print(f"Description: {strategy.get('description')}")
        print("\nSources:")
        for source_name, source_config in strategy.get('sources', {}).items():
            if source_config.get('enabled'):
                priority = source_config.get('priority', 3)
                print(f"  [{priority}] {source_name}: {source_config.get('strategy', 'N/A')}")
