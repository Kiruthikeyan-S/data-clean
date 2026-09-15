"""
Test Suite for Multi-Entity vs Single-Entity Dataset Detection."
"""
import json, sys, pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
from backend.pipeline import process_file_pipeline

def test_multi_collection_json():
    print("\n--- 1. Testing Multi-Collection JSON Ingestion ---")
    multi_json = {
        "stores": [
            {"STORE_ID": "s001", "Store Name": "Downtown Mall Branch", "city": "chennai", "zip": "600001", "active": "yes"},
            {"STORE_ID": "s002", "Store Name": "City Center Outlet", "city": "mumbai", "zip": "400001", "active": "no"}
        ],
        "items": [
            {"product_id": "p101", "item_title": "Nike Running Shoes", "mrp": "$5,999.00", "in_stock": "15"},
            {"product_id": "p102", "item_title": "Adidas Cotton T-Shirt", "mrp": "$2,499.50", "in_stock": "0"}
        ],
        "customers": [
            {"cust_id": "c001", "first_name": "Ravi", "last_name": "Kumar", "mail": "RAVI@GMAIL.COM", "mobile": "9876543210"},
            {"cust_id": "c002", "first_name": "Priya", "last_name": "Sharma", "mail": "priya@yahoo.com", "mobile": "9876543211"}
        ],
        "transactions": [
            {"txn_id": "ord-101", "store_id": "s001", "product_id": "p101", "cust_id": "c001", "order_date": "15/01/2024", "qty": "2", "grand_total": "$11,998.00", "pay_type": "Credit Card"}
        ]
    }
    file_bytes = json.dumps(multi_json).encode('utf-8')
    res = process_file_pipeline("enterprise_data.json", "application/json", file_bytes)
    assert res.status == "completed"
    assert res.entity_info is not None
    assert res.entity_info.is_mixed is True
    assert res.entity_info.split_tables is not None
    assert len(res.entity_info.split_tables) == 4
    table_types = [t.entity_type for t in res.entity_info.split_tables]
    print(f"Detected Split Tables: {table_types}")
    assert "store" in table_types
    assert "item" in table_types
    assert "customer" in table_types
    assert "transaction" in table_types
    for t in res.entity_info.split_tables:
        print(f"  {t.icon} {t.display_name} -> {len(t.records)} records, cols: {t.columns}")
        assert t.schema_mapping_report is not None
        assert len(t.records) > 0
    print("Multi-Collection JSON separated successfully!")

def test_flat_mixed_csv():
    print("\n--- 2. Testing Flat Mixed CSV Table Ingestion ---")
    csv_content = """store_id,store_name,city,product_id,item_name,selling_price,customer_id,full_name,email,transaction_id,purchase_date,quantity,total_amount
S001,Downtown Branch,Chennai,P101,Running Shoes,5999.00,C001,Ravi Kumar,ravi@gmail.com,TXN001,2024-01-15,1,5999.00
S001,Downtown Branch,Chennai,P102,Cotton Shirt,2499.50,C002,Priya Sharma,prgya@yahoo.com,TXN002,2024-01-16,2,4999.00
S002,Outlet Store,Mumbai,P101,Running Shoes,5999.00,C001,Ravi Kumar,ravi@gmail.com,TXN003,2024-01-17,1,5999.00
"""
    file_bytes = csv_content.encode('utf-8')
    res = process_file_pipeline("retail_mixed.csv", "text/csv", file_bytes)
    assert res.status == "completed"
    assert res.entity_info is not None
    assert res.entity_info.is_mixed is True
    assert res.entity_info.split_tables is not None
    assert len(res.entity_info.split_tables) >= 3
    for t in res.entity_info.split_tables:
        print(f"  {t.icon} {t.display_name} -> {len(t.records)} rows (deduped: {t.duplicates_removed})")
    print("Flat Mixed CSV separated successfully!")

def test_single_entity_store():
    print("\n--- 3. Testing Single-Entity Store Dataset ---")
    store_csv = """S__ID,Store Name,city,zipcode,active,launch_date
s001,downtown mall branch,chennai,600001,yes,15/01/2024
s002,city center outlet,mumbai,400001,no,2024.02.20
s003,express mart,bangalore,560001,yes,2023-11-01
"""
    file_bytes = store_csv.encode('utf-8')
    res = process_file_pipeline("stores.csv", "text/csv", file_bytes)
    assert res.status == "completed"
    assert res.entity_info is not None
    assert res.entity_info.is_mixed is False
    assert res.entity_info.entity_type == "store"
    assert res.entity_info.split_tables is None  # Should NOT split
    print(f"Single Entity: {res.entity_info.entity_type}, is:mixed: {res.entity_info.is_mixed}")
    assert "store_id" in res.columns
    assert "store_name" in res.columns
    assert "postal_code" in res.columns
    assert "active" in res.columns
    assert res.structured_data[0]["store_id"] == "S001"
    assert res.structured_data[0]["active"] is True
    print("Single-Entity Store processed directly without splitting!")

def test_single_entity_customer():
    print("\n--- 4. Testing Single-Entity Customer Dataset ---")
    cust_json = [
        {"cust_id": "c001", "first_name": "ravi", "last_name": "kumar", "mail": "RAVI@GMAIL.COM", "mobile": "9876543210", "signup": "2024-01-01"},
        {"cust_id": "c002", "first_name": "priya", "last_name": "sharma", "mail": "priya@yahoo.com", "mobile": "9876543211", "signup": "2024-02-15"}
    ]
    file_bytes = json.dumps(cust_json).encode('utf-8')
    res = process_file_pipeline("customers.json", "application/json", file_bytes)
    assert res.status == "completed"
    assert res.entity_info is not None
    assert res.entity_info.is_mixed is False
    assert res.entity_info.entity_type == "customer"
    assert res.entity_info.split_tables is None  # Should NOT split
    print(f"Single Entity: {res.entity_info.entity_type}, is:mixed: {res.entity_info.is_mixed}")
    assert "customer_id" in res.columns
    assert "full_name" in res.columns
    assert "email" in res.columns
    assert res.structured_data[0]["customer_id"] == "C001"
    assert res.structured_data[0]["full_name"] == "Ravi Kumar"
    print("Single-Entity Customer processed directly without splitting!")

if __name__ == '__main__':
    test_multi_collection_json()
    test_flat_mixed_csv()
    test_single_entity_store()
    test_single_entity_customer()
    print("'\n ALL MULTI-ENTITY AND SINGLE-ENTITY TESTS PASSED 100%!")
