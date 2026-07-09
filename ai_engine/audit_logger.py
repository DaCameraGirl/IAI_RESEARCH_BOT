"""
Audit Logger - Log all hunts and decisions for compliance and review
Maintains detailed audit trail of all bot activities
"""

from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import json
import hashlib


class AuditLogger:
    """
    Log all bot activities for audit trail
    Features:
    - Hunt logging
    - Decision logging
    - User action logging
    - Compliance tracking
    - Export capabilities
    """
    
    def __init__(self, workspace_root: Path):
        """
        Initialize audit logger
        
        Args:
            workspace_root: Root directory of workspace
        """
        self.workspace_root = Path(workspace_root)
        self.log_dir = self.workspace_root / ".bob" / "audit_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session log
        self.session_id = self._generate_session_id()
        self.session_log = []
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]
    
    def log_hunt_start(
        self,
        study_id: str,
        config: Dict
    ):
        """
        Log hunt start
        
        Args:
            study_id: Study ID
            config: Hunt configuration
        """
        entry = {
            'event_type': 'hunt_start',
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'study_id': study_id,
            'config': {
                'keywords': config.get('keywords', []),
                'critical_date': config.get('critical_date'),
                'sources_enabled': self._get_enabled_sources(config)
            }
        }
        
        self.session_log.append(entry)
        self._write_log_entry(entry)
    
    def log_hunt_complete(
        self,
        study_id: str,
        statistics: Dict,
        duration_seconds: float
    ):
        """
        Log hunt completion
        
        Args:
            study_id: Study ID
            statistics: Hunt statistics
            duration_seconds: Hunt duration
        """
        entry = {
            'event_type': 'hunt_complete',
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'study_id': study_id,
            'statistics': statistics,
            'duration_seconds': duration_seconds
        }
        
        self.session_log.append(entry)
        self._write_log_entry(entry)
    
    def log_candidate_generated(
        self,
        study_id: str,
        candidate: Dict,
        tier: str,
        reasoning: str
    ):
        """
        Log candidate generation
        
        Args:
            study_id: Study ID
            candidate: Candidate dict
            tier: READY_SUBMIT or HOLD
            reasoning: Why this tier was assigned
        """
        entry = {
            'event_type': 'candidate_generated',
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'study_id': study_id,
            'candidate': {
                'title': candidate.get('title'),
                'source': candidate.get('source'),
                'date': candidate.get('date'),
                'url': candidate.get('url')
            },
            'tier': tier,
            'reasoning': reasoning
        }
        
        self.session_log.append(entry)
        self._write_log_entry(entry)
    
    def log_duplicate_detected(
        self,
        study_id: str,
        candidate: Dict,
        duplicate_info: Dict
    ):
        """
        Log duplicate detection
        
        Args:
            study_id: Study ID
            candidate: Candidate that was duplicate
            duplicate_info: Information about the duplicate
        """
        entry = {
            'event_type': 'duplicate_detected',
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'study_id': study_id,
            'candidate': {
                'title': candidate.get('title'),
                'url': candidate.get('url')
            },
            'duplicate_type': duplicate_info.get('duplicate_type'),
            'original_study': duplicate_info.get('duplicates', [{}])[0].get('study_id')
        }
        
        self.session_log.append(entry)
        self._write_log_entry(entry)
    
    def log_submission(
        self,
        study_id: str,
        candidate: Dict,
        submission_file: str
    ):
        """
        Log candidate submission
        
        Args:
            study_id: Study ID
            candidate: Submitted candidate
            submission_file: Path to submission file
        """
        entry = {
            'event_type': 'submission',
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'study_id': study_id,
            'candidate': {
                'title': candidate.get('title'),
                'source': candidate.get('source'),
                'date': candidate.get('date')
            },
            'submission_file': submission_file
        }
        
        self.session_log.append(entry)
        self._write_log_entry(entry)
    
    def log_error(
        self,
        study_id: str,
        error_type: str,
        error_message: str,
        context: Dict = None
    ):
        """
        Log error
        
        Args:
            study_id: Study ID
            error_type: Type of error
            error_message: Error message
            context: Additional context
        """
        entry = {
            'event_type': 'error',
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'study_id': study_id,
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {}
        }
        
        self.session_log.append(entry)
        self._write_log_entry(entry)
    
    def log_user_action(
        self,
        action: str,
        details: Dict
    ):
        """
        Log user action
        
        Args:
            action: Action type
            details: Action details
        """
        entry = {
            'event_type': 'user_action',
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'action': action,
            'details': details
        }
        
        self.session_log.append(entry)
        self._write_log_entry(entry)
    
    def _write_log_entry(self, entry: Dict):
        """Write log entry to file"""
        # Daily log file
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file = self.log_dir / f"audit_{date_str}.jsonl"
        
        # Append to log file (JSONL format)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    
    def _get_enabled_sources(self, config: Dict) -> List[str]:
        """Get list of enabled sources from config"""
        sources = []
        
        source_flags = [
            'enable_wayback', 'enable_fcc', 'enable_ptab',
            'enable_usenet', 'enable_university', 'enable_distributor',
            'enable_archive_texts', 'enable_github', 'enable_forums'
        ]
        
        for flag in source_flags:
            if config.get(flag):
                source_name = flag.replace('enable_', '')
                sources.append(source_name)
        
        return sources
    
    def get_session_summary(self) -> Dict:
        """Get summary of current session"""
        if not self.session_log:
            return {'session_id': self.session_id, 'events': 0}
        
        # Count events by type
        event_counts = {}
        for entry in self.session_log:
            event_type = entry['event_type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Get studies involved
        studies = set()
        for entry in self.session_log:
            if 'study_id' in entry:
                studies.add(entry['study_id'])
        
        return {
            'session_id': self.session_id,
            'total_events': len(self.session_log),
            'event_counts': event_counts,
            'studies': list(studies),
            'start_time': self.session_log[0]['timestamp'],
            'end_time': self.session_log[-1]['timestamp']
        }
    
    def export_logs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        study_id: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Export logs to JSON file
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            study_id: Filter by study ID
            output_path: Output file path
            
        Returns:
            Path to exported file
        """
        # Collect logs
        logs = []
        
        # Read all log files
        for log_file in sorted(self.log_dir.glob("audit_*.jsonl")):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        
                        # Apply filters
                        if start_date and entry['timestamp'] < start_date:
                            continue
                        if end_date and entry['timestamp'] > end_date:
                            continue
                        if study_id and entry.get('study_id') != study_id:
                            continue
                        
                        logs.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        # Generate output path
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.log_dir / f"export_{timestamp}.json"
        
        # Write export
        export_data = {
            'export_date': datetime.now().isoformat(),
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'study_id': study_id
            },
            'total_entries': len(logs),
            'logs': logs
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✓ Exported {len(logs)} log entries to: {output_path}")
        
        return output_path
    
    def generate_compliance_report(
        self,
        study_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Generate compliance report for a study
        
        Args:
            study_id: Study ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Compliance report dict
        """
        # Collect relevant logs
        logs = []
        
        for log_file in sorted(self.log_dir.glob("audit_*.jsonl")):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        
                        if entry.get('study_id') != study_id:
                            continue
                        
                        if start_date and entry['timestamp'] < start_date:
                            continue
                        if end_date and entry['timestamp'] > end_date:
                            continue
                        
                        logs.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        # Analyze logs
        hunts = [e for e in logs if e['event_type'] == 'hunt_complete']
        candidates = [e for e in logs if e['event_type'] == 'candidate_generated']
        submissions = [e for e in logs if e['event_type'] == 'submission']
        duplicates = [e for e in logs if e['event_type'] == 'duplicate_detected']
        errors = [e for e in logs if e['event_type'] == 'error']
        
        return {
            'study_id': study_id,
            'report_date': datetime.now().isoformat(),
            'date_range': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_hunts': len(hunts),
                'total_candidates': len(candidates),
                'total_submissions': len(submissions),
                'duplicates_prevented': len(duplicates),
                'errors': len(errors)
            },
            'hunt_history': [
                {
                    'timestamp': h['timestamp'],
                    'duration': h.get('duration_seconds'),
                    'results': h.get('statistics', {}).get('total_found', 0)
                }
                for h in hunts
            ],
            'submission_history': [
                {
                    'timestamp': s['timestamp'],
                    'candidate_title': s['candidate']['title'],
                    'submission_file': s['submission_file']
                }
                for s in submissions
            ]
        }


