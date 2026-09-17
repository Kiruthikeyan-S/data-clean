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


def safe_duplicated(df: pd.DataFrame, subset=None, keep: str = "first") -> pd.Series:
    """Computes duplicate mask safely even if cells contain unhashable types like dicts or lists."""
    try:
        if subset:
            return df.duplicated(subset=subset, keep=keep)
        return df.duplicated(keep=keep)
    except TypeError:
        target = df[subset] if subset else df
        str_df = target.map(lambda x: json.dumps(x, sort_keys=True, default=str) if isinstance(x, (dict, list, set)) else str(x))
        return str_df.duplicated(keep=keep)


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
    try:
        all_empty_mask = df.isna().all(axis=1) | (df.astype(str).replace(r'^\s*$', np.nan, regex=True).isna().all(axis=1))
        empty_rows_count = int(all_empty_mask.sum())
        if empty_rows_count > 0:
            df = df[~all_empty_mask].reset_index(drop=True)
            change_highlights.append(f"Removed {empty_rows_count} completely empty row(s)")
    except Exception:
        pass

    # 3. Cell-by-cell cleaning and metric tracking
    def clean_cell_tracker(val: Any) -> Any:
        nonlocal nulls_normalized_count, whitespace_trimmed_count
        if val is None:
            return None
        if isinstance(val, (dict, list, tuple, set)):
            # Convert unhashable nested dict/list into clean JSON string
            try:
                return json.dumps(val, ensure_ascii=False)
            except Exception:
                return str(val)
        try:
            if pd.isna(val):
                return None
        except Exception:
            pass
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

    # 3b. Sanitize negative numbers in positive-only inventory/quantity columns
    for col in df.columns:
        col_lower = str(col).lower()
        if any(k in col_lower for k in ("stock", "qty", "quantity", "inventory", "units")):
            def _clean_qty(v):
                if v is None:
                    return None
                try:
                    num = float(str(v).replace(",", "").strip())
                    if num < 0:
                        return abs(int(num)) if num.is_integer() else abs(num)
                except Exception:
                    pass
                return v
            df[col] = df[col].map(_clean_qty)

    # 4. Check for any rows that became completely empty after null normalization
    all_empty_after = df.isna().all(axis=1)
    extra_empty = int(all_empty_after.sum())
    if extra_empty > 0:
        empty_rows_count += extra_empty
        df = df[~all_empty_after].reset_index(drop=True)

    # 5. Deduplicate safely and capture duplicates count + sample
    dup_mask = safe_duplicated(df, keep="first")
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

    # 6. Drop completely empty columns (where all cells are None / NaN)
    empty_cols = [c for c in df.columns if df[c].isna().all()]
    if empty_cols and len(empty_cols) < len(df.columns):
        df = df.drop(columns=empty_cols)
        change_highlights.append(f"Removed {len(empty_cols)} completely empty column(s) with no data")

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
    Supports multi-collection JSON files and multi-sheet Excel workbooks.
    """
    is_multi_collection = False
    collections_data: Dict[str, Dict[str, Any]] = {}

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
        try:
            xl = pd.ExcelFile(io.BytesIO(file_bytes))
            sheet_names = xl.sheet_names
            if len(sheet_names) >= 2:
                # Multi-sheet Excel workbook
                for sname in sheet_names:
                    sheet_df = pd.read_excel(xl, sheet_name=sname, dtype=object)
                    if not sheet_df.empty:
                        raw_s_df = sheet_df.copy()
                        clean_s_df, s_metrics = clean_structured_dataframe(sheet_df)
                        if not clean_s_df.empty:
                            collections_data[sname] = {
                                "raw_df": raw_s_df,
                                "cleaned_df": clean_s_df,
                                "metrics": s_metrics
                            }
                if len(collections_data) >= 2:
                    is_multi_collection = True
                    df = pd.concat([c["cleaned_df"] for c in collections_data.values()], axis=0, ignore_index=True)
                elif len(collections_data) == 1:
                    df = list(collections_data.values())[0]["cleaned_df"]
                else:
                    df = pd.read_excel(xl, sheet_name=sheet_names[0], dtype=object)
            else:
                df = pd.read_excel(xl, sheet_name=sheet_names[0], dtype=object)
        except Exception:
            df = pd.read_excel(io.BytesIO(file_bytes), dtype=object)

    elif file_type == "json":
        data = json.loads(file_bytes.decode("utf-8"))
        if isinstance(data, list):
            # Flatten nested dicts if any
            try:
                df = pd.json_normalize(data, sep="_")
            except Exception:
                df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Check for multiple entity collections (e.g. {"stores": [...], "items": [...], "customers": [...]})
            coll_keys = [
                k for k, v in data.items()
                if (isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict)) or (isinstance(v, dict) and len(v) > 0)
            ]
            if len(coll_keys) >= 2:
                # Multi-collection JSON dataset
                for k in coll_keys:
                    val = data[k]
                    try:
                        if isinstance(val, list):
                            c_df = pd.json_normalize(val, sep="_")
                        elif isinstance(val, dict):
                            c_df = pd.json_normalize([val], sep="_")
                        else:
                            c_df = pd.DataFrame(val)
                    except Exception:
                        c_df = pd.DataFrame(val if isinstance(val, list) else [val])
                    
                    if not c_df.empty:
                        raw_c_df = c_df.copy()
                        clean_c_df, c_metrics = clean_structured_dataframe(c_df)
                        if not clean_c_df.empty:
                            collections_data[k] = {
                                "raw_df": raw_c_df,
                                "cleaned_df": clean_c_df,
                                "metrics": c_metrics
                            }
                if len(collections_data) >= 2:
                    is_multi_collection = True
                    df = pd.concat([c["cleaned_df"] for c in collections_data.values()], axis=0, ignore_index=True)
                elif len(collections_data) == 1:
                    df = list(collections_data.values())[0]["cleaned_df"]
                else:
                    df = pd.DataFrame([data])
            elif len(coll_keys) == 1:
                # Single collection wrapped in top-level dict (e.g. {"customers": [...]})
                k = coll_keys[0]
                val = data[k]
                try:
                    df = pd.json_normalize(val, sep="_") if isinstance(val, list) else pd.json_normalize([val], sep="_")
                except Exception:
                    df = pd.DataFrame(val if isinstance(val, list) else [val])
            elif any(isinstance(v, list) for v in data.values()):
                try:
                    df = pd.DataFrame(data)
                except Exception:
                    df = pd.json_normalize([data], sep="_")
            else:
                try:
                    df = pd.json_normalize([data], sep="_")
                except Exception:
                    df = pd.DataFrame([data])
        else:
            df = pd.DataFrame([{"data": data}])
    else:
        raise ValueError(f"Unsupported structured file type: {file_type}")
        
    # Keep copy of raw original dataframe before cleaning for quality auditing
    original_raw_df = df.copy()
    cleaned_df, metrics = clean_structured_dataframe(df)
    
    # Run comprehensive quality audit
    from backend.cleaning.data_auditor import audit_structured_data
    from backend.models.schemas import QualityAuditReport, QualityDimension
    
    if is_multi_collection:
        # Audit each collection individually to avoid cross-schema sparse matrix null inflation
        all_dims_by_id = {}
        total_issues_sum = 0
        total_cells_sum = 0
        total_rows_sum = 0
        
        for k, c_info in collections_data.items():
            c_audit = audit_structured_data(c_info["raw_df"], c_info["cleaned_df"])
            total_issues_sum += c_audit.total_issues_handled
            total_cells_sum += c_audit.total_cells or c_info["raw_df"].size
            total_rows_sum += c_audit.total_rows or len(c_info["raw_df"])
            
            for d in c_audit.dimensions:
                if d.id not in all_dims_by_id:
                    all_dims_by_id[d.id] = QualityDimension(
                        id=d.id,
                        title=d.title,
                        count=d.count,
                        status=d.status,
                        summary=d.summary,
                        affected_columns=list(d.affected_columns),
                        items=list(d.items),
                        raw_samples=list(d.raw_samples) if d.raw_samples else None,
                        total_denominator=d.total_denominator
                    )
                else:
                    target_d = all_dims_by_id[d.id]
                    target_d.count += d.count
                    target_d.affected_columns = list(set(target_d.affected_columns + d.affected_columns))
                    target_d.items.extend(d.items[:10])
                    if d.total_denominator:
                        target_d.total_denominator = (target_d.total_denominator or 0) + d.total_denominator
                    if target_d.count > 0:
                        if d.id == "record_matching":
                            target_d.status = f"{target_d.count} Candidates"
                        elif d.id == "missing_values":
                            target_d.status = f"{target_d.count} Handled"
                        else:
                            target_d.status = f"{target_d.count} Detected"
                    else:
                        target_d.status = "Clean"
                        
        from backend.models.schemas import RecordMatchingReport
        all_candidates = []
        all_merged_recs = []
        all_conflicts = []
        for k, c_info in collections_data.items():
            c_aud = audit_structured_data(c_info["raw_df"], c_info["cleaned_df"])
            if c_aud.record_matching:
                all_candidates.extend(c_aud.record_matching.candidate_pairs)
                all_merged_recs.extend(c_aud.record_matching.merged_records)
                all_conflicts.extend(c_aud.record_matching.conflicts)
                
        multi_matching_report = RecordMatchingReport(
            total_records=total_rows_sum,
            merge_candidates_count=len(all_candidates),
            merged_count=len(all_merged_recs),
            conflicts_count=len(all_conflicts),
            kept_separate_count=max(0, total_rows_sum - (len(all_merged_recs) * 2)),
            final_records_count=max(1, total_rows_sum - len(all_merged_recs)),
            candidate_pairs=all_candidates,
            merged_records=all_merged_recs,
            conflicts=all_conflicts
        )
        if "record_matching" in all_dims_by_id:
            all_dims_by_id["record_matching"].record_matching = multi_matching_report
            all_dims_by_id["record_matching"].count = len(all_candidates) + len(all_conflicts)
            all_dims_by_id["record_matching"].total_denominator = total_rows_sum
            all_dims_by_id["record_matching"].status = f"{len(all_candidates)} Candidates" if len(all_candidates) > 0 else ("Conflicts Found" if len(all_conflicts) > 0 else "Clean")

        audit_report = QualityAuditReport(
            dimensions=list(all_dims_by_id.values()),
            total_issues_handled=total_issues_sum,
            total_cells=total_cells_sum,
            total_rows=total_rows_sum,
            record_matching=multi_matching_report
        )
        metrics["quality_audit"] = audit_report
        metrics["is_multi_collection"] = True
        metrics["collections_data"] = collections_data
        metrics["duplicates_removed"] = sum(c_info["metrics"].get("duplicates_removed", 0) for c_info in collections_data.values())
        metrics["empty_rows_removed"] = sum(c_info["metrics"].get("empty_rows_removed", 0) for c_info in collections_data.values())
        metrics["nulls_normalized"] = sum(c_info["metrics"].get("nulls_normalized", 0) for c_info in collections_data.values())
        metrics["whitespace_trimmed"] = sum(c_info["metrics"].get("whitespace_trimmed", 0) for c_info in collections_data.values())
        metrics["change_highlights"].insert(0, f"Detected multi-entity dataset containing {len(collections_data)} collections: {', '.join(collections_data.keys())}")
    else:
        audit_report = audit_structured_data(original_raw_df, cleaned_df)
        metrics["quality_audit"] = audit_report
    
    records = cleaned_df.replace({np.nan: None}).to_dict(orient="records")
    columns = list(cleaned_df.columns)
    
    return records, columns, metrics
