"""
Prompt Service - Handles template file management and rendering.
"""
from pathlib import Path
from typing import List, Dict, Optional
from jinja2 import Template
import os


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def list_prompts(category: Optional[str] = None) -> List[str]:
    """
    List all available prompt templates.

    Args:
        category: Optional category filter (e.g., 'title', 'description', 'tags')

    Returns:
        List of prompt file paths relative to prompts directory
    """
    if not PROMPTS_DIR.exists():
        PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
        return []

    prompts = []

    if category:
        # List prompts in a specific category
        category_dir = PROMPTS_DIR / category
        if category_dir.exists():
            for file in category_dir.glob("*.j2"):
                # Return relative path like "title/v1.j2"
                prompts.append(f"{category}/{file.name}")
    else:
        # List all prompts across all categories
        for category_dir in PROMPTS_DIR.iterdir():
            if category_dir.is_dir():
                for file in category_dir.glob("*.j2"):
                    prompts.append(f"{category_dir.name}/{file.name}")

    return sorted(prompts)


def get_prompt_content(prompt_path: str) -> str:
    """
    Read the content of a prompt template file.

    Args:
        prompt_path: Relative path to prompt file (e.g., "title/v1.j2")

    Returns:
        Template content as string
    """
    file_path = PROMPTS_DIR / prompt_path
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")

    return file_path.read_text(encoding='utf-8')


def save_prompt(prompt_path: str, content: str) -> None:
    """
    Save a prompt template to file.

    Args:
        prompt_path: Relative path to prompt file (e.g., "title/v2.j2")
        content: Template content to save
    """
    file_path = PROMPTS_DIR / prompt_path

    # Create category directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)

    file_path.write_text(content, encoding='utf-8')


def render_prompt(template_string: str, product) -> str:
    """
    Render a Jinja2 template with product data.

    Args:
        template_string: Jinja2 template string
        product: Product object or dictionary with product data

    Returns:
        Rendered prompt string
    """
    template = Template(template_string)

    # Convert product to dict if it's an object
    if hasattr(product, 'to_dict'):
        context = product.to_dict()
    else:
        context = product

    return template.render(**context)


def get_prompt_config(prompt_path: str) -> Optional[Dict[str, str]]:
    """
    Get the saved model configuration for a prompt template.

    Prompt configs are stored in .config files next to the template.
    E.g., title/v1.j2 -> title/v1.j2.config

    Args:
        prompt_path: Relative path to prompt file (e.g., "title/v1.j2")

    Returns:
        Dictionary with 'model' key if config exists, None otherwise
    """
    config_path = PROMPTS_DIR / f"{prompt_path}.config"

    if not config_path.exists():
        return None

    # Simple format: just the model name on first line
    model = config_path.read_text(encoding='utf-8').strip()
    return {'model': model}


def save_prompt_config(prompt_path: str, model: str) -> None:
    """
    Save the model configuration for a prompt template.

    Args:
        prompt_path: Relative path to prompt file (e.g., "title/v1.j2")
        model: Model name to associate with this prompt
    """
    config_path = PROMPTS_DIR / f"{prompt_path}.config"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(model, encoding='utf-8')


def list_categories() -> List[str]:
    """
    List all prompt categories (subdirectories in prompts folder).

    Returns:
        List of category names
    """
    if not PROMPTS_DIR.exists():
        return []

    categories = [d.name for d in PROMPTS_DIR.iterdir() if d.is_dir()]
    return sorted(categories)