# Example usage
if __name__ == "__main__":
    logger = AuditLogger(Path("."))
    
    # Log hunt start
    logger.log_hunt_start(
        study_id='26052',
        config={
            'keywords': ['blender', 'offset', 'blade'],
            'critical_date': '2019-10-28',
            'enable_wayback': True,
            'enable_fcc': True
        }
    )
    
    # Log candidate
    logger.log_candidate_generated(
        study_id='26052',
        candidate={
            'title': 'Blender Datasheet 2018',
            'source': 'wayback',
            'date': '2018-03-15',
            'url': 'https://example.com/datasheet.pdf'
        },
        tier='READY_SUBMIT',
        reasoning='High confidence, before critical date, credible source'
    )
    
    # Log hunt complete
    logger.log_hunt_complete(
        study_id='26052',
        statistics={
            'total_found': 25,
            'ready_submit': 3,
            'hold': 9
        },
        duration_seconds=45.2
    )
    
    # Get session summary
    summary = logger.get_session_summary()
    print(f"\nSession Summary:")
    print(f"  Events: {summary['total_events']}")
    print(f"  Studies: {', '.join(summary['studies'])}")
    
    # Generate compliance report
    report = logger.generate_compliance_report('26052')
    print(f"\nCompliance Report:")
    print(f"  Total hunts: {report['summary']['total_hunts']}")
    print(f"  Total candidates: {report['summary']['total_candidates']}")
