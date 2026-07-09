"""Test MusicBrainz and Discogs search functions."""
import sys
sys.path.insert(0, r'C:\Users\enter\OneDrive\Desktop\RWS_RESEARCH_BOT\scripts')

from product_search import search_musicbrainz, search_discogs

print("=" * 60)
print("Testing MusicBrainz API (no key needed)")
print("=" * 60)
results = search_musicbrainz('Amazing Grace', max_results=3)
print(f"\nFound {len(results)} MusicBrainz results:")
for r in results[:3]:
    print(f"  - {r['title']} by {r['artist']}")
    print(f"    Released: {r['release_date']}")
    print(f"    URL: {r['url']}")
    print()

print("=" * 60)
print("Testing Discogs API (requires DISCOGS_API_KEY)")
print("=" * 60)
results = search_discogs('Amazing Grace hymnal', max_results=3)
print(f"\nFound {len(results)} Discogs results:")
for r in results[:3]:
    print(f"  - {r['title']} by {r['artist']}")
    print(f"    Year: {r['year']}, Format: {r['format']}")
    print(f"    URL: {r['url']}")
    print()

print("=" * 60)
print("Test complete!")
print("=" * 60)
