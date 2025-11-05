# Excel Enricher - Design Document

## 1. Core Goal
A simple internal Streamlit tool. A user uploads one Excel file. They test prompts against a sample, and when ready, run those prompts against the whole file to get an enriched Excel file back.

## 2. The User Workflow (The "Simple" Part)
This is the entire workflow for one user:

**Start:** The user runs `streamlit run app.py`.

**Load:** The user uploads their Excel file (with embedded images) in the sidebar.

**Step 1 (Lab Tab):**
- The user selects a sample product (e.g., "SKU-1001").
- They load an existing prompt (e.g., `title/v1.j2`) or write one in the text box.
- They select which models to test (e.g., "GPT-4o" and "Claude 3 Sonnet").
- They click "Test" and see the results side-by-side.
- They tweak the prompt text and click "Test" again.
- Once happy, they save it (e.g., as `title/v2.j2`).

**Step 2 (Batch Tab):**
- The user selects their "production" model (e.g., "Claude 3 Sonnet").
- They select their "production" prompts from the dropdowns (e.g., `title/v2.j2`, `description/v1.j2`).
- They click "Run Batch".
- A progress bar appears. When done, a download button appears.

**Finish:** The user downloads the new Excel file with "Generated Title" and "Generated Description" columns.

## 3. System Components

### 3.1. Main UI (app.py)
This file just handles the UI.

**Sidebar:**
- `st.file_uploader("Upload Excel File")`
- (All API keys are hidden in `secrets.toml`, so no user input is needed).

**Tab 1: 🔬 Lab (Test & Save Prompts)**
- `st.selectbox("1. Select Sample Product")` (shows SKUs)
- `st.image()` (shows the sample's image)
- `st.selectbox("2. Load Prompt")` (lists files from `./prompts/`)
- `st.text_area("3. Edit Prompt")` (the main editor)
- `st.multiselect("4. Select Models to Test")` (["gpt-4o", "claude-3-sonnet", ...])
- `st.button("Run Test")`
- `st.columns()` (to show results side-by-side)
- `st.text_input("Save as...")`
- `st.button("Save Prompt")`

**Tab 2: 🏭 Batch (Run & Download)**
- `st.selectbox("1. Select Model for Batch")`
- `st.selectbox("2. Select Title Prompt")` (lists files from `./prompts/title/`)
- `st.selectbox("3. Select Description Prompt")` (lists files from `./prompts/description/`)
- `st.selectbox("4. Select Tags Prompt")` (lists files from `./prompts/tags/`)
- `st.button("Run Batch Generation")`
- `st.progress()`
- `st.download_button("Download Enriched Excel")`

### 3.2. Configuration (.streamlit/secrets.toml)
This file holds the API keys. Simple and secure.

```toml
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-..."
GOOGLE_API_KEY = "..."
```

### 3.3. Backend Services (To keep app.py clean)

**data_service.py:**
- **Goal:** Turn the Excel file into a list of Product objects.
- **Key Function:** `load_products(uploaded_file)`.
- **Details:** Uses `openpyxl` to find and extract the embedded images and `pandas` for the text. This is the only "complex" part, and it's hidden away here.

**prompt_service.py:**
- **Goal:** Handle all file reading/writing.
- **Key Functions:**
  - `list_prompts()`: Returns a list of files (e.g., `["title/v1.j2", ...]`).
  - `get_prompt_content(path)`: Returns the text from a file.
  - `save_prompt(path, content)`: Saves the text to a file.
  - `render_prompt(template_string, product)`: Uses Jinja2 to fill in the blanks (e.g., `{{ description_cn }}`).

**llm_service.py:**
- **Goal:** Make all LLMs work the same way.
- **Key Function:** `generate(model_name, prompt, image)`.
- **Details:** This function:
  - Picks the right API key from `st.secrets`.
  - Formats the image and prompt for the specific model (e.g., Claude's JSON format).
  - Makes the API call.
  - Returns the generated text and the token counts (`input_tokens`, `output_tokens`).

**monitoring.py:**
- **Goal:** Calculate cost.
- **Key Data:** A dictionary of prices (e.g., `COSTS = {"gpt-4o": ...}`).
- **Key Function:** `calculate_cost(model_name, input_tokens, output_tokens)`.
