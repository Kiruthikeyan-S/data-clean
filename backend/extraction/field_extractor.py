import re
from typing import Dict, Any, Optional, List, Tuple
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
    "amount": r"(?:₹|\$|€|£|INR|USD|EUR|GBP|Rs\.?|Total|Amount|Price|Grand Total|Net Amount)\s*[:=]?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)",
    "dob": r"(?:DOB|Date of Birth|Birth Date|D\.O\.B\.?)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})",
    "date": r"(?:Date|Dated|Invoice Date|Created Date|Order Date|Issued)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})",
    "id_number": r"(?:ID|ID No|ID Number|Aadhaar|PAN|Passport|SSN|License No|Reg No|Account No|Invoice No|Order ID|Order No|Receipt No)\s*[:=\-#]\s*([A-Za-z0-9\-\/]{3,30})",
    "payment_method": r"(?:Payment Method|Payment Mode|Paid Via|Payment)\s*[:=\-]\s*(Cash|Card|Credit Card|Debit Card|UPI|Net Banking|Online|PayPal|GPay|Apple Pay)",
    "quantity": r"(?:Qty|Quantity|Units|Items Count)\s*[:=\-]?\s*(\d+)",
}

# Line-level label matchers
LABEL_PATTERNS = {
    "name": [
        r"^(?:Name|Full Name|Customer Name|Patient Name|Employee Name|Candidate Name|Contact Name|Student Name|Applicant|Buyer)\s*[:=\-]\s*(.+)$",
        r"^(?:Mr\.|Ms\.|Mrs\.|Dr\.)\s+([A-Za-z\s]{3,35})$"
    ],
    "store_name": [
        r"^(?:Store|Store Name|Branch|Branch Name|Retailer|Shop|Outlet|Merchant)\s*[:=\-]\s*(.+)$"
    ],
    "item_name": [
        r"^(?:Product|Item|Item Name|Product Name|Description|Item Description)\s*[:=\-]\s*(.+)$"
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
        r"^(?:Total Amount|Grand Total|Net Amount|Total|Amount Paid|Subtotal|Fee|Price|Balance Due)\s*[:=\-]\s*(.+)$"
    ],
    "id_number": [
        r"^(?:Invoice Number|Invoice No|Order Number|Order ID|Bill Number|Bill No|Receipt No|Transaction ID)\s*[:=\-#]\s*(.+)$"
    ],
    "payment_method": [
        r"^(?:Payment Method|Payment Mode|Paid By|Paid Via)\s*[:=\-]\s*(.+)$"
    ]
}

HEADER_STOPWORDS = {
    "INVOICE", "RECEIPT", "STATEMENT", "REPORT", "RESUME", "CURRICULUM", "CERTIFICATE",
    "PROFILE", "CUSTOMER PROFILE", "USER PROFILE", "EMPLOYEE PROFILE", "DETAILS", "SUMMARY", "DATA",
    "TAX INVOICE", "RETAIL INVOICE", "PURCHASE ORDER"
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
        "store_name": None,
        "item_name": None,
        "dob": None,
        "date": None,
        "email": None,
        "phone": None,
        "address": None,
        "id_number": None,
        "amount": None,
        "payment_method": None,
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

    # Payment Method
    pm_match = re.search(PATTERNS["payment_method"], raw_text, re.IGNORECASE)
    if pm_match:
        extracted_raw["payment_method"] = pm_match.group(1).strip()

    # 2. First pass: Line-by-line explicit label matching
    for i, line in enumerate(lines):
        for field, patterns in LABEL_PATTERNS.items():
            if extracted_raw.get(field) is None:
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


def evaluate_heuristic_confidence(extracted_raw: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    """
    Evaluates whether the Rule-Based Heuristic extraction is complete and high-confidence,
    allowing the system to safely BYPASS the LLM.
    
    Returns:
        {
            "confidence_score": float (0.0 to 1.0),
            "can_bypass_llm": bool,
            "matched_fields_count": int,
            "reasons": List[str]
        }
    """
    if not raw_text or not extracted_raw:
        return {"confidence_score": 0.0, "can_bypass_llm": False, "matched_fields_count": 0, "reasons": ["Empty input"]}

    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    num_lines = len(lines)

    # Count non-null extracted fields
    matched_fields = [k for k, v in extracted_raw.items() if v is not None and str(v).strip()]
    matched_count = len(matched_fields)

    # Check for multi-row tabular signals (e.g. repeated commas, pipes, or tab-delimited records)
    has_table_headers = any(re.search(r"\b(id|sku|item|product|price|qty|total|tax)\b.*\b(id|sku|item|product|price|qty|total|tax)\b", l, re.IGNORECASE) for l in lines)
    is_multi_row_table = (num_lines > 5 and has_table_headers and any("," in l or "|" in l or "\t" in l for l in lines[1:6]))

    # Key entity anchors
    has_identity = bool(extracted_raw.get("name") or extracted_raw.get("id_number") or extracted_raw.get("email") or extracted_raw.get("store_name"))
    has_contact = bool(extracted_raw.get("email") or extracted_raw.get("phone") or extracted_raw.get("address"))
    has_transaction = bool(extracted_raw.get("amount") or extracted_raw.get("date") or extracted_raw.get("id_number"))

    # Confidence calculation
    reasons = []
    confidence = 0.50

    if matched_count >= 4:
        confidence += 0.30
        reasons.append(f"Heuristically extracted {matched_count} distinct entities")
    elif matched_count >= 2:
        confidence += 0.15
        reasons.append(f"Heuristically extracted {matched_count} entities")

    if has_identity:
        confidence += 0.10
        reasons.append("Identified primary entity/name")
    if has_transaction:
        confidence += 0.05
        reasons.append("Identified transaction/financial indicators")

    # If document has high ratio of matched lines
    if num_lines > 0 and (matched_count / max(num_lines, 1)) >= 0.4:
        confidence += 0.05

    confidence = min(1.0, round(confidence, 2))

    # LLM Bypass condition:
    # 1. Confidence >= 0.85
    # 2. Contains identity & either contact or transaction
    # 3. Not a multi-row structured table requiring complex row decomposition
    can_bypass = (confidence >= 0.85 and (has_identity and (has_contact or has_transaction)) and not is_multi_row_table)

    return {
        "confidence_score": confidence,
        "can_bypass_llm": can_bypass,
        "matched_fields_count": matched_count,
        "matched_fields": matched_fields,
        "reasons": reasons
    }


def map_to_schema(extracted_raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalizes and maps extracted raw entities into standardized field items.
    ONLY includes fields that actually have extracted data in the document.
    """
    field_configs = [
        ("name", "Name", "text", normalize_name),
        ("store_name", "Store Name", "text", normalize_name),
        ("item_name", "Item / Product", "text", normalize_text),
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
        ("payment_method", "Payment Method", "text", normalize_text),
    ]

    mapped_fields = []
    for key, label, ftype, norm_func in field_configs:
        raw_val = extracted_raw.get(key)
        if raw_val is not None and str(raw_val).strip():
            norm_val = norm_func(raw_val)
            mapped_fields.append({
                "key": key,
                "label": label,
                "field_type": ftype,
                "raw_value": str(raw_val).strip(),
                "value": norm_val if norm_val is not None else str(raw_val).strip(),
                "confidence": 0.95,
                "is_valid": True,
                "error_message": None
            })

    return mapped_fields
