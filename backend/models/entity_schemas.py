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
            "selling_price": "unit_price",
            "cat": "category",
            "dept": "category"
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


@dataclass
class CanonicalField:
    """
    Specification for a canonical column in a standardized business schema.
    """
    name: str
    field_type: str  # 'id', 'text_title', 'text', 'date', 'numeric', 'boolean', 'email', 'phone', 'postal_code'
    aliases: Set[str] = field(default_factory=set)
    description: str = ""
    is_primary_key: bool = False


CANONICAL_SCHEMAS: Dict[str, Dict[str, CanonicalField]] = {
    EntityType.STORE.value: {
        "store_id": CanonicalField(
            name="store_id",
            field_type="id",
            aliases={"store_id", "store_code", "store_num", "store_number", "branch_id", "branch_code", "outlet_id", "outlet_code", "warehouse_id", "warehouse_code", "id", "store_no", "s_id", "sid", "str_id"},
            description="Unique store or branch identifier",
            is_primary_key=True
        ),
        "store_name": CanonicalField(
            name="store_name",
            field_type="text_title",
            aliases={"store_name", "store_title", "branch_name", "outlet_name", "warehouse_name", "location_name", "store", "name", "branch"},
            description="Official name of the store location"
        ),
        "address": CanonicalField(
            name="address",
            field_type="text",
            aliases={"address", "street", "address_street", "store_address", "address_line1", "address_line_1", "location_address", "street_address", "addr"},
            description="Street address of the store"
        ),
        "city": CanonicalField(
            name="city",
            field_type="text_title",
            aliases={"city", "store_city", "address_city", "town", "district", "municipality"},
            description="City where the store is located"
        ),
        "state": CanonicalField(
            name="state",
            field_type="text_title",
            aliases={"state", "store_state", "address_state", "province", "region"},
            description="State or province code/name"
        ),
        "postal_code": CanonicalField(
            name="postal_code",
            field_type="postal_code",
            aliases={"postal_code", "address_postal_code", "zipcode", "zip_code", "address_zip", "zip", "pin_code", "pincode", "pin", "postcode"},
            description="Postal or ZIP code"
        ),
        "country": CanonicalField(
            name="country",
            field_type="text_title",
            aliases={"country", "store_country", "address_country", "nation"},
            description="Country where the store is located"
        ),
        "phone": CanonicalField(
            name="phone",
            field_type="phone",
            aliases={"phone", "store_phone", "contact", "telephone", "mobile", "phone_number", "contact_number"},
            description="Store contact phone number"
        ),
        "opened_on": CanonicalField(
            name="opened_on",
            field_type="date",
            aliases={"opened_on", "opening_date", "opened_date", "store_opening_date", "established_date", "launch_date", "open_date"},
            description="Date when the store opened (YYYY-MM-DD)"
        ),
        "active": CanonicalField(
            name="active",
            field_type="boolean",
            aliases={"active", "isactive", "is_active", "status", "store_status", "operational_status"},
            description="Whether the store is currently operational"
        )
    },

    EntityType.ITEM.value: {
        "item_id": CanonicalField(
            name="item_id",
            field_type="id",
            aliases={"item_id", "product_id", "sku", "sku_id", "sku_code", "prod_code", "product_code", "item_code", "barcode", "upc", "ean", "asin", "id", "item_no", "p_id", "pid", "prod_id"},
            description="Unique product SKU or item identifier",
            is_primary_key=True
        ),
        "item_name": CanonicalField(
            name="item_name",
            field_type="text_title",
            aliases={"item_name", "product_name", "title", "product", "product_title", "item_title", "description", "item_description", "name"},
            description="Product or catalog item title"
        ),
        "category": CanonicalField(
            name="category",
            field_type="text_title",
            aliases={"category", "product_category", "item_category", "dept", "department", "sub_category", "subcategory", "group", "cat", "cat_name", "category_name"},
            description="Merchandise category or department"
        ),
        "selling_price": CanonicalField(
            name="selling_price",
            field_type="numeric",
            aliases={"selling_price", "price", "retail_price", "price_usd", "unit_price", "product_price", "item_price", "mrp", "msrp", "list_price", "rate", "cost_per_unit"},
            description="Customer retail selling price"
        ),
        "cost_price": CanonicalField(
            name="cost_price",
            field_type="numeric",
            aliases={"cost_price", "cost", "purchase_price", "wholesale_price", "buying_price", "unit_cost"},
            description="Wholesale inventory acquisition cost"
        ),
        "stock_quantity": CanonicalField(
            name="stock_quantity",
            field_type="numeric",
            aliases={"stock_quantity", "inventory", "in_stock", "stock_qty", "stock", "quantity", "qty", "units_in_stock", "available_stock", "reorder_level", "stock_count", "units", "units_in_stock"},
            description="Units currently on hand in inventory"
        ),
        "available": CanonicalField(
            name="available",
            field_type="boolean",
            aliases={"available", "is_available", "active", "is_active", "status", "in_stock_bool"},
            description="Whether the item is available for purchase"
        )
    },

    EntityType.CUSTOMER.value: {
        "customer_id": CanonicalField(
            name="customer_id",
            field_type="id",
            aliases={"customer_id", "cust_id", "client_id", "member_id", "user_id", "customer_code", "shopper_id", "buyer_id", "patron_id", "id", "c_id", "cid"},
            description="Unique customer account identifier",
            is_primary_key=True
        ),
        "full_name": CanonicalField(
            name="full_name",
            field_type="text_title",
            aliases={"full_name", "name", "customer_name", "cust_name", "client_name", "member_name"},
            description="Full name of the customer"
        ),
        "email": CanonicalField(
            name="email",
            field_type="email",
            aliases={"email", "contact_email", "contact_email", "contact.email", "customer_email", "cust_email", "email_address", "mail"},
            description="Customer email address"
        ),
        "phone": CanonicalField(
            name="phone",
            field_type="phone",
            aliases={"phone", "mobile", "telephone", "customer_phone", "cust_phone", "contact", "cell", "phone_number", "contact_number"},
            description="Customer contact phone number"
        ),
        "address": CanonicalField(
            name="address",
            field_type="text",
            aliases={"address", "street", "customer_address", "address_street", "address_line1", "addr"},
            description="Customer street address"
        ),
        "city": CanonicalField(
            name="city",
            field_type="text_title",
            aliases={"city", "customer_city", "address_city", "town"},
            description="Customer city"
        ),
        "state": CanonicalField(
            name="state",
            field_type="text_title",
            aliases={"state", "customer_state", "address_state", "province"},
            description="Customer state"
        ),
        "postal_code": CanonicalField(
            name="postal_code",
            field_type="postal_code",
            aliases={"postal_code", "customer_postal_code", "customer_zip", "zip", "zipcode", "pin", "pincode"},
            description="Customer postal/zip code"
        ),
        "country": CanonicalField(
            name="country",
            field_type="text_title",
            aliases={"country", "customer_country", "address_country"},
            description="Customer country"
        ),
        "registered_on": CanonicalField(
            name="registered_on",
            field_type="date",
            aliases={"registered_on", "registered", "signup_date", "member_since", "customer_since", "registration_date", "date_of_registration", "created_at"},
            description="Account creation or signup date (YYYY-MM-DD)"
        ),
        "loyalty_tier": CanonicalField(
            name="loyalty_tier",
            field_type="text_title",
            aliases={"loyalty_tier", "tier", "segment", "membership_tier", "customer_type", "membership"},
            description="Customer loyalty tier (Bronze, Silver, Gold, Platinum)"
        ),
        "loyalty_points": CanonicalField(
            name="loyalty_points",
            field_type="numeric",
            aliases={"loyalty_points", "reward_points", "points", "rewards"},
            description="Accumulated loyalty reward points"
        ),
        "status": CanonicalField(
            name="status",
            field_type="boolean",
            aliases={"status", "is_active", "active", "account_status"},
            description="Whether customer account is active"
        )
    },

    EntityType.TRANSACTION.value: {
        "transaction_id": CanonicalField(
            name="transaction_id",
            field_type="id",
            aliases={"transaction_id", "txn_id", "order_id", "invoice_id", "receipt_id", "bill_id", "sale_id", "purchase_id", "order_number", "invoice_number", "bill_number", "id", "t_id", "tid", "tx_id"},
            description="Unique transaction or invoice number",
            is_primary_key=True
        ),
        "store_id": CanonicalField(
            name="store_id",
            field_type="id",
            aliases={"store_id", "branch_id", "outlet_id", "store_code", "branch_code"},
            description="Reference to the Store location"
        ),
        "item_id": CanonicalField(
            name="item_id",
            field_type="id",
            aliases={"item_id", "product_id", "sku", "product_code", "item_code"},
            description="Reference to the Product item"
        ),
        "customer_id": CanonicalField(
            name="customer_id",
            field_type="id",
            aliases={"customer_id", "cust_id", "client_id", "member_id"},
            description="Reference to the Customer"
        ),
        "purchase_date": CanonicalField(
            name="purchase_date",
            field_type="date",
            aliases={"purchase_date", "transaction_date", "txn_date", "order_date", "sale_date", "invoice_date", "billing_date", "date", "created_at", "timestamp"},
            description="Date and time of purchase (YYYY-MM-DD)"
        ),
        "quantity": CanonicalField(
            name="quantity",
            field_type="numeric",
            aliases={"quantity", "qty", "units", "units_sold", "items_purchased", "count"},
            description="Number of units purchased"
        ),
        "unit_price": CanonicalField(
            name="unit_price",
            field_type="numeric",
            aliases={"unit_price", "price", "item_price", "rate", "cost_per_unit"},
            description="Price per single unit"
        ),
        "total_amount": CanonicalField(
            name="total_amount",
            field_type="numeric",
            aliases={"total_amount", "order_total", "grand_total", "subtotal", "net_amount", "gross_amount", "total", "amount", "final_amount"},
            description="Final transaction total amount"
        ),
        "payment_method": CanonicalField(
            name="payment_method",
            field_type="text_title",
            aliases={"payment_method", "payment_type", "payment_mode", "pay_type", "tender_type", "payment"},
            description="Payment method used (Credit Card, Cash, UPI)"
        )
    }
}


def get_canonical_fields(entity_type: str) -> Dict[str, CanonicalField]:
    """Returns canonical field dictionary for given entity type."""
    return CANONICAL_SCHEMAS.get(entity_type.lower(), {})

