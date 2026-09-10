import re
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np

# Known keyword vocabularies for retail entities
STORE_KEYWORDS = {
    "store", "store_id", "store_name", "branch", "branch_id", "branch_name",
    "location", "retail_outlet", "outlet", "region", "territory", "store_manager",
    "warehouse", "pos_terminal", "register_no", "station"
}

ITEM_KEYWORDS = {
    "item", "item_id", "item_name", "item_desc", "item_description", "product",
    "product_id", "product_name", "product_title", "sku", "barcode", "upc",
    "category", "sub_category", "department", "brand", "unit_price", "price",
    "mrp", "cost", "cost_price", "stock", "inventory", "stock_qty", "quantity", "qty",
    "course_code", "course_title"
}

CUSTOMER_KEYWORDS = {
    "customer", "customer_id", "customer_name", "client", "client_name", "buyer",
    "buyer_name", "shopper", "consumer", "patron", "email", "customer_email",
    "phone", "customer_phone", "mobile", "address", "shipping_address",
    "billing_address", "city", "state", "postal_code", "zip", "dob", "gender",
    "loyalty_tier", "membership", "points", "student_name"
}

TRANSACTION_KEYWORDS = {
    "order", "order_id", "order_number", "invoice", "invoice_no", "invoice_id",
    "receipt", "receipt_no", "transaction", "transaction_id", "bill_no",
    "date", "order_date", "invoice_date", "timestamp", "payment_method",
    "payment_type", "total", "total_amount", "amount", "subtotal", "tax", "vat",
    "gst", "discount", "net_amount", "grand_total"
}

def classify_column_entity(col_name: str) -> str:
    c = str(col_name).lower().strip().replace(" ", "_").replace("-", "_")
    for kw in STORE_KEYWORDS:
        if kw == c or (len(kw) > 3 and kw in c):
            return "store"
    for kw in ITEM_KEYWORDS:
        if kw == c or (len(kw) > 3 and kw in c):
            return "item"
    for kw in CUSTOMER_KEYWORDS:
        if kw == c or (len(kw) > 3 and kw in c):
            return "customer"
    for kw in TRANSACTION_KEYWORDS:
        if kw == c or (len(kw) > 3 and kw in c):
            return "transaction"
    return "other"

def detect_retail_dataset_type(columns: List[str]) -> Dict[str, Any]:
    store_fields = []
    item_fields = []
    customer_fields = []
    transaction_fields = []
    
    for col in columns:
        entity = classify_column_entity(col)
        if entity == "store":
            store_fields.append(col)
        elif entity == "item":
            item_fields.append(col)
        elif entity == "customer":
            customer_fields.append(col)
        elif entity == "transaction":
            transaction_fields.append(col)
            
    has_store = len(store_fields) > 0
    has_item = len(item_fields) > 0
    has_customer = len(customer_fields) > 0
    has_tx = len(transaction_fields) > 0
    
    entity_counts = sum([has_store, has_item, has_customer, has_tx])
    
    if entity_counts >= 2 or (has_item and (has_store or has_customer or has_tx)):
        entity_type = "COMBINED_TRANSACTION"
        entity_label = "Combined Retail Transaction (Store + Items + Customer)"
    elif has_item:
        entity_type = "ITEM"
        entity_label = "Item & Product Catalog Data"
    elif has_customer:
        entity_type = "CUSTOMER"
        entity_label = "Customer & Demographic Profiles"
    elif has_store:
        entity_type = "STORE"
        entity_label = "Store & Branch Network Data"
    else:
        entity_type = "GENERAL_RETAIL"
        entity_label = "Retail Operational Dataset"
        
    return {
        "entity_type": entity_type,
        "entity_label": entity_label,
        "store_fields": store_fields,
        "item_fields": item_fields,
        "customer_fields": customer_fields,
        "transaction_fields": transaction_fields
    }

