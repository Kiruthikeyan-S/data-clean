import io
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

from backend.pipeline import process_file_pipeline
from backend.analytics.business_analyst import generate_business_analysis

def test_retail_sales_analysis():
    csv_bytes = b"""store_id,store_name,city,product_id,product_name,unit_price,customer_id,customer_name,customer_email,purchase_date,quantity,total_amount,payment_method
S001,Downtown Mall,Chennai,P101,Nike Running Shoes,5999.00,C001,Ravi Kumar,ravi@gmail.com,2024-01-15,2,11998.00,Credit Card
S001,Downtown Mall,Chennai,P102,Adidas T-Shirt,2499.00,C002,Priya Sharma,priya@yahoo.com,2024-01-15,1,2499.00,UPI
S002,City Center,Mumbai,P101,Nike Running Shoes,5999.00,C001,Ravi Kumar,ravi@gmail.com,2024-01-16,1,5999.00,Credit Card
S002,City Center,Mumbai,P103,Puma Cap,899.00,C003,Amit Patel,amit@hotmail.com,2024-01-17,3,2697.00,Cash
"""
    response = process_file_pipeline("sales_intelligence.csv", "text/csv", csv_bytes)
    assert response.status == "completed"
    assert response.business_analysis is not None
    ba = response.business_analysis
    print(f"\n--- {ba.headline} ---")
    print(f"Entity Type: {ba.entity_type}")
    print("\nMetrics:")
    for m in ba.metrics:
        print(f"  • {m.label}: {m.value} ({m.subtext})")
    print("\nInsights:")
    for ins in ba.insights:
        print(f"  [{ins.badge}] {ins.title}: {ins.description}")

    assert len(ba.metrics) >= 3
    assert len(ba.insights) >= 2

def test_store_catalog_analysis():
    df_store = pd.DataFrame([
        {"store_id": "STR-01", "store_name": "Phoenix Mall", "city": "Bangalore", "state": "Karnataka", "sq_ft": 15000},
        {"store_id": "STR-02", "store_name": "Express Avenue", "city": "Chennai", "state": "Tamil Nadu", "sq_ft": 12000},
        {"store_id": "STR-03", "store_name": "Forum Mall", "city": "Bangalore", "state": "Karnataka", "sq_ft": 18000}
    ])
    report = generate_business_analysis(df_store, entity_type="store")
    print(f"\n--- Store Report: {report.headline} ---")
    for m in report.metrics:
        print(f"  • {m.label}: {m.value}")
    assert report.entity_type == "store"
    assert len(report.metrics) >= 2

if __name__ == "__main__":
    print("Testing Business Analysis & Intelligence Engine...")
    test_retail_sales_analysis()
    test_store_catalog_analysis()
    print("\nALL BUSINESS ANALYSIS TESTS PASSED SUCCESSFULLY!")
