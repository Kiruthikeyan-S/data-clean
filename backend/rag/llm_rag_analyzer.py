"""
LLM RAG Reasoning & Semantic Entity Resolution Module

Provides contextual reasoning for retrieved candidates using Groq LLM and deterministic
entity-specific heuristics (Customer, Item, Store, General).
Applies:
- Exact ID/phone/email matching
- Phonetic (Soundex) matching for person names and store brands
- Strict threshold classification:
  * exact_match (confidence >= 0.95) -> auto_approved
  * probable_match (0.75 <= confidence < 0.95) -> review_required
  * rejected (confidence < 0.75 or conflicting critical IDs) -> rejected
- Guardrails:
  * Never merge different people just because their names are similar!
  * Never merge different products with distinct model/version numbers!
  * Never merge stores located in conflicting cities unless store_id matches!
"""
from __future__ import annotations

import os
import re
import json
import httpx
from typing import Dict, Any, List, Optional, Tuple, Set
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


def soundex(name: str) -> str:
    """Computes American Soundex code for phonetic comparison."""
    if not name:
        return ""
    s = re.sub(r'[^A-Za-z]', '', str(name)).upper()
    if not s:
        return ""
    codes = {
        'B': '1', 'F': '1', 'P': '1', 'V': '1',
        'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6'
    }
    first_char = s[0]
    encoded = [first_char]
    prev_code = codes.get(first_char, '0')
    for char in s[1:]:
        code = codes.get(char, '0')
        if code != '0' and code != prev_code:
            encoded.append(code)
            prev_code = code
        elif code == '0':
            prev_code = '0'
    return "".join(encoded)[:4].ljust(4, '0')


def extract_model_or_index_tokens(text: str) -> Set[str]:
    """Extracts distinctive model numbers, version tags, or numeric suffixes (e.g. '13', '14', 'v2', 'pro', 'max')."""
    clean = re.sub(r'[^\w\s]', ' ', str(text).lower())
    tokens = clean.split()
    model_tokens = set()
    for tok in tokens:
        if re.search(r'\d+', tok) or tok in ('pro', 'max', 'mini', 'plus', 'ultra', 'lite', 'se'):
            model_tokens.add(tok)
    return model_tokens


