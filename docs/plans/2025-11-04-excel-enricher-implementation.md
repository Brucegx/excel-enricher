# Excel Enricher Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Streamlit tool that enriches Excel product files with AI-generated content (titles, descriptions, tags) using vision-capable LLMs.

**Architecture:** Service-oriented design with clear separation: data layer handles Excel I/O and image extraction, prompt layer manages Jinja2 templates, LLM layer provides unified interface to OpenAI/Anthropic/Google, and Streamlit UI orchestrates testing and batch workflows.

**Tech Stack:** Streamlit, pandas, openpyxl, Jinja2, OpenAI SDK, Anthropic SDK, Google Generative AI SDK, Pillow

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `README.md`
- Create: `.streamlit/secrets.toml.example`

**Step 1: Create requirements.txt**

```txt
streamlit==1.29.0
pandas==2.1.3
openpyxl==3.1.2
Jinja2==3.1.2
openai==1.3.7
anthropic==0.7.7
google-generativeai==0.3.1
Pillow==10.1.0
```

**Step 2: Create README.md**

```markdown
# Excel Enricher

AI-powered tool for enriching product Excel files with generated content.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API keys:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your API keys
```

3. Run:
```bash
streamlit run app.py
```

## Usage

1. Upload Excel file with products (must have: Item#, PIC, 卖点, Section columns)
2. Test prompts in Lab tab
3. Run batch processing in Batch tab
4. Download enriched Excel

## Project Structure

- `app.py` - Main Streamlit UI
- `services/` - Backend services
  - `data_service.py` - Excel handling
  - `prompt_service.py` - Template management
  - `llm_service.py` - LLM interface
  - `monitoring.py` - Cost tracking
- `prompts/` - Jinja2 templates
- `logs/` - Cost logs
```

**Step 3: Create secrets example file**

```toml
# Copy this to .streamlit/secrets.toml and add your API keys

OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_API_KEY = "..."
```

**Step 4: Create directory structure**

Run:
```bash
mkdir -p services prompts/{title,description,tags} logs tests
touch services/__init__.py
```

**Step 5: Commit**

```bash
git add requirements.txt README.md .streamlit/secrets.toml.example services/ prompts/ logs/ tests/
git commit -m "feat: initialize project structure with dependencies"
```

---

## Task 2: Data Service - Product Model

**Files:**
- Create: `services/data_service.py`
- Create: `tests/test_data_service.py`

**Step 1: Write failing test for Product dataclass**

Create `tests/test_data_service.py`:

```python
import pytest
from services.data_service import Product


def test_product_creation():
    """Test Product dataclass can be instantiated with required fields"""
    product = Product(
        item_number="SKU-001",
        selling_points="Great product",
        section="Electronics",
        colors="Red, Blue",
        scent="None",
        image_bytes=b"fake_image_data",
        original_row={"Item#": "SKU-001", "卖点": "Great product"}
    )

    assert product.item_number == "SKU-001"
    assert product.selling_points == "Great product"
    assert product.section == "Electronics"
    assert product.colors == "Red, Blue"
    assert product.scent == "None"
    assert product.image_bytes == b"fake_image_data"
    assert product.original_row["Item#"] == "SKU-001"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_service.py::test_product_creation -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'services.data_service'"

**Step 3: Write minimal Product dataclass**

Create `services/data_service.py`:

```python
"""Data service for handling Excel files and Product objects."""
from dataclasses import dataclass
from typing import Dict, List, Any
import io


@dataclass
class Product:
    """Represents a product with text fields and embedded image."""
    item_number: str
    selling_points: str  # 卖点
    section: str
    colors: str
    scent: str
    image_bytes: bytes
    original_row: Dict[str, Any]  # For export
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_data_service.py::test_product_creation -v`

Expected: PASS (1 passed)

**Step 5: Commit**

```bash
git add services/data_service.py tests/test_data_service.py
git commit -m "feat: add Product dataclass for representing products"
```

---

## Task 3: Data Service - Excel Loading

**Files:**
- Modify: `services/data_service.py`
- Modify: `tests/test_data_service.py`

**Step 1: Write failing test for load_products**

Add to `tests/test_data_service.py`:

```python
from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image
from services.data_service import load_products


def test_load_products_from_excel():
    """Test loading products from Excel with embedded images"""
    # Create test Excel with openpyxl (for images)
    wb = Workbook()
    ws = wb.active

    # Add headers
    ws['A1'] = 'Item#'
    ws['B1'] = 'PIC'
    ws['C1'] = '卖点'
    ws['D1'] = 'Section'
    ws['E1'] = 'Colors'
    ws['F1'] = 'Scent'

    # Add data row
    ws['A2'] = 'SKU-001'
    ws['C2'] = 'Great product'
    ws['D2'] = 'Electronics'
    ws['E2'] = 'Red'
    ws['F2'] = 'None'

    # Create and embed a small test image
    img = Image.new('RGB', (10, 10), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    openpyxl_img = OpenpyxlImage(img_bytes)
    ws.add_image(openpyxl_img, 'B2')

    # Save to BytesIO
    excel_bytes = BytesIO()
    wb.save(excel_bytes)
    excel_bytes.seek(0)

    # Test loading
    products = load_products(excel_bytes)

    assert len(products) == 1
    assert products[0].item_number == 'SKU-001'
    assert products[0].selling_points == 'Great product'
    assert products[0].section == 'Electronics'
    assert len(products[0].image_bytes) > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_service.py::test_load_products_from_excel -v`

Expected: FAIL with "ImportError: cannot import name 'load_products'"

**Step 3: Write minimal load_products implementation**

Add to `services/data_service.py`:

```python
import pandas as pd
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image


def load_products(uploaded_file) -> List[Product]:
    """
    Load products from Excel file with embedded images.

    Args:
        uploaded_file: File-like object (BytesIO or UploadedFile)

    Returns:
        List of Product objects

    Raises:
        ValueError: If required columns are missing
    """
    # Read text data with pandas
    df = pd.read_excel(uploaded_file, engine='openpyxl')

    # Validate required columns
    required_cols = ['Item#', 'PIC', '卖点', 'Section']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

    # Reset file pointer for openpyxl
    uploaded_file.seek(0)

    # Load workbook for images
    wb = load_workbook(uploaded_file)
    ws = wb.active

    # Extract images (assumes images are in column B, starting from row 2)
    images = {}
    for img in ws._images:
        # Get row number from anchor
        row = img.anchor._from.row + 1  # openpyxl is 0-indexed
        if row > 1:  # Skip header
            # Convert image to bytes
            img_bytes = img._data()
            images[row] = img_bytes

    # Build Product objects
    products = []
    for idx, row in df.iterrows():
        excel_row = idx + 2  # Excel rows start at 1, header is row 1

        # Skip if no image
        if excel_row not in images:
            continue

        product = Product(
            item_number=str(row['Item#']),
            selling_points=str(row.get('卖点', '')),
            section=str(row.get('Section', '')),
            colors=str(row.get('Colors', '')),
            scent=str(row.get('Scent', '')),
            image_bytes=images[excel_row],
            original_row=row.to_dict()
        )
        products.append(product)

    return products
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_data_service.py::test_load_products_from_excel -v`

Expected: PASS (2 passed)

**Step 5: Commit**

```bash
git add services/data_service.py tests/test_data_service.py
git commit -m "feat: implement load_products for Excel with images"
```

---

## Task 4: Data Service - Excel Export

**Files:**
- Modify: `services/data_service.py`
- Modify: `tests/test_data_service.py`

**Step 1: Write failing test for export_enriched_excel**

Add to `tests/test_data_service.py`:

```python
from services.data_service import export_enriched_excel


def test_export_enriched_excel():
    """Test exporting products with generated columns"""
    # Create test product
    product = Product(
        item_number="SKU-001",
        selling_points="Great product",
        section="Electronics",
        colors="Red",
        scent="None",
        image_bytes=b"fake",
        original_row={
            "Item#": "SKU-001",
            "卖点": "Great product",
            "Section": "Electronics",
            "Colors": "Red",
            "Scent": "None"
        }
    )

    # Generated data
    generated_data = [{
        "Generated Title": "Amazing Electronics",
        "Generated Description": "This is a great product",
        "Generated Tags": "electronics, red, new"
    }]

    # Export
    excel_bytes = export_enriched_excel([product], generated_data)

    # Verify output
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0

    # Read back and verify columns
    df = pd.read_excel(BytesIO(excel_bytes))
    assert "Generated Title" in df.columns
    assert "Generated Description" in df.columns
    assert "Generated Tags" in df.columns
    assert df.iloc[0]["Generated Title"] == "Amazing Electronics"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_service.py::test_export_enriched_excel -v`

Expected: FAIL with "ImportError: cannot import name 'export_enriched_excel'"

**Step 3: Write export_enriched_excel implementation**

Add to `services/data_service.py`:

```python
def export_enriched_excel(products: List[Product], generated_data: List[Dict[str, str]]) -> bytes:
    """
    Export products with generated columns to Excel.

    Args:
        products: List of Product objects
        generated_data: List of dicts with generated fields

    Returns:
        Excel file as bytes
    """
    # Build DataFrame from original rows
    rows = [p.original_row for p in products]
    df = pd.DataFrame(rows)

    # Add generated columns
    gen_df = pd.DataFrame(generated_data)
    df = pd.concat([df, gen_df], axis=1)

    # Write to bytes
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return output.getvalue()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_data_service.py::test_export_enriched_excel -v`

Expected: PASS (3 passed)

**Step 5: Commit**

```bash
git add services/data_service.py tests/test_data_service.py
git commit -m "feat: implement export_enriched_excel for adding generated columns"
```

---

## Task 5: Prompt Service - Template Management

**Files:**
- Create: `services/prompt_service.py`
- Create: `tests/test_prompt_service.py`

**Step 1: Write failing test for list_prompts**

Create `tests/test_prompt_service.py`:

```python
import pytest
import os
from pathlib import Path
from services.prompt_service import list_prompts


def test_list_prompts(tmp_path):
    """Test listing prompt template files"""
    # Create test prompt structure
    prompts_dir = tmp_path / "prompts"
    (prompts_dir / "title").mkdir(parents=True)
    (prompts_dir / "description").mkdir(parents=True)

    (prompts_dir / "title" / "v1.j2").write_text("Title prompt")
    (prompts_dir / "title" / "v2.j2").write_text("Title prompt v2")
    (prompts_dir / "description" / "v1.j2").write_text("Desc prompt")

    # Test listing all
    prompts = list_prompts(str(prompts_dir))
    assert len(prompts) == 3
    assert "title/v1.j2" in prompts
    assert "title/v2.j2" in prompts
    assert "description/v1.j2" in prompts

    # Test filtering by category
    title_prompts = list_prompts(str(prompts_dir), category="title")
    assert len(title_prompts) == 2
    assert all("title/" in p for p in title_prompts)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_prompt_service.py::test_list_prompts -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'services.prompt_service'"

**Step 3: Write prompt_service with list_prompts**

Create `services/prompt_service.py`:

```python
"""Prompt service for managing Jinja2 templates."""
from pathlib import Path
from typing import List, Optional, Dict
from jinja2 import Template


def list_prompts(prompts_dir: str = "prompts", category: Optional[str] = None) -> List[str]:
    """
    List all prompt template files.

    Args:
        prompts_dir: Base prompts directory
        category: Optional category to filter (e.g., "title")

    Returns:
        List of relative paths (e.g., ["title/v1.j2", ...])
    """
    base_path = Path(prompts_dir)

    if not base_path.exists():
        return []

    # Find all .j2 files
    if category:
        pattern = f"{category}/**/*.j2"
    else:
        pattern = "**/*.j2"

    prompts = []
    for file_path in base_path.glob(pattern):
        relative_path = file_path.relative_to(base_path)
        prompts.append(str(relative_path))

    return sorted(prompts)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_prompt_service.py::test_list_prompts -v`

Expected: PASS (1 passed)

**Step 5: Commit**

```bash
git add services/prompt_service.py tests/test_prompt_service.py
git commit -m "feat: implement list_prompts for discovering templates"
```

---

## Task 6: Prompt Service - Template Read/Write

**Files:**
- Modify: `services/prompt_service.py`
- Modify: `tests/test_prompt_service.py`

**Step 1: Write failing tests for get/save prompt**

Add to `tests/test_prompt_service.py`:

```python
from services.prompt_service import get_prompt_content, get_prompt_config, save_prompt


def test_get_prompt_content(tmp_path):
    """Test reading prompt template content"""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    template_path = prompts_dir / "title" / "v1.j2"
    template_path.parent.mkdir(parents=True)
    template_path.write_text("Generate title for {{ item_number }}")

    content = get_prompt_content(str(prompts_dir), "title/v1.j2")
    assert content == "Generate title for {{ item_number }}"


def test_get_prompt_config(tmp_path):
    """Test reading prompt config JSON"""
    prompts_dir = tmp_path / "prompts"
    config_path = prompts_dir / "title" / "v1.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text('{"model": "gpt-4o"}')

    config = get_prompt_config(str(prompts_dir), "title/v1")
    assert config["model"] == "gpt-4o"

    # Test missing config
    config = get_prompt_config(str(prompts_dir), "title/v2")
    assert config == {}


def test_save_prompt(tmp_path):
    """Test saving prompt template and config"""
    prompts_dir = tmp_path / "prompts"

    save_prompt(
        prompts_dir=str(prompts_dir),
        path="title/v1",
        content="Generate title for {{ item_number }}",
        model="claude-sonnet-4"
    )

    # Verify .j2 file
    template_path = prompts_dir / "title" / "v1.j2"
    assert template_path.exists()
    assert template_path.read_text() == "Generate title for {{ item_number }}"

    # Verify .json file
    config_path = prompts_dir / "title" / "v1.json"
    assert config_path.exists()
    assert '"model": "claude-sonnet-4"' in config_path.read_text()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_prompt_service.py::test_get_prompt_content -v`

Expected: FAIL with "ImportError: cannot import name 'get_prompt_content'"

**Step 3: Implement get/save functions**

Add to `services/prompt_service.py`:

```python
import json


def get_prompt_content(prompts_dir: str, path: str) -> str:
    """
    Read prompt template content.

    Args:
        prompts_dir: Base prompts directory
        path: Relative path (e.g., "title/v1.j2")

    Returns:
        Template content as string
    """
    file_path = Path(prompts_dir) / path

    if not file_path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")

    return file_path.read_text()


def get_prompt_config(prompts_dir: str, path: str) -> Dict[str, str]:
    """
    Read prompt config JSON.

    Args:
        prompts_dir: Base prompts directory
        path: Relative path WITHOUT extension (e.g., "title/v1")

    Returns:
        Config dict (e.g., {"model": "gpt-4o"}) or {} if not found
    """
    config_path = Path(prompts_dir) / f"{path}.json"

    if not config_path.exists():
        return {}

    return json.loads(config_path.read_text())


def save_prompt(prompts_dir: str, path: str, content: str, model: str):
    """
    Save prompt template and config.

    Args:
        prompts_dir: Base prompts directory
        path: Relative path WITHOUT extension (e.g., "title/v1")
        content: Template content
        model: Model name for config
    """
    base_path = Path(prompts_dir)

    # Validate path (no directory traversal)
    if ".." in path:
        raise ValueError("Invalid path: cannot contain '..'")

    # Save template
    template_path = base_path / f"{path}.j2"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(content)

    # Save config
    config_path = base_path / f"{path}.json"
    config = {"model": model}
    config_path.write_text(json.dumps(config, indent=2))
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_prompt_service.py -v`

Expected: PASS (4 passed)

**Step 5: Commit**

```bash
git add services/prompt_service.py tests/test_prompt_service.py
git commit -m "feat: implement prompt template read/write operations"
```

---

## Task 7: Prompt Service - Template Rendering

**Files:**
- Modify: `services/prompt_service.py`
- Modify: `tests/test_prompt_service.py`

**Step 1: Write failing test for render_prompt**

Add to `tests/test_prompt_service.py`:

```python
from services.prompt_service import render_prompt
from services.data_service import Product


def test_render_prompt():
    """Test rendering Jinja2 template with product data"""
    product = Product(
        item_number="SKU-001",
        selling_points="High quality product",
        section="Electronics",
        colors="Red, Blue",
        scent="None",
        image_bytes=b"fake",
        original_row={}
    )

    template = """Generate a title for product {{ item_number }}.
Section: {{ section }}
Selling points: {{ selling_points }}
Colors: {{ colors }}"""

    result = render_prompt(template, product)

    assert "SKU-001" in result
    assert "Electronics" in result
    assert "High quality product" in result
    assert "Red, Blue" in result
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_prompt_service.py::test_render_prompt -v`

Expected: FAIL with "ImportError: cannot import name 'render_prompt'"

**Step 3: Implement render_prompt**

Add to `services/prompt_service.py`:

```python
def render_prompt(template_string: str, product) -> str:
    """
    Render Jinja2 template with product data.

    Args:
        template_string: Jinja2 template
        product: Product object

    Returns:
        Rendered prompt string
    """
    template = Template(template_string)

    return template.render(
        item_number=product.item_number,
        selling_points=product.selling_points,
        section=product.section,
        colors=product.colors,
        scent=product.scent
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_prompt_service.py::test_render_prompt -v`

Expected: PASS (5 passed)

**Step 5: Commit**

```bash
git add services/prompt_service.py tests/test_prompt_service.py
git commit -m "feat: implement render_prompt for Jinja2 template rendering"
```

---

## Task 8: LLM Service - Model Configuration

**Files:**
- Create: `services/llm_service.py`
- Create: `tests/test_llm_service.py`

**Step 1: Write failing test for model config**

Create `tests/test_llm_service.py`:

```python
import pytest
from services.llm_service import MODELS, get_model_config


def test_model_config():
    """Test model configuration dictionary"""
    assert "gpt-4o" in MODELS
    assert "claude-sonnet-4" in MODELS
    assert "gemini-2-flash" in MODELS

    assert MODELS["gpt-4o"]["provider"] == "openai"
    assert MODELS["claude-sonnet-4"]["provider"] == "anthropic"
    assert MODELS["gemini-2-flash"]["provider"] == "google"


def test_get_model_config():
    """Test getting model configuration"""
    config = get_model_config("gpt-4o")
    assert config["provider"] == "openai"
    assert "api_model" in config

    with pytest.raises(ValueError):
        get_model_config("invalid-model")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_service.py::test_model_config -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'services.llm_service'"

**Step 3: Create llm_service with model config**

Create `services/llm_service.py`:

```python
"""LLM service for unified interface to multiple providers."""
from typing import Dict, Any
import base64
from io import BytesIO


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


def get_model_config(model_name: str) -> Dict[str, str]:
    """
    Get configuration for a model.

    Args:
        model_name: Model name (e.g., "gpt-4o")

    Returns:
        Model config dict

    Raises:
        ValueError: If model not found
    """
    if model_name not in MODELS:
        raise ValueError(f"Unknown model: {model_name}")

    return MODELS[model_name]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_service.py -v`

Expected: PASS (2 passed)

**Step 5: Commit**

```bash
git add services/llm_service.py tests/test_llm_service.py
git commit -m "feat: add LLM service with model configuration"
```

---

## Task 9: LLM Service - OpenAI Integration

**Files:**
- Modify: `services/llm_service.py`
- Modify: `tests/test_llm_service.py`

**Step 1: Write test for OpenAI generation (will be mocked)**

Add to `tests/test_llm_service.py`:

```python
from unittest.mock import Mock, patch
from services.llm_service import generate


@patch('services.llm_service.openai')
def test_generate_openai(mock_openai):
    """Test generating with OpenAI model"""
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Generated title"))]
    mock_response.usage = Mock(prompt_tokens=100, completion_tokens=20)
    mock_openai.OpenAI.return_value.chat.completions.create.return_value = mock_response

    # Mock secrets
    secrets = {"OPENAI_API_KEY": "sk-test"}

    result = generate(
        model_name="gpt-4o",
        prompt="Generate a title",
        image_bytes=b"fake_image",
        secrets=secrets
    )

    assert result["text"] == "Generated title"
    assert result["input_tokens"] == 100
    assert result["output_tokens"] == 20
    assert result["model"] == "gpt-4o"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_service.py::test_generate_openai -v`

Expected: FAIL with "ImportError: cannot import name 'generate'"

**Step 3: Implement generate function with OpenAI**

Add to `services/llm_service.py`:

```python
import openai
from openai import OpenAI


def generate(model_name: str, prompt: str, image_bytes: bytes, secrets: Dict[str, str]) -> Dict[str, Any]:
    """
    Generate text using specified LLM model.

    Args:
        model_name: Model name (e.g., "gpt-4o")
        prompt: Text prompt
        image_bytes: Image as bytes
        secrets: Dict with API keys

    Returns:
        {
            "text": str,
            "input_tokens": int,
            "output_tokens": int,
            "model": str
        }
    """
    config = get_model_config(model_name)
    provider = config["provider"]

    if provider == "openai":
        return _generate_openai(config["api_model"], prompt, image_bytes, secrets)
    elif provider == "anthropic":
        return _generate_anthropic(config["api_model"], prompt, image_bytes, secrets)
    elif provider == "google":
        return _generate_google(config["api_model"], prompt, image_bytes, secrets)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _generate_openai(model: str, prompt: str, image_bytes: bytes, secrets: Dict[str, str]) -> Dict[str, Any]:
    """Generate using OpenAI API."""
    api_key = secrets.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in secrets")

    client = OpenAI(api_key=api_key)

    # Encode image as base64 data URL
    img_b64 = base64.b64encode(image_bytes).decode()
    data_url = f"data:image/png;base64,{img_b64}"

    # Make API call
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ],
        max_tokens=500
    )

    return {
        "text": response.choices[0].message.content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "model": model
    }


def _generate_anthropic(model: str, prompt: str, image_bytes: bytes, secrets: Dict[str, str]) -> Dict[str, Any]:
    """Generate using Anthropic API."""
    # Placeholder - will implement in next task
    raise NotImplementedError("Anthropic integration not yet implemented")


def _generate_google(model: str, prompt: str, image_bytes: bytes, secrets: Dict[str, str]) -> Dict[str, Any]:
    """Generate using Google API."""
    # Placeholder - will implement in next task
    raise NotImplementedError("Google integration not yet implemented")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_service.py::test_generate_openai -v`

Expected: PASS (3 passed)

**Step 5: Commit**

```bash
git add services/llm_service.py tests/test_llm_service.py
git commit -m "feat: implement OpenAI integration for text generation"
```

---

## Task 10: LLM Service - Anthropic Integration

**Files:**
- Modify: `services/llm_service.py`
- Modify: `tests/test_llm_service.py`

**Step 1: Write test for Anthropic generation**

Add to `tests/test_llm_service.py`:

```python
@patch('services.llm_service.anthropic')
def test_generate_anthropic(mock_anthropic):
    """Test generating with Anthropic model"""
    # Mock Anthropic response
    mock_response = Mock()
    mock_response.content = [Mock(text="Generated description")]
    mock_response.usage = Mock(input_tokens=150, output_tokens=30)
    mock_anthropic.Anthropic.return_value.messages.create.return_value = mock_response

    secrets = {"ANTHROPIC_API_KEY": "sk-ant-test"}

    result = generate(
        model_name="claude-sonnet-4",
        prompt="Generate a description",
        image_bytes=b"fake_image",
        secrets=secrets
    )

    assert result["text"] == "Generated description"
    assert result["input_tokens"] == 150
    assert result["output_tokens"] == 30
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_service.py::test_generate_anthropic -v`

Expected: FAIL (NotImplementedError or assertion error)

**Step 3: Implement Anthropic integration**

Update `_generate_anthropic` in `services/llm_service.py`:

```python
import anthropic
from anthropic import Anthropic


def _generate_anthropic(model: str, prompt: str, image_bytes: bytes, secrets: Dict[str, str]) -> Dict[str, Any]:
    """Generate using Anthropic API."""
    api_key = secrets.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in secrets")

    client = Anthropic(api_key=api_key)

    # Encode image as base64
    img_b64 = base64.b64encode(image_bytes).decode()

    # Determine media type (assume PNG, could detect from bytes)
    media_type = "image/png"

    # Make API call
    response = client.messages.create(
        model=model,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )

    return {
        "text": response.content[0].text,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "model": model
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_service.py::test_generate_anthropic -v`

Expected: PASS (4 passed)

**Step 5: Commit**

```bash
git add services/llm_service.py tests/test_llm_service.py
git commit -m "feat: implement Anthropic integration for text generation"
```

---

## Task 11: LLM Service - Google Integration

**Files:**
- Modify: `services/llm_service.py`
- Modify: `tests/test_llm_service.py`

**Step 1: Write test for Google generation**

Add to `tests/test_llm_service.py`:

```python
@patch('services.llm_service.genai')
def test_generate_google(mock_genai):
    """Test generating with Google model"""
    # Mock Google response
    mock_response = Mock()
    mock_response.text = "Generated tags"
    mock_response.usage_metadata = Mock(
        prompt_token_count=120,
        candidates_token_count=25
    )
    mock_model = Mock()
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    secrets = {"GOOGLE_API_KEY": "test-key"}

    result = generate(
        model_name="gemini-2-flash",
        prompt="Generate tags",
        image_bytes=b"fake_image",
        secrets=secrets
    )

    assert result["text"] == "Generated tags"
    assert result["input_tokens"] == 120
    assert result["output_tokens"] == 25
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_service.py::test_generate_google -v`

Expected: FAIL (NotImplementedError or assertion error)

**Step 3: Implement Google integration**

Update `_generate_google` in `services/llm_service.py`:

```python
import google.generativeai as genai
from PIL import Image


def _generate_google(model: str, prompt: str, image_bytes: bytes, secrets: Dict[str, str]) -> Dict[str, Any]:
    """Generate using Google Generative AI API."""
    api_key = secrets.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in secrets")

    genai.configure(api_key=api_key)

    # Convert bytes to PIL Image
    img = Image.open(BytesIO(image_bytes))

    # Create model and generate
    client = genai.GenerativeModel(model)
    response = client.generate_content([prompt, img])

    return {
        "text": response.text,
        "input_tokens": response.usage_metadata.prompt_token_count,
        "output_tokens": response.usage_metadata.candidates_token_count,
        "model": model
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_service.py -v`

Expected: PASS (5 passed)

**Step 5: Commit**

```bash
git add services/llm_service.py tests/test_llm_service.py
git commit -m "feat: implement Google Generative AI integration"
```

---

## Task 12: Monitoring Service - Cost Calculation

**Files:**
- Create: `services/monitoring.py`
- Create: `tests/test_monitoring.py`

**Step 1: Write failing test for cost calculation**

Create `tests/test_monitoring.py`:

```python
import pytest
from services.monitoring import COSTS, calculate_cost


def test_cost_configuration():
    """Test cost configuration exists for all models"""
    assert "gpt-4o" in COSTS
    assert "claude-sonnet-4" in COSTS
    assert "gemini-2-flash" in COSTS

    assert "input" in COSTS["gpt-4o"]
    assert "output" in COSTS["gpt-4o"]


def test_calculate_cost():
    """Test cost calculation"""
    # GPT-4o: $2.50 per 1M input, $10.00 per 1M output
    cost = calculate_cost("gpt-4o", input_tokens=1000, output_tokens=500)
    expected = (1000 * 2.50 / 1_000_000) + (500 * 10.00 / 1_000_000)
    assert abs(cost - expected) < 0.0001

    # Claude Sonnet 4
    cost = calculate_cost("claude-sonnet-4", input_tokens=2000, output_tokens=300)
    expected = (2000 * 3.00 / 1_000_000) + (300 * 15.00 / 1_000_000)
    assert abs(cost - expected) < 0.0001

    # Gemini (much cheaper)
    cost = calculate_cost("gemini-2-flash", input_tokens=1000, output_tokens=500)
    expected = (1000 * 0.075 / 1_000_000) + (500 * 0.30 / 1_000_000)
    assert abs(cost - expected) < 0.00001
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_monitoring.py::test_calculate_cost -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'services.monitoring'"

**Step 3: Create monitoring service with cost calculation**

Create `services/monitoring.py`:

```python
"""Monitoring service for cost tracking."""
from typing import Dict
from datetime import datetime
import json
from pathlib import Path


# Pricing per 1M tokens (as of Nov 2024)
COSTS = {
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00
    },
    "claude-sonnet-4": {
        "input": 3.00,
        "output": 15.00
    },
    "gemini-2-flash": {
        "input": 0.075,
        "output": 0.30
    }
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost in USD for token usage.

    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    if model not in COSTS:
        return 0.0

    pricing = COSTS[model]
    input_cost = (input_tokens * pricing["input"]) / 1_000_000
    output_cost = (output_tokens * pricing["output"]) / 1_000_000

    return input_cost + output_cost
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_monitoring.py -v`

Expected: PASS (2 passed)

**Step 5: Commit**

```bash
git add services/monitoring.py tests/test_monitoring.py
git commit -m "feat: implement cost calculation for LLM usage"
```

---

## Task 13: Monitoring Service - Cost Logging

**Files:**
- Modify: `services/monitoring.py`
- Modify: `tests/test_monitoring.py`

**Step 1: Write failing test for log_cost**

Add to `tests/test_monitoring.py`:

```python
import json
from services.monitoring import log_cost


def test_log_cost(tmp_path):
    """Test logging cost to JSONL file"""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    log_cost(
        logs_dir=str(logs_dir),
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=200,
        context="experimental"
    )

    # Verify log file created
    log_file = logs_dir / "costs.jsonl"
    assert log_file.exists()

    # Verify content
    lines = log_file.read_text().strip().split('\n')
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["model"] == "gpt-4o"
    assert entry["input_tokens"] == 1000
    assert entry["output_tokens"] == 200
    assert entry["context"] == "experimental"
    assert "timestamp" in entry
    assert "cost_usd" in entry

    # Log another entry
    log_cost(
        logs_dir=str(logs_dir),
        model="claude-sonnet-4",
        input_tokens=500,
        output_tokens=100,
        context="batch"
    )

    # Verify appended
    lines = log_file.read_text().strip().split('\n')
    assert len(lines) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_monitoring.py::test_log_cost -v`

Expected: FAIL with "ImportError: cannot import name 'log_cost'"

**Step 3: Implement log_cost function**

Add to `services/monitoring.py`:

```python
def log_cost(logs_dir: str, model: str, input_tokens: int, output_tokens: int, context: str):
    """
    Log cost to JSONL file.

    Args:
        logs_dir: Directory for log files
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        context: Context string ("experimental" or "batch")
    """
    logs_path = Path(logs_dir)
    logs_path.mkdir(parents=True, exist_ok=True)

    log_file = logs_path / "costs.jsonl"

    # Calculate cost
    cost = calculate_cost(model, input_tokens, output_tokens)

    # Create log entry
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost, 6),
        "context": context
    }

    # Append to file
    with log_file.open('a') as f:
        f.write(json.dumps(entry) + '\n')
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_monitoring.py -v`

Expected: PASS (3 passed)

**Step 5: Commit**

```bash
git add services/monitoring.py tests/test_monitoring.py
git commit -m "feat: implement cost logging to JSONL file"
```

---

## Task 14: Monitoring Service - Monthly Summary

**Files:**
- Modify: `services/monitoring.py`
- Modify: `tests/test_monitoring.py`

**Step 1: Write failing test for monthly summary**

Add to `tests/test_monitoring.py`:

```python
from services.monitoring import get_monthly_summary


