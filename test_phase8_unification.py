import json
import pytest
from backend.unification.data_unifier import (
    DataUnifier,
    export_unified_to_json,
    export_unified_to_csv,
    export_unified_to_excel
)

def test_data_unification_and_exports():
    unifier = DataUnifier()

    # Source 1: Stores in California
    stores_src1 = [
        {"store_id": "STR_CA_01", "store_name": "San Francisco Branch", "city": "San Francisco"}
    ]
    unifier.add_dataset("store", stores_src1, source_name="california_stores.csv")

    # Source 2: Stores in Texas (with one duplicate of CA store)
    stores_src2 = [
        {"store_id": "STR_TX_01", "store_name": "Austin Branch", "city": "Austin"},
        {"store_id": "STR_CA_01", "store_name": "San Francisco Branch", "city": "San Francisco"} # Duplicate across files
    ]
    unifier.add_dataset("store", stores_src2, source_name="texas_stores.csv")

    # Transactions from POS
    transactions = [
        {"transaction_id": "TXN_1", "store_id": "STR_CA_01", "total_amount": 100.0},
        {"transaction_id": "TXN_2", "store_id": "STR_TX_01", "total_amount": 250.0}
    ]
    unifier.add_dataset("transaction", transactions, source_name="pos_export.json")

    res = unifier.unify()

    # Stores unified and deduplicated (STR_CA_01, STR_TX_01 -> 2 stores)
    assert len(res.entities["store"]) == 2
    assert res.record_counts["store"] == 2

    # Transactions preserved (2 transactions)
    assert len(res.entities["transaction"]) == 2

    # Check provenance
    assert "california_stores.csv" in res.sources_merged
    assert "texas_stores.csv" in res.sources_merged
    assert "_source_name" in res.entities["store"][0]

    # Test Exports
    json_str = export_unified_to_json(res)
    parsed_json = json.loads(json_str)
    assert "store" in parsed_json

    csv_str = export_unified_to_csv(res, "store")
    assert "store_id,store_name,city" in csv_str.lower()
    assert "STR_TX_01" in csv_str

    excel_bytes = export_unified_to_excel(res)
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 1000 # Valid Excel workbook binary
