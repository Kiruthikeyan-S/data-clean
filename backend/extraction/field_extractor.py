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
    "postal_code": r"\b\d{5}(?:-\d{4})?\b|\b\d{6}\b",
    "amount": r"(?:₹|\$|€|£|INR|USD|EUR|GBP|Rs\.?|Total|Amount|Price|Postage)\s*[:=]?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)",
    "dob": r"(?:DOB|Date of Birth|Birth Date|D\.O\.B\.?)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})",
    "date": r"(?:Date|Dated|Invoice Date|Created Date|Issued|Ship Date)\s*[:=\-]\s*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})",
    "id_number": r"(?:ID|ID No|ID Number|Aadhaar|PAN|Passport|SSN|License No|Reg No|Account No|Invoice No)\s*[:=\-#]\s*([A-Za-z0-9\-\/]{4,25})",
    "tracking_number": r"\b(9[1-5]\d{20,24}|1Z[0-9A-Z]{16}|\d{12}|\d{20,26})\b",
    "carrier": r"\b(USPS|FEDEX|UPS|DHL|AMAZON LOGISTICS|ONTRAC|PUROLATOR)\b",
    "service_type": r"\b(PRIORITY\s+MAIL(?:\s+2-DAY|\s+3-DAY|\s+EXPRESS)?|FIRST-CLASS\s+PACKAGE|GROUND\s+ADVANTAGE|STANDARD\s+OVERNIGHT|PRIORITY\s+OVERNIGHT|2DAY|GROUND|EXPRESS)\b",
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
    ],
    "carrier": [
        r"^(?:Carrier|Shipping Carrier|Delivery Service)\s*[:=\-]\s*(.+)$"
    ],
    "service_type": [
        r"^(?:Service Type|Service|Class of Mail)\s*[:=\-]\s*(.+)$"
    ],
    "tracking_number": [
        r"^(?:Tracking\s*(?:#|No|Number)?|Tracking|Waybill|AWB|Package ID)\s*[:=\-#]\s*([A-Za-z0-9\s]{10,35})$"
    ],
    "recipient_name": [
        r"^(?:Recipient\s+Name|Deliver\s+To|Ship\s+To|Recipient|Consignee|Addressee)\s*(?:\([^)]*\))?\s*[:=\-]\s*(.+)$"
    ],
    "sender_name": [
        r"^(?:Sender\s+Name|Ship\s+From|Sender|Shipper|Return\s+To)\s*(?:\([^)]*\))?\s*[:=\-]\s*(.+)$"
    ],
    "postage_amount": [
        r"^(?:Postage|Postage\s+Paid|Shipping\s+Fee|Total\s+Postage)\s*[:=\-]\s*(.+)$"
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
        "postal_code": None,
        "carrier": None,
        "service_type": None,
        "tracking_number": None,
        "recipient_name": None,
        "recipient_address": None,
        "sender_name": None,
        "sender_address": None,
        "postage_amount": None,
        "delivery_instructions": None
    }

    # 1. Regex pattern scans across full text
    # Carrier
    carrier_m = re.search(PATTERNS["carrier"], raw_text, re.IGNORECASE)
    if carrier_m:
        extracted_raw["carrier"] = carrier_m.group(1).upper()

    # Service Type
    service_m = re.search(PATTERNS["service_type"], raw_text, re.IGNORECASE)
    if service_m:
        extracted_raw["service_type"] = service_m.group(1).title()

    # Tracking Number
    track_m = re.search(PATTERNS["tracking_number"], raw_text)
    if track_m:
        extracted_raw["tracking_number"] = track_m.group(1).replace(" ", "")

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

    # Shipping Label Multi-line Ship To / Deliver To
    ship_to_m = re.search(r'(?:SHIP\s+TO|DELIVER\s+TO)\s*(?:\([^)]*\))?\s*[:=\-]?\s*\n([^\n]+(?:\n[^\n]+){1,4})', raw_text, re.IGNORECASE)
    if ship_to_m:
        to_lines = [l.strip() for l in ship_to_m.group(1).splitlines() if l.strip()]
        clean_lines = []
        for tl in to_lines:
            sub = re.sub(r'^(?:Recipient\s+Name|Name|Company|Address|Delivery\s+Address)\s*[:=\-]\s*', '', tl, flags=re.I).strip()
            if sub and not sub.startswith('('):
                clean_lines.append(sub)
        if clean_lines:
            extracted_raw["recipient_name"] = clean_lines[0]
            if len(clean_lines) > 1:
                extracted_raw["recipient_address"] = ", ".join(clean_lines[1:])

    # Shipping Label Multi-line Ship From / Sender
    ship_from_m = re.search(r'(?:SHIP\s+FROM|FROM|RETURN\s+TO)\s*(?:\([^)]*\))?\s*[:=\-]?\s*\n([^\n]+(?:\n[^\n]+){1,3})', raw_text, re.IGNORECASE)
    if ship_from_m:
        from_lines = [l.strip() for l in ship_from_m.group(1).splitlines() if l.strip()]
        clean_lines = []
        for fl in from_lines:
            sub = re.sub(r'^(?:Sender\s+Name|Name|Address|Contact\s+Phone)\s*[:=\-]\s*', '', fl, flags=re.I).strip()
            if sub and not sub.startswith('('):
                clean_lines.append(sub)
        if clean_lines:
            extracted_raw["sender_name"] = clean_lines[0]
            if len(clean_lines) > 1:
                extracted_raw["sender_address"] = ", ".join(clean_lines[1:])

    # Postage amount specifically
    postage_m = re.search(r'(?:Postage|Paid)\s*[:=]?\s*\$([0-9]+\.[0-9]{2})', raw_text, re.IGNORECASE)
    if postage_m:
        extracted_raw["postage_amount"] = postage_m.group(1)

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

        # Phone matching per line if explicit Phone: header (MUST be 7-15 digits to avoid tracking numbers)
        if extracted_raw["phone"] is None:
            if re.search(r"(?:Phone|Mobile|Tel|Cell|Contact)\s*[:=\-]?\s*(.+)", line, re.IGNORECASE):
                pm = re.search(PATTERNS["phone"], line)
                if pm:
                    digits = re.sub(r"\D", "", pm.group(0))
                    if 7 <= len(digits) <= 15:
                        extracted_raw["phone"] = pm.group(0).strip()

        # Postal code in address lines
        if extracted_raw["postal_code"] is None and ("PIN" in line.upper() or "ZIP" in line.upper()):
            pin_m = re.search(r"\b\d{5}(?:-\d{4})?\b|\b\d{6}\b", line)
            if pin_m:
                extracted_raw["postal_code"] = pin_m.group(0)

        # Amount matching
        if extracted_raw["amount"] is None:
            amt_m = re.search(PATTERNS["amount"], line, re.IGNORECASE)
            if amt_m:
                extracted_raw["amount"] = amt_m.group(1)

    # 3. Second pass: Fallbacks only if explicit labels didn't find the entity
    # Fallback Phone (strictly 10-15 digits, ignoring 16+ barcode/tracking numbers)
    if extracted_raw["phone"] is None:
        for line in lines:
            pm = re.search(PATTERNS["phone"], line)
            if pm:
                digits = re.sub(r"\D", "", pm.group(0))
                if 10 <= len(digits) <= 15:
                    extracted_raw["phone"] = pm.group(0).strip()
                    break

    # Fallback Name heuristics: first line if looks like a person's name (2-4 capitalized words, no punctuation/numbers)
    if extracted_raw["name"] is None and len(lines) > 0:
        for line in lines[:3]:
            if line.upper() in HEADER_STOPWORDS:
                continue
            if any(sw in line.upper() for sw in ["PROFILE", "INVOICE", "RECEIPT", "STATEMENT", "REPORT", "SUMMARY", "PRIORITY", "USPS", "FEDEX", "UPS", "MAIL"]):
                continue
            if re.match(r"^[A-Z][a-zA-Z\.\']+(\s+[A-Z][a-zA-Z\.\']+){1,3}$", line) and len(line) < 35:
                extracted_raw["name"] = line
                break

    return extracted_raw