def test_get_monthly_summary(tmp_path):
    """Test getting monthly cost summary"""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    # Create test log entries
    log_cost(logs_dir=str(logs_dir), model="gpt-4o", input_tokens=1000, output_tokens=200, context="experimental")
    log_cost(logs_dir=str(logs_dir), model="gpt-4o", input_tokens=2000, output_tokens=300, context="batch")
    log_cost(logs_dir=str(logs_dir), model="claude-sonnet-4", input_tokens=1500, output_tokens=250, context="batch")

    # Get summary
    summary = get_monthly_summary(str(logs_dir))

    # Verify structure
    current_month = datetime.utcnow().strftime("%Y-%m")
    assert current_month in summary

    month_data = summary[current_month]
    assert "total" in month_data
    assert "by_model" in month_data
    assert "by_context" in month_data

    # Verify aggregations
    assert "gpt-4o" in month_data["by_model"]
    assert "claude-sonnet-4" in month_data["by_model"]
    assert "experimental" in month_data["by_context"]
    assert "batch" in month_data["by_context"]

    # Verify total is sum of all costs
    total_by_model = sum(month_data["by_model"].values())
    assert abs(month_data["total"] - total_by_model) < 0.0001
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_monitoring.py::test_get_monthly_summary -v`

Expected: FAIL with "ImportError: cannot import name 'get_monthly_summary'"

**Step 3: Implement get_monthly_summary function**

Add to `services/monitoring.py`:

```python
from collections import defaultdict


