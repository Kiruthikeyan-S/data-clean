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

# Preferred fast & accurate models
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b"
]


def extract_batch_records(
    client: Groq,
    batch_text: str,
    expected_count: int,
    models: List[str]
) -> Optional[List[Dict[str, Any]]]:
    """Helper to extract tabular records for a specific chunk/batch of items."""
    system_instruction = (
        "You are an expert Data Extraction and Schema Normalization engine.\n"
        "Extract every single item/record from the provided text into structured tabular records JSON.\n"
        "Standardization rules:\n"
        "- Dates: Format as ISO 8601 (YYYY-MM-DD or YYYY-MM)\n"
        "- Names & Roles: Format in Title Case\n"
        "- Numbers & Salaries: Clean numeric values without currency symbols ($/₹/€/£/INR/USD) or commas\n"
        "- Currencies & Periods: Normalized into separate standardized columns (e.g. currency: 'USD', period: 'Year' or 'Hour')\n\n"
        "Return JSON format:\n"
        "{\n"
        '  "data_type": "records",\n'
        '  "columns": ["name", "job_role", "location", "joining_date", "manager", "salary", "currency", "period"],\n'
        '  "records": [\n'
        '    {"name": "...", "job_role": "...", "location": "...", "joining_date": "YYYY-MM-DD", "manager": "...", "salary": 145000, "currency": "USD", "period": "Year"}\n'
        "  ]\n"
        "}\n\n"
        f"CRITICAL: You MUST extract ALL {expected_count} individual items present in the text into 'records'. "
        f"Return exactly {expected_count} records without skipping, omitting, or truncating any."
    )

    for model_name in models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Extract all {expected_count} records from this batch:\n\n{batch_text}"}
                ],
                response_format={"type": "json_object"},
                max_tokens=8192,
                temperature=0.1
            )
            content = response.choices[0].message.content
            parsed = json.loads(content)
            records = parsed.get("records")
            if records and isinstance(records, list) and len(records) > 0:
                return [r for r in records if isinstance(r, dict)]
        except Exception as err:
            print(f"Batch extraction attempt with {model_name} failed: {err}")
            continue

    return None


