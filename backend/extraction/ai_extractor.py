import os
import json
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

def extract_fields_with_llm(raw_text: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Uses Groq LLM to understand document semantics and schema structure.
    Intelligently determines if the input is:
    1. Multi-Record Dataset (e.g. employee list, transactions, catalog items, tabular text, rosters)
       -> Extracts clean tabular records with dynamic standardized column headers.
    2. Single-Entity Document (e.g. individual invoice, certificate, single receipt, letter)
       -> Extracts standardized key-value fields.
    """
    key_to_use = api_key or os.environ.get("GROQ_API_KEY", "") or GROQ_API_KEY
    if not key_to_use or not raw_text.strip():
        return None

    try:
        http_client = httpx.Client(verify=False, timeout=25.0)
        client = Groq(api_key=key_to_use, http_client=http_client)

        system_instruction = (
            "You are an expert Data Extraction and Schema Intelligence AI engine.\n"
            "Analyze the unstructured document text and determine its structural category:\n\n"
            "CATEGORY A: Multi-Record Dataset\n"
            "(Use this if the text contains multiple people, employees, transactions, line items, products, student records, logs, or tabular entries)\n"
            "Extract a list of records with clean standardized column headers and normalized cell values.\n"
            "Standardization rules:\n"
            "- Dates: Format as ISO 8601 (YYYY-MM-DD or YYYY-MM)\n"
            "- Names & Roles: Format in Title Case\n"
            "- Numbers & Salaries: Clean numbers without currency symbols ($/₹/€/£/INR/USD) or commas\n"
            "- Currencies & Periods: Normalized into separate standardized columns (e.g. currency: 'USD', period: 'Year')\n"
            "Return JSON:\n"
            "{\n"
            '  "data_type": "records",\n'
            '  "columns": ["name", "job_role", "location", "joining_date", "manager", "salary", "currency", "period"],\n'
            '  "records": [\n'
            '    {"name": "Marcus Vance", "job_role": "Senior Backend Architect", "location": "Austin", "joining_date": "2021-03-14", "manager": "Clara Oswald", "salary": 145000, "currency": "USD", "period": "Year"}\n'
            "  ]\n"
            "}\n\n"
            "CATEGORY B: Single-Record Document\n"
            "(Use this if the text is a single individual invoice, single receipt, personal bio, certificate, or letter)\n"
            "Extract key-value fields with label, value, raw_value, and field_type.\n"
            "Return JSON:\n"
            "{\n"
            '  "data_type": "key_value",\n'
            '  "fields": [\n'
            '    {"key": "name", "label": "Full Name", "value": "John Doe", "raw_value": "JOHN DOE", "field_type": "text"}\n'
            "  ]\n"
            "}"
        )

        user_content = f"Extract and structure this document data:\n\n{raw_text[:12000]}"

        for model_name in GROQ_MODELS:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                content = response.choices[0].message.content
                parsed = json.loads(content)
                
                # Check for Multi-Record Dataset output
                records = parsed.get("records")
                if records and isinstance(records, list) and len(records) > 0:
                    # Clean up column headers and records
                    columns = parsed.get("columns")
                    if not columns or not isinstance(columns, list):
                        columns = list(records[0].keys())
                    
                    # Ensure all records have dict structure
                    sanitized_records = []
                    for r in records:
                        if isinstance(r, dict):
                            sanitized_records.append(r)

                    if sanitized_records:
                        return {
                            "data_type": "records",
                            "columns": columns,
                            "records": sanitized_records
                        }

                # Check for Single-Record Document output
                fields = parsed.get("fields")
                if fields and isinstance(fields, list) and len(fields) > 0:
                    sanitized_fields = []
                    for f in fields:
                        if isinstance(f, dict) and "key" in f:
                            val = f.get("value")
                            raw_val = f.get("raw_value", val)
                            # Only include if actual non-null, non-empty data exists
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
