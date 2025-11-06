"""
Data Service - Handles loading and exporting Excel files with embedded images.
"""
from dataclasses import dataclass
from typing import Optional, List
import pandas as pd
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image
import io


@dataclass
class Product:
    """Product data model representing a row in the Excel file."""
    item_number: str
    pic_column: Optional[str]  # Column header for image
    selling_points_cn: Optional[str]  # 卖点
    seo_title: Optional[str]
    description: Optional[str]
    section: Optional[str]
    scent: Optional[str]
    colors: Optional[str]
    specification: Optional[str]
    weight: Optional[str]
    package_size: Optional[str]
    # Add other columns as needed from the original design

    # Image data
    image: Optional[Image.Image] = None  # PIL Image object

    # Generated content (will be populated by LLM)
    generated_title: Optional[str] = None
    generated_description: Optional[str] = None
    generated_tags: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert product to dictionary for Jinja2 template rendering."""
        return {
            'item_number': self.item_number,
            'selling_points_cn': self.selling_points_cn,
            'seo_title': self.seo_title,
            'description': self.description,
            'section': self.section,
            'scent': self.scent,
            'colors': self.colors,
            'specification': self.specification,
            'weight': self.weight,
            'package_size': self.package_size,
        }


def load_products(uploaded_file) -> List[Product]:
    """
    Load products from an uploaded Excel file with embedded images.

    Args:
        uploaded_file: Streamlit UploadedFile object or file path

    Returns:
        List of Product objects
    """
    # Load the workbook with openpyxl to extract images
    wb = openpyxl.load_workbook(uploaded_file)
    ws = wb.active

    # Extract images from the worksheet
    images_by_row = {}
    for img in ws._images:
        # Get the row number where the image is anchored
        # Images are anchored to cells, get the row
        if hasattr(img, 'anchor') and hasattr(img.anchor, '_from'):
            row = img.anchor._from.row + 1  # openpyxl is 0-indexed for anchor
            # Convert image to PIL Image
            image_data = img._data()
            pil_image = Image.open(io.BytesIO(image_data))
            images_by_row[row] = pil_image

    # Load the data with pandas
    df = pd.read_excel(uploaded_file)

    # Map column names (adjust based on actual Excel structure)
    products = []
    for idx, row in df.iterrows():
        # Excel row numbers start at 2 (1 is header)
        excel_row = idx + 2

        product = Product(
            item_number=str(row.get('Item#', '')),
            pic_column=str(row.get('PIC', '')),
            selling_points_cn=str(row.get('卖点', '')) if pd.notna(row.get('卖点')) else None,
            seo_title=str(row.get('SEO Title Search', '')) if pd.notna(row.get('SEO Title Search')) else None,
            description=str(row.get('Item Description', '')) if pd.notna(row.get('Item Description')) else None,
            section=str(row.get('Section', '')) if pd.notna(row.get('Section')) else None,
            scent=str(row.get('Scent', '')) if pd.notna(row.get('Scent')) else None,
            colors=str(row.get('Colors', '')) if pd.notna(row.get('Colors')) else None,
            specification=str(row.get('Specification L*W*H', '')) if pd.notna(row.get('Specification L*W*H')) else None,
            weight=str(row.get('Weight（g）', '')) if pd.notna(row.get('Weight（g）')) else None,
            package_size=str(row.get('Package size', '')) if pd.notna(row.get('Package size')) else None,
            image=images_by_row.get(excel_row)
        )
        products.append(product)

    return products


def export_enriched_excel(products: List[Product], original_file) -> bytes:
    """
    Export products to Excel with generated content columns.

    Args:
        products: List of Product objects with generated content
        original_file: Original uploaded file to preserve formatting

    Returns:
        Excel file as bytes
    """
    # Load original Excel
    df = pd.read_excel(original_file)

    # Add new columns for generated content
    df['Generated Title'] = [p.generated_title for p in products]
    df['Generated Description'] = [p.generated_description for p in products]
    df['Generated Tags'] = [p.generated_tags for p in products]

    # Write to bytes
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return output.getvalue()
