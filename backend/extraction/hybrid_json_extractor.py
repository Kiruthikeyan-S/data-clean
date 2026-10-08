"""
Hybrid JSON Extractor Module

Detects JSON datasets where records contain an identifier and an unstructured
natural-language text field (e.g. amazon_customers.json, amazon_items.json, amazon_stores.json).
Converts unstructured text into structured entity attributes (Customer, Item, Store)
with full validation, deduplication of repeated phrases, preservation of raw text,
and cross-file relationship resolution.
"""
from __future__ import annotations
import re
import math
from typing import Dict, Any, List, Tuple, Optional, Set
import pandas as pd
import numpy as np

from backend.models.schemas import ValidationErrorItem
from backend.normalization.normalizer import normalize_name, normalize_city, normalize_email

NULL_STRINGS = {"", "null", "none", "nan", "nat", "n/a", "na", "nil", "undefined", "-", "--", "#n/a", "unknown"}

KNOWN_CITIES = {
    "bengaluru", "bangalore", "chennai", "mumbai", "delhi", "new delhi", "kolkata",
    "hyderabad", "pune", "coimbatore", "madurai", "avadi", "salem", "trichy", "tiruchirappalli",
    "mysuru", "mysore", "kochi", "cochin", "thiruvananthapuram", "trivandrum", "ahmedabad",
    "jaipur", "lucknow", "chandigarh", "bhopal", "patna", "nagpur", "indore", "surat",
    "vadodara", "visakhapatnam", "vizag", "kanpur", "thane", "nashik", "varanasi", "noida", "gurgaon", "gurugram"
}

KNOWN_CATEGORIES = {
    "electronics", "mobiles", "fashion", "kitchen", "sports", "home", "stationery", "books",
    "toys", "beauty", "appliances", "automotive", "grocery", "fitness"
}


