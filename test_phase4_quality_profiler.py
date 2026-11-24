import pandas as pd
import pytest
from backend.quality.data_quality_profiler import (
    DataQualityProfiler,
    profile_dataset
)

def test_quality_profiler_comprehensive():
    df = pd.DataFrame({
        "customer_id": ["C1", "C2", "C3", "C1"], # C1 is duplicate
        "email": ["valid@test.com", "not_an_email", "another@domain.org", None],
        "phone": ["+1-555-123-4567", "123", "+44-20-7946-0958", "N/A"], # "123" is invalid phone (<7 digits)
        "purchase_date": ["2023-01-15", "invalid-date", "2023-03-20", "2023-04-10"],
        "unit_price": [19.99, -45.00, 150.00, 0.0], # -45.00 is negative price!
        "store_id": ["STR_01", "STR_ORPHAN", "STR_01", "STR_02"]
    })

    foreign_keys = {
        "store_id": {"STR_01", "STR_02"} # STR_ORPHAN should be flagged as orphan FK
    }

    report = profile_dataset(df, entity_type="transaction", foreign_keys=foreign_keys)

    assert report.total_records == 4
    assert report.missing_value_count >= 2 # email None and phone N/A
    assert report.duplicate_count >= 2 or "duplicate_primary_key" in str(report.issues_by_column)
    assert report.quality_percentage < 100.0

    # Verify column specific issues
    email_issues = report.issues_by_column.get("email", [])
    assert any(iss["issue_type"] == "invalid_email_format" for iss in email_issues)

    phone_issues = report.issues_by_column.get("phone", [])
    assert any(iss["issue_type"] == "invalid_phone_format" for iss in phone_issues)

    date_issues = report.issues_by_column.get("purchase_date", [])
    assert any(iss["issue_type"] == "inconsistent_date_format" for iss in date_issues)

    price_issues = report.issues_by_column.get("unit_price", [])
    assert any(iss["issue_type"] == "negative_or_unparseable_price" for iss in price_issues)

    # Check referential integrity
    assert len(report.referential_integrity_issues) == 1
    assert "STR_ORPHAN" in report.referential_integrity_issues[0]["sample_orphans"]

    # Recommended corrections
    assert len(report.recommended_corrections) > 0