def get_monthly_summary(logs_dir: str) -> Dict[str, Dict]:
    """
    Get monthly cost summary from logs.

    Args:
        logs_dir: Directory containing cost logs

    Returns:
        {
            "2025-11": {
                "total": 12.45,
                "by_model": {"gpt-4o": 8.20, ...},
                "by_context": {"experimental": 3.45, ...}
            },
            ...
        }
    """
    logs_path = Path(logs_dir)
    log_file = logs_path / "costs.jsonl"

    if not log_file.exists():
        return {}

    # Aggregate by month
    monthly_data = defaultdict(lambda: {
        "total": 0.0,
        "by_model": defaultdict(float),
        "by_context": defaultdict(float)
    })

    with log_file.open('r') as f:
        for line in f:
            entry = json.loads(line)

            # Extract month from timestamp
            timestamp = entry["timestamp"]
            month = timestamp[:7]  # "2025-11"

            cost = entry["cost_usd"]
            model = entry["model"]
            context = entry["context"]

            # Aggregate
            monthly_data[month]["total"] += cost
            monthly_data[month]["by_model"][model] += cost
            monthly_data[month]["by_context"][context] += cost

    # Convert defaultdicts to regular dicts
    result = {}
    for month, data in monthly_data.items():
        result[month] = {
            "total": round(data["total"], 4),
            "by_model": dict(data["by_model"]),
            "by_context": dict(data["by_context"])
        }

    return result
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_monitoring.py -v`

Expected: PASS (4 passed)

**Step 5: Commit**

```bash
git add services/monitoring.py tests/test_monitoring.py
git commit -m "feat: implement monthly cost summary aggregation"
```

---

## Task 15: Initial Prompt Templates

**Files:**
- Create: `prompts/title/v1.j2`
- Create: `prompts/title/v1.json`
- Create: `prompts/description/v1.j2`
- Create: `prompts/description/v1.json`
- Create: `prompts/tags/v1.j2`
- Create: `prompts/tags/v1.json`

**Step 1: Create title prompt template**

Create `prompts/title/v1.j2`:

```jinja2
You are a product title generator for e-commerce listings.

