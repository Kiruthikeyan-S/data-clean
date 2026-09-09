import io
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

NULL_VALUES = {
    "n/a", "na", "null", "none", "nil", "undefined", "unknown", 
    "-", "--", "nan", "nat", "#n/a", "#na", "null value"
}

def clean_column_name(col: Any) -> str:
    """Cleans and standardizes column headers."""
    s = str(col).strip()
    s = " ".join(s.split())
    return s if s else "Column"


def clean_structured_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans a pandas DataFrame and tracks comprehensive cleansing metrics:
    1. Removes completely empty rows and columns.
    2. Drops duplicate rows (and retains sample duplicate records).
    3. Trims whitespace and normalizes null representations.
    4. Generates an itemized change report.
    """
    initial_rows, initial_cols = df.shape
    empty_rows_count = 0
    duplicates_count = 0
    nulls_normalized_count = 0
    whitespace_trimmed_count = 0
    change_highlights: List[str] = []
    
    # 1. Clean column headers
    cleaned_cols = []
    seen = {}
    headers_changed = 0
    for col in df.columns:
        c_clean = clean_column_name(col)
        if str(col) != c_clean:
            headers_changed += 1
        if c_clean in seen:
            seen[c_clean] += 1
            cleaned_cols.append(f"{c_clean}_{seen[c_clean]}")
        else:
            seen[c_clean] = 0
            cleaned_cols.append(c_clean)
    df.columns = cleaned_cols
    if headers_changed > 0:
        change_highlights.append(f"Standardized {headers_changed} column header name(s)")

    # 2. Count & drop completely empty rows before cell cleaning
    all_empty_mask = df.isna().all(axis=1) | (df.astype(str).replace(r'^\s*$', np.nan, regex=True).isna().all(axis=1))
    empty_rows_count = int(all_empty_mask.sum())
    if empty_rows_count > 0:
        df = df[~all_empty_mask].reset_index(drop=True)
        change_highlights.append(f"Removed {empty_rows_count} completely empty row(s)")

    # 3. Cell-by-cell cleaning and metric tracking
    def clean_cell_tracker(val: Any) -> Any:
        nonlocal nulls_normalized_count, whitespace_trimmed_count
        if pd.isna(val) or val is None:
            return None
        if isinstance(val, str):
            v_strip = val.strip()
            if val != v_strip:
                whitespace_trimmed_count += 1
            if not v_strip or v_strip.lower() in NULL_VALUES:
                nulls_normalized_count += 1
                return None
            return v_strip
        if isinstance(val, (np.generic, np.number)):
            if np.isnan(val):
                return None
            return val.item()
        return val

    df = df.map(clean_cell_tracker)

    # 4. Check for any rows that became completely empty after null normalization
    all_empty_after = df.isna().all(axis=1)
    extra_empty = int(all_empty_after.sum())
    if extra_empty > 0:
        empty_rows_count += extra_empty
        df = df[~all_empty_after].reset_index(drop=True)

    # 5. Deduplicate and capture duplicates count + sample
    dup_mask = df.duplicated(keep="first")
    duplicates_count = int(dup_mask.sum())
    removed_samples = []
    if duplicates_count > 0:
        # Capture up to 5 sample duplicate records
        sample_dups = df[dup_mask].head(5).replace({np.nan: None}).to_dict(orient="records")
        removed_samples = sample_dups
        df = df[~dup_mask].reset_index(drop=True)
        change_highlights.append(f"Removed {duplicates_count} duplicate record(s)")

    if whitespace_trimmed_count > 0:
        change_highlights.append(f"Trimmed leading/trailing whitespace in {whitespace_trimmed_count} cell(s)")
    if nulls_normalized_count > 0:
        change_highlights.append(f"Standardized {nulls_normalized_count} inconsistent missing/null values (e.g. 'N/A', 'null', empty strings)")

    final_rows, final_cols = df.shape

    metrics = {
        "initial_rows": initial_rows,
        "final_rows": final_rows,
        "duplicates_removed": duplicates_count,
        "empty_rows_removed": empty_rows_count,
        "nulls_normalized": nulls_normalized_count,
        "whitespace_trimmed": whitespace_trimmed_count,
        "modifications_count": duplicates_count + empty_rows_count + nulls_normalized_count + whitespace_trimmed_count,
        "change_highlights": change_highlights,
        "removed_samples": removed_samples,
        "column_names": list(df.columns)
    }

    return df, metrics


def read_and_clean_structured_file(file_type: str, file_bytes: bytes) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, Any]]:
    """
    Reads CSV, Excel, or JSON bytes into DataFrame, cleans it, and returns records, columns, and metrics.
    """
    if file_type == "csv":
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), skipinitialspace=True, dtype=object)
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1", skipinitialspace=True, dtype=object)
            except Exception:
                df = pd.read_csv(io.BytesIO(file_bytes), engine="python", on_bad_lines="skip", skipinitialspace=True, dtype=object)
        except Exception:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), engine="python", on_bad_lines="skip", skipinitialspace=True, dtype=object)
            except Exception:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1", engine="python", on_bad_lines="skip", dtype=object)
    elif file_type == "excel":
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=object)
    elif file_type == "json":
        data = json.loads(file_bytes.decode("utf-8"))
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            if any(isinstance(v, list) for v in data.values()):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
        else:
            df = pd.DataFrame([{"data": data}])
    else:
        raise ValueError(f"Unsupported structured file type: {file_type}")
        
    # Keep copy of raw original dataframe before cleaning for quality auditing
    original_raw_df = df.copy()
    cleaned_df, metrics = clean_structured_dataframe(df)
    
    # Run comprehensive quality audit on raw vs cleaned data
    from backend.cleaning.data_auditor import audit_structured_data
    audit_report = audit_structured_data(original_raw_df, cleaned_df)
    metrics["quality_audit"] = audit_report
    
    records = cleaned_df.replace({np.nan: None}).to_dict(orient="records")
    columns = list(cleaned_df.columns)
    
    return records, columns, metrics
