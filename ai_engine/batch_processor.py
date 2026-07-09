"""
Batch Processor - Hunt multiple studies at once
Parallel execution with progress tracking and error handling
"""

from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json

from .hunt_orchestrator import HuntOrchestrator, HuntConfig
from .dashboard_updater import DashboardUpdater
from .email_notifier import EmailNotifier


class BatchProcessor:
    """
    Process multiple studies in parallel
    Features:
    - Parallel hunt execution
    - Progress tracking
    - Error handling and retry
    - Dashboard updates
    - Email notifications
    - Summary report
    """
    
    def __init__(
        self,
        workspace_root: Path,
        max_workers: int = 3,
        enable_notifications: bool = True
    ):
        """
        Initialize batch processor
        
        Args:
            workspace_root: Root directory of workspace
            max_workers: Maximum parallel hunts (default: 3)
            enable_notifications: Enable email notifications
        """
        self.workspace_root = Path(workspace_root)
        self.max_workers = max_workers
        self.enable_notifications = enable_notifications
        
        # Initialize components
        self.dashboard_updater = DashboardUpdater(workspace_root)
        self.email_notifier = EmailNotifier() if enable_notifications else None
        
        # Batch statistics
        self.batch_stats = {
            'total_studies': 0,
            'completed': 0,
            'failed': 0,
            'total_ready_submit': 0,
            'total_hold': 0,
            'start_time': None,
            'end_time': None
        }
    
    def hunt_all_active_studies(self, study_loader) -> Dict:
        """
        Hunt all active studies in parallel
        
        Args:
            study_loader: StudyLoader instance
            
        Returns:
            Batch report dict
        """
        active_studies = study_loader.get_active_studies()
        
        if not active_studies:
            print("No active studies found")
            return {'studies': [], 'statistics': self.batch_stats}
        
        print(f"\n{'='*60}")
        print(f"Batch Hunt: {len(active_studies)} active studies")
        print(f"Max parallel: {self.max_workers}")
        print(f"{'='*60}\n")
        
        # Hunt each study
        study_ids = [study['study_id'] for study in active_studies]
        return self.hunt_studies(study_ids, study_loader)
    
    def hunt_studies(
        self,
        study_ids: List[str],
        study_loader,
        retry_failed: bool = True
    ) -> Dict:
        """
        Hunt specific studies in parallel
        
        Args:
            study_ids: List of study IDs to hunt
            study_loader: StudyLoader instance
            retry_failed: Retry failed hunts once
            
        Returns:
            Batch report dict
        """
        self.batch_stats['total_studies'] = len(study_ids)
        self.batch_stats['start_time'] = datetime.now().isoformat()
        
        results = []
        failed_studies = []
        
        # Execute hunts in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all hunts
            future_to_study = {
                executor.submit(self._hunt_single_study, study_id, study_loader): study_id
                for study_id in study_ids
            }
            
            # Process as they complete
            for future in as_completed(future_to_study):
                study_id = future_to_study[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['status'] == 'success':
                        self.batch_stats['completed'] += 1
                        self.batch_stats['total_ready_submit'] += result['statistics']['ready_submit']
                        self.batch_stats['total_hold'] += result['statistics']['hold']
                        
                        print(f"✓ {study_id}: {result['statistics']['ready_submit']} READY_SUBMIT, {result['statistics']['hold']} HOLD")
                    else:
                        self.batch_stats['failed'] += 1
                        failed_studies.append(study_id)
                        print(f"✗ {study_id}: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    self.batch_stats['failed'] += 1
                    failed_studies.append(study_id)
                    print(f"✗ {study_id}: {str(e)}")
                    
                    results.append({
                        'study_id': study_id,
                        'status': 'error',
                        'error': str(e)
                    })
        
        # Retry failed studies once
        if retry_failed and failed_studies:
            print(f"\nRetrying {len(failed_studies)} failed studies...")
            
            for study_id in failed_studies:
                try:
                    result = self._hunt_single_study(study_id, study_loader)
                    
                    # Update results
                    for i, r in enumerate(results):
                        if r['study_id'] == study_id:
                            results[i] = result
                            break
                    
                    if result['status'] == 'success':
                        self.batch_stats['completed'] += 1
                        self.batch_stats['failed'] -= 1
                        self.batch_stats['total_ready_submit'] += result['statistics']['ready_submit']
                        self.batch_stats['total_hold'] += result['statistics']['hold']
                        print(f"✓ {study_id}: Retry successful")
                    else:
                        print(f"✗ {study_id}: Retry failed")
                
                except Exception as e:
                    print(f"✗ {study_id}: Retry error: {e}")
        
        self.batch_stats['end_time'] = datetime.now().isoformat()
        
        # Generate batch report
        batch_report = {
            'studies': results,
            'statistics': self.batch_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save batch report
        self._save_batch_report(batch_report)
        
        # Print summary
        self._print_summary(batch_report)
        
        return batch_report
    
    def _hunt_single_study(self, study_id: str, study_loader) -> Dict:
        """
        Hunt a single study
        
        Args:
            study_id: Study ID
            study_loader: StudyLoader instance
            
        Returns:
            Hunt result dict
        """
        try:
            # Load study
            study = study_loader.get_study(study_id)
            
            if not study:
                return {
                    'study_id': study_id,
                    'status': 'error',
                    'error': 'Study not found'
                }
            
            # Load search strategy
            strategy = study_loader.get_search_strategy(study_id)
            
            # Configure hunt
            hunt_config = HuntConfig(
                study_id=study['study_id'],
                study_folder=Path(study['study_folder']),
                critical_date=study.get('critical_date', ''),
                keywords=study.get('keywords', []),
                part_numbers=study.get('part_numbers', []),
                manufacturers=study.get('manufacturers', []),
                target_domains=study.get('target_domains', []),
                patent_number=study.get('patent_number'),
                
                # Apply strategy
                enable_wayback=strategy['sources'].get('wayback', {}).get('enabled', False),
                enable_fcc=strategy['sources'].get('fcc', {}).get('enabled', False),
                enable_ptab=strategy['sources'].get('ptab', {}).get('enabled', False),
                enable_usenet=strategy['sources'].get('usenet', {}).get('enabled', False),
                enable_university=strategy['sources'].get('university', {}).get('enabled', False),
                enable_distributor=strategy['sources'].get('distributor', {}).get('enabled', False),
                enable_archive_texts=strategy['sources'].get('archive_texts', {}).get('enabled', False),
                enable_github=strategy['sources'].get('github', {}).get('enabled', False),
                enable_forums=strategy['sources'].get('forums', {}).get('enabled', False),
                
                # Rate limiting
                max_results_per_source=10
            )
            
            # Execute hunt
            orchestrator = HuntOrchestrator(hunt_config)
            report = orchestrator.execute_hunt()
            
            # Update dashboard
            self.dashboard_updater.update_after_hunt(report)
            
            # Send email notification
            if self.email_notifier:
                self.email_notifier.notify_hunt_complete(report)
            
            return {
                'study_id': study_id,
                'status': 'success',
                'statistics': report['statistics'],
                'candidates': report['candidates']
            }
        
        except Exception as e:
            return {
                'study_id': study_id,
                'status': 'error',
                'error': str(e)
            }
    
    def _save_batch_report(self, batch_report: Dict):
        """Save batch report to file"""
        reports_dir = self.workspace_root / "batch_reports"
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = reports_dir / f"batch_hunt_{timestamp}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(batch_report, f, indent=2)
        
        print(f"\n✓ Batch report saved: {report_path}")
    
    def _print_summary(self, batch_report: Dict):
        """Print batch summary"""
        stats = batch_report['statistics']
        
        print(f"\n{'='*60}")
        print(f"Batch Hunt Summary")
        print(f"{'='*60}")
        print(f"Total studies: {stats['total_studies']}")
        print(f"Completed: {stats['completed']}")
        print(f"Failed: {stats['failed']}")
        print(f"")
        print(f"🏆 Total READY_SUBMIT: {stats['total_ready_submit']}")
        print(f"📋 Total HOLD: {stats['total_hold']}")
        print(f"")
        
        # Calculate duration
        if stats['start_time'] and stats['end_time']:
            start = datetime.fromisoformat(stats['start_time'])
            end = datetime.fromisoformat(stats['end_time'])
            duration = (end - start).total_seconds()
            print(f"Duration: {duration:.1f} seconds")
        
        print(f"{'='*60}\n")
        
        # Show top performers
        successful_studies = [
            s for s in batch_report['studies']
            if s['status'] == 'success' and s['statistics']['ready_submit'] > 0
        ]
        
        if successful_studies:
            print("Top Studies (by READY_SUBMIT count):")
            successful_studies.sort(
                key=lambda s: s['statistics']['ready_submit'],
                reverse=True
            )
            
            for study in successful_studies[:5]:
                print(f"  • {study['study_id']}: {study['statistics']['ready_submit']} READY_SUBMIT")


# Example usage
if __name__ == "__main__":
    from config.study_loader import StudyLoader
    
    # Initialize
    workspace_root = Path(".")
    loader = StudyLoader(workspace_root)
    processor = BatchProcessor(workspace_root, max_workers=3)
    
    # Hunt all active studies
    print("Starting batch hunt for all active studies...")
    batch_report = processor.hunt_all_active_studies(loader)
    
    print(f"\n✓ Batch hunt complete!")
    print(f"  Total READY_SUBMIT: {batch_report['statistics']['total_ready_submit']}")