def analyze_retail_intelligence(df: pd.DataFrame) -> Dict[str, Any]:
    if df is None or df.empty:
        return {
            "entity_type": "GENERAL_RETAIL",
            "entity_label": "Retail Operational Dataset",
            "entity_breakdown": {
                "store_fields": [], "item_fields": [], "customer_fields": [], "transaction_fields": []
            },
            "best_selling_items": [],
            "least_selling_items": [],
            "store_sales": [],
            "customer_patterns": [],
            "sales_forecast": [],
            "inventory_recommendations": [],
            "summary_metrics": []
        }
        
    cols = [str(c) for c in df.columns]
    type_info = detect_retail_dataset_type(cols)
    entity_type = type_info["entity_type"]
    entity_label = type_info["entity_label"]
    
    best_selling = []
    least_selling = []
    store_sales = []
    customer_patterns = []
    sales_forecast = []
    inventory_recs = []
    summary_metrics = []
    
    # 1. Identify Item column & Quantity / Amount column
    item_col = None
    for c in cols:
        low = c.lower()
        if any(k in low for k in ["item_name", "product_name", "product", "item", "sku", "course_title", "title", "name"]):
            item_col = c
            break
            
    qty_col = None
    for c in cols:
        low = c.lower()
        if any(k in low for k in ["qty", "quantity", "units_sold", "count", "sold"]):
            qty_col = c
            break
            
    amt_col = None
    for c in cols:
        low = c.lower()
        if any(k in low for k in ["total_amount", "amount", "revenue", "sales", "price", "subtotal", "grand_total"]):
            amt_col = c
            break

    if item_col:
        try:
            if qty_col and pd.to_numeric(df[qty_col], errors='coerce').notnull().any():
                df_calc = df.copy()
                df_calc['_metric'] = pd.to_numeric(df_calc[qty_col], errors='coerce').fillna(1)
                grouped = df_calc.groupby(item_col)['_metric'].sum().sort_values(ascending=False)
                metric_label = "Units Sold"
            elif amt_col and pd.to_numeric(df[amt_col], errors='coerce').notnull().any():
                df_calc = df.copy()
                df_calc['_metric'] = pd.to_numeric(df_calc[amt_col], errors='coerce').fillna(0)
                grouped = df_calc.groupby(item_col)['_metric'].sum().sort_values(ascending=False)
                metric_label = "Total Revenue ($)"
            else:
                grouped = df[item_col].value_counts()
                metric_label = "Total Records"
                
            valid_mask = [bool(str(x).strip()) for x in grouped.index]
            grouped = grouped[valid_mask]
            
            top_items = grouped.head(5)
            for idx, (name, val) in enumerate(top_items.items(), 1):
                best_selling.append({
                    "name": str(name),
                    "metric_value": round(float(val), 2),
                    "metric_label": metric_label,
                    "rank": idx
                })
                
            if len(grouped) > 3:
                bot_items = grouped.tail(min(5, len(grouped) - 1)).iloc[::-1]
                for idx, (name, val) in enumerate(bot_items.items(), 1):
                    least_selling.append({
                        "name": str(name),
                        "metric_value": round(float(val), 2),
                        "metric_label": metric_label,
                        "rank": idx
                    })
        except Exception as e:
            print(f"Retail item ranking error: {e}")

    # 2. Store-wise Sales Performance
    store_col = None
    for c in cols:
        low = c.lower()
        if any(k in low for k in ["store_name", "store_id", "branch", "location", "outlet", "city", "region"]):
            store_col = c
            break
            
    if store_col:
        try:
            if amt_col and pd.to_numeric(df[amt_col], errors='coerce').notnull().any():
                df_calc = df.copy()
                df_calc['_rev'] = pd.to_numeric(df_calc[amt_col], errors='coerce').fillna(0)
                store_grp = df_calc.groupby(store_col)['_rev'].sum().sort_values(ascending=False).head(8)
                store_sales = [{"store": str(k), "sales": round(float(v), 2), "unit": "$"} for k, v in store_grp.items()]
            else:
                store_grp = df[store_col].value_counts().head(8)
                store_sales = [{"store": str(k), "sales": int(v), "unit": "Orders"} for k, v in store_grp.items()]
        except Exception as e:
            print(f"Store sales error: {e}")

    # 3. Customer Purchase Patterns
    cust_col = None
    for c in cols:
        low = c.lower()
        if any(k in low for k in ["customer_name", "customer_id", "client", "buyer", "shopper", "email"]):
            cust_col = c
            break
            
    if cust_col:
        try:
            cust_counts = df[cust_col].value_counts()
            repeat_buyers = int((cust_counts > 1).sum())
            one_time = int((cust_counts == 1).sum())
            total_customers = len(cust_counts)
            repeat_rate = round((repeat_buyers / max(1, total_customers)) * 100, 1)
            
            customer_patterns = [
                {"segment": "Repeat Customers", "count": repeat_buyers, "share": f"{repeat_rate}%"},
                {"segment": "One-Time Shoppers", "count": one_time, "share": f"{round(100 - repeat_rate, 1)}%"},
                {"segment": "Total Active Shoppers", "count": total_customers, "share": "100%"}
            ]
        except Exception as e:
            print(f"Customer pattern error: {e}")

    # 4. Sales & Demand Forecast
    date_col = None
    for c in cols:
        low = c.lower()
        if any(k in low for k in ["date", "order_date", "invoice_date", "timestamp", "day"]):
            date_col = c
            break

    try:
        if date_col and (amt_col or qty_col):
            val_col = amt_col if amt_col else qty_col
            df_time = df.copy()
            df_time['_val'] = pd.to_numeric(df_time[val_col], errors='coerce').fillna(1)
            df_time['_dt'] = pd.to_datetime(df_time[date_col], errors='coerce')
            df_time = df_time.dropna(subset=['_dt']).sort_values('_dt')
            
            if len(df_time) >= 3:
                daily = df_time.groupby(df_time['_dt'].dt.strftime('%Y-%m-%d'))['_val'].sum().reset_index()
                hist_vals = daily['_val'].tolist()
                dates = daily['_dt'].tolist()
                
                for d, v in zip(dates[-6:], hist_vals[-6:]):
                    sales_forecast.append({
                        "period": str(d),
                        "value": round(float(v), 2),
                        "type": "Historical"
                    })
                    
                recent_avg = float(np.mean(hist_vals[-3:]))
                for i in range(1, 4):
                    proj_val = round(recent_avg * (1.05 ** i), 2)
                    sales_forecast.append({
                        "period": f"Projected +{i}d",
                        "value": proj_val,
                        "type": "Projected Demand"
                    })
    except Exception as e:
        print(f"Sales forecast error: {e}")

    # 5. Inventory Recommendations
    if best_selling:
        top_name = best_selling[0]["name"]
        inventory_recs.append({
            "action": "Restock Priority",
            "item": top_name,
            "badge": "High Demand",
            "type": "urgent",
            "reason": f"Top performing item with {best_selling[0]['metric_value']} {best_selling[0]['metric_label']}. Recommend increasing safety stock by 20%."
        })
        
    if least_selling:
        bot_name = least_selling[0]["name"]
        inventory_recs.append({
            "action": "Clearance / Promotion",
            "item": bot_name,
            "badge": "Slow Moving",
            "type": "warning",
            "reason": f"Low demand velocity ({least_selling[0]['metric_value']} {least_selling[0]['metric_label']}). Recommend bundling or promotional discount."
        })

    # 6. Summary Metrics
    summary_metrics.append({
        "label": "Retail Dataset Type",
        "value": entity_label.split(" ")[0] if " " in entity_label else entity_label,
        "subtext": entity_label,
        "trend": "neutral"
    })
    
    if best_selling:
        summary_metrics.append({
            "label": "Top Best-Selling Item",
            "value": best_selling[0]["name"][:20] + ("..." if len(best_selling[0]["name"]) > 20 else ""),
            "subtext": f"{best_selling[0]['metric_value']} {best_selling[0]['metric_label']}",
            "trend": "up"
        })
        
    if least_selling:
        summary_metrics.append({
            "label": "Slowest Moving Item",
            "value": least_selling[0]["name"][:20] + ("..." if len(least_selling[0]["name"]) > 20 else ""),
            "subtext": f"{least_selling[0]['metric_value']} {least_selling[0]['metric_label']}",
            "trend": "down"
        })
        
    if store_sales:
        summary_metrics.append({
            "label": "Leading Store Branch",
            "value": store_sales[0]["store"][:20],
            "subtext": f"{store_sales[0]['sales']} {store_sales[0]['unit']}",
            "trend": "up"
        })

    return {
        "entity_type": entity_type,
        "entity_label": entity_label,
        "entity_breakdown": {
            "store_fields": type_info["store_fields"],
            "item_fields": type_info["item_fields"],
            "customer_fields": type_info["customer_fields"],
            "transaction_fields": type_info["transaction_fields"]
        },
        "best_selling_items": best_selling,
        "least_selling_items": least_selling,
        "store_sales": store_sales,
        "customer_patterns": customer_patterns,
        "sales_forecast": sales_forecast,
        "inventory_recommendations": inventory_recs,
        "summary_metrics": summary_metrics
    }
