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
    val_str = re.sub(r'\s+', ' ', val_str)
    return val_str

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
    
    for key in all_keys:
        val_a = rec_a.get(key)
        val_b = rec_b.get(key)
        
        is_empty_a = is_empty_value(val_a)
        is_empty_b = is_empty_value(val_b)
        
        if not is_empty_a and not is_empty_b:
            norm_a = normalize_match_val(val_a)
            norm_b = normalize_match_val(val_b)
            
            if norm_a == norm_b:
                matched_fields.append(str(key))
                weighted_score += get_field_weight(str(key))
            else:
                conflicts[str(key)] = [val_a, val_b]
                
    confidence = min(0.99, round(weighted_score / max(len(matched_fields) or 1, 2.0) * (len(matched_fields) / 2.0), 2))
    confidence = min(0.98, max(0.0, confidence))
    if len(matched_fields) >= 3:
        confidence = max(confidence, 0.88)
    elif len(matched_fields) == 2:
        confidence = max(confidence, 0.72)
        
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

    for i in range(n):
        for j in range(i + 1, n):
            comparison_count += 1
            if comparison_count > max_comparisons:
                break
                
            rec_a = records[i]
            rec_b = records[j]
            
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
                            entity_type=entity_type
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