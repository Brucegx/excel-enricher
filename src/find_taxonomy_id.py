#!/usr/bin/env python3
"""
Etsy Taxonomy ID Finder

Helps you find the correct taxonomy ID for your product category.

Usage:
    python find_taxonomy_id.py [search_term]

Examples:
    python find_taxonomy_id.py              # List all top-level categories
    python find_taxonomy_id.py jewelry      # Search for jewelry-related categories
    python find_taxonomy_id.py "home decor" # Search for home decor categories
"""

import os
import sys
import json
import requests
from typing import List, Dict, Any


class TaxonomyFinder:
    """Helps find Etsy taxonomy IDs."""

    BASE_URL = "https://openapi.etsy.com/v3"

    def __init__(self, api_key: str):
        """Initialize with API key."""
        self.api_key = api_key
        self.headers = {
            "x-api-key": api_key,
            "Accept": "application/json"
        }

    def fetch_all_taxonomies(self) -> Dict[str, Any]:
        """Fetch the entire taxonomy tree."""
        endpoint = f"{self.BASE_URL}/application/seller-taxonomy/nodes"

        print("Fetching taxonomy tree from Etsy API...")
        response = requests.get(endpoint, headers=self.headers)

        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()

        return response.json()

    def flatten_taxonomy(self, taxonomy_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten the taxonomy tree into a list of nodes.

        Args:
            taxonomy_data: The raw API response

        Returns:
            List of taxonomy nodes with their paths
        """
        results = taxonomy_data.get("results", [])
        flattened = []

        def traverse(node, path=""):
            """Recursively traverse the taxonomy tree."""
            node_id = node.get("id")
            node_name = node.get("name", "")
            level = node.get("level", 0)
            parent_id = node.get("parent_id")
            full_path = f"{path} > {node_name}" if path else node_name

            flattened.append({
                "id": node_id,
                "name": node_name,
                "path": full_path,
                "level": level,
                "parent_id": parent_id
            })

            # Traverse children
            children = node.get("children", [])
            for child in children:
                traverse(child, full_path)

        # Start traversal from root nodes
        for node in results:
            traverse(node)

        return flattened

    def search_taxonomies(self, search_term: str, taxonomies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Search for taxonomies matching the search term.

        Args:
            search_term: The term to search for
            taxonomies: List of flattened taxonomies

        Returns:
            List of matching taxonomies
        """
        search_lower = search_term.lower()
        matches = []

        for tax in taxonomies:
            if search_lower in tax["name"].lower() or search_lower in tax["path"].lower():
                matches.append(tax)

        return matches

    def print_taxonomies(self, taxonomies: List[Dict[str, Any]], limit: int = None):
        """
        Pretty print taxonomy list.

        Args:
            taxonomies: List of taxonomies to print
            limit: Maximum number to display (None = all)
        """
        if not taxonomies:
            print("No taxonomies found.")
            return

        print("\n" + "="*80)
        print(f"Found {len(taxonomies)} categor{'ies' if len(taxonomies) != 1 else 'y'}")
        print("="*80)

        display_count = len(taxonomies) if limit is None else min(limit, len(taxonomies))

        for i, tax in enumerate(taxonomies[:display_count], 1):
            indent = "  " * tax["level"]
            print(f"\n{i}. {indent}ID: {tax['id']}")
            print(f"   {indent}Name: {tax['name']}")
            print(f"   {indent}Path: {tax['path']}")

        if limit and len(taxonomies) > limit:
            print(f"\n... and {len(taxonomies) - limit} more")
            print(f"\nTip: Use a more specific search term to narrow results")

    def list_top_level(self, taxonomies: List[Dict[str, Any]]):
        """List only top-level categories."""
        top_level = [t for t in taxonomies if t["level"] == 0]
        self.print_taxonomies(top_level)


def main():
    """Command-line entry point."""
    print("="*80)
    print("Etsy Taxonomy ID Finder")
    print("="*80)

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Get API key
    api_key = os.getenv("ETSY_API_KEY")
    if not api_key:
        print("\n❌ Error: ETSY_API_KEY environment variable not set")
        print("\nPlease set it with one of these methods:")
        print("  1. export ETSY_API_KEY='your_api_key_here'")
        print("  2. Create a .env file with: ETSY_API_KEY=your_api_key_here")
        sys.exit(1)

    try:
        # Fetch taxonomies
        finder = TaxonomyFinder(api_key)
        taxonomy_data = finder.fetch_all_taxonomies()
        all_taxonomies = finder.flatten_taxonomy(taxonomy_data)

        print(f"✓ Loaded {len(all_taxonomies)} total categories\n")

        # Check if user provided a search term
        if len(sys.argv) > 1:
            search_term = " ".join(sys.argv[1:])
            print(f"🔍 Searching for: '{search_term}'")

            matches = finder.search_taxonomies(search_term, all_taxonomies)
            finder.print_taxonomies(matches, limit=50)

            if matches:
                print("\n" + "="*80)
                print("💡 To fetch metadata for a category, use:")
                print(f"   python src/fetch_taxonomy_metadata.py <ID>")
                print("\nExample:")
                print(f"   python src/fetch_taxonomy_metadata.py {matches[0]['id']}")
        else:
            print("📋 Showing top-level categories (use a search term for more specific results)")
            finder.list_top_level(all_taxonomies)

            print("\n" + "="*80)
            print("💡 Usage:")
            print("   python src/find_taxonomy_id.py [search_term]")
            print("\nExamples:")
            print("   python src/find_taxonomy_id.py jewelry")
            print("   python src/find_taxonomy_id.py \"home decor\"")
            print("   python src/find_taxonomy_id.py clothing")

    except requests.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
