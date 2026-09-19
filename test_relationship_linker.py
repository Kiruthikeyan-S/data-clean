"""
Test Suite for Separated Same-Entity Resolution & Cross-Entity Relationship Network
Tests:
1. Part 18 Expected Test Case (Customer, Transaction, Product, Store).
2. Part 9 Nested JSON Support (relationship_context.buyer_phone).
3. Verifies that Customer + Product + Store + Transaction NEVER merge into a single ENT-001 cluster.
4. Verifies individual REL-0001, REL-0002... relationship edges with evidence.
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.models.schemas import ProcessResponse, ProcessSummary, EntityClassificationInfo
from backend.matching.cross_file_linker import link_batch_records

def test_part_18_architecture():
    print("=" * 70)
    print("RUNNING PART 18 TEST CASE: Customer + Transaction + Product + Store")
    print("=" * 70)

    # 1. Customer File
    file_customer = ProcessResponse(
        id="f_cust",
        filename="customer.json",
        file_type="json",
        mime_type="application/json",
        classification="structured",
        status="completed",
        steps=[],
        summary=ProcessSummary(
            total_records=1, valid_records=1, invalid_records=0,
            processing_time_ms=10.0, file_type="json", classification="structured"
        ),
        columns=["customer_id", "customer_name", "phone", "city"],
        structured_data=[
            {
                "customer_id": "CUST001",
                "customer_name": "Kiruthikeyan",
                "phone": "9876543210",
                "city": "Chennai"
            }
        ],
        entity_info=EntityClassificationInfo(entity_type="customer", confidence=0.98)
    )

    # 2. Transaction File
    file_transaction = ProcessResponse(
        id="f_txn",
        filename="transaction.json",
        file_type="json",
        mime_type="application/json",
        classification="structured",
        status="completed",
        steps=[],
        summary=ProcessSummary(
            total_records=1, valid_records=1, invalid_records=0,
            processing_time_ms=10.0, file_type="json", classification="structured"
        ),
        columns=["transaction_id", "customer_id", "store_id", "product_id"],
        structured_data=[
            {
                "transaction_id": "TXN001",
                "customer_id": "CUST001",
                "store_id": "STR001",
                "product_id": "ITM005"
            }
        ],
        entity_info=EntityClassificationInfo(entity_type="transaction", confidence=0.98)
    )

    # 3. Product File
    file_product = ProcessResponse(
        id="f_prod",
        filename="item.json",
        file_type="json",
        mime_type="application/json",
        classification="structured",
        status="completed",
        steps=[],
        summary=ProcessSummary(
            total_records=1, valid_records=1, invalid_records=0,
            processing_time_ms=10.0, file_type="json", classification="structured"
        ),
        columns=["product_id", "product_name", "sku"],
        structured_data=[
            {
                "product_id": "ITM005",
                "product_name": "HP Laptop",
                "sku": "HP-LAP-005"
            }
        ],
        entity_info=EntityClassificationInfo(entity_type="item", confidence=0.98)
    )

    # 4. Store File
    file_store = ProcessResponse(
        id="f_store",
        filename="store.json",
        file_type="json",
        mime_type="application/json",
        classification="structured",
        status="completed",
        steps=[],
        summary=ProcessSummary(
            total_records=1, valid_records=1, invalid_records=0,
            processing_time_ms=10.0, file_type="json", classification="structured"
        ),
        columns=["store_id", "store_name"],
        structured_data=[
            {
                "store_id": "STR001",
                "store_name": "ABC Chennai"
            }
        ],
        entity_info=EntityClassificationInfo(entity_type="store", confidence=0.98)
    )

    results, rel_index = link_batch_records([file_customer, file_transaction, file_product, file_store])

    summary = rel_index["summary"]
    relationships = rel_index["relationships"]
    entity_matches = rel_index["entity_matches"]

    print(f"Summary: {summary}")
    print(f"Type Counts: {rel_index['relationship_type_counts']}")
    print(f"\nTotal Individual Relationships Generated: {len(relationships)}")
    
    for r in relationships:
        src = f"{r['source']['entity_type']}:{r['source']['entity_id']} ({r['source']['name']})"
        tgt = f"{r['target']['entity_type']}:{r['target']['entity_id']} ({r['target']['name']})"
        print(f"  [{r['relationship_id']}] {src}  ──[{r['relationship_type']}]──>  {tgt}  ({r['confidence_percent']} conf)")

    # Assertions
    # 1. We must have at least 6 distinct relationship edges
    assert len(relationships) >= 6, f"Expected 6 relationship edges, found {len(relationships)}"

    # 2. Check for expected edges
    rel_types = {(r['source']['entity_id'], r['relationship_type'], r['target']['entity_id']) for r in relationships}
    
    assert ("CUST001", "purchased", "ITM005") in rel_types, "Missing Customer -> purchased -> Product"
    assert ("CUST001", "purchased_at", "STR001") in rel_types, "Missing Customer -> purchased_at -> Store"
    assert ("TXN001", "customer", "CUST001") in rel_types, "Missing Transaction -> customer -> Customer"
    assert ("TXN001", "product", "ITM005") in rel_types, "Missing Transaction -> product -> Product"
    assert ("TXN001", "store", "STR001") in rel_types, "Missing Transaction -> store -> Store"
    assert ("STR001", "sold", "ITM005") in rel_types, "Missing Store -> sold -> Product"

    # 3. Customer + Product + Store + Transaction must NOT be merged into one single entity
    # Same-entity matches should be 0 because all 4 records represent distinct real-world items
    assert len(entity_matches) == 0, f"Expected 0 same-entity merges, found {len(entity_matches)}"
    
    print("\n✓ ALL PART 18 ASSERTIONS PASSED PERFECTLY!")


def test_part_9_nested_json():
    print("\n" + "=" * 70)
    print("RUNNING PART 9 TEST CASE: Nested JSON Key Extraction")
    print("=" * 70)

    # File A with nested customer contact
    file_nested = ProcessResponse(
        id="f_nested",
        filename="nested_orders.json",
        file_type="json",
        mime_type="application/json",
        classification="structured",
        status="completed",
        steps=[],
        summary=ProcessSummary(
            total_records=1, valid_records=1, invalid_records=0,
            processing_time_ms=10.0, file_type="json", classification="structured"
        ),
        columns=["order_id", "relationship_context", "product_id"],
        structured_data=[
            {
                "order_id": "ORD-NESTED-99",
                "product_id": "ITM005",
                "relationship_context": {
                    "buyer_name": "Kiruthikeyan",
                    "buyer_phone": "9876543210",
                    "buyer_email": "kiruthi@example.com"
                }
            }
        ],
        entity_info=EntityClassificationInfo(entity_type="transaction", confidence=0.95)
    )

    # File B customer registry
    file_customer = ProcessResponse(
        id="f_cust",
        filename="customers.csv",
        file_type="csv",
        mime_type="text/csv",
        classification="structured",
        status="completed",
        steps=[],
        summary=ProcessSummary(
            total_records=1, valid_records=1, invalid_records=0,
            processing_time_ms=10.0, file_type="csv", classification="structured"
        ),
        columns=["customer_id", "customer_name", "phone"],
        structured_data=[
            {
                "customer_id": "CUST001",
                "customer_name": "Kiruthikeyan",
                "phone": "+91 98765 43210"
            }
        ],
        entity_info=EntityClassificationInfo(entity_type="customer", confidence=0.95)
    )

    results, rel_index = link_batch_records([file_nested, file_customer])
    relationships = rel_index["relationships"]

    print(f"Nested JSON Relationships Generated: {len(relationships)}")
    for r in relationships:
        print(f"  [{r['relationship_id']}] {r['source']['name']} ──[{r['relationship_type']}]──> {r['target']['name']}")

    assert len(relationships) >= 1, "Expected nested JSON phone to match customer record"
    print("✓ ALL PART 9 NESTED JSON ASSERTIONS PASSED PERFECTLY!")


if __name__ == "__main__":
    test_part_18_architecture()
    test_part_9_nested_json()
    print("\n" + "=" * 70)
    print("ALL TEST SUITES PASSED WITH 100% SUCCESS!")
    print("=" * 70)
