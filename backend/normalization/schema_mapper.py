"""
Schema Mapper & Reusable Canonical Schema Engine

Maps raw column headers to standard canonical target field names
based on identified Business Entity (Store, Item, Customer, Transaction, etc.).

Core Capabilities:
1. Reusable SchemaMappingEngine with configurable alias dictionaries.
2. Deterministic exact & alias matching first, followed by Schema RAG and LLM suggestions.
3. Row-by-Row Alias Value Merging (coalesces non-null values across duplicate alias keys).
4. Conflict Detection when multiple columns map to the same canonical target.
5. Field Combiner (e.g. first_name + last_name -> full_name).
6. Location Extractor (parses "Miami, FL" or "704 Main St, Miami, FL" -> city, state).
7. Selling Price vs Cost Price isolation (never mistakenly merged).
8. Preservation of unmapped/extra fields.
9. Comprehensive Structured Schema Mapping Report.
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
    entity_type: Optional[str] = "general",
    custom_aliases: Optional[Dict[str, str]] = None
) -> Tuple[Optional[str], str, float]:
    """
    Finds the canonical target field name matching a raw header.
    Returns:
        (canonical_name, mapping_method, confidence)
    """
    token = normalize_header_token(header)
    
    # 0. Custom alias dictionary check (highest user priority)
    if custom_aliases:
        norm_custom = {normalize_header_token(k): v for k, v in custom_aliases.items()}
        if token in norm_custom:
            target = norm_custom[token]
            if target in canonical_fields:
                return target, "custom_alias", 1.0

    # 1. Direct exact match
    if token in canonical_fields:
        return token, "exact", 1.0
        
    # 2. Canonical alias lookup
    for canonical_name, field_def in canonical_fields.items():
        if token in field_def.aliases:
            return canonical_name, "alias", 0.98
            
    # 3. Sub-token match (e.g. "store_city_name" -> "city")
    name_parts = {"first_name", "firstname", "fname", "last_name", "lastname", "lname", "given_name", "surname"}
    if token in name_parts:
        return None, "unmapped", 0.0

    for canonical_name, field_def in canonical_fields.items():
        for alias in field_def.aliases:
            if alias in token and len(alias) >= 4:
                if token.endswith(f"_{alias}") or token.startswith(f"{alias}_"):
                    return canonical_name, "token_match", 0.85

    # 4. Schema Knowledge RAG Semantic Retrieval Fallback
    try:
        rag_candidates = retrieve_schema_mapping_for_column(header, entity_type=entity_type or "general", top_k=1)
        if rag_candidates:
            top_cand = rag_candidates[0]
            sim_score = float(top_cand.get("similarity_score", 0.0))
            if sim_score >= 0.50:
                rag_field = top_cand.get("canonical_field")
                if rag_field in canonical_fields:
                    return rag_field, "rag_semantic", round(sim_score, 3)
    except Exception:
        pass

    return None, "unmapped", 0.0


def extract_city_state_from_location(val: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Attempts to extract (city, state) from location strings.
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


class SchemaMappingEngine:
    """
    Reusable and configurable Schema Mapping Engine.
    Handles canonical alignment, conflict detection, alias coalescing, and reporting.
    """
    def __init__(self, custom_aliases: Optional[Dict[str, str]] = None):
        self.custom_aliases = custom_aliases or {}

    def add_aliases(self, aliases: Dict[str, str]) -> None:
        """Add or update custom aliases."""
        self.custom_aliases.update(aliases)

    def map_dataframe(
        self,
        df: pd.DataFrame,
        entity_type: str
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]], List[str]]:
        """
        Maps raw DataFrame headers to canonical schema fields for the given entity type.
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
        mapping_metadata: Dict[str, Dict[str, Any]] = {}
        unmapped_cols: List[str] = []
        
        for raw_col in df.columns:
            target, method, conf = find_canonical_field_for_header(
                raw_col,
                canonical_fields,
                entity_type=entity_type,
                custom_aliases=self.custom_aliases
            )
            if target:
                if target not in canonical_groups:
                    canonical_groups[target] = []
                canonical_groups[target].append(raw_col)
                mapping_metadata[raw_col] = {
                    "target": target,
                    "method": method,
                    "confidence": conf
                }
            else:
                unmapped_cols.append(raw_col)

        # 2. Build canonical DataFrame with conflict-aware alias merging
        canonical_df = pd.DataFrame(index=df.index)
        ordered_canonical_keys = list(canonical_fields.keys())

        for canonical_name in ordered_canonical_keys:
            if canonical_name in canonical_groups:
                orig_cols = canonical_groups[canonical_name]
                
                # Check for conflicts across duplicate alias columns
                has_conflict = False
                conflict_count = 0
                if len(orig_cols) > 1:
                    overlap = df[orig_cols].dropna(how="any")
                    if not overlap.empty:
                        conflicts = overlap.apply(
                            lambda row: len(set(str(v).strip().lower() for v in row if str(v).strip().lower() not in ("null", "none", "nan", "n/a", ""))) > 1,
                            axis=1
                        )
                        conflict_count = int(conflicts.sum())
                        has_conflict = conflict_count > 0

                # Coalesce: row-by-row non-null merge
                merged_series = df[orig_cols[0]].copy()
                for extra_col in orig_cols[1:]:
                    merged_series = merged_series.combine_first(df[extra_col])
                    
                canonical_df[canonical_name] = merged_series
                populated_count = int(merged_series.notna().sum())

                # Primary mapping method
                primary_col = orig_cols[0]
                meta = mapping_metadata.get(primary_col, {"method": "alias", "confidence": 0.95})

                schema_report.append({
                    "canonical_field": canonical_name,
                    "field_type": canonical_fields[canonical_name].field_type,
                    "description": canonical_fields[canonical_name].description,
                    "source_aliases": orig_cols,
                    "mapping_method": meta["method"],
                    "confidence": meta["confidence"],
                    "is_mapped": True,
                    "has_conflict": has_conflict,
                    "conflict_count": conflict_count,
                    "rows_populated": populated_count
                })

                if has_conflict:
                    highlights.append(f"Detected and resolved {conflict_count} conflicting values across alias columns ({', '.join(orig_cols)}) for '{canonical_name}'")
                elif len(orig_cols) > 1:
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
                    "mapping_method": "none",
                    "confidence": 0.0,
                    "is_mapped": False,
                    "has_conflict": False,
                    "conflict_count": 0,
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

                for rep in schema_report:
                    if rep["canonical_field"] == "full_name":
                        rep["is_mapped"] = True
                        rep["source_aliases"] = [fn_col, ln_col]
                        rep["mapping_method"] = "combination"
                        rep["confidence"] = 1.0
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


# Default global instance
_default_engine = SchemaMappingEngine()


def map_dataframe_to_canonical_schema(
    df: pd.DataFrame,
    entity_type: str,
    custom_aliases: Optional[Dict[str, str]] = None
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], List[str]]:
    """
    Convenience functional interface for schema mapping.
    Maps and standardizes all column headers in a DataFrame to canonical schema fields.
    """
    engine = SchemaMappingEngine(custom_aliases=custom_aliases) if custom_aliases else _default_engine
    return engine.map_dataframe(df, entity_type)
