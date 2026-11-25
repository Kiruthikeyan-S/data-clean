"""
Verification test for 50-Item Retail Business Analytics & Demand Prediction Dataset.
Verifies that processing the dataset activates:
1. Business Analytics Engine (Store, Item, Customer, Transaction analytics)
2. Inventory Demand Prediction Engine (30-day forecast, stock shortage alerts, reorder recommendations)
3. Relationship Validation Engine (Multi-entity integrity)
"""

import os
import pytest
from backend.pipeline import process_file_pipeline


def test_business_analytics_and_demand_prediction_50_items():
    csv_path = "sample_data/retail_business_analytics_demand_50_items.csv"
    assert os.path.exists(csv_path), f"File {csv_path} does not exist"

    with open(csv_path, "rb") as f:
        file_bytes = f.read()

    # Process through full pipeline
    res = process_file_pipeline(
        filename="retail_business_analytics_demand_50_items.csv",
        content_type="text/csv",
        file_bytes=file_bytes
    )

    assert res.status == "completed"
    assert res.entity_info is not None
    assert res.entity_info.entity_type == "mixed"
    assert res.entity_info.split_tables is not None
    assert len(res.entity_info.split_tables) >= 3

    # 1. Verify Business Analytics
    assert res.business_analytics is not None, "business_analytics should not be None"
    biz = res.business_analytics

    # Store analytics
    assert "store_analytics" in biz
    assert biz["store_analytics"]["total_stores"] == 5
    assert len(biz["store_analytics"]["store_wise_metrics"]) == 5

    # Item analytics
    assert "item_analytics" in biz
    assert biz["item_analytics"]["total_catalog_items"] == 50
    assert len(biz["item_analytics"]["fast_selling_products"]) > 0

    # Customer analytics
    assert "customer_analytics" in biz
    assert biz["customer_analytics"]["total_customers"] == 30
    assert len(biz["customer_analytics"]["top_customers_by_spend"]) > 0

    # Transaction analytics
    assert "transaction_analytics" in biz
    assert biz["transaction_analytics"]["total_transactions"] == 233
    assert biz["transaction_analytics"]["total_revenue"] > 10000

    # 2. Verify Demand Prediction Engine
    assert res.demand_prediction is not None, "demand_prediction should not be None"
    demand = res.demand_prediction
    assert demand["total_products_analyzed"] == 50
    assert demand["forecast_horizon_days"] == 30
    assert demand["stock_shortage_alerts_count"] > 0
    assert demand["recommendations_count"] > 0
    assert len(demand["forecasts"]) == 50

    # Check first forecast entry structure
    f0 = demand["forecasts"][0]
    assert "item_id" in f0
    assert "item_name" in f0
    assert "current_stock" in f0
    assert "predicted_demand" in f0
    assert "reorder_urgency" in f0
    assert "actionable_recommendation" in f0

    # 3. Verify Relationship Validation
    assert res.relationship_validation is not None
    assert res.relationship_validation["integrity_percentage"] == 100.0
