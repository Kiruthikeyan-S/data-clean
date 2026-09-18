import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Pattern
from enum import Enum

class EntityType(str, Enum):
    """Business entity and domain types."""
    STORE = "store"
    ITEM = "item"
    CUSTOMER = "customer"
    TRANSACTION = "transaction"
    CAR = "car"
    INVOICE = "invoice"
    EMPLOYEE = "employee"
    STUDENT = "student"
    MEDICAL = "medical"

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

    car_schema = EntitySchema(
        name=EntityType.CAR.value,
        display_name="Vehicle / Automotive",
        icon="directions_car",
        strong_keywords={
            "vin", "vehicle_identification_number", "make", "model", "car_model", "vehicle_model",
            "mileage", "odometer", "odometer_reading", "license_plate", "plate_number", "plate_no",
            "engine_no", "engine_number", "transmission", "fuel_type", "body_style", "vehicle_id",
            "car_name", "trim", "doors", "seating_capacity", "cubic_capacity", "chassis_number", "chassis_no"
        },
        medium_keywords={
            "vehicle", "car", "auto", "engine", "gearbox", "horsepower", "torque", "exterior_color",
            "interior_color", "cylinders", "displacement", "mpg", "kpl", "fuel_economy"
        },
        weak_keywords={
            "year", "price", "color", "status", "type", "description", "id", "city", "state", "brand"
        },
        aliases={
            "vehicle_identification_number": "vin",
            "chassis_number": "vin",
            "chassis_no": "vin",
            "car_model": "model",
            "plate_number": "license_plate",
            "plate_no": "license_plate",
            "odometer": "mileage",
            "odometer_reading": "mileage"
        },
        value_patterns=[
            re.compile(r"^[A-HJ-NPR-Z0-9]{17}$", re.IGNORECASE),  # Standard 17-char VIN
            re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$", re.IGNORECASE)  # Plate number format
        ],
        co_occurrence_rules=[
            {"vin", "make", "model"},
            {"make", "model", "year", "mileage"},
            {"license_plate", "engine_no"}
        ],
        foreign_key_columns={"vin", "license_plate"}
    )

    invoice_schema = EntitySchema(
        name=EntityType.INVOICE.value,
        display_name="Invoice / Billing Document",
        icon="receipt_long",
        strong_keywords={
            "invoice_no", "invoice_num", "invoice_number", "bill_to", "billed_to", "invoice_date",
            "due_date", "vendor_name", "supplier_name", "tax_amount", "tax_rate", "po_number",
            "purchase_order", "payment_terms", "gstin", "vat_number", "subtotal"
        },
        medium_keywords={
            "invoice", "billing", "bill", "vendor", "supplier", "tax", "gst", "vat", "remit_to"
        },
        weak_keywords={
            "date", "total", "amount", "discount", "notes", "status", "description"
        },
        aliases={
            "invoice_num": "invoice_no",
            "invoice_number": "invoice_no",
            "bill_number": "invoice_no",
            "billed_to": "bill_to"
        },
        value_patterns=[
            re.compile(r"^INV[-\s]?\d+$", re.IGNORECASE),
            re.compile(r"^BILL[-\s]?\d+$", re.IGNORECASE)
        ],
        co_occurrence_rules=[
            {"invoice_no", "invoice_date", "total_amount"},
            {"bill_to", "vendor_name", "total_amount"}
        ],
        foreign_key_columns={"invoice_no"}
    )

    employee_schema = EntitySchema(
        name=EntityType.EMPLOYEE.value,
        display_name="Employee / HR Record",
        icon="badge",
        strong_keywords={
            "emp_id", "employee_id", "employee_name", "emp_name", "department", "designation",
            "job_title", "salary", "hire_date", "joining_date", "date_of_joining", "manager_id",
            "work_email", "emp_email", "payroll", "employment_status", "job_role"
        },
        medium_keywords={
            "employee", "staff", "dept", "experience", "qualification", "supervisor", "grade"
        },
        weak_keywords={
            "name", "email", "phone", "address", "city", "state", "status", "age", "gender"
        },
        aliases={
            "employee_id": "emp_id",
            "employee_name": "name",
            "emp_name": "name",
            "date_of_joining": "joining_date",
            "job_title": "designation"
        },
        value_patterns=[
            re.compile(r"^EMP[-\s]?\d+$", re.IGNORECASE)
        ],
        co_occurrence_rules=[
            {"emp_id", "department", "salary"},
            {"employee_id", "designation", "hire_date"}
        ],
        foreign_key_columns={"emp_id", "manager_id"}
    )

    student_schema = EntitySchema(
        name=EntityType.STUDENT.value,
        display_name="Academic / Course Syllabus & Student Record",
        icon="school",
        strong_keywords={
            "student_id", "roll_no", "reg_no", "roll_number", "registration_no", "student_name",
            "cgpa", "gpa", "course", "major", "semester", "sem", "attendance_pct", "enrollment_date",
            "graduation_year", "academic_year", "batch_year", "course_code", "subject_code",
            "course_title", "course_name", "subject_name", "credits", "credit", "syllabus",
            "curriculum", "lecture_hours", "tutorial_hours", "practical_hours", "prerequisites",
            "course_category", "course_type", "admission_no", "paper_code", "paper_name"
        },
        medium_keywords={
            "student", "class", "section", "subject", "marks", "exam_score", "grade",
            "module", "unit", "topic", "topics", "lecture", "tutorial", "practical", "lab",
            "faculty", "instructor", "professor", "branch", "stream", "program", "degree",
            "regulations", "scheme", "internal_marks", "end_sem", "elective"
        },
        weak_keywords={
            "name", "code", "title", "dob", "email", "phone", "department", "status",
            "age", "gender", "category", "type", "hours", "description"
        },
        aliases={
            "course_name": "course_title",
            "subject_name": "course_title",
            "subject": "course_title",
            "subject_code": "course_code",
            "sem": "semester",
            "credit": "credits",
            "roll_number": "roll_no",
            "registration_no": "reg_no",
            "student_name": "name",
            "gpa": "cgpa"
        },
        value_patterns=[
            re.compile(r"^STU[-\s]?\d+$", re.IGNORECASE),
            re.compile(r"^[A-Z]{2,4}\s?\d{3,5}[A-Z]?$", re.IGNORECASE),  # e.g. CS301, AI101, AD8302
            re.compile(r"^(?:Semester|Sem)[-\s]?(?:[1-8]|I|II|III|IV|V|VI|VII|VIII)$", re.IGNORECASE)
        ],
        co_occurrence_rules=[
            {"course_code", "course_title", "credits"},
            {"course_code", "course_name", "credits"},
            {"subject_code", "subject_name", "credits"},
            {"semester", "course_code", "credits"},
            {"semester", "course_title"},
            {"semester", "subject_name"},
            {"student_id", "cgpa", "department"},
            {"roll_no", "course", "semester"},
            {"syllabus", "course_code"},
            {"curriculum", "semester"}
        ],
        foreign_key_columns={"student_id", "roll_no", "course_code", "subject_code"}
    )

    medical_schema = EntitySchema(
        name=EntityType.MEDICAL.value,
        display_name="Medical / Patient Record",
        icon="local_hospital",
        strong_keywords={
            "patient_id", "patient_name", "doctor_name", "physician", "diagnosis", "prescription",
            "blood_group", "hospital", "clinic", "treatment", "admission_date", "discharge_date",
            "dosage", "symptoms", "medical_record_number", "mrn"
        },
        medium_keywords={
            "patient", "doctor", "medication", "disease", "vital_signs", "allergies", "ward"
        },
        weak_keywords={
            "name", "dob", "age", "gender", "phone", "address", "date", "status"
        },
        aliases={
            "medical_record_number": "patient_id",
            "mrn": "patient_id",
            "patient_name": "name",
            "physician": "doctor_name"
        },
        value_patterns=[
            re.compile(r"^PAT[-\s]?\d+$", re.IGNORECASE),
            re.compile(r"^MRN[-\s]?\d+$", re.IGNORECASE)
        ],
        co_occurrence_rules=[
            {"patient_id", "diagnosis", "doctor_name"},
            {"patient_id", "treatment", "admission_date"}
        ],
        foreign_key_columns={"patient_id"}
    )

    return {
        EntityType.STORE.value: store_schema,
        EntityType.ITEM.value: item_schema,
        EntityType.CUSTOMER.value: customer_schema,
        EntityType.TRANSACTION.value: transaction_schema,
        EntityType.CAR.value: car_schema,
        EntityType.INVOICE.value: invoice_schema,
        EntityType.EMPLOYEE.value: employee_schema,
        EntityType.STUDENT.value: student_schema,
        EntityType.MEDICAL.value: medical_schema,
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
    },

    EntityType.CAR.value: {
        "vin": CanonicalField(
            name="vin",
            field_type="id",
            aliases={"vin", "vehicle_identification_number", "chassis_number", "chassis_no", "vehicle_id", "car_id", "id"},
            description="17-character unique Vehicle Identification Number",
            is_primary_key=True
        ),
        "make": CanonicalField(
            name="make",
            field_type="text_title",
            aliases={"make", "brand", "manufacturer", "car_make", "vehicle_make", "company"},
            description="Vehicle manufacturer/brand (e.g. Honda, Toyota, BMW)"
        ),
        "model": CanonicalField(
            name="model",
            field_type="text_title",
            aliases={"model", "car_model", "vehicle_model", "trim", "variant", "name", "car_name"},
            description="Vehicle model and variant (e.g. Civic, Camry, Model 3)"
        ),
        "year": CanonicalField(
            name="year",
            field_type="numeric",
            aliases={"year", "model_year", "manufacturing_year", "mfg_year", "yr"},
            description="Manufacturing model year"
        ),
        "mileage": CanonicalField(
            name="mileage",
            field_type="numeric",
            aliases={"mileage", "odometer", "odometer_reading", "km_driven", "miles", "distance"},
            description="Total odometer mileage or distance traveled"
        ),
        "price": CanonicalField(
            name="price",
            field_type="numeric",
            aliases={"price", "selling_price", "cost", "msrp", "rate", "amount", "total_price"},
            description="Vehicle market or sale price"
        ),
        "color": CanonicalField(
            name="color",
            field_type="text_title",
            aliases={"color", "exterior_color", "paint", "body_color", "colour"},
            description="Exterior vehicle color"
        ),
        "license_plate": CanonicalField(
            name="license_plate",
            field_type="id",
            aliases={"license_plate", "plate_number", "plate_no", "registration_number", "reg_no", "plate"},
            description="Official vehicle registration license plate"
        ),
        "transmission": CanonicalField(
            name="transmission",
            field_type="text",
            aliases={"transmission", "gearbox", "transmission_type", "gear_type", "drive_type"},
            description="Transmission type (Automatic, Manual, CVT, EV Single-Speed)"
        ),
        "fuel_type": CanonicalField(
            name="fuel_type",
            field_type="text",
            aliases={"fuel_type", "fuel", "engine_type", "propulsion"},
            description="Fuel propulsion type (Gasoline, Diesel, Electric, Hybrid)"
        )
    },

    EntityType.INVOICE.value: {
        "invoice_no": CanonicalField(
            name="invoice_no",
            field_type="id",
            aliases={"invoice_no", "invoice_number", "invoice_num", "bill_no", "bill_number", "id", "inv_no"},
            description="Unique invoice or bill number",
            is_primary_key=True
        ),
        "invoice_date": CanonicalField(
            name="invoice_date",
            field_type="date",
            aliases={"invoice_date", "bill_date", "date", "issue_date", "created_at"},
            description="Date when invoice was issued"
        ),
        "due_date": CanonicalField(
            name="due_date",
            field_type="date",
            aliases={"due_date", "payment_due_date", "expiry_date"},
            description="Payment due date"
        ),
        "vendor_name": CanonicalField(
            name="vendor_name",
            field_type="text_title",
            aliases={"vendor_name", "supplier_name", "merchant_name", "biller", "company_name", "seller"},
            description="Issuing vendor or supplier business name"
        ),
        "bill_to": CanonicalField(
            name="bill_to",
            field_type="text_title",
            aliases={"bill_to", "billed_to", "customer_name", "client_name", "buyer_name", "recipient"},
            description="Recipient customer or business name"
        ),
        "subtotal": CanonicalField(
            name="subtotal",
            field_type="numeric",
            aliases={"subtotal", "sub_total", "net_amount", "base_amount"},
            description="Invoice subtotal before taxes"
        ),
        "tax_amount": CanonicalField(
            name="tax_amount",
            field_type="numeric",
            aliases={"tax_amount", "tax", "gst", "vat", "sales_tax"},
            description="Total tax amount"
        ),
        "total_amount": CanonicalField(
            name="total_amount",
            field_type="numeric",
            aliases={"total_amount", "grand_total", "total", "amount_due", "balance_due", "final_amount"},
            description="Final payable invoice amount"
        )
    },

    EntityType.EMPLOYEE.value: {
        "emp_id": CanonicalField(
            name="emp_id",
            field_type="id",
            aliases={"emp_id", "employee_id", "staff_id", "worker_id", "id", "badge_no"},
            description="Unique employee corporate identifier",
            is_primary_key=True
        ),
        "name": CanonicalField(
            name="name",
            field_type="text_title",
            aliases={"name", "employee_name", "emp_name", "full_name", "staff_name"},
            description="Employee full name"
        ),
        "department": CanonicalField(
            name="department",
            field_type="text_title",
            aliases={"department", "dept", "division", "team", "business_unit", "dept_name"},
            description="Assigned corporate department"
        ),
        "designation": CanonicalField(
            name="designation",
            field_type="text_title",
            aliases={"designation", "job_title", "title", "role", "position", "job_role"},
            description="Job title or designation"
        ),
        "salary": CanonicalField(
            name="salary",
            field_type="numeric",
            aliases={"salary", "compensation", "wage", "base_salary", "ctc", "pay_rate", "annual_salary"},
            description="Annual or monthly base salary"
        ),
        "joining_date": CanonicalField(
            name="joining_date",
            field_type="date",
            aliases={"joining_date", "hire_date", "start_date", "date_of_joining", "employment_date"},
            description="Date when employment commenced (YYYY-MM-DD)"
        ),
        "email": CanonicalField(
            name="email",
            field_type="email",
            aliases={"email", "work_email", "emp_email", "corporate_email"},
            description="Corporate email address"
        ),
        "phone": CanonicalField(
            name="phone",
            field_type="phone",
            aliases={"phone", "mobile", "contact", "work_phone"},
            description="Contact phone number"
        )
    },

    EntityType.STUDENT.value: {
        "course_code": CanonicalField(
            name="course_code",
            field_type="id",
            aliases={"course_code", "subject_code", "code", "c_code", "paper_code", "course_no", "subject_no"},
            description="Academic course or subject code"
        ),
        "course_title": CanonicalField(
            name="course_title",
            field_type="text_title",
            aliases={"course_title", "course_name", "subject_name", "subject", "course", "paper_name", "title", "course_description"},
            description="Official title/name of the course or subject"
        ),
        "semester": CanonicalField(
            name="semester",
            field_type="text_title",
            aliases={"semester", "sem", "term", "academic_semester", "academic_term"},
            description="Academic semester or term"
        ),
        "credits": CanonicalField(
            name="credits",
            field_type="numeric",
            aliases={"credits", "credit", "credits_count", "cr", "course_credits", "unit_credits"},
            description="Number of academic course credits"
        ),
        "course_category": CanonicalField(
            name="course_category",
            field_type="text_title",
            aliases={"course_category", "category", "course_type", "type", "elective_type", "domain"},
            description="Academic course category (Core, Elective, Lab)"
        ),
        "student_id": CanonicalField(
            name="student_id",
            field_type="id",
            aliases={"student_id", "roll_no", "reg_no", "roll_number", "registration_no", "id", "admission_no"},
            description="Unique student matriculation or registration number",
            is_primary_key=True
        ),
        "name": CanonicalField(
            name="name",
            field_type="text_title",
            aliases={"name", "student_name", "full_name", "candidate_name", "instructor", "faculty", "professor"},
            description="Student or faculty full name"
        ),
        "department": CanonicalField(
            name="department",
            field_type="text_title",
            aliases={"department", "branch", "major", "stream", "dept", "discipline", "program"},
            description="Academic department or specialization"
        ),
        "cgpa": CanonicalField(
            name="cgpa",
            field_type="numeric",
            aliases={"cgpa", "gpa", "grade_point", "percentage", "score", "marks_pct", "marks"},
            description="Cumulative Grade Point Average (0.0 - 10.0 or 4.0)"
        ),
        "attendance_pct": CanonicalField(
            name="attendance_pct",
            field_type="numeric",
            aliases={"attendance_pct", "attendance", "attendance_percentage", "attendance_rate", "pct_attendance"},
            description="Academic course attendance percentage (0 - 100%)"
        ),
        "email": CanonicalField(
            name="email",
            field_type="email",
            aliases={"email", "student_email", "college_email", "university_email"},
            description="Student / academic email address"
        )
    },

    EntityType.MEDICAL.value: {
        "patient_id": CanonicalField(
            name="patient_id",
            field_type="id",
            aliases={"patient_id", "mrn", "medical_record_number", "patient_no", "id", "case_id"},
            description="Unique medical record number (MRN)",
            is_primary_key=True
        ),
        "name": CanonicalField(
            name="name",
            field_type="text_title",
            aliases={"name", "patient_name", "full_name"},
            description="Patient full name"
        ),
        "doctor_name": CanonicalField(
            name="doctor_name",
            field_type="text_title",
            aliases={"doctor_name", "physician", "doctor", "consultant", "surgeon", "dr_name"},
            description="Attending physician / doctor"
        ),
        "diagnosis": CanonicalField(
            name="diagnosis",
            field_type="text",
            aliases={"diagnosis", "condition", "illness", "disease", "findings"},
            description="Clinical diagnosis or disease finding"
        ),
        "prescription": CanonicalField(
            name="prescription",
            field_type="text",
            aliases={"prescription", "medication", "treatment", "medicine", "drugs", "rx"},
            description="Prescribed medications and dosage"
        ),
        "blood_group": CanonicalField(
            name="blood_group",
            field_type="text",
            aliases={"blood_group", "blood_type", "blood_grp"},
            description="Patient blood group (e.g. O+, A+, B-, AB+)"
        ),
        "hospital": CanonicalField(
            name="hospital",
            field_type="text_title",
            aliases={"hospital", "clinic", "facility", "health_center", "medical_center"},
            description="Treating hospital or medical center"
        )
    }
}


def get_canonical_fields(entity_type: str) -> Dict[str, CanonicalField]:
    """Returns canonical field dictionary for given entity type."""
    return CANONICAL_SCHEMAS.get(entity_type.lower(), {})

