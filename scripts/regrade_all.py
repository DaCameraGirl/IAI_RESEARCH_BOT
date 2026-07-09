#!/usr/bin/env python3
"""Regrade all study candidates with current READY threshold."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from patent_hunter import regrade_stored_candidates
from study_bot import STUDY_META

if __name__ == "__main__":
    print("Regrading all studies with new READY threshold...")
    total = 0
    for study_id in STUDY_META.keys():
        try:
            count = regrade_stored_candidates(study_id)
            if count > 0:
                print(f"  {study_id}: {count} candidates regraded")
            total += count
        except Exception as e:
            print(f"  {study_id}: Error - {e}")
    print(f"\nTotal: {total} candidates regraded")
