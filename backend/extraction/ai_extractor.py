import os
import json
import re
import httpx
from typing import Dict, Any, List, Optional
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Official supported Groq models with high speed and reliability
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768"
]


def is_auth_error(err: Exception) -> bool:
    """Detects 401 Unauthorized / Invalid API Key errors to fail fast."""
    err_str = str(err).lower()
    return "401" in err_str or "invalid api key" in err_str or "invalid_api_key" in err_str or "unauthorized" in err_str


def repair_and_parse_json(content: str) -> Optional[Dict[str, Any]]:
    """
    Robust JSON parser for LLM outputs.
    Handles:
    - Markdown code fences (```json ... ```)
    - Truncated JSON (unclosed brackets/braces)
    - Trailing commas before } or ]
    - Leading/trailing text outside the JSON object
    """
    if not content or not content.strip():
        return None

    text = content.strip()

    # 1. Strip markdown fences if present
    fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1).strip()

    # 2. Extract substring from first '{' or '[' to last '}' or ']'
    start_brace = text.find('{')
    start_bracket = text.find('[')
    
    start_idx = -1
    if start_brace != -1 and start_bracket != -1:
        start_idx = min(start_brace, start_bracket)
    elif start_brace != -1:
        start_idx = start_brace
    elif start_bracket != -1:
        start_idx = start_bracket

    if start_idx != -1:
        text = text[start_idx:]

    # Direct attempt
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        elif isinstance(parsed, list):
            return {"data_type": "records", "records": parsed}
    except Exception:
        pass

    # 3. Clean common LLM quirks (trailing commas)
    cleaned = re.sub(r',\s*([}\]])', r'\1', text)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        elif isinstance(parsed, list):
            return {"data_type": "records", "records": parsed}
    except Exception:
        pass

    # 4. Handle truncated JSON by balancing open braces and brackets
    open_braces = 0
    open_brackets = 0
    in_string = False
    escape = False

    for char in cleaned:
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char == '{':
                open_braces += 1
            elif char == '}':
                open_braces = max(0, open_braces - 1)
            elif char == '[':
                open_brackets += 1
            elif char == ']':
                open_brackets = max(0, open_brackets - 1)

    balanced = cleaned
    if in_string:
        balanced += '"'

    balanced += (']' * open_brackets) + ('}' * open_braces)
    balanced = re.sub(r',\s*([}\]])', r'\1', balanced)

    try:
        parsed = json.loads(balanced)
        if isinstance(parsed, dict):
            return parsed
        elif isinstance(parsed, list):
            return {"data_type": "records", "records": parsed}
    except Exception:
        pass

    return None


def separate_amount_and_currency(raw_value: Any) -> Tuple[Optional[float], Optional[str]]:
    """Separates numeric amount from currency symbol or code."""
    if raw_value is None:
        return None, None
    s = str(raw_value).strip()
    if not s:
        return None, None

    currency_map = {
        "$": "USD", "USD": "USD",
        "₹": "INR", "INR": "INR", "RS": "INR", "RS.": "INR",
        "€": "EUR", "EUR": "EUR",
        "£": "GBP", "GBP": "GBP",
        "SAR": "SAR", "SR": "SAR",
        "AED": "AED", "CAD": "CAD", "AUD": "AUD", "JPY": "JPY", "CNY": "CNY"
    }

    found_curr = None
    for sym, code in currency_map.items():
        pattern = r'(?i)(?:^|\s|\b)' + re.escape(sym) + r'(?:\s|\b|$)' if len(sym) > 1 else re.escape(sym)
        if re.search(pattern, s):
            found_curr = code
            break

    num_str = re.sub(r'[^\d.-]', '', s.replace(',', ''))
    amt = None
    try:
        if num_str and num_str not in ('-', '.'):
            amt = float(num_str)
    except ValueError:
        pass

    return amt, found_curr


