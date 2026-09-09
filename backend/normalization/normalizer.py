import re
import datetime
from typing import Any, Optional, Union
from dateutil import parser as date_parser
import phonenumbers
from email_validator import validate_email, EmailNotValidError

def normalize_name(name_str: Optional[str]) -> Optional[str]:
    """
    Normalizes person names to Title Case while respecting particles, initials, and apostrophes.
    Example: 'RAVI KUMAR' -> 'Ravi Kumar', 'mcdonald' -> 'McDonald'
    """
    if not name_str or not isinstance(name_str, str):
        return None
    
    clean = " ".join(name_str.strip().split())
    if not clean:
        return None
        
    # Title case each word with apostrophe handling
    def _capitalize_part(word: str) -> str:
        # Handle O'Connor, D'Angelo
        if "'" in word:
            subparts = word.split("'")
            return "'".join(s.capitalize() for s in subparts)
        # Handle Mc/Mac
        if word.lower().startswith("mc") and len(word) > 2:
            return "Mc" + word[2:].capitalize()
        return word.capitalize()

    words = clean.split(" ")
    return " ".join(_capitalize_part(w) for w in words)


def normalize_date(date_val: Any) -> Optional[str]:
    """
    Parses various date formats into standard ISO 8601 string 'YYYY-MM-DD'.
    Example: '12/05/2001' -> '2001-05-12' (or '2001-12-05' based on context/parser)
    """
    if date_val is None:
        return None
    if isinstance(date_val, (datetime.date, datetime.datetime)):
        return date_val.strftime("%Y-%m-%d")
    
    if not isinstance(date_val, str):
        date_str = str(date_val).strip()
    else:
        date_str = date_val.strip()
        
    if not date_str or len(date_str) < 4:
        return None

    try:
        # Try dayfirst=False then dayfirst=True if needed
        # We can inspect common patterns
        parsed = date_parser.parse(date_str, dayfirst=True)
        # Year sanity check (1900 to 2100)
        if 1900 <= parsed.year <= 2100:
            return parsed.strftime("%Y-%m-%d")
    except Exception:
        pass

    try:
        parsed = date_parser.parse(date_str, dayfirst=False)
        if 1900 <= parsed.year <= 2100:
            return parsed.strftime("%Y-%m-%d")
    except Exception:
        pass

    return None


def normalize_email(email_str: Optional[str]) -> Optional[str]:
    """
    Normalizes email address: lowercases, trims whitespace, verifies format.
    Example: 'RAVI@GMAIL.COM' -> 'ravi@gmail.com'
    """
    if not email_str or not isinstance(email_str, str):
        return None
    
    clean = email_str.strip().lower()
    try:
        # Check syntax without needing live DNS lookup
        valid = validate_email(clean, check_deliverability=False)
        return valid.normalized
    except EmailNotValidError:
        # Regex fallback for standard emails
        match = re.search(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}", clean)
        if match:
            return match.group(0).lower()
        return None


def normalize_phone(phone_str: Optional[str], default_region: str = "IN") -> Optional[str]:
    """
    Normalizes phone numbers to standard E.164 international format.
    Example: '+91-98765 43210' -> '+919876543210'
    """
    if not phone_str:
        return None
    
    phone_s = str(phone_str).strip()
    if not phone_s:
        return None
    
    # Try phonenumbers parse
    try:
        # If starts with +
        if phone_s.startswith("+"):
            parsed = phonenumbers.parse(phone_s, None)
        else:
            parsed = phonenumbers.parse(phone_s, default_region)
            
        if phonenumbers.is_valid_number(parsed) or phonenumbers.is_possible_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
        
    # Clean fallback: extract digits
    digits = re.sub(r"[^\d+]", "", phone_s)
    if len(digits) >= 10:
        if not digits.startswith("+") and len(digits) == 10:
            return f"+91{digits}" if default_region == "IN" else f"+1{digits}"
        return digits
        
    return None


def normalize_number(num_val: Any) -> Optional[Union[int, float]]:
    """
    Normalizes currency / formatted numbers by removing symbols, codes, and commas.
    Example: '₹10,000' -> 10000, '$1,234.56' -> 1234.56, 'INR 15,000' -> 15000
    """
    if num_val is None:
        return None
    if isinstance(num_val, (int, float)):
        return num_val
        
    val_str = str(num_val).strip()
    if not val_str:
        return None
        
    # Strip currency codes and symbols: INR, USD, EUR, GBP, Rs., Rs, ₹, $, €, £, ¥, etc.
    cleaned = re.sub(r"(?i)\b(inr|usd|eur|gbp|rs\.?)\b", "", val_str)
    cleaned = re.sub(r"[₹\$€£¥\s]", "", cleaned)
    # Remove thousands separators (commas)
    cleaned = cleaned.replace(",", "")
    
    # Check if integer or float
    try:
        if "." in cleaned:
            f = float(cleaned)
            return round(f, 4)
        else:
            return int(cleaned)
    except ValueError:
        return None


def normalize_postal_code(code_val: Any) -> Optional[str]:
    """
    Normalizes ZIP / PIN postal codes.
    """
    if not code_val:
        return None
    val_str = str(code_val).strip()
    # Remove extra spaces
    cleaned = re.sub(r"\s+", "", val_str)
    if re.match(r"^\d{5,6}(-\d{4})?$", cleaned):
        return cleaned
    return cleaned if len(cleaned) <= 10 else None


def normalize_text(text_val: Any) -> Optional[str]:
    """
    Trims whitespace and standardizes single line text.
    """
    if text_val is None:
        return None
    s = " ".join(str(text_val).strip().split())
    return s if s else None
