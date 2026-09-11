from typing import List, Dict, Any, Optional

ENTITY_COLUMNS = {
    "STORE": {
        "store_id", "store_name", "store_code", "branch", "branch_name", "branch_id",
        "location", "region", "city", "state", "country", "manager_name", "store_type",
        "store_manager", "store_location", "postal_code", "zip_code", "outlet_id"
    },
    "ITEM": {
        "item_id", "product_id", "sku", "item_code", "product_code", "product_name",
        "item_name", "item_description", "product_description", "category", "sub_category",
        "department", "brand", "unit_price", "price", "cost", "unit_cost", "stock",
        "stock_quantity", "inventory", "inventory_level", "supplier", "barcode", "size", "color"
    },
    "CUSTOMER": {
        "customer_id", "client_id", "user_id", "customer_name", "client_name", "full_name",
        "first_name", "last_name", "email", "phone", "contact", "gender", "age",
        "address", "city", "state", "country", "postal_code", "zip", "loyalty_tier",
        "segment", "membership_type", "registration_date", "dob", "date_of_birth"
    },
    "TRANSACTION": {
        "transaction_id", "order_id", "invoice_id", "invoice_no", "receipt_no", "bill_no",
        "date", "order_date", "transaction_date", "invoice_date", "timestamp", "time",
        "quantity", "qty", "units_sold", "unit_price", "subtotal", "tax", "discount",
        "total_amount", "grand_total", "net_amount", "amount", "payment_method", "payment_mode",
        "status", "order_status"
    }
}

def classify_column(column_name: str) -> Dict[str, Any]:
    """
    Determines the most probable retail entity domain for a given column name.
    """
    clean_col = column_name.lower().strip().replace(" ", "_").replace("-", "_")
    
    # Exact or substring match in entity sets
    for entity, cols in ENTITY_COLUMNS.items():
        if clean_col in cols:
            return {"entity": entity, "confidence": 0.95, "matched_rule": f"exact_{clean_col}"}
            
    # Fuzzy keyword heuristics
    if any(k in clean_col for k in ["store", "branch", "outlet", "region"]):
        return {"entity": "STORE", "confidence": 0.85, "matched_rule": "keyword_store"}
    if any(k in clean_col for k in ["product", "item", "sku", "brand", "category", "stock", "inventory", "barcode"]):
        return {"entity": "ITEM", "confidence": 0.85, "matched_rule": "keyword_item"}
    if any(k in clean_col for k in ["customer", "client", "user", "member", "loyalty", "email", "phone", "dob"]):
        return {"entity": "CUSTOMER", "confidence": 0.85, "matched_rule": "keyword_customer"}
    if any(k in clean_col for k in ["order", "invoice", "trans", "receipt", "qty", "quantity", "discount", "payment", "amount", "sale"]):
        return {"entity": "TRANSACTION", "confidence": 0.85, "matched_rule": "keyword_transaction"}
        
    return {"entity": "GENERAL", "confidence": 0.5, "matched_rule": "fallback"}

def classify_dataset_entities(columns: List[str]) -> Dict[str, Any]:
    """
    Analyzes all columns of a dataset to categorize its schema across Store, Item, Customer, and Transaction domains.
    Determines primary dataset type.
    """
    if not columns:
        return {
            "primary_entity": "GENERAL",
            "entity_breakdown": {},
            "column_entity_map": {}
        }
        
    column_map = {}
    counts = {"STORE": 0, "ITEM": 0, "CUSTOMER": 0, "TRANSACTION": 0, "GENERAL": 0}
    
    for col in columns:
        res = classify_column(col)
        column_map[col] = res["entity"]
        counts[res["entity"]] = counts.get(res["entity"], 0) + 1
        
    # Primary entity is the non-general category with highest count
    domain_counts = {k: v for k, v in counts.items() if k != "GENERAL"}
    if domain_counts and max(domain_counts.values()) > 0:
        sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
        top_domain, top_count = sorted_domains[0]
        
        # If multiple domains have significant columns, it is a UNIFIED or TRANSACTION_MERGED dataset
        active_domains = [d for d, c in domain_counts.items() if c > 0]
        if len(active_domains) >= 3 or ("TRANSACTION" in active_domains and len(active_domains) >= 2):
            primary_entity = "UNIFIED_WAREHOUSE"
        else:
            primary_entity = top_domain
    else:
        primary_entity = "GENERAL"
        
    return {
        "primary_entity": primary_entity,
        "entity_breakdown": counts,
        "column_entity_map": column_map
    }
