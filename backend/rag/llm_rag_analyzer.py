"""
LLM RAG Reasoning & Semantic Analyzer Module

Provides contextual reasoning for retrieved candidates using Groq LLM.
Prompts LLM with:
- Current Record
- Top-K Retrieved Records
- Entity Matching Rules
Returns structured JSON with semantic match analysis, field overlap, and explanation.
"""
from __future__ import annotations
import os
import json
import httpx
from typing import Dict, Any, List, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b"
]


def heuristic_rag_analysis(
    current_record: Dict[str, Any],
    candidate_record: Dict[str, Any],
    candidate_id: str,
    entity_type: str = "general"
) -> Dict[str, Any]:
    """Fast deterministic semantic analyzer fallback when LLM is unavailable."""
    matching_fields = []
    reasons = []

    # Check phone
    phone_curr = str(current_record.get("phone") or current_record.get("mobile") or "").strip()
    phone_cand = str(candidate_record.get("phone") or candidate_record.get("mobile") or "").strip()
    if phone_curr and phone_cand and phone_curr == phone_cand:
        matching_fields.append("phone")
        reasons.append("Phone matches exactly")

    # Check email
    email_curr = str(current_record.get("email") or "").strip().lower()
    email_cand = str(candidate_record.get("email") or "").strip().lower()
    if email_curr and email_cand and email_curr == email_cand:
        matching_fields.append("email")
        reasons.append("Email matches exactly")

    # Check ID / Code
    id_curr = str(current_record.get("id") or current_record.get(f"{entity_type}_id") or "").strip().upper()
    id_cand = str(candidate_record.get("id") or candidate_record.get(f"{entity_type}_id") or "").strip().upper()
    if id_curr and id_cand and id_curr == id_cand:
        matching_fields.append("id")
        reasons.append(f"{entity_type.capitalize()} ID matches exactly")

    # Check Name
    name_curr = str(current_record.get("name") or current_record.get("customer_name") or current_record.get("store_name") or current_record.get("product_name") or "").strip().lower()
    name_cand = str(candidate_record.get("name") or candidate_record.get("customer_name") or candidate_record.get("store_name") or candidate_record.get("product_name") or "").strip().lower()
    if name_curr and name_cand:
        if name_curr == name_cand:
            matching_fields.append("name")
            reasons.append("Name matches exactly")
        elif name_curr in name_cand or name_cand in name_curr:
            matching_fields.append("name")
            reasons.append("Name is a partial/initial variation")

    # Check Address / City
    addr_curr = str(current_record.get("address") or "").strip().lower()
    addr_cand = str(candidate_record.get("address") or "").strip().lower()
    if addr_curr and addr_cand and (addr_curr == addr_cand or addr_curr in addr_cand or addr_cand in addr_curr):
        matching_fields.append("address")
        reasons.append("Address is strongly similar")

    is_possible = len(matching_fields) >= 1
    reason_str = ", ".join(reasons) if reasons else "No direct matching fields identified."

    return {
        "candidate_id": candidate_id,
        "possible_match": is_possible,
        "matching_fields": matching_fields,
        "semantic_confidence": round(min(1.0, 0.40 + 0.25 * len(matching_fields)), 2),
        "reason": reason_str
    }


def analyze_candidate_with_llm(
    current_record: Dict[str, Any],
    retrieved_candidates: List[Dict[str, Any]],
    entity_type: str = "general",
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Analyzes semantic relationships between a current record and Top-K retrieved candidates using Groq LLM.
    Returns structured analysis for each candidate.
    """
    if not current_record or not retrieved_candidates:
        return []

    key_to_use = api_key or os.environ.get("GROQ_API_KEY", "") or GROQ_API_KEY
    if not key_to_use:
        # Fallback to local heuristic analyzer
        return [
            heuristic_rag_analysis(
                current_record=current_record,
                candidate_record=c.get("cleaned_record", {}),
                candidate_id=c.get("record_id", "UNKNOWN"),
                entity_type=entity_type
            )
            for c in retrieved_candidates
        ]

    prompt_data = {
        "entity_type": entity_type,
        "current_record": current_record,
        "retrieved_candidates": [
            {
                "candidate_id": c.get("record_id"),
                "similarity_score": c.get("similarity_score"),
                "record": c.get("cleaned_record", {})
            }
            for c in retrieved_candidates
        ]
    }

    system_instruction = (
        "You are an expert Data Deduplication & Entity Resolution AI.\n"
        "Analyze the relationship between the Current Record and the Retrieved Historical Candidates.\n"
        "Rules:\n"
        "- Assess whether each candidate could represent the same real-world entity (person, store, or product).\n"
        "- Identify exact, partial, or phonetic matching fields (e.g. 'Kirthikeyan' vs 'S Kiruthikeyan', 'Anna Nagar Chennai' vs 'Anna Nagar, Chennai').\n"
        "- Explain the semantic connection clearly and concisely.\n"
        "- Return JSON format ONLY:\n"
        "{\n"
        '  "analyses": [\n'
        '    {\n'
        '      "candidate_id": "...",\n'
        '      "possible_match": true,\n'
        '      "matching_fields": ["phone", "name", "address"],\n'
        '      "semantic_confidence": 0.95,\n'
        '      "reason": "Phone matches exactly, address is strongly similar, and customer names are phonetic variations of the same person."\n'
        '    }\n'
        '  ]\n'
        "}\n"
    )

    try:
        http_client = httpx.Client(verify=False, timeout=15.0)
        client = Groq(api_key=key_to_use, http_client=http_client)

        for model_name in GROQ_MODELS:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": f"Analyze these candidates:\n\n{json.dumps(prompt_data, indent=2, default=str)}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=2048
                )
                content = response.choices[0].message.content
                parsed = json.loads(content)
                analyses = parsed.get("analyses")
                if analyses and isinstance(analyses, list):
                    return analyses
            except Exception as e:
                print(f"[RAG LLM Analyzer] Model {model_name} failed: {e}")
                continue
    except Exception as e:
        print(f"[RAG LLM Analyzer] Groq client connection failed: {e}")

    # Fallback to deterministic heuristic
    return [
        heuristic_rag_analysis(
            current_record=current_record,
            candidate_record=c.get("cleaned_record", {}),
            candidate_id=c.get("record_id", "UNKNOWN"),
            entity_type=entity_type
        )
        for c in retrieved_candidates
    ]