def map_to_schema(extracted_raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalizes and maps extracted raw entities into standardized field items.
    ONLY includes fields that actually have extracted data in the document.
    """
    field_configs = [
        ("carrier", "Carrier", "text", normalize_text),
        ("service_type", "Service Type", "text", normalize_text),
        ("tracking_number", "Tracking Number", "text", normalize_text),
        ("recipient_name", "Recipient Name", "text", normalize_name),
        ("recipient_company", "Recipient Company", "text", normalize_text),
        ("recipient_address", "Recipient Address", "text", normalize_text),
        ("sender_name", "Sender Name", "text", normalize_name),
        ("sender_address", "Sender Address", "text", normalize_text),
        ("postage_amount", "Postage Paid", "number", normalize_number),
        ("delivery_instructions", "Delivery Instructions", "text", normalize_text),
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


def extract_records_from_unstructured_text(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Rule-based parser that segments unstructured text containing multiple records
    (e.g., repeating profiles, numbered lists, multi-line blocks, customer rosters)
    into a standardized tabular records dataset.
    """
    if not raw_text or not raw_text.strip():
        return None

    # Check if text represents a technical test report (TC-001 ... TC-100)
    tc_pattern = re.compile(
        r'(?:^|\n)\s*TC-[\s\n]*(\d{3})\s*\n'
        r'(.*?)'
        r'([0-9,.]+\s*(?:ms|s|seconds))'
        r'[\s\n]+(PASS|FAIL|P|F)\b',
        re.DOTALL
    )
    tc_matches = list(tc_pattern.finditer(raw_text))
    if len(tc_matches) >= 2:
        recs = []
        for m in tc_matches:
            tc_id = f"TC-{m.group(1)}"
            body = m.group(2).strip()
            exec_time = m.group(3).strip().replace('\n', ' ')
            status = "PASS" if m.group(4).strip() in ("PASS", "P") else "FAIL"
            lines = [l.strip() for l in body.splitlines() if l.strip()]
            desc = lines[0] if lines else "Verification Test"
            inp = lines[1] if len(lines) > 1 else ""
            exp = lines[2] if len(lines) > 2 else "Pass verification"
            act = " ".join(lines[3:]) if len(lines) > 3 else exp
            recs.append({
                "test_case_id": tc_id,
                "description": desc,
                "input_data": inp,
                "expected_result": exp,
                "actual_result": act,
                "execution_time": exec_time,
                "status": status
            })
        if recs:
            return {
                "data_type": "records",
                "columns": ["test_case_id", "description", "input_data", "expected_result", "actual_result", "execution_time", "status"],
                "records": recs,
                "document_type": "technical_test_report"
            }

    # Check if text represents a Book or Educational Document (Chapters / Sections)
    chapter_pattern = re.compile(
        r'(?:^|\n)\s*(?:Chapter\s+(\d+|[IVXLCDM]+)|Section\s+(\d+(?:\.\d+)*))\s*[:\-–—]?\s*([^\n]+)',
        re.IGNORECASE
    )
    chap_matches = list(chapter_pattern.finditer(raw_text))
    if len(chap_matches) >= 2:
        recs = []
        for idx, m in enumerate(chap_matches):
            chap_num = m.group(1) or m.group(2)
            chap_title = m.group(3).strip()
            start_pos = m.end()
            end_pos = chap_matches[idx + 1].start() if idx + 1 < len(chap_matches) else len(raw_text)
            body = raw_text[start_pos:end_pos].strip()
            summary = (body[:200] + "...") if len(body) > 200 else body
            summary = re.sub(r'\s+', ' ', summary).strip()
            recs.append({
                "chapter_number": f"Chapter {chap_num}" if not chap_num.lower().startswith("section") else chap_num,
                "chapter_title": chap_title,
                "summary": summary,
                "character_count": len(body)
            })
        if len(recs) >= 2:
            return {
                "data_type": "records",
                "columns": ["chapter_number", "chapter_title", "summary", "character_count"],
                "records": recs,
                "document_type": "book_educational"
            }

    # 1. Check for multiple occurrences of primary record headers (e.g. at least 2 "Name:", "Record:", or numbered items)
    name_headers = re.findall(r'(?:^|\n)\s*(?:Name|Full Name|Customer Name|Employee Name|Candidate Name|Contact Name|User Name)\s*[:=\-]', raw_text, flags=re.IGNORECASE)
    numbered_headers = re.findall(r'(?:^|\n)\s*(?:\d+[\.\)]|\#\d+|\[\d+\]|Record\s+\d+|Item\s+\d+|Profile\s+\d+|Employee\s+\d+)\s+', raw_text, flags=re.IGNORECASE)

    best_blocks: List[str] = []

    # Case A: At least 2 numbered items
    if len(numbered_headers) >= 2:
        chunks = [c.strip() for c in re.split(r'\n(?=\s*(?:\d+[\.\)]|\#\d+|\[\d+\]|Record\s+\d+|Item\s+\d+|Profile\s+\d+|Employee\s+\d+)\s+)', raw_text, flags=re.IGNORECASE) if c.strip()]
        if len(chunks) >= 2:
            best_blocks = chunks

    # Case B: Explicit horizontal separators (---, ===)
    elif len(re.findall(r'\n\s*[-=_]{3,}\s*\n', raw_text)) >= 1:
        chunks = [c.strip() for c in re.split(r'\n\s*[-=_]{3,}\s*\n', raw_text) if c.strip()]
        if len(chunks) >= 2:
            best_blocks = chunks

    # Case C: At least 2 repeated "Name:" headers
    elif len(name_headers) >= 2:
        chunks = [c.strip() for c in re.split(r'(?=(?:^|\n)\s*(?:Name|Full Name|Customer Name|Employee Name|Candidate Name|Contact Name|User Name)\s*[:=\-])', raw_text, flags=re.IGNORECASE) if c.strip()]
        if len(chunks) >= 2:
            best_blocks = chunks

    if len(best_blocks) < 2:
        return None

    all_records: List[Dict[str, Any]] = []
    for block in best_blocks:
        raw_fields = identify_fields(block)
        mapped = map_to_schema(raw_fields)
        row = {f["key"]: f["value"] for f in mapped if f["value"] is not None}
        
        # Keep row if it has at least 2 non-empty fields or 1 strong identifier (name/email/phone/id_number)
        if len(row) >= 2 or any(k in row for k in ["name", "email", "phone", "id_number"]):
            all_records.append(row)

    if len(all_records) >= 2:
        # Collect all columns in order
        all_cols: List[str] = []
        for r in all_records:
            for k in r.keys():
                if k not in all_cols:
                    all_cols.append(k)

        # Filter empty columns
        valid_cols = [c for c in all_cols if any(r.get(c) for r in all_records)]
        if not valid_cols:
            valid_cols = all_cols

        final_records = [{c: r.get(c) for c in valid_cols} for r in all_records]
        return {
            "data_type": "records",
            "columns": valid_cols,
            "records": final_records
        }

    return None

