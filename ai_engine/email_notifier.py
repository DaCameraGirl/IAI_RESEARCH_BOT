"""
Email Notifier - Send notifications when READY_SUBMIT candidates are found
Supports SMTP, Gmail, Outlook, and custom email providers
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json


class EmailNotifier:
    """
    Send email notifications for hunt results
    Configurable via config/email_config.json
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize email notifier
        
        Args:
            config_path: Path to email config file (default: config/email_config.json)
        """
        if config_path is None:
            config_path = Path("config/email_config.json")
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.enabled = self.config.get('enabled', False)
    
    def _load_config(self) -> Dict:
        """Load email configuration"""
        if not self.config_path.exists():
            # Create default config
            default_config = {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True,
                'sender_email': 'your-email@gmail.com',
                'sender_password': 'your-app-password',
                'recipient_email': 'your-email@gmail.com',
                'notify_on_ready_submit': True,
                'notify_on_hold': False,
                'min_candidates_to_notify': 1,
                'subject_template': '[RWS Bot] {count} READY_SUBMIT candidates found for study {study_id}',
                'include_candidate_details': True
            }
            
            # Create config directory if needed
            self.config_path.parent.mkdir(exist_ok=True)
            
            # Write default config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            print(f"✓ Created default email config: {self.config_path}")
            print(f"  Edit this file to enable email notifications")
            
            return default_config
        
        # Load existing config
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def notify_hunt_complete(self, hunt_report: Dict):
        """
        Send notification after hunt completion
        
        Args:
            hunt_report: Hunt report dict from HuntOrchestrator
        """
        if not self.enabled:
            return
        
        stats = hunt_report['statistics']
        study_id = hunt_report['study_id']
        
        # Check if we should notify
        ready_submit_count = stats.get('ready_submit', 0)
        hold_count = stats.get('hold', 0)
        
        should_notify = False
        
        if self.config.get('notify_on_ready_submit', True) and ready_submit_count >= self.config.get('min_candidates_to_notify', 1):
            should_notify = True
        
        if self.config.get('notify_on_hold', False) and hold_count > 0:
            should_notify = True
        
        if not should_notify:
            return
        
        # Build email
        subject = self.config.get('subject_template', '').format(
            count=ready_submit_count,
            study_id=study_id
        )
        
        body = self._build_email_body(hunt_report)
        
        # Send email
        try:
            self._send_email(subject, body)
            print(f"✓ Email notification sent for study {study_id}")
        except Exception as e:
            print(f"✗ Failed to send email: {e}")
    
    def _build_email_body(self, hunt_report: Dict) -> str:
        """Build email body from hunt report"""
        stats = hunt_report['statistics']
        study_id = hunt_report['study_id']
        timestamp = datetime.fromisoformat(hunt_report['timestamp'])
        
        lines = [
            f"Hunt completed for study {study_id}",
            f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Results:",
            f"  • Sources searched: {stats['sources_searched']}",
            f"  • Total found: {stats['total_found']}",
            f"  • Filtered (known): {stats['filtered_known']}",
            f"  • Filtered (paywall): {stats['filtered_paywall']}",
            "",
            f"  🏆 READY_SUBMIT: {stats['ready_submit']}",
            f"  📋 HOLD: {stats['hold']}",
            "",
            f"Success rate: {hunt_report['summary']['success_rate']:.1%}",
            ""
        ]
        
        # Add candidate details if enabled
        if self.config.get('include_candidate_details', True):
            ready_candidates = [
                c for c in hunt_report.get('candidates', [])
                if c['tier'] == 'READY_SUBMIT'
            ]
            
            if ready_candidates:
                lines.append("READY_SUBMIT Candidates:")
                lines.append("")
                
                for i, candidate in enumerate(ready_candidates, 1):
                    lines.append(f"{i}. {candidate['title']}")
                    lines.append(f"   Source: {candidate['source']}")
                    lines.append(f"   Date: {candidate['date']}")
                    lines.append(f"   Rank: {candidate['rank']} (confidence: {candidate['confidence']:.2f})")
                    lines.append(f"   File: {candidate['filename']}")
                    lines.append("")
        
        # Add next action
        if stats['ready_submit'] > 0:
            lines.append("Next Action:")
            lines.append(f"Review {stats['ready_submit']} READY_SUBMIT candidates in the candidates/ folder")
            lines.append("Copy and paste into RWS portal for submission")
        
        return '\n'.join(lines)
    
    def _send_email(self, subject: str, body: str):
        """Send email via SMTP"""
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.config['sender_email']
        msg['To'] = self.config['recipient_email']
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server
        smtp_server = self.config['smtp_server']
        smtp_port = self.config['smtp_port']
        use_tls = self.config.get('use_tls', True)
        
        if use_tls:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        
        # Login
        server.login(
            self.config['sender_email'],
            self.config['sender_password']
        )
        
        # Send email
        server.send_message(msg)
        server.quit()
    
    def test_email(self):
        """Send test email to verify configuration"""
        if not self.enabled:
            print("Email notifications are disabled in config")
            return False
        
        subject = "[RWS Bot] Test Email"
        body = f"This is a test email from RWS Research Bot.\n\nSent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            self._send_email(subject, body)
            print("✓ Test email sent successfully!")
            return True
        except Exception as e:
            print(f"✗ Failed to send test email: {e}")
            print("\nTroubleshooting:")
            print("1. Check SMTP server and port")
            print("2. Verify email and password")
            print("3. For Gmail: Use App Password (not regular password)")
            print("4. Check firewall/antivirus settings")
            return False


# Example usage
if __name__ == "__main__":
    notifier = EmailNotifier()
    
    # Test email configuration
    print("Testing email configuration...")
    notifier.test_email()
    
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
        },
        'candidates': [
            {
                'title': 'Blender Datasheet 2018',
                'source': 'wayback',
                'date': '2018-03-15',
                'tier': 'READY_SUBMIT',
                'rank': 3,
                'confidence': 0.87,
                'filename': 'READY_SUBMIT_Blender_Datasheet_2018.txt'
            }
        ]
    }
    
    # Send notification
    notifier.notify_hunt_complete(hunt_report)
