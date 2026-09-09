from typing import Dict, Any

def extract_txt(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts text from raw text files with encoding detection fallback.
    """
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
    text = ""
    for enc in encodings:
        try:
            text = file_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
            
    return {
        "text": text,
        "confidence": 1.0,
        "extraction_method": "direct_text"
    }
