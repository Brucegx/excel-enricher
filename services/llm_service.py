"""
LLM Service - Unified interface for multiple LLM providers.
"""
from typing import Optional, Dict, Tuple
import streamlit as st
from PIL import Image
import base64
import io
import openai
import anthropic
import google.generativeai as genai


# Model configurations
AVAILABLE_MODELS = {
    'gpt-4o': {
        'provider': 'openai',
        'display_name': 'GPT-4o',
        'api_key_name': 'OPENAI_API_KEY'
    },
    'claude-sonnet-4': {
        'provider': 'anthropic',
        'display_name': 'Claude Sonnet 4',
        'api_key_name': 'ANTHROPIC_API_KEY',
        'model_id': 'claude-sonnet-4-20250514'
    },
    'gemini-2.0-flash-exp': {
        'provider': 'google',
        'display_name': 'Gemini 2.0 Flash',
        'api_key_name': 'GOOGLE_API_KEY'
    }
}


def _image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


def _get_api_key(model_name: str) -> str:
    """Get API key from Streamlit secrets."""
    config = AVAILABLE_MODELS.get(model_name)
    if not config:
        raise ValueError(f"Unknown model: {model_name}")

    key_name = config['api_key_name']
    if key_name not in st.secrets:
        raise ValueError(f"API key not found in secrets: {key_name}")

    return st.secrets[key_name]


def _generate_openai(model_name: str, prompt: str, image: Optional[Image.Image]) -> Tuple[str, int, int]:
    """Generate using OpenAI API."""
    api_key = _get_api_key(model_name)
    client = openai.OpenAI(api_key=api_key)

    messages = []

    if image:
        # Format with image
        base64_image = _image_to_base64(image)
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        })
    else:
        # Text only
        messages.append({
            "role": "user",
            "content": prompt
        })

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=1000
    )

    return (
        response.choices[0].message.content,
        response.usage.prompt_tokens,
        response.usage.completion_tokens
    )


def _generate_anthropic(model_name: str, prompt: str, image: Optional[Image.Image]) -> Tuple[str, int, int]:
    """Generate using Anthropic API."""
    api_key = _get_api_key(model_name)
    client = anthropic.Anthropic(api_key=api_key)

    # Get the actual model ID
    model_id = AVAILABLE_MODELS[model_name].get('model_id', model_name)

    content = []

    if image:
        # Add image
        base64_image = _image_to_base64(image)
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": base64_image
            }
        })

    # Add text
    content.append({
        "type": "text",
        "text": prompt
    })

    response = client.messages.create(
        model=model_id,
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": content
        }]
    )

    return (
        response.content[0].text,
        response.usage.input_tokens,
        response.usage.output_tokens
    )


def _generate_google(model_name: str, prompt: str, image: Optional[Image.Image]) -> Tuple[str, int, int]:
    """Generate using Google Generative AI API."""
    api_key = _get_api_key(model_name)
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(model_name)

    if image:
        # Generate with image
        response = model.generate_content([prompt, image])
    else:
        # Text only
        response = model.generate_content(prompt)

    # Google doesn't always provide token counts in the same way
    # Estimate based on response
    input_tokens = len(prompt.split()) * 1.3  # Rough estimate
    output_tokens = len(response.text.split()) * 1.3

    return (
        response.text,
        int(input_tokens),
        int(output_tokens)
    )


def generate(model_name: str, prompt: str, image: Optional[Image.Image] = None) -> Dict[str, any]:
    """
    Generate content using the specified LLM model.

    Args:
        model_name: Name of the model to use (e.g., 'gpt-4o')
        prompt: The prompt text
        image: Optional PIL Image

    Returns:
        Dictionary with:
            - text: Generated text
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - model: Model name used
    """
    if model_name not in AVAILABLE_MODELS:
        raise ValueError(f"Unknown model: {model_name}")

    config = AVAILABLE_MODELS[model_name]
    provider = config['provider']

    # Route to appropriate provider
    if provider == 'openai':
        text, input_tokens, output_tokens = _generate_openai(model_name, prompt, image)
    elif provider == 'anthropic':
        text, input_tokens, output_tokens = _generate_anthropic(model_name, prompt, image)
    elif provider == 'google':
        text, input_tokens, output_tokens = _generate_google(model_name, prompt, image)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    return {
        'text': text,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'model': model_name
    }


def get_available_models() -> list:
    """Get list of available model names."""
    return list(AVAILABLE_MODELS.keys())


def get_model_display_name(model_name: str) -> str:
    """Get the display name for a model."""
    return AVAILABLE_MODELS.get(model_name, {}).get('display_name', model_name)
