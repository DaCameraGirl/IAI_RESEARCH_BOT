#!/usr/bin/env python3
"""Study requirement maps for thorough candidate drafting."""

from __future__ import annotations

STUDY_KEYWORDS: dict[str, list[str]] = {
    "25867": [
        "memory transaction", "programmed i/o", "remote memory", "memory mapped",
        "host bus", "network interface", "priority queue", "packet priority",
        "posted write", "non-posted", "sequence number", "acknowledgement",
        "retransmit", "lossy", "packet drop", "congestion", "ethernet",
        "ordering", "rdma", "remote dma",
    ],
    "25854": [
        "pulsed laser", "wafer", "fissure", "crack", "divide", "sapphire",
        "gan", "semiconductor", "stealth dicing", "laser dicing", "substrate",
        "modified region", "processed portion",
    ],
    "25853": ["resin", "package", "light emitting", "led", "encapsulant"],
}

STUDY_REQUIREMENTS: dict[str, list[dict[str, str]]] = {
    "25867": [
        {"id": "1.1", "name": "Receive MTMs from local memory controller", "keywords": ["memory transaction", "memory controller", "processor bus", "host bus"]},
        {"id": "1.2", "name": "Determine MTMs destined for remote node", "keywords": ["remote", "remote node", "destined", "destination"]},
        {"id": "1.3", "name": "Determine transaction type for each MTM", "keywords": ["transaction type", "posted", "non-posted", "request", "response"]},
        {"id": "1.4", "name": "Compose network packet encapsulating MTM", "keywords": ["encapsulat", "packet", "network packet", "frame"]},
        {"id": "1.5", "name": "Assign sending priority per packet", "keywords": ["priority", "packet priority", "sending priority", "qos"]},
        {"id": "1.6", "name": "Organize packets into priority groups", "keywords": ["queue", "priority queue", "group", "organize"]},
        {"id": "1.7", "name": "Send into lossy network by priority order", "keywords": ["lossy", "packet drop", "congestion", "drop", "network"]},
        {"id": "1.8", "name": "Ensure per-priority proper sequence at remote", "keywords": ["sequence", "ordering", "order", "sequenc"]},
        {"id": "1.9", "name": "Posted/response/non-posted priority mapping", "keywords": ["posted write", "non-posted", "response", "priority"]},
        {"id": "1.10", "name": "First/second/third priority queues FIFO", "keywords": ["fifo", "first queue", "second queue", "third queue", "priority queue"]},
        {"id": "1.11", "name": "Resend packet + subsequent on missing ACK", "keywords": ["retransmit", "resend", "ack", "timeout", "nack"]},
        {"id": "1.12", "name": "ACK + sequence match or drop", "keywords": ["acknowledgement", "ack", "sequence number", "expected sequence"]},
        {"id": "1.13", "name": "Lossy network is Ethernet", "keywords": ["ethernet", "lan", "ieee 802"]},
    ],
    "25854": [
        {"id": "1.1", "name": "Laser inside substrate", "keywords": ["laser", "inside", "substrate", "internal"]},
        {"id": "1.2", "name": "Fissure linking adjacent processed portions", "keywords": ["fissure", "adjacent", "processed portion", "link", "crack"]},
        {"id": "1.3", "name": "Wafer dividing along line", "keywords": ["divide", "dividing", "wafer", "split"]},
    ],
    "25853": [
        {"id": "1.1", "name": "Resin package structure", "keywords": ["resin", "package", "encapsul"]},
        {"id": "1.2", "name": "Light emitting device", "keywords": ["led", "light emitting", "semiconductor light"]},
    ],
}

PRIORITY_REQ_IDS: dict[str, tuple[str, ...]] = {
    "25867": ("1.7", "1.8", "1.13"),
    "25854": ("1.1", "1.2", "1.3"),
    "25853": ("1.1", "1.2"),
}

SYNONYM_QUERIES: dict[str, list[str]] = {
    "25867": [
        "ethernet priority queue packet drop congestion",
        "remote memory transaction programmed I/O network",
        "packet retransmit acknowledgement sequence number ethernet",
        "lossy network priority ordering retransmission",
        "posted write non-posted request priority queue",
        "memory mapped remote node network interface",
        "ethernet switch drop QoS queue",
        "go-back-N retransmit packet network",
        "RDMA ethernet congestion drop",
        "remote DMA memory transaction ethernet",
        "host bus network packet priority",
        "ACK NACK sequence number network packet",
        "memory transaction MTM ethernet bridge",
        "programmed I/O bus adapter network packet",
        "non-posted write priority FIFO queue ethernet",
        "IEEE 802.3 congestion drop retransmit",
        "protocol processing engine DMA ethernet",
        "remote memory access network adapter priority",
        "packet coalescing interconnect memory",
        "channel adapter segregate transmit priority",
    ],
    "25854": [
        "laser fissure wafer divide sapphire",
        "stealth dicing internal modification substrate",
        "pulsed laser crack adjacent processed portion",
    ],
    "25853": [
        "LED resin package encapsulant light emitting",
    ],
}

CPC_QUERIES: dict[str, list[str]] = {
    "25867": [
        "H04L12/56 priority queue ethernet",
        "H04L47/10 congestion drop packet",
        "G06F13/28 remote memory bus",
        "H04L69/16 TCP retransmit sequence",
    ],
    "25854": [],
    "25853": [],
}

NPL_QUERIES: dict[str, list[str]] = {
    "25867": [
        "ethernet congestion control priority queue",
        "remote memory access network protocol",
        "packet retransmission sequence number",
        "RDMA over ethernet lossy",
        "memory channel remote DMA",
        "SCI interconnect remote memory",
        "TCP selective repeat ethernet",
    ],
    "25854": [
        "laser stealth dicing sapphire wafer",
    ],
    "25853": [],
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