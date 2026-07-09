"""
Timeline Visualizer - Generate visual timeline showing prior art dates vs critical date
Helps identify temporal relationships and filing date gaps
"""

from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime, timedelta
import json


class TimelineVisualizer:
    """
    Generate timeline visualizations for prior art
    Features:
    - ASCII timeline for terminal
    - HTML timeline for browser
    - Critical date highlighting
    - Date gap analysis
    - Temporal clustering
    """
    
    def __init__(self, critical_date: str):
        """
        Initialize timeline visualizer
        
        Args:
            critical_date: Critical date in YYYY-MM-DD format
        """
        self.critical_date = datetime.strptime(critical_date, '%Y-%m-%d')
    
    def generate_ascii_timeline(
        self,
        candidates: List[Dict],
        width: int = 80
    ) -> str:
        """
        Generate ASCII timeline for terminal display
        
        Args:
            candidates: List of candidate dicts with 'date' field
            width: Terminal width in characters
            
        Returns:
            ASCII timeline string
        """
        # Filter candidates with valid dates
        dated_candidates = [
            c for c in candidates
            if c.get('date') and self._parse_date(c['date'])
        ]
        
        if not dated_candidates:
            return "No candidates with valid dates"
        
        # Parse dates
        for candidate in dated_candidates:
            candidate['parsed_date'] = self._parse_date(candidate['date'])
        
        # Sort by date
        dated_candidates.sort(key=lambda c: c['parsed_date'])
        
        # Find date range
        earliest = dated_candidates[0]['parsed_date']
        latest = max(dated_candidates[-1]['parsed_date'], self.critical_date)
        
        # Build timeline
        lines = []
        lines.append("=" * width)
        lines.append("PRIOR ART TIMELINE")
        lines.append("=" * width)
        lines.append("")
        
        # Calculate scale
        total_days = (latest - earliest).days
        if total_days == 0:
            total_days = 1
        
        scale = (width - 20) / total_days
        
        # Add timeline axis
        lines.append(f"{earliest.strftime('%Y-%m-%d')} " + "-" * (width - 30) + f" {latest.strftime('%Y-%m-%d')}")
        lines.append("")
        
        # Add critical date marker
        critical_pos = int((self.critical_date - earliest).days * scale)
        critical_line = " " * critical_pos + "▼ CRITICAL DATE"
        lines.append(critical_line)
        lines.append(" " * critical_pos + "│")
        lines.append("")
        
        # Add candidates
        for candidate in dated_candidates:
            pos = int((candidate['parsed_date'] - earliest).days * scale)
            
            # Determine marker based on relation to critical date
            if candidate['parsed_date'] < self.critical_date:
                marker = "●"  # Valid prior art
                status = "✓"
            else:
                marker = "○"  # After critical date
                status = "✗"
            
            # Build line
            line = " " * pos + marker
            
            # Add title (truncated)
            title = candidate.get('title', 'Untitled')[:40]
            date_str = candidate['parsed_date'].strftime('%Y-%m-%d')
            
            lines.append(f"{line} {status} {date_str} - {title}")
        
        lines.append("")
        lines.append("Legend:")
        lines.append("  ● = Before critical date (valid prior art)")
        lines.append("  ○ = After critical date (invalid)")
        lines.append("=" * width)
        
        return "\n".join(lines)
    
    def generate_html_timeline(
        self,
        candidates: List[Dict],
        output_path: Path
    ):
        """
        Generate interactive HTML timeline
        
        Args:
            candidates: List of candidate dicts
            output_path: Path to save HTML file
        """
        # Filter candidates with valid dates
        dated_candidates = [
            c for c in candidates
            if c.get('date') and self._parse_date(c['date'])
        ]
        
        if not dated_candidates:
            output_path.write_text("<html><body>No candidates with valid dates</body></html>")
            return
        
        # Parse dates
        for candidate in dated_candidates:
            candidate['parsed_date'] = self._parse_date(candidate['date'])
        
        # Sort by date
        dated_candidates.sort(key=lambda c: c['parsed_date'])
        
        # Build HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Prior Art Timeline</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .timeline {{
            position: relative;
            padding: 40px 0;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .timeline-axis {{
            position: relative;
            height: 2px;
            background: #ddd;
            margin: 20px 40px;
        }}
        .critical-date {{
            position: absolute;
            width: 3px;
            height: 100px;
            background: #ff4444;
            top: -50px;
        }}
        .critical-label {{
            position: absolute;
            top: -70px;
            left: -50px;
            width: 100px;
            text-align: center;
            font-weight: bold;
            color: #ff4444;
            font-size: 12px;
        }}
        .candidate {{
            position: absolute;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            top: -5px;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        .candidate:hover {{
            transform: scale(1.5);
        }}
        .candidate.valid {{
            background: #4CAF50;
            border: 2px solid #2E7D32;
        }}
        .candidate.invalid {{
            background: #f44336;
            border: 2px solid #c62828;
        }}
        .tooltip {{
            position: absolute;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 1000;
            max-width: 300px;
            top: 30px;
        }}
        .candidate:hover .tooltip {{
            opacity: 1;
        }}
        .legend {{
            margin: 20px 40px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 5px;
        }}
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
        }}
        .legend-dot {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 5px;
            vertical-align: middle;
        }}
        .stats {{
            margin: 20px 40px;
            padding: 15px;
            background: #e3f2fd;
            border-radius: 5px;
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
    </style>
</head>
<body>
    <h1>Prior Art Timeline</h1>
    
    <div class="stats">
        <strong>Critical Date:</strong> {self.critical_date.strftime('%Y-%m-%d')}<br>
        <strong>Total Candidates:</strong> {len(dated_candidates)}<br>
        <strong>Valid Prior Art:</strong> {len([c for c in dated_candidates if c['parsed_date'] < self.critical_date])}<br>
        <strong>After Critical Date:</strong> {len([c for c in dated_candidates if c['parsed_date'] >= self.critical_date])}
    </div>
    
    <div class="timeline">
        <div class="timeline-axis">
"""
        
        # Calculate positions
        earliest = dated_candidates[0]['parsed_date']
        latest = max(dated_candidates[-1]['parsed_date'], self.critical_date)
        total_days = (latest - earliest).days
        if total_days == 0:
            total_days = 1
        
        # Add critical date marker
        critical_pos = ((self.critical_date - earliest).days / total_days) * 100
        html += f"""
            <div class="critical-date" style="left: {critical_pos}%;">
                <div class="critical-label">CRITICAL<br>DATE</div>
            </div>
"""
        
        # Add candidates
        for candidate in dated_candidates:
            pos = ((candidate['parsed_date'] - earliest).days / total_days) * 100
            is_valid = candidate['parsed_date'] < self.critical_date
            
            title = candidate.get('title', 'Untitled')
            date_str = candidate['parsed_date'].strftime('%Y-%m-%d')
            source = candidate.get('source', 'Unknown')
            
            html += f"""
            <div class="candidate {'valid' if is_valid else 'invalid'}" style="left: {pos}%;">
                <div class="tooltip">
                    <strong>{title}</strong><br>
                    Date: {date_str}<br>
                    Source: {source}<br>
                    Status: {'✓ Valid prior art' if is_valid else '✗ After critical date'}
                </div>
            </div>
"""
        
        html += """
        </div>
    </div>
    
    <div class="legend">
        <div class="legend-item">
            <span class="legend-dot" style="background: #4CAF50; border: 2px solid #2E7D32;"></span>
            Valid Prior Art (before critical date)
        </div>
        <div class="legend-item">
            <span class="legend-dot" style="background: #f44336; border: 2px solid #c62828;"></span>
            After Critical Date (invalid)
        </div>
    </div>
</body>
</html>
"""
        
        output_path.write_text(html, encoding='utf-8')
        print(f"✓ Timeline saved: {output_path}")
    
    def analyze_date_gaps(self, candidates: List[Dict]) -> Dict:
        """
        Analyze temporal gaps in prior art coverage
        
        Args:
            candidates: List of candidate dicts
            
        Returns:
            Gap analysis dict
        """
        # Filter and parse dates
        dated_candidates = []
        for candidate in candidates:
            parsed_date = self._parse_date(candidate.get('date'))
            if parsed_date and parsed_date < self.critical_date:
                dated_candidates.append({
                    **candidate,
                    'parsed_date': parsed_date
                })
        
        if not dated_candidates:
            return {'gaps': [], 'coverage': 0}
        
        # Sort by date
        dated_candidates.sort(key=lambda c: c['parsed_date'])
        
        # Find gaps
        gaps = []
        for i in range(len(dated_candidates) - 1):
            current = dated_candidates[i]['parsed_date']
            next_date = dated_candidates[i + 1]['parsed_date']
            
            gap_days = (next_date - current).days
            
            # Consider gaps > 365 days significant
            if gap_days > 365:
                gaps.append({
                    'start': current.strftime('%Y-%m-%d'),
                    'end': next_date.strftime('%Y-%m-%d'),
                    'days': gap_days,
                    'years': gap_days / 365.25
                })
        
        # Calculate coverage
        earliest = dated_candidates[0]['parsed_date']
        total_days = (self.critical_date - earliest).days
        coverage = len(dated_candidates) / max(total_days / 365.25, 1)
        
        return {
            'gaps': gaps,
            'coverage': coverage,
            'earliest_date': earliest.strftime('%Y-%m-%d'),
            'latest_date': dated_candidates[-1]['parsed_date'].strftime('%Y-%m-%d'),
            'total_candidates': len(dated_candidates)
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        
        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y',
            '%B %d, %Y',
            '%b %d, %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None


# Example usage
if __name__ == "__main__":
    visualizer = TimelineVisualizer(critical_date="2019-10-28")
    
    # Example candidates
    candidates = [
        {'title': 'Early Patent 2005', 'date': '2005-03-15', 'source': 'uspto'},
        {'title': 'Datasheet 2010', 'date': '2010-06-20', 'source': 'wayback'},
        {'title': 'Conference Paper 2015', 'date': '2015-09-10', 'source': 'ieee'},
        {'title': 'Recent Patent 2018', 'date': '2018-12-01', 'source': 'uspto'},
        {'title': 'Too Late 2020', 'date': '2020-01-15', 'source': 'uspto'},
    ]
    
    # Generate ASCII timeline
    ascii_timeline = visualizer.generate_ascii_timeline(candidates)
    print(ascii_timeline)
    
    # Generate HTML timeline
    visualizer.generate_html_timeline(candidates, Path("timeline.html"))
    
    # Analyze gaps
    gap_analysis = visualizer.analyze_date_gaps(candidates)
    print(f"\nGap Analysis:")
    print(f"  Coverage: {gap_analysis['coverage']:.2f} candidates/year")
    print(f"  Significant gaps: {len(gap_analysis['gaps'])}")
