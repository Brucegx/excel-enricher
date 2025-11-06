"""
Sample Data Service - Provides pre-loaded sample products for testing.
"""
import pickle
import os
from typing import List
from .data_service import Product


def load_sample_products() -> List[Product]:
    """
    Load pre-saved sample products from pickle file.

    Returns:
        List of Product objects with images
    """
    sample_file = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'sample_products.pkl')

    if not os.path.exists(sample_file):
        raise FileNotFoundError(f"Sample data file not found: {sample_file}")

    with open(sample_file, 'rb') as f:
        products = pickle.load(f)

    return products


def has_sample_data() -> bool:
    """
    Check if sample data is available.

    Returns:
        True if sample data exists, False otherwise
    """
    sample_file = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'sample_products.pkl')
    return os.path.exists(sample_file)