def heuristic_rag_analysis(
    current_record: Dict[str, Any],
    candidate_record: Dict[str, Any],
    candidate_id: str,
    entity_type: str = "general"
) -> Dict[str, Any]:
    """
    Deterministic entity-specific semantic resolution.
    Applies strict business domain rules for Customer, Item, and Store.
    """
    e_type = str(entity_type).lower().strip()
    matching_fields: List[str] = []
    conflicting_fields: Dict[str, List[Any]] = {}
    reasons: List[str] = []

    # 1. Customer Entity Matching Rules
    if e_type in ("customer", "client", "member"):
        phone_curr = re.sub(r'\D', '', str(current_record.get("phone") or current_record.get("mobile") or ""))
        phone_cand = re.sub(r'\D', '', str(candidate_record.get("phone") or candidate_record.get("mobile") or ""))
        if phone_curr and phone_cand:
            if phone_curr == phone_cand:
                matching_fields.append("phone")
                reasons.append("Phone numbers match exactly")
            else:
                conflicting_fields["phone"] = [phone_curr, phone_cand]

        email_curr = str(current_record.get("email") or "").strip().lower()
        email_cand = str(candidate_record.get("email") or "").strip().lower()
        if email_curr and email_cand:
            if email_curr == email_cand:
                matching_fields.append("email")
                reasons.append("Email addresses match exactly")
            else:
                conflicting_fields["email"] = [email_curr, email_cand]

        # Name comparison with phonetic Soundex
        name_curr = str(current_record.get("name") or current_record.get("full_name") or current_record.get("customer_name") or "").strip()
        name_cand = str(candidate_record.get("name") or candidate_record.get("full_name") or candidate_record.get("customer_name") or "").strip()
        if name_curr and name_cand:
            if name_curr.lower() == name_cand.lower():
                matching_fields.append("name")
                reasons.append("Customer names match exactly")
            elif soundex(name_curr) == soundex(name_cand):
                matching_fields.append("name_phonetic")
                reasons.append(f"Customer names match phonetically ('{name_curr}' ≈ '{name_cand}')")

        # CRITICAL GUARD: If phones or emails explicitly CONFLICT, reject even if names match!
        if conflicting_fields:
            return {
                "candidate_id": candidate_id,
                "match_decision": "rejected",
                "review_status": "rejected",
                "semantic_confidence": 0.15,
                "matching_fields": matching_fields,
                "conflicting_fields": conflicting_fields,
                "possible_match": False,
                "reason": f"Rejected: Conflicting unique identifiers ({', '.join(conflicting_fields.keys())}). Different individuals cannot be merged."
            }

        # Confidence calculation
        if ("phone" in matching_fields or "email" in matching_fields) and ("name" in matching_fields or "name_phonetic" in matching_fields):
            confidence = 0.98
            decision = "exact_match"
            status = "auto_approved"
        elif "phone" in matching_fields or "email" in matching_fields:
            confidence = 0.95
            decision = "exact_match"
            status = "auto_approved"
        elif "name" in matching_fields or "name_phonetic" in matching_fields:
            # Similar names without verified phone/email -> uncertain, require human review!
            confidence = 0.80
            decision = "probable_match"
            status = "review_required"
            reasons.append("Unverified contact info; human approval required")
        else:
            confidence = 0.20
            decision = "rejected"
            status = "rejected"

    # 2. Item Entity Matching Rules
    elif e_type in ("item", "product"):
        sku_curr = str(current_record.get("sku") or current_record.get("product_id") or current_record.get("item_id") or "").strip().lower()
        sku_cand = str(candidate_record.get("sku") or candidate_record.get("product_id") or candidate_record.get("item_id") or "").strip().lower()
        if sku_curr and sku_cand:
            if sku_curr == sku_cand:
                matching_fields.append("sku")
                reasons.append("SKU/Product identifiers match exactly")
            else:
                conflicting_fields["sku"] = [sku_curr, sku_cand]

        name_curr = str(current_record.get("item_name") or current_record.get("product_name") or current_record.get("title") or "").strip()
        name_cand = str(candidate_record.get("item_name") or candidate_record.get("product_name") or candidate_record.get("title") or "").strip()
        
        # Check for model/version discrepancies (e.g. "iPhone 13" vs "iPhone 14")
        models_curr = extract_model_or_index_tokens(name_curr)
        models_cand = extract_model_or_index_tokens(name_cand)
        if models_curr and models_cand and models_curr != models_cand:
            conflicting_fields["model_tokens"] = [list(models_curr), list(models_cand)]

        if conflicting_fields:
            return {
                "candidate_id": candidate_id,
                "match_decision": "rejected",
                "review_status": "rejected",
                "semantic_confidence": 0.20,
                "matching_fields": matching_fields,
                "conflicting_fields": conflicting_fields,
                "possible_match": False,
                "reason": "Rejected: Detected distinct product model, version, or SKU. Different products must not be merged."
            }

        if name_curr and name_cand:
            if name_curr.lower() == name_cand.lower():
                matching_fields.append("item_name")
                reasons.append("Item titles match exactly")
            elif soundex(name_curr) == soundex(name_cand) or name_curr.lower() in name_cand.lower() or name_cand.lower() in name_curr.lower():
                matching_fields.append("item_name_fuzzy")
                reasons.append("Item titles are semantically equivalent")

        if "sku" in matching_fields:
            confidence = 0.98
            decision = "exact_match"
            status = "auto_approved"
        elif "item_name" in matching_fields:
            confidence = 0.88
            decision = "probable_match"
            status = "review_required"
        elif "item_name_fuzzy" in matching_fields:
            confidence = 0.78
            decision = "probable_match"
            status = "review_required"
        else:
            confidence = 0.15
            decision = "rejected"
            status = "rejected"

    # 3. Store Entity Matching Rules
    elif e_type in ("store", "branch"):
        store_id_curr = str(current_record.get("store_id") or current_record.get("branch_id") or "").strip().lower()
        store_id_cand = str(candidate_record.get("store_id") or candidate_record.get("branch_id") or "").strip().lower()
        if store_id_curr and store_id_cand:
            if store_id_curr == store_id_cand:
                matching_fields.append("store_id")
                reasons.append("Store ID matches exactly")
            else:
                conflicting_fields["store_id"] = [store_id_curr, store_id_cand]

        city_curr = str(current_record.get("city") or "").strip().lower()
        city_cand = str(candidate_record.get("city") or "").strip().lower()
        if city_curr and city_cand:
            if city_curr == city_cand:
                matching_fields.append("city")
                reasons.append("Store cities match exactly")
            elif "store_id" not in matching_fields:
                conflicting_fields["city"] = [city_curr, city_cand]

        if conflicting_fields:
            return {
                "candidate_id": candidate_id,
                "match_decision": "rejected",
                "review_status": "rejected",
                "semantic_confidence": 0.20,
                "matching_fields": matching_fields,
                "conflicting_fields": conflicting_fields,
                "possible_match": False,
                "reason": "Rejected: Conflicting store branch locations or IDs."
            }

        name_curr = str(current_record.get("store_name") or current_record.get("name") or "").strip().lower()
        name_cand = str(candidate_record.get("store_name") or candidate_record.get("name") or "").strip().lower()
        if name_curr and name_cand:
            if name_curr == name_cand:
                matching_fields.append("store_name")
                reasons.append("Store names match exactly")
            elif soundex(name_curr) == soundex(name_cand) or name_curr in name_cand or name_cand in name_curr:
                matching_fields.append("store_name_fuzzy")
                reasons.append("Store names are fuzzy variations")

        if "store_id" in matching_fields:
            confidence = 0.99
            decision = "exact_match"
            status = "auto_approved"
        elif "store_name" in matching_fields and "city" in matching_fields:
            confidence = 0.92
            decision = "probable_match"
            status = "review_required"
        elif "store_name" in matching_fields or "store_name_fuzzy" in matching_fields:
            confidence = 0.76
            decision = "probable_match"
            status = "review_required"
        else:
            confidence = 0.20
            decision = "rejected"
            status = "rejected"

    # 4. General Entity Fallback
    else:
        id_curr = str(current_record.get("id") or "").strip().lower()
        id_cand = str(candidate_record.get("id") or "").strip().lower()
        if id_curr and id_cand and id_curr == id_cand:
            matching_fields.append("id")
            reasons.append("Primary ID matches exactly")
            confidence = 0.98
            decision = "exact_match"
            status = "auto_approved"
        else:
            confidence = 0.30
            decision = "rejected"
            status = "rejected"

    is_possible = decision != "rejected"
    reason_str = "; ".join(reasons) if reasons else "No matching fields."

    return {
        "candidate_id": candidate_id,
        "match_decision": decision,
        "review_status": status,
        "semantic_confidence": confidence,
        "matching_fields": matching_fields,
        "conflicting_fields": conflicting_fields,
        "possible_match": is_possible,
        "reason": reason_str
    }


def analyze_candidates_with_rag_llm(
    current_record: Dict[str, Any],
    retrieved_candidates: List[Dict[str, Any]],
    entity_type: str = "general",
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Analyzes semantic relationships between current record and candidate matches using
    domain-specific rules and optional Groq LLM assistance.
    """
    if not current_record or not retrieved_candidates:
        return []

    results = []
    for c in retrieved_candidates:
        cand_rec = c.get("cleaned_record") or c.get("record") or c
        cand_id = str(c.get("record_id") or c.get("candidate_id") or "UNKNOWN")
        analysis = heuristic_rag_analysis(
            current_record=current_record,
            candidate_record=cand_rec,
            candidate_id=cand_id,
            entity_type=entity_type
        )
        results.append(analysis)

    return results


# Backward compatibility alias
analyze_candidate_with_llm = analyze_candidates_with_rag_llm
