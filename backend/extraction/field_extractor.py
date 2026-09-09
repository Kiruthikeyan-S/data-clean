import re
from typing import Dict, Any, Optional, List
from backend.normalization.normalizer import (
    normalize_name,
    normalize_date,
    normalize_email,
    normalize_phone,
    normalize_number,
    normalize_postal_code,
    normalize_text
)

# Common field keywords and extraction patterns
PATTERNS = {
    "email": r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}",
    "phone": r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}",
    "postal_code": r"\b\d{5,6}\b",
    "amount": r"(?:₹|\$|€|£|INR|USD|EUR|GBP|Rs\.?|Total|Amount|Price)\s*[:=]?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)",
    "dob": r"(?:DOB|Date of Birth|Birth Date|D\.O\.B\.?)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})",
    "date": r"(?:Date|Dated|Invoice Date|Created Date|Issued)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})",
    "id_number": r"(?:ID|ID No|ID Number|Aadhaar|PAN|Passport|SSN|License No|Reg No|Account No|Invoice No)\s*[:=\-#]\s*([A-Za-z0-9\-\/]{4,25})",
}

# Line-level label matchers
LABEL_PATTERNS = {
    "name": [
        r"^(?:Name|Full Name|Customer Name|Patient Name|Employee Name|Candidate Name|Contact Name|Student Name|Applicant)\s*[:=\-]\s*(.+)$",
        r"^(?:Mr\.|Ms\.|Mrs\.|Dr\.)\s+([A-Za-z\s]{3,35})$"
    ],
    "organization": [
        r"^(?:Company|Organization|Employer|Institution|University|Hospital|Client|Vendor|Firm)\s*[:=\-]\s*(.+)$"
    ],
    "address": [
        r"^(?:Address|Residence|Location|Street Address|Billing Address|Shipping Address)\s*[:=\-]\s*(.+)$"
    ],
    "city": [
        r"^(?:City|Town|District)\s*[:=\-]\s*(.+)$"
    ],
    "postal_code": [
        r"^(?:Postal Code|PIN Code|ZIP Code|PIN|ZIP)\s*[:=\-]\s*(.+)$"
    ],
    "amount": [
        r"^(?:Total Amount|Grand Total|Net Amount|Total|Amount Paid|Subtotal|Fee|Price)\s*[:=\-]\s*(.+)$"
    ]
}

HEADER_STOPWORDS = {
    "INVOICE", "RECEIPT", "STATEMENT", "REPORT", "RESUME", "CURRICULUM", "CERTIFICATE",
    "PROFILE", "CUSTOMER PROFILE", "USER PROFILE", "EMPLOYEE PROFILE", "DETAILS", "SUMMARY", "DATA"
}


