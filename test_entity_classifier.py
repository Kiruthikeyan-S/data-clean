"""
Test Suite for Business Entity Identification & Splitting
Tests single-entity files (Store, Item, Customer, Transaction),
mixed datasets, deduplication, and non-retail/unknown datasets.
"""
import io
import sys
import pandas as pd

# Fix Windows console UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

from backend.pipeline import process_file_pipeline
from backend.extraction.entity_classifier import classify_columns
from backend.cleaning.entity_splitter import split_mixed_dataframe

def test_single_store():
    csv_data = """store_id,store_name,city,state,store_manager
STR-101,Downtown Branch,Chennai,Tamil Nadu,Ramesh
STR-102,Mall Road Branch,Mumbai,Maharashtra,Suresh
"""
    df = pd.read_csv(io.StringIO(csv_data))
    res = classify_columns(list(df.columns), df)
    print(f"Store Test -> file_type: {res.file_type}, confidence: {res.confidence:.0%}")
    assert res.file_type == "store"
    assert res.confidence >= 0.70
    assert not res.is_mixed

def test_single_item():
    csv_data = """product_id,product_name,sku,category,unit_price,stock
P101,Running Shoes,SKU-RS-10,Footwear,2999.00,50
P102,Cotton T-Shirt,SKU-TS-20,Apparel,799.00,100
"""
    df = pd.read_csv(io.StringIO(csv_data))
    res = classify_columns(list(df.columns), df)
    print(f"Item Test -> file_type: {res.file_type}, confidence: {res.confidence:.0%}")
    assert res.file_type == "item"
    assert res.confidence >= 0.70
    assert not res.is_mixed

def test_single_customer():
    csv_data = """customer_id,customer_name,customer_email,phone,city
C001,Ravi Kumar,ravi@gmail.com,+919876543210,Chennai
C002,Priya Sharma,priya@yahoo.com,+919876543211,Mumbai
"""
    df = pd.read_csv(io.StringIO(csv_data))
    res = classify_columns(list(df.columns), df)
    print(f"Customer Test -> file_type: {res.file_type}, confidence: {res.confidence:.0%}")
    assert res.file_type == "customer"
    assert res.confidence >= 0.70
    assert not res.is_mixed

def test_single_transaction():
    csv_data = """order_id,purchase_date,quantity,total_amount,payment_method
ORD-901,2024-01-15,2,5998.00,Credit Card
ORD-902,2024-01-16,1,2499.00,UPI
"""
    df = pd.read_csv(io.StringIO(csv_data))
    res = classify_columns(list(df.columns), df)
    print(f"Transaction Test -> file_type: {res.file_type}, confidence: {res.confidence:.0%}")
    assert res.file_type == "transaction"
    assert res.confidence >= 0.70
    assert not res.is_mixed

def test_mixed_file_and_splitter():
    csv_data = """store_id,store_name,city,product_id,product_name,unit_price,customer_id,customer_name,customer_email,purchase_date,quantity,total_amount
S001,Downtown Mall,Chennai,P101,Nike Shoes,5999.00,C001,Ravi Kumar,ravi@gmail.com,2024-01-15,2,11998.00
S001,Downtown Mall,Chennai,P102,Adidas Shirt,2499.00,C002,Priya Sharma,priya@yahoo.com,2024-01-15,1,2499.00
S002,City Center,Mumbai,P101,Nike Shoes,5999.00,C001,Ravi Kumar,ravi@gmail.com,2024-01-16,1,5999.00
S002,City Center,Mumbai,P103,Puma Cap,899.00,C003,Amit Patel,amit@hotmail.com,2024-01-17,3,2697.00
"""
    df = pd.read_csv(io.StringIO(csv_data))
    res = classify_columns(list(df.columns), df)
    print(f"Mixed Test -> file_type: {res.file_type}, is_mixed: {res.is_mixed}, details: {res.details}")
    assert res.file_type == "mixed"
    assert res.is_mixed

    tables = split_mixed_dataframe(df, res)
    print(f"Split produced {len(tables)} tables:")
    for t in tables:
        print(f"  {t.icon} {t.display_name} -> {t.total_rows} rows before, {t.deduplicated_rows} after dedup ({t.duplicates_removed} duplicates removed)")

    # Verify per-entity tables
    entity_types = {t.entity_type for t in tables}
    assert "store" in entity_types
    assert "item" in entity_types
    assert "customer" in entity_types
    assert "transaction" in entity_types

    store_table = next(t for t in tables if t.entity_type == "store")
    assert store_table.deduplicated_rows == 2  # 4 rows deduped to 2 unique stores

    item_table = next(t for t in tables if t.entity_type == "item")
    assert item_table.deduplicated_rows == 3  # 4 rows deduped to 3 unique items

    cust_table = next(t for t in tables if t.entity_type == "customer")
    assert cust_table.deduplicated_rows == 3  # 4 rows deduped to 3 unique customers

    txn_table = next(t for t in tables if t.entity_type == "transaction")
    assert txn_table.deduplicated_rows == 4  # All 4 transactions preserved

def test_pipeline_end_to_end():
    csv_bytes = b"""store_id,store_name,city,product_id,product_name,unit_price,customer_id,customer_name,customer_email,purchase_date,quantity,total_amount
S001,Downtown Mall,Chennai,P101,Nike Shoes,5999.00,C001,Ravi Kumar,ravi@gmail.com,2024-01-15,2,11998.00
S001,Downtown Mall,Chennai,P102,Adidas Shirt,2499.00,C002,Priya Sharma,priya@yahoo.com,2024-01-15,1,2499.00
S002,City Center,Mumbai,P101,Nike Shoes,5999.00,C001,Ravi Kumar,ravi@gmail.com,2024-01-16,1,5999.00
"""
    response = process_file_pipeline("retail_sales.csv", "text/csv", csv_bytes)
    assert response.status == "completed"
    assert response.entity_info is not None
    assert response.entity_info.is_mixed
    assert response.entity_info.split_tables is not None
    assert len(response.entity_info.split_tables) >= 3
    print("\nEnd-to-End Pipeline Success!")
    print(f"File: {response.filename}, Classification: {response.entity_info.entity_type}")
    for t in response.entity_info.split_tables:
        print(f"  {t.icon} {t.display_name}: {t.deduplicated_rows} records ({t.columns})")

if __name__ == "__main__":
    print("Running Entity Classifier & Splitter Tests...")
    test_single_store()
    test_single_item()
    test_single_customer()
    test_single_transaction()
    test_mixed_file_and_splitter()
    test_pipeline_end_to_end()
    print("\n ALL TESTS PASSED SUCCESSFULLY!")
