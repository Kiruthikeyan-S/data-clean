import mimetypes
from pathlib import Path
from typing import Dict, Tuple

# Extension to type mappings
EXTENSION_MAP = {
    # Images
    ".jpg": ("image", "image/jpeg"),
    ".jpeg": ("image", "image/jpeg"),
    ".png": ("image", "image/png"),
    ".webp": ("image", "image/webp"),
    ".bmp": ("image", "image/bmp"),
    ".tiff": ("image", "image/tiff"),
    # Documents
    ".pdf": ("pdf", "application/pdf"),
    ".txt": ("txt", "text/plain"),
    ".docx": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ".doc": ("docx", "application/msword"),
    ".eml": ("email", "message/rfc822"),
    ".msg": ("email", "application/vnd.ms-outlook"),
    # Structured
    ".csv": ("csv", "text/csv"),
    ".xlsx": ("excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ".xls": ("excel", "application/vnd.ms-excel"),
    ".json": ("json", "application/json"),
}

STRUCTURED_TYPES = {"csv", "excel", "json"}
UNSTRUCTURED_TYPES = {"image", "pdf", "txt", "docx", "email"}


def detect_file_type(filename: str, content_type: str = None, file_bytes: bytes = None) -> Dict[str, str]:
    """
    Detects the file type and MIME type based on file extension, MIME content type,
    and magic bytes analysis.
    """
    ext = Path(filename).suffix.lower()
    guessed_type, _ = mimetypes.guess_type(filename)
    
    # 1. Check magic bytes if file_bytes is provided
    if file_bytes and len(file_bytes) >= 4:
        if file_bytes.startswith(b"%PDF"):
            return {"file_type": "pdf", "mime_type": "application/pdf"}
        elif file_bytes.startswith(b"\xff\xd8\xff"):
            return {"file_type": "image", "mime_type": "image/jpeg"}
        elif file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return {"file_type": "image", "mime_type": "image/png"}
        elif file_bytes.startswith(b"RIFF") and len(file_bytes) > 12 and file_bytes[8:12] == b"WEBP":
            return {"file_type": "image", "mime_type": "image/webp"}
        elif file_bytes.startswith(b"PK\x03\x04"):
            # Zip archive (could be docx or xlsx)
            if ext in [".xlsx", ".xls"]:
                return {"file_type": "excel", "mime_type": EXTENSION_MAP[ext][1]}
            elif ext in [".docx", ".doc"]:
                return {"file_type": "docx", "mime_type": EXTENSION_MAP[ext][1]}

    # 2. Match based on extension map
    if ext in EXTENSION_MAP:
        file_type, mime = EXTENSION_MAP[ext]
        return {
            "file_type": file_type,
            "mime_type": content_type or guessed_type or mime
        }

    # 3. Match based on content_type if available
    if content_type:
        ct = content_type.lower()
        if "csv" in ct:
            return {"file_type": "csv", "mime_type": "text/csv"}
        elif "json" in ct:
            return {"file_type": "json", "mime_type": "application/json"}
        elif "pdf" in ct:
            return {"file_type": "pdf", "mime_type": "application/pdf"}
        elif "spreadsheet" in ct or "excel" in ct:
            return {"file_type": "excel", "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        elif "wordprocessing" in ct or "msword" in ct:
            return {"file_type": "docx", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        elif "image" in ct:
            return {"file_type": "image", "mime_type": content_type}
        elif "message/rfc822" in ct:
            return {"file_type": "email", "mime_type": "message/rfc822"}
        elif "text" in ct:
            return {"file_type": "txt", "mime_type": "text/plain"}

    # Default fallback
    return {
        "file_type": "txt",
        "mime_type": guessed_type or "application/octet-stream"
    }


def classify_data_type(file_type: str) -> str:
    """
    Classifies file type into structured or unstructured.
    """
    if file_type.lower() in STRUCTURED_TYPES:
        return "structured"
    return "unstructured"
