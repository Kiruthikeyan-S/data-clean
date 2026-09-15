from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

from backend.models import entity_schemas
from backend.extraction.entity_classifier import EntityClassificationResult


@dataclass
class EntityTable:
    """
    Represents a separated table for a specific entity type.
    """
    entity_type: str  # 'store', 'item', 'customer', 'transaction'
    display_name: str  # 'Store Data', 'Item Data', etc.
    icon: str  # '🏪', '📦', '👤', '🧾'
    columns: List[str]
    records: List[Dict[str, Any]]
    total_rows: int
    deduplicated_rows: int  # rows after dedup
    duplicates_removed: int
    confidence: float  # from classifier


def deduplicate_entity(df: pd.DataFrame, entity_type: str) -> Tuple[pd.DataFrame, int]:
    """
    Deduplicates a single-entity DataFrame.

    For Store/Item/Customer: Drop exact duplicate rows.
    For Transaction: Return as-is with 0 duplicates removed.

    If available, use the first column ending in `_id` or `id` as the primary dedup key.
    Otherwise, deduplicate on all columns.

    Args:
        df (pd.DataFrame): The single-entity DataFrame to deduplicate.
        entity_type (str): The entity type ('store', 'item', 'customer', 'transaction').

    Returns:
        Tuple[pd.DataFrame, int]: A tuple containing the deduplicated DataFrame and the number of duplicates removed.
    """
    if df.empty:
        return df, 0

    if entity_type.lower() == 'transaction':
        return df, 0
    
    initial_rows = len(df)
    
    # Find potential ID column for deduplication
    id_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if col_lower.endswith('_id') or col_lower == 'id':
            id_col = col
            break
            
    try:
        if id_col:
            deduped_df = df.drop_duplicates(subset=[id_col], keep='first')
        else:
            deduped_df = df.drop_duplicates(keep='first')
    except TypeError:
        import json
        if id_col:
            str_series = df[id_col].astype(str)
            dup_mask = str_series.duplicated(keep='first')
        else:
            str_df = df.map(lambda x: json.dumps(x, sort_keys=True, default=str) if isinstance(x, (dict, list, set)) else str(x))
            dup_mask = str_df.duplicated(keep='first')
        deduped_df = df[~dup_mask]
        
    duplicates_removed = initial_rows - len(deduped_df)
    
    return deduped_df, duplicates_removed


def split_mixed_dataframe(df: pd.DataFrame, classification: EntityClassificationResult) -> List[EntityTable]:
    """
    Splits a mixed DataFrame into separate entity-specific DataFrames based on
    column assignments from the Entity Classifier.

    Args:
        df (pd.DataFrame): The full cleaned DataFrame containing columns from multiple entities.
        classification (EntityClassificationResult): The classification result containing column assignments.

    Returns:
        List[EntityTable]: A list of separated entity tables.
    """
    entity_tables = []
    
    if df.empty or not classification or not classification.column_assignments:
        return entity_tables
        
    # Group columns by assigned entity
    entity_cols: Dict[str, List[str]] = {}
    for col, entity in classification.column_assignments.items():
        if col in df.columns:
            if entity not in entity_cols:
                entity_cols[entity] = []
            entity_cols[entity].append(col)
            
    # Foreign key keywords to include in Transaction
    fk_keywords = ['store_id', 'customer_id', 'cust_id', 'client_id', 'product_id', 'item_id', 'member_id']
    fk_columns = [col for col in df.columns if any(kw in str(col).lower() for kw in fk_keywords)]
    
    entity_metadata = {
        'store': {'display': 'Store Data', 'icon': '🏪'},
        'item': {'display': 'Product/Item Data', 'icon': '📦'},
        'customer': {'display': 'Customer Data', 'icon': '👤'},
        'transaction': {'display': 'Transaction Data', 'icon': '🧾'}
    }
    
    for entity_type, cols in entity_cols.items():
        entity_lower = entity_type.lower()
        
        selected_cols = list(cols)
        
        # Add FKs to transaction entity
        if entity_lower == 'transaction':
            for fk_col in fk_columns:
                if fk_col not in selected_cols:
                    selected_cols.append(fk_col)
                    
        # Extract subset
        entity_df = df[selected_cols].copy()
        
        # Drop rows that are completely empty in these columns
        entity_df.dropna(how='all', inplace=True)
        
        if entity_df.empty:
            continue
            
        total_rows = len(entity_df)
        
        # Deduplicate
        deduped_df, duplicates_removed = deduplicate_entity(entity_df, entity_lower)
        deduped_df.reset_index(drop=True, inplace=True)
        
        # Determine confidence score
        confidence = 0.0
        if hasattr(classification, 'entity_confidence') and classification.entity_confidence and entity_type in classification.entity_confidence:
            confidence = classification.entity_confidence[entity_type]
        elif hasattr(classification, 'confidence_score'):
            confidence = classification.confidence_score
            
        meta = entity_metadata.get(entity_lower, {'display': f'{entity_type.capitalize()} Data', 'icon': '📁'})
        
        # Replace NaN with None for JSON serialization compatibility
        records = deduped_df.where(pd.notnull(deduped_df), None).to_dict(orient='records')
        
        table = EntityTable(
            entity_type=entity_lower,
            display_name=meta['display'],
            icon=meta['icon'],
            columns=list(deduped_df.columns),
            records=records,
            total_rows=total_rows,
            deduplicated_rows=len(deduped_df),
            duplicates_removed=duplicates_removed,
            confidence=confidence
        )
        entity_tables.append(table)
        
    return entity_tables
