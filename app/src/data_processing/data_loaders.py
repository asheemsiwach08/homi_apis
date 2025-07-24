import io
import PyPDF2
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(source: Union[str, bytes, io.BytesIO], password: str = "") -> str:
    """
    Extract text from a PDF.
    * source can be: local file path, raw bytes, or a BytesIO stream.
    """
    try:
        # Normalise the input into a file‑like object
        if isinstance(source, (bytes, bytearray)):
            file_obj = io.BytesIO(source)
        elif isinstance(source, io.BytesIO):
            file_obj = source
        elif isinstance(source, str):
            if not source.lower().endswith(".pdf"):
                raise ValueError("Provided file is not a PDF.")
            file_obj = open(source, "rb")
        else:
            raise TypeError("Unsupported source type for PDF extraction.")

        with file_obj as fp:
            reader = PyPDF2.PdfReader(fp)
            if reader.is_encrypted:
                logger.info("PDF is encrypted. Attempting decryption.")
                if password is None:
                    raise ValueError("Encrypted PDF requires a password.")
                if not reader.decrypt(password):
                    raise PermissionError("Incorrect password or failed to decrypt PDF.")

            if not reader.pages:
                raise ValueError("PDF file is empty or unreadable.")

            text_parts: list[str] = []
            for idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                logger.info("Extracted text from page %s", idx)
                text_parts.append(page_text)

            return "".join(text_parts).strip()
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}") from e
