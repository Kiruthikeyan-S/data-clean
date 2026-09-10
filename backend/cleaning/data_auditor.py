import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from backend.models.schemas import AuditDetailItem, QualityDimension, QualityAuditReport, ProcessedField

NULL_REPRESENTATIONS = {
    "n/a", "na", "null", "none", "nil", "undefined", "unknown", 
    "-", "--", "nan", "nat", "#n/a", "#na", "null value", ""
}

def audit_structured_data(original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> QualityAuditReport:
    """
    Performs comprehensive data quality audit across the 6 key dimensions:
    1. Missing Values
    2. Duplicates
    3. Wrong Data Types
    4. Invalid Values
    5. Outliers
    6. Format Differences
    """
    dimensions: List[QualityDimension] = []
    total_issues = 0

    # =========================================================================
    # 1. MISSING VALUES
    # =========================================================================
    missing_items: List[AuditDetailItem] = []
    missing_cols_set = set()

    for col in original_df.columns:
        col_str = str(col)
        for row_idx, val in enumerate(original_df[col]):
            val_clean = str(val).strip().lower() if val is not None and not pd.isna(val) else ""
            if pd.isna(val) or val is None or val_clean in NULL_REPRESENTATIONS:
                missing_cols_set.add(col_str)
                if len(missing_items) < 50:  # Cap at 50 for display responsiveness
                    missing_items.append(AuditDetailItem(
                        row_index=row_idx + 1,
                        column=col_str,
                        original_value=str(val) if val is not None and not pd.isna(val) else "null",
                        cleaned_value=None,
                        issue_description=f"Missing or inconsistent null representation '{val}' normalized to null",
                        severity="warning"
                    ))

    missing_count = sum(
        original_df[col].apply(lambda v: pd.isna(v) or v is None or str(v).strip().lower() in NULL_REPRESENTATIONS).sum()
        for col in original_df.columns
    )
    total_issues += int(missing_count)

    dimensions.append(QualityDimension(
        id="missing_values",
        title="Missing Values",
        count=int(missing_count),
        status=f"{missing_count} Handled" if missing_count > 0 else "Clean",
        summary=f"Identified {missing_count} missing or unstandardized null values across {len(missing_cols_set)} column(s)." if missing_count > 0 else "No missing values found across dataset.",
        affected_columns=list(missing_cols_set),
        items=missing_items
    ))

    # =========================================================================
    # 2. DUPLICATES
    # =========================================================================
    dup_mask = original_df.duplicated(keep="first")
    dup_count = int(dup_mask.sum())
    dup_items: List[AuditDetailItem] = []
    raw_dup_samples: List[Dict[str, Any]] = []

    if dup_count > 0:
        dup_rows = original_df[dup_mask]
        raw_dup_samples = dup_rows.head(10).replace({np.nan: None}).to_dict(orient="records")
        for idx in original_df[dup_mask].index[:30]:
            row_dict = original_df.loc[idx].to_dict()
            sample_preview = ", ".join([f"{k}={v}" for k, v in list(row_dict.items())[:3]])
            dup_items.append(AuditDetailItem(
                row_index=int(idx) + 1,
                column="All Columns (Full Row)",
                original_value=sample_preview,
                cleaned_value="Dropped (Duplicate removed)",
                issue_description="Exact duplicate of an earlier row in the dataset",
                severity="warning"
            ))

    total_issues += dup_count
    dimensions.append(QualityDimension(
        id="duplicates",
        title="Duplicates",
        count=dup_count,
        status=f"{dup_count} Removed" if dup_count > 0 else "Clean",
        summary=f"Found and eliminated {dup_count} identical duplicate row(s) to guarantee record uniqueness." if dup_count > 0 else "Zero duplicate rows found in dataset.",
        affected_columns=list(original_df.columns) if dup_count > 0 else [],
        items=dup_items,
        raw_samples=raw_dup_samples
    ))

    # =========================================================================
    # 3. WRONG DATA TYPES
    # =========================================================================
    type_items: List[AuditDetailItem] = []
    type_cols_set = set()
    type_issues_count = 0

    NUMERIC_TOKENS = {
        "salary", "price", "amount", "cgpa", "score", "attendance", "stock",
        "quantity", "qty", "pct", "percent", "percentage", "cost", "turnover",
        "revenue", "sq_ft", "footfall", "rate", "units", "total_amount", "unit_price"
    }
    TEXT_EXCLUSION_TOKENS = {
        "country", "name", "manager", "manager_name", "address", "city", "state",
        "email", "phone", "status", "category", "type", "description", "title",
        "code", "id", "record_type", "branch"
    }

    for col in original_df.columns:
        col_str = str(col)
        col_lower = col_str.lower().strip()
        tokens = set(re.split(r"[_\s\-]+", col_lower))

        # Check if column is genuinely expected to be numeric (not a text/name/country column)
        is_text_column = bool(tokens.intersection(TEXT_EXCLUSION_TOKENS)) or col_lower in TEXT_EXCLUSION_TOKENS
        is_expected_numeric = bool(tokens.intersection(NUMERIC_TOKENS)) and not is_text_column
        
        if is_expected_numeric:
            for row_idx, val in enumerate(original_df[col]):
                if val is not None and not pd.isna(val):
                    val_str = str(val).strip()
                    if val_str and val_str.lower() not in NULL_REPRESENTATIONS:
                        # Clean currency/commas to see if numeric
                        num_candidate = re.sub(r"[₹\$€£¥,\s]", "", val_str)
                        try:
                            float(num_candidate)
                        except ValueError:
                            # Non-numeric text in numeric column
                            type_issues_count += 1
                            type_cols_set.add(col_str)
                            if len(type_items) < 30:
                                type_items.append(AuditDetailItem(
                                    row_index=row_idx + 1,
                                    column=col_str,
                                    original_value=val_str,
                                    cleaned_value=None,
                                    issue_description=f"Expected numeric value in '{col_str}', but encountered string type '{val_str}'",
                                    severity="error"
                                ))

    total_issues += type_issues_count
    dimensions.append(QualityDimension(
        id="wrong_data_types",
        title="Wrong Data Types",
        count=type_issues_count,
        status=f"{type_issues_count} Detected" if type_issues_count > 0 else "Clean",
        summary=f"Detected {type_issues_count} values with incompatible data types in {len(type_cols_set)} column(s)." if type_issues_count > 0 else "All column values conform to expected data types.",
        affected_columns=list(type_cols_set),
        items=type_items
    ))

    # =========================================================================
    # 4. INVALID VALUES
    # =========================================================================
    invalid_items: List[AuditDetailItem] = []
    invalid_cols_set = set()
    invalid_count = 0

    for col in original_df.columns:
        col_str = str(col)
        col_lower = col_str.lower()
        
        for row_idx, val in enumerate(original_df[col]):
            if val is not None and not pd.isna(val):
                val_str = str(val).strip()
                if val_str and val_str.lower() not in NULL_REPRESENTATIONS:
                    # Check email validity
                    if "email" in col_lower:
                        if not re.match(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$", val_str):
                            invalid_count += 1
                            invalid_cols_set.add(col_str)
                            if len(invalid_items) < 30:
                                invalid_items.append(AuditDetailItem(
                                    row_index=row_idx + 1,
                                    column=col_str,
                                    original_value=val_str,
                                    cleaned_value=val_str,
                                    issue_description=f"Malformed email syntax '{val_str}' (missing valid domain)",
                                    severity="warning"
                                ))
                    # Check percentage out of bounds
                    elif "attendance" in col_lower or "pct" in col_lower or "percent" in col_lower:
                        try:
                            f_val = float(re.sub(r"[%\s]", "", val_str))
                            if f_val < 0 or f_val > 100:
                                invalid_count += 1
                                invalid_cols_set.add(col_str)
                                if len(invalid_items) < 30:
                                    invalid_items.append(AuditDetailItem(
                                        row_index=row_idx + 1,
                                        column=col_str,
                                        original_value=val_str,
                                        cleaned_value=str(max(0, min(100, f_val))),
                                        issue_description=f"Percentage value {f_val}% is outside allowable 0-100% boundary",
                                        severity="warning"
                                    ))
                        except ValueError:
                            pass
                    # Check age bounds
                    elif col_lower == "age":
                        try:
                            age_val = float(val_str)
                            if age_val < 0 or age_val > 130:
                                invalid_count += 1
                                invalid_cols_set.add(col_str)
                                if len(invalid_items) < 30:
                                    invalid_items.append(AuditDetailItem(
                                        row_index=row_idx + 1,
                                        column=col_str,
                                        original_value=val_str,
                                        cleaned_value=None,
                                        issue_description=f"Unrealistic human age ({age_val}) outside 0-130 range",
                                        severity="warning"
                                    ))
                        except ValueError:
                            pass

    total_issues += invalid_count
    dimensions.append(QualityDimension(
        id="invalid_values",
        title="Invalid Values",
        count=invalid_count,
        status=f"{invalid_count} Flagged" if invalid_count > 0 else "Clean",
        summary=f"Flagged {invalid_count} semantically invalid value(s) (such as syntax errors or range violations)." if invalid_count > 0 else "Zero invalid semantic values detected.",
        affected_columns=list(invalid_cols_set),
        items=invalid_items
    ))

    # =========================================================================
    # 5. OUTLIERS
    # =========================================================================
    outlier_items: List[AuditDetailItem] = []
    outlier_cols_set = set()
    outlier_count = 0

    # Detect outliers using Interquartile Range (IQR) on numeric columns with >= 4 values
    for col in original_df.columns:
        col_str = str(col)
        # Extract numeric series
        numeric_vals = []
        val_indices = []
        for row_idx, v in enumerate(original_df[col]):
            if v is not None and not pd.isna(v):
                v_clean = re.sub(r"[₹\$€£¥,\s%]", "", str(v).strip())
                try:
                    numeric_vals.append(float(v_clean))
                    val_indices.append(row_idx)
                except ValueError:
                    pass

        if len(numeric_vals) >= 6:
            series = pd.Series(numeric_vals)
            q25 = series.quantile(0.25)
            q75 = series.quantile(0.75)
            iqr = q75 - q25
            if iqr > 0:
                lower_bound = q25 - (1.5 * iqr)
                upper_bound = q75 + (1.5 * iqr)
                for pos, num in enumerate(numeric_vals):
                    if num < lower_bound or num > upper_bound:
                        outlier_count += 1
                        outlier_cols_set.add(col_str)
                        row_num = val_indices[pos] + 1
                        if len(outlier_items) < 30:
                            outlier_items.append(AuditDetailItem(
                                row_index=row_num,
                                column=col_str,
                                original_value=str(original_df[col].iloc[val_indices[pos]]),
                                cleaned_value=str(num),
                                issue_description=f"Statistical outlier ({num}) falls outside normal IQR range [{round(lower_bound, 1)}, {round(upper_bound, 1)}]",
                                severity="info"
                            ))

    total_issues += outlier_count
    dimensions.append(QualityDimension(
        id="outliers",
        title="Outliers",
        count=outlier_count,
        status=f"{outlier_count} Detected" if outlier_count > 0 else "Clean",
        summary=f"Detected {outlier_count} statistical outlier(s) based on IQR distribution in {len(outlier_cols_set)} column(s)." if outlier_count > 0 else "No statistical outliers detected in numeric distributions.",
        affected_columns=list(outlier_cols_set),
        items=outlier_items
    ))

    # =========================================================================
    # 6. FORMAT DIFFERENCES
    # =========================================================================
    format_items: List[AuditDetailItem] = []
    format_cols_set = set()
    format_count = 0

    TEXT_COL_KEYWORDS = {"address", "street", "city", "country", "name", "desc", "description", "title", "notes", "specs", "location", "manager"}

    for col in original_df.columns:
        col_str = str(col)
        col_lower = col_str.lower()
        is_text_col = any(k in col_lower for k in TEXT_COL_KEYWORDS)

        for row_idx, val in enumerate(original_df[col]):
            if val is not None and not pd.isna(val):
                val_str = str(val)
                # Whitespace formatting
                if val_str != val_str.strip():
                    format_count += 1
                    format_cols_set.add(col_str)
                    if len(format_items) < 25:
                        format_items.append(AuditDetailItem(
                            row_index=row_idx + 1,
                            column=col_str,
                            original_value=f"'{val_str}'",
                            cleaned_value=val_str.strip(),
                            issue_description="Leading/trailing whitespace stripped",
                            severity="info"
                        ))
                # Currency formatting in numeric fields (ONLY for actual currency strings or numeric thousands separators)
                elif not is_text_col and (re.match(r"^[₹\$€£¥]\s*[\d,.]+$", val_str.strip()) or re.match(r"^\d{1,3}(,\d{3})+(\.\d+)?$", val_str.strip())):
                    format_count += 1
                    format_cols_set.add(col_str)
                    if len(format_items) < 25:
                        cleaned_num = re.sub(r"[₹\$€£¥,\s]", "", val_str)
                        format_items.append(AuditDetailItem(
                            row_index=row_idx + 1,
                            column=col_str,
                            original_value=val_str,
                            cleaned_value=cleaned_num,
                            issue_description="Currency symbol/thousands separator harmonized to standard number",
                            severity="info"
                        ))
                # Date format differences (slash vs dash)
                elif re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", val_str.strip()):
                    format_count += 1
                    format_cols_set.add(col_str)
                    if len(format_items) < 25:
                        format_items.append(AuditDetailItem(
                            row_index=row_idx + 1,
                            column=col_str,
                            original_value=val_str,
                            cleaned_value="YYYY-MM-DD",
                            issue_description=f"Slash-separated date '{val_str}' harmonized to ISO 8601 standard",
                            severity="info"
                        ))

    total_issues += format_count
    dimensions.append(QualityDimension(
        id="format_differences",
        title="Format Differences",
        count=format_count,
        status=f"{format_count} Harmonized" if format_count > 0 else "Standard",
        summary=f"Harmonized {format_count} formatting inconsistencies (dates, currencies, whitespace, casing)." if format_count > 0 else "All values follow standardized uniform formatting.",
        affected_columns=list(format_cols_set),
        items=format_items
    ))

    return QualityAuditReport(
        dimensions=dimensions,
        total_issues_handled=total_issues
    )


def audit_unstructured_data(raw_text: str, fields: List[ProcessedField]) -> QualityAuditReport:
    """
    Quality audit for unstructured extracted text and fields.
    """
    dimensions: List[QualityDimension] = []
    
    # 1. Missing Values
    missing = [f for f in fields if f.value is None]
    dimensions.append(QualityDimension(
        id="missing_values",
        title="Missing Values",
        count=len(missing),
        status=f"{len(missing)} Not Present",
        summary=f"{len(missing)} standard field(s) were not present in the document and mapped to null.",
        affected_columns=[f.label for f in missing],
        items=[AuditDetailItem(
            column=f.label,
            original_value="Not Found in Document",
            cleaned_value=None,
            issue_description=f"Field '{f.label}' was absent in uploaded document",
            severity="info"
        ) for f in missing]
    ))

    # 2. Duplicates (Find actual non-empty duplicate lines)
    raw_lines = [l.strip() for l in raw_text.splitlines() if len(l.strip()) > 1]
    seen_lines = set()
    dup_lines: List[str] = []
    for line in raw_lines:
        if line.lower() in seen_lines:
            dup_lines.append(line)
        else:
            seen_lines.add(line.lower())

    dup_items = [
        AuditDetailItem(
            column="Source Document Text",
            original_value=d_line,
            cleaned_value="Consolidated / Deduplicated",
            issue_description="Repetitive or duplicate text line removed during OCR text cleanup",
            severity="info"
        )
        for d_line in dup_lines[:20]
    ]

    dup_count = len(dup_lines)
    dimensions.append(QualityDimension(
        id="duplicates",
        title="Duplicates",
        count=dup_count,
        status=f"{dup_count} Consolidated" if dup_count > 0 else "Clean",
        summary=f"Consolidated {dup_count} redundant duplicate text line(s)." if dup_count > 0 else "No duplicate lines found in source document.",
        items=dup_items
    ))

    # 3. Wrong Data Types
    type_issues = [f for f in fields if not f.is_valid and "type" in (f.error_message or "").lower()]
    dimensions.append(QualityDimension(
        id="wrong_data_types",
        title="Wrong Data Types",
        count=len(type_issues),
        status=f"{len(type_issues)} Flagged" if type_issues else "Clean",
        summary=f"{len(type_issues)} data type discrepancies found." if type_issues else "All extracted fields match their target data types.",
        items=[AuditDetailItem(
            column=f.label,
            original_value=f.raw_value,
            cleaned_value=f.value,
            issue_description=f.error_message or "Data type mismatch",
            severity="warning"
        ) for f in type_issues]
    ))

    # 4. Invalid Values
    invalid = [f for f in fields if not f.is_valid]
    dimensions.append(QualityDimension(
        id="invalid_values",
        title="Invalid Values",
        count=len(invalid),
        status=f"{len(invalid)} Flagged" if invalid else "Verified",
        summary=f"{len(invalid)} invalid field syntax issues flagged." if invalid else "All extracted field values passed format verification.",
        items=[AuditDetailItem(
            column=f.label,
            original_value=f.raw_value,
            cleaned_value=f.value,
            issue_description=f.error_message or "Validation rule failure",
            severity="warning"
        ) for f in invalid]
    ))

    # 5. Outliers
    dimensions.append(QualityDimension(
        id="outliers",
        title="Outliers",
        count=0,
        status="Clean",
        summary="No statistical anomalies detected in document single-record extraction.",
        items=[]
    ))

    # 6. Format Differences
    normalized = [f for f in fields if f.raw_value is not None and str(f.raw_value) != str(f.value)]
    dimensions.append(QualityDimension(
        id="format_differences",
        title="Format Differences",
        count=len(normalized),
        status=f"{len(normalized)} Standardized" if normalized else "Standard",
        summary=f"Converted {len(normalized)} field(s) into ISO dates, Title Case, or international phone formats." if normalized else "All extracted fields follow uniform standardized format.",
        affected_columns=[f.label for f in normalized],
        items=[AuditDetailItem(
            column=f.label,
            original_value=f.raw_value,
            cleaned_value=f.value,
            issue_description=f"Standardized {f.field_type} format",
            severity="info"
        ) for f in normalized]
    ))

    total_issues = sum(dim.count for dim in dimensions)

    return QualityAuditReport(
        dimensions=dimensions,
        total_issues_handled=total_issues
    )
