"""
Test verification for 50-Item Retail Business Analytics & AI Demand Prediction
"""

import os
import pytest
from backend.pipeline import process_file_pipeline


def test_business_analytics_and_demand_prediction_on_50_items():
    csv_path = "sample_data/retail_business_analytics_demand_50_items.csv"
    assert os.path.exists(csv_path)

    with open(csv_path, "rb") as f:
        file_bytes = f.read()

    response = process_file_pipeline(
        filename="retail_business_analytics_demand_50_items.csv",
        content_type="text/csv",
        file_bytes=file_bytes
    )

    assert response.status == "completed"
    assert response.classification == "structured"

    # 1. Verify Entity Splitting into Store, Item, Customer, Transaction
    assert response.entity_info is not None
    assert response.entity_info.entity_type == "mixed"
    assert response.entity_info.split_tables is not None
    assert len(response.entity_info.split_tables) >= 3

    # 2. Verify Business Analytics
    assert response.business_analytics is not None
    ba = response.business_analytics
    assert "store_analytics" in ba
    assert "item_analytics" in ba
    assert "customer_analytics" in ba
    assert "transaction_analytics" in ba

    # Verify Store metrics
    store_analytics = ba["store_analytics"]
    assert store_analytics["total_stores"] >= 5
    assert len(store_analytics["store_wise_metrics"]) >= 5
    assert len(store_analytics["best_performing_stores"]) >= 1

    # Verify Item analytics
    item_analytics = ba["item_analytics"]
    assert item_analytics["total_catalog_items"] >= 50
    assert len(item_analytics["fast_selling_products"]) >= 1

    # Verify Transaction analytics
    txn_analytics = ba["transaction_analytics"]
    assert txn_analytics["total_revenue"] > 1000
    assert txn_analytics["total_transactions"] >= 200

    # 3. Verify AI Demand Prediction & Stock Forecasting
    assert response.demand_prediction is not None
    dp = response.demand_prediction
    assert dp["total_products_analyzed"] >= 50
    assert dp["data_sufficiency_status"] == "sufficient"
    assert dp["forecast_horizon_days"] == 30
    assert dp["stock_shortage_alerts_count"] > 0
    assert dp["recommendations_count"] > 0
    assert len(dp["forecasts"]) >= 50

    # Verify sample forecast structure
    sample_fc = dp["forecasts"][0]
    assert "item_id" in sample_fc
    assert "item_name" in sample_fc
    assert "predicted_demand" in sample_fc
    assert "reorder_urgency" in sample_fc
    assert "actionable_recommendation" in sample_fc
