"""
Monitoring Service - Cost calculation and logging.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import json


# Pricing per 1M tokens (as of 2025)
# Format: (input_price, output_price) per 1M tokens in USD
PRICING = {
    'gpt-4o': (2.50, 10.00),  # $2.50 input, $10.00 output per 1M tokens
    'claude-sonnet-4': (3.00, 15.00),  # $3.00 input, $15.00 output per 1M tokens
    'gemini-2.0-flash-exp': (0.00, 0.00),  # Free tier (update when pricing announced)
}


LOGS_DIR = Path(__file__).parent.parent / "logs"


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate the cost of an LLM API call.

    Args:
        model_name: Name of the model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    if model_name not in PRICING:
        # Unknown model, return 0
        return 0.0

    input_price, output_price = PRICING[model_name]

    # Calculate cost (prices are per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price

    return input_cost + output_cost


def log_usage(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    usage_type: str,
    prompt_template: str = None,
    product_id: str = None
) -> None:
    """
    Log usage to JSONL file.

    Args:
        model_name: Name of the model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cost: Cost in USD
        usage_type: Type of usage ('experimental', 'batch')
        prompt_template: Optional prompt template name
        product_id: Optional product identifier
    """
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Log file path: logs/usage_YYYY-MM.jsonl
    log_file = LOGS_DIR / f"usage_{datetime.now().strftime('%Y-%m')}.jsonl"

    # Create log entry
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'model': model_name,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'cost': round(cost, 6),
        'usage_type': usage_type,
    }

    if prompt_template:
        log_entry['prompt_template'] = prompt_template

    if product_id:
        log_entry['product_id'] = product_id

    # Append to log file
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')


def get_monthly_summary(year: int = None, month: int = None) -> Dict:
    """
    Get usage summary for a specific month.

    Args:
        year: Year (defaults to current year)
        month: Month (defaults to current month)

    Returns:
        Dictionary with usage summary:
            - total_cost: Total cost in USD
            - total_calls: Total number of API calls
            - by_model: Breakdown by model
            - by_usage_type: Breakdown by usage type
    """
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month

    log_file = LOGS_DIR / f"usage_{year:04d}-{month:02d}.jsonl"

    if not log_file.exists():
        return {
            'total_cost': 0.0,
            'total_calls': 0,
            'by_model': {},
            'by_usage_type': {},
            'period': f"{year:04d}-{month:02d}"
        }

    # Read and aggregate logs
    total_cost = 0.0
    total_calls = 0
    by_model = {}
    by_usage_type = {}

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line.strip())
            total_cost += entry['cost']
            total_calls += 1

            # By model
            model = entry['model']
            if model not in by_model:
                by_model[model] = {'calls': 0, 'cost': 0.0, 'input_tokens': 0, 'output_tokens': 0}
            by_model[model]['calls'] += 1
            by_model[model]['cost'] += entry['cost']
            by_model[model]['input_tokens'] += entry['input_tokens']
            by_model[model]['output_tokens'] += entry['output_tokens']

            # By usage type
            usage_type = entry['usage_type']
            if usage_type not in by_usage_type:
                by_usage_type[usage_type] = {'calls': 0, 'cost': 0.0}
            by_usage_type[usage_type]['calls'] += 1
            by_usage_type[usage_type]['cost'] += entry['cost']

    return {
        'total_cost': round(total_cost, 2),
        'total_calls': total_calls,
        'by_model': by_model,
        'by_usage_type': by_usage_type,
        'period': f"{year:04d}-{month:02d}"
    }


def get_recent_logs(limit: int = 10) -> List[Dict]:
    """
    Get the most recent log entries.

    Args:
        limit: Number of recent entries to return

    Returns:
        List of log entries (most recent first)
    """
    # Get current month log file
    log_file = LOGS_DIR / f"usage_{datetime.now().strftime('%Y-%m')}.jsonl"

    if not log_file.exists():
        return []

    # Read all entries
    entries = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            entries.append(json.loads(line.strip()))

    # Return most recent entries (reverse chronological)
    return entries[-limit:][::-1]
