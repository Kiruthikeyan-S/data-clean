"""
Test Suite for Schema Mapping, Alias Merging, and Canonical Value Standardization.
"""
import io
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

from backend.models.entity_schemas import get_canonical_fields, EntityType
from backend.normalization.schema_mapper import map_dataframe_to_canonical_schema
from backend.normalization.value_standardizer import standardize_canonical_values
from backend.pipeline import process_file_pipeline

def test_store_schema_mapping_and_standardization():
    raw_data = {
        "STORE_ID": ["s001", "s002"],
        "Store Name": ["downtown mall branch", "CITY CENTER OUTLET"],
        "city": ["chennai", "mumbai"],
        "zipcode": ["600001", "400001"],
        "active": ["yes", "no"],
        "launch_date": ["15/01/2024", "2024.02.20"]
    }
    df = pd.DataFrame(raw_data)
    
    # 1. Map to canonical schema
    mapped_df, mapping, map_highlights = map_dataframe_to_canonical_schema(df, "store")
    print("\n--- Store Schema Mapping ---")
    print(f"Original Columns: {list(df.columns)}")
    print(f"Mapped Columns:   {list(mapped_df.columns)}")
    print(f"Mapping Dict:     {mapping}")
    
    assert "store_id" in mapped_df.columns
    assert "store_name" in mapped_df.columns
    assert "postal_code" in mapped_df.columns
    assert "active" in mapped_df.columns
    assert "opened_on" in mapped_df.columns
    assert "city" in mapped_df.columns
    
    # 2. Value standardization
    std_df, mod_counts, val_highlights = standardize_canonical_values(mapped_df, "store")
    print("\n--- Store Standardized Values ---")
    print(std_df)
    
    assert std_df["store_id"].iloc[0] == "S001"
    assert std_df["store_name"].iloc[0] == "Downtown Mall Branch"
    assert std_df["city"].iloc[0] == "Chennai"
    assert std_df["city"].iloc[1] == "Mumbai"
    assert std_df["active"].iloc[0] == True
    assert std_df["active"].iloc[1] == False
    assert std_df["opened_on"].iloc[0] == "2024-01-15"
    assert std_df["opened_on"].iloc[1] == "2024-02-20"


def test_alias_merging():
    # Input has both 'zip' and 'postal_code' containing complementary data
    raw_data = {
        "store_id": ["STR-01", "STR-02"],
        "name": ["Alpha Store", "Beta Store"],
        "zip": ["600001", None],
        "postal_code": [None, "400001"]
    }
    df = pd.DataFrame(raw_data)
    mapped_df, mapping, highlights = map_dataframe_to_canonical_schema(df, "store")
    print("\n--- Alias Merging Test ---")
    print(f"Mapped Columns: {list(mapped_df.columns)}")
    print(f"Merged postal_code values: {mapped_df['postal_code'].tolist()}")
    
    # Should merge zip and postal_code into ONE 'postal_code' column with both values populated
    assert "postal_code" in mapped_df.columns
    assert "zip" not in mapped_df.columns
    assert mapped_df["postal_code"].tolist() == ["600001", "400001"]


def test_item_schema_mapping_and_standardization():
    raw_data = {
        "product_code": ["p101", "p102"],
        "item_title": ["nike running shoes", "adidas cotton t-shirt"],
        "mrp": ["$5,999.00", "₹2,499.50"],
        "cost": ["$3,500.00", "₹1,200.00"],
        "in_stock": ["15", "0"],
        "is_available": ["yes", "no"]
    }
    df = pd.DataFrame(raw_data)
    mapped_df, mapping, _ = map_dataframe_to_canonical_schema(df, "item")
    std_df, _, _ = standardize_canonical_values(mapped_df, "item")
    
    print("\n--- Item Standardized Values ---")
    print(std_df)
    
    assert "item_id" in std_df.columns
    assert "item_name" in std_df.columns
    assert "selling_price" in std_df.columns
    assert "cost_price" in std_df.columns
    assert "stock_quantity" in std_df.columns
    assert "available" in std_df.columns
    
    assert std_df["item_id"].iloc[0] == "P101"
    assert std_df["item_name"].iloc[0] == "Nike Running Shoes"
    assert std_df["selling_price"].iloc[0] == 5999.0
    assert std_df["selling_price"].iloc[1] == 2499.5
    assert std_df["cost_price"].iloc[0] == 3500.0
    assert std_df["cost_price"].iloc[1] == 1200.0
    assert std_df["stock_quantity"].iloc[0] == 15
    assert std_df["available"].iloc[0] == True
    assert std_df["available"].iloc[1] == False


