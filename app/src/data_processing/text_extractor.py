"""
Comprehensive text extraction module for various file types.
Supports PDF, images (PNG, JPEG, JPG), CSV, Excel, Word documents, and text files.
"""

import re
import io
import csv
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any
from difflib import SequenceMatcher

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

def extract_keywords(text: str) -> str:
    """Extract keywords from a text string.
    Args:
        text: Text string
        
    Returns:
        Keywords as string
    """
    # text = text.lower().strip()
    words = re.findall(r'[a-z]+', text, re.IGNORECASE)
    stop_words = {'the', 'of', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are', 'was', 'were'}
    keywords = [word for word in words if word not in stop_words]
    return " ".join(keywords)

def match_subject_keywords(subject1: str, subject2: str, threshold: float = 0.5) -> bool:
    """Match subject keywords using sequence similarity.
    Args:
        subject1: First subject string
        subject2: Second subject string
        threshold: Similarity threshold (default: 0.5)
        
    Returns:
        True if subjects are similar, False otherwise
    """
    keywords1 = extract_keywords(subject1)
    keywords2 = extract_keywords(subject2)

    if not keywords1 or not keywords2:
        return False
    similarity = SequenceMatcher(None, keywords1, keywords2).ratio()
    return similarity >= threshold


def gather_pdf_content(email: dict) -> tuple[str, dict]:
    """Gather PDF content from an email.
    Args:
        email: Email dictionary with 'sender', 'date', 'subject', and 'content'
        
    Returns:
        PDF content as string, Email dictionary with 'sender', 'date', 'subject', and 'content'
    """
    import html
    try:
        content = email['content']
        # # Remove HTML tags
        # content = re.sub(r'<[^>]+>', '', content)
        # # Decode HTML entities
        # content = html.unescape(content)
        # # filtered_content = re.sub(r'[^a-z0-9]+', '', content, re.IGNORECASE)
        # filtered_content = " ".join(content.split()).strip()

        filtered_content = content
        filtered_content = filtered_content.replace("Part-1 of Thread:", "\n-+-\n").replace("Part-2 of Thread:", "\n-+-\n").replace("Part-3 of Thread:", "\n-+-\n")
        # print("🔹🔹🔹 Filtered Content: ", filtered_content)
        
        pdf_content = f"""
        From: {email['sender']}
        To: disbursement@basichomeloan.com
        
        Date: {email['date']}
        
        Subject: {email['subject']}

        Content:
        {filtered_content.strip()}
        --------------------------------
        """
        return pdf_content, {"from": email['sender'], "to": "disbursement@basichomeloan.com", "date": email['date'], "subject": email['subject'], "content": filtered_content.strip()}

    except Exception as e:
        logger.error(f"Error gathering PDF content: {str(e)}")
        return "", {"from": "", "to": "", "date": "", "subject": "", "content": ""}


from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor

def escape_html(text):
    """Escape HTML special characters"""
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

def email_string_to_pdf(email_text: dict, output_path: str = None) -> tuple[bool, bytes]:
    """Convert email text to PDF.
    Args:
        email_text: Email dictionary with 'from', 'to', 'date', 'subject', and 'content'
        output_path: Optional path to save the PDF file. If None, PDF is only returned as bytes.
    Returns:
        tuple[bool, bytes]: Tuple containing success status and PDF content as binary data (blob)
    """
    try:
        # Bytes to store content
        buffer = io.BytesIO()
        
        pdf = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        styles = getSampleStyleSheet()
        elements = []

        # Create custom styles
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading1'],
            fontSize=10,
            textColor=HexColor('#2C3E50'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )
        
        label_style = ParagraphStyle(
            'CustomLabel',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#7F8C8D'),
            fontName='Helvetica-Bold',
            spaceAfter=4
        )
        
        value_style = ParagraphStyle(
            'CustomValue',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#2C3E50'),
            spaceAfter=10,
            leftIndent=20
        )
        
        subject_style = ParagraphStyle(
            'CustomSubject',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor('#2C3E5E'), # Dark blue color
            fontName='Helvetica-Bold',
            spaceAfter=12
        )
        
        content_style = ParagraphStyle(
            'CustomContent',
            parent=styles['BodyText'],
            fontSize=8,
            textColor=HexColor('#2C3E50'),
            leading=9,
            spaceAfter=10,
            leftIndent=0,
            rightIndent=0
        )
        
        separator_style = ParagraphStyle(
            'CustomSeparator',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#2C3E50'), # Blue Color
            spaceAfter=12,
            leftIndent=0,
            rightIndent=0
        )

        # Add title/header
        elements.append(Spacer(1, 0.2*inch))
        
        # From field
        from_value = escape_html(email_text.get("from", ""))
        if from_value:
            elements.append(Paragraph(f"<b>From:</b> {from_value}", label_style))
            # elements.append(Paragraph(from_value, value_style))
        
        # To field
        to_value = escape_html(email_text.get("to", ""))
        if to_value:
            elements.append(Paragraph(f"<b>To:</b> :{to_value}", label_style))
            # elements.append(Paragraph(to_value, value_style))
        
        # Date field
        date_value = escape_html(email_text.get("date", ""))
        if date_value:
            elements.append(Paragraph(f"<b>Date:</b> {date_value}", label_style))
            # elements.append(Paragraph(date_value, date_style))
        
        # Subject field
        subject_value = escape_html(email_text.get("subject", ""))
        if subject_value:
            elements.append(Paragraph(f"<b>Subject:</b> {subject_value}", subject_style))
            # elements.append(Spacer(1, 0.2*inch))
        
        # Content field - preserve line breaks
        content_value = escape_html(email_text.get("content", ""))
        if content_value:
            # Replace newlines with <br/> tags for proper line breaks in PDF
            content_value = content_value.replace('\n', '<br/>')
            # Split into paragraphs if there are double newlines
            paragraphs = content_value.split('<br/><br/>')
            for para in paragraphs:
                if "-+-" in para:
                    para = para.replace("-+-", "")
                    # Add a horizontal line
                    elements.append(Paragraph(f"{45*'- - '}", separator_style))
                    elements.append(Paragraph(f"<b></b> {para.strip()}", content_style))
                    elements.append(Spacer(1, 0.1*inch))
                else:
                    if para.strip():
                        elements.append(Paragraph(para.strip(), content_style))
                        elements.append(Spacer(1, 0.1*inch))

        # Build PDF in memory
        pdf.build(elements)
        
        # Get PDF bytes from buffer
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Optionally save to file if output_path is provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return True, pdf_bytes 

    except Exception as e:
        logger.error(f"Error converting email text to PDF: {str(e)}")
        return False, None

# Email content correction functions
def correct_email_links(string: str) -> str:

    string = re.sub(r"https?://\S+|www\.\S+", "", string)  # Clear the links
    email_list = re.findall(r"<[a-zA-Z0-9.]+@[a-zA-Z0-9.]+[^>]+>", string)

    for email in email_list:
        string = string.replace(email, "mailto:"+email.replace("<","").replace(">","").replace("mailto:",","))
    return string

def correct_symbols_from_string(string: str) -> str:

    string = re.sub(r"[<>*]", " ", string)
    return string

def clean_email_content(text: str) -> str:
    """
    Clean and format email content by correcting links, symbols, and organizing thread parts.
    
    Args:
        text: Raw email content string to clean
        
    Returns:
        Cleaned and formatted email content string
        
    Raises:
        ValueError: If input is not a string or is None
    """
    # Input validation
    if text is None:
        raise ValueError("Input text cannot be None")
    
    if not isinstance(text, str):
        raise ValueError(f"Input must be a string, got {type(text).__name__}")
    
    # Handle empty string
    if not text.strip():
        return ""
    
    try:
        # Apply email link and symbol corrections
        text = correct_email_links(string=text)
        
        text = correct_symbols_from_string(string=text)
        
    except Exception as e:
        print(f"Warning: Error during email content correction: {e}")
        # Continue with original text if corrections fail
    
    try:
        # Split text into lines
        splitted_text = text.split("\n")
    except Exception as e:
        print(f"Error: Failed to split text into lines: {e}")
        return text  # Return processed text if splitting fails
    
    # Build cleaned text
    cleaned_text = ""
    parts = 1
    
    try:
        for line in splitted_text:
            # Skip empty lines
            if not line.strip():
                continue
            
            lowered_line = line.strip().lower()
            
            # Check for email thread markers
            if "from:" in lowered_line:
                cleaned_text += "\n" + f"Part-{parts} of Thread: \n" + line.strip()
                parts += 1
            elif len(lowered_line) <= 80:
                # Check if line contains non-alphanumeric characters (symbols, punctuation, etc.)
                filtered_symbol_text = re.findall(r"[^a-zA-Z0-9\s]", line)
                if len(filtered_symbol_text) > 0:
                    cleaned_text += "\n" + line.strip()
    except Exception as e:
        print(f"Error: Failed during line processing: {e}")
        # Return what we have so far
        return cleaned_text if cleaned_text else text
    
    # Return cleaned text, or original if cleaning resulted in empty string
    return cleaned_text.strip() if cleaned_text.strip() else text.strip()

# Subject validation pattern
SUBJECT_PATTERN = re.compile(
    r"""^
    .+?\s\(basic\ home\ loan\)\s–\s
    disbursement\ confirmation\ request\s\|\s
    .+?\s\|\s
    .+?\s\|\s
    .+?
    $""",
    re.VERBOSE
)

def is_valid_subject(subject: str) -> bool:
    return bool(SUBJECT_PATTERN.match(subject))

