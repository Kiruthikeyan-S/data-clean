"""
Record Serializer Module for RAG Knowledge Base

Converts structured records (Store, Item, Customer, Transaction, General)
into high-density, semantic, searchable text for vector embedding.
"""
from __future__ import annotations
import re
from typing import Dict, Any, List, Optional

NULL_VALUES = {"", "null", "none", "nan", "nat", "n/a", "na", "nil", "undefined", "-", "--", "#n/a", "unknown"}


def is_valid_value(val: Any) -> bool:
    """Checks if a value is non-null and meaningful for serialization."""
    if val is None:
        return False
    val_str = str(val).strip().lower()
    return val_str not in NULL_VALUES


def clean_val_str(val: Any) -> str:
    """Cleans and formats cell value for serialization."""
    s = str(val).strip()
    if re.match(r"^\d+\.0+$", s):
        s = s.split(".")[0]
    return " ".join(s.split())


def serialize_record_to_text(record: Dict[str, Any], entity_type: str = "general") -> str:
    """
    Serializes a single record into standardized, searchable text
    tailored to the entity type (Store, Item, Customer, Transaction).
    
    Example Output:
    "Customer | ID: CUS001 | Name: Naveen Singh | Phone: +919876543210 | Email: naveen@example.com | City: Chennai | Address: 12 Anna Nagar"
    """
    if not record or not isinstance(record, dict):
        return ""

    entity_label = entity_type.capitalize() if entity_type else "Entity"
    parts = [f"Entity: {entity_label}"]

    # Priority field order per entity
    priority_keys_map = {
        "customer": [
            "customer_id", "cust_id", "id", "code",
            "name", "full_name", "customer_name", "first_name", "last_name",
            "phone", "mobile", "contact", "customer_phone",
            "email", "customer_email",
            "address", "street", "city", "state", "pin", "pincode", "zip_code", "postal_code", "country",
            "age", "gender", "dob"
        ],
        "store": [
            "store_id", "branch_id", "outlet_id", "id", "code",
            "store_name", "branch_name", "outlet_name", "name",
            "city", "state", "address", "location", "pin", "pincode", "zip_code", "postal_code",
            "manager", "manager_name", "phone", "email", "store_type", "region"
        ],
        "item": [
            "product_id", "item_id", "sku", "barcode", "upc", "ean", "id", "code",
            "product_name", "item_name", "name", "title",
            "category", "subcategory", "brand", "manufacturer",
            "price", "unit_price", "selling_price", "mrp", "cost_price",
            "stock", "quantity", "inventory"
        ],
        "transaction": [
            "transaction_id", "order_id", "invoice_id", "bill_id", "id",
            "date", "transaction_date", "order_date",
            "customer_id", "store_id", "item_id", "product_id",
            "total_amount", "amount", "price", "quantity", "qty", "payment_method"
        ]
    }

    priority_keys = priority_keys_map.get(entity_type.lower(), [])
    handled_keys = set()

    # 1. Add priority fields first in consistent semantic order
    for p_key in priority_keys:
        for k, v in record.items():
            k_lower = str(k).strip().lower().replace("-", "_").replace(" ", "_")
            if k_lower == p_key and is_valid_value(v):
                label = str(k).replace("_", " ").title()
                parts.append(f"{label}: {clean_val_str(v)}")
                handled_keys.add(k)
                break

    # 2. Add remaining fields
    for k, v in record.items():
        if k not in handled_keys and not str(k).startswith("_") and is_valid_value(v):
            label = str(k).replace("_", " ").title()
            parts.append(f"{label}: {clean_val_str(v)}")

    return " | ".join(parts)


def serialize_schema_alias(raw_header: str, canonical_field: str, entity_type: str) -> str:
    """Serializes a schema column alias into searchable text for Schema Knowledge RAG."""
    clean_raw = raw_header.strip().replace("_", " ").replace("-", " ")
    clean_canon = canonical_field.strip().replace("_", " ")
    return f"Column Header: '{clean_raw}' represents canonical field '{clean_canon}' in {entity_type} schema."