Product Information:
- Item Number: {{ item_number }}
- Section: {{ section }}
- Selling Points: {{ selling_points }}
- Colors: {{ colors }}
- Scent: {{ scent }}

Generate a clear, SEO-friendly product title (max 150 characters) based on the image and product information provided.

Requirements:
- Include key product features
- Be descriptive but concise
- Optimize for search engines
- Focus on what's visible in the image

Return only the title, no explanation.
```

Create `prompts/title/v1.json`:

```json
{
  "model": "gpt-4o"
}
```

**Step 2: Create description prompt template**

Create `prompts/description/v1.j2`:

```jinja2
You are a product description writer for e-commerce listings.

Product Information:
- Item Number: {{ item_number }}
- Section: {{ section }}
- Selling Points: {{ selling_points }}
- Colors: {{ colors }}
- Scent: {{ scent }}

Generate a detailed product description (150-300 words) based on the image and product information.

Requirements:
- Highlight key features and benefits
- Describe what's visible in the image
- Include relevant specifications
- Use persuasive but factual language
- Format with short paragraphs

Return only the description, no explanation.
```

Create `prompts/description/v1.json`:

```json
{
  "model": "claude-sonnet-4"
}
```

**Step 3: Create tags prompt template**

Create `prompts/tags/v1.j2`:

```jinja2
You are a product tagging specialist for e-commerce.

