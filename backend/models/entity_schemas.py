import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Pattern
from enum import Enum

class EntityType(str, Enum):
    """Business entity types."""
    STORE = "store"
    ITEM = "item"
    CUSTOMER = "customer"
    TRANSACTION = "transaction"

CONFIDENCE_THRESHOLD = 0.70

@dataclass
class EntitySchema:
    """
    Schema definition for a business entity used in dataset classification.
    
    Attributes:
        name: The canonical identifier for the entity type.
        display_name: Human-readable name for UI presentation.
        icon: Icon identifier for UI presentation.
        strong_keywords: Very specific column names that strongly indicate this entity (weight 1.0).
        medium_keywords: Moderately specific column names (weight 0.6).
        weak_keywords: Ambiguous names that could belong to multiple entities (weight 0.3).
        aliases: Maps of equivalent column names (e.g. store_id = branch_id).
        value_patterns: Regex patterns for cell values that indicate this entity.
        co_occurrence_rules: Lists of column combinations that confirm this entity type.
        foreign_key_columns: Columns that appear as references in other entities.
    """
    name: str
    display_name: str
    icon: str
    strong_keywords: Set[str] = field(default_factory=set)
    medium_keywords: Set[str] = field(default_factory=set)
    weak_keywords: Set[str] = field(default_factory=set)
    aliases: Dict[str, str] = field(default_factory=dict)
    value_patterns: List[Pattern] = field(default_factory=list)
    co_occurrence_rules: List[Set[str]] = field(default_factory=list)
    foreign_key_columns: Set[str] = field(default_factory=set)


