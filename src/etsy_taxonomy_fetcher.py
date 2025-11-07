"""
Etsy Taxonomy Metadata Fetcher

This script fetches all attribute metadata for a given Etsy taxonomy ID
and outputs the data as both JSON and Excel files.

Usage:
    python etsy_taxonomy_fetcher.py <taxonomy_id>
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class EtsyTaxonomyFetcher:
    """Fetches and processes Etsy taxonomy metadata."""

    BASE_URL = "https://openapi.etsy.com/v3"

    def __init__(self, api_key: str):
        """
        Initialize the fetcher with API credentials.

        Args:
            api_key: Etsy API key (from your Etsy app)
        """
        self.api_key = api_key
        self.headers = {
            "x-api-key": api_key,
            "Accept": "application/json"
        }

    def fetch_taxonomy_properties(self, taxonomy_id: int) -> Dict[str, Any]:
        """
        Fetch all properties for a given taxonomy ID.

        Args:
            taxonomy_id: The Etsy taxonomy/category ID

        Returns:
            Dict containing the API response

        Raises:
            requests.HTTPError: If the API request fails
        """
        endpoint = f"{self.BASE_URL}/application/seller-taxonomy/nodes/{taxonomy_id}/properties"

        print(f"Fetching properties for taxonomy ID: {taxonomy_id}")
        print(f"Endpoint: {endpoint}")

        response = requests.get(endpoint, headers=self.headers)

        # Raise an error for bad status codes
        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()

        return response.json()

    def parse_property(self, prop: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single property from the API response into a structured format.

        Args:
            prop: Raw property data from API

        Returns:
            Parsed property with standardized fields
        """
        # Extract enumerated values if they exist
        possible_values = prop.get("possible_values", [])
        is_enumerated = len(possible_values) > 0

        # Format enumerated values as a list
        enum_values = []
        if is_enumerated:
            for value in possible_values:
                if isinstance(value, dict):
                    # Handle both value_id + name format and other formats
                    value_id = value.get("value_id") or value.get("id")
                    name = value.get("name") or value.get("display_name")
                    enum_values.append({
                        "value_id": value_id,
                        "name": name
                    })
                else:
                    # Simple value format
                    enum_values.append({"name": str(value)})

        # Extract scales if they exist
        scales = prop.get("scales", [])
        scale_info = []
        if scales:
            for scale in scales:
                if isinstance(scale, dict):
                    scale_info.append({
                        "scale_id": scale.get("scale_id") or scale.get("id"),
                        "scale_name": scale.get("display_name") or scale.get("name"),
                        "description": scale.get("description", "")
                    })

        # Build the parsed property object
        parsed = {
            "property_id": prop.get("property_id"),
            "property_name": prop.get("name") or prop.get("display_name"),
            "display_name": prop.get("display_name") or prop.get("name"),
            "is_required": prop.get("is_required", False),
            "is_enumerated": is_enumerated,
            "enumerated_values": enum_values if is_enumerated else None,
            "enumerated_values_count": len(enum_values) if is_enumerated else 0,
            "description": prop.get("description", ""),
            "supports_attributes": prop.get("supports_attributes", False),
            "supports_variations": prop.get("supports_variations", False),
            "is_multivalued": prop.get("is_multivalued", False),
            "max_values_allowed": prop.get("max_values_allowed"),
            "scales": scale_info if scale_info else None,
            "raw_data": prop  # Keep original for reference
        }

        return parsed

    def process_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the API response and structure it for output.

        Args:
            response_data: Raw API response

        Returns:
            Structured data ready for JSON/Excel output
        """
        properties = response_data.get("results", [])

        if not properties:
            print("Warning: No properties found in response")

        parsed_properties = []
        for prop in properties:
            parsed_properties.append(self.parse_property(prop))

        # Summary statistics
        total_properties = len(parsed_properties)
        required_count = sum(1 for p in parsed_properties if p["is_required"])
        optional_count = total_properties - required_count
        enumerated_count = sum(1 for p in parsed_properties if p["is_enumerated"])

        result = {
            "metadata": {
                "taxonomy_id": response_data.get("taxonomy_id"),
                "fetched_at": datetime.utcnow().isoformat(),
                "total_properties": total_properties,
                "required_properties": required_count,
                "optional_properties": optional_count,
                "enumerated_properties": enumerated_count
            },
            "properties": parsed_properties,
            "raw_response": response_data
        }

        return result

    def save_json(self, data: Dict[str, Any], output_path: str) -> None:
        """
        Save processed data as JSON file.

        Args:
            data: Processed data dictionary
            output_path: Path to save JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✓ JSON saved to: {output_path}")

    def get_metadata_for_taxonomy(self, taxonomy_id: int, output_dir: str = "output") -> Dict[str, Any]:
        """
        Main method to fetch, parse, and save taxonomy metadata.

        Args:
            taxonomy_id: The Etsy taxonomy ID to fetch
            output_dir: Directory to save output files

        Returns:
            Processed data dictionary
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Fetch from API
        raw_response = self.fetch_taxonomy_properties(taxonomy_id)

        # Process the response
        processed_data = self.process_response(raw_response)

        # Save JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(output_dir, f"taxonomy_{taxonomy_id}_{timestamp}.json")
        self.save_json(processed_data, json_path)

        return processed_data


def main():
    """Command-line entry point."""
    if len(sys.argv) < 2:
        print("Usage: python etsy_taxonomy_fetcher.py <taxonomy_id>")
        print("\nExample: python etsy_taxonomy_fetcher.py 1234")
        print("\nYou also need to set ETSY_API_KEY environment variable or create a .env file")
        sys.exit(1)

    # Get taxonomy ID from command line
    try:
        taxonomy_id = int(sys.argv[1])
    except ValueError:
        print(f"Error: taxonomy_id must be an integer, got '{sys.argv[1]}'")
        sys.exit(1)

    # Get API key from environment
    api_key = os.getenv("ETSY_API_KEY")
    if not api_key:
        print("Error: ETSY_API_KEY environment variable not set")
        print("\nPlease set it with: export ETSY_API_KEY='your_api_key_here'")
        print("Or create a .env file with: ETSY_API_KEY=your_api_key_here")
        sys.exit(1)

    # Create fetcher and run
    try:
        fetcher = EtsyTaxonomyFetcher(api_key)
        result = fetcher.get_metadata_for_taxonomy(taxonomy_id)

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Taxonomy ID: {result['metadata']['taxonomy_id']}")
        print(f"Total Properties: {result['metadata']['total_properties']}")
        print(f"  - Required: {result['metadata']['required_properties']}")
        print(f"  - Optional: {result['metadata']['optional_properties']}")
        print(f"  - Enumerated: {result['metadata']['enumerated_properties']}")
        print("="*60)

    except requests.HTTPError as e:
        print(f"\nAPI Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Try to load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    main()
