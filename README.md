# Excel Enricher

AI-powered tool for enriching product Excel files with generated content using multiple LLM models.

## Features

- **Multi-Model Support**: Test and compare GPT-4o, Claude Sonnet 4, and Gemini 2.0 Flash
- **Template System**: Save and reuse Jinja2 prompt templates
- **Batch Processing**: Generate content for entire Excel files
- **Cost Tracking**: Monitor API costs with detailed logging
- **Image Support**: Extract and use embedded product images

## Setup

1. **Install dependencies** (use miniconda or virtualenv):
```bash
pip install -r requirements.txt
```

2. **Configure API keys**:
```bash
cp .streamlit/secrets_example.toml .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your actual API keys
```

Example `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_API_KEY = "..."
```

3. **Run the application**:
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Step 1: Upload Excel File

Upload your product Excel file in the sidebar. The file should contain:
- **Required columns**: `Item#`, `Section`
- **Optional columns**: `卖点`, `SEO Title Search`, `Item Description`, `Colors`, `Scent`, `Specification L*W*H`, `Weight（g）`, `Package size`
- **Embedded images**: One image per product row

### Step 2: Test Prompts (Lab Tab)

1. Select a sample product from the dropdown
2. Load an existing prompt template or create a new one
3. Select models to test (you can compare multiple models side-by-side)
4. Click "Run Test" to generate content
5. Compare results and costs
6. Save your best prompt with the best-performing model

**Jinja2 Template Variables Available**:
- `{{ item_number }}`
- `{{ section }}`
- `{{ selling_points_cn }}`
- `{{ seo_title }}`
- `{{ description }}`
- `{{ colors }}`
- `{{ scent }}`
- `{{ specification }}`
- `{{ weight }}`
- `{{ package_size }}`

### Step 3: Batch Processing (Batch Tab)

1. Select your production prompts for:
   - Title generation
   - Description generation
   - Tags generation
2. Click "Run Batch Generation"
3. Wait for processing to complete (progress bar will show)
4. Download the enriched Excel file

The output Excel will have three new columns:
- `Generated Title`
- `Generated Description`
- `Generated Tags`

### Cost Monitoring

View real-time cost tracking in the sidebar:
- Total monthly cost
- Number of API calls
- Cost breakdown by model

Detailed logs are saved in `logs/usage_YYYY-MM.jsonl`

## Project Structure

```
excel-enricher/
├── app.py                      # Main Streamlit application
├── services/                   # Backend services
│   ├── __init__.py
│   ├── data_service.py        # Excel loading/exporting with images
│   ├── prompt_service.py      # Template management
│   ├── llm_service.py         # LLM API integrations
│   └── monitoring.py          # Cost calculation and logging
├── prompts/                   # Jinja2 template library
│   ├── title/
│   │   └── v1.j2
│   ├── description/
│   │   └── v1.j2
│   └── tags/
│       └── v1.j2
├── logs/                      # Cost logs (auto-generated)
│   └── usage_YYYY-MM.jsonl
├── .streamlit/
│   ├── secrets.toml          # API keys (gitignored)
│   └── secrets_example.toml  # Template for secrets
├── requirements.txt
└── README.md
```

## Supported Models

| Model | Provider | Display Name | Notes |
|-------|----------|--------------|-------|
| `gpt-4o` | OpenAI | GPT-4o | $2.50/$10.00 per 1M tokens |
| `claude-sonnet-4` | Anthropic | Claude Sonnet 4 | $3.00/$15.00 per 1M tokens |
| `gemini-2.0-flash-exp` | Google | Gemini 2.0 Flash | Free tier (experimental) |

## Tips

1. **Start Small**: Test prompts on a few sample products before running batch processing
2. **Compare Models**: Different models excel at different tasks - test them side-by-side
3. **Iterate on Prompts**: Save multiple versions (v1, v2, v3) as you refine your templates
4. **Monitor Costs**: Check the sidebar regularly to track spending
5. **Backup Your Data**: Always keep a copy of your original Excel file

## Troubleshooting

**Error: "API key not found in secrets"**
- Make sure you've created `.streamlit/secrets.toml` and added your API keys

**Error: "No image found for this product"**
- Ensure your Excel file has embedded images (not just file paths)
- Images should be inserted directly into Excel cells

**Error loading Excel file**
- Verify your Excel file is in `.xlsx` format
- Check that required columns (`Item#`, `Section`) exist

## License

Internal tool - All rights reserved