def get_entity_schemas() -> Dict[str, EntitySchema]:
    """
    Returns the comprehensive schema definitions for Store, Item, Customer, and Transaction entities.
    
    Returns:
        A dictionary mapping EntityType values to their corresponding EntitySchema definitions.
    """
    
    store_schema = EntitySchema(
        name=EntityType.STORE.value,
        display_name="Store / Branch",
        icon="storefront",
        strong_keywords={
            "store_id", "store_name", "store_code", "branch_id", "branch_name", "branch_code",
            "outlet_id", "outlet_name", "outlet_code", "warehouse_id", "warehouse_name",
            "store_location", "store_address", "store_city", "store_state", "store_country",
            "store_phone", "store_email", "store_type", "store_status", "store_region",
            "store_area", "store_manager", "store_size", "store_format", "store_opening_date",
            "branch_manager", "branch_location"
        },
        medium_keywords={
            "branch", "outlet", "warehouse", "region", "area", "zone", "district",
            "territory", "sq_ft", "footfall", "location_type"
        },
        weak_keywords={
            "city", "state", "country", "address", "location", "region", "area", "zone",
            "pin_code", "zip_code", "postal_code"
        },
        aliases={
            "branch_id": "store_id",
            "outlet_id": "store_id",
            "store_code": "store_id",
            "branch_code": "store_id",
            "outlet_code": "store_id",
            "branch_name": "store_name",
            "outlet_name": "store_name"
        },
        value_patterns=[
            re.compile(r"^STR-\d{3,5}$", re.IGNORECASE),
            re.compile(r"^BRN-\d{3,5}$", re.IGNORECASE)
        ],
        co_occurrence_rules=[
            {"store_id", "store_name", "city"},
            {"branch_id", "location", "manager"},
            {"outlet_id", "sq_ft"}
        ],
        foreign_key_columns={"store_id", "branch_id", "outlet_id"}
    )
    
    item_schema = EntitySchema(
        name=EntityType.ITEM.value,
        display_name="Item / Product",
        icon="inventory_2",
        strong_keywords={
            "product_id", "product_name", "product_code", "item_id", "item_name", "item_code",
            "sku", "sku_id", "sku_code", "barcode", "upc", "ean", "asin", "product_category",
            "product_type", "product_description", "product_brand", "product_price",
            "item_price", "unit_price", "cost_price", "selling_price", "mrp", "msrp",
            "list_price", "product_weight", "product_size", "product_color", "item_category",
            "item_type", "item_description"
        },
        medium_keywords={
            "category", "subcategory", "sub_category", "brand", "manufacturer", "supplier",
            "vendor", "unit", "uom", "unit_of_measure", "weight", "size", "color", "variant",
            "model", "material", "stock", "inventory", "reorder_level", "min_stock", "max_stock"
        },
        weak_keywords={
            "price", "cost", "name", "description", "type", "status", "code", "image",
            "image_url", "thumbnail"
        },
        aliases={
            "item_id": "product_id",
            "sku_id": "product_id",
            "sku": "product_id",
            "item_name": "product_name",
            "item_code": "product_code",
            "product_price": "unit_price",
            "selling_price": "unit_price"
        },
        value_patterns=[
            re.compile(r"^\d{12,13}$"),  # UPC/EAN approximation
            re.compile(r"^[A-Z0-9]{10}$", re.IGNORECASE)  # ASIN approximation
        ],
        co_occurrence_rules=[
            {"product_id", "product_name", "price"},
            {"sku", "category", "brand"},
            {"item_id", "description", "unit_price"}
        ],
        foreign_key_columns={"product_id", "item_id", "sku"}
    )
    
    customer_schema = EntitySchema(
        name=EntityType.CUSTOMER.value,
        display_name="Customer / Client",
        icon="person",
        strong_keywords={
            "customer_id", "customer_name", "customer_email", "customer_phone",
            "customer_address", "cust_id", "cust_name", "client_id", "client_name",
            "member_id", "member_name", "membership_id", "loyalty_id", "customer_code",
            "shopper_id", "buyer_id", "patron_id", "customer_city", "customer_state",
            "customer_country", "customer_age", "customer_gender", "customer_dob",
            "customer_type", "customer_segment", "customer_since", "registration_date",
            "signup_date", "first_purchase_date"
        },
        medium_keywords={
            "email", "phone", "mobile", "contact", "gender", "age", "dob", "date_of_birth",
            "birth_date", "membership", "loyalty", "loyalty_points", "reward_points",
            "segment", "tier", "first_name", "last_name", "full_name", "middle_name"
        },
        weak_keywords={
            "name", "address", "city", "state", "country", "pin_code", "zip_code", "postal_code"
        },
        aliases={
            "cust_id": "customer_id",
            "client_id": "customer_id",
            "member_id": "customer_id",
            "shopper_id": "customer_id",
            "cust_name": "customer_name",
            "client_name": "customer_name"
        },
        value_patterns=[
            re.compile(r"^[^@]+@[^@]+\.[^@]+$"),  # Email
            re.compile(r"^\+?\d{10,15}$")  # Phone
        ],
        co_occurrence_rules=[
            {"customer_id", "first_name", "last_name"},
            {"client_id", "email", "phone"},
            {"member_id", "loyalty_points"}
        ],
        foreign_key_columns={"customer_id", "client_id", "member_id", "cust_id"}
    )
    
    transaction_schema = EntitySchema(
        name=EntityType.TRANSACTION.value,
        display_name="Transaction / Sales",
        icon="receipt_long",
        strong_keywords={
            "transaction_id", "order_id", "invoice_id", "receipt_id", "bill_id", "sale_id",
            "purchase_id", "order_number", "invoice_number", "bill_number", "purchase_date",
            "order_date", "transaction_date", "sale_date", "invoice_date", "billing_date",
            "order_time", "transaction_time", "total_amount", "order_total", "grand_total",
            "subtotal", "net_amount", "gross_amount", "tax_amount", "discount_amount",
            "payment_method", "payment_type", "payment_status", "order_status", "delivery_date",
            "shipping_date", "delivery_status", "return_date", "refund_amount"
        },
        medium_keywords={
            "quantity", "qty", "units", "units_sold", "items_purchased", "line_total",
            "line_amount", "tax", "discount", "discount_percent", "shipping_cost",
            "delivery_charge", "tip", "coupon", "coupon_code", "promo_code", "channel",
            "sales_channel", "cashier", "sales_rep", "payment_mode"
        },
        weak_keywords={
            "date", "amount", "total", "status", "type", "notes", "remarks", "comments"
        },
        aliases={
            "invoice_id": "transaction_id",
            "receipt_id": "transaction_id",
            "sale_id": "transaction_id",
            "order_id": "transaction_id",
            "order_number": "transaction_id",
            "invoice_number": "transaction_id"
        },
        value_patterns=[
            re.compile(r"^TXN-\d+$", re.IGNORECASE),
            re.compile(r"^ORD-\d+$", re.IGNORECASE),
            re.compile(r"^INV-\d+$", re.IGNORECASE)
        ],
        co_occurrence_rules=[
            {"transaction_id", "order_date", "total_amount"},
            {"invoice_id", "customer_id", "amount"},
            {"order_id", "product_id", "quantity"}
        ],
        foreign_key_columns={"transaction_id", "order_id", "invoice_id"}
    )
    
    return {
        EntityType.STORE.value: store_schema,
        EntityType.ITEM.value: item_schema,
        EntityType.CUSTOMER.value: customer_schema,
        EntityType.TRANSACTION.value: transaction_schema,
    }
