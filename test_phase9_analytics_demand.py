import pytest
from backend.analytics.business_analytics import generate_business_analytics_report
from backend.analytics.demand_predictor import predict_product_demand, DemandPredictor

def test_business_analytics_computation():
    stores = [
        {"store_id": "STR_01", "store_name": "Downtown", "city": "Miami"},
        {"store_id": "STR_02", "store_name": "Uptown", "city": "Denver"}
    ]
    items = [
        {"item_id": "PRD_A", "item_name": "Wireless Mouse", "stock_quantity": 5}, # Low stock
        {"item_id": "PRD_B", "item_name": "Keyboard", "stock_quantity": 50},
        {"item_id": "PRD_C", "item_name": "Desk Lamp", "stock_quantity": 20} # Non-selling
    ]
    customers = [
        {"customer_id": "CUST_1", "name": "Alice", "loyalty_tier": "Gold"},
        {"customer_id": "CUST_2", "name": "Bob", "loyalty_tier": "Silver"}
    ]
    transactions = [
        {"transaction_id": "T1", "store_id": "STR_01", "customer_id": "CUST_1", "item_id": "PRD_A", "quantity": 2, "total_amount": 40.0, "payment_method": "Card", "transaction_date": "2023-01-01"},
        {"transaction_id": "T2", "store_id": "STR_01", "customer_id": "CUST_1", "item_id": "PRD_A", "quantity": 1, "total_amount": 20.0, "payment_method": "Card", "transaction_date": "2023-01-02"},
        {"transaction_id": "T3", "store_id": "STR_02", "customer_id": "CUST_2", "item_id": "PRD_B", "quantity": 1, "total_amount": 100.0, "payment_method": "Cash", "transaction_date": "2023-01-03"}
    ]

    report = generate_business_analytics_report(stores, items, customers, transactions)

    # Store analytics check
    st_an = report["store_analytics"]
    assert st_an["total_stores"] == 2
    assert len(st_an["best_performing_stores"]) > 0

    # Item analytics check
    it_an = report["item_analytics"]
    assert len(it_an["low_stock_products"]) >= 1
    assert any(itm["item_id"] == "PRD_C" for itm in it_an["non_selling_products"])

    # Customer analytics check
    cu_an = report["customer_analytics"]
    assert cu_an["total_customers"] == 2
    assert cu_an["top_customers_by_spend"][0]["customer_id"] == "CUST_2" # 100.0 vs 60.0

    # Transaction analytics check
    tx_an = report["transaction_analytics"]
    assert tx_an["total_revenue"] == 160.0
    assert tx_an["total_transactions"] == 3
    assert tx_an["average_transaction_value"] == round(160.0 / 3, 2)
    assert len(tx_an["sales_trends_timeline"]) == 3


def test_demand_predictor_sufficiency_and_forecasting():
    items = [
        {"item_id": "PRD_A", "item_name": "Wireless Mouse", "stock_quantity": 5}
    ]

    # Test 1: Insufficient data (<5 transactions)
    sparse_txns = [
        {"item_id": "PRD_A", "quantity": 2, "transaction_date": "2023-01-01"}
    ]
    report_sparse = predict_product_demand(items, sparse_txns)
    assert report_sparse.data_sufficiency_status == "insufficient"
    assert report_sparse.limitations is not None
    assert len(report_sparse.forecasts) == 0

    # Test 2: Sufficient data (>=5 transactions)
    sufficient_txns = [
        {"item_id": "PRD_A", "quantity": 2, "transaction_date": "2023-01-01"},
        {"item_id": "PRD_A", "quantity": 3, "transaction_date": "2023-01-03"},
        {"item_id": "PRD_A", "quantity": 1, "transaction_date": "2023-01-05"},
        {"item_id": "PRD_A", "quantity": 4, "transaction_date": "2023-01-07"},
        {"item_id": "PRD_A", "quantity": 2, "transaction_date": "2023-01-10"}
    ]
    report_ok = predict_product_demand(items, sufficient_txns, forecast_horizon_days=30)
    assert report_ok.data_sufficiency_status == "sufficient"
    assert len(report_ok.forecasts) == 1
    fc = report_ok.forecasts[0]
    assert fc["predicted_demand"] > 0
    assert fc["upper_confidence_bound"] >= fc["predicted_demand"]
    assert fc["stock_shortage_warning"] is True # Stock was 5, 30 days demand is > 20
    assert fc["recommended_reorder_quantity"] > 0
