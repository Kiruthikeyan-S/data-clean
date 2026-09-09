import re
import unicodedata
from typing import List, Optional

NULL_VARIANTS = {"n/a", "na", "null", "none", "nil", "undefined", "unknown", "-", "--", "nan"}

def normalize_unicode(text: str) -> str:
    """Normalizes Unicode characters (NFKC) and handles special quotes/dashes."""
    if not text:
        return ""
    # NFKC normalizes compatibility characters
    normalized = unicodedata.normalize("NFKC", text)
    # Replace smart quotes and dashes with standard ASCII equivalents
    replacements = {
        '“': '"', '”': '"', '„': '"', '‟': '"',
        '‘': "'", '’': "'", '‚': "'", '‛': "'",
        '–': '-', '—': '-', '−': '-',
        '\u00a0': ' ',  # Non-breaking space
        '\ufeff': '',   # BOM
    }
    for orig, rep in replacements.items():
        normalized = normalized.replace(orig, rep)
    return normalized


def remove_noise(text: str) -> str:
    """Removes non-printable control characters while preserving newlines and tabs."""
    if not text:
        return ""
    # Filter out control characters except \n, \r, \t
    cleaned = "".join(ch for ch in text if ch in ('\n', '\r', '\t') or unicodedata.category(ch)[0] != "C")
    return cleaned


def normalize_whitespace(text: str) -> str:
    """Normalizes newlines, removes consecutive blank lines, and trims line whitespace."""
    if not text:
        return ""
    # Standardize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    
    # Remove excessive blank lines (max 1 empty line in between)
    collapsed_lines: List[str] = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                collapsed_lines.append("")
                prev_blank = True
        else:
            collapsed_lines.append(line)
            prev_blank = False
            
    return "\n".join(collapsed_lines).strip()


def remove_duplicate_lines(text: str) -> str:
    """Removes immediate consecutive duplicate lines."""
    if not text:
        return ""
    lines = text.split("\n")
    unique_lines: List[str] = []
    prev = None
    for line in lines:
        if line != prev or line == "":
            unique_lines.append(line)
            prev = line
    return "\n".join(unique_lines)


def correct_safe_ocr_errors(text: str) -> str:
    """
    Safely fixes OCR misrecognitions only in unambiguous contexts.
    E.g., common punctuation spacing glitches like ' : ' or ' , '.
    """
    if not text:
        return ""
    # Remove space before colons, commas, periods if isolated
    text = re.sub(r"\s+([:,.;])", r"\1", text)
    # Ensure space after colon in key-value contexts e.g. "Name:John" -> "Name: John"
    text = re.sub(r"([A-Za-z]+):([^\s/])", r"\1: \2", text)
    return text


def clean_text_data(text: str) -> str:
    """
    Full text cleaning pipeline for extracted unstructured data.
    """
    if not text:
        return ""
    t = normalize_unicode(text)
    t = remove_noise(t)
    t = correct_safe_ocr_errors(t)
    t = normalize_whitespace(t)
    t = remove_duplicate_lines(t)
    return t
