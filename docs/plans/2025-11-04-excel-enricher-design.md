# Excel Enricher - Complete Design Document

**Date:** 2025-11-04
**Status:** Approved for Implementation

## Overview

A Streamlit tool for enriching product Excel files with AI-generated content. Users test prompts against samples in a Lab environment, then run batch processing using the best-performing models.

---

## User Workflow

### Setup
```bash
streamlit run app.py
```

### Step 1: Lab Tab (Experimentation)
1. Upload Excel file with product data and embedded images
2. Select a sample product from dropdown
3. Load or write a Jinja2 prompt template
4. Test against multiple LLM models (GPT-4o, Claude Sonnet 4, Gemini 2 Flash)
5. Compare results side-by-side
6. Select the best-performing model
7. Save prompt template with model preference

### Step 2: Batch Tab (Production)
1. Select production prompts for title, description, and tags
2. System auto-loads each prompt's preferred model (can differ per field)
3. Click "Run Batch" to process all products
4. Monitor progress bar
5. Download enriched Excel with 3 new columns appended

---

## Excel File Structure

### Input Columns (Example)
- `Item#` - Product SKU (required)
- `PIC` - Embedded image column (required, one image per product)
- `卖点` - Selling points in Chinese (required)
- `Section` - Product category (required)
- `Scent` - Product scent
- `Colors` - Available colors
- Plus ~20 other columns (pricing, SEO, inventory, etc.)

### Output
All original columns preserved + 3 new columns:
- `Generated Title`
- `Generated Description`
- `Generated Tags`

---

## Architecture

### Project Structure
```
excel-enricher/
├── app.py                      # Main Streamlit UI
├── services/
│   ├── data_service.py         # Excel parsing & export
│   ├── prompt_service.py       # Template management
│   ├── llm_service.py          # Unified LLM interface
│   └── monitoring.py           # Cost tracking
├── prompts/
│   ├── title/
│   │   ├── v1.j2              # Template
│   │   └── v1.json            # {"model": "gpt-4o"}
│   ├── description/
│   └── tags/
├── logs/
│   └── costs.jsonl            # Cost tracking log
├── .streamlit/
│   └── secrets.toml           # API keys (not committed)
├── docs/
│   └── plans/
└── requirements.txt
```

### Data Flow
1. **Upload** → `data_service.load_products()` → List of Product objects
2. **Lab testing** → `prompt_service.render_prompt()` → `llm_service.generate()` → Results
3. **Batch processing** → Loop all products → Generate 3 fields each → Export
4. **Download** → `data_service.export_enriched_excel()` → Excel bytes

---

## Component Details

### Product Object
```python
@dataclass
class Product:
    item_number: str
    selling_points: str      # 卖点
    section: str
    colors: str
    scent: str
    image_bytes: bytes       # Extracted from PIC column
    _original_row: dict      # For export
```

### data_service.py

