"""
Test suite for BMW Spare Parts Demand Prediction & Vehicle Sales Auto-Adapter
"""

import os
import pytest
from backend.pipeline import process_file_pipeline


def test_bmw_spare_parts_demand_adapter():
    csv_path = "sample_data/bmw_spare_parts_inventory_demand.csv"
    assert os.path.exists(csv_path), f"File {csv_path} does not exist"

    with open(csv_path, "rb") as f:
        content = f.read()

    res = process_file_pipeline(
        filename="bmw_spare_parts_inventory_demand.csv",
        content_type="text/csv",
        file_bytes=content
    )

    assert res.status == "completed"
    assert res.demand_prediction is not None, "demand_prediction must not be None"
    assert res.business_analytics is not None, "business_analytics must not be None"

    demand = res.demand_prediction
    assert demand["forecast_horizon_days"] == 30
    assert demand["data_sufficiency_status"] == "sufficient"
    assert len(demand["forecasts"]) == 220
    assert demand["stock_shortage_alerts_count"] > 0
    assert demand["recommendations_count"] > 0

    # Verify first entry structure
    f0 = demand["forecasts"][0]
    assert "item_id" in f0
    assert "item_name" in f0
    assert "current_stock" in f0
    assert "daily_velocity" in f0 or "historical_sales_velocity_daily" in f0
    assert "predicted_demand" in f0
    assert "lower_confidence_bound" in f0
    assert "upper_confidence_bound" in f0
    assert "reorder_urgency" in f0


def test_vehicle_sales_classification_adapter():
    mock_csv = """MODEL,YEAR,MILEAGE,PRICE,COLOR,TRANSMISSION,FUEL TYPE,REGION,ENGINE SIZE L,SALES VOLUME,SALES CLASSIFICATION
5 Series,2016,151748,98740,Red,Manual,Petrol,Asia,3.5,8300,High
I8,2013,121671,79219,Red,Automatic,Hybrid,North America,1.6,3428,Low
5 Series,2022,10991,113265,Blue,Automatic,Petrol,North America,4.5,6994,Low
X3,2024,27255,60971,Blue,Automatic,Petrol,Middle East,1.7,4047,Low
7 Series,2020,122131,40898,Black,Manual,Diesel,South America,2.1,3880,Low
"""
    res = process_file_pipeline(
        filename="BMW_Car_Sales_Classification.csv",
        content_type="text/csv",
        file_bytes=mock_csv.encode("utf-8")
    )

    assert res.status == "completed"
    assert res.business_analytics is not None
    assert res.demand_prediction is not None
    assert res.business_analytics["transaction_analytics"]["total_revenue"] > 0
    assert len(res.demand_prediction["forecasts"]) >= 4
