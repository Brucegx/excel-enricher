#!/usr/bin/env python3
"""
Etsy Taxonomy Metadata Fetcher - Main Entry Point

Fetches taxonomy metadata from Etsy API and outputs both JSON and Excel files.

Usage:
    python fetch_taxonomy_metadata.py <taxonomy_id>

Example:
    python fetch_taxonomy_metadata.py 1062
"""

import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from etsy_taxonomy_fetcher import EtsyTaxonomyFetcher
from excel_converter import convert_to_excel


def main():
    """Main entry point for the script."""
    print("="*60)
    print("Etsy Taxonomy Metadata Fetcher")
    print("="*60)

    # Check arguments
    if len(sys.argv) < 2:
        print("\n❌ Error: Missing taxonomy ID")
        print("\nUsage: python fetch_taxonomy_metadata.py <taxonomy_id>")
        print("\nExample: python fetch_taxonomy_metadata.py 1062")
        print("\nYou also need to set ETSY_API_KEY environment variable")
        print("  Option 1: export ETSY_API_KEY='your_api_key_here'")
        print("  Option 2: Create .env file with: ETSY_API_KEY=your_api_key_here")
        sys.exit(1)

    # Get taxonomy ID from command line
    try:
        taxonomy_id = int(sys.argv[1])
    except ValueError:
        print(f"\n❌ Error: Taxonomy ID must be an integer, got '{sys.argv[1]}'")
        sys.exit(1)

    # Load environment variables from .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Get API key from environment
    api_key = os.getenv("ETSY_API_KEY")
    if not api_key:
        print("\n❌ Error: ETSY_API_KEY environment variable not set")
        print("\nPlease set it with one of these methods:")
        print("  1. export ETSY_API_KEY='your_api_key_here'")
        print("  2. Create a .env file with: ETSY_API_KEY=your_api_key_here")
        print("\nTo get an API key:")
        print("  1. Go to https://www.etsy.com/developers/your-apps")
        print("  2. Create an app (or use existing)")
        print("  3. Copy the 'Keystring' value")
        sys.exit(1)

    print(f"\n📋 Fetching metadata for taxonomy ID: {taxonomy_id}")
    print("-"*60)

    try:
        # Step 1: Fetch from API and save as JSON
        print("\n[1/2] Fetching from Etsy API...")
        fetcher = EtsyTaxonomyFetcher(api_key)
        result = fetcher.get_metadata_for_taxonomy(taxonomy_id, output_dir="output")

        # Find the JSON file that was just created
        from datetime import datetime
        import glob

        pattern = f"output/taxonomy_{taxonomy_id}_*.json"
        json_files = sorted(glob.glob(pattern), reverse=True)

        if not json_files:
            print("❌ Error: JSON file was not created")
            sys.exit(1)

        json_path = json_files[0]  # Most recent file

        # Step 2: Convert to Excel
        print("\n[2/2] Converting to Excel...")
        excel_path = convert_to_excel(json_path)

        # Print summary
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"\nTaxonomy ID: {result['metadata']['taxonomy_id']}")
        print(f"Total Properties: {result['metadata']['total_properties']}")
        print(f"  ├─ Required: {result['metadata']['required_properties']}")
        print(f"  ├─ Optional: {result['metadata']['optional_properties']}")
        print(f"  └─ Enumerated: {result['metadata']['enumerated_properties']}")
        print("\nOutput Files:")
        print(f"  📄 JSON: {json_path}")
        print(f"  📊 Excel: {excel_path}")
        print("\n" + "="*60)

        # Show some examples
        if result['properties']:
            print("\n📌 Sample Properties:")
            print("-"*60)
            for prop in result['properties'][:5]:  # Show first 5
                req = "✓ REQUIRED" if prop['is_required'] else "  Optional"
                enum = f" | {prop['enumerated_values_count']} values" if prop['is_enumerated'] else ""
                print(f"  {req} | {prop['property_name']}{enum}")

            if len(result['properties']) > 5:
                print(f"  ... and {len(result['properties']) - 5} more")

        print("\n💡 Tip: Open the Excel file to see all properties with details!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