Product Information:
- Item Number: {{ item_number }}
- Section: {{ section }}
- Selling Points: {{ selling_points }}
- Colors: {{ colors }}
- Scent: {{ scent }}

Generate 5-10 relevant product tags based on the image and information.

Requirements:
- Use lowercase
- Focus on: category, features, use cases, attributes
- Be specific and searchable
- Separate with commas

Example format: electronics, wireless, bluetooth, portable, red

Return only the comma-separated tags, no explanation.
```

Create `prompts/tags/v1.json`:

```json
{
  "model": "gemini-2-flash"
}
```

**Step 4: Verify files created**

Run: `ls -R prompts/`

Expected: See all 6 files organized in subdirectories

**Step 5: Commit**

```bash
git add prompts/
git commit -m "feat: add initial v1 prompt templates for title, description, tags"
```

---

## Task 16: Streamlit App - Basic Structure

**Files:**
- Create: `app.py`

**Step 1: Create basic app structure with imports**

Create `app.py`:

```python
"""Excel Enricher - AI-powered product content generation."""
import streamlit as st
from services.data_service import load_products, export_enriched_excel
from services.prompt_service import list_prompts, get_prompt_content, get_prompt_config, save_prompt, render_prompt
from services.llm_service import generate
from services.monitoring import log_cost


