#!/usr/bin/env python3
"""
Demo Taxonomy Search - Shows what the search would return
(Uses sample data, no API key needed)
"""

import sys

# Sample taxonomy data (subset of what Etsy API would return)
SAMPLE_TAXONOMIES = [
    {"id": 1076, "name": "Candles", "path": "Home & Living > Home Décor > Candles", "level": 2},
    {"id": 69152145, "name": "Scented Candles", "path": "Home & Living > Home Décor > Candles > Scented Candles", "level": 3},
    {"id": 69152146, "name": "Unscented Candles", "path": "Home & Living > Home Décor > Candles > Unscented Candles", "level": 3},
    {"id": 69152147, "name": "Soy Candles", "path": "Home & Living > Home Décor > Candles > Soy Candles", "level": 3},
    {"id": 69152148, "name": "Beeswax Candles", "path": "Home & Living > Home Décor > Candles > Beeswax Candles", "level": 3},
    {"id": 69152149, "name": "Pillar Candles", "path": "Home & Living > Home Décor > Candles > Pillar Candles", "level": 3},
    {"id": 69152150, "name": "Votive Candles", "path": "Home & Living > Home Décor > Candles > Votive Candles", "level": 3},
    {"id": 69152151, "name": "Tea Light Candles", "path": "Home & Living > Home Décor > Candles > Tea Light Candles", "level": 3},
    {"id": 69152152, "name": "Jar Candles", "path": "Home & Living > Home Décor > Candles > Jar Candles", "level": 3},
    {"id": 69152153, "name": "Taper Candles", "path": "Home & Living > Home Décor > Candles > Taper Candles", "level": 3},
    {"id": 69152154, "name": "Floating Candles", "path": "Home & Living > Home Décor > Candles > Floating Candles", "level": 3},
    {"id": 551, "name": "Soaps", "path": "Bath & Beauty > Soaps", "level": 1},
    {"id": 1062, "name": "Jewelry", "path": "Accessories > Jewelry", "level": 1},
    {"id": 843, "name": "Home & Living", "path": "Home & Living", "level": 0},
]


def search_taxonomies(search_term):
    """Search for taxonomies matching the term."""
    search_lower = search_term.lower()
    matches = []

    for tax in SAMPLE_TAXONOMIES:
        if search_lower in tax["name"].lower() or search_lower in tax["path"].lower():
            matches.append(tax)

    return matches


def print_results(search_term, matches):
    """Print search results."""
    print("="*80)
    print("DEMO: Taxonomy ID Finder (Using Sample Data)")
    print("="*80)
    print(f"\n🔍 Searching for: '{search_term}'")

    if not matches:
        print(f"\nNo categories found matching '{search_term}'")
        return

    print(f"\nFound {len(matches)} categor{'ies' if len(matches) != 1 else 'y'}")
    print("="*80)

    for i, tax in enumerate(matches, 1):
        indent = "  " * tax["level"]
        print(f"\n{i}. {indent}ID: {tax['id']}")
        print(f"   {indent}Name: {tax['name']}")
        print(f"   {indent}Path: {tax['path']}")

    print("\n" + "="*80)
    print("💡 To fetch metadata for a category, use:")
    print(f"   python src/fetch_taxonomy_metadata.py <ID>")
    print("\nExample:")
    print(f"   python src/fetch_taxonomy_metadata.py {matches[0]['id']}")
    print("="*80)

    print("\n📝 Note: This is DEMO data. With a real API key, you would get:")
    print("   - Complete taxonomy tree (thousands of categories)")
    print("   - All subcategories and paths")
    print("   - Real-time data from Etsy")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        search_term = " ".join(sys.argv[1:])
    else:
        search_term = input("Enter category to search for: ")

    matches = search_taxonomies(search_term)
    print_results(search_term, matches)


if __name__ == "__main__":
    main()
