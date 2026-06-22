#!/usr/bin/env python3
"""Build verified URLs for patent and NPL candidates."""

from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _normalize_pub(pub: str) -> str:
    pub = pub.strip().upper().replace("-", "").replace(" ", "")
    if not pub.startswith(("US", "EP", "WO", "CN", "JP", "KR")):
        pub = "US" + pub
    return pub


def patent_digits(pub: str) -> str:
    pub = _normalize_pub(pub)
    pub = re.sub(r"(\d)[A-Z]\d+$", r"\1", pub)
    m = re.match(r"^US(19\d{2}|20\d{2})(\d+)$", pub)
    if m:
        return f"{m.group(1)}{m.group(2)}"
    m = re.match(r"^US(\d+)$", pub)
    return m.group(1) if m else pub.replace("US", "")


def google_patent_url(pub: str) -> str:
    return f"https://patents.google.com/patent/{_normalize_pub(pub)}"


def uspto_url(pub: str) -> str:
    digits = patent_digits(pub)
    if re.match(r"^(19|20)\d{6,}$", digits):
        return (
            "https://patft.uspto.gov/netacgi/nph-Parser?"
            f"Sect1=PTO2&Sect2=HITOFF&p=1&u=%2Fnetahtml%2FPTO%2Fsearch-bool.html"
            f"&r=0&f=S&l=50&TERM1={digits}&FIELD1=APNR"
        )
    return (
        "https://patft.uspto.gov/netacgi/nph-Parser?"
        f"Sect1=PTO1&Sect2=HITOFF&d=PALL&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.htm"
        f"&r=1&f=G&l=50&s1={digits}.PN.&OS=PN/{digits}&RS=PN/{digits}"
    )


def uspto_pdf_url(pub: str) -> str:
    digits = patent_digits(pub)
    if re.match(r"^(19|20)\d{6,}$", digits):
        return f"https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/{digits}"
    return f"https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/{digits}"


def fetch_google_pdf_url(pub: str) -> str:
    url = google_patent_url(pub)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError):
        return ""

    m = re.search(r"(https://patentimages\.storage\.googleapis\.com/[^\"\s]+\.pdf)", html)
    if m:
        return m.group(1)
    m = re.search(r"(https://patentimages\.storage\.googleapis\.com/[^\"\s]+)", html)
    return m.group(1) if m else ""


def patent_links(pub: str, html: str | None = None) -> dict[str, str]:
    """Return google, pdf, uspto, uspto_pdf links for a publication."""
    google = google_patent_url(pub)
    pdf = ""
    if html:
        m = re.search(r"(https://patentimages\.storage\.googleapis\.com/[^\"\s]+\.pdf)", html)
        if m:
            pdf = m.group(1)
        elif m := re.search(r"(https://patentimages\.storage\.googleapis\.com/[^\"\s]+)", html):
            pdf = m.group(1)
    if not pdf:
        pdf = fetch_google_pdf_url(pub)
    if not pdf:
        pdf = uspto_pdf_url(pub)

    espacenet = (
        "https://worldwide.espacenet.com/patent/search?"
        f"q=pn%3D{_normalize_pub(pub)}"
    )

    return {
        "google": google,
        "pdf": pdf,
        "uspto": uspto_url(pub),
        "uspto_pdf": uspto_pdf_url(pub),
        "espacenet": espacenet,
        "doi": "n/a",
    }


def crossref_lookup(title: str, year: str | None = None, before: str | None = None) -> dict[str, str]:
    """Look up DOI and URL via Crossref (free API, no key)."""
    query = urllib.parse.quote(title[:200])
    url = f"https://api.crossref.org/works?query.title={query}&rows=5"
    if before:
        url += f"&filter=until-pub-date:{before}"
    elif year:
        url += f"&filter=until-pub-date:{year}-12-31"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "RWS-Research-Bot/1.0 (mailto:research@local)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            import json

            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return {"doi": "not found", "url": "", "journal": ""}

    items = data.get("message", {}).get("items", [])
    if not items:
        return {"doi": "not found", "url": "", "journal": ""}

    best = items[0]
    for item in items:
        issued = (item.get("issued") or {}).get("date-parts", [[]])
        if issued and issued[0]:
            pub_year = int(issued[0][0])
            if before and len(before) >= 4:
                limit = int(before[:4])
                if pub_year > limit:
                    continue
            elif year and pub_year > int(year):
                continue
        best = item
        break
    doi = best.get("DOI", "not found")
    journal = ""
    if best.get("container-title"):
        journal = best["container-title"][0]
    link = f"https://doi.org/{doi}" if doi and doi != "not found" else ""
    return {"doi": doi, "url": link, "journal": journal}