def main():
    st.set_page_config(
        page_title="Excel Enricher",
        page_icon="✨",
        layout="wide"
    )

    st.title("✨ Excel Enricher")
    st.markdown("AI-powered product content generation")

    # Initialize session state
    if 'products' not in st.session_state:
        st.session_state.products = None
    if 'test_results' not in st.session_state:
        st.session_state.test_results = {}

    # Sidebar for file upload
    with st.sidebar:
        st.header("Upload")
        uploaded_file = st.file_uploader(
            "Upload Excel File",
            type=["xlsx", "xls"],
            help="Excel file must contain: Item#, PIC, 卖点, Section"
        )

        if uploaded_file:
            if st.session_state.products is None:
                with st.spinner("Loading products..."):
                    try:
                        products = load_products(uploaded_file)
                        st.session_state.products = products
                        st.success(f"✓ Loaded {len(products)} products")
                    except Exception as e:
                        st.error(f"Error loading file: {e}")

    # Main content
    if st.session_state.products is None:
        st.info("👈 Upload an Excel file to get started")
        return

    # Tabs
    tab1, tab2 = st.tabs(["🔬 Lab (Test & Save)", "🏭 Batch (Run & Download)"])

    with tab1:
        render_lab_tab()

    with tab2:
        render_batch_tab()


def render_lab_tab():
    """Render the Lab tab for testing prompts."""
    st.header("Lab: Test Prompts")
    st.write("TODO: Implement lab functionality")


def render_batch_tab():
    """Render the Batch tab for production runs."""
    st.header("Batch: Generate Content")
    st.write("TODO: Implement batch functionality")


if __name__ == "__main__":
    main()
```

**Step 2: Test app runs**

Run: `streamlit run app.py`

Expected: App opens in browser, shows upload UI

**Step 3: Stop app**

Press Ctrl+C in terminal

**Step 4: Commit**

```bash
git add app.py
git commit -m "feat: create basic Streamlit app structure with upload"
```

---

## Task 17: Streamlit App - Lab Tab UI

**Files:**
- Modify: `app.py`

**Step 1: Implement Lab tab UI**

Replace `render_lab_tab()` in `app.py`:

```python
def render_lab_tab():
    """Render the Lab tab for testing prompts."""
    products = st.session_state.products

    st.header("🔬 Lab: Test & Save Prompts")

    # Step 1: Select sample product
    st.subheader("1. Select Sample Product")
    product_options = [p.item_number for p in products]
    selected_sku = st.selectbox("Product", product_options, key="lab_product")

    # Find selected product
    product = next(p for p in products if p.item_number == selected_sku)

    # Display product info
    col1, col2 = st.columns([1, 2])

    with col1:
        st.image(product.image_bytes, caption=product.item_number, use_column_width=True)

    with col2:
        st.markdown("**Product Details:**")
        st.markdown(f"- **Item #:** {product.item_number}")
        st.markdown(f"- **Section:** {product.section}")
        st.markdown(f"- **Selling Points:** {product.selling_points}")
        st.markdown(f"- **Colors:** {product.colors}")
        st.markdown(f"- **Scent:** {product.scent}")

    st.divider()

    # Step 2: Load/Edit prompt
    st.subheader("2. Load or Edit Prompt")

    col1, col2 = st.columns([1, 2])

    with col1:
        available_prompts = ["(New prompt)"] + list_prompts()
        selected_prompt = st.selectbox("Load existing prompt", available_prompts, key="load_prompt")

        # Load prompt content if selected
        if selected_prompt != "(New prompt)":
            prompt_content = get_prompt_content("prompts", selected_prompt)
        else:
            prompt_content = "Write your prompt here...\n\nAvailable variables:\n{{ item_number }}\n{{ selling_points }}\n{{ section }}\n{{ colors }}\n{{ scent }}"

    with col2:
        st.info("💡 Use Jinja2 syntax: {{ variable_name }}")

    # Step 3: Edit prompt
    st.subheader("3. Edit Prompt")
    prompt_text = st.text_area(
        "Prompt Template",
        value=prompt_content,
        height=200,
        key="prompt_editor"
    )

    st.divider()

    # Step 4: Select models
    st.subheader("4. Select Models to Test")
    models = st.multiselect(
        "Models",
        options=["gpt-4o", "claude-sonnet-4", "gemini-2-flash"],
        default=["gpt-4o"],
        key="test_models"
    )

    # Step 5: Test button
    if st.button("🧪 Run Test", type="primary", use_container_width=True):
        if not models:
            st.error("Please select at least one model")
        else:
            run_test(product, prompt_text, models)

    # Display results
    if st.session_state.test_results:
        st.divider()
        st.subheader("Results")
        display_test_results()

    # Step 6: Save prompt
    if st.session_state.test_results:
        st.divider()
        st.subheader("5. Save Prompt")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            save_path = st.text_input(
                "Save as",
                placeholder="e.g., title/v2",
                key="save_path"
            )

        with col2:
            model_for_save = st.selectbox(
                "Best model",
                options=models,
                key="save_model"
            )

        with col3:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("💾 Save", use_container_width=True):
                if save_path:
                    try:
                        save_prompt("prompts", save_path, prompt_text, model_for_save)
                        st.success(f"✓ Saved as {save_path}.j2 with model {model_for_save}")
                    except Exception as e:
                        st.error(f"Error saving: {e}")
                else:
                    st.error("Please enter a save path")


