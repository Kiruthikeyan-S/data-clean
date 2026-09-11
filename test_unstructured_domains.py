import sys
import io
from backend.pipeline import process_file_pipeline

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_domains():
    print("=== 1. Testing Unstructured Customer Profiles List ===")
    customer_txt = """
    1. Customer account #CUST-9821 belongs to Marcus Vance (marcus.vance@techcorp.io, +1-512-555-0149). He holds Platinum loyalty.
    2. Emily Chen (emily.chen88@gmail.com) registered on July 14, 2023, during a summer promotional drive. She lives in Chicago, IL.
    3. Profile ID 44021: David O'Connor, located in Dublin, Ireland (d.oconnor@consultant.ie). David has made 14 lifetime purchases.
    4. Priya Sharma (Loyalty #IN-88201) is a Bengaluru-based frequent shopper who primarily orders gourmet coffee and premium pantry.
    5. Walk-in loyalty record for Jordan Miller (jordan.m@outlook.com, phone 206-555-9831, Seattle, WA). Gold member since 2021.
    6. Elena Rostova (elena.rostova@legalhub.de) resides in Frankfurt, Germany. She opted out of marketing emails.
    7. Account #CUST-1104: Kevin Patel from Toronto, ON. Kevin joined the VIP program in March 2024, has spent CAD 1,420 to date.
    8. Aisha Al-Mansoor (aisha.m@innovate.ae, Dubai, UAE) registered via Apple ID sign-in.
    9. Member #US-7718: Samuel Green (sam.green@londonpress.co.uk) residing in London, UK.
    10. Customer #CHI-552: Natalie Brooks (natalie.b@atlantatech.org, phone 404-555-0182, Atlanta, GA). Silver tier loyalty member.
    """

    res_cust = process_file_pipeline("unstructured_customers.txt", "text/plain", customer_txt.encode("utf-8"))
    print(f"Classification: {res_cust.classification}")
    print(f"Columns: {res_cust.columns}")
    assert isinstance(res_cust.structured_data, list)
    assert "customer_name" in res_cust.columns or "email" in res_cust.columns
    assert "product_name" not in res_cust.columns
    print(f"Total Customer Records: {len(res_cust.structured_data)}")
    for r in res_cust.structured_data[:3]:
        print(f" -> {r.get('customer_id')} | {r.get('customer_name')} | {r.get('email')} | {r.get('city_location')} | {r.get('loyalty_tier')}")

    print("\n=== 2. Testing Unstructured Product Catalog List ===")
    product_txt = """
    1. Apex-V Pro Smartwatch (UPC 880921445102, Midnight Blue edition) sells for $349.00. Key technical specifications include IP68 water resistance.
    2. EcoClean Citrus Multi-Surface Disinfectant Spray (Item code: HOU-554). Selling at $7.99 per unit.
    3. Wireless Noise-Cancelling Over-Ear Headphones (SKU: AUD-9920, Silver). Retailing at $199.99.
    """
    res_prod = process_file_pipeline("unstructured_products.txt", "text/plain", product_txt.encode("utf-8"))
    print(f"Columns: {res_prod.columns}")
    assert isinstance(res_prod.structured_data, list)
    assert "product_name" in res_prod.columns
    assert "unit_price" in res_prod.columns
    print(f"Total Product Records: {len(res_prod.structured_data)}")
    for r in res_prod.structured_data:
        print(f" -> {r.get('product_name')} | {r.get('sku')} | ${r.get('unit_price')}")

    print("\n==========================================")
    print("DOMAIN-AWARE EXTRACTION PASSED PERFECTLY!")
    print("==========================================")

if __name__ == "__main__":
    test_domains()