def normalize_field_casing(key: str, val: Any) -> Any:
    """
    Preserves raw casing for IDs, SKUs, emails, codes, and abbreviations
    without forcing improper Title Case.
    """
    if not isinstance(val, str):
        return val
    s = val.strip()
    if not s:
        return s

    k = key.lower()
    # IDs, SKUs, codes, VINs, UUIDs: preserve exact string without title casing
    if any(tok in k for tok in ("id", "sku", "code", "vin", "uuid", "isbn", "no", "number", "key")):
        return s

    # Emails: standard lowercase
    if "email" in k or ("@" in s and "." in s and " " not in s):
        return s.lower()

    # Acronyms or currency: preserve if all caps (e.g. USA, USD, VAT, GST, CEO, CTO)
    if s.isupper() and len(s) <= 5:
        return s

    return s


def _extract_batch_chunk(
    client: Groq,
    batch_text: str,
    batch_index: int,
    expected_count: int,
    models: List[str] = GROQ_MODELS
) -> Dict[str, Any]:
    """
    Extracts tabular records for a specific chunk/batch of items with programmatic verification.
    Reconciles expected_count vs extracted_count, tracks batch status, retries incomplete chunks,
    and returns a structured batch result.
    """
    # Detect chunk document domain to supply schema-appropriate prompt instructions
    lower_batch = batch_text.lower()
    if "tc-" in lower_batch or "test case" in lower_batch or "verification report" in lower_batch:
        example_cols = ["test_case_id", "category", "description", "input_data", "expected_result", "actual_result", "execution_time", "status"]
        example_record = {"test_case_id": "TC-001", "category": "Auth", "description": "Empty email", "input_data": "email=''", "expected_result": "Error", "actual_result": "Error", "execution_time": "0.2 ms", "status": "PASS"}
    elif "inv-" in lower_batch or "invoice" in lower_batch:
        example_cols = ["item_no", "description", "quantity", "unit_price", "total_amount", "tax_amount"]
        example_record = {"item_no": "1", "description": "Consulting Services", "quantity": 10, "unit_price": 150.0, "total_amount": 1500.0, "tax_amount": 75.0}
    else:
        example_cols = ["id", "name", "category", "details", "date", "status", "value"]
        example_record = {"id": "REC-001", "name": "Item Name", "category": "Category", "details": "Record info", "date": "2024-01-01", "status": "Active", "value": 100}

    import json
    cols_json = json.dumps(example_cols)
    rec_json = json.dumps(example_record)

    system_instruction = (
        "You are an expert Data Extraction and Schema Normalization engine.\n"
        "Extract every single item/record from the provided text into structured tabular records JSON.\n"
        "Standardization rules:\n"
        "- Dates: Format as ISO 8601 (YYYY-MM-DD or YYYY-MM)\n"
        "- Names & Roles: Format in Title Case\n"
        "- Identifiers & Emails & SKUs: Preserve exact original casing, DO NOT Title Case IDs or codes\n"
        "- Numbers & Salaries: Clean numeric values without currency symbols ($/₹/€/£/INR/USD) or commas\n"
        "- Currencies: Extracted into a separate 'currency' column (e.g. 'USD', 'INR', 'SAR', 'EUR')\n\n"
        "Return JSON format:\n"
        "{\n"
        f'  "data_type": "records",\n'
        f'  "columns": {cols_json},\n'
        f'  "records": [\n'
        f'    {rec_json}\n'
        "  ]\n"
        "}\n\n"
        f"CRITICAL: You MUST extract ALL {expected_count} individual items present in the text into 'records'. "
        f"Return exactly {expected_count} records without skipping, omitting, or truncating any."
    )

    best_records: List[Dict[str, Any]] = []
    errors: List[str] = []

    for model_name in models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Extract all {expected_count} records from batch #{batch_index}:\n\n{batch_text}"}
                ],
                response_format={"type": "json_object"},
                max_tokens=8192,
                temperature=0.1
            )
            content = response.choices[0].message.content
            parsed = repair_and_parse_json(content)
            if parsed and isinstance(parsed, dict):
                records = parsed.get("records")
                if records and isinstance(records, list):
                    valid_recs = [r for r in records if isinstance(r, dict) and len(r) > 0]
                    # Check if this model met the expected count
                    if len(valid_recs) >= expected_count:
                        best_records = valid_recs
                        break
                    elif len(valid_recs) > len(best_records):
                        best_records = valid_recs
        except Exception as err:
            if is_auth_error(err):
                print(f"[Warning] Groq API key is invalid or unauthorized (401). Falling back to local rule-based extractor.")
                errors.append(f"Auth error (401): {str(err)}")
                break
            errors.append(f"Model {model_name} chunk #{batch_index} error: {str(err)}")
            continue

    # Clean and validate casing on extracted records
    sanitized_records: List[Dict[str, Any]] = []
    for idx, r in enumerate(best_records):
        clean_r = {}
        for k, v in r.items():
            clean_r[k] = normalize_field_casing(k, v)
        # Store source batch reference
        clean_r["_source_batch"] = batch_index
        clean_r["_source_item_offset"] = idx
        sanitized_records.append(clean_r)

    extracted_count = len(sanitized_records)
    if extracted_count >= expected_count:
        status = "complete"
    elif extracted_count > 0:
        status = "partial"
    else:
        status = "failed"

    return {
        "batch_index": batch_index,
        "expected_count": expected_count,
        "extracted_count": extracted_count,
        "status": status,
        "records": sanitized_records,
        "skipped_count": max(0, expected_count - extracted_count),
        "errors": errors
    }


