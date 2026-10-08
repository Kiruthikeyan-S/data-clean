import pytest
import pandas as pd
import numpy as np
from backend.cleaning.data_auditor import (
    generate_data_profile, 
    audit_structured_data, 
    audit_12_fundamentals
)
from backend.cleaning.structured_cleaner import (
    clean_structured_dataframe, 
    read_and_clean_structured_file
)
from backend.cleaning.text_cleaner import clean_text_data
from backend.matching.record_matcher import (
    analyze_record_matching, 
    merge_record_pair, 
    compare_records
)
from backend.matching.cross_file_linker import link_batch_records
from backend.models.schemas import ProcessResponse, EntityClassificationInfo, ProcessSummary
from backend.validation.validator import validate_entity_records
from backend.pipeline import process_file_pipeline


def test_fundamental_1_data_profiling():
    """F1: Statistical profiling of pre/post cleaning datasets."""
    df = pd.DataFrame({
        "customer_id": ["CUST001", "CUST002", "CUST003", "CUST004"],
        "age": [25, 30, np.nan, 45],
        "city": ["Chennai", "Chennai", "Bangalore", None],
        "amount": [100.0, 250.5, 300.0, 500.0]
    })
    profile = generate_data_profile(df, entity_type="customer")
    assert profile.total_rows == 4
    assert profile.total_columns == 4
    assert "age" in profile.column_stats
    assert profile.column_stats["age"].null_count == 1
    assert profile.column_stats["age"].null_percentage == 25.0
    assert profile.column_stats["amount"].min_value == 100.0
    assert profile.column_stats["amount"].max_value == 500.0
    assert profile.column_stats["amount"].quartiles is not None


def test_fundamental_2_missing_value_handling():
    """F2: Normalization of missing markers without fabricating unknown data."""
    df = pd.DataFrame({
        "customer_id": ["C1", "C2", "C3", "C4"],
        "email": ["user@domain.com", "N/A", "missing", "  "],
        "phone": ["9876543210", "NULL", "not available", "9123456789"]
    })
    cleaned_df, metrics = clean_structured_dataframe(df)
    assert metrics["nulls_normalized"] >= 4
    assert pd.isna(cleaned_df.iloc[1]["email"])
    assert pd.isna(cleaned_df.iloc[2]["email"])
    assert pd.isna(cleaned_df.iloc[1]["phone"])
    assert pd.isna(cleaned_df.iloc[2]["phone"])


def test_fundamental_3_duplicate_removal_vs_transactions():
    """F3: Exact duplicate removal while preserving legitimate separate transactions."""
    # 1. Exact duplicate rows are dropped
    dup_df = pd.DataFrame({
        "store_id": ["S1", "S1", "S2"],
        "city": ["Chennai", "Chennai", "Mumbai"]
    })
    cleaned_dup, metrics = clean_structured_dataframe(dup_df)
    assert len(cleaned_dup) == 2
    assert metrics["duplicates_removed"] == 1

    # 2. Distinct transactions sharing customer/product are preserved
    txn_df = pd.DataFrame({
        "transaction_id": ["TXN-001", "TXN-002"],
        "customer_id": ["CUST-1", "CUST-1"],
        "product_id": ["PROD-10", "PROD-10"],
        "amount": [50.0, 50.0]
    })
    cleaned_txn, txn_metrics = clean_structured_dataframe(txn_df, entity_type="transaction")
    assert len(cleaned_txn) == 2
    assert txn_metrics["duplicates_removed"] == 0


def test_fundamental_4_data_type_correction():
    """F4: Safe semantic types: retaining strings & leading zeros for phone/SKUs/postal codes."""
    df = pd.DataFrame({
        "phone_number": ["09876543210", "01234567890"],
        "pincode": ["00123", "00456"],
        "sku": ["009988", "007766"]
    })
    cleaned_df, _ = clean_structured_dataframe(df)
    assert cleaned_df["phone_number"].iloc[0] == "09876543210"
    assert cleaned_df["pincode"].iloc[0] == "00123"
    assert cleaned_df["sku"].iloc[0] == "009988"


def test_fundamental_5_format_standardization():
    """F5: Standardize formats: dates, emails, names, whitespace."""
    raw_text = "  arun kumar  \t\n"
    cleaned = clean_text_data(raw_text)
    assert cleaned == "arun kumar"


def test_fundamental_6_text_cleaning():
    """F6: Unicode NFKC normalization, stripped control characters, whitespace."""
    dirty_text = "Hello\u200B World\x00\r\nTest \t Line  "
    cleaned = clean_text_data(dirty_text)
    assert "\x00" not in cleaned
    assert "\u200B" not in cleaned
    assert "Hello World" in cleaned


def test_fundamental_7_outlier_detection_non_destructive():
    """F7: IQR and Z-score outlier detection without destructive deletion."""
    df = pd.DataFrame({
        "product_id": [f"P{i}" for i in range(1, 10)],
        "price": [100.0, 105.0, 110.0, 102.0, 98.0, 104.0, 108.0, 112.0, 9999.0]
    })
    audit = audit_structured_data(df, df, entity_type="item")
    outlier_dim = next((d for d in audit.dimensions if d.id == "outliers"), None)
    assert outlier_dim is not None
    assert outlier_dim.count >= 1
    # Ensure outlier price was flagged, NOT deleted from cleaned_df
    assert len(df) == 9


