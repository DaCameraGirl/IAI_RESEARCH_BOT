#!/usr/bin/env python3
"""Product evidence search — Archive.org, YouTube, Reddit, Wayback Machine."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _fetch_json(url: str, timeout: int = 20) -> dict[str, Any]:
    """Fetch JSON from URL with rate limiting."""
    time.sleep(1.0)  # Rate limit
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"Fetch error: {e}")
        return {}


def search_archive_org(
    query: str,
    mediatype: str = "texts",
    max_results: int = 20,
) -> list[dict[str, str]]:
    """
    Search Archive.org for product manuals, catalogs, technical documents.
    
    Args:
        query: Search query (e.g., "blender manual offset blade")
        mediatype: Type of media (texts, movies, audio, etc.)
        max_results: Maximum number of results to return
    
    Returns:
        List of dicts with keys: title, identifier, url, description, year
    """
    # Archive.org Advanced Search API
    # https://archive.org/advancedsearch.php
    q = urllib.parse.quote(query)
    fields = "identifier,title,description,year,downloads"
    url = (
        f"https://archive.org/advancedsearch.php?"
        f"q={q}&fl={fields}&rows={max_results}&page=1"
        f"&output=json&mediatype={mediatype}"
    )
    
    data = _fetch_json(url)
    if not data or "response" not in data:
        return []
    
    results = []
    for doc in data["response"].get("docs", []):
        identifier = doc.get("identifier", "")
        if not identifier:
            continue
        
        results.append({
            "title": doc.get("title", "Unknown"),
            "identifier": identifier,
            "url": f"https://archive.org/details/{identifier}",
            "description": doc.get("description", "")[:200],
            "year": str(doc.get("year", "unknown")),
            "downloads": doc.get("downloads", 0),
        })
    
    return results


def search_youtube(
    query: str,
    before_date: str | None = None,
    max_results: int = 10,
) -> list[dict[str, str]]:
    """
    Search YouTube for teardown/repair videos (requires API key).
    
    Args:
        query: Search query (e.g., "blender teardown repair")
        before_date: ISO date string (YYYY-MM-DD) for publishedBefore filter
        max_results: Maximum number of results
    
    Returns:
        List of dicts with keys: title, video_id, url, channel, published_date
    
    Note: Requires YOUTUBE_API_KEY environment variable.
    """
    import os
    
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("YouTube search requires YOUTUBE_API_KEY environment variable")
        return []
    
    q = urllib.parse.quote(query)
    url = (
        f"https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&q={q}&type=video&maxResults={max_results}&key={api_key}"
    )
    
    if before_date:
        # Convert YYYY-MM-DD to RFC 3339 format
        url += f"&publishedBefore={before_date}T23:59:59Z"
    
    data = _fetch_json(url)
    if not data or "items" not in data:
        return []
    
    results = []
    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId", "")
        if not video_id:
            continue
        
        snippet = item.get("snippet", {})
        results.append({
            "title": snippet.get("title", "Unknown"),
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "channel": snippet.get("channelTitle", "Unknown"),
            "published_date": snippet.get("publishedAt", "")[:10],
            "description": snippet.get("description", "")[:200],
        })
    
    return results


def search_reddit(
    query: str,
    subreddit: str | None = None,
    before_timestamp: int | None = None,
    max_results: int = 25,
) -> list[dict[str, str]]:
    """
    Search Reddit using Pushshift API for product discussions.
    
    Args:
        query: Search query (e.g., "blender blade offset")
        subreddit: Specific subreddit to search (e.g., "BuyItForLife")
        before_timestamp: Unix timestamp for posts before this date
        max_results: Maximum number of results
    
    Returns:
        List of dicts with keys: title, url, author, created_date, score, subreddit
    """
    # Pushshift Reddit Search API
    q = urllib.parse.quote(query)
    url = f"https://api.pushshift.io/reddit/search/submission/?q={q}&size={max_results}"
    
    if subreddit:
        url += f"&subreddit={subreddit}"
    
    if before_timestamp:
        url += f"&before={before_timestamp}"
    
    data = _fetch_json(url, timeout=30)
    if not data or "data" not in data:
        return []
    
    results = []
    for post in data.get("data", []):
        post_id = post.get("id", "")
        if not post_id:
            continue
        
        results.append({
            "title": post.get("title", "Unknown"),
            "url": f"https://reddit.com{post.get('permalink', '')}",
            "author": post.get("author", "unknown"),
            "created_date": time.strftime("%Y-%m-%d", time.gmtime(post.get("created_utc", 0))),
            "score": post.get("score", 0),
            "subreddit": post.get("subreddit", "unknown"),
            "selftext": post.get("selftext", "")[:200],
        })
    
    return results


def search_wayback_machine(
    url: str,
    from_date: str = "20100101",
    to_date: str = "20191231",
) -> list[dict[str, str]]:
    """
    Search Wayback Machine for archived versions of a URL.
    
    Args:
        url: URL to search for (e.g., "vitamix.com")
        from_date: Start date in YYYYMMDD format
        to_date: End date in YYYYMMDD format
    
    Returns:
        List of dicts with keys: timestamp, url, status_code
    """
    # Wayback Machine CDX API
    # https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server
    encoded_url = urllib.parse.quote(url)
    api_url = (
        f"https://web.archive.org/cdx/search/cdx?"
        f"url={encoded_url}&from={from_date}&to={to_date}"
        f"&output=json&limit=50&filter=statuscode:200"
    )
    
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"Wayback fetch error: {e}")
        return []
    
    if not data or len(data) < 2:
        return []
    
    # First row is headers
    headers = data[0]
    results = []
    
    for row in data[1:]:
        if len(row) < 3:
            continue
        
        timestamp = row[1]  # YYYYMMDDHHMMSS format
        original_url = row[2]
        status_code = row[4] if len(row) > 4 else "200"
        
        # Format timestamp as YYYY-MM-DD
        date_str = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
        
        results.append({
            "timestamp": timestamp,
            "date": date_str,
            "url": f"https://web.archive.org/web/{timestamp}/{original_url}",
            "original_url": original_url,
            "status_code": status_code,
        })
    
    return results


def search_product_evidence(
    product_keywords: list[str],
    technical_terms: list[str],
    before_date: str,
    max_per_source: int = 10,
) -> dict[str, list[dict[str, str]]]:
    """
    Search multiple sources for product evidence.
    
    Args:
        product_keywords: Product names/types (e.g., ["blender", "food processor"])
        technical_terms: Technical features (e.g., ["offset blade", "eccentric rotor"])
        before_date: Critical date in YYYY-MM-DD format
        max_per_source: Max results per source
    
    Returns:
        Dict with keys: archive_org, youtube, reddit, wayback
    """
    results = {
        "archive_org": [],
        "youtube": [],
        "reddit": [],
        "wayback": [],
    }
    
    # Build search queries
    queries = []
    for product in product_keywords[:3]:  # Limit to avoid too many queries
        for term in technical_terms[:3]:
            queries.append(f"{product} {term}")
    
    # Archive.org search
    print("Searching Archive.org for product manuals...")
    for query in queries[:5]:  # Limit queries
        hits = search_archive_org(
            f"{query} manual catalog datasheet",
            mediatype="texts",
            max_results=max_per_source,
        )
        results["archive_org"].extend(hits)
        if len(results["archive_org"]) >= max_per_source * 2:
            break
    
    # YouTube search (if API key available)
    print("Searching YouTube for teardown videos...")
    for query in queries[:3]:
        hits = search_youtube(
            f"{query} teardown repair disassembly",
            before_date=before_date,
            max_results=max_per_source,
        )
        results["youtube"].extend(hits)
        if len(results["youtube"]) >= max_per_source * 2:
            break
    
    # Reddit search
    print("Searching Reddit for product discussions...")
    before_ts = int(time.mktime(time.strptime(before_date, "%Y-%m-%d")))
    for query in queries[:3]:
        hits = search_reddit(
            query,
            subreddit=None,  # Search all subreddits
            before_timestamp=before_ts,
            max_results=max_per_source,
        )
        results["reddit"].extend(hits)
        if len(results["reddit"]) >= max_per_source * 2:
            break
    
    # Wayback Machine search for manufacturer sites
    print("Searching Wayback Machine for archived product pages...")
    manufacturer_domains = [
        "vitamix.com",
        "blendtec.com",
        "ninja.com",
        "cuisinart.com",
        "kitchenaid.com",
        "oster.com",
        "hamilton-beach.com",
    ]
    
    to_date = before_date.replace("-", "")
    for domain in manufacturer_domains[:5]:
        hits = search_wayback_machine(
            domain,
            from_date="20100101",
            to_date=to_date,
        )
        results["wayback"].extend(hits)
        if len(results["wayback"]) >= max_per_source * 3:
            break
    
    return results


if __name__ == "__main__":
    # Test searches
    print("Testing Archive.org search...")
    archive_results = search_archive_org("blender manual offset blade", max_results=5)
    print(f"Found {len(archive_results)} Archive.org results")
    for r in archive_results[:2]:
        print(f"  - {r['title']} ({r['year']}): {r['url']}")
    
    print("\nTesting Reddit search...")
    reddit_results = search_reddit("blender blade design", max_results=5)
    print(f"Found {len(reddit_results)} Reddit results")
    for r in reddit_results[:2]:
        print(f"  - {r['title']} (r/{r['subreddit']}): {r['url']}")
    
    print("\nTesting Wayback Machine search...")
    wayback_results = search_wayback_machine("vitamix.com", to_date="20191231")
    print(f"Found {len(wayback_results)} Wayback snapshots")
    for r in wayback_results[:2]:
        print(f"  - {r['date']}: {r['url']}")
