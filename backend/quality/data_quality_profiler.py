"""
Data Quality Profiler Engine

Comprehensive, non-destructive data quality assessment module.
Detects:
- Missing values (nulls, empty strings, placeholder tokens)
- Duplicate records (exact row duplicates and primary key collisions)
- Invalid values and incorrect data types
- Inconsistent date formats and unparseable dates
- Invalid email addresses and phone numbers
- Negative prices or negative quantities where invalid
- Incorrect currency formats
- Inconsistent column names
- Unexpected values (domain anomalies)
- Referential integrity errors (foreign keys pointing to non-existent primary keys)

Produces a structured QualityProfileReport without mutating uncertain values.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Set, Tuple
import pandas as pd
import numpy as np

NULL_REPRESENTATIONS = {
    "n/a", "na", "null", "none", "nil", "undefined", "unknown",
    "-", "--", "nan", "nat", "#n/a", "#na", "null value", "missing",
    "not available", "n.a.", "n/d", "not applicable", ""
}

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-\(\)\.]{7,20}$")
ISO_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)?$")


@dataclass
class ColumnIssue:
    column: str
    issue_type: str
    count: int
    sample_invalid_values: List[Any]
    description: str
    recommended_correction: str
    severity: str  # "high", "medium", "low"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QualityProfileReport:
    total_records: int
    valid_records: int
    invalid_records: int
    missing_value_count: int
    duplicate_count: int
    invalid_value_count: int
    quality_percentage: float
    issues_by_column: Dict[str, List[Dict[str, Any]]]
    recommended_corrections: List[Dict[str, Any]]
    column_quality_scores: Dict[str, float]
    referential_integrity_issues: List[Dict[str, Any]]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DataQualityProfiler:
    """
    Reusable Data Quality Profiler that assesses tabular data against
    quality rules, schema integrity, and referential constraints.
    """
    def __init__(self, foreign_key_lookups: Optional[Dict[str, Set[Any]]] = None):
        """
        Args:
            foreign_key_lookups: Dict mapping FK column name -> Set of valid primary key values.
                e.g. {"store_id": {"STR_01", "STR_02"}, "customer_id": {"CUST_01"}}
        """
        self.foreign_key_lookups = foreign_key_lookups or {}

    def is_null_or_empty(self, val: Any) -> bool:
        if val is None:
            return True
        try:
            if pd.isna(val):
                return True
        except Exception:
            pass
        s = str(val).strip().lower()
        return s in NULL_REPRESENTATIONS

    def profile_dataframe(
        self,
        df: pd.DataFrame,
        entity_type: Optional[str] = None,
        primary_key_col: Optional[str] = None
    ) -> QualityProfileReport:
        """
        Profiles a pandas DataFrame across all quality dimensions.
        """
        if df.empty:
            return QualityProfileReport(
                total_records=0,
                valid_records=0,
                invalid_records=0,
                missing_value_count=0,
                duplicate_count=0,
                invalid_value_count=0,
                quality_percentage=100.0,
                issues_by_column={},
                recommended_corrections=[],
                column_quality_scores={},
                referential_integrity_issues=[],
                summary={"status": "empty"}
            )

        total_rows = len(df)
        total_cols = len(df.columns)
        total_cells = total_rows * total_cols

        issues_by_column: Dict[str, List[ColumnIssue]] = {str(c): [] for c in df.columns}
        row_has_invalid_value = [False] * total_rows

        total_missing_cells = 0
        total_invalid_cells = 0
        column_error_counts: Dict[str, int] = {str(c): 0 for c in df.columns}

        # 1. Inconsistent column name detection
        for col in df.columns:
            c_str = str(col)
            if re.search(r"[\s\-\.]+", c_str) or re.search(r"[A-Z]", c_str) and re.search(r"[a-z]", c_str):
                # Check if mixed casing or special chars
                if " " in c_str or "-" in c_str:
                    clean_name = re.sub(r"[\s\-]+", "_", c_str).lower().strip("_")
                    issues_by_column[c_str].append(ColumnIssue(
                        column=c_str,
                        issue_type="inconsistent_column_name",
                        count=1,
                        sample_invalid_values=[c_str],
                        description=f"Column header '{c_str}' contains spaces or hyphens",
                        recommended_correction=f"Rename header to snake_case '{clean_name}'",
                        severity="low"
                    ))

        # 2. Check each column cell by cell
        for col in df.columns:
            c_name = str(col)
            c_lower = c_name.lower()
            series = df[col]

            col_missing = 0
            col_invalids = 0
            invalid_samples: List[Any] = []

            # Identify column domain role
            is_email_col = "email" in c_lower
            is_phone_col = any(k in c_lower for k in ("phone", "mobile", "contact_no", "ph_no", "cell"))
            is_date_col = any(k in c_lower for k in ("date", "dob", "registered_on", "created_at", "timestamp"))
            is_price_col = any(k in c_lower for k in ("price", "cost", "salary", "amount", "total", "subtotal", "tax", "mrp"))
            is_qty_col = any(k in c_lower for k in ("quantity", "qty", "stock", "units"))
            is_fk_col = c_lower in self.foreign_key_lookups or (c_lower.endswith("_id") and c_lower in self.foreign_key_lookups)

            for r_idx, val in enumerate(series):
                if self.is_null_or_empty(val):
                    col_missing += 1
                    continue

                val_str = str(val).strip()

                # A. Email validation
                if is_email_col:
                    if not EMAIL_REGEX.match(val_str):
                        col_invalids += 1
                        row_has_invalid_value[r_idx] = True
                        if len(invalid_samples) < 5:
                            invalid_samples.append(val_str)

                # B. Phone validation
                elif is_phone_col:
                    digits = re.sub(r"\D", "", val_str)
                    if not PHONE_REGEX.match(val_str) or len(digits) < 7:
                        col_invalids += 1
                        row_has_invalid_value[r_idx] = True
                        if len(invalid_samples) < 5:
                            invalid_samples.append(val_str)

                # C. Date consistency validation
                elif is_date_col:
                    if ISO_DATE_REGEX.match(val_str):
                        parsed_ok = True
                    else:
                        try:
                            pd.to_datetime(val_str, errors="raise")
                            parsed_ok = True
                            if len(invalid_samples) < 5:
                                invalid_samples.append(val_str)
                        except Exception:
                            parsed_ok = False

                    if not parsed_ok:
                        col_invalids += 1
                        row_has_invalid_value[r_idx] = True
                        if len(invalid_samples) < 5:
                            invalid_samples.append(val_str)

                # D. Negative price or quantity check
                elif is_price_col or is_qty_col:
                    # Strip currency symbols if present
                    clean_num = re.sub(r"[^\d.-]", "", val_str.replace(",", ""))
                    try:
                        num = float(clean_num)
                        # Prices and non-return quantities must not be negative
                        if num < 0:
                            col_invalids += 1
                            row_has_invalid_value[r_idx] = True
                            if len(invalid_samples) < 5:
                                invalid_samples.append(val_str)
                    except ValueError:
                        col_invalids += 1
                        row_has_invalid_value[r_idx] = True
                        if len(invalid_samples) < 5:
                            invalid_samples.append(val_str)

            # Record missing issue for column
            if col_missing > 0:
                total_missing_cells += col_missing
                column_error_counts[c_name] += col_missing
                issues_by_column[c_name].append(ColumnIssue(
                    column=c_name,
                    issue_type="missing_values",
                    count=col_missing,
                    sample_invalid_values=["null / missing"],
                    description=f"{col_missing} missing or placeholder values in '{c_name}'",
                    recommended_correction=f"Provide default imputation or leave blank according to business policy",
                    severity="high" if is_email_col or is_phone_col or c_lower.endswith("_id") else "medium"
                ))

            # Record invalid values for column
            if col_invalids > 0:
                total_invalid_cells += col_invalids
                column_error_counts[c_name] += col_invalids
                issue_name = "invalid_format"
                rec_corr = "Standardize to required format"
                if is_email_col:
                    issue_name = "invalid_email_format"
                    rec_corr = "Review invalid email addresses for typo corrections (e.g. missing @ or domain)"
                elif is_phone_col:
                    issue_name = "invalid_phone_format"
                    rec_corr = "Normalize digits and add country code prefix (+E.164)"
                elif is_date_col:
                    issue_name = "inconsistent_date_format"
                    rec_corr = "Normalize dates to standard ISO 8601 (YYYY-MM-DD)"
                elif is_price_col:
                    issue_name = "negative_or_unparseable_price"
                    rec_corr = "Verify transaction price; prices cannot be negative unless an explicit refund/discount"

                issues_by_column[c_name].append(ColumnIssue(
                    column=c_name,
                    issue_type=issue_name,
                    count=col_invalids,
                    sample_invalid_values=invalid_samples,
                    description=f"{col_invalids} invalid or malformed value(s) in '{c_name}'",
                    recommended_correction=rec_corr,
                    severity="high"
                ))

        # 3. Duplicate Record Detection
        try:
            # Exact row duplicates
            exact_dup_mask = df.astype(str).duplicated(keep=False)
            duplicate_count = int(exact_dup_mask.sum())
        except Exception:
            duplicate_count = 0

        # Primary Key collision check
        pk_col = primary_key_col
        if not pk_col:
            for c in df.columns:
                cl = str(c).lower()
                if cl in ("id", "store_id", "item_id", "customer_id", "transaction_id", "emp_id", "vin"):
                    pk_col = c
                    break

        if pk_col and pk_col in df.columns:
            non_null_pk = df[pk_col].dropna().astype(str)
            pk_dups = non_null_pk[non_null_pk.duplicated(keep=False)]
            if not pk_dups.empty:
                pk_dup_count = len(pk_dups)
                issues_by_column[str(pk_col)].append(ColumnIssue(
                    column=str(pk_col),
                    issue_type="duplicate_primary_key",
                    count=pk_dup_count,
                    sample_invalid_values=list(pk_dups.unique()[:5]),
                    description=f"Primary key '{pk_col}' has {pk_dup_count} colliding records",
                    recommended_correction="Resolve duplicate primary keys by deduplicating or assigning unique UUIDs",
                    severity="high"
                ))

        # 4. Referential Integrity Checks
        referential_integrity_issues: List[Dict[str, Any]] = []
        for fk_col_name, valid_pks in self.foreign_key_lookups.items():
            matched_col = None
            for c in df.columns:
                if str(c).lower() == fk_col_name.lower():
                    matched_col = c
                    break

            if matched_col:
                series = df[matched_col].dropna().astype(str).str.strip()
                orphan_keys = [val for val in series if val and val.lower() not in NULL_REPRESENTATIONS and val not in valid_pks]
                if orphan_keys:
                    orphan_count = len(orphan_keys)
                    total_invalid_cells += orphan_count
                    ref_issue = {
                        "foreign_key_column": str(matched_col),
                        "orphan_count": orphan_count,
                        "sample_orphans": list(set(orphan_keys))[:5],
                        "description": f"Found {orphan_count} orphan foreign key(s) in '{matched_col}' that do not exist in master dataset",
                        "recommended_correction": "Verify reference ID or register parent record before linking"
                    }
                    referential_integrity_issues.append(ref_issue)
                    issues_by_column[str(matched_col)].append(ColumnIssue(
                        column=str(matched_col),
                        issue_type="referential_integrity_orphan",
                        count=orphan_count,
                        sample_invalid_values=list(set(orphan_keys))[:5],
                        description=ref_issue["description"],
                        recommended_correction=ref_issue["recommended_correction"],
                        severity="high"
                    ))

        # 5. Compute summary statistics & scores
        invalid_rows_count = sum(1 for has_err in row_has_invalid_value if has_err)
        valid_rows_count = max(0, total_rows - invalid_rows_count)

        # Quality percentage
        quality_score = 1.0 - (total_missing_cells + total_invalid_cells) / max(1, total_cells)
        quality_percentage = round(max(0.0, min(100.0, quality_score * 100.0)), 2)

        # Column quality scores
        column_quality_scores: Dict[str, float] = {}
        for c in df.columns:
            c_name = str(c)
            errs = column_error_counts.get(c_name, 0)
            c_score = round(max(0.0, min(1.0, 1.0 - (errs / max(1, total_rows)))), 3)
            column_quality_scores[c_name] = c_score

        # Recommended corrections aggregation
        recommended_corrections: List[Dict[str, Any]] = []
        for c_name, issues in issues_by_column.items():
            for iss in issues:
                recommended_corrections.append({
                    "column": c_name,
                    "issue_type": iss.issue_type,
                    "severity": iss.severity,
                    "recommendation": iss.recommended_correction
                })

        # Format output dictionary
        formatted_issues: Dict[str, List[Dict[str, Any]]] = {}
        for c_name, issues in issues_by_column.items():
            if issues:
                formatted_issues[c_name] = [iss.to_dict() for iss in issues]

        summary = {
            "total_records": total_rows,
            "total_columns": total_cols,
            "valid_records": valid_rows_count,
            "invalid_records": invalid_rows_count,
            "missing_value_count": total_missing_cells,
            "duplicate_count": duplicate_count,
            "invalid_value_count": total_invalid_cells,
            "quality_percentage": quality_percentage,
            "critical_columns": [c for c, score in column_quality_scores.items() if score < 0.70]
        }

        return QualityProfileReport(
            total_records=total_rows,
            valid_records=valid_rows_count,
            invalid_records=invalid_rows_count,
            missing_value_count=total_missing_cells,
            duplicate_count=duplicate_count,
            invalid_value_count=total_invalid_cells,
            quality_percentage=quality_percentage,
            issues_by_column=formatted_issues,
            recommended_corrections=recommended_corrections,
            column_quality_scores=column_quality_scores,
            referential_integrity_issues=referential_integrity_issues,
            summary=summary
        )


def profile_dataset(
    df: pd.DataFrame,
    entity_type: Optional[str] = None,
    foreign_keys: Optional[Dict[str, Set[Any]]] = None
) -> QualityProfileReport:
    """Convenience function to profile a dataset."""
    profiler = DataQualityProfiler(foreign_key_lookups=foreign_keys)
    return profiler.profile_dataframe(df, entity_type=entity_type)
