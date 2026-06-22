#!/usr/bin/env python3
"""Build Windows .ico from genie mascot for desktop shortcut."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "assets" / "genie-mascot.jpg"
OUT = REPO / "assets" / "genie-mascot.ico"


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Missing mascot image: {SRC}")

    img = Image.open(SRC).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    sizes = [256, 128, 64, 48, 32, 16]
    icons = [img.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]
    icons[0].save(
        OUT,
        format="ICO",
        sizes=[(i.width, i.height) for i in icons],
        append_images=icons[1:],
    )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()