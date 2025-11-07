# Etsy Taxonomy Metadata Fetcher

A tool to fetch and export Etsy listing attribute metadata for any product category (taxonomy).

## 🎯 What It Does

Instead of manually opening Etsy listings and screenshotting attributes one by one, this tool:

1. **Fetches** all required/optional attributes for a specific product category via Etsy API
2. **Exports** the data as both **JSON** and **Excel** formats
3. **Provides** detailed information about each attribute:
   - Attribute name
   - Whether it's required or optional
   - Whether it has enumerated (predefined) values
   - All possible enumeration values with their IDs
   - Descriptions and additional metadata

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Etsy API Key (see setup below)

### Installation

```bash
# Clone or navigate to the project directory
cd excel-enricher

# Install dependencies
pip install -r requirements.txt
```

### Setup Etsy API Key

1. Go to [Etsy Developers Portal](https://www.etsy.com/developers/your-apps)
2. Create a new app or use an existing one
3. Copy the **Keystring** (this is your API key)
4. Set the environment variable:

**Option 1: Using .env file (recommended)**
```bash
# Create a .env file in the project root
echo "ETSY_API_KEY=your_api_key_here" > .env
```

**Option 2: Export in terminal**
```bash
export ETSY_API_KEY='your_api_key_here'
```

### Usage

```bash
# Basic usage
python src/fetch_taxonomy_metadata.py <taxonomy_id>

# Example: Fetch metadata for taxonomy ID 1062 (Jewelry category)
python src/fetch_taxonomy_metadata.py 1062
```

### Output

The tool creates two files in the `output/` directory:

1. **JSON file**: `taxonomy_<id>_<timestamp>.json`
   - Complete structured data
   - Raw API response included
   - Machine-readable format

2. **Excel file**: `taxonomy_<id>_<timestamp>.xlsx`
   - Three sheets:
     - **Summary**: Overview and statistics
     - **Properties**: All attributes with details
     - **Enumerated Values**: All possible values for each enumerated attribute
   - Color-coded (yellow = required, green = has enumerations)
   - Sortable and filterable

## 📊 Example Output Structure

### JSON Format

```json
{
  "metadata": {
    "taxonomy_id": 1062,
    "fetched_at": "2025-11-07T16:30:00",
    "total_properties": 45,
    "required_properties": 8,
    "optional_properties": 37,
    "enumerated_properties": 15
  },
  "properties": [
    {
      "property_id": 46803063659,
      "property_name": "Primary color",
      "display_name": "Primary color",
      "is_required": false,
      "is_enumerated": true,
      "enumerated_values": [
        {"value_id": 1, "name": "Beige"},
        {"value_id": 2, "name": "Black"},
        {"value_id": 3, "name": "Blue"}
      ],
      "enumerated_values_count": 3,
      "description": "The main color of the item",
      "supports_attributes": true,
      "supports_variations": true,
      "is_multivalued": false,
      "max_values_allowed": null,
      "scales": null
    }
  ]
}
```

### Excel Format

**Properties Sheet:**
| Property ID | Property Name | Required? | Enumerated? | Enum Count | Description |
|-------------|---------------|-----------|-------------|------------|-------------|
| 46803063659 | Primary color | NO        | YES         | 15         | The main... |
| 46803063660 | Material      | YES       | YES         | 42         | The prima...|

**Enumerated Values Sheet:**
| Property ID | Property Name | Value ID | Value Name |
|-------------|---------------|----------|------------|
| 46803063659 | Primary color | 1        | Beige      |
| 46803063659 | Primary color | 2        | Black      |
| 46803063659 | Primary color | 3        | Blue       |

## 🔍 How to Find Taxonomy IDs

### Method 1: Use Etsy's Seller Taxonomy Browser

```bash
# You can create a script to fetch all taxonomy categories
# For now, here are some common ones:
```

**Common Taxonomy IDs:**
- `1062` - Jewelry
- `69150467` - Clothing
- `843` - Home & Living
- `562` - Art & Collectibles
- `66` - Bath & Beauty
- `1063` - Bags & Purses

### Method 2: Browse via Etsy API

The taxonomy hierarchy can be fetched using:
```
GET https://openapi.etsy.com/v3/application/seller-taxonomy/nodes
```

You can create a helper script to explore the full taxonomy tree if needed.

## 📁 Project Structure

```
excel-enricher/
├── src/
│   ├── fetch_taxonomy_metadata.py  # Main entry point
│   ├── etsy_taxonomy_fetcher.py    # API fetching logic
│   └── excel_converter.py          # Excel export logic
├── output/                          # Generated files go here
├── requirements.txt                 # Python dependencies
├── .env                            # Your API key (create this)
└── README.md                       # This file
```

## 🛠️ Advanced Usage

### Using Individual Modules

**Fetch only (JSON output):**
```bash
python src/etsy_taxonomy_fetcher.py 1062
```

**Convert existing JSON to Excel:**
```bash
python src/excel_converter.py output/taxonomy_1062_20251107_163000.json
```

### Programmatic Usage

```python
from src.etsy_taxonomy_fetcher import EtsyTaxonomyFetcher
from src.excel_converter import convert_to_excel

# Fetch data
fetcher = EtsyTaxonomyFetcher(api_key="your_key")
result = fetcher.get_metadata_for_taxonomy(1062)

# Convert to Excel
convert_to_excel("output/taxonomy_1062.json")
```

## 🔐 Authentication

The Etsy API v3 requires:
- **x-api-key** header with your API key (no OAuth needed for taxonomy endpoints)
- Public endpoints don't require user authorization
- Rate limits apply (check Etsy API documentation)

## 🐛 Troubleshooting

### Error: "ETSY_API_KEY environment variable not set"
**Solution:** Create a `.env` file or export the variable as shown in Setup section.

### Error: "API returned status code 404"
**Solution:** The taxonomy ID doesn't exist. Try a different ID or check if it's valid.

### Error: "API returned status code 401"
**Solution:** Your API key is invalid or expired. Get a new one from Etsy Developers Portal.

### Error: "No properties found in response"
**Solution:** The taxonomy might be too generic or have no properties. Try a more specific category.

## 📚 API Documentation

- [Etsy Open API v3 Documentation](https://developer.etsy.com/documentation/reference/)
- [Taxonomy Endpoints](https://developer.etsy.com/documentation/reference/#tag/SellerTaxonomy)
- [Get Your API Key](https://www.etsy.com/developers/your-apps)

## 🎯 Next Steps

This tool currently focuses on **fetching metadata**. Future enhancements could include:

1. **Listing Upload**: Create listings programmatically using the fetched metadata
2. **Bulk Operations**: Process multiple taxonomies at once
3. **AI Integration**: Auto-populate attributes using GPT/Claude
4. **Validation**: Verify listing data against taxonomy requirements
5. **Template Generator**: Create listing templates based on metadata

## 💡 Use Cases

1. **Research**: Understand what attributes are needed before creating listings
2. **Automation**: Build tools to bulk-create listings with proper attributes
3. **Documentation**: Keep a reference of all available attributes for your categories
4. **AI Training**: Use the structured data to train AI models for listing generation
5. **Validation**: Ensure your listings have all required attributes

## 📄 License

This project is for educational and personal use. Make sure to comply with Etsy's API Terms of Service.

## 🤝 Contributing

Feel free to open issues or submit pull requests for improvements!

---

**Made to solve the problem of manually screenshotting Etsy listing attributes!** 🎉
