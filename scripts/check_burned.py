#!/usr/bin/env python3
"""Check if a document number is in a study's known_citations.csv."""

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STUDY_DIRS = {
    "25867": REPO / "25867_Remote_Memory_Transactions",
    "25854": REPO / "25854_Semiconductor_Wafer_Dividing",
    "25853": REPO / "25853_Light_Emitting_Device_Resin_Package",
}


def normalize(doc: str) -> str:
    return doc.strip().upper().replace("-", "").replace(" ", "")


def load_burned(study_id: str) -> dict[str, str]:
    folder = STUDY_DIRS.get(study_id)
    if not folder:
        raise SystemExit(f"Unknown study {study_id}. Use: {', '.join(STUDY_DIRS)}")
    csv_path = folder / "known_art" / "known_citations.csv"
    if not csv_path.exists():
        raise SystemExit(f"Missing {csv_path}")

    burned: dict[str, str] = {}
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            key = normalize(row["Citation/Document Number"])
            burned[key] = row.get("Relation", "unknown")
    return burned


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scripts/check_burned.py <study_id> <doc_number> [doc_number ...]")
        print("Example: python scripts/check_burned.py 25867 US5613071")
        raise SystemExit(1)

    study_id = sys.argv[1]
    burned = load_burned(study_id)

    for raw in sys.argv[2:]:
        key = normalize(raw)
        if key in burned:
            print(f"BURNED  {raw}  ({burned[key]})")
        else:
            print(f"CLEAR   {raw}")


if __name__ == "__main__":
    main()