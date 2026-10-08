import json
import pytest
import pandas as pd
from backend.extraction.hybrid_json_extractor import (
    is_hybrid_json_dataset,
    detect_entity_type_from_records,
    process_hybrid_json
)
from backend.pipeline import process_file_pipeline
from backend.matching.cross_file_linker import link_batch_records


def test_customer_hybrid_json_extraction():
    """Test Customer hybrid JSON extraction with various sentence patterns."""
    records = [
        {
            "id": "C301",
            "text": "Kavitha Pillai (Avadi) id C301 - email kavitha1@example.com. Saves items in wishlist but rarely buys."
        },
        {
            "id": "C302",
            "text": "Customer C302: Swetha Pillai from Bengaluru, phone 9780400237. Uses cash on delivery and orders mostly electronics."
        },
        {
            "id": "C304",
            "text": "cust=Hari Pillai | id=C304 | ph=9134533070 | note: gave 5 star reviews often"
        },
        {
            "id": "C312",
            "text": "Customer C312: Janani   iyer , phone 98-4148 5253x. Is a prime member."
        },
        {
            "id": "C317",
            "text": "Customer C317: Gopal Kumar from Mumbai, phone 9191254308. Is a first-time buyer and is a first-time buyer."
        }
    ]

    assert is_hybrid_json_dataset(records) is True
    assert detect_entity_type_from_records(records) == "customer"

    extracted, cols, entity_type, errors, highlights = process_hybrid_json(records)
    assert entity_type == "customer"
    assert "customer_id" in cols
    assert "customer_name" in cols
    assert "email" in cols
    assert "phone" in cols

    # C301
    assert extracted[0]["customer_id"] == "C301"
    assert extracted[0]["customer_name"] == "Kavitha Pillai"
    assert extracted[0]["city"] == "Avadi"
    assert extracted[0]["email"] == "kavitha1@example.com"
    assert "wishlist" in extracted[0]["buying_preferences"].lower()

    # C302
    assert extracted[1]["customer_id"] == "C302"
    assert extracted[1]["customer_name"] == "Swetha Pillai"
    assert extracted[1]["city"] == "Bengaluru"
    assert extracted[1]["phone"] == "9780400237"
    assert extracted[1]["payment_preference"] == "Cash on Delivery"

    # C304
    assert extracted[2]["customer_id"] == "C304"
    assert extracted[2]["customer_name"] == "Hari Pillai"
    assert extracted[2]["phone"] == "9134533070"

    # C312 (malformed phone)
    assert extracted[3]["phone"] == "98-4148 5253x"
    assert any("phone" in e.field.lower() for e in errors)
    assert extracted[3]["membership_status"] == "Prime"

    # C317 (deduplicated phrase in membership)
    assert extracted[4]["membership_status"] == "First-time Buyer"


def test_item_hybrid_json_extraction():
    """Test Item hybrid JSON extraction with prices, seller IDs, and validation."""
    records = [
        {
            "id": "I201",
            "text": "Board game - Rs 915. Best seller this month. Delivery in 2-3 days. (item no I201, seller S140)"
        },
        {
            "id": "I202",
            "text": "product=Bluetooth speaker | cat=Electronics | mrp=2662 | price=2048 | id=I202 | Customers say it is good for daily use."
        },
        {
            "id": "I207",
            "text": "Item I207: Phone cover in Mobiles category, price Rs.187, sold by S121. Price dropped last week."
        },
        {
            "id": "I210",
            "text": "Item I209: Running shoes in Fashion category, price Rs.-1499, sold by S120. Delivery in 2-3 days."
        },
        {
            "id": "I220",
            "text": "Item I219: Mixer grinder in Kitchen category, price Rs.NA, sold by S130."
        }
    ]

    assert is_hybrid_json_dataset(records) is True
    assert detect_entity_type_from_records(records) == "item"

    extracted, cols, entity_type, errors, highlights = process_hybrid_json(records)
    assert entity_type == "item"
    assert "product_name" in cols
    assert "price" in cols
    assert "seller_id" in cols

    # I201
    assert extracted[0]["product_name"] == "Board game"
    assert extracted[0]["price"] == 915.0
    assert extracted[0]["seller_id"] == "S140"
    assert extracted[0]["delivery_information"] == "Delivery in 2-3 days"

    # I202
    assert extracted[1]["product_name"] == "Bluetooth speaker"
    assert extracted[1]["category"] == "Electronics"
    assert extracted[1]["mrp"] == 2662.0
    assert extracted[1]["price"] == 2048.0

    # I207
    assert extracted[2]["product_name"] == "Phone cover"
    assert extracted[2]["category"] == "Mobiles"
    assert extracted[2]["price"] == 187.0
    assert extracted[2]["seller_id"] == "S121"

    # I210 with outer ID vs inner ID conflict and negative price
    assert extracted[3]["price"] == -1499.0
    assert extracted[3]["seller_id"] == "S120"
    assert any("negative" in e.message.lower() for e in errors)
    assert any("conflict" in e.message.lower() for e in errors)

    # I220 with NA price -> None
    assert extracted[4]["price"] is None
    assert extracted[4]["seller_id"] == "S130"


