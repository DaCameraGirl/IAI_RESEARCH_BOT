#!/usr/bin/env python3
"""Study requirement maps for thorough candidate drafting."""

from __future__ import annotations

STUDY_KEYWORDS: dict[str, list[str]] = {
    "26052": [
        "blade", "blender", "rotor", "offset", "longitudinal axis", "container",
        "eccentric", "off-center", "off center", "tornado", "vortex", "mixing",
        "chopping", "food processor", "rechargeable", "blending",
    ],
    "25974": [
        "oximidol", "tyrosinase inhibitor", "thiamidol", "isopropyl lauroyl sarcosinate",
        "melanin", "skin whitening", "skin brightening", "hydroquinone", "kojic acid",
        "niacinamide", "arbutin", "resorcinol", "thiazolyl", "alkylamidothiazole",
        "beiersdorf", "sarcosinate",
    ],
}

STUDY_REQUIREMENTS: dict[str, list[dict[str, str]]] = {
    "26052": [
        {"id": "1.1", "name": "Blades rotate around rotational axis, blend contents", "keywords": ["blade", "rotor", "rotational axis", "blend", "container"]},
        {"id": "1.2", "name": "Blade rotational axis offset from container's longitudinal axis", "keywords": ["offset", "longitudinal axis", "container", "off-center", "off center", "eccentric"]},
        {"id": "1.3", "name": "Offset is 5%-15% of blade diameter", "keywords": ["offset", "diameter", "percent", "5%", "15%", "eccentric"]},
    ],
    "25974": [
        {"id": "1", "name": "Oximidol (exact structure)", "keywords": ["oximidol", "methyloxetanecarbamido", "thiazolyl resorcinol", "3081328-14-2", "kt-939", "kwhite 939", "nexawhite 939"]},
        {"id": "2", "name": "Cosmetic/dermatological formulation with Oximidol or structurally similar", "keywords": ["cosmetic", "dermatological", "formulation", "tyrosinase inhibitor", "skin whitening", "skin brightening"]},
        {"id": "3", "name": "Oximidol (or alkylamidothiazole) with Isopropyl Lauroyl Sarcosinate", "keywords": ["isopropyl lauroyl sarcosinate", "sarcosinate", "solvent", "thiamidol", "alkylamidothiazole"]},
    ],
}

PRIORITY_REQ_IDS: dict[str, tuple[str, ...]] = {
    "26052": ("1.1", "1.2", "1.3"),
    "25974": ("1", "2", "3"),
}

SYNONYM_QUERIES: dict[str, list[str]] = {
    "26052": [
        "blender offset blade vortex mixing",
        "eccentric blade rotor blending container",
        "off-center rotor food processor design",
        "blade rotational axis offset container longitudinal axis",
        "tornado effect blending blade offset",
        "rechargeable blender chopper offset blade diameter",
    ],
    "25974": [
        "oximidol tyrosinase inhibitor skin whitening",
        "thiamidol isopropyl lauroyl sarcosinate solvent",
        "alkylamidothiazole resorcinol skin brightening formulation",
        "KT-939 KWhite 939 NexaWhite 939 cosmetic",
        "thiazolyl resorcinol melanin inhibitor",
        "Beiersdorf thiamidol product literature solvent",
    ],
}

CPC_QUERIES: dict[str, list[str]] = {
    "26052": [
        "A47J43/046 blender blade arrangement",
        "A47J43/07 rotating blade mixer",
        "A47J43/044 blade offset container",
    ],
    "25974": [
        "A61K8/44 cosmetic compositions nitrogen organic compounds",
        "A61Q19/02 skin whitening preparations",
        "A61K31/425 thiazole compounds",
    ],
}

NPL_QUERIES: dict[str, list[str]] = {
    "26052": [
        "blender offset blade vortex mixing product literature",
        "food processor eccentric rotor design manual",
    ],
    "25974": [
        "thiamidol isopropyl lauroyl sarcosinate solubility dissertation",
        "tyrosinase inhibitor thiazolyl resorcinol conference abstract",
        "Beiersdorf thiamidol product literature solvent",
    ],
}


def map_requirements(study_id: str, text: str) -> list[dict[str, str]]:
    """Return requirement rows with select/why for drafting."""
    text_l = text.lower()
    rows = []
    for req in STUDY_REQUIREMENTS.get(study_id, []):
        hits = [k for k in req["keywords"] if k.lower() in text_l]
        if len(hits) >= 2:
            select, why = "yes", f"Abstract/title mentions: {', '.join(hits[:3])}"
        elif len(hits) == 1:
            select, why = "maybe", f"Weak signal — verify in PDF: {hits[0]}"
        else:
            select, why = "no", "No keyword hit in title/abstract — check claims manually"
        rows.append({"id": req["id"], "name": req["name"], "select": select, "why": why, "hits": hits})
    return rows


def ctrl_f_phrases(text: str, keywords: list[str], limit: int = 6) -> list[str]:
    """Pull Ctrl+F phrases from abstract sentences containing keywords."""
    phrases: list[str] = []
    sentences = re_split_sentences(text)
    for sent in sentences:
        sl = sent.lower()
        if any(k.lower() in sl for k in keywords):
            clean = " ".join(sent.split())
            if 20 <= len(clean) <= 220:
                phrases.append(clean)
        if len(phrases) >= limit:
            break
    if not phrases and text:
        phrases.append(text[:180].strip() + ("…" if len(text) > 180 else ""))
    return phrases[:limit]


def re_split_sentences(text: str) -> list[str]:
    import re

    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) > 15]
