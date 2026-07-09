"""
Dashboard Auto-Updater - Updates _DASHBOARD.md after each hunt
Tracks hunt results, candidate counts, and study progress
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List
import re


class DashboardUpdater:
    """
    Automatically updates _DASHBOARD.md with hunt results
    Tracks:
    - Hunt completion dates
    - Candidate counts (READY_SUBMIT vs HOLD)
    - Success rates
    - Next actions
    """
    
    def __init__(self, workspace_root: Path):
        """
        Initialize dashboard updater
        
        Args:
            workspace_root: Root directory of workspace
        """
        self.workspace_root = Path(workspace_root)
        self.dashboard_path = self.workspace_root / "_DASHBOARD.md"
    
    def update_after_hunt(self, hunt_report: Dict):
        """
        Update dashboard after hunt completion
        
        Args:
            hunt_report: Hunt report dict from HuntOrchestrator
        """
        if not self.dashboard_path.exists():
            print(f"⚠ Dashboard not found: {self.dashboard_path}")
            return
        
        # Read current dashboard
        dashboard_text = self.dashboard_path.read_text(encoding='utf-8')
        
        # Find study section
        study_id = hunt_report['study_id']
        study_section = self._find_study_section(dashboard_text, study_id)
        
        if not study_section:
            print(f"⚠ Study {study_id} not found in dashboard")
            return
        
        # Update study section
        updated_section = self._update_study_section(
            study_section,
            hunt_report
        )
        
        # Replace in dashboard
        updated_dashboard = dashboard_text.replace(study_section, updated_section)
        
        # Write back
        self.dashboard_path.write_text(updated_dashboard, encoding='utf-8')
        
        print(f"✓ Updated dashboard for study {study_id}")
    
    def _find_study_section(self, dashboard_text: str, study_id: str) -> str:
        """Find study section in dashboard"""
        # Pattern: ## ACTIVE — NNNNN Study Name ... (until next ##)
        pattern = rf'(## ACTIVE — {study_id}\b.*?)(?=\n##|\Z)'
        match = re.search(pattern, dashboard_text, re.DOTALL)
        
        if match:
            return match.group(1)
        
        return ""
    
    def _update_study_section(self, section: str, hunt_report: Dict) -> str:
        """Update study section with hunt results"""
        lines = section.split('\n')
        
        # Find or add hunt results section
        hunt_results_idx = -1
        for i, line in enumerate(lines):
            if 'Last Hunt:' in line or 'Hunt Results:' in line:
                hunt_results_idx = i
                break
        
        # Build hunt results
        stats = hunt_report['statistics']
        timestamp = datetime.fromisoformat(hunt_report['timestamp'])
        
        hunt_results = [
            f"**Last Hunt:** {timestamp.strftime('%Y-%m-%d %H:%M')}",
            f"- Sources searched: {stats['sources_searched']}",
            f"- Total found: {stats['total_found']}",
            f"- Filtered (known): {stats['filtered_known']}",
            f"- Filtered (paywall): {stats['filtered_paywall']}",
            f"- **READY_SUBMIT: {stats['ready_submit']}** 🏆",
            f"- HOLD: {stats['hold']}",
            f"- Success rate: {hunt_report['summary']['success_rate']:.1%}"
        ]
        
        # Add next action
        if stats['ready_submit'] > 0:
            hunt_results.append(f"\n**Next Action:** Review {stats['ready_submit']} READY_SUBMIT candidates in `candidates/` folder")
        elif stats['hold'] > 0:
            hunt_results.append(f"\n**Next Action:** Review {stats['hold']} HOLD candidates for potential submission")
        else:
            hunt_results.append("\n**Next Action:** Try different search strategy or expand keywords")
        
        # Insert or replace hunt results
        if hunt_results_idx >= 0:
            # Replace existing hunt results (find end of section)
            end_idx = hunt_results_idx + 1
            while end_idx < len(lines) and lines[end_idx].startswith(('- ', '**Next Action')):
                end_idx += 1
            
            # Replace
            lines[hunt_results_idx:end_idx] = hunt_results
        else:
            # Add after header (line 0 is "## ACTIVE — ...")
            lines.insert(1, '\n' + '\n'.join(hunt_results))
        
        return '\n'.join(lines)
    
    def add_candidate_to_dashboard(
        self,
        study_id: str,
        candidate_title: str,
        candidate_tier: str,
        candidate_file: str
    ):
        """
        Add candidate to dashboard's candidate list
        
        Args:
            study_id: Study ID
            candidate_title: Candidate title
            candidate_tier: READY_SUBMIT or HOLD
            candidate_file: Filename in candidates/ folder
        """
        if not self.dashboard_path.exists():
            return
        
        dashboard_text = self.dashboard_path.read_text(encoding='utf-8')
        study_section = self._find_study_section(dashboard_text, study_id)
        
        if not study_section:
            return
        
        # Find or create candidates section
        lines = study_section.split('\n')
        
        candidates_idx = -1
        for i, line in enumerate(lines):
            if 'Candidates:' in line or 'Found Candidates:' in line:
                candidates_idx = i
                break
        
        # Build candidate entry
        icon = "🏆" if candidate_tier == "READY_SUBMIT" else "📋"
        candidate_entry = f"- {icon} [{candidate_tier}] {candidate_title} (`{candidate_file}`)"
        
        if candidates_idx >= 0:
            # Add after candidates header
            lines.insert(candidates_idx + 1, candidate_entry)
        else:
            # Add new candidates section
            lines.append("\n**Found Candidates:**")
            lines.append(candidate_entry)
        
        # Update dashboard
        updated_section = '\n'.join(lines)
        updated_dashboard = dashboard_text.replace(study_section, updated_section)
        self.dashboard_path.write_text(updated_dashboard, encoding='utf-8')


# Example usage
if __name__ == "__main__":
    updater = DashboardUpdater(Path("."))
    
    # Example hunt report
    hunt_report = {
        'study_id': '26052',
        'timestamp': datetime.now().isoformat(),
        'statistics': {
            'sources_searched': 6,
            'total_found': 25,
            'filtered_known': 8,
            'filtered_paywall': 5,
            'candidates_generated': 12,
            'ready_submit': 3,
            'hold': 9
        },
        'summary': {
            'success_rate': 0.12
        }
    }
    
    updater.update_after_hunt(hunt_report)
    print("✓ Dashboard updated")
