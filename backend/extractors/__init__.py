from typing import Dict, Any
from backend.extractors.image_extractor import extract_image
from backend.extractors.pdf_extractor import extract_pdf
from backend.extractors.text_extractor import extract_txt
from backend.extractors.docx_extractor import extract_docx
from backend.extractors.email_extractor import extract_email

def extract_data(file_type: str, file_bytes: bytes) -> Dict[str, Any]:
    """
    Routes unstructured file to appropriate extractor.
    """
    ft = file_type.lower()
    if ft == "image":
        return extract_image(file_bytes)
    elif ft == "pdf":
        return extract_pdf(file_bytes)
    elif ft == "txt":
        return extract_txt(file_bytes)
    elif ft == "docx":
        return extract_docx(file_bytes)
    elif ft == "email":
        return extract_email(file_bytes)
    else:
        # Default to text extractor
        return extract_txt(file_bytes)
