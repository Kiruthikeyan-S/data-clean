from __future__ import annotations
import re
import math
from typing import Dict, Any, List, Tuple, Optional, Set
import pandas as pd
import numpy as np

from backend.models.schemas import (
    RecordMatchCandidate,
    MergedRecordDetail,
    RecordMatchConflict,
    RecordMatchingReport
)
from backend.rag.llm_rag_analyzer import heuristic_rag_analysis, analyze_candidate_with_llm
from backend.rag.record_retriever import search_similar_records, ingest_records_batch

FIELD_WEIGHTS: Dict[str, float] = {
    'id': 1.0,
    'customer_id': 1.0,
    'store_id': 1.0,
    'item_id': 1.0,
    'product_id': 1.0,
    'sku': 1.0,
    'barcode': 1.0,
    'upc': 1.0,
    'ean': 1.0,
    'asin': 1.0,
    'branch_id': 1.0,
    'outlet_id': 1.0,
    'email': 0.85,
    'phone': 0.85,
    'mobile': 0.85,
    'contact': 0.85,
    'store_email': 0.85,
    'customer_email': 0.85,
    'customer_phone': 0.85,
    'name': 0.60,
    'full_name': 0.60,
    'first_name': 0.60,
    'last_name': 0.60,
    'store_name': 0.60,
    'product_name': 0.60,
    'item_name': 0.60,
    'address': 0.60,
    'street': 0.60,
    'location': 0.60,
    'manager': 0.60,
    'city': 0.30,
    'state': 0.30,
    'pin': 0.30,
    'pin_code': 0.30,
    'zip_code': 0.30,
    'postal_code': 0.30,
    'country': 0.20,
    'category': 0.30,
    'brand': 0.30,
    'department': 0.30,
    'gender': 0.20,
    'status': 0.20
}

NULL_STRINGS: Set[str] = {
    '', 'null', 'none', 'nan', 'nat', 'n/a', 'na', 'nil', 'undefined', '-', '--', '#n/a', 'unknown'
}

def is_empty_value(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, (int, float, bool)):
        if isinstance(val, float) and (np.isnan(val) or math.isnan(val)):
            return True
        return False
    val_str = str(val).strip().lower()
    return val_str in NULL_STRINGS