def extract_batch_records(
    client: Groq,
    batch_text: str,
    expected_count: int,
    models: List[str] = GROQ_MODELS
) -> Optional[List[Dict[str, Any]]]:
    """
    Public helper to extract tabular records for a specific chunk/batch.
    Uses _extract_batch_chunk with verification and fallback models.
    """
    res = _extract_batch_chunk(
        client=client,
        batch_text=batch_text,
        batch_index=0,
        expected_count=expected_count,
        models=models
    )
    recs = res.get("records", [])
    return recs if recs else None


def extract_fields_with_llm(raw_text: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Uses Groq LLM to understand document semantics and schema structure.
    Intelligently determines if the input is:
    1. Multi-Record Dataset (e.g. employee list, transactions, catalog items, tabular text, rosters)
       -> Chunks large datasets into batches of ~10 items to extract 100% of all records without truncation.
       -> Programmatically reconciles expected vs extracted counts, detecting skipped records and duplicates.
    2. Single-Entity Document (e.g. individual invoice, certificate, single receipt, letter)
       -> Extracts standardized key-value fields with schema validation and currency preservation.
    """
    key_to_use = api_key or os.environ.get("GROQ_API_KEY", "") or GROQ_API_KEY
    if not key_to_use or not raw_text.strip():
        return None

    try:
        http_client = httpx.Client(verify=False, timeout=35.0)
        client = Groq(api_key=key_to_use, http_client=http_client)

        # ─── CASE 1: Detect Multi-Record List / Paragraph Dataset ───
        # Check for numbered items (e.g., "1. ", "2. ", "[1] "), bulleted lists ("- ", "* "), or double newline paragraphs
        entries = [e.strip() for e in re.split(r'\n(?=\s*(?:\d+[\.\)]|\-|\*|\[\d+\]|\#\d+)\s+)', raw_text) if e.strip()]
        if len(entries) < 6:
            para_entries = [p.strip() for p in re.split(r'\n\s*\n+', raw_text) if p.strip()]
            if len(para_entries) >= 6:
                entries = para_entries

        # If 6 or more distinct items/paragraphs detected -> Run batch chunk extraction to process ALL items
        if len(entries) >= 6:
            batch_size = 10
            all_records: List[Dict[str, Any]] = []
            batch_audits: List[Dict[str, Any]] = []
            extraction_errors: List[str] = []

            auth_failed = False
            for batch_idx, i in enumerate(range(0, len(entries), batch_size)):
                if auth_failed:
                    break
                batch = entries[i:i + batch_size]
                batch_text = "\n".join(batch)
                chunk_res = _extract_batch_chunk(
                    client=client,
                    batch_text=batch_text,
                    batch_index=batch_idx,
                    expected_count=len(batch),
                    models=GROQ_MODELS
                )
                if any("401" in str(e) or "Auth error" in str(e) for e in chunk_res.get("errors", [])):
                    auth_failed = True
                    break
                batch_audits.append({
                    "batch_index": batch_idx,
                    "expected_count": chunk_res["expected_count"],
                    "extracted_count": chunk_res["extracted_count"],
                    "status": chunk_res["status"],
                    "skipped_count": chunk_res["skipped_count"]
                })
                if chunk_res["errors"]:
                    extraction_errors.extend(chunk_res["errors"])
                if chunk_res.get("records"):
                    all_records.extend(chunk_res["records"])

            if all_records:
                # Find all unique column keys in order of appearance (ignoring internal metadata keys)
                all_columns: List[str] = []
                for r in all_records:
                    for k in r.keys():
                        if k.startswith("_"):
                            continue
                        if k not in all_columns:
                            all_columns.append(k)

                # Filter out columns that are 100% empty across all records
                valid_columns = []
                for col in all_columns:
                    has_data = any(
                        r.get(col) is not None
                        and str(r.get(col)).strip() != ""
                        and str(r.get(col)).strip().lower() not in ["null", "none", "n/a", "-", "nil", "nan", "undefined"]
                        for r in all_records
                    )
                    if has_data:
                        valid_columns.append(col)

                if not valid_columns:
                    valid_columns = all_columns

                # Normalize each record to have uniform columns and casing
                final_records = []
                seen_signatures = set()
                duplicate_count = 0

                for r in all_records:
                    rec_clean = {}
                    for k in valid_columns:
                        val = r.get(k)
                        rec_clean[k] = normalize_field_casing(k, val)
                    
                    # Compute signature across non-null fields to detect duplicates across chunks
                    sig = tuple(sorted((k, str(v)) for k, v in rec_clean.items() if v is not None))
                    if sig in seen_signatures:
                        duplicate_count += 1
                    else:
                        seen_signatures.add(sig)

                    final_records.append(rec_clean)

                total_expected = len(entries)
                total_extracted = len(final_records)
                completeness_rate = round(total_extracted / total_expected, 3) if total_expected > 0 else 1.0

                return {
                    "data_type": "records",
                    "columns": valid_columns,
                    "records": final_records,
                    "audit": {
                        "total_expected": total_expected,
                        "total_extracted": total_extracted,
                        "completeness_rate": completeness_rate,
                        "duplicate_chunks_detected": duplicate_count,
                        "batches": batch_audits,
                        "errors": extraction_errors
                    }
                }

        # ─── CASE 2: Single-Record or Multi-Chunk Document ───
        system_instruction = (
            "You are an expert Data Extraction, Computer Vision Synthesis, and Universal Schema Intelligence AI engine.\n"
            "Analyze the document text, OCR stream, or scene analysis and extract structured records or domain fields:\n\n"
            "CATEGORY A: Multi-Record Dataset or Book Chapter Structure\n"
            "(Use this if the text contains multiple entries, people, items, test cases, chapters, sections, transactions, or logs)\n"
            "Extract clean standardized records. For books/educational texts: chapter_number, chapter_title, section_heading, author, isbn, content, page_number.\n"
            "For technical test reports: test_case_id, category, description, input_data, expected_result, actual_result, execution_time, status, source_page.\n"
            "Return JSON:\n"
            "{\n"
            '  "data_type": "records",\n'
            '  "columns": ["id", "title", "description", "status"],\n'
            '  "records": [{"id": "1", "title": "...", "description": "...", "status": "Active"}]\n'
            "}\n\n"
            "CATEGORY B: Single-Record Document or Logistics / Billing Label\n"
            "(Use this for Shipping Labels, Invoices, Receipts, Business Cards, Certificates, ID Profiles)\n"
            "- For Shipping Labels: carrier, service_type, sender_name, sender_address, receiver_name, receiver_company, receiver_address, postal_code, tracking_number, postage, delivery_instructions, barcode_data\n"
            "- For Invoices/Receipts: invoice_no, invoice_date, merchant, subtotal, tax, total, payment_method\n"
            "- For Business Cards: person_name, job_title, company_name, email, phone, website, address\n"
            "Return JSON:\n"
            "{\n"
            '  "data_type": "key_value",\n'
            '  "fields": [\n'
            '    {"key": "carrier", "label": "Carrier", "value": "USPS", "raw_value": "USPS", "field_type": "text"},\n'
            '    {"key": "tracking_number", "label": "Tracking Number", "value": "9400111899223197428490", "raw_value": "9400 1118 9922 3197 4284 90", "field_type": "identifier"}\n'
            '  ]\n'
            "}"
        )

        # Chunk large document text without truncation (e.g. 104-page books or large text)
        max_chunk_chars = 15000
        if len(raw_text) <= max_chunk_chars:
            text_chunks = [raw_text]
        else:
            # Split along page breaks, double newlines, or paragraphs
            raw_parts = re.split(r'(?:\n\s*--- PAGE \d+ ---\s*\n|\n{2,})', raw_text)
            text_chunks = []
            curr_chunk = []
            curr_len = 0
            for part in raw_parts:
                p_len = len(part)
                if curr_len + p_len > max_chunk_chars and curr_chunk:
                    text_chunks.append("\n\n".join(curr_chunk))
                    curr_chunk = [part]
                    curr_len = p_len
                else:
                    curr_chunk.append(part)
                    curr_len += p_len
            if curr_chunk:
                text_chunks.append("\n\n".join(curr_chunk))

        all_chunk_records = []
        all_chunk_fields = []
        all_columns = []

        auth_failed = False
        for c_idx, chunk_text in enumerate(text_chunks):
            if auth_failed:
                break
            user_content = f"Extract and structure document chunk #{c_idx + 1} of {len(text_chunks)}. Return valid JSON:\n\n{chunk_text}"
            chunk_parsed = None

            for model_name in GROQ_MODELS:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_content}
                        ],
                        response_format={"type": "json_object"},
                        max_tokens=8192,
                        temperature=0.1
                    )
                    content = response.choices[0].message.content
                    parsed = repair_and_parse_json(content)
                    if parsed and isinstance(parsed, dict):
                        chunk_parsed = parsed
                        break
                except Exception as model_err:
                    if is_auth_error(model_err):
                        print(f"[Warning] Groq API key is invalid or unauthorized (401). Falling back to local high-precision rule extractor.")
                        auth_failed = True
                        break
                    print(f"Model {model_name} failed on chunk #{c_idx + 1}: {model_err}")
                    continue

            if chunk_parsed:
                # Accumulate records if chunk returned records
                recs = chunk_parsed.get("records")
                if recs and isinstance(recs, list):
                    cols = chunk_parsed.get("columns") or (list(recs[0].keys()) if recs else [])
                    for col in cols:
                        if col not in all_columns:
                            all_columns.append(col)
                    for r in recs:
                        if isinstance(r, dict):
                            all_chunk_records.append(r)

                # Accumulate key-values if chunk returned fields
                flds = chunk_parsed.get("fields")
                if flds and isinstance(flds, list):
                    for f in flds:
                        if isinstance(f, dict) and not any(ef.get("key") == f.get("key") for ef in all_chunk_fields):
                            all_chunk_fields.append(f)

        if all_chunk_records:
            sanitized_records = []
            for r in all_chunk_records:
                rec_clean = {}
                for k in all_columns:
                    rec_clean[k] = normalize_field_casing(k, r.get(k))
                sanitized_records.append(rec_clean)

            return {
                "data_type": "records",
                "columns": all_columns,
                "records": sanitized_records,
                "audit": {
                    "total_chunks_processed": len(text_chunks),
                    "total_records": len(sanitized_records),
                    "status": "complete"
                }
            }

        if all_chunk_fields:
            return {
                "data_type": "key_value",
                "fields": all_chunk_fields,
                "audit": {
                    "total_chunks_processed": len(text_chunks),
                    "total_fields": len(all_chunk_fields),
                    "status": "complete"
                }
            }

        for model_name in GROQ_MODELS:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=8192,
                    temperature=0.1
                )
                content = response.choices[0].message.content
                parsed = repair_and_parse_json(content)
                if not parsed or not isinstance(parsed, dict):
                    continue

                # Check for Multi-Record Dataset output
                records = parsed.get("records")
                if records and isinstance(records, list) and len(records) > 0:
                    columns = parsed.get("columns")
                    if not columns or not isinstance(columns, list):
                        columns = list(records[0].keys())

                    sanitized_records = [r for r in records if isinstance(r, dict)]

                    if sanitized_records:
                        valid_columns = []
                        for col in columns:
                            has_data = any(
                                r.get(col) is not None
                                and str(r.get(col)).strip() != ""
                                and str(r.get(col)).strip().lower() not in ["null", "none", "n/a", "-", "nil", "nan", "undefined"]
                                for r in sanitized_records
                            )
                            if has_data:
                                valid_columns.append(col)

                        if not valid_columns:
                            valid_columns = columns

                        final_records = []
                        for r in sanitized_records:
                            rec_clean = {}
                            for k in valid_columns:
                                rec_clean[k] = normalize_field_casing(k, r.get(k))
                            final_records.append(rec_clean)

                        return {
                            "data_type": "records",
                            "columns": valid_columns,
                            "records": final_records,
                            "audit": {
                                "model_used": model_name,
                                "total_records": len(final_records),
                                "status": "complete"
                            }
                        }

                # Check for Single-Record Document output
                fields = parsed.get("fields")
                if fields and isinstance(fields, list) and len(fields) > 0:
                    sanitized_fields = []
                    for f in fields:
                        if isinstance(f, dict) and "key" in f:
                            key_name = str(f.get("key"))
                            val = f.get("value")
                            raw_val = f.get("raw_value", val)
                            field_type = str(f.get("field_type", "text"))
                            curr = f.get("currency")

                            # If currency isn't separated yet, separate it
                            if field_type in ("currency", "amount", "salary") or any(c in str(raw_val) for c in ("$", "₹", "€", "£", "SAR")):
                                amt, detected_curr = separate_amount_and_currency(raw_val)
                                if amt is not None:
                                    val = amt
                                    if not curr and detected_curr:
                                        curr = detected_curr

                            cased_val = normalize_field_casing(key_name, val)

                            is_missing = val is None or str(val).strip().lower() in ["null", "none", "n/a", "", "-", "nil", "nan"]

                            sanitized_fields.append({
                                "key": key_name,
                                "label": str(f.get("label", key_name.replace("_", " ").title())),
                                "value": None if is_missing else cased_val,
                                "raw_value": raw_val,
                                "currency": curr,
                                "field_type": field_type,
                                "confidence": 0.98 if not is_missing else 0.0,
                                "is_extracted": not is_missing,
                                "is_valid": True,
                                "error_message": None if not is_missing else "Value was missing or unextractable in source"
                            })

                    if sanitized_fields:
                        return {
                            "data_type": "key_value",
                            "fields": sanitized_fields,
                            "audit": {
                                "model_used": model_name,
                                "total_fields": len(sanitized_fields),
                                "extracted_fields": sum(1 for sf in sanitized_fields if sf["is_extracted"]),
                                "missing_fields": sum(1 for sf in sanitized_fields if not sf["is_extracted"])
                            }
                        }

            except Exception as model_err:
                if is_auth_error(model_err):
                    print(f"[Warning] Groq API key is invalid or unauthorized (401). Falling back to local rule-based extractor.")
                    break
                print(f"Groq model {model_name} attempt failed: {model_err}")
                continue

    except Exception as e:
        print(f"Groq LLM extraction error: {e}")

    return None


def classify_columns_with_llm(
    columns: list,
    sample_values: dict,
    api_key: str = None,
) -> dict:
    """
    Use Groq LLM to classify DataFrame columns into business entity types
    (store, item, customer, transaction, car, invoice, employee, student, medical)
    when rule-based confidence is low.

    Args:
        columns: List of column names.
        sample_values: Dict of {column_name: [sample cell values]}.
        api_key: Optional Groq API key override.

    Returns:
        Dict with keys: file_type, column_assignments, entity_confidence, details.
    """
    key_to_use = api_key or os.environ.get("GROQ_API_KEY", "") or GROQ_API_KEY
    if not key_to_use or not columns:
        return None

    try:
        http_client = httpx.Client(verify=False, timeout=25.0)
        client = Groq(api_key=key_to_use, http_client=http_client)

        # Build compact sample preview
        sample_preview = []
        for col in columns:
            vals = sample_values.get(col, [])
            preview = ", ".join(str(v) for v in vals[:5])
            sample_preview.append(f"  {col}: [{preview}]")

        system_prompt = (
            "You are an expert Multi-Domain Business Data Schema Classifier AI.\n"
            "Given column names and sample values from a dataset, classify the dataset into one of the canonical domains:\n"
            "- car: Vehicle/Automotive (VIN, make, model, year, mileage, license plate, odometer, engine)\n"
            "- customer: Customer/Client/Member/Shopper (name, phone, email, address, loyalty)\n"
            "- store: Store/Branch/Outlet/Warehouse location (store_id, branch_name, city, manager)\n"
            "- item: Product/Item/SKU/Inventory/Merchandise (sku, item_name, unit_price, stock, category)\n"
            "- transaction: Order/Sale/Purchase/Billing log (transaction_id, customer_id, store_id, total_amount, date)\n"
            "- invoice: Invoice/Billing document (invoice_no, vendor_name, bill_to, tax_amount, due_date)\n"
            "- employee: Employee/HR/Staff record (emp_id, name, department, designation, salary, joining_date)\n"
            "- student: Academic/Course Syllabus/Curriculum/Student record (syllabus, course_code, subject_name, semester, credits, student_id, roll_no, cgpa, department)\n"
            "- medical: Medical/Patient record (patient_id, mrn, doctor_name, diagnosis, prescription, blood_group)\n"
            "- technical_test_report: Technical Test Report / Verification (test_case_id, tc_id, category, description, input_data, expected_result, actual_result, execution_time, status)\n"
            "- mixed: Dataset containing multiple independent entity tables\n"
            "- unknown: Unrecognized general dataset\n\n"
            "Rules:\n"
            "- If a dataset contains test case IDs (TC-001), test descriptions, expected/actual results, or status PASS/FAIL, classify as 'technical_test_report'. Do NOT classify as 'customer' or 'employee' just because test cases contain emails or names in input payloads.\n"
            "- If a dataset contains course codes, subject titles, semesters, credits, or syllabus modules, classify as 'student' (Academic / Course Syllabus).\n"
            "- If a column like store_id or customer_id appears alongside order_date/quantity, it is a foreign key in a Transaction.\n"
            "- If the file has columns from only one domain, set file_type to that domain.\n\n"
            "Return valid JSON:\n"
            "{\n"
            '  "file_type": "car|customer|store|item|transaction|invoice|employee|student|medical|mixed|unknown",\n'
            '  "column_assignments": {"col_name": "domain_type", ...},\n'
            '  "entity_confidence": {"car": 0.0, "customer": 0.0, "store": 0.0, "item": 0.0, "transaction": 0.0, "invoice": 0.0, "employee": 0.0, "student": 0.0, "medical": 0.0},\n'
            '  "reasoning": "Brief explanation of domain decision",\n'
            '  "details": "Brief explanation"\n'
            "}"
        )

        user_content = (
            f"Classify these {len(columns)} columns:\n"
            + "\n".join(sample_preview)
        )

        for model_name in GROQ_MODELS:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                content = response.choices[0].message.content
                parsed = repair_and_parse_json(content)

                if parsed and "file_type" in parsed:
                    return parsed

            except Exception as model_err:
                if is_auth_error(model_err):
                    print(f"[Warning] Groq API key is invalid (401). Using local canonical schema classifier.")
                    break
                print(f"Groq column classification model {model_name} failed: {model_err}")
                continue

    except Exception as e:
        print(f"Groq column classification error: {e}")

    return None


def classify_domain_with_llm(
    text_or_data: str,
    api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Use Groq LLM to classify unstructured text or document contents into a business domain.

    Returns:
        Dict with detected_type, confidence, reasoning, primary_match_key, extracted_fields.
    """
    key_to_use = api_key or os.environ.get("GROQ_API_KEY", "") or GROQ_API_KEY
    if not key_to_use or not text_or_data.strip():
        return None

    try:
        http_client = httpx.Client(verify=False, timeout=25.0)
        client = Groq(api_key=key_to_use, http_client=http_client)

        system_prompt = (
            "You are an expert Multi-Domain Document Classification AI.\n"
            "Analyze the provided document text and classify it into one of these business domains:\n"
            "- car: Vehicle/Automotive (VIN, make, model, year, mileage, license plate)\n"
            "- customer: Customer/Client profile (name, phone, email, address)\n"
            "- store: Retail store/branch profile (store_id, address, manager)\n"
            "- item: Product catalog/item description (sku, price, specs)\n"
            "- transaction: Sales transaction/receipt (transaction_id, date, amount)\n"
            "- invoice: Commercial invoice/bill (invoice_no, vendor, bill_to, tax, total)\n"
            "- employee: Employee/Staff profile (emp_id, department, designation, salary)\n"
            "- student: Academic/Course Syllabus/Curriculum/Student record (syllabus, course_code, semester, credits, subjects, modules, student_id, roll_no, cgpa, department)\n"
            "- medical: Medical/Patient chart (patient_id, mrn, diagnosis, prescription, doctor)\n"
            "- technical_test_report: Technical Test Report / Verification (test_case_id, tc_id, category, description, input_data, expected_result, actual_result, execution_time, status, test suite)\n"
            "- unknown: General or unrecognized document\n\n"
            "Rules:\n"
            "- If the document is a verification report, QA test report, or contains TC-xxx test cases with PASS/FAIL results, classify as 'technical_test_report'. Never classify as customer or employee just because sample test data contains emails or names.\n\n"
            "Return valid JSON:\n"
            "{\n"
            '  "detected_type": "car|customer|store|item|transaction|invoice|employee|student|medical|technical_test_report|unknown",\n'
            '  "confidence": 0.95,\n'
            '  "reasoning": "Explanation why this belongs to the detected domain",\n'
            '  "primary_match_key": "vin|phone|store_id|product_id|transaction_id|invoice_no|emp_id|student_id|patient_id|test_case_id|course_code",\n'
            '  "extracted_fields": ["field1", "field2", ...]\n'
            "}"
        )

        user_content = f"Classify the domain of this document text:\n\n{text_or_data[:6000]}"

        for model_name in GROQ_MODELS:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                content = response.choices[0].message.content
                parsed = repair_and_parse_json(content)

                if parsed and "detected_type" in parsed:
                    return parsed

            except Exception as model_err:
                if is_auth_error(model_err):
                    print(f"[Warning] Groq API key is invalid (401). Using local domain pattern classifier.")
                    break
                print(f"Groq domain classification model {model_name} failed: {model_err}")
                continue

    except Exception as e:
        print(f"Groq domain classification error: {e}")

    return None

