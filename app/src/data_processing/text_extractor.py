"""
Comprehensive text extraction module for various file types.
Supports PDF, images (PNG, JPEG, JPG), CSV, Excel, Word documents, and text files.
"""

import io
import csv
import logging
from typing import Optional, Union, Dict, Any
from pathlib import Path

# PDF processing
import PyPDF2

# Image processing and OCR
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("OCR dependencies not available. Image text extraction will be disabled.")

# Document processing
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logging.warning("python-docx not available. DOCX text extraction will be disabled.")

try:
    import pandas as pd
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    logging.warning("pandas/openpyxl not available. Excel text extraction will be disabled.")

logger = logging.getLogger(__name__)


class TextExtractor:
    """Comprehensive text extractor for various file types."""
    
    def __init__(self):
        """Initialize the text extractor."""
        self.supported_extensions = {
            '.pdf': self._extract_pdf_text,
            '.png': self._extract_image_text,
            '.jpg': self._extract_image_text,
            '.jpeg': self._extract_image_text,
            '.csv': self._extract_csv_text,
            '.xlsx': self._extract_excel_text,
            '.xls': self._extract_excel_text,
            '.docx': self._extract_docx_text,
            '.doc': self._extract_docx_text,  # Note: .doc support is limited
            '.txt': self._extract_text_file,
        }
    
    def extract_text(self, content: Union[bytes, str], filename: str, 
                    content_type: Optional[str] = None) -> str:
        """
        Extract text from file content based on file extension.
        
        Args:
            content: File content as bytes or string
            filename: Original filename with extension
            content_type: MIME content type (optional)
            
        Returns:
            Extracted text as string
        """
        try:
            # Get file extension
            file_path = Path(filename.lower())
            extension = file_path.suffix
            
            if extension not in self.supported_extensions:
                logger.warning(f"Unsupported file type: {extension} for file {filename}")
                return f"[Unsupported file type: {extension}]"
            
            # Extract text using appropriate method
            extractor_method = self.supported_extensions[extension]
            extracted_text = extractor_method(content, filename)
            
            if extracted_text:
                logger.info(f"Successfully extracted text from {filename}")
                return extracted_text
            else:
                logger.warning(f"No text extracted from {filename}")
                return f"[No text found in {filename}]"
                
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            return f"[Error extracting text from {filename}: {str(e)}]"
    
    def _extract_pdf_text(self, content: Union[bytes, str], filename: str) -> str:
        """Extract text from PDF content."""
        try:
            from .data_loaders import extract_text_from_pdf
            return extract_text_from_pdf(content)
        except Exception as e:
            logger.error(f"PDF extraction error for {filename}: {str(e)}")
            return f"[PDF extraction failed: {str(e)}]"
    
    def _extract_image_text(self, content: Union[bytes, str], filename: str) -> str:
        """Extract text from image using OCR."""
        if not OCR_AVAILABLE:
            return "[OCR not available - cannot extract text from image]"
        
        try:
            # Convert content to bytes if it's a string
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            # Open image using PIL
            image = Image.open(io.BytesIO(content))
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            if text.strip():
                return f"[Image OCR Text from {filename}]:\n{text.strip()}"
            else:
                return f"[No text detected in image {filename}]"
                
        except Exception as e:
            logger.error(f"Image OCR error for {filename}: {str(e)}")
            return f"[Image OCR failed: {str(e)}]"
    
    def _extract_csv_text(self, content: Union[bytes, str], filename: str) -> str:
        """Extract text from CSV content."""
        try:
            # Convert content to string if it's bytes
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            # Parse CSV content
            csv_reader = csv.reader(io.StringIO(content))
            rows = list(csv_reader)
            
            if not rows:
                return f"[Empty CSV file: {filename}]"
            
            # Convert to readable format
            csv_text = []
            for i, row in enumerate(rows):
                row_text = " | ".join(str(cell) for cell in row)
                csv_text.append(f"Row {i+1}: {row_text}")
            
            return f"[CSV Content from {filename}]:\n" + "\n".join(csv_text)
            
        except Exception as e:
            logger.error(f"CSV extraction error for {filename}: {str(e)}")
            return f"[CSV extraction failed: {str(e)}]"
    
    def _extract_excel_text(self, content: Union[bytes, str], filename: str) -> str:
        """Extract text from Excel content."""
        if not EXCEL_AVAILABLE:
            return "[Excel processing not available]"
        
        try:
            # Convert content to bytes if it's a string
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            # Read Excel file using pandas
            excel_data = pd.read_excel(io.BytesIO(content), sheet_name=None)
            
            excel_text = []
            for sheet_name, df in excel_data.items():
                if not df.empty:
                    sheet_text = [f"Sheet: {sheet_name}"]
                    # Convert DataFrame to string representation
                    sheet_text.append(df.to_string(index=False))
                    excel_text.append("\n".join(sheet_text))
            
            if excel_text:
                return f"[Excel Content from {filename}]:\n" + "\n\n".join(excel_text)
            else:
                return f"[Empty Excel file: {filename}]"
                
        except Exception as e:
            logger.error(f"Excel extraction error for {filename}: {str(e)}")
            return f"[Excel extraction failed: {str(e)}]"
    
    def _extract_docx_text(self, content: Union[bytes, str], filename: str) -> str:
        """Extract text from Word document content."""
        if not DOCX_AVAILABLE:
            return "[Word document processing not available]"
        
        try:
            # Convert content to bytes if it's a string
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            # Parse Word document
            doc = Document(io.BytesIO(content))
            
            # Extract text from paragraphs
            paragraphs = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text.strip())
            
            if paragraphs:
                return f"[Word Document Content from {filename}]:\n" + "\n".join(paragraphs)
            else:
                return f"[Empty Word document: {filename}]"
                
        except Exception as e:
            logger.error(f"Word document extraction error for {filename}: {str(e)}")
            return f"[Word document extraction failed: {str(e)}]"
    
    def _extract_text_file(self, content: Union[bytes, str], filename: str) -> str:
        """Extract text from plain text file."""
        try:
            # Convert content to string if it's bytes
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            if content.strip():
                return f"[Text File Content from {filename}]:\n{content.strip()}"
            else:
                return f"[Empty text file: {filename}]"
                
        except Exception as e:
            logger.error(f"Text file extraction error for {filename}: {str(e)}")
            return f"[Text file extraction failed: {str(e)}]"


# Global instance for easy access
text_extractor = TextExtractor()


def extract_text_from_attachment(attachment: Dict[str, Any]) -> str:
    """
    Extract text from an attachment using the appropriate method.
    
    Args:
        attachment: Attachment dictionary with 'content', 'filename', and 'content_type'
        
    Returns:
        Extracted text as string
    """
    content = attachment.get('content')
    filename = attachment.get('filename', 'unknown')
    content_type = attachment.get('content_type')
    
    if not content:
        return f"[No content available for {filename}]"
    
    return text_extractor.extract_text(content, filename, content_type)


def extract_all_attachment_texts(attachments: list) -> str:
    """
    Extract text from all attachments and combine into a single string.
    
    Args:
        attachments: List of attachment dictionaries
        
    Returns:
        Combined text from all attachments
    """
    if not attachments:
        return ""
    
    extracted_texts = []
    for attachment in attachments:
        filename = attachment.get('filename', 'unknown')
        extracted_text = extract_text_from_attachment(attachment)
        extracted_texts.append(f"--- {filename} ---\n{extracted_text}\n")
    
    return "\n".join(extracted_texts) 