def normalize_match_val(val: Any) -> str:
    if is_empty_value(val):
        return ''
    val_str = str(val).strip().lower()
    if re.match(r'^\d+\.0+$', val_str):
        val_str = val_str.split('.')[0]
    # Remove punctuation commas, periods, hyphens for text comparison
    val_str = re.sub(r'[,;\.\-_]+', ' ', val_str)
    val_str = re.sub(r'\s+', ' ', val_str).strip()
    return val_str


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Computes exact Levenshtein character similarity ratio."""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    len1, len2 = len(s1), len(s2)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    dist = dp[len1][len2]
    max_len = max(len1, len2)
    return max(0.0, 1.0 - (dist / max_len))


def extract_distinctive_suffix(s: str) -> Optional[str]:
    """Extracts trailing index letters or digits like '1', '2', 'a', 'b'."""
    m = re.search(r'\b([a-z]|\d+|[ivx]+)\s*$', s.strip().lower())
    return m.group(1) if m else None


def string_similarity(s1: str, s2: str) -> float:
    """Computes token set / fuzzy character similarity between two strings (0.0 to 1.0)."""
    if not s1 or not s2:
        return 0.0
    s1_clean = s1.strip().lower()
    s2_clean = s2.strip().lower()
    if s1_clean == s2_clean:
        return 1.0

    # Check for conflicting index numbers/letters (e.g. "Admin User 1" vs "Admin User 2", "Store A" vs "Store B")
    suff1 = extract_distinctive_suffix(s1_clean)
    suff2 = extract_distinctive_suffix(s2_clean)
    if suff1 and suff2 and suff1 != suff2:
        return 0.20  # Explicitly different entity indices

    # Check for initial prefix (e.g. "s kiruthikeyan" vs "kiruthikeyan")
    tokens1 = s1_clean.split()
    tokens2 = s2_clean.split()
    
    # If first token is a single letter initial and remaining tokens match
    if len(tokens1) > 1 and len(tokens1[0]) == 1 and " ".join(tokens1[1:]) == s2_clean:
        return 0.92
    if len(tokens2) > 1 and len(tokens2[0]) == 1 and " ".join(tokens2[1:]) == s1_clean:
        return 0.92

    # Direct Levenshtein on full strings
    ratio_full = levenshtein_ratio(s1_clean, s2_clean)
    if ratio_full >= 0.75:
        return ratio_full

    # Token set Jaccard similarity
    t1 = set(tokens1)
    t2 = set(tokens2)
    if t1 and t2:
        jaccard_tokens = len(t1.intersection(t2)) / len(t1.union(t2))
        if jaccard_tokens >= 0.70:
            return min(0.95, 0.70 + (0.25 * jaccard_tokens))

    # Substring check only if length ratio is very close (e.g. >= 0.80)
    len_ratio = min(len(s1_clean), len(s2_clean)) / max(len(s1_clean), len(s2_clean))
    if (s1_clean in s2_clean or s2_clean in s1_clean) and len_ratio >= 0.80:
        return 0.85

    return ratio_full


def get_field_weight(field_name: str) -> float:
    clean_name = str(field_name).strip().lower().replace('-', '_').replace(' ', '_')
    if clean_name in FIELD_WEIGHTS:
        return FIELD_WEIGHTS[clean_name]
    for key, weight in FIELD_WEIGHTS.items():
        if key in clean_name or clean_name in key:
            return weight
    return 0.50


def compare_records(
    rec_a: Dict[str, Any],
    rec_b: Dict[str, Any],
    entity_type: Optional[str] = None
) -> Tuple[List[str], Dict[str, List[Any]], float]:
    all_keys = set(rec_a.keys()).union(set(rec_b.keys()))
    all_keys = {k for k in all_keys if not str(k).startswith('_')}
    
    matched_fields: List[str] = []
    conflicts: Dict[str, List[Any]] = {}
    weighted_score = 0.0
    total_active_weight = 0.0
    
    FUZZY_MATCHABLE_FIELDS = {
        'name', 'full_name', 'first_name', 'last_name', 'customer_name', 'store_name',
        'product_name', 'item_name', 'address', 'street', 'location', 'city', 'title', 'brand'
    }

    for key in all_keys:
        val_a = rec_a.get(key)
        val_b = rec_b.get(key)
        
        is_empty_a = is_empty_value(val_a)
        is_empty_b = is_empty_value(val_b)
        
        if not is_empty_a and not is_empty_b:
            norm_a = normalize_match_val(val_a)
            norm_b = normalize_match_val(val_b)
            k_clean = str(key).strip().lower().replace('-', '_').replace(' ', '_')
            f_weight = get_field_weight(k_clean)
            total_active_weight += f_weight
            
            # Exact match after punctuation/case normalization
            if norm_a == norm_b:
                matched_fields.append(str(key))
                weighted_score += f_weight
            elif k_clean in FUZZY_MATCHABLE_FIELDS or any(f in k_clean for f in FUZZY_MATCHABLE_FIELDS):
                # Fuzzy matching for names, addresses, products
                sim = string_similarity(norm_a, norm_b)
                if sim >= 0.70:
                    matched_fields.append(str(key))
                    weighted_score += (f_weight * sim)
                else:
                    conflicts[str(key)] = [val_a, val_b]
            else:
                conflicts[str(key)] = [val_a, val_b]
                
    if total_active_weight > 0:
        confidence = min(0.99, round(weighted_score / total_active_weight, 2))
    else:
        confidence = 0.0

    if len(matched_fields) >= 3 and len(conflicts) == 0:
        confidence = max(confidence, 0.95)
    elif len(matched_fields) == 2 and len(conflicts) == 0:
        confidence = max(confidence, 0.85)
        
    return matched_fields, conflicts, confidence

def merge_record_pair(
    rec_a: Dict[str, Any],
    rec_b: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[str]]:
    all_keys = set(rec_a.keys()).union(set(rec_b.keys()))
    all_keys = {k for k in all_keys if not str(k).startswith('_')}
    
    merged: Dict[str, Any] = {}
    filled_fields: List[str] = []
    
    for key in all_keys:
        val_a = rec_a.get(key)
        val_b = rec_b.get(key)
        
        is_empty_a = is_empty_value(val_a)
        is_empty_b = is_empty_value(val_b)
        
        if not is_empty_a and not is_empty_b:
            merged[key] = val_a
        elif not is_empty_a and is_empty_b:
            merged[key] = val_a
            filled_fields.append(str(key))
        elif is_empty_a and not is_empty_b:
            merged[key] = val_b
            filled_fields.append(str(key))
        else:
            merged[key] = None
            
    return merged, filled_fields

PRIMARY_ID_KEYS: Set[str] = {
    'id', 'customer_id', 'cust_id', 'client_id', 'member_id', 'user_id',
    'store_id', 'branch_id', 'outlet_id', 'warehouse_id',
    'item_id', 'product_id', 'sku', 'sku_id', 'barcode', 'upc', 'ean', 'asin',
    'transaction_id', 'order_id', 'invoice_id', 'receipt_id', 'bill_id', 'sale_id',
    'student_id', 'emp_id', 'employee_id', 'roll_no', 'reg_no'
}

def have_conflicting_primary_ids(rec_a: Dict[str, Any], rec_b: Dict[str, Any]) -> bool:
    """Returns True if both records have non-empty but DIFFERENT primary identifiers or distinct person names."""
    all_keys = set(rec_a.keys()).union(set(rec_b.keys()))
    for key in all_keys:
        k_clean = str(key).strip().lower().replace('-', '_').replace(' ', '_')
        # Check all ID columns (student_id, employee_id, id, etc.)
        if k_clean.endswith('_id') or k_clean.endswith('id') or k_clean in PRIMARY_ID_KEYS or k_clean in ('roll_no', 'reg_no', 'code'):
            val_a = rec_a.get(key)
            val_b = rec_b.get(key)
            if not is_empty_value(val_a) and not is_empty_value(val_b):
                if normalize_match_val(val_a) != normalize_match_val(val_b):
                    return True
        # Check name columns (name, full_name, first_name)
        if k_clean in ('name', 'full_name', 'first_name', 'student_name', 'customer_name', 'person_name'):
            val_a = rec_a.get(key)
            val_b = rec_b.get(key)
            if not is_empty_value(val_a) and not is_empty_value(val_b):
                norm_a = normalize_match_val(val_a)
                norm_b = normalize_match_val(val_b)
                if norm_a != norm_b and string_similarity(norm_a, norm_b) < 0.65:
                    return True
    return False

def analyze_record_matching(
    records: List[Dict[str, Any]],
    entity_type: Optional[str] = 'general',
    max_comparisons: int = 5000
) -> RecordMatchingReport:
    if not records or len(records) < 2:
        return RecordMatchingReport(
            total_records=len(records) if records else 0,
            merge_candidates_count=0,
            merged_count=0,
            conflicts_count=0,
            kept_separate_count=len(records) if records else 0,
            final_records_count=len(records) if records else 0
        )

    n = len(records)
    candidate_pairs: List[RecordMatchCandidate] = []
    merged_records: List[MergedRecordDetail] = []
    conflicts: List[RecordMatchConflict] = []
    
    matched_indices_set: Set[int] = set()
    comparison_count = 0
    is_transaction_entity = str(entity_type).lower().strip() in (
        'transaction', 'transactions', 'sale', 'sales', 'order', 'orders', 'log', 'logs'
    )

    for i in range(n):
        for j in range(i + 1, n):
            comparison_count += 1
            if comparison_count > max_comparisons:
                break
                
            rec_a = records[i]
            rec_b = records[j]

            # If comparing transaction events with different transaction IDs -> distinct transactions
            if is_transaction_entity:
                txn_id_a = rec_a.get('transaction_id') or rec_a.get('order_id') or rec_a.get('invoice_id')
                txn_id_b = rec_b.get('transaction_id') or rec_b.get('order_id') or rec_b.get('invoice_id')
                if txn_id_a and txn_id_b and normalize_match_val(txn_id_a) != normalize_match_val(txn_id_b):
                    continue

            # If both records have distinct non-empty Primary IDs (e.g. CUST-001 vs CUST-002) -> distinct entities
            if have_conflicting_primary_ids(rec_a, rec_b):
                continue
                
            matched_fields, conflict_dict, confidence = compare_records(rec_a, rec_b, entity_type)
            
            is_only_weak = all(get_field_weight(f) <= 0.30 for f in matched_fields)
            if len(matched_fields) == 2 and is_only_weak:
                continue
                
            if len(matched_fields) >= 2:
                if len(conflict_dict) > 0:
                    conflicts.append(RecordMatchConflict(
                        conflict_id=f'conflict_{i}_{j}',
                        record_a_index=i + 1,
                        record_b_index=j + 1,
                        record_a=rec_a,
                        record_b=rec_b,
                        matched_fields=matched_fields,
                        conflicting_fields=conflict_dict,
                        status='Review Required',
                        entity_type=entity_type
                    ))
                else:
                    merged_preview, filled_fields = merge_record_pair(rec_a, rec_b)
                    
                    if len(filled_fields) > 0:
                        status_label = 'high_confidence' if len(matched_fields) >= 3 or confidence >= 0.85 else 'merge_candidate'
                        rag_eval = heuristic_rag_analysis(rec_a, rec_b, f'cand_{i}_{j}', entity_type or 'general')
                        rag_explanation = rag_eval.get("reason", f"Matched using fields: {', '.join(matched_fields)}")
                        
                        candidate_pairs.append(RecordMatchCandidate(
                            candidate_id=f'cand_{i}_{j}',
                            record_a_index=i + 1,
                            record_b_index=j + 1,
                            record_a=rec_a,
                            record_b=rec_b,
                            matched_fields=matched_fields,
                            matched_field_count=len(matched_fields),
                            match_confidence=confidence,
                            match_status=status_label,
                            merged_preview=merged_preview,
                            entity_type=entity_type,
                            rag_explanation=rag_explanation,
                            rag_matched_record_id=rec_b.get("id") or rec_b.get(f"{entity_type}_id") or f"ROW-{j+1}"
                        ))
                        
                        merged_records.append(MergedRecordDetail(
                            merge_id=f'merge_{i}_{j}',
                            record_a_index=i + 1,
                            record_b_index=j + 1,
                            original_record_a=rec_a,
                            original_record_b=rec_b,
                            merged_record=merged_preview,
                            filled_fields=filled_fields,
                            matched_using_fields=matched_fields,
                            status='Successfully Merged',
                            entity_type=entity_type
                        ))
                        
                        matched_indices_set.add(i)
                        matched_indices_set.add(j)

        if comparison_count > max_comparisons:
            break

    merged_count = len(merged_records)
    candidates_count = len(candidate_pairs)
    conflicts_count = len(conflicts)
    
    kept_separate = max(0, n - len(matched_indices_set))
    final_records = max(1, n - merged_count)

    return RecordMatchingReport(
        total_records=n,
        merge_candidates_count=candidates_count,
        merged_count=merged_count,
        conflicts_count=conflicts_count,
        kept_separate_count=kept_separate,
        final_records_count=final_records,
        candidate_pairs=candidate_pairs,
        merged_records=merged_records,
        conflicts=conflicts
    )

def audit_record_matching_for_dataset(
    df: pd.DataFrame,
    entity_type: Optional[str] = 'general',
    split_collections: Optional[Dict[str, pd.DataFrame]] = None
) -> RecordMatchingReport:
    if split_collections and len(split_collections) > 0:
        combined_candidates: List[RecordMatchCandidate] = []
        combined_merged: List[MergedRecordDetail] = []
        combined_conflicts: List[RecordMatchConflict] = []
        total_rec_sum = 0
        
        for e_name, e_df in split_collections.items():
            if e_df is not None and not e_df.empty:
                e_records = e_df.replace({np.nan: None}).to_dict(orient='records')
                e_report = analyze_record_matching(e_records, entity_type=e_name)
                
                total_rec_sum += e_report.total_records
                combined_candidates.extend(e_report.candidate_pairs)
                combined_merged.extend(e_report.merged_records)
                combined_conflicts.extend(e_report.conflicts)
                
        return RecordMatchingReport(
            total_records=total_rec_sum or len(df),
            merge_candidates_count=len(combined_candidates),
            merged_count=len(combined_merged),
            conflicts_count=len(combined_conflicts),
            kept_separate_count=max(0, (total_rec_sum or len(df)) - (len(combined_merged) * 2)),
            final_records_count=max(1, (total_rec_sum or len(df)) - len(combined_merged)),
            candidate_pairs=combined_candidates,
            merged_records=combined_merged,
            conflicts=combined_conflicts
        )
    else:
        records = df.replace({np.nan: None}).to_dict(orient='records') if df is not None and not df.empty else []
        return analyze_record_matching(records, entity_type=entity_type)


def find_rag_matches_for_record(
    query_record: Dict[str, Any],
    entity_type: str = "customer",
    top_k: int = 5,
    min_similarity: float = 0.35
) -> Dict[str, Any]:
    """
    RAG-Powered Entity Matching Function.
    
    1. Retrieves Top-K similar historical records from the isolated Vector Database.
    2. Uses Groq LLM to generate semantic analysis and reason about relationship.
    3. Deterministically verifies field weights, exact/fuzzy matches, and validation rules.
    4. Returns structured decision JSON.
    """
    if not query_record:
        return {"possible_match": False, "matches": []}

    # Step 1: RAG Vector Retrieval
    candidates = search_similar_records(
        query_record=query_record,
        entity_type=entity_type,
        top_k=top_k,
        min_score=min_similarity
    )

    if not candidates:
        return {
            "possible_match": False,
            "query_record": query_record,
            "entity_type": entity_type,
            "matches": []
        }

    # Step 2: Groq LLM Semantic Analysis
    llm_analyses = analyze_candidate_with_llm(
        current_record=query_record,
        retrieved_candidates=candidates,
        entity_type=entity_type
    )

    llm_map = {a.get("candidate_id"): a for a in llm_analyses}

    # Step 3: Deterministic Record Matcher Verification
    verified_matches = []
    for cand in candidates:
        cand_id = cand["record_id"]
        cand_rec = cand["cleaned_record"]

        # Check conflicting primary IDs
        if have_conflicting_primary_ids(query_record, cand_rec):
            continue

        matched_fields, conflicts, confidence = compare_records(query_record, cand_rec, entity_type)
        
        # Must have at least 1 strong field or confidence >= 0.70
        is_only_weak = all(get_field_weight(f) <= 0.30 for f in matched_fields)
        if is_only_weak or len(matched_fields) == 0:
            continue

        llm_eval = llm_map.get(cand_id, {})
        reason = llm_eval.get("reason") or f"Matched using fields: {', '.join(matched_fields)}"

        merged_preview, filled_fields = merge_record_pair(query_record, cand_rec)

        verified_matches.append({
            "possible_match": True,
            "matched_record_id": cand_id,
            "matching_fields": matched_fields,
            "match_score": round(confidence, 2),
            "reason": reason,
            "has_conflicts": len(conflicts) > 0,
            "conflicting_fields": conflicts,
            "merged_preview": merged_preview,
            "filled_fields": filled_fields
        })

    # Sort by match score descending
    verified_matches.sort(key=lambda x: x["match_score"], reverse=True)

    best_match = verified_matches[0] if verified_matches else None

    return {
        "possible_match": bool(best_match),
        "best_match": best_match,
        "all_candidates": verified_matches,
        "retrieved_count": len(candidates),
        "verified_count": len(verified_matches)
    }