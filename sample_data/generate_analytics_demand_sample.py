"""
Generate realistic retail dataset with minimum 50 catalog items and 100+ transactions
designed specifically for:
1. Business Analytics (Store revenue, Item velocity, Customer spending, Sales timeline)
2. Inventory Demand Prediction (30-day forecasts, stock shortage warnings, reorder suggestions)
3. Relationship Validation (Stores <-> Items <-> Customers <-> Transactions)
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd

os.makedirs("sample_data/batch", exist_ok=True)

# 1. 50 Distinct Products / Items across 5 categories
categories = {
    "Electronics": [
        ("ITM-001", "Ultra Wireless Earbuds Pro", 89.99, 12),      # Low stock, high velocity -> alert
        ("ITM-002", "Noise-Canceling Bluetooth Headphones", 149.50, 45),
        ("ITM-003", "4K Ultra-HD Smart Monitor 27in", 299.00, 8),   # Critical shortage
        ("ITM-004", "Mechanical Gaming Keyboard RGB", 79.99, 25),
        ("ITM-005", "Ergonomic Wireless Mouse", 39.99, 60),
        ("ITM-006", "Fast Charging USB-C Hub 7-in-1", 45.00, 15),
        ("ITM-007", "Smart Home Security Camera", 69.99, 30),
        ("ITM-008", "Portable Bluetooth Speaker Waterproof", 55.00, 5), # Critical shortage
        ("ITM-009", "Wireless Qi Charging Stand", 29.99, 50),
        ("ITM-010", "Dual-Band Wi-Fi 6 Mesh Router", 129.99, 18),
    ],
    "Office & Workspace": [
        ("ITM-011", "Ergonomic Mesh Office Chair", 199.99, 10),
        ("ITM-012", "Motorized Adjustable Standing Desk", 380.00, 6), # Low stock
        ("ITM-013", "LED Dimmable Desk Lamp with USB", 34.99, 40),
        ("ITM-014", "Memory Foam Seat Cushion", 28.50, 65),
        ("ITM-015", "Under-Desk Footrest Adjustable", 24.99, 35),
        ("ITM-016", "Aluminum Laptop Stand Riser", 32.00, 55),
        ("ITM-017", "Cable Management Organizer Kit", 14.99, 120),
        ("ITM-018", "Magnetic Desktop Whiteboard", 22.50, 45),
        ("ITM-019", "Leather Executive Desk Blotter Mat", 26.99, 30),
        ("ITM-020", "Heavy Duty Desktop Monitor Arm", 59.99, 14),
    ],
    "Fitness & Lifestyle": [
        ("ITM-021", "Stainless Steel Insulated Water Bottle 32oz", 24.99, 9), # Low stock
        ("ITM-022", "High-Density Yoga Mat Non-Slip", 35.00, 42),
        ("ITM-023", "Adjustable Dumbbell Set 50lbs", 189.00, 7), # Critical shortage
        ("ITM-024", "Resistance Bands Set 5-Pack", 18.99, 80),
        ("ITM-025", "Smart Fitness Tracker Band", 49.99, 22),
        ("ITM-026", "Deep Tissue Muscle Foam Roller", 21.50, 38),
        ("ITM-027", "Speed Jump Rope Aluminum Handles", 12.99, 70),
        ("ITM-028", "Hydration Backpack 2L Water Bladder", 38.00, 16),
        ("ITM-029", "Gym Duffle Bag Waterproof", 42.50, 28),
        ("ITM-030", "Grip Strength Trainer Kit", 15.99, 95),
    ],
    "Kitchen & Home": [
        ("ITM-031", "Electric Gooseneck Pour-Over Kettle", 59.99, 11),
        ("ITM-032", "Conical Burr Coffee Grinder", 79.99, 15),
        ("ITM-033", "Cast Iron Skillet Pre-Seasoned 12in", 39.99, 24),
        ("ITM-034", "Digital Meat Thermometer Instant Read", 19.99, 65),
        ("ITM-035", "Non-Stick Silicone Kitchen Utensils 10pc", 29.99, 40),
        ("ITM-036", "Compact Air Fryer 4-Quart", 69.99, 8), # Low stock
        ("ITM-037", "Airtight Food Storage Containers 12pc", 36.50, 32),
        ("ITM-038", "Automatic Soap Dispenser Touchless", 22.00, 50),
        ("ITM-039", "Bamboo Cutting Board 3-Piece Set", 25.00, 45),
        ("ITM-040", "Stainless Steel Mixing Bowls Set", 28.00, 30),
    ],
    "Travel & Gear": [
        ("ITM-041", "Anti-Theft Travel Backpack 35L", 65.00, 13),
        ("ITM-042", "Hardside Spinner Luggage Carry-On", 119.00, 5), # Critical shortage
        ("ITM-043", "Compression Packing Cubes 6-Set", 22.99, 75),
        ("ITM-044", "Memory Foam Travel Neck Pillow", 19.50, 50),
        ("ITM-045", "Universal International Travel Adapter", 17.99, 90),
        ("ITM-046", "RFID Blocking Passport Holder Wallet", 14.50, 60),
        ("ITM-047", "Compact Windproof Travel Umbrella", 18.00, 40),
        ("ITM-048", "Digital Luggage Scale Handheld", 11.99, 85),
        ("ITM-049", "TSA Approved Travel Toiletry Bottles", 9.99, 110),
        ("ITM-050", "High Capacity Power Bank 20000mAh", 39.99, 18),
    ]
}

# Flatten 50 items
items_data = []
for cat, itms in categories.items():
    for item_id, item_name, price, stock in itms:
        items_data.append({
            "item_id": item_id,
            "item_name": item_name,
            "category": cat,
            "unit_price": price,
            "stock_quantity": stock,
            "store_id": f"STR-10{random.randint(1, 5)}"
        })

df_items = pd.DataFrame(items_data)

# 2. 5 Stores
stores_data = [
    {"store_id": "STR-101", "store_name": "Downtown Tech Flagship", "city": "San Francisco", "state": "CA"},
    {"store_id": "STR-102", "store_name": "Metropolitan Plaza Store", "city": "New York", "state": "NY"},
    {"store_id": "STR-103", "store_name": "Silicon Valley Hub", "city": "San Jose", "state": "CA"},
    {"store_id": "STR-104", "store_name": "Northwest Retail Gallery", "city": "Seattle", "state": "WA"},
    {"store_id": "STR-105", "store_name": "Midwest Commerce Center", "city": "Chicago", "state": "IL"},
]
df_stores = pd.DataFrame(stores_data)

# 3. 25 Customers
customers_data = [
    {"customer_id": f"CUST-{1000 + i}", "customer_name": name, "email": f"{name.lower().replace(' ', '.')}@example.com", "phone": f"+1-555-01{i:02d}"}
    for i, name in enumerate([
        "Alice Johnson", "Bob Smith", "Carol Martinez", "David Lee", "Emma Watson",
        "Frank Miller", "Grace Hopper", "Henry Ford", "Ivy Taylor", "Jack Robinson",
        "Karen White", "Leo Messi", "Mia Wong", "Nathan Drake", "Olivia Wilde",
        "Peter Parker", "Quinn Fabray", "Ryan Gosling", "Sophia Loren", "Tom Hanks",
        "Uma Thurman", "Victor Hugo", "Wendy Darling", "Xavier Woods", "Yara Shahidi"
    ], start=1)
]
df_customers = pd.DataFrame(customers_data)

# 4. 120 Transactions across the past 30 days
base_date = datetime(2026, 11, 24)
transactions_data = []
payment_methods = ["Credit Card", "Debit Card", "Apple Pay", "PayPal", "Cash"]

random.seed(42)

for t_idx in range(1, 131):
    txn_id = f"TXN-2026-{10000 + t_idx}"
    days_ago = random.randint(0, 28)
    txn_date = (base_date - timedelta(days=days_ago, hours=random.randint(1, 12), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M")
    
    # Pick item
    itm = random.choice(items_data)
    store = random.choice(stores_data)
    cust = random.choice(customers_data)
    
    qty = random.choices([1, 2, 3, 4, 5], weights=[60, 25, 8, 4, 3])[0]
    unit_p = itm["unit_price"]
    total_amt = round(qty * unit_p, 2)
    pay = random.choice(payment_methods)
    
    transactions_data.append({
        "transaction_id": txn_id,
        "transaction_date": txn_date,
        "customer_id": cust["customer_id"],
        "customer_name": cust["customer_name"],
        "store_id": store["store_id"],
        "store_name": store["store_name"],
        "item_id": itm["item_id"],
        "item_name": itm["item_name"],
        "category": itm["category"],
        "quantity": qty,
        "unit_price": unit_p,
        "total_amount": total_amt,
        "stock_quantity": itm["stock_quantity"],
        "payment_method": pay
    })

# Sort by date
transactions_data.sort(key=lambda x: x["transaction_date"])
df_txns = pd.DataFrame(transactions_data)

# Save combined multi-entity dataset (Single CSV with all 50 items and transactions)
combined_csv_path = "sample_data/retail_business_analytics_50_items.csv"
df_txns.to_csv(combined_csv_path, index=False)

# Save multi-sheet Excel file
combined_xlsx_path = "sample_data/retail_business_analytics_50_items.xlsx"
with pd.ExcelWriter(combined_xlsx_path, engine="openpyxl") as writer:
    df_txns.to_excel(writer, sheet_name="Transactions", index=False)
    df_items.to_excel(writer, sheet_name="Items_Catalog", index=False)
    df_stores.to_excel(writer, sheet_name="Stores", index=False)
    df_customers.to_excel(writer, sheet_name="Customers", index=False)

# Save separate CSV files for Batch Mode upload
df_items.to_csv("sample_data/batch/items_catalog_50.csv", index=False)
df_txns.to_csv("sample_data/batch/sales_transactions_130.csv", index=False)
df_stores.to_csv("sample_data/batch/stores.csv", index=False)
df_customers.to_csv("sample_data/batch/customers.csv", index=False)

print(f"Generated {len(items_data)} items, {len(stores_data)} stores, {len(customers_data)} customers, and {len(transactions_data)} transactions.")
print(f"Combined CSV saved to: {combined_csv_path}")
print(f"Combined Excel saved to: {combined_xlsx_path}")
print("Batch CSVs saved to: sample_data/batch/")
