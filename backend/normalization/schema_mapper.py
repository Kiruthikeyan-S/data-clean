"""
Schema Mapper & Row-by-Row Alias Merger Module

Maps raw column headers to standard canonical target field names
based on identified Business Entity (Store, Item, Customer, Transaction).

Core Capabilities:
1. Row-by-Row Alias Value Merging (coalesces non-null values across duplicate alias keys)
2. Field Combiner (e.g. first_name + last_name -> full_name)
3. Location Extractor (parses "Miami, FL" or "704 Main St, Miami, FL" -> city, state)
4. Selling Price vs Cost Price isolation (never merged)
5. Unmapped/extra fields preservation
6. Structured Schema Mapping Reporting
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
from backend.rag.schema_retriever import retrieve_schema_mapping_for_column


def normalize_header_token(header: str) -> str:
    """Normalizes header string for alias matching."""
    s = str(header).strip().lower()
    s = re.sub(r"[\s\-\.]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def find_canonical_field_for_header(
    header: str,
    canonical_fields: Dict[str, CanonicalField],
    entity_type: Optional[str] = "general"
) -> Optional[str]:
    """
    Finds the canonical target field name matching a raw header.
    Matches exact canonical name, alias dictionary, sub-token, or Schema RAG retrieval.
    """
    token = normalize_header_token(header)
    
    # Direct exact match
    if token in canonical_fields:
        return token
        
    # Alias lookup
    for canonical_name, field_def in canonical_fields.items():
        if token in field_def.aliases:
            return canonical_name
            
    # Sub-token match (e.g. "store_city_name" -> "city")
    # Exclude name parts (first_name, last_name) from accidentally matching full_name
    name_parts = {"first_name", "firstname", "fname", "last_name", "lastname", "lname", "given_name", "surname"}
    if token in name_parts:
        return None

    for canonical_name, field_def in canonical_fields.items():
        for alias in field_def.aliases:
            if alias in token and len(alias) >= 4:
                if token.endswith(f"_{alias}") or token.startswith(f"{alias}_"):
                    return canonical_name

    # Schema Knowledge RAG Semantic Retrieval Fallback
    try:
        rag_candidates = retrieve_schema_mapping_for_column(header, entity_type=entity_type or "general", top_k=1)
        if rag_candidates:
            top_cand = rag_candidates[0]
            if top_cand.get("similarity_score", 0) >= 0.50:
                rag_field = top_cand.get("canonical_field")
                if rag_field in canonical_fields:
                    return rag_field
    except Exception:
        pass

    return None


def extract_city_state_from_location(val: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Attempts to extract (city, state) from location strings like:
    - '704 Main St, Miami, FL' -> ('Miami', 'FL')
    - 'Miami, FL' -> ('Miami', 'FL')
    - 'CO, Denver' -> ('Denver', 'CO')
    - 'Denver, CO' -> ('Denver', 'CO')
    - 'Dallas, TX' -> ('Dallas', 'TX')
    - 'Chennai, Tamil Nadu' -> ('Chennai', 'Tamil Nadu')
    """
    if val is None or pd.isna(val) or not isinstance(val, str):
        return None, None
    s = val.strip()
    if not s or s.lower() in ("null", "none", "nan", "n/a", "-"):
        return None, None
        
    # Match: "CO, Denver" (State, City)
    m_rev = re.match(r"^([A-Za-z]{2}),\s*([A-Za-z\s]+)$", s)
    if m_rev:
        return m_rev.group(2).strip(), m_rev.group(1).strip().upper()

    # Match: "..., City, State" or "City, State"
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if len(parts) >= 2:
        candidate_state = parts[-1].strip()
        candidate_city = parts[-2].strip()
        if len(candidate_state) == 2:
            candidate_state = candidate_state.upper()
        # Clean street number/name if mixed in city part
        city_clean = re.sub(r"^\d+\s+[A-Za-z0-9\.\s]+(?:\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd))\s*", "", candidate_city, flags=re.IGNORECASE).strip()
        if not city_clean:
            city_clean = candidate_city
        return city_clean, candidate_state

    return None, None


