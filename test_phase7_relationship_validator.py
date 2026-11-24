import pytest
from backend.validation.relationship_validator import (
    RelationshipValidator,
    validate_relationships
)

def test_relationship_validator_all_checks():
    stores = [
        {"store_id": "STR_01", "store_name": "Downtown"},
        {"store_id": "STR_02", "store_name": "Uptown"},
        {"store_id": "STR_01", "store_name": "Duplicate Store"} # Duplicate PK!
    ]

    items = [
        {"item_id": "ITM_100", "item_name": "Latte", "store_id": "STR_01"},
        {"item_id": "ITM_200", "item_name": "Croissant", "store_id": "STR_NONEXISTENT"} # Orphan store_id!
    ]

    customers = [
        {"customer_id": "CUST_01", "name": "Alice"}
    ]

    transactions = [
        # Valid transaction
        {"transaction_id": "TXN_001", "store_id": "STR_01", "customer_id": "CUST_01", "item_id": "ITM_100"},
        # Transaction with orphan customer and missing store
        {"transaction_id": "TXN_002", "store_id": None, "customer_id": "CUST_GHOST", "item_id": "ITM_100"},
        # Conflicting store for same transaction
        {"transaction_id": "TXN_001", "store_id": "STR_02", "customer_id": "CUST_01", "item_id": "ITM_100"}
    ]

    report = validate_relationships(
        stores=stores,
        items=items,
        customers=customers,
        transactions=transactions
    )

    summary = report.referential_summary
    assert summary["duplicate_primary_keys"] >= 1
    assert summary["orphan_foreign_keys"] >= 2 # ITM_200 orphan store and TXN_002 orphan customer
    assert summary["missing_foreign_keys"] >= 1 # TXN_002 missing store
    assert summary["conflicting_relationships"] >= 1 # TXN_001 conflicting store
    assert report.integrity_percentage < 100.0
