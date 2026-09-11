import sys
import io
import json
import pandas as pd
from backend.pipeline import process_file_pipeline
from backend.analytics.retail_intelligence import merge_relational_datasets, generate_retail_intelligence

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_retail_pipeline():
    print("=== 1. Testing Retail Intelligence on Single Transactions Dataset ===")
    retail_csv = """order_id,customer_id,product_name,category,quantity,unit_price,total_amount,order_date
ORD-101,CUST-001,MacBook Pro,Electronics,1,1999.99,1999.99,2026-08-01
ORD-101,CUST-001,Wireless Mouse,Accessories,2,29.99,59.98,2026-08-01
ORD-102,CUST-002,Dell XPS 15,Electronics,1,1499.00,1499.00,2026-08-05
ORD-103,CUST-001,USB-C Hub,Accessories,1,49.99,49.99,2026-08-10
ORD-104,CUST-003,Mechanical Keyboard,Accessories,1,119.99,119.99,2026-08-15
ORD-105,CUST-002,Wireless Mouse,Accessories,1,29.99,29.99,2026-08-20
ORD-106,CUST-004,MacBook Pro,Electronics,1,1999.99,1999.99,2026-08-22
ORD-107,CUST-005,Monitor 4K,Electronics,1,399.99,399.99,2026-08-25
"""
    res = process_file_pipeline("transactions.csv", "text/csv", retail_csv.encode("utf-8"))
    assert res.classification == "structured"
    assert res.retail_intelligence is not None
    intel = res.retail_intelligence
    
    print(f"Revenue: ${intel.kpis.total_revenue:,.2f}")
    print(f"Units Sold: {intel.kpis.total_units_sold}")
    print(f"Orders: {intel.kpis.total_transactions}")
    print(f"Avg Order Value: ${intel.kpis.avg_order_value:.2f}")
    print(f"Top Seller: {intel.product_analytics.top_selling[0].product_name} (${intel.product_analytics.top_selling[0].revenue:.2f})")
    print(f"RFM Segments: {[s.segment_name for s in intel.customer_intelligence.segments_summary]}")
    print(f"Market Basket Pairs: {len(intel.basket_analysis.pairs)}")
    print(f"Demand Forecasts Count: {len(intel.demand_forecasting.forecasts)}")

    print("\n=== 2. Testing Multi-Table Relational Merge (Store + Item + Customer + Orders) ===")
    store_df = pd.DataFrame([
        {"store_id": "STR-01", "store_name": "Downtown Megastore", "city": "New York", "manager_name": "Alice"}
    ])
    item_df = pd.DataFrame([
        {"item_id": "ITM-01", "product_name": "MacBook Pro", "category": "Electronics", "unit_price": 1999.99},
        {"item_id": "ITM-02", "product_name": "Wireless Mouse", "category": "Accessories", "unit_price": 29.99}
    ])
    cust_df = pd.DataFrame([
        {"customer_id": "CUST-01", "customer_name": "Bruce Wayne", "email": "bruce@wayne.com", "loyalty_tier": "VIP"}
    ])
    order_df = pd.DataFrame([
        {"order_id": "ORD-501", "store_id": "STR-01", "customer_id": "CUST-01", "item_id": "ITM-01", "quantity": 1, "total_amount": 1999.99, "order_date": "2026-08-01"},
        {"order_id": "ORD-501", "store_id": "STR-01", "customer_id": "CUST-01", "item_id": "ITM-02", "quantity": 2, "total_amount": 59.98, "order_date": "2026-08-01"}
    ])

    batch_datasets = [
        {"filename": "stores.csv", "columns": list(store_df.columns), "structured_data": store_df.to_dict(orient="records")},
        {"filename": "items.csv", "columns": list(item_df.columns), "structured_data": item_df.to_dict(orient="records")},
        {"filename": "customers.csv", "columns": list(cust_df.columns), "structured_data": cust_df.to_dict(orient="records")},
        {"filename": "orders.csv", "columns": list(order_df.columns), "structured_data": order_df.to_dict(orient="records")}
    ]

    merged = merge_relational_datasets(batch_datasets)
    assert merged is not None
    print(f"Relational Merge OK! Unified Table Columns: {merged['columns']}")
    print(f"Total Unified Records: {merged['total_records']}")
    assert merged["total_records"] == 2
    assert "store_name" in merged["columns"]
    assert "customer_name" in merged["columns"]
    assert "product_name" in merged["columns"]

    print("\n==========================================")
    print("ALL RETAIL INTELLIGENCE & MERGE TESTS PASSED!")
    print("==========================================")

if __name__ == "__main__":
    test_retail_pipeline()