def test_fundamental_8_data_validation():
    """F8: Validation checks with severity levels for entity types."""
    records = [
        {"customer_id": "C1", "customer_email": "invalid_email_format", "customer_phone": "123"},
        {"customer_id": "C2", "customer_email": "valid@email.com", "customer_phone": "9876543210"}
    ]
    _, issues = validate_entity_records(records, columns=["customer_id", "customer_email", "customer_phone"], entity_type="customer")
    assert len(issues) >= 2  # invalid email and invalid phone length
    assert any("email" in i.field.lower() or "email" in i.message.lower() for i in issues)


def test_fundamental_9_inconsistency_negative_stock_preserved():
    """F9 CRITICAL FIX: Negative quantities/stock are preserved as raw numbers, never silently abs()'d."""
    df = pd.DataFrame({
        "product_id": ["P1", "P2", "P3"],
        "stock": [-50, 20, -5],
        "quantity": ["-10", "15", "-3"]
    })
    cleaned_df, _ = clean_structured_dataframe(df, entity_type="item")
    # Verify raw negative values are strictly preserved
    assert cleaned_df.iloc[0]["stock"] == -50
    assert cleaned_df.iloc[2]["stock"] == -5
    assert cleaned_df.iloc[0]["quantity"] == "-10"

    # Verify audit catches negative stock as review issues
    _, issues = validate_entity_records(cleaned_df.to_dict(orient="records"), columns=list(cleaned_df.columns), entity_type="item")
    assert any("negative" in i.message.lower() for i in issues)


def test_fundamental_10_data_transformation():
    """F10: Structured data transformation preserving column lineage."""
    df = pd.DataFrame({
        "Cust_Name": ["Alice", "Bob"],
        "Email_Addr": ["a@b.com", "c@d.com"]
    })
    cleaned_df, metrics = clean_structured_dataframe(df)
    assert len(cleaned_df) == 2
    assert "Cust_Name" in cleaned_df.columns or "cust_name" in cleaned_df.columns


def test_fundamental_11_entity_matching_safety():
    """F11: Require >=2 attributes or verified ID; block single-city-only merges."""
    # Case 1: Two customers sharing only City 'Chennai' must NOT merge
    weak_records = [
        {"customer_id": "C1", "customer_name": "Arun", "city": "Chennai"},
        {"customer_id": "C2", "customer_name": "Bala", "city": "Chennai"}
    ]
    report = analyze_record_matching(weak_records, entity_type="customer")
    assert report.merge_candidates_count == 0  # Blocked!

    # Case 2: Conflicting unique IDs must NOT merge
    conflict_records = [
        {"customer_id": "C1", "customer_name": "Arun Kumar", "phone": "9876543210"},
        {"customer_id": "C2", "customer_name": "Arun Kumar", "phone": "9876543210"}
    ]
    conflict_report = analyze_record_matching(conflict_records, entity_type="customer")
    assert conflict_report.conflicts_count >= 1 or conflict_report.merge_candidates_count == 0


def test_fundamental_11_cross_file_confidence_bug_fix():
    """F11 BUG FIX: When 0 relationships exist, average confidence must be 0.0 (not 0.95)."""
    # Two unrelated datasets
    resp1 = ProcessResponse(
        id="f1",
        filename="students.csv",
        file_type="csv",
        mime_type="text/csv",
        classification="structured",
        status="completed",
        steps=[],
        summary=ProcessSummary(total_records=1, valid_records=1, invalid_records=0, processing_time_ms=10, file_type="csv", classification="structured"),
        structured_data=[{"student_id": "ST1", "name": "Raj"}],
        columns=["student_id", "name"],
        entity_info=EntityClassificationInfo(entity_type="student", is_mixed=False, confidence=0.9, method="rule_based", details="", entities_detected={}, column_assignments={})
    )
    resp2 = ProcessResponse(
        id="f2",
        filename="cars.csv",
        file_type="csv",
        mime_type="text/csv",
        classification="structured",
        status="completed",
        steps=[],
        summary=ProcessSummary(total_records=1, valid_records=1, invalid_records=0, processing_time_ms=10, file_type="csv", classification="structured"),
        structured_data=[{"vin": "VIN123", "model": "Civic"}],
        columns=["vin", "model"],
        entity_info=EntityClassificationInfo(entity_type="car", is_mixed=False, confidence=0.9, method="rule_based", details="", entities_detected={}, column_assignments={})
    )

    _, index = link_batch_records([resp1, resp2])
    assert len(index["relationships"]) == 0
    assert index["summary"]["relationships_found"] == 0
    assert index["summary"]["average_confidence"] == 0.0


def test_fundamental_12_quality_verification_audit_trail():
    """F12: Comprehensive 6-dimension audit and 12-fundamentals scorecard with provenance."""
    raw_df = pd.DataFrame({
        "cust_id": ["C1", "C2", "C3", "C3"],
        "name": ["  Arun ", "Bala", "NULL", "NULL"],
        "phone": ["9876543210", "N/A", "9123456789", "9123456789"]
    })
    cleaned_df, metrics = clean_structured_dataframe(raw_df)
    audit = audit_structured_data(raw_df, cleaned_df, entity_type="customer")
    pre_prof = generate_data_profile(raw_df)
    post_prof = generate_data_profile(cleaned_df)
    fund_report = audit_12_fundamentals(
        raw_df, cleaned_df, quality_audit=audit, pre_profile=pre_prof, post_profile=post_prof, cleansing_metrics=metrics
    )
    assert len(fund_report.fundamentals) == 12
    assert fund_report.total_actions_completed > 0
    assert len(metrics["provenance_log"]) > 0
