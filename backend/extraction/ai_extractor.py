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

def extract_fields_with_llm(raw_text: str, api_key: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Uses Groq LLM to understand document content, identify all important fields,
    convert to standardized key-value structures, and return normalized fields.
    """
    key_to_use = api_key or os.environ.get("GROQ_API_KEY", "") or GROQ_API_KEY
    if not key_to_use or not raw_text.strip():
        return None

    try:
        http_client = httpx.Client(verify=False, timeout=25.0)
        client = Groq(api_key=key_to_use, http_client=http_client)

        system_instruction = (
            "You are an expert Data Extraction and Cleansing AI engine. "
            "Analyze the unstructured document text, understand its semantics, identify all important fields and entities "
            "(e.g., Name, Date of Birth, Document Date, Email, Phone, Address, City, Postal Code, ID Number, Organization, Amount, etc.).\n"
            "Rules for standardization:\n"
            "1. Standardize all dates to ISO 8601 (YYYY-MM-DD).\n"
            "2. Standardize names to Title Case.\n"
            "3. Standardize phone numbers to international E.164 or clean digits.\n"
            "4. Standardize emails to lowercase trimmed format.\n"
            "5. Standardize amounts and numbers by stripping currency symbols ($/₹/€/£/INR/USD) and commas.\n"
            "6. Keep the raw_value verbatim as found in the text.\n"
            "7. Return ONLY valid JSON with this exact schema:\n"
            '{"fields": [{"key": "name", "label": "Full Name", "value": "John Doe", "raw_value": "JOHN DOE", "field_type": "text"}]}'
        )

        user_content = f"Extract and standardize structured data from this document:\n\n{raw_text[:8000]}"

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
                fields = parsed.get("fields")
                if fields and isinstance(fields, list) and len(fields) > 0:
                    sanitized_fields = []
                    for f in fields:
                        if isinstance(f, dict) and "key" in f and "label" in f:
                            sanitized_fields.append({
                                "key": str(f.get("key")),
                                "label": str(f.get("label")),
                                "value": f.get("value"),
                                "raw_value": f.get("raw_value"),
                                "field_type": str(f.get("field_type", "text")),
                                "confidence": 0.98,
                                "is_valid": True,
                                "error_message": None
                            })
                    if sanitized_fields:
                        return sanitized_fields
            except Exception as model_err:
                print(f"Groq model {model_name} attempt failed: {model_err}")
                continue

    except Exception as e:
        print(f"Groq LLM extraction error: {e}")

    return None