def run_test(product, prompt_text, models):
    """Run test with selected models."""
    st.session_state.test_results = {}

    # Render prompt
    try:
        rendered_prompt = render_prompt(prompt_text, product)
    except Exception as e:
        st.error(f"Error rendering prompt: {e}")
        return

    # Test each model
    for model in models:
        with st.spinner(f"Testing {model}..."):
            try:
                result = generate(
                    model_name=model,
                    prompt=rendered_prompt,
                    image_bytes=product.image_bytes,
                    secrets=st.secrets
                )

                # Log cost
                log_cost(
                    logs_dir="logs",
                    model=model,
                    input_tokens=result["input_tokens"],
                    output_tokens=result["output_tokens"],
                    context="experimental"
                )

                st.session_state.test_results[model] = result
            except Exception as e:
                st.session_state.test_results[model] = {"error": str(e)}


def display_test_results():
    """Display test results side-by-side."""
    results = st.session_state.test_results

    cols = st.columns(len(results))

    for idx, (model, result) in enumerate(results.items()):
        with cols[idx]:
            st.markdown(f"**{model}**")

            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                st.markdown(result["text"])
                st.caption(f"Tokens: {result['input_tokens']} in, {result['output_tokens']} out")
```

**Step 2: Test Lab tab**

Run: `streamlit run app.py`

Expected: Lab tab shows product selector, prompt editor, model selector (may need secrets for actual testing)

**Step 3: Stop app and commit**

```bash
git add app.py
git commit -m "feat: implement Lab tab UI for testing prompts"
```

---

## Task 18: Streamlit App - Batch Tab UI

**Files:**
- Modify: `app.py`

**Step 1: Implement Batch tab UI**

Replace `render_batch_tab()` in `app.py`:

```python
def render_batch_tab():
    """Render the Batch tab for production runs."""
    st.header("🏭 Batch: Generate Content")

    st.subheader("1. Select Prompts")

    col1, col2, col3 = st.columns(3)

    with col1:
        title_prompts = list_prompts(category="title")
        if not title_prompts:
            st.warning("No title prompts found. Create one in Lab tab.")
            title_prompt = None
        else:
            title_prompt = st.selectbox("Title Prompt", title_prompts, key="batch_title")
            if title_prompt:
                config = get_prompt_config("prompts", title_prompt.replace(".j2", ""))
                model = config.get("model", "unknown")
                st.caption(f"Uses: {model}")

    with col2:
        desc_prompts = list_prompts(category="description")
        if not desc_prompts:
            st.warning("No description prompts found.")
            desc_prompt = None
        else:
            desc_prompt = st.selectbox("Description Prompt", desc_prompts, key="batch_desc")
            if desc_prompt:
                config = get_prompt_config("prompts", desc_prompt.replace(".j2", ""))
                model = config.get("model", "unknown")
                st.caption(f"Uses: {model}")

    with col3:
        tags_prompts = list_prompts(category="tags")
        if not tags_prompts:
            st.warning("No tags prompts found.")
            tags_prompt = None
        else:
            tags_prompt = st.selectbox("Tags Prompt", tags_prompts, key="batch_tags")
            if tags_prompt:
                config = get_prompt_config("prompts", tags_prompt.replace(".j2", ""))
                model = config.get("model", "unknown")
                st.caption(f"Uses: {model}")

    st.divider()

    # Run batch button
    if st.button("🚀 Run Batch Generation", type="primary", use_container_width=True):
        if not all([title_prompt, desc_prompt, tags_prompt]):
            st.error("Please select prompts for all three fields")
        else:
            run_batch(title_prompt, desc_prompt, tags_prompt)

    # Display results if available
    if 'batch_results' in st.session_state and st.session_state.batch_results:
        st.divider()
        st.success(f"✓ Generated content for {len(st.session_state.batch_results)} products")

        # Preview
        st.subheader("Preview (First 5 rows)")
        import pandas as pd
        preview_df = pd.DataFrame(st.session_state.batch_results[:5])
        st.dataframe(preview_df, use_container_width=True)

        # Download button
        excel_bytes = export_enriched_excel(
            st.session_state.products,
            st.session_state.batch_results
        )

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"enriched_{timestamp}.xlsx"

        st.download_button(
            label="📥 Download Enriched Excel",
            data=excel_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


def run_batch(title_prompt_path, desc_prompt_path, tags_prompt_path):
    """Run batch generation for all products."""
    products = st.session_state.products

    # Load prompts and configs
    title_template = get_prompt_content("prompts", title_prompt_path)
    title_config = get_prompt_config("prompts", title_prompt_path.replace(".j2", ""))
    title_model = title_config.get("model", "gpt-4o")

    desc_template = get_prompt_content("prompts", desc_prompt_path)
    desc_config = get_prompt_config("prompts", desc_prompt_path.replace(".j2", ""))
    desc_model = desc_config.get("model", "gpt-4o")

    tags_template = get_prompt_content("prompts", tags_prompt_path)
    tags_config = get_prompt_config("prompts", tags_prompt_path.replace(".j2", ""))
    tags_model = tags_config.get("model", "gpt-4o")

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    results = []

    for idx, product in enumerate(products):
        status_text.text(f"Processing {product.item_number} ({idx + 1}/{len(products)})...")

        # Generate title
        try:
            title_prompt = render_prompt(title_template, product)
            title_result = generate(title_model, title_prompt, product.image_bytes, st.secrets)
            log_cost("logs", title_model, title_result["input_tokens"], title_result["output_tokens"], "batch")
            generated_title = title_result["text"]
        except Exception as e:
            st.warning(f"Error generating title for {product.item_number}: {e}")
            generated_title = ""

        # Generate description
        try:
            desc_prompt = render_prompt(desc_template, product)
            desc_result = generate(desc_model, desc_prompt, product.image_bytes, st.secrets)
            log_cost("logs", desc_model, desc_result["input_tokens"], desc_result["output_tokens"], "batch")
            generated_desc = desc_result["text"]
        except Exception as e:
            st.warning(f"Error generating description for {product.item_number}: {e}")
            generated_desc = ""

        # Generate tags
        try:
            tags_prompt = render_prompt(tags_template, product)
            tags_result = generate(tags_model, tags_prompt, product.image_bytes, st.secrets)
            log_cost("logs", tags_model, tags_result["input_tokens"], tags_result["output_tokens"], "batch")
            generated_tags = tags_result["text"]
        except Exception as e:
            st.warning(f"Error generating tags for {product.item_number}: {e}")
            generated_tags = ""

        results.append({
            "Generated Title": generated_title,
            "Generated Description": generated_desc,
            "Generated Tags": generated_tags
        })

        progress_bar.progress((idx + 1) / len(products))

    status_text.text("✓ Complete!")
    st.session_state.batch_results = results
```

**Step 2: Test Batch tab**

Run: `streamlit run app.py`

Expected: Batch tab shows prompt selectors and run button

**Step 3: Stop app and commit**

```bash
git add app.py
git commit -m "feat: implement Batch tab UI for production runs"
```

---

## Task 19: Add Error Handling and Retries

**Files:**
- Modify: `services/llm_service.py`

**Step 1: Add retry logic with exponential backoff**

Add to `services/llm_service.py` at the top:

```python
import time
from functools import wraps


def retry_with_backoff(max_retries=3, initial_delay=1.0):
    """Decorator for retrying with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if it's a rate limit error
                    error_str = str(e).lower()
                    if "rate" in error_str or "429" in error_str:
                        if attempt < max_retries - 1:
                            time.sleep(delay)
                            delay *= 2  # Exponential backoff
                            continue

                    # For other errors, fail immediately
                    raise

            # If we exhausted all retries
            raise last_exception

        return wrapper
    return decorator
```

**Step 2: Apply retry decorator to provider functions**

Update provider functions in `services/llm_service.py`:

```python
@retry_with_backoff(max_retries=3, initial_delay=1.0)
def _generate_openai(model: str, prompt: str, image_bytes: bytes, secrets: Dict[str, str]) -> Dict[str, Any]:
    """Generate using OpenAI API with retry logic."""
    # ... existing implementation ...


@retry_with_backoff(max_retries=3, initial_delay=1.0)
def _generate_anthropic(model: str, prompt: str, image_bytes: bytes, secrets: Dict[str, str]) -> Dict[str, Any]:
    """Generate using Anthropic API with retry logic."""
    # ... existing implementation ...


@retry_with_backoff(max_retries=3, initial_delay=1.0)
def _generate_google(model: str, prompt: str, image_bytes: bytes, secrets: Dict[str, str]) -> Dict[str, Any]:
    """Generate using Google API with retry logic."""
    # ... existing implementation ...
```

**Step 3: Test manually (will test with integration later)**

**Step 4: Commit**

```bash
git add services/llm_service.py
git commit -m "feat: add retry logic with exponential backoff for rate limits"
```

---

## Task 20: Add Sidebar Cost Summary

**Files:**
- Modify: `app.py`

**Step 1: Add cost summary to sidebar**

Update sidebar in `main()` function in `app.py`:

```python
    # In sidebar, after file upload section
    with st.sidebar:
        # ... existing upload code ...

        st.divider()

        # Cost summary
        with st.expander("💰 Cost Summary"):
            from services.monitoring import get_monthly_summary

            summary = get_monthly_summary("logs")

            if not summary:
                st.info("No costs logged yet")
            else:
                for month, data in sorted(summary.items(), reverse=True):
                    st.markdown(f"**{month}**")
                    st.metric("Total", f"${data['total']:.4f}")

                    st.caption("By Model:")
                    for model, cost in data['by_model'].items():
                        st.caption(f"- {model}: ${cost:.4f}")

                    st.caption("By Context:")
                    for context, cost in data['by_context'].items():
                        st.caption(f"- {context}: ${cost:.4f}")

                    st.divider()
```

**Step 2: Test (need to have some logs first)**

Run: `streamlit run app.py`

Expected: Sidebar shows cost summary expander

**Step 3: Stop app and commit**

```bash
git add app.py
git commit -m "feat: add cost summary to sidebar"
```

---

## Task 21: Final Testing and Documentation

**Files:**
- Modify: `README.md`

**Step 1: Run all tests**

Run: `pytest -v`

Expected: All tests pass

**Step 2: Update README with complete instructions**

Update `README.md`:

```markdown
# Excel Enricher

AI-powered tool for enriching product Excel files with generated content using vision-capable LLMs.

## Features

- 🔬 **Lab Mode**: Test prompts against sample products with multiple models
- 🏭 **Batch Mode**: Generate content for all products using best-performing models
- 💰 **Cost Tracking**: Automatic logging and monthly summaries
- 🎯 **Model Selection**: Choose optimal models per prompt (GPT-4o, Claude Sonnet 4, Gemini 2 Flash)
- 📊 **Excel Export**: Download enriched files with generated columns

## Setup

### 1. Install Dependencies

Using conda (recommended):
```bash
conda create -n excel-enricher python=3.10
conda activate excel-enricher
pip install -r requirements.txt
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the example secrets file:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` with your API keys:
```toml
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_API_KEY = "..."
```

### 3. Run

```bash
streamlit run app.py
```

## Usage

### Lab Workflow

1. Upload Excel file (must have: Item#, PIC, 卖点, Section)
2. Select a sample product
3. Load or write a Jinja2 prompt template
4. Test with multiple models (GPT-4o, Claude Sonnet 4, Gemini 2 Flash)
5. Compare results side-by-side
6. Select best model and save prompt

### Batch Workflow

1. Select production prompts for title, description, and tags
2. System auto-loads each prompt's preferred model
3. Click "Run Batch Generation"
4. Monitor progress
5. Download enriched Excel with 3 new columns

## Excel File Requirements

Your Excel file must contain these columns:
- `Item#` - Product SKU (required)
- `PIC` - Column with embedded images (required, one per product)
- `卖点` - Selling points in Chinese (required)
- `Section` - Product category (required)
- `Colors` - Available colors (optional but recommended)
- `Scent` - Product scent (optional but recommended)

## Project Structure

```
excel-enricher/
├── app.py                    # Main Streamlit UI
├── services/
│   ├── data_service.py       # Excel parsing & export
│   ├── prompt_service.py     # Template management
│   ├── llm_service.py        # Unified LLM interface
│   └── monitoring.py         # Cost tracking
├── prompts/                  # Jinja2 templates
│   ├── title/
│   ├── description/
│   └── tags/
├── logs/                     # Cost logs (JSONL)
├── tests/                    # Unit tests
└── requirements.txt
```

## Available Template Variables

When writing prompts, use these Jinja2 variables:
- `{{ item_number }}` - Product SKU
- `{{ selling_points }}` - 卖点 field
- `{{ section }}` - Product section/category
- `{{ colors }}` - Available colors
- `{{ scent }}` - Product scent

## Development

Run tests:
```bash
pytest -v
```

Run with coverage:
```bash
pytest --cov=services tests/
```

## Cost Tracking

Costs are automatically logged to `logs/costs.jsonl` with:
- Timestamp
- Model used
- Token counts
- Calculated cost
- Context (experimental or batch)

View monthly summaries in the sidebar cost expander.

## Troubleshooting

**"Missing required columns" error:**
- Ensure Excel has: Item#, PIC, 卖点, Section

**"No products found":**
- Check that images are embedded in PIC column
- Verify Excel format is .xlsx or .xls

**API errors:**
- Verify API keys in `.streamlit/secrets.toml`
- Check rate limits (retries happen automatically)

**Import errors:**
- Activate conda environment: `conda activate excel-enricher`
- Reinstall dependencies: `pip install -r requirements.txt`

## License

Internal tool - not for redistribution.
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: complete README with setup and usage instructions"
```

---

## Execution Complete

All tasks implemented! The Excel Enricher is ready for use.

### Summary

- ✅ Project setup with dependencies
- ✅ Data service (Excel loading, export, Product model)
- ✅ Prompt service (Jinja2 templates, read/write)
- ✅ LLM service (OpenAI, Anthropic, Google with retries)
- ✅ Monitoring service (cost calculation, logging, summaries)
- ✅ Initial prompt templates (title, description, tags)
- ✅ Streamlit UI (Lab tab, Batch tab, sidebar)
- ✅ Error handling and cost tracking
- ✅ Complete documentation

### Next Steps

1. Set up `.streamlit/secrets.toml` with your API keys
2. Test with a sample Excel file
3. Create custom prompts in Lab tab
4. Run batch processing
5. Review costs in sidebar

### Testing Checklist

- [ ] Upload Excel file
- [ ] Test prompts with all 3 models in Lab
- [ ] Save prompt with model preference
- [ ] Run batch for 5-10 products
- [ ] Verify enriched Excel columns
- [ ] Check cost logs are created
