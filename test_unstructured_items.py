import sys
import io
from backend.pipeline import process_file_pipeline

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_unstructured_items():
    unstructured_txt = """
    3. Apex-V Pro Smartwatch (UPC 880921445102, Midnight Blue edition) sells for $349.00. Key technical specifications include IP68 water resistance, AMOLED always-on display, heart rate variability monitoring, and 7-day battery endurance.
    4. EcoClean Citrus Multi-Surface Disinfectant Spray, 32 fl oz bottle (Item code: HOU-554). Selling at $7.99 per unit or $38.00 for a pack of six. Active ingredient: 0.5% citric acid. Shelf location: Aisle 4, Shelf C, Bay 2.
    5. Wireless Noise-Cancelling Over-Ear Headphones (SKU: AUD-9920, Silver). Retailing at $199.99, wholesale price $110.00. Features Bluetooth 5.3, 40mm neodymium drivers, 30-hour playback, and comes packaged with a USB-C fast charging braided cable.
    6. Men's Trail Runner Waterproof Hiking Boots, Size 10.5 US, Charcoal Gray (SKU: APP-4410). Priced at $135.00. Constructed with Vibram rubber outsoles and Gore-Tex breathable membranes; currently 18 pairs available in local stock.
    7. Smart LED Ambient Light Strip, 16.4 ft WiFi-enabled (Item: IOT-332). Works with HomeKit and Alexa. Retails at $29.99. Minimum reorder threshold is set to 50 units; supplier lead time is currently 14 business days from Shenzhen.
    8. Sourdough Organic Boule Loaf (SKU: BKY-004), baked fresh daily at 5:00 AM using stone-ground heritage flour. Sold for $6.50 per loaf, has a recommended shelf life of 3 days, and unsold inventory is marked down by 50% after 7:00 PM daily.
    9. ProSeries 65W GaN Multi-Port USB-C Wall Charger (SKU: ELEC-770). Compact foldable design with dual USB-C PD and single USB-A output. Retail is $39.99 with bulk merchant packaging available at $22.50 per unit on orders exceeding 25 units.
    10. Stainless Steel Double-Wall Insulated Travel Tumbler 24oz, Forest Green (SKU: KITCH-310). Retails for $24.95. Keeps beverages hot for 12 hours or cold for 24 hours, equipped with a spill-resistant magnetic sliding lid.
    """

    res = process_file_pipeline("unstructured_items.txt", "text/plain", unstructured_txt.encode("utf-8"))
    
    print(f"Classification: {res.classification}")
    print(f"Total Structured Records: {len(res.structured_data) if isinstance(res.structured_data, list) else 'Not list'}")
    print(f"Columns: {res.columns}")
    
    assert isinstance(res.structured_data, list)
    assert len(res.structured_data) == 8
    assert "product_name" in res.columns
    assert "unit_price" in res.columns
    assert "sku" in res.columns
    
    for row in res.structured_data:
        print(f" -> #{row.get('item_number')} | {row.get('product_name')} | SKU: {row.get('sku')} | ${row.get('unit_price')} | {row.get('category')}")
        
    print("\nRetail Intelligence check:")
    if res.retail_intelligence:
        print(f"Top Seller / High value product: {res.retail_intelligence.product_analytics.top_selling[0].product_name}")
        print(f"Forecast count: {len(res.retail_intelligence.demand_forecasting.forecasts)}")
        
    print("\nSUCCESS: Unstructured items parsed into clean structured records table perfectly!")

if __name__ == "__main__":
    test_unstructured_items()
