import pandas as pd
import pytest
from backend.cleaning.entity_splitter import (
    separate_entities,
    split_mixed_dataframe,
    deduplicate_entity
)
from backend.extraction.entity_classifier import classify_columns

def test_mixed_retail_separation_with_relationships():
    # Mixed retail dataset containing Store, Customer, Item, and Transaction
    df = pd.DataFrame({
        "store_id": ["STR_01", "STR_01", "STR_02"],
        "store_name": ["Downtown Branch", "Downtown Branch", "Uptown Branch"],
        "store_city": ["Miami", "Miami", "Denver"],
        "customer_id": ["CUST_101", "CUST_102", "CUST_101"],
        "customer_name": ["Alice Smith", "Bob Jones", "Alice Smith"],
        "customer_email": ["alice@test.com", "bob@test.com", "alice@test.com"],
        "product_id": ["PRD_501", "PRD_502", "PRD_501"],
        "product_name": ["Wireless Headphones", "Mechanical Keyboard", "Wireless Headphones"],
        "unit_price": [99.99, 149.99, 99.99],
        "transaction_id": ["TXN_001", "TXN_002", "TXN_003"],
        "order_date": ["2023-01-10", "2023-01-11", "2023-01-12"],
        "quantity": [1, 2, 1],
        "total_amount": [99.99, 299.98, 99.99]
    })

    tables = separate_entities(df)
    
    # Must separate into store, customer, item, transaction
    assert "store" in tables
    assert "customer" in tables
    assert "item" in tables
    assert "transaction" in tables

    # Stores deduplicated (STR_01, STR_02 -> 2 rows)
    assert len(tables["store"].records) == 2
    # Customers deduplicated (CUST_101, CUST_102 -> 2 rows)
    assert len(tables["customer"].records) == 2
    # Items deduplicated (PRD_501, PRD_502 -> 2 rows)
    assert len(tables["item"].records) == 2
    # Transactions preserved (3 rows)
    assert len(tables["transaction"].records) == 3

    # Check relationship keys preserved in transaction
    txn_cols = tables["transaction"].columns
    assert any("store_id" in c for c in txn_cols)
    assert any("customer_id" in c for c in txn_cols)
    assert any("item_id" in c or "product_id" in c for c in txn_cols)
