"""
Generates comprehensive 50-Item Retail & Business Analytics dataset for:
- Sales & Volume Analytics (Store, Item, Customer, Transaction metrics)
- AI Inventory Demand Prediction (30-day forecast, stock shortages, reorder recommendations)
- Relationship Validation (Referential integrity between Stores, Items, Customers, Transactions)
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd

os.makedirs("sample_data", exist_ok=True)

# 1. 50 Diverse Retail & Tech Products across categories
PRODUCTS = [
    # Electronics & Computing (1-10)
    ("ITM-001", "UltraBook Pro 15-inch Laptop", "Electronics", 1299.99, 12),
    ("ITM-002", "Wireless Ergonomic Mouse", "Accessories", 49.99, 85),
    ("ITM-003", "Mechanical Gaming Keyboard RGB", "Accessories", 119.50, 4),      # Critical shortage candidate
    ("ITM-004", "27-inch 4K UHD Monitor", "Electronics", 389.00, 18),
    ("ITM-005", "Noise-Cancelling Wireless Headphones", "Audio", 249.99, 6),        # Critical shortage candidate
    ("ITM-006", "USB-C Multi-Port Hub Adapter", "Accessories", 39.99, 120),
    ("ITM-007", "External SSD 1TB High-Speed", "Storage", 109.99, 8),              # Medium shortage
    ("ITM-008", "HD 1080p Streaming Webcam", "Accessories", 69.99, 32),
    ("ITM-009", "Bluetooth Conference Speaker", "Audio", 129.00, 15),
    ("ITM-010", "Smart Wi-Fi 6 Mesh Router", "Networking", 199.99, 5),             # Critical shortage

    # Smart Office & Furniture (11-20)
    ("ITM-011", "Ergonomic Mesh Task Chair", "Furniture", 289.00, 14),
    ("ITM-012", "Motorized Adjustable Standing Desk", "Furniture", 549.00, 7),
    ("ITM-013", "LED Dimmable Desk Lamp with Qi Charger", "Lighting", 45.00, 60),
    ("ITM-014", "Anti-Fatigue Standing Desk Mat", "Office", 39.99, 45),
    ("ITM-015", "Under-Desk Cable Management Tray", "Office", 24.50, 95),
    ("ITM-016", "Dual Monitor Articulating Arm", "Accessories", 79.99, 22),
    ("ITM-017", "Acoustic Desktop Privacy Panel", "Office", 89.00, 16),
    ("ITM-018", "Magnetic Whiteboard 36x24", "Office", 59.99, 28),
    ("ITM-019", "High-Security Micro-Cut Paper Shredder", "Equipment", 149.99, 9),
    ("ITM-020", "Steel Mobile 3-Drawer Filing Cabinet", "Furniture", 169.00, 11),

    # Smart Home & IoT (21-30)
    ("ITM-021", "Smart Thermostat Pro Eco", "Smart Home", 179.99, 3),              # Critical shortage
    ("ITM-022", "Indoor Security Camera 2K Pan/Tilt", "Smart Home", 59.99, 40),
    ("ITM-023", "Smart Doorbell with Night Vision", "Smart Home", 139.00, 12),
    ("ITM-024", "Smart Wi-Fi Plug Pack of 4", "Smart Home", 34.99, 75),
    ("ITM-025", "Smart LED Color Light Strip 5M", "Lighting", 29.99, 88),
    ("ITM-026", "Automated Robot Vacuum Cleaner", "Home Appliances", 399.00, 6),    # Critical shortage
    ("ITM-027", "Air Purifier with HEPA Filter", "Home Appliances", 129.99, 15),
    ("ITM-028", "Smart Sensor Water Leak Detector", "Smart Home", 28.50, 50),
    ("ITM-029", "Digital Weather Station Wireless", "Smart Home", 49.00, 30),
    ("ITM-030", "Smart Lock Keyless Deadbolt", "Smart Home", 189.99, 8),

    # Audio & Media (31-40)
    ("ITM-031", "Compact Soundbar with Subwoofer", "Audio", 159.00, 20),
    ("ITM-032", "Portable Waterproof Bluetooth Speaker", "Audio", 79.99, 42),
    ("ITM-033", "Studio Quality Condenser Microphone", "Audio", 119.00, 10),
    ("ITM-034", "Adjustable Boom Arm Mic Stand", "Accessories", 35.00, 65),
    ("ITM-035", "Wireless Lavalier Lapel Mic Kit", "Audio", 89.99, 14),
    ("ITM-036", "Turntable Vinyl Record Player", "Audio", 149.00, 9),
    ("ITM-037", "Over-Ear Open-Back Reference Headphones", "Audio", 219.00, 7),
    ("ITM-038", "Mini Portable Movie Projector", "Electronics", 229.00, 11),
    ("ITM-039", "Tripod Stand with Ring Light", "Photography", 49.99, 55),
    ("ITM-040", "Smartphone Gimbal 3-Axis Stabilizer", "Photography", 109.00, 16),

    # Power & Infrastructure Supplies (41-50)
    ("ITM-041", "Uninterruptible Power Supply Battery Backup (UPS)", "Power", 189.00, 4), # Critical shortage
    ("ITM-042", "High-Capacity Power Bank 26800mAh", "Power", 59.99, 90),
    ("ITM-043", "Surge Protector Power Strip 12-Outlets", "Power", 29.99, 110),
    ("ITM-044", "Cat6 Ethernet Patch Cable 50FT", "Networking", 19.99, 130),
    ("ITM-045", "10-Port Gigabit Ethernet Switch", "Networking", 69.99, 25),
    ("ITM-046", "Fast Wireless Charging Pad 15W", "Power", 25.00, 80),
    ("ITM-047", "Heavy Duty Extension Cord 25FT", "Power", 22.50, 70),
    ("ITM-048", "Solar Powered Emergency Lantern", "Lighting", 39.99, 40),
    ("ITM-049", "Universal International Travel Adapter", "Accessories", 21.99, 100),
    ("ITM-050", "Heavy Duty Anti-Theft Laptop Cable Lock", "Security", 29.50, 60),
]

# 2. 5 Stores
STORES = [
    ("STR-101", "Downtown Innovation Flagship", "500 Market St, San Francisco, CA"),
    ("STR-102", "Metropolis Tech Plaza", "750 5th Avenue, New York, NY"),
    ("STR-103", "Suburban Galleria Mall", "1200 Lakeview Blvd, Chicago, IL"),
    ("STR-104", "Airport Express Terminal", "Terminal 3 Gate B, Atlanta, GA"),
    ("STR-105", "Pacific Coast Omni Depot", "300 Ocean Way, Seattle, WA"),
]

# 3. 30 Customers
CUSTOMERS = [
    ("CUST-1001", "Alice Walker", "alice.w@example.com", "+1-555-0101", "Gold"),
    ("CUST-1002", "Bob Martinez", "bob.m@example.com", "+1-555-0102", "Silver"),
    ("CUST-1003", "Catherine Zhang", "c.zhang@example.com", "+1-555-0103", "Platinum"),
    ("CUST-1004", "David Miller", "d.miller@example.com", "+1-555-0104", "Bronze"),
    ("CUST-1005", "Elena Rostova", "elena.r@example.com", "+1-555-0105", "Platinum"),
    ("CUST-1006", "Frank Castle", "frank.c@example.com", "+1-555-0106", "Gold"),
    ("CUST-1007", "Grace Hopper", "grace.h@example.com", "+1-555-0107", "Platinum"),
    ("CUST-1008", "Henry Ford", "henry.f@example.com", "+1-555-0108", "Silver"),
    ("CUST-1009", "Isabella Garcia", "isabella.g@example.com", "+1-555-0109", "Bronze"),
    ("CUST-1010", "Jack Ryan", "jack.r@example.com", "+1-555-0110", "Gold"),
    ("CUST-1011", "Karen Scott", "karen.s@example.com", "+1-555-0111", "Bronze"),
    ("CUST-1012", "Liam O'Connor", "liam.oc@example.com", "+1-555-0112", "Silver"),
    ("CUST-1013", "Mia Tanaka", "mia.t@example.com", "+1-555-0113", "Gold"),
    ("CUST-1014", "Noah Webster", "noah.w@example.com", "+1-555-0114", "Silver"),
    ("CUST-1015", "Olivia Wilde", "olivia.w@example.com", "+1-555-0115", "Platinum"),
    ("CUST-1016", "Peter Parker", "peter.p@example.com", "+1-555-0116", "Bronze"),
    ("CUST-1017", "Quinn Fabray", "quinn.f@example.com", "+1-555-0117", "Gold"),
    ("CUST-1018", "Rachel Green", "rachel.g@example.com", "+1-555-0118", "Silver"),
    ("CUST-1019", "Steve Rogers", "steve.r@example.com", "+1-555-0119", "Platinum"),
    ("CUST-1020", "Tony Stark", "tony.s@example.com", "+1-555-0120", "Platinum"),
    ("CUST-1021", "Uma Thurman", "uma.t@example.com", "+1-555-0121", "Gold"),
    ("CUST-1022", "Victor Creed", "victor.c@example.com", "+1-555-0122", "Bronze"),
    ("CUST-1023", "Wanda Maximoff", "wanda.m@example.com", "+1-555-0123", "Platinum"),
    ("CUST-1024", "Xavier Charles", "xavier.c@example.com", "+1-555-0124", "Gold"),
    ("CUST-1025", "Yara Shahidi", "yara.s@example.com", "+1-555-0125", "Silver"),
    ("CUST-1026", "Zane Malik", "zane.m@example.com", "+1-555-0126", "Bronze"),
    ("CUST-1027", "Arthur Dent", "arthur.d@example.com", "+1-555-0127", "Gold"),
    ("CUST-1028", "Bruce Wayne", "bruce.w@example.com", "+1-555-0128", "Platinum"),
    ("CUST-1029", "Clark Kent", "clark.k@example.com", "+1-555-0129", "Gold"),
    ("CUST-1030", "Diana Prince", "diana.p@example.com", "+1-555-0130", "Platinum"),
]

# Generate 200 transactions covering 60 days to satisfy statistical demand forecast window
random.seed(42)
start_date = datetime(2026, 9, 15)
transactions = []

payment_methods = ["Credit Card", "Debit Card", "Apple Pay", "Google Pay", "Cash"]

# Ensure every single product (1 to 50) has at least 1-8 transactions
for p_idx, (p_id, p_name, cat, price, stock) in enumerate(PRODUCTS):
    # Some products have high frequency (fast selling), some moderate, some low
    if p_idx in [2, 4, 9, 20, 25, 40]: # High velocity items (will trigger stock shortages)
        n_txns = random.randint(8, 14)
    elif p_idx % 3 == 0:
        n_txns = random.randint(4, 7)
    else:
        n_txns = random.randint(2, 4)

    for _ in range(n_txns):
        day_offset = random.randint(0, 59)
        txn_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        cust = random.choice(CUSTOMERS)
        store = random.choice(STORES)
        qty = random.randint(1, 3) if p_idx in [2, 4, 9, 20, 25, 40] else random.randint(1, 2)
        total_amt = round(qty * price, 2)
        pay_method = random.choice(payment_methods)

        transactions.append({
            "transaction_id": f"TXN-{len(transactions) + 10001}",
            "transaction_date": txn_date,
            "customer_id": cust[0],
            "customer_name": cust[1],
            "customer_email": cust[2],
            "customer_phone": cust[3],
            "store_id": store[0],
            "store_name": store[1],
            "store_location": store[2],
            "item_id": p_id,
            "item_name": p_name,
            "category": cat,
            "unit_price": price,
            "quantity": qty,
            "total_amount": total_amt,
            "stock_quantity": stock,
            "payment_method": pay_method
        })

# Sort by date
transactions.sort(key=lambda x: x["transaction_date"])

# Create DataFrame
df_all = pd.DataFrame(transactions)

# 1. Save Full Combined CSV (for single-file upload & entity splitting)
csv_path = "sample_data/retail_business_analytics_demand_50_items.csv"
df_all.to_csv(csv_path, index=False)
print(f"Generated {len(df_all)} transactions covering 50 items in {csv_path}")

# 2. Save Excel Multi-Sheet Workbook
excel_path = "sample_data/retail_business_analytics_demand_50_items.xlsx"

# Prepare distinct entity tables
df_items = pd.DataFrame([{
    "item_id": p[0], "item_name": p[1], "category": p[2], "unit_price": p[3], "stock_quantity": p[4]
} for p in PRODUCTS])

df_stores = pd.DataFrame([{
    "store_id": s[0], "store_name": s[1], "store_location": s[2]
} for s in STORES])

df_customers = pd.DataFrame([{
    "customer_id": c[0], "customer_name": c[1], "customer_email": c[2], "customer_phone": c[3], "loyalty_tier": c[4]
} for c in CUSTOMERS])

df_txns = pd.DataFrame([{
    "transaction_id": t["transaction_id"],
    "transaction_date": t["transaction_date"],
    "customer_id": t["customer_id"],
    "store_id": t["store_id"],
    "item_id": t["item_id"],
    "quantity": t["quantity"],
    "unit_price": t["unit_price"],
    "total_amount": t["total_amount"],
    "payment_method": t["payment_method"]
} for t in transactions])

with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    df_all.to_excel(writer, sheet_name="Full_Retail_Transactions", index=False)
    df_txns.to_excel(writer, sheet_name="Transactions", index=False)
    df_items.to_excel(writer, sheet_name="Products_Catalog", index=False)
    df_stores.to_excel(writer, sheet_name="Stores", index=False)
    df_customers.to_excel(writer, sheet_name="Customers", index=False)

print(f"Generated multi-sheet Excel file in {excel_path}")
