import pymupdf as fitz
import io
from typing import Dict, Any, List
from backend.extractors.image_extractor import extract_image

def extract_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts text from PDF.
    1. Checks if selectable text exists across pages using PyMuPDF.
    2. If selectable text is sufficient, returns it directly.
    3. If scanned / image-only PDF, renders pages as images and runs OpenCV + OCR.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    num_pages = len(doc)
    
    extracted_pages_text: List[str] = []
    is_scanned = False
    
    # 1. Try native text extraction
    for page_num in range(num_pages):
        page = doc[page_num]
        text = page.get_text("text").strip()
        extracted_pages_text.append(text)
    
    total_text = "\n\n".join([t for t in extracted_pages_text if t])
    
    # Check if text is non-empty and has reasonable content
    # If text is too short or empty across pages, treat as scanned PDF
    if len(total_text.strip()) < 20 and num_pages > 0:
        is_scanned = True
        ocr_pages_text: List[str] = []
        confidences = []
        
        for page_num in range(num_pages):
            page = doc[page_num]
            # Render page at 2x resolution (144 DPI) for crisp OCR
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            
            ocr_res = extract_image(img_bytes)
            if ocr_res["text"]:
                ocr_pages_text.append(ocr_res["text"])
            if ocr_res["confidence"] > 0:
                confidences.append(ocr_res["confidence"])
                
        doc.close()
        full_text = "\n\n".join(ocr_pages_text)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.85
        return {
            "text": full_text,
            "pages": num_pages,
            "is_scanned": True,
            "confidence": round(avg_conf, 3),
            "extraction_method": "ocr_scanned_pdf"
        }
    
    doc.close()
    return {
        "text": total_text,
        "pages": num_pages,
        "is_scanned": False,
        "confidence": 1.0,
        "extraction_method": "pymupdf_native_text"
    }