**`load_products(uploaded_file) -> List[Product]`**
- Uses pandas for tabular data
- Uses openpyxl for embedded image extraction from PIC column
- Matches images to rows by position
- Validates required fields (Item#, PIC, 卖点, Section)
- Returns Product objects

**`export_enriched_excel(products, generated_data) -> bytes`**
- Appends 3 new columns to original Excel
- Preserves all formatting and original data
- Returns bytes for download

**Error Handling:**
- Missing columns → Show clear error, don't proceed
- Missing images → Skip products with warning
- Invalid format → User-friendly error message

### prompt_service.py

**Available Template Variables:**
- `{{ item_number }}`
- `{{ selling_points }}` (卖点)
- `{{ section }}`
- `{{ colors }}`
- `{{ scent }}`
- Image passed separately to LLM

**Functions:**

**`list_prompts(category=None) -> List[str]`**
- Scans prompts/ directory
- Returns paths like `["title/v1.j2", "description/v2.j2"]`
- Optional category filter

**`get_prompt_content(path: str) -> str`**
- Reads .j2 template file
- Returns raw Jinja2 template

**`get_prompt_config(path: str) -> dict`**
- Reads corresponding .json file (e.g., `title/v1.json`)
- Returns `{"model": "gpt-4o"}`
- Fallback: Returns `{}` if missing

**`save_prompt(path: str, content: str, model: str)`**
- Saves template to `{path}.j2`
- Saves config to `{path}.json` with model preference
- Creates parent directories
- Validates safe paths (no `../`)

**`render_prompt(template_string: str, product: Product) -> str`**
- Uses Jinja2 to substitute variables
- Returns ready-to-send prompt

### llm_service.py

**Supported Models:**
```python
MODELS = {
    "gpt-4o": {
        "provider": "openai",
        "api_model": "gpt-4o"
    },
    "claude-sonnet-4": {
        "provider": "anthropic",
        "api_model": "claude-3-5-sonnet-20241022"
    },
    "gemini-2-flash": {
        "provider": "google",
        "api_model": "gemini-2.0-flash-exp"
    }
}
```

**`generate(model_name: str, prompt: str, image_bytes: bytes) -> dict`**
- Returns: `{"text": str, "input_tokens": int, "output_tokens": int, "model": str}`
- Reads API keys from `st.secrets`
- Provider-specific formatting:
  - OpenAI: base64 data URL in messages
  - Anthropic: base64 in content blocks
  - Google: PIL Image or bytes
- Error handling:
  - Rate limits → Retry with backoff (1s, 2s, 4s)
  - Missing API key → Clear error
  - Timeout (>60s) → Cancel with message
  - Empty response → Log and show error

### monitoring.py

**`log_cost(model: str, input_tokens: int, output_tokens: int, context: str)`**
- Appends to `logs/costs.jsonl`
- Entry format: `{"timestamp": "ISO8601", "model": str, "input_tokens": int, "output_tokens": int, "cost_usd": float, "context": str}`
- Context: "experimental" (Lab) or "batch" (Production)

**`get_monthly_summary() -> dict`**
- Reads and aggregates costs.jsonl
- Returns: `{"2025-11": {"total": 12.45, "by_model": {...}, "by_context": {...}}}`

**Pricing (Nov 2024):**
```python
COSTS = {
    "gpt-4o": {"input": 2.50, "output": 10.00},  # per 1M tokens
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "gemini-2-flash": {"input": 0.075, "output": 0.30}
}
```

**UI Integration:**
- Silent logging (no interruptions)
- Optional: Sidebar expander with monthly summary

---

## UI Implementation

### Sidebar
- File uploader (.xlsx, .xls)
- Status: "✓ Loaded N products"
- Optional: Cost summary expander

### Lab Tab (🔬 Test & Save Prompts)

**Layout:**
1. **Select Sample Product** - Dropdown of all Item# values
2. **View Product** - Image + data table (5 fields)
3. **Load/Edit Prompt**:
   - Dropdown: "Load existing prompt"
   - Text area: Editable Jinja2 template
   - Helper text: Available variables
4. **Select Models** - Multi-select (all 3 models)
5. **Test Button** - Triggers generation
6. **Results Display**:
   - Side-by-side columns (one per model)
   - Shows: text, token counts, response time
7. **Select Best Model** - Dropdown: "Which model for this prompt?"
8. **Save Prompt**:
   - Text input: "Save as..." (e.g., "title/v2")
   - Button saves both .j2 and .json

**State Management:**
- `st.session_state` for uploaded file, products, test results

### Batch Tab (🏭 Run & Download)

**Layout:**
1. **Select Prompts** (3 dropdowns):
   - Title Prompt → Lists `prompts/title/*.j2`
   - Description Prompt → Lists `prompts/description/*.j2`
   - Tags Prompt → Lists `prompts/tags/*.j2`
   - Shows model for each: "(uses gpt-4o)"
2. **Run Batch Button**
3. **Progress Display**:
   - Progress bar: X/N products
   - Status: "Processing SKU-1234 (15/100)..."
4. **Results**:
   - Success message
   - Preview table (first 5 rows)
   - Download button: `products_enriched_2025-11-04.xlsx`

**Processing:**
- Sequential (avoid rate limits)
- For each product: render 3 prompts → call LLM 3 times → collect
- Log costs with context="batch"
- Continue on errors, log failed SKUs

---

## Error Handling

### Excel Issues
- Missing required columns → List missing, block processing
- Empty file → "No products found"
- Missing images → Skip products, show warnings
- Corrupted file → User-friendly error

### Prompt Issues
- Invalid Jinja2 → Show syntax error with line number
- Empty prompt → Warn before testing

### API Issues
- Rate limits → Auto-retry with backoff
- Invalid/missing key → Setup instructions
- Timeout → Cancel and notify
- Empty response → Log and show error

### Batch Processing
- Partial failures → Continue, log failed items, download partial
- User cancels → Stop button, save progress

### File System
- Save conflicts → Confirm overwrite
- Invalid names → Sanitize (no `../`, special chars)

---

## Testing & Deployment

### Local Setup
```bash
# Install
pip install streamlit pandas openpyxl jinja2 openai anthropic google-generativeai pillow

# Configure
mkdir -p .streamlit
cat > .streamlit/secrets.toml << EOF
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_API_KEY = "..."
EOF

# Initialize
mkdir -p prompts/{title,description,tags} logs

# Run
streamlit run app.py
```

### Initial Templates
Create starter templates:
- `prompts/title/v1.j2` + `v1.json`
- `prompts/description/v1.j2` + `v1.json`
- `prompts/tags/v1.j2` + `v1.json`

### Manual Testing
- ✓ Upload Excel
- ✓ Test all 3 models
- ✓ Save with model preference
- ✓ Run batch (5-10 products)
- ✓ Verify enriched Excel
- ✓ Check cost logs

### Deployment Options
- **Local**: `streamlit run app.py`
- **Streamlit Cloud**: Deploy to share
- **Docker**: Containerize

### Security
- `.gitignore`: Add `secrets.toml`, `logs/`
- Never commit API keys
- Cost logs safe to commit (no sensitive data)

---

## Success Criteria

1. Users can upload Excel and see products loaded
2. Lab tab allows testing prompts against 3 models
3. Users can save prompts with model preferences
4. Batch tab processes all products with correct models per field
5. Download provides enriched Excel with 3 new columns
6. Costs logged silently to JSONL
7. All errors handled gracefully with clear messages

---

## Future Enhancements (Out of Scope)

- Parallel batch processing with rate limiting
- Prompt version history/git integration
- A/B testing framework for prompts
- Custom model parameters (temperature, max_tokens)
- Real-time cost display in UI
- Support for additional LLM providers