def map_dataframe_to_canonical_schema(
    df: pd.DataFrame,
    entity_type: str
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], List[str]]:
    """
    Maps and standardizes all column headers in a DataFrame to canonical schema fields.
    Merges non-null values across duplicate alias columns row-by-row and deletes old alias columns.

    Args:
        df: The DataFrame to map.
        entity_type: The identified entity type ('store', 'item', 'customer', 'transaction').

    Returns:
        Tuple containing:
          - pd.DataFrame with clean canonical column headers & merged values
          - List[Dict[str, Any]]: Structured schema mapping report
          - List[str]: Human-readable change highlights
    """
    if df.empty or not entity_type or entity_type.lower() in ("unknown", "general"):
        return df, [], []

    canonical_fields = get_canonical_fields(entity_type)
    if not canonical_fields:
        return df, [], []

    schema_report: List[Dict[str, Any]] = []
    highlights: List[str] = []
    
    # 1. Group original columns by canonical target
    canonical_groups: Dict[str, List[str]] = {}
    unmapped_cols: List[str] = []
    
    for raw_col in df.columns:
        canonical_target = find_canonical_field_for_header(raw_col, canonical_fields, entity_type=entity_type)
        if canonical_target:
            if canonical_target not in canonical_groups:
                canonical_groups[canonical_target] = []
            canonical_groups[canonical_target].append(raw_col)
        else:
            unmapped_cols.append(raw_col)

    # 2. Build new canonical DataFrame with row-by-row alias merging
    canonical_df = pd.DataFrame(index=df.index)

    # Define standard column order from canonical schema
    ordered_canonical_keys = list(canonical_fields.keys())

    for canonical_name in ordered_canonical_keys:
        if canonical_name in canonical_groups:
            orig_cols = canonical_groups[canonical_name]
            
            # Row-by-row non-null merge across all matched alias columns
            merged_series = df[orig_cols[0]].copy()
            for extra_col in orig_cols[1:]:
                # Coalesce: take first non-null, non-empty value
                merged_series = merged_series.combine_first(df[extra_col])
                
            canonical_df[canonical_name] = merged_series
            populated_count = int(merged_series.notna().sum())

            schema_report.append({
                "canonical_field": canonical_name,
                "field_type": canonical_fields[canonical_name].field_type,
                "description": canonical_fields[canonical_name].description,
                "source_aliases": orig_cols,
                "is_mapped": True,
                "rows_populated": populated_count
            })

            if len(orig_cols) > 1:
                highlights.append(f"Merged alias columns ({', '.join(orig_cols)}) into single canonical field '{canonical_name}'")
            elif str(orig_cols[0]) != canonical_name:
                highlights.append(f"Mapped header '{orig_cols[0]}' → canonical '{canonical_name}'")
        else:
            # Field was not present in input
            schema_report.append({
                "canonical_field": canonical_name,
                "field_type": canonical_fields[canonical_name].field_type,
                "description": canonical_fields[canonical_name].description,
                "source_aliases": [],
                "is_mapped": False,
                "rows_populated": 0
            })

    # 3. Special field combination rules
    # A. Customer full_name combination (first_name + last_name)
    if entity_type == EntityType.CUSTOMER.value:
        norm_unmapped = {normalize_header_token(c): c for c in unmapped_cols}
        has_fn = "first_name" in norm_unmapped or "firstname" in norm_unmapped or "fname" in norm_unmapped
        has_ln = "last_name" in norm_unmapped or "lastname" in norm_unmapped or "lname" in norm_unmapped
        
        if has_fn and has_ln:
            fn_col = norm_unmapped.get("first_name") or norm_unmapped.get("firstname") or norm_unmapped.get("fname")
            ln_col = norm_unmapped.get("last_name") or norm_unmapped.get("lastname") or norm_unmapped.get("lname")
            
            combined_name = (df[fn_col].fillna("").astype(str).str.strip() + " " + df[ln_col].fillna("").astype(str).str.strip()).str.strip()
            if "full_name" in canonical_df and not canonical_df["full_name"].empty:
                canonical_df["full_name"] = canonical_df["full_name"].combine_first(combined_name)
            else:
                canonical_df["full_name"] = combined_name
                
            highlights.append(f"Combined separate '{fn_col}' and '{ln_col}' columns into canonical 'full_name'")
            if fn_col in unmapped_cols: unmapped_cols.remove(fn_col)
            if ln_col in unmapped_cols: unmapped_cols.remove(ln_col)

            # Update schema report for full_name
            for rep in schema_report:
                if rep["canonical_field"] == "full_name":
                    rep["is_mapped"] = True
                    rep["source_aliases"] = [fn_col, ln_col]
                    rep["rows_populated"] = int(canonical_df["full_name"].notna().sum())

    # B. Location splitting for Store / Customer (City / State from address or location)
    if entity_type in (EntityType.STORE.value, EntityType.CUSTOMER.value):
        loc_candidates = [c for c in df.columns if any(k in normalize_header_token(c) for k in ("location", "address", "addr"))]
        for l_col in loc_candidates:
            extracted_any = False
            for idx in df.index:
                val = df.loc[idx, l_col]
                c_ext, s_ext = extract_city_state_from_location(val)
                if c_ext and "city" in canonical_df:
                    if pd.isna(canonical_df.loc[idx, "city"]) or not str(canonical_df.loc[idx, "city"]).strip():
                        canonical_df.loc[idx, "city"] = c_ext
                        extracted_any = True
                if s_ext and "state" in canonical_df:
                    if pd.isna(canonical_df.loc[idx, "state"]) or not str(canonical_df.loc[idx, "state"]).strip():
                        canonical_df.loc[idx, "state"] = s_ext
                        extracted_any = True
            if extracted_any:
                highlights.append(f"Extracted city/state values from '{l_col}'")

    # 4. Retain any unmapped extra columns (do NOT delete unrecognized fields)
    for u_col in unmapped_cols:
        canonical_df[u_col] = df[u_col]

    return canonical_df, schema_report, highlights