def test_store_hybrid_json_extraction():
    """Test Store hybrid JSON extraction with city, phone, policies."""
    records = [
        {
            "id": "S101",
            "text": "seller=Global Mobiles | id=S101 | city=Pune | note: accepts returns for 10 days"
        },
        {
            "id": "S102",
            "text": "Star Mart (store id S102) - Coimbatore. Owner phone 9297118916. Gives gst invoice."
        },
        {
            "id": "S103",
            "text": "Store S103: Prime Mart, based in Chennai. This seller is Amazon Fulfilled (Prime eligible) and has some late-delivery complaints."
        },
        {
            "id": "S110",
            "text": "Store S110: Lakshmi Mart, based in Madurai. This seller offers free delivery above 499 rupees and offers free delivery above 499 rupees."
        }
    ]

    assert is_hybrid_json_dataset(records) is True
    assert detect_entity_type_from_records(records) == "store"

    extracted, cols, entity_type, errors, highlights = process_hybrid_json(records)
    assert entity_type == "store"
    assert "store_name" in cols
    assert "city" in cols
    assert "delivery_policy" in cols

    # S101
    assert extracted[0]["store_id"] == "S101"
    assert extracted[0]["store_name"] == "Global Mobiles"
    assert extracted[0]["city"] == "Pune"
    assert "returns for 10 days" in extracted[0]["delivery_policy"].lower()

    # S102
    assert extracted[1]["store_id"] == "S102"
    assert extracted[1]["store_name"] == "Star Mart"
    assert extracted[1]["city"] == "Coimbatore"
    assert extracted[1]["owner_phone"] == "9297118916"

    # S103
    assert extracted[2]["store_id"] == "S103"
    assert extracted[2]["store_name"] == "Prime Mart"
    assert extracted[2]["city"] == "Chennai"
    assert "Prime eligible" in extracted[2]["notes"]

    # S110 (deduplicated delivery policy)
    assert "offers free delivery above 499 rupees" in extracted[3]["delivery_policy"].lower()
    # verify not repeated twice
    assert extracted[3]["delivery_policy"].lower().count("free delivery") == 1


def test_pipeline_hybrid_json_and_cross_file_linking():
    """End-to-end test with JSON bytes through pipeline and cross-file Store/Item resolution."""
    cust_json = json.dumps([
        {"id": "C301", "text": "Kavitha Pillai (Avadi) id C301 - email kavitha1@example.com."}
    ]).encode("utf-8")

    item_json = json.dumps([
        {"id": "I201", "text": "Board game - Rs 915. Best seller this month. (item no I201, seller S101)"}
    ]).encode("utf-8")

    store_json = json.dumps([
        {"id": "S101", "text": "seller=Global Mobiles | id=S101 | city=Pune | note: accepts returns for 10 days"}
    ]).encode("utf-8")

    resp_cust = process_file_pipeline("amazon_customers.json", "application/json", cust_json)
    resp_item = process_file_pipeline("amazon_items.json", "application/json", item_json)
    resp_store = process_file_pipeline("amazon_stores.json", "application/json", store_json)

    assert resp_cust.entity_info.entity_type == "customer"
    assert "customer_name" in resp_cust.columns or "full_name" in resp_cust.columns
    cust_val = resp_cust.structured_data[0].get("customer_name") or resp_cust.structured_data[0].get("full_name")
    assert cust_val == "Kavitha Pillai"

    assert resp_item.entity_info.entity_type == "item"
    assert "product_name" in resp_item.columns or "item_name" in resp_item.columns
    assert resp_item.structured_data[0]["seller_id"] == "S101"

    assert resp_store.entity_info.entity_type == "store"
    assert "store_name" in resp_store.columns
    assert resp_store.structured_data[0]["store_name"] == "Global Mobiles"

    # Cross-file resolution: Item S101 seller matches Store S101
    _, index = link_batch_records([resp_cust, resp_item, resp_store])
    assert index["summary"]["relationships_found"] >= 1
    rel = index["relationships"][0]
    assert rel["source"]["entity_id"] == "S101"
    assert rel["target"]["entity_id"] == "I201"
    assert rel["relationship_type"] == "sold"
