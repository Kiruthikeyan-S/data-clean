"""
Canonical Value Standardizer Module

Standardizes cell values based on canonical schema column types:
- Dates -> ISO 8601 (YYYY-MM-DD)
- Booleans -> True / False (Python boolean)
- Cities / States / Names -> Consistent Title Case
- IDs -> Consistent trimmed uppercase representation
- Prices / Numbers -> Clean numeric floats/ints without currency symbols
- Emails -> Lowercased & validated
- Phones -> Standardized E.164 / cleaned phone numbers
"""
from __future__ import annotations

import re
import json
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np

from backend.models.entity_schemas import get_canonical_fields, CanonicalField
from backend.normalization.normalizer import (
    normalize_name,
    normalize_date,
    normalize_email,
    normalize_phone,
    normalize_number,
    normalize_postal_code,
    normalize_text
)

BOOLEAN_TRUE_VALUES = {"true", "t", "yes", "y", "1", "1.0", "active", "in_stock", "available", "enabled"}
BOOLEAN_FALSE_VALUES = {"false", "f", "no", "n", "0", "0.0", "inactive", "out_of_stock", "disabled"}


def standardize_boolean(val: Any) -> Any:
    """Normalizes boolean-like representations to Python boolean."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in BOOLEAN_TRUE_VALUES:
        return True
    if s in BOOLEAN_FALSE_VALUES:
        return False
    return val


def standardize_id(val: Any) -> Any:
    """Normalizes identifier strings (trimmed, normalized format)."""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s.lower() in ("null", "none", "nan", "n/a", "-"):
        return None
    # If standard code format like s001 / str-01 / ord-123 -> uppercase prefix
    if re.match(r"^[a-zA-Z]+[-\s_]?\d+$", s):
        return s.upper()
    return s


def standardize_date_iso(val: Any) -> Any:
    """Standardizes dates (including ISO timestamps with T...Z) to YYYY-MM-DD."""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s.lower() in ("null", "none", "nan", "n/a", "-"):
        return None
    
    # Strip ISO timestamp time portion if present (e.g. "2020-11-01T00:00:00Z" -> "2020-11-01")
    iso_time_match = re.match(r"^(\d{4}[-/]\d{1,2}[-/]\d{1,2})[T\s].*$", s)
    if iso_time_match:
        s = iso_time_match.group(1)

    return normalize_date(s)


def standardize_canonical_values(
    df: pd.DataFrame,
    entity_type: str
) -> Tuple[pd.DataFrame, Dict[str, int], List[str]]:
    """
    Standardizes all values in a DataFrame according to the canonical field types
    of the identified Business Entity.

    Args:
        df: The DataFrame to standardize.
        entity_type: The identified entity type ('store', 'item', 'customer', 'transaction').

    Returns:
        Tuple containing:
          - pd.DataFrame with standardized cell values
          - Dict[str, int]: Modification count per field type
          - List[str]: Value standardization change highlights
    """
    if df.empty:
        return df, {}, []

    canonical_fields = get_canonical_fields(entity_type)
    std_df = df.copy()
    
    mod_counts = {
        "dates_standardized": 0,
        "booleans_standardized": 0,
        "text_standardized": 0,
        "numbers_standardized": 0,
        "ids_standardized": 0,
        "emails_standardized": 0,
        "phones_standardized": 0,
        "postal_codes_standardized": 0
    }
    highlights = []

    for col in std_df.columns:
        col_str = str(col)
        col_lower = col_str.lower()
        field_def: Optional[CanonicalField] = canonical_fields.get(col_lower)
        
        # Determine target field type
        field_type = field_def.field_type if field_def else None
        if not field_type:
            # Fallback heuristic by column name
            if "date" in col_lower or "dob" in col_lower or "opened" in col_lower or "registered" in col_lower:
                field_type = "date"
            elif "email" in col_lower:
                field_type = "email"
            elif "phone" in col_lower or "mobile" in col_lower:
                field_type = "phone"
            elif "price" in col_lower or "amount" in col_lower or "cost" in col_lower or "qty" in col_lower or "quantity" in col_lower or "points" in col_lower:
                field_type = "numeric"
            elif col_lower in ("status", "is_active", "active", "available", "is_available"):
                field_type = "boolean"
            elif col_lower.endswith("_id") or col_lower == "id" or col_lower.endswith("_code"):
                field_type = "id"
            elif col_lower in ("city", "state", "country", "name", "category", "brand", "manager_name", "store_name", "item_name", "full_name", "payment_method", "loyalty_tier"):
                field_type = "text_title"
            elif "zip" in col_lower or "pin" in col_lower or "postal" in col_lower:
                field_type = "postal_code"

        if not field_type:
            continue

        # Standardize based on field type
        new_values = []
        changed_in_col = 0

        for val in std_df[col]:
            if val is None or (isinstance(val, float) and np.isnan(val)):
                new_values.append(None)
                continue

            orig_val = val
            std_val = val

            if field_type == "date":
                std_val = standardize_date_iso(val)
                if std_val is not None and std_val != orig_val:
                    mod_counts["dates_standardized"] += 1
                    changed_in_col += 1
                elif std_val is None:
                    std_val = orig_val

            elif field_type == "boolean":
                std_val = standardize_boolean(val)
                if std_val is not None and std_val != orig_val:
                    mod_counts["booleans_standardized"] += 1
                    changed_in_col += 1

            elif field_type == "text_title":
                std_val = normalize_name(str(val))
                if std_val is not None and std_val != orig_val:
                    mod_counts["text_standardized"] += 1
                    changed_in_col += 1
                elif std_val is None:
                    std_val = orig_val

            elif field_type == "id":
                std_val = standardize_id(val)
                if std_val is not None and std_val != orig_val:
                    mod_counts["ids_standardized"] += 1
                    changed_in_col += 1
                elif std_val is None:
                    std_val = orig_val

            elif field_type == "numeric":
                std_val = normalize_number(val)
                if std_val is not None and std_val != orig_val:
                    mod_counts["numbers_standardized"] += 1
                    changed_in_col += 1
                elif std_val is None:
                    std_val = orig_val

            elif field_type == "email":
                std_val = normalize_email(str(val))
                if std_val is not None and std_val != orig_val:
                    mod_counts["emails_standardized"] += 1
                    changed_in_col += 1
                elif std_val is None:
                    std_val = orig_val

            elif field_type == "phone":
                std_val = normalize_phone(str(val))
                if std_val is not None and std_val != orig_val:
                    mod_counts["phones_standardized"] += 1
                    changed_in_col += 1
                elif std_val is None:
                    std_val = orig_val

            elif field_type == "postal_code":
                std_val = normalize_postal_code(val)
                if std_val is not None and std_val != orig_val:
                    mod_counts["postal_codes_standardized"] += 1
                    changed_in_col += 1
                elif std_val is None:
                    std_val = orig_val

            new_values.append(std_val)

        std_df[col] = new_values

    # Generate summary highlights
    if mod_counts["dates_standardized"] > 0:
        highlights.append(f"Standardized {mod_counts['dates_standardized']} date value(s) to ISO 8601 (YYYY-MM-DD)")
    if mod_counts["booleans_standardized"] > 0:
        highlights.append(f"Standardized {mod_counts['booleans_standardized']} boolean value(s) to canonical true/false")
    if mod_counts["text_standardized"] > 0:
        highlights.append(f"Standardized {mod_counts['text_standardized']} text / city / name cell(s) to Title Case")
    if mod_counts["numbers_standardized"] > 0:
        highlights.append(f"Standardized {mod_counts['numbers_standardized']} numeric / currency value(s) to clean numbers")
    if mod_counts["ids_standardized"] > 0:
        highlights.append(f"Standardized {mod_counts['ids_standardized']} ID / code representation(s)")
    if mod_counts["emails_standardized"] > 0:
        highlights.append(f"Standardized {mod_counts['emails_standardized']} email address(es)")
    if mod_counts["phones_standardized"] > 0:
        highlights.append(f"Standardized {mod_counts['phones_standardized']} phone number(s)")

    return std_df, mod_counts, highlights
