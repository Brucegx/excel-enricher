#!/usr/bin/env python3
"""
Test/Demo Script with Sample Data

This demonstrates what the tool does using sample Etsy API response data.
No API key needed for this demo!
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from excel_converter import convert_to_excel


# Sample response data (simplified from actual Etsy API response)
SAMPLE_TAXONOMY_RESPONSE = {
    "count": 3,
    "results": [
        {
            "property_id": 46803063659,
            "name": "Primary color",
            "display_name": "Primary color",
            "description": "The main color of the item",
            "is_required": False,
            "is_multivalued": False,
            "supports_attributes": True,
            "supports_variations": True,
            "possible_values": [
                {"value_id": 1, "name": "Beige"},
                {"value_id": 2, "name": "Black"},
                {"value_id": 3, "name": "Blue"},
                {"value_id": 4, "name": "Brown"},
                {"value_id": 5, "name": "Gold"},
                {"value_id": 6, "name": "Gray"},
                {"value_id": 7, "name": "Green"},
                {"value_id": 8, "name": "Orange"},
                {"value_id": 9, "name": "Pink"},
                {"value_id": 10, "name": "Purple"},
                {"value_id": 11, "name": "Red"},
                {"value_id": 12, "name": "Silver"},
                {"value_id": 13, "name": "White"},
                {"value_id": 14, "name": "Yellow"},
                {"value_id": 15, "name": "Clear"}
            ]
        },
        {
            "property_id": 46803063660,
            "name": "Material",
            "display_name": "Material",
            "description": "The primary material of the item",
            "is_required": True,
            "is_multivalued": True,
            "max_values_allowed": 13,
            "supports_attributes": True,
            "supports_variations": False,
            "possible_values": [
                {"value_id": 100, "name": "Acrylic"},
                {"value_id": 101, "name": "Aluminum"},
                {"value_id": 102, "name": "Brass"},
                {"value_id": 103, "name": "Bronze"},
                {"value_id": 104, "name": "Ceramic"},
                {"value_id": 105, "name": "Copper"},
                {"value_id": 106, "name": "Crystal"},
                {"value_id": 107, "name": "Gold"},
                {"value_id": 108, "name": "Gold Filled"},
                {"value_id": 109, "name": "Gold Plated"},
                {"value_id": 110, "name": "Leather"},
                {"value_id": 111, "name": "Metal"},
                {"value_id": 112, "name": "Pearl"},
                {"value_id": 113, "name": "Plastic"},
                {"value_id": 114, "name": "Resin"},
                {"value_id": 115, "name": "Rose Gold"},
                {"value_id": 116, "name": "Rubber"},
                {"value_id": 117, "name": "Silver"},
                {"value_id": 118, "name": "Stainless Steel"},
                {"value_id": 119, "name": "Sterling Silver"},
                {"value_id": 120, "name": "Stone"},
                {"value_id": 121, "name": "Wood"}
            ]
        },
        {
            "property_id": 46803063661,
            "name": "Size",
            "display_name": "Size",
            "description": "The size of the jewelry item",
            "is_required": False,
            "is_multivalued": False,
            "supports_attributes": False,
            "supports_variations": True,
            "scales": [
                {
                    "scale_id": 1,
                    "display_name": "US Ring Size",
                    "description": "Standard US ring sizes"
                },
                {
                    "scale_id": 2,
                    "display_name": "EU Ring Size",
                    "description": "European ring sizes"
                }
            ],
            "possible_values": []
        },
        {
            "property_id": 46803063662,
            "name": "Occasion",
            "display_name": "Occasion",
            "description": "The occasion or event this item is suitable for",
            "is_required": False,
            "is_multivalued": True,
            "max_values_allowed": 5,
            "supports_attributes": True,
            "supports_variations": False,
            "possible_values": [
                {"value_id": 200, "name": "Anniversary"},
                {"value_id": 201, "name": "Birthday"},
                {"value_id": 202, "name": "Christmas"},
                {"value_id": 203, "name": "Graduation"},
                {"value_id": 204, "name": "Valentine's Day"},
                {"value_id": 205, "name": "Wedding"}
            ]
        },
        {
            "property_id": 46803063663,
            "name": "Style",
            "display_name": "Style",
            "description": "The style or aesthetic of the item",
            "is_required": False,
            "is_multivalued": False,
            "supports_attributes": True,
            "supports_variations": False,
            "possible_values": [
                {"value_id": 300, "name": "Art Deco"},
                {"value_id": 301, "name": "Bohemian"},
                {"value_id": 302, "name": "Minimalist"},
                {"value_id": 303, "name": "Modern"},
                {"value_id": 304, "name": "Rustic"},
                {"value_id": 305, "name": "Vintage"}
            ]
        },
        {
            "property_id": 46803063664,
            "name": "Personalization",
            "display_name": "Personalization",
            "description": "Custom text or engraving option",
            "is_required": False,
            "is_multivalued": False,
            "supports_attributes": True,
            "supports_variations": False,
            "possible_values": []  # Free text field
        }
    ]
}


def process_sample_data():
    """Process sample data and create outputs."""
    print("="*80)
    print("DEMO: Etsy Taxonomy Metadata Fetcher")
    print("="*80)
    print("\nThis demo shows what the tool does using SAMPLE DATA")
    print("(No API key needed for this demo!)")
    print("\n" + "-"*80)

    # Import the parser from our actual code
    from etsy_taxonomy_fetcher import EtsyTaxonomyFetcher

    # Create a dummy fetcher just to use its parsing methods
    fetcher = EtsyTaxonomyFetcher(api_key="demo_key")

    # Parse the properties
    parsed_properties = []
    for prop in SAMPLE_TAXONOMY_RESPONSE["results"]:
        parsed_properties.append(fetcher.parse_property(prop))

    # Create the structured output
    total_properties = len(parsed_properties)
    required_count = sum(1 for p in parsed_properties if p["is_required"])
    optional_count = total_properties - required_count
    enumerated_count = sum(1 for p in parsed_properties if p["is_enumerated"])

    result = {
        "metadata": {
            "taxonomy_id": 1062,  # Jewelry category
            "fetched_at": datetime.utcnow().isoformat(),
            "total_properties": total_properties,
            "required_properties": required_count,
            "optional_properties": optional_count,
            "enumerated_properties": enumerated_count
        },
        "properties": parsed_properties,
        "raw_response": SAMPLE_TAXONOMY_RESPONSE
    }

    # Create output directory
    Path("output").mkdir(exist_ok=True)

    # Save JSON
    json_path = "output/sample_taxonomy_1062_demo.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Sample JSON created: {json_path}")

    # Create Excel
    excel_path = "output/sample_taxonomy_1062_demo.xlsx"
    convert_to_excel(json_path, excel_path)
    print(f"✓ Sample Excel created: {excel_path}")

    # Print summary
    print("\n" + "="*80)
    print("SAMPLE DATA SUMMARY")
    print("="*80)
    print(f"\nTaxonomy ID: {result['metadata']['taxonomy_id']} (Jewelry)")
    print(f"Total Properties: {result['metadata']['total_properties']}")
    print(f"  ├─ Required: {result['metadata']['required_properties']}")
    print(f"  ├─ Optional: {result['metadata']['optional_properties']}")
    print(f"  └─ Enumerated: {result['metadata']['enumerated_properties']}")

    print("\n" + "-"*80)
    print("PROPERTY DETAILS:")
    print("-"*80)

    for prop in parsed_properties:
        req_label = "✓ REQUIRED" if prop['is_required'] else "  Optional"
        enum_info = f" | {prop['enumerated_values_count']} values" if prop['is_enumerated'] else " | Free text"
        multi = " | Multi-value" if prop.get('is_multivalued') else ""

        print(f"\n{req_label} | {prop['property_name']}{enum_info}{multi}")
        print(f"           Property ID: {prop['property_id']}")

        if prop.get('description'):
            print(f"           Description: {prop['description']}")

        if prop.get('max_values_allowed'):
            print(f"           Max values: {prop['max_values_allowed']}")

        if prop.get('scales'):
            print(f"           Has scales: {len(prop['scales'])} scale(s)")
            for scale in prop['scales']:
                print(f"             - {scale['scale_name']}")

        if prop['is_enumerated'] and prop['enumerated_values_count'] <= 10:
            print(f"           Values: {', '.join(v['name'] for v in prop['enumerated_values'])}")
        elif prop['is_enumerated']:
            sample_values = [v['name'] for v in prop['enumerated_values'][:5]]
            print(f"           Sample values: {', '.join(sample_values)}, ... (+{prop['enumerated_values_count']-5} more)")

    print("\n" + "="*80)
    print("WHAT YOU NEED TO USE THE REAL TOOL:")
    print("="*80)
    print("""
1. Etsy API Key (Keystring)
   - Go to: https://www.etsy.com/developers/your-apps
   - Create an app or use existing
   - Copy the 'Keystring' value
   - This is a public API key (no OAuth needed for taxonomy endpoints)

2. Taxonomy ID for your category
   - Use: python src/find_taxonomy_id.py "your category"
   - Or check common IDs in QUICKSTART.md
   - Examples: 1062 (Jewelry), 69150467 (Clothing), 843 (Home & Living)

3. Set the API key:
   Option A: export ETSY_API_KEY='your_keystring_here'
   Option B: Create .env file with: ETSY_API_KEY=your_keystring_here

4. Run the tool:
   python src/fetch_taxonomy_metadata.py <taxonomy_id>
""")

    print("="*80)
    print("📊 The Excel file has been created with:")
    print("  - Summary sheet with statistics")
    print("  - Properties sheet with all attributes")
    print("  - Enumerated Values sheet with all possible values")
    print("\n  Color coding:")
    print("    🟨 Yellow = Required property")
    print("    🟩 Green = Has enumerated values")
    print("="*80)

    return result


if __name__ == "__main__":
    try:
        process_sample_data()
        print("\n✅ Demo completed successfully!")
        print("\nOpen the files in output/ to see the results.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