def test_customer_schema_mapping_and_standardization():
    raw_data = {
        "cust_id": ["c001", "c002"],
        "first_name": ["ravi", "priya"],
        "last_name": ["kumar", "sharma"],
        "mail": ["RAVI@GMAIL.COM", "priya@yahoo.com"],
        "mobile": ["9876543210", "9876543211"],
        "signup_date": ["25/12/1990", "10/05/1995"]
    }
    df = pd.DataFrame(raw_data)
    mapped_df, _, _ = map_dataframe_to_canonical_schema(df, "customer")
    std_df, _, _ = standardize_canonical_values(mapped_df, "customer")
    
    print("\n--- Customer Standardized Values ---")
    print(std_df)
    
    assert "customer_id" in std_df.columns
    assert "full_name" in std_df.columns
    assert "email" in std_df.columns
    assert "phone" in std_df.columns
    assert "registered_on" in std_df.columns
    
    assert std_df["full_name"].iloc[0] == "Ravi Kumar"
    assert std_df["full_name"].iloc[1] == "Priya Sharma"
    assert std_df["email"].iloc[0] == "ravi@gmail.com"
    assert std_df["registered_on"].iloc[0] == "1990-12-25"
    assert std_df["registered_on"].iloc[1] == "1995-05-10"


def test_transaction_schema_mapping_and_standardization():
    raw_data = {
        "txn_id": ["ord-101", "ord-102"],
        "order_date": ["15-01-2024", "16-01-2024"],
        "qty": ["2", "1"],
        "grand_total": ["$11,998.00", "₹2,499.00"],
        "pay_type": ["credit card", "upi"]
    }
    df = pd.DataFrame(raw_data)
    mapped_df, _, _ = map_dataframe_to_canonical_schema(df, "transaction")
    std_df, _, _ = standardize_canonical_values(mapped_df, "transaction")
    
    print("\n--- Transaction Standardized Values ---")
    print(std_df)
    
    assert "transaction_id" in std_df.columns
    assert "purchase_date" in std_df.columns
    assert "quantity" in std_df.columns
    assert "total_amount" in std_df.columns
    assert "payment_method" in std_df.columns
    
    assert std_df["transaction_id"].iloc[0] == "ORD-101"
    assert std_df["purchase_date"].iloc[0] == "2024-01-15"
    assert std_df["quantity"].iloc[0] == 2
    assert std_df["total_amount"].iloc[0] == 11998.0
    assert std_df["payment_method"].iloc[0] == "Credit Card"
    assert std_df["payment_method"].iloc[1] == "Upi"


def test_pipeline_with_schema_mapping():
    csv_bytes = b"""STORE_ID,Store Name,city,zipcode,active,launch_date
s001,downtown mall branch,chennai,600001,yes,15/01/2024
s002,city center outlet,mumbai,400001,no,2024.02.20
"""
    response = process_file_pipeline("store_raw.csv", "text/csv", csv_bytes)
    assert response.status == "completed"
    assert response.entity_info.entity_type == "store"
    
    # Check that output columns are canonical
    expected_canonical_cols = {"store_id", "store_name", "city", "postal_code", "active", "opened_on"}
    output_cols = set(response.columns)
    print(f"\nPipeline Output Columns: {response.columns}")
    assert expected_canonical_cols.issubset(output_cols)
    
    records = response.structured_data
    assert records[0]["store_id"] == "S001"
    assert records[0]["store_name"] == "Downtown Mall Branch"
    assert records[0]["city"] == "Chennai"
    assert records[0]["active"] is True
    assert records[0]["opened_on"] == "2024-01-15"
    print("\n--- Pipeline Canonical Table Output ---")
    print(records)


if __name__ == "__main__":
    print("Running Schema Mapping & Value Standardization Tests...")
    test_store_schema_mapping_and_standardization()
    test_alias_merging()
    test_item_schema_mapping_and_standardization()
    test_customer_schema_mapping_and_standardization()
    test_transaction_schema_mapping_and_standardization()
    test_pipeline_with_schema_mapping()
    print("\nALL SCHEMA MAPPING & VALUE STANDARDIZATION TESTS PASSED 100%!")
