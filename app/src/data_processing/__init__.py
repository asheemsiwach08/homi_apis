"""
Data processing package for the Email Analysis and Bank Application Verification System.

This package contains modules for:
- AI-based verification of bank applications
- Excel and CSV data processing
- Text extraction from various file formats
- Data loading and transformation utilities
"""

from .ai_basic_verification import ai_basic_verification
from .excel_table import (
    get_data_from_csv,
    fill_bankappid_missing_values,
    filter_and_deduplicate_csv
)
from .text_extractor import TextExtractor
from .data_loaders import extract_text_from_pdf
from .date_converter import convert_datetime_to_date

__all__ = [
    'ai_basic_verification',
    'get_data_from_csv',
    'fill_bankappid_missing_values',
    'filter_and_deduplicate_csv',
    'TextExtractor',
    'extract_text_from_pdf',
    'convert_datetime_to_date'
] 