"""
Schema Mapper & Alias Merger Module

Maps raw column headers to standard canonical target field names
based on identified Business Entity (Store, Item, Customer, Transaction).
Handles merging when multiple input aliases resolve to the same canonical target.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np

from backend.models.entity_schemas import (
    get_canonical_fields,
    CanonicalField,
    EntityType
)


def normalize_header_token(header: str) -> str:
    """Normalizes header string for alias matching."""
    s = str(header).strip().lower()
    s = re.sub(r"[\s\-\.]+", "_", s)
    return s


def find_canonical_field_for_header(
    header: str,
    canonical_fields: Dict[str, CanonicalField]
) -> Optional[str]:
    """
    Finds the canonical target field name matching a raw header.
    Matches exact canonical name or any alias in the canonical schema.
    """
    token = normalize_header_token(header)
    
    # Direct exact match
    if token in canonical_fields:
        return token
        
    # Alias lookup
    for canonical_name, field_def in canonical_fields.items():
        if token in field_def.aliases:
            return canonical_name
            
    # Fuzzy sub-token / prefix match if unequivocal
    # e.g. "store_city_name" -> "city", "product_unit_price" -> "unit_price"
    for canonical_name, field_def in canonical_fields.items():
        for alias in field_def.aliases:
            if alias in token and len(alias) >= 4:
                # Check if it's a strong specific match
                if token.endswith(f"_{alias}") or token.startswith(f"{alias}_"):
                    return canonical_name

    return None


def map_dataframe_to_canonical_schema(
    df: pd.DataFrame,
    entity_type: str
) -> Tuple[pd.DataFrame, Dict[str, str], List[str]]:
    """
    Maps and standardizes all column headers in a DataFrame to canonical names.
    If multiple raw columns map to the same canonical field, merges them safely.

    Args:
        df: The DataFrame to map.
        entity_type: The identified entity type ('store', 'item', 'customer', 'transaction').

    Returns:
        Tuple containing:
          - pd.DataFrame with canonical column headers
          - Dict[str, str]: Map of raw_column -> canonical_column
          - List[str]: Human-readable change highlights
    """
    if df.empty or not entity_type or entity_type.lower() in ("unknown", "general"):
        return df, {}, []

    canonical_fields = get_canonical_fields(entity_type)
    if not canonical_fields:
        return df, {}, []

    mapping: Dict[str, str] = {}
    highlights: List[str] = []
    
    # Group original columns by canonical target
    canonical_groups: Dict[str, List[str]] = {}
    
    for raw_col in df.columns:
        canonical_target = find_canonical_field_for_header(raw_col, canonical_fields)
        if canonical_target:
            mapping[raw_col] = canonical_target
            if canonical_target not in canonical_groups:
                canonical_groups[canonical_target] = []
            canonical_groups[canonical_target].append(raw_col)
            if str(raw_col) != canonical_target:
                highlights.append(f"Mapped header '{raw_col}' → canonical '{canonical_target}'")
        else:
            # Keep original column header if no standard canonical match
            mapping[raw_col] = str(raw_col)

    # Build new DataFrame with mapped and merged columns
    new_df = pd.DataFrame(index=df.index)
    processed_originals = set()

    for canonical_name, orig_cols in canonical_groups.items():
        if len(orig_cols) == 1:
            # Single column mapping
            new_df[canonical_name] = df[orig_cols[0]]
            processed_originals.add(orig_cols[0])
        else:
            # Multiple input columns map to the SAME canonical field (e.g. 'zip' and 'postal_code')
            # Merge by taking the first non-null, non-empty value across rows
            merged_series = df[orig_cols[0]].copy()
            for extra_col in orig_cols[1:]:
                # Fill nulls in merged_series with values from extra_col
                merged_series = merged_series.combine_first(df[extra_col])
                processed_originals.add(extra_col)
            new_df[canonical_name] = merged_series
            processed_originals.add(orig_cols[0])
            highlights.append(f"Merged alias columns ({', '.join(orig_cols)}) into single canonical field '{canonical_name}'")

    # Add any remaining unmapped columns
    for orig_col in df.columns:
        if orig_col not in processed_originals:
            new_df[orig_col] = df[orig_col]

    return new_df, mapping, highlights