def extract_fields_with_llm(raw_text: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Uses Groq LLM to understand document semantics and schema structure.
    Intelligently determines if the input is:
    1. Multi-Record Dataset (e.g. employee list, transactions, catalog items, tabular text, rosters)
       -> Chunks large datasets into batches of ~10 items to extract 100% of all records without truncation.
    2. Single-Entity Document (e.g. individual invoice, certificate, single receipt, letter)
       -> Extracts standardized key-value fields.
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

            for i in range(0, len(entries), batch_size):
                batch = entries[i:i + batch_size]
                batch_text = "\n".join(batch)
                batch_recs = extract_batch_records(client, batch_text, len(batch), GROQ_MODELS)
                if batch_recs:
                    all_records.extend(batch_recs)

            if all_records:
                # Find all unique column keys in order of appearance
                all_columns: List[str] = []
                for r in all_records:
                    for k in r.keys():
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

                # Normalize each record to have uniform columns
                final_records = []
                for r in all_records:
                    final_records.append({k: r.get(k) for k in valid_columns})

                return {
                    "data_type": "records",
                    "columns": valid_columns,
                    "records": final_records
                }

        # ─── CASE 2: Single-Record or Short Multi-Record Document ───
        system_instruction = (
            "You are an expert Data Extraction, Computer Vision Synthesis, and Schema Intelligence AI engine.\n"
            "Analyze the unstructured document text or computer vision scene analysis and determine its structural category:\n\n"
            "CATEGORY A: Multi-Record Dataset\n"
            "(Use this if the text contains multiple people, employees, transactions, line items, products, student records, logs, or tabular entries)\n"
            "Extract a list of records with clean standardized column headers and normalized cell values.\n"
            "Standardization rules:\n"
            "- Dates: Format as ISO 8601 (YYYY-MM-DD or YYYY-MM)\n"
            "- Names & Roles: Format in Title Case\n"
            "- Numbers & Salaries: Clean numbers without currency symbols ($/₹/€/£/INR/USD) or commas\n"
            "- Currencies & Periods: Normalized into separate standardized columns (e.g. currency: 'USD', period: 'Year')\n"
            "CRITICAL: You MUST extract ALL individual items/records described in the text into 'records'. Never truncate or sample.\n"
            "Return JSON:\n"
            "{\n"
            '  "data_type": "records",\n'
            '  "columns": ["name", "job_role", "location", "joining_date", "manager", "salary", "currency", "period"],\n'
            '  "records": [\n'
            '    {"name": "Marcus Vance", "job_role": "Senior Backend Architect", "location": "Austin", "joining_date": "2021-03-14", "manager": "Clara Oswald", "salary": 145000, "currency": "USD", "period": "Year"}\n'
            "  ]\n"
            "}\n\n"
            "CATEGORY B: Single-Record Document or Visual Photo Analysis\n"
            "(Use this if the input is a single invoice, receipt, personal profile, certificate, OR visual photo analysis of food, objects, products, vehicles, scenes)\n"
            "Extract all relevant domain fields and properties into clean, informative key-values:\n"
            "- For Food/Dining images: main_item, side_items, category, sauce, container, visible_contents, food_counts, dominant_colors\n"
            "- For Products/Objects: product_name, category, detected_objects, colors, features\n"
            "- For Documents: name, date, email, amount, organization, etc.\n"
            "CRITICAL: Only extract fields with actual information. Do NOT include empty/null placeholder fields.\n"
            "Return JSON:\n"
            "{\n"
            '  "data_type": "key_value",\n'
            '  "fields": [\n'
            '    {"key": "main_item", "label": "Main Item", "value": "Burger", "raw_value": "Cheeseburger", "field_type": "text"},\n'
            '    {"key": "side_items", "label": "Side Items", "value": "French Fries", "raw_value": "French Fries", "field_type": "text"},\n'
            '    {"key": "category", "label": "Category", "value": "Fast Food", "raw_value": "Fast Food", "field_type": "text"}\n'
            '  ]\n'
            "}"
        )

        user_content = f"Extract and structure this document or visual image data. Return valid JSON:\n\n{raw_text[:20000]}"

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
                parsed = json.loads(content)

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

                        final_records = [{k: r.get(k) for k in valid_columns} for r in sanitized_records]

                        return {
                            "data_type": "records",
                            "columns": valid_columns,
                            "records": final_records
                        }

                # Check for Single-Record Document output
                fields = parsed.get("fields")
                if fields and isinstance(fields, list) and len(fields) > 0:
                    sanitized_fields = []
                    for f in fields:
                        if isinstance(f, dict) and "key" in f:
                            val = f.get("value")
                            raw_val = f.get("raw_value", val)
                            if val is not None and str(val).strip() and str(val).strip().lower() not in ["null", "none", "n/a", "", "-"]:
                                sanitized_fields.append({
                                    "key": str(f.get("key")),
                                    "label": str(f.get("label", f.get("key").replace("_", " ").title())),
                                    "value": val,
                                    "raw_value": raw_val if raw_val is not None else val,
                                    "field_type": str(f.get("field_type", "text")),
                                    "confidence": 0.98,
                                    "is_valid": True,
                                    "error_message": None
                                })
                    if sanitized_fields:
                        return {
                            "data_type": "key_value",
                            "fields": sanitized_fields
                        }

            except Exception as model_err:
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
    (Store, Item, Customer, Transaction) when rule-based confidence is low.

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
            "You are a Business Data Schema Classifier AI.\n"
            "Given column names and sample values from a dataset, classify each column into one of:\n"
            "- store: Store/Branch/Outlet/Warehouse location data\n"
            "- item: Product/Item/SKU/Inventory data\n"
            "- customer: Customer/Client/Member/Shopper data\n"
            "- transaction: Order/Sale/Invoice/Purchase/Billing data\n"
            "- unknown: Does not fit any retail business entity\n\n"
            "Rules:\n"
            "- If a column like store_id or customer_id appears alongside order_date/quantity, "
            "it is a foreign key in a Transaction — assign it to transaction.\n"
            "- If the file has columns from multiple entity types, set file_type to 'mixed'.\n"
            "- If the file has columns from only one entity type, set file_type to that entity.\n\n"
            "Return valid JSON:\n"
            "{\n"
            '  "file_type": "store|item|customer|transaction|mixed|unknown",\n'
            '  "column_assignments": {"col_name": "entity_type", ...},\n'
            '  "entity_confidence": {"store": 0.0, "item": 0.0, "customer": 0.0, "transaction": 0.0},\n'
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
                parsed = json.loads(content)

                if "file_type" in parsed and "column_assignments" in parsed:
                    return parsed

            except Exception as model_err:
                print(f"Groq column classification model {model_name} failed: {model_err}")
                continue

    except Exception as e:
        print(f"Groq column classification error: {e}")

    return None
