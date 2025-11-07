# Quick Start Guide

## 3 Steps to Get Etsy Listing Metadata

### Step 1: Setup (One-time)

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
cp .env.example .env
# Edit .env and add your Etsy API key
```

**Get your Etsy API Key:**
1. Go to https://www.etsy.com/developers/your-apps
2. Create an app (or use existing)
3. Copy the **Keystring** value

### Step 2: Find Your Category's Taxonomy ID

```bash
# Search for your category
python src/find_taxonomy_id.py jewelry
python src/find_taxonomy_id.py "home decor"
python src/find_taxonomy_id.py clothing
```

**Example output:**
```
Found 15 categories
================================================================================

1. ID: 1062
   Name: Jewelry
   Path: Accessories > Jewelry

2. ID: 1063
   Name: Necklaces
   Path: Accessories > Jewelry > Necklaces
```

### Step 3: Fetch Metadata

```bash
# Use the taxonomy ID you found
python src/fetch_taxonomy_metadata.py 1062
```

**You'll get:**
- 📄 JSON file: `output/taxonomy_1062_<timestamp>.json`
- 📊 Excel file: `output/taxonomy_1062_<timestamp>.xlsx`

## Excel File Contents

The Excel file has 3 sheets:

1. **Summary** - Overview and statistics
2. **Properties** - All attributes with:
   - Property ID and name
   - Required vs optional
   - Enumerated vs free-text
   - Number of possible values
   - Descriptions
3. **Enumerated Values** - All possible values for each enumerated field

## What to Do with the Data

Now you have ALL the attributes Etsy requires/accepts for your category!

**Instead of:**
1. ❌ Opening Etsy listing page
2. ❌ Screenshotting each attribute section
3. ❌ Asking GPT to interpret screenshots
4. ❌ Manually filling in values
5. ❌ Repeating for each listing

**You can:**
1. ✅ Open the Excel file once
2. ✅ Feed all attributes to GPT in one go
3. ✅ Automate listing creation
4. ✅ Validate your data before uploading

## Common Taxonomy IDs

| ID | Category |
|----|----------|
| 1062 | Jewelry |
| 69150467 | Clothing |
| 843 | Home & Living |
| 562 | Art & Collectibles |
| 66 | Bath & Beauty |
| 1063 | Bags & Purses |

## Troubleshooting

**"ETSY_API_KEY environment variable not set"**
→ Create `.env` file with `ETSY_API_KEY=your_key_here`

**"API returned status code 404"**
→ Invalid taxonomy ID, use `find_taxonomy_id.py` to find the right one

**"No properties found"**
→ Try a more specific subcategory

## Next Steps

- 📖 Read the full [README.md](README.md) for advanced usage
- 🔧 Check out the [DESIGN.md](DESIGN.md) for technical details
- 🤖 Integrate with GPT API for automated listing generation
- 📦 Build bulk upload functionality

---

**That's it! No more manual screenshotting!** 🎉