def identify_fields(raw_text: str) -> Dict[str, Any]:
    """
    Identifies common structured entities from unstructured raw text using regex,
    rules, and keyword heuristics.
    """
    if not raw_text:
        return {}

    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    extracted_raw: Dict[str, Any] = {
        "name": None,
        "dob": None,
        "date": None,
        "email": None,
        "phone": None,
        "address": None,
        "id_number": None,
        "amount": None,
        "organization": None,
        "city": None,
        "postal_code": None
    }

    # 1. Regex pattern scans across full text
    # Email
    email_match = re.search(PATTERNS["email"], raw_text, re.IGNORECASE)
    if email_match:
        extracted_raw["email"] = email_match.group(0)

    # DOB specifically
    dob_match = re.search(PATTERNS["dob"], raw_text, re.IGNORECASE)
    if dob_match:
        extracted_raw["dob"] = dob_match.group(1).strip()

    # General Date (if distinct from DOB)
    date_match = re.search(PATTERNS["date"], raw_text, re.IGNORECASE)
    if date_match:
        extracted_raw["date"] = date_match.group(1).strip()
    elif not extracted_raw["dob"]:
        gen_date = re.search(r"\b(\d{1,4}[/\-\.]\d{1,2}[/\-\.]\d{1,4})\b", raw_text)
        if gen_date:
            extracted_raw["date"] = gen_date.group(1).strip()

    # ID Number
    id_match = re.search(PATTERNS["id_number"], raw_text, re.IGNORECASE)
    if id_match:
        extracted_raw["id_number"] = id_match.group(1).strip()

    # 2. First pass: Line-by-line explicit label matching
    for i, line in enumerate(lines):
        for field, patterns in LABEL_PATTERNS.items():
            if extracted_raw[field] is None:
                for pat in patterns:
                    m = re.search(pat, line, re.IGNORECASE)
                    if m:
                        val = m.group(1).strip()
                        if not val and i + 1 < len(lines):
                            val = lines[i + 1].strip()
                        extracted_raw[field] = val
                        break

        # Phone matching per line if explicit Phone: header
        if extracted_raw["phone"] is None:
            if re.search(r"(?:Phone|Mobile|Tel|Cell|Contact)\s*[:=\-]?\s*(.+)", line, re.IGNORECASE):
                pm = re.search(PATTERNS["phone"], line)
                if pm:
                    extracted_raw["phone"] = pm.group(0).strip()

        # Postal code in address lines
        if extracted_raw["postal_code"] is None and ("PIN" in line.upper() or "ZIP" in line.upper()):
            pin_m = re.search(r"\b\d{5,6}\b", line)
            if pin_m:
                extracted_raw["postal_code"] = pin_m.group(0)

        # Amount matching
        if extracted_raw["amount"] is None:
            amt_m = re.search(PATTERNS["amount"], line, re.IGNORECASE)
            if amt_m:
                extracted_raw["amount"] = amt_m.group(1)

    # 3. Second pass: Fallbacks only if explicit labels didn't find the entity
    # Fallback Phone
    if extracted_raw["phone"] is None:
        for line in lines:
            pm = re.search(PATTERNS["phone"], line)
            if pm and len(re.sub(r"\D", "", pm.group(0))) >= 10:
                extracted_raw["phone"] = pm.group(0).strip()
                break

    # Fallback Name heuristics: first line if looks like a person's name (2-4 capitalized words, no punctuation/numbers)
    if extracted_raw["name"] is None and len(lines) > 0:
        for line in lines[:3]:
            if line.upper() in HEADER_STOPWORDS:
                continue
            if any(sw in line.upper() for sw in ["PROFILE", "INVOICE", "RECEIPT", "STATEMENT", "REPORT", "SUMMARY"]):
                continue
            if re.match(r"^[A-Z][a-zA-Z\.\']+(\s+[A-Z][a-zA-Z\.\']+){1,3}$", line) and len(line) < 35:
                extracted_raw["name"] = line
                break

    return extracted_raw


def map_to_schema(extracted_raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalizes and maps extracted raw entities into standardized field items.
    """
    field_configs = [
        ("name", "Name", "text", normalize_name),
        ("dob", "Date of Birth", "date", normalize_date),
        ("date", "Document Date", "date", normalize_date),
        ("email", "Email", "email", normalize_email),
        ("phone", "Phone", "phone", normalize_phone),
        ("address", "Address", "text", normalize_text),
        ("city", "City", "text", normalize_name),
        ("postal_code", "Postal Code", "postal_code", normalize_postal_code),
        ("id_number", "ID Number", "text", normalize_text),
        ("organization", "Organization", "text", normalize_text),
        ("amount", "Amount", "number", normalize_number),
    ]

    mapped_fields = []
    for key, label, ftype, norm_func in field_configs:
        raw_val = extracted_raw.get(key)
        norm_val = norm_func(raw_val) if raw_val is not None else None
        
        mapped_fields.append({
            "key": key,
            "label": label,
            "field_type": ftype,
            "raw_value": raw_val,
            "value": norm_val,
            "confidence": 0.95 if norm_val is not None else None,
            "is_valid": True,
            "error_message": None
        })

    return mapped_fields
