import pytest
from backend.rag.llm_rag_analyzer import soundex, heuristic_rag_analysis
from backend.matching.record_matcher import (
    ReversibleMergeManager,
    compare_records,
    analyze_record_matching
)

def test_soundex_phonetic_matching():
    assert soundex("Smith") == soundex("Smyth")
    assert soundex("Robert") == soundex("Rupert")
    assert soundex("John") != soundex("Alice")


def test_customer_matching_safety_guardrails():
    # Similar names but different phone numbers MUST be rejected
    rec_a = {"name": "John Smith", "phone": "1112223333", "email": "john.a@test.com"}
    rec_b = {"name": "John Smyth", "phone": "9998887777", "email": "john.b@test.com"}
    
    analysis = heuristic_rag_analysis(rec_a, rec_b, "cand_1", "customer")
    assert analysis["match_decision"] == "rejected"
    assert analysis["possible_match"] is False
    assert "phone" in analysis["conflicting_fields"]


def test_item_matching_product_version_guardrails():
    # Similar name but different product version/model tokens
    item_a = {"item_name": "Apple iPhone 13 128GB", "sku": "SKU-IPH-13"}
    item_b = {"item_name": "Apple iPhone 14 128GB", "sku": "SKU-IPH-14"}

    analysis = heuristic_rag_analysis(item_a, item_b, "cand_2", "item")
    assert analysis["match_decision"] == "rejected"
    assert analysis["possible_match"] is False


def test_reversible_merge_workflow():
    manager = ReversibleMergeManager()
    rec_a = {"id": "CUST_1", "name": "Alice Smith", "email": "alice@test.com", "phone": None}
    rec_b = {"id": "CUST_1", "name": "Alice Smith", "email": None, "phone": "+1-555-0100"}
    merged = {"id": "CUST_1", "name": "Alice Smith", "email": "alice@test.com", "phone": "+1-555-0100"}

    # 1. Record merge
    entry = manager.record_merge(
        merge_id="merge_001",
        entity_type="customer",
        rec_a=rec_a,
        rec_b=rec_b,
        merged=merged,
        matched_fields=["id", "name"],
        confidence=0.98,
        decision="auto_approved"
    )
    assert entry.is_active is True
    assert entry.decision == "auto_approved"

    # 2. Reverse merge
    orig_a, orig_b = manager.reverse_merge("merge_001")
    assert orig_a["phone"] is None
    assert orig_b["email"] is None
    assert manager.history["merge_001"].is_active is False
    assert manager.history["merge_001"].decision == "undone"