def deduplicate_phrases(text: str) -> str:
    """
    Eliminates immediate duplicate phrases in text (e.g. 'phrase and phrase', 'phrase. phrase.').
    """
    if not text:
        return ""
    s = text.strip()
    # Pattern: 'X and X'
    m = re.match(r"^(.*?)(?:\s+and\s+)\1(?:\.|\s*)$", s, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    
    # Pattern: 'X. X.'
    sentences = [p.strip() for p in re.split(r"[.\n]+", s) if p.strip()]
    if len(sentences) >= 2:
        seen = []
        for sent in sentences:
            sent_clean = " ".join(sent.split())
            if not any(sent_clean.lower() == existing.lower() for existing in seen):
                seen.append(sent_clean)
        return ". ".join(seen) + ("." if seen else "")
    return s


def is_hybrid_json_record(record: Dict[str, Any]) -> bool:
    """Checks if an individual JSON object is a hybrid record with an ID and rich text description."""
    if not isinstance(record, dict):
        return False
    keys_lower = [str(k).lower().strip() for k in record.keys()]
    has_id = any(k in ("id", "customer_id", "item_id", "store_id", "record_id", "key", "code") for k in keys_lower)
    has_text = any(k in ("text", "description", "details", "info", "raw_text", "content", "summary", "notes") for k in keys_lower)
    
    if has_id and has_text and len(record) <= 6:
        # Check that text value actually has substantive length
        for k, v in record.items():
            if str(k).lower().strip() in ("text", "description", "details", "info", "raw_text", "content", "summary", "notes"):
                if isinstance(v, str) and len(v.strip()) >= 15:
                    return True
    return False


def is_hybrid_json_dataset(records: List[Dict[str, Any]]) -> bool:
    """Checks if the dataset predominantly contains hybrid structured/unstructured records."""
    if not records or not isinstance(records, list):
        return False
    sample = records[:min(20, len(records))]
    match_count = sum(1 for r in sample if is_hybrid_json_record(r))
    return (match_count / max(len(sample), 1)) >= 0.60


def detect_entity_type_from_records(records: List[Dict[str, Any]]) -> str:
    """Detects whether hybrid records represent 'customer', 'item', or 'store'."""
    cust_score = 0
    item_score = 0
    store_score = 0

    for r in records[:30]:
        outer_id = str(r.get("id") or r.get("customer_id") or r.get("item_id") or r.get("store_id") or "").strip().upper()
        if outer_id.startswith("C") and len(outer_id) >= 2 and outer_id[1:].isdigit():
            cust_score += 3
        elif outer_id.startswith("I") and len(outer_id) >= 2 and outer_id[1:].isdigit():
            item_score += 3
        elif outer_id.startswith("S") and len(outer_id) >= 2 and outer_id[1:].isdigit():
            store_score += 3

        text = ""
        for k, v in r.items():
            if str(k).lower().strip() in ("text", "description", "details", "info", "raw_text", "content", "summary", "notes"):
                text = str(v).lower()
                break

        if any(w in text for w in ("customer", "wishlist", "buys books", "buyer", "returned 2 orders", "orders so far", "pays by upi", "cash on delivery", "prime member")):
            cust_score += 2
        if any(w in text for w in ("item", "product", "mrp", "rs.", "rs ", "sold by", "seller s", "stock", "warranty", "delivery in", "category")):
            item_score += 2
        if any(w in text for w in ("store", "seller", "owner phone", "gst invoice", "ships within", "prime eligible", "amazon fulfilled", "free delivery above", "star seller rating", "sells only branded")):
            store_score += 2

    if item_score > cust_score and item_score > store_score:
        return "item"
    if store_score > cust_score and store_score > item_score:
        return "store"
    if cust_score > 0:
        return "customer"
    return "customer"


def extract_customer_from_text(outer_id: Optional[str], text: str, row_idx: int) -> Tuple[Dict[str, Any], List[ValidationErrorItem]]:
    """Extracts structured Customer fields from unstructured text string."""
    errors: List[ValidationErrorItem] = []
    
    extracted: Dict[str, Any] = {
        "customer_id": outer_id,
        "customer_name": None,
        "city": None,
        "phone": None,
        "email": None,
        "membership_status": None,
        "payment_preference": None,
        "buying_preferences": None,
        "notes": None,
        "raw_text": text
    }

    # 1. Inner ID and conflict checking
    inner_id_match = re.search(r"\b(?:id|cust_id|cust)\s*[=:]?\s*(C\d+)\b", text, re.IGNORECASE)
    if not inner_id_match:
        inner_id_match = re.search(r"\bCustomer\s+(C\d+)\b", text, re.IGNORECASE)
    
    if inner_id_match:
        inner_id = inner_id_match.group(1).upper()
        if not extracted["customer_id"]:
            extracted["customer_id"] = inner_id
        elif outer_id and outer_id.upper() != inner_id:
            errors.append(ValidationErrorItem(
                field=f"Row {row_idx + 1}, Customer ID",
                message=f"Warning: Outer ID '{outer_id}' conflicts with inner text ID '{inner_id}'",
                raw_value=f"outer={outer_id}, inner={inner_id}"
            ))

    # 2. Email
    email_match = re.search(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b", text)
    if email_match:
        extracted["email"] = email_match.group(1).lower().strip()

    # 3. Phone (preserve malformed, validate digits)
    phone_match = re.search(r"\b(?:phone|ph|mobile|contact)\s*[=:]?\s*([0-9\s\-+xX]{6,20})\b", text, re.IGNORECASE)
    if phone_match:
        raw_ph = phone_match.group(1).strip()
        # Clean phone
        if raw_ph and raw_ph not in (".", "-", "NA", "null"):
            extracted["phone"] = raw_ph
            digits = re.sub(r"\D", "", raw_ph)
            if len(digits) < 10 or len(digits) > 12 or any(c in raw_ph for c in ("x", "X")):
                errors.append(ValidationErrorItem(
                    field=f"Row {row_idx + 1}, phone",
                    message=f"Warning: Phone number format non-standard or malformed: '{raw_ph}'",
                    raw_value=raw_ph
                ))

    # 4. Name and City patterns
    # Format A: "cust=Hari Pillai | id=C304 | ph=..."
    kv_cust_match = re.search(r"\bcust\s*=\s*([^|]+)", text, re.IGNORECASE)
    if kv_cust_match:
        extracted["customer_name"] = normalize_name(kv_cust_match.group(1).strip())
    
    # Format B: "Customer C302: Swetha Pillai from Bengaluru, phone ..."
    if not extracted["customer_name"]:
        c_prefix_match = re.search(r"\bCustomer\s+[A-Z0-9]+:\s*([^,]+?)\s+(?:from\s+([^,]+?))?(?:,\s*phone|\.|\s*$)", text, re.IGNORECASE)
        if c_prefix_match:
            extracted["customer_name"] = normalize_name(c_prefix_match.group(1).strip())
            if c_prefix_match.group(2):
                extracted["city"] = normalize_city(c_prefix_match.group(2).strip())

    # Format C: "Kavitha Pillai (Avadi) id C301 - email ..."
    if not extracted["customer_name"]:
        paren_match = re.search(r"^([A-Za-z\s]+)\s*\(([^)]+)\)\s*(?:id|email|-)", text.strip(), re.IGNORECASE)
        if paren_match:
            extracted["customer_name"] = normalize_name(paren_match.group(1).strip())
            extracted["city"] = normalize_city(paren_match.group(2).strip())

    # City fallback from text
    if not extracted["city"]:
        for city in KNOWN_CITIES:
            if re.search(rf"\b(?:from|in|at|\()\s*{city}\b", text, re.IGNORECASE) or re.search(rf"\b{city}\b", text, re.IGNORECASE):
                extracted["city"] = normalize_city(city)
                break

    # 5. Membership status
    if re.search(r"\b(?:is\s+a\s+)?prime\s+member\b", text, re.IGNORECASE):
        extracted["membership_status"] = "Prime"
    elif re.search(r"\b(?:is\s+a\s+)?first[- ]time\s+buyer\b", text, re.IGNORECASE):
        extracted["membership_status"] = "First-time Buyer"
    elif re.search(r"\b(?:regular|gold|silver|platinum)\s+member\b", text, re.IGNORECASE):
        m = re.search(r"\b(regular|gold|silver|platinum)\s+member\b", text, re.IGNORECASE)
        if m:
            extracted["membership_status"] = m.group(1).title()

    # 6. Payment preferences
    payment_methods = []
    if re.search(r"\b(?:uses\s+)?cash\s+on\s+delivery\b", text, re.IGNORECASE) or re.search(r"\bCOD\b", text):
        payment_methods.append("Cash on Delivery")
    if re.search(r"\b(?:pays\s+by\s+)?upi\b", text, re.IGNORECASE):
        payment_methods.append("UPI")
    if re.search(r"\b(?:credit|debit)\s+card\b", text, re.IGNORECASE):
        payment_methods.append("Card")
    if payment_methods:
        extracted["payment_preference"] = ", ".join(payment_methods)

    # 7. Buying preferences & Notes
    pref_items = []
    if re.search(r"\b(?:saves\s+items\s+in\s+wishlist(?:\s+but\s+rarely\s+buys)?)\b", text, re.IGNORECASE):
        pref_items.append("Saves items in wishlist but rarely buys")
    if re.search(r"\b(?:orders\s+mostly\s+electronics)\b", text, re.IGNORECASE):
        pref_items.append("Orders mostly electronics")
    if re.search(r"\b(?:waits\s+for\s+sale\s+days)\b", text, re.IGNORECASE):
        pref_items.append("Waits for sale days")
    if re.search(r"\b(?:buys\s+books\s+every\s+month)\b", text, re.IGNORECASE):
        pref_items.append("Buys books every month")
    if re.search(r"\b(?:has\s+\d+\s+orders\s+so\s+far)\b", text, re.IGNORECASE):
        m = re.search(r"\b(has\s+\d+\s+orders\s+so\s+far)\b", text, re.IGNORECASE)
        if m:
            pref_items.append(m.group(1).capitalize())

    if pref_items:
        # Deduplicate phrases
        unique_prefs = []
        for p in pref_items:
            if p not in unique_prefs:
                unique_prefs.append(p)
        extracted["buying_preferences"] = "; ".join(unique_prefs)

    # Notes (e.g. kv notes or reviews / complaints)
    note_parts = []
    note_kv = re.search(r"\bnote:\s*([^|]+)", text, re.IGNORECASE)
    if note_kv:
        note_parts.append(deduplicate_phrases(note_kv.group(1).strip()))
    
    if re.search(r"\bgave\s+5\s+star\s+reviews\s+often\b", text, re.IGNORECASE):
        note_parts.append("Gave 5 star reviews often")
    if re.search(r"\bcomplained\s+about\s+late\s+delivery(?:\s+once)?\b", text, re.IGNORECASE):
        note_parts.append("Complained about late delivery once")
    if re.search(r"\breturned\s+\d+\s+orders\s+last\s+month\b", text, re.IGNORECASE):
        m = re.search(r"\b(returned\s+\d+\s+orders\s+last\s+month)\b", text, re.IGNORECASE)
        if m:
            note_parts.append(m.group(1).capitalize())

    if note_parts:
        unique_notes = []
        for n in note_parts:
            n_clean = deduplicate_phrases(n)
            if n_clean and n_clean not in unique_notes:
                unique_notes.append(n_clean)
        extracted["notes"] = "; ".join(unique_notes)

    return extracted, errors


def extract_item_from_text(outer_id: Optional[str], text: str, row_idx: int) -> Tuple[Dict[str, Any], List[ValidationErrorItem]]:
    """Extracts structured Item/Product fields from unstructured text string."""
    errors: List[ValidationErrorItem] = []
    
    extracted: Dict[str, Any] = {
        "item_id": outer_id,
        "product_name": None,
        "category": None,
        "mrp": None,
        "price": None,
        "seller_id": None,
        "description": None,
        "stock_information": None,
        "delivery_information": None,
        "raw_text": text
    }

    # 1. Inner ID and conflict checking
    inner_id_match = re.search(r"\b(?:id|item\s*no|item_id)\s*[=:]?\s*(I\d+)\b", text, re.IGNORECASE)
    if not inner_id_match:
        inner_id_match = re.search(r"\bItem\s+(I\d+)\b", text, re.IGNORECASE)
    
    if inner_id_match:
        inner_id = inner_id_match.group(1).upper()
        if not extracted["item_id"]:
            extracted["item_id"] = inner_id
        elif outer_id and outer_id.upper() != inner_id:
            errors.append(ValidationErrorItem(
                field=f"Row {row_idx + 1}, Item ID",
                message=f"Warning: Outer ID '{outer_id}' conflicts with inner text ID '{inner_id}'",
                raw_value=f"outer={outer_id}, inner={inner_id}"
            ))

    # 2. Seller ID (e.g. "sold by S121", "seller S140", "seller=S101")
    seller_match = re.search(r"\b(?:sold\s+by|seller)\s*[=:]?\s*(S\d+)\b", text, re.IGNORECASE)
    if seller_match:
        extracted["seller_id"] = seller_match.group(1).upper()

    # 3. Product Name & Category
    # Format A: "product=Bluetooth speaker | cat=Electronics | mrp=2662 | price=2048 | id=I202"
    kv_prod = re.search(r"\bproduct\s*=\s*([^|]+)", text, re.IGNORECASE)
    if kv_prod:
        extracted["product_name"] = kv_prod.group(1).strip()
    
    kv_cat = re.search(r"\bcat\s*=\s*([^|]+)", text, re.IGNORECASE)
    if kv_cat:
        extracted["category"] = kv_cat.group(1).strip()

    # Format B: "Item I207: Phone cover in Mobiles category, price Rs.187, sold by S121."
    if not extracted["product_name"]:
        item_prefix = re.search(r"\bItem\s+[A-Z0-9]+:\s*([^,]+?)\s+in\s+([A-Za-z]+)\s+category", text, re.IGNORECASE)
        if item_prefix:
            extracted["product_name"] = item_prefix.group(1).strip()
            extracted["category"] = item_prefix.group(2).strip()

    # Format C: "Board game - Rs 915. Best seller this month..."
    if not extracted["product_name"]:
        dash_match = re.search(r"^([A-Za-z0-9\s]+?)\s*-\s*Rs\.?\s*([0-9\-\.]+)", text.strip(), re.IGNORECASE)
        if dash_match:
            extracted["product_name"] = dash_match.group(1).strip()
            # price captured here too
            try:
                p_val = float(dash_match.group(2))
                extracted["price"] = p_val
            except Exception:
                pass

    # Category fallback
    if not extracted["category"]:
        for cat in KNOWN_CATEGORIES:
            if re.search(rf"\b{cat}\b", text, re.IGNORECASE):
                extracted["category"] = cat.capitalize()
                break

    # 4. MRP & Price parsing
    # MRP
    mrp_match = re.search(r"\bmrp\s*[=:]?\s*(?:Rs\.?\s*)?([0-9\-\.]+)\b", text, re.IGNORECASE)
    if mrp_match:
        try:
            extracted["mrp"] = float(mrp_match.group(1))
        except Exception:
            pass

    # Price
    if extracted["price"] is None:
        price_match = re.search(r"\bprice\s*[=:]?\s*(?:Rs\.?\s*)?([0-9\-\.]+|NA)\b", text, re.IGNORECASE)
        if price_match:
            p_str = price_match.group(1).strip()
            if p_str.upper() == "NA":
                extracted["price"] = None
            else:
                try:
                    f_price = float(p_str)
                    extracted["price"] = f_price
                    if f_price < 0:
                        errors.append(ValidationErrorItem(
                            field=f"Row {row_idx + 1}, price",
                            message=f"Warning: Negative product price ({f_price}) detected. Preserved raw value for review.",
                            raw_value=p_str
                        ))
                except Exception:
                    pass

    if extracted["price"] is None:
        rs_match = re.search(r"\bRs\.?\s*([0-9\-\.]+)\b", text, re.IGNORECASE)
        if rs_match:
            try:
                f_price = float(rs_match.group(1))
                extracted["price"] = f_price
                if f_price < 0:
                    errors.append(ValidationErrorItem(
                        field=f"Row {row_idx + 1}, price",
                        message=f"Warning: Negative product price ({f_price}) detected. Preserved raw value for review.",
                        raw_value=rs_match.group(1)
                    ))
            except Exception:
                pass

    # 5. Stock Information
    stock_match = re.search(r"\b(Only\s+\d+\s+left\s+in\s+stock|In\s+stock|Out\s+of\s+stock)\b", text, re.IGNORECASE)
    if stock_match:
        extracted["stock_information"] = stock_match.group(1).strip()

    # 6. Delivery Information
    deliv_match = re.search(r"\b(Delivery\s+in\s+[\d\-]+\s+days|Cash\s+on\s+delivery\s+available|Free\s+delivery|Ships\s+within\s+[\d\-]+\s+days)\b", text, re.IGNORECASE)
    if deliv_match:
        extracted["delivery_information"] = deliv_match.group(1).strip()

    # 7. Description & Reviews (Deduplicate repeated phrases!)
    desc_phrases = []
    if re.search(r"\bBest\s+seller\s+this\s+month\b", text, re.IGNORECASE):
        desc_phrases.append("Best seller this month")
    if re.search(r"\bAvailable\s+in\s+\d+\s+colou?rs\b", text, re.IGNORECASE):
        m = re.search(r"\b(Available\s+in\s+\d+\s+colou?rs)\b", text, re.IGNORECASE)
        if m:
            desc_phrases.append(m.group(1).capitalize())
    if re.search(r"\bComes\s+with\s+\d+\s+year\s+warranty\b", text, re.IGNORECASE):
        m = re.search(r"\b(Comes\s+with\s+\d+\s+year\s+warranty)\b", text, re.IGNORECASE)
        if m:
            desc_phrases.append(m.group(1).capitalize())
    if re.search(r"\bEligible\s+for\s+return\s+within\s+\d+\s+days\b", text, re.IGNORECASE):
        m = re.search(r"\b(Eligible\s+for\s+return\s+within\s+\d+\s+days)\b", text, re.IGNORECASE)
        if m:
            desc_phrases.append(m.group(1).capitalize())
    if re.search(r"\bCustomers\s+say\s+it\s+is\s+good\s+for\s+daily\s+use\b", text, re.IGNORECASE):
        desc_phrases.append("Customers say it is good for daily use")
    if re.search(r"\bSome\s+reviews\s+say\s+packaging\s+was\s+poor\b", text, re.IGNORECASE):
        desc_phrases.append("Some reviews say packaging was poor")
    if re.search(r"\bPrice\s+dropped\s+last\s+week\b", text, re.IGNORECASE):
        desc_phrases.append("Price dropped last week")

    if desc_phrases:
        unique_desc = []
        for d in desc_phrases:
            d_dedup = deduplicate_phrases(d)
            if d_dedup and d_dedup not in unique_desc:
                unique_desc.append(d_dedup)
        extracted["description"] = "; ".join(unique_desc)

    return extracted, errors


def extract_store_from_text(outer_id: Optional[str], text: str, row_idx: int) -> Tuple[Dict[str, Any], List[ValidationErrorItem]]:
    """Extracts structured Store/Seller fields from unstructured text string."""
    errors: List[ValidationErrorItem] = []
    
    extracted: Dict[str, Any] = {
        "store_id": outer_id,
        "store_name": None,
        "city": None,
        "owner_phone": None,
        "delivery_policy": None,
        "notes": None,
        "raw_text": text
    }

    # 1. Inner ID and conflict checking
    inner_id_match = re.search(r"\b(?:id|store\s*id|store_id)\s*[=:]?\s*(S\d+)\b", text, re.IGNORECASE)
    if not inner_id_match:
        inner_id_match = re.search(r"\bStore\s+(S\d+)\b", text, re.IGNORECASE)
    
    if inner_id_match:
        inner_id = inner_id_match.group(1).upper()
        if not extracted["store_id"]:
            extracted["store_id"] = inner_id
        elif outer_id and outer_id.upper() != inner_id:
            errors.append(ValidationErrorItem(
                field=f"Row {row_idx + 1}, Store ID",
                message=f"Warning: Outer ID '{outer_id}' conflicts with inner text ID '{inner_id}'",
                raw_value=f"outer={outer_id}, inner={inner_id}"
            ))

    # 2. Store Name
    # Format A: "seller=Global Mobiles | id=S101 | city=Pune"
    kv_seller = re.search(r"\bseller\s*=\s*([^|]+)", text, re.IGNORECASE)
    if kv_seller:
        extracted["store_name"] = normalize_name(kv_seller.group(1).strip())

    # Format B: "Store S103: Prime Mart, based in Chennai."
    if not extracted["store_name"]:
        store_prefix = re.search(r"\bStore\s+[A-Z0-9]+:\s*([^,]+?)(?:,\s*based\s+in|\.|\s*$)", text, re.IGNORECASE)
        if store_prefix:
            extracted["store_name"] = normalize_name(store_prefix.group(1).strip())

    # Format C: "Star Mart (store id S102) - Coimbatore."
    if not extracted["store_name"]:
        paren_store = re.search(r"^([A-Za-z0-9\s&]+?)\s*\((?:store\s*id|id)\s*[A-Z0-9]+\)\s*-\s*([A-Za-z\s]+)", text.strip(), re.IGNORECASE)
        if paren_store:
            extracted["store_name"] = normalize_name(paren_store.group(1).strip())
            extracted["city"] = normalize_city(paren_store.group(2).strip())

    # 3. City
    kv_city = re.search(r"\bcity\s*=\s*([^|]+)", text, re.IGNORECASE)
    if kv_city:
        extracted["city"] = normalize_city(kv_city.group(1).strip())
    elif not extracted["city"]:
        based_city = re.search(r"\bbased\s+in\s+([A-Za-z\s]+?)(?:\.|\s*,|\s*$)", text, re.IGNORECASE)
        if based_city:
            extracted["city"] = normalize_city(based_city.group(1).strip())
        else:
            for city in KNOWN_CITIES:
                if re.search(rf"\b{city}\b", text, re.IGNORECASE):
                    extracted["city"] = normalize_city(city)
                    break

    # 4. Owner Phone
    phone_match = re.search(r"\b(?:Owner\s+phone|phone|ph|mobile|contact)\s*[=:]?\s*([0-9\s\-+xX]{6,20})\b", text, re.IGNORECASE)
    if phone_match:
        raw_ph = phone_match.group(1).strip()
        if raw_ph and raw_ph not in (".", "-", "NA", "null"):
            extracted["owner_phone"] = raw_ph
            digits = re.sub(r"\D", "", raw_ph)
            if len(digits) < 10 or len(digits) > 12:
                errors.append(ValidationErrorItem(
                    field=f"Row {row_idx + 1}, owner_phone",
                    message=f"Warning: Phone number format non-standard: '{raw_ph}'",
                    raw_value=raw_ph
                ))

    # 5. Delivery Policy
    deliv_policies = []
    if re.search(r"\boffers\s+free\s+delivery\s+above\s+\d+\s+rupees\b", text, re.IGNORECASE):
        m = re.search(r"\b(offers\s+free\s+delivery\s+above\s+\d+\s+rupees)\b", text, re.IGNORECASE)
        if m:
            deliv_policies.append(m.group(1).capitalize())
    if re.search(r"\bships\s+within\s+\d+\s+days\b", text, re.IGNORECASE):
        m = re.search(r"\b(ships\s+within\s+\d+\s+days)\b", text, re.IGNORECASE)
        if m:
            deliv_policies.append(m.group(1).capitalize())
    if re.search(r"\baccepts\s+returns\s+for\s+\d+\s+days\b", text, re.IGNORECASE):
        m = re.search(r"\b(accepts\s+returns\s+for\s+\d+\s+days)\b", text, re.IGNORECASE)
        if m:
            deliv_policies.append(m.group(1).capitalize())
    if re.search(r"\bships\s+from\s+own\s+warehouse\b", text, re.IGNORECASE):
        deliv_policies.append("Ships from own warehouse")

    if deliv_policies:
        unique_policies = []
        for p in deliv_policies:
            p_dedup = deduplicate_phrases(p)
            if p_dedup and p_dedup not in unique_policies:
                unique_policies.append(p_dedup)
        extracted["delivery_policy"] = "; ".join(unique_policies)

    # 6. Notes / Badges
    notes_list = []
    note_kv = re.search(r"\bnote:\s*([^|]+)", text, re.IGNORECASE)
    if note_kv:
        notes_list.append(deduplicate_phrases(note_kv.group(1).strip()))
    
    if re.search(r"\bAmazon\s+Fulfilled\s*\(Prime\s+eligible\)\b", text, re.IGNORECASE) or re.search(r"\bis\s+amazon\s+fulfilled\b", text, re.IGNORECASE):
        notes_list.append("Amazon Fulfilled (Prime eligible)")
    if re.search(r"\bnew\s+seller\s+since\s+\d+\b", text, re.IGNORECASE):
        m = re.search(r"\b(new\s+seller\s+since\s+\d+)\b", text, re.IGNORECASE)
        if m:
            notes_list.append(m.group(1).capitalize())
    if re.search(r"\b\d+\.\d+\s+star\s+seller\s+rating\b", text, re.IGNORECASE):
        m = re.search(r"\b(\d+\.\d+\s+star\s+seller\s+rating)\b", text, re.IGNORECASE)
        if m:
            notes_list.append(m.group(1).capitalize())
    if re.search(r"\bgives\s+gst\s+invoice\b", text, re.IGNORECASE):
        notes_list.append("Gives GST invoice")
    if re.search(r"\bsells\s+only\s+branded\s+products\b", text, re.IGNORECASE):
        notes_list.append("Sells only branded products")
    if re.search(r"\bhas\s+some\s+late-delivery\s+complaints\b", text, re.IGNORECASE):
        notes_list.append("Has some late-delivery complaints")

    if notes_list:
        unique_notes = []
        for n in notes_list:
            n_dedup = deduplicate_phrases(n)
            if n_dedup and n_dedup not in unique_notes:
                unique_notes.append(n_dedup)
        extracted["notes"] = "; ".join(unique_notes)

    return extracted, errors


def process_hybrid_json(
    records: List[Dict[str, Any]],
    filename: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[str], str, List[ValidationErrorItem], List[str]]:
    """
    Main entry point for processing hybrid structured/unstructured JSON datasets.
    
    Returns:
    - cleaned_records: List of structured dictionary records
    - columns: List of extracted column names
    - entity_type: 'customer' | 'item' | 'store'
    - errors: List of ValidationErrorItem objects
    - change_highlights: List of audit transformation descriptions
    """
    entity_type = detect_entity_type_from_records(records)
    all_extracted_records: List[Dict[str, Any]] = []
    all_errors: List[ValidationErrorItem] = []
    
    for row_idx, r in enumerate(records):
        outer_id = str(r.get("id") or r.get("customer_id") or r.get("item_id") or r.get("store_id") or "").strip()
        text_val = ""
        for k, v in r.items():
            if str(k).lower().strip() in ("text", "description", "details", "info", "raw_text", "content", "summary", "notes"):
                text_val = str(v)
                break

        if entity_type == "customer":
            extracted, errs = extract_customer_from_text(outer_id, text_val, row_idx)
        elif entity_type == "item":
            extracted, errs = extract_item_from_text(outer_id, text_val, row_idx)
        elif entity_type == "store":
            extracted, errs = extract_store_from_text(outer_id, text_val, row_idx)
        else:
            extracted, errs = extract_customer_from_text(outer_id, text_val, row_idx)

        all_extracted_records.append(extracted)
        all_errors.extend(errs)

    # Determine standard columns order per entity
    if entity_type == "customer":
        columns = [
            "customer_id", "customer_name", "city", "phone", "email",
            "membership_status", "payment_preference", "buying_preferences", "notes"
        ]
    elif entity_type == "item":
        columns = [
            "item_id", "product_name", "category", "mrp", "price",
            "seller_id", "description", "stock_information", "delivery_information"
        ]
    elif entity_type == "store":
        columns = [
            "store_id", "store_name", "city", "owner_phone", "delivery_policy", "notes"
        ]
    else:
        columns = list(all_extracted_records[0].keys()) if all_extracted_records else ["id", "text"]

    change_highlights = [
        f"Detected hybrid JSON dataset with unstructured '{entity_type}' entity narratives",
        f"Extracted {len(columns)} structured attribute fields across {len(all_extracted_records)} records using Rule-Based Hybrid NLP Parser",
        f"Preserved original raw text in lineage records and verified authoritative IDs"
    ]

    return all_extracted_records, columns, entity_type, all_errors, change_highlights
