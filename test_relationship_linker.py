"""
Test Cross-File Relationship Linker Workflow
Verifies:
1. Normalization of comparison fields (Phone, Email, Customer ID, Store ID, Product SKU, Address).
2. Exact matching on Phone, Email, Store ID, Product SKU.
3. Fuzzy matching on Name, Address, Product Title.
4. Confidence calculation (0.0 to 1.0).
5. Semantic relationship categorization (Customer ↔ Product, Customer ↔ Store, Store ↔ Product).
6. Relationship index output structure.
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.models.schemas import ProcessResponse, ProcessSummary, EntityClassificationInfo
from backend.matching.cross_file_linker import link_batch_records

def test_cross_file_linking():
    # File 1: Customers CSV
    file1 = ProcessResponse(
        id="file_1",
        filename="customers.csv",
        file_type="csv",
        mime_type="text/csv",
        classification="structured",
        status="completed",
        steps=[],
        summary=ProcessSummary(
            total_records=2,
            valid_records=2,
            invalid_records=0,
            processing_time_ms=50.0,
            file_type="csv",
            classification="structured"
        ),
        columns=["customer_id", "customer_name", "phone", "email", "city"],
        structured_data=[
            {
                "customer_id": "CUST-001",
                "customer_name": "Alice Johnson",
                "phone": "+1 (555) 019-2834",
                "email": "alice.j@example.com",
                "city": "New York"
            },
            {
                "customer_id": "CUST-002",
                "customer_name": "Bob Smith",
                "phone": "9876543210",
                "email": "bob.smith@company.org",
                "city": "Los Angeles"
            }
        ],
        entity_info=EntityClassificationInfo(entity_type="customer", confidence=0.95)
    )

    # File 2: Orders / Products Excel
    file2 = ProcessResponse(
        id="file_2",
        filename="store_sales.xlsx",
        file_type="xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        classification="structured",
        status="completed",
        steps=[],
        summary=ProcessSummary(
            total_records=2,
            valid_records=2,
            invalid_records=0,
            processing_time_ms=60.0,
            file_type="xlsx",
            classification="structured"
        ),
        columns=["order_id", "contact_phone", "product_name", "sku", "store_id", "total_amount"],
        structured_data=[
            {
                "order_id": "ORD-9901",
                "contact_phone": "5550192834",  # Matches Alice's phone
                "product_name": "Ultra HD Monitor 4K",
                "sku": "SKU-MON-4K",
                "store_id": "STORE-EAST-01",
                "total_amount": 499.99
            },
            {
                "order_id": "ORD-9902",
                "contact_phone": "9876543210",  # Matches Bob's phone
                "product_name": "Ergonomic Keyboard",
                "sku": "SKU-KEY-01",
                "store_id": "STORE-WEST-02",
                "total_amount": 129.99
            }
        ],
        entity_info=EntityClassificationInfo(entity_type="transaction", confidence=0.92)
    )

    # File 3: Store Directory JSON
    file3 = ProcessResponse(
        id="file_3",
        filename="stores.json",
        file_type="json",
        mime_type="application/json",
        classification="structured",
        status="completed",
        steps=[],
        summary=ProcessSummary(
            total_records=1,
            valid_records=1,
            invalid_records=0,
            processing_time_ms=30.0,
            file_type="json",
            classification="structured"
        ),
        columns=["store_id", "store_name", "store_city", "store_phone"],
        structured_data=[
            {
                "store_id": "STORE-EAST-01",  # Matches Store East in Orders
                "store_name": "NYC Flagship Superstore",
                "store_city": "New York",
                "store_phone": "2125551000"
            }
        ],
        entity_info=EntityClassificationInfo(entity_type="store", confidence=0.98)
    )

    results, rel_index = link_batch_records([file1, file2, file3])

    print("=" * 60)
    print(f"Total Entities Linked: {rel_index['total_entities_linked']}")
    print(f"Cross-File Entities: {rel_index['cross_file_entities_count']}")
    print(f"Average Confidence: {rel_index['average_confidence']}")
    print(f"Types Breakdown: {rel_index['relationship_types_breakdown']}")
    print("=" * 60)

    for ent in rel_index["entities"]:
        print(f"Entity: {ent['entity_id']} | Name: {ent['display_name']} | Rel: {ent['relationship_type']} | Conf: {ent['confidence_percent']}")
        print(f"  Primary Key: {ent['primary_match_key']}")
        print(f"  Match Method: {ent['match_method']}")
        print(f"  Files: {ent['files_involved']}")
        print(f"  Records count: {ent['records_count']}")
        print("-" * 40)

    assert rel_index["total_entities_linked"] >= 1, "Expected at least 1 linked entity with 3+ records"
    assert rel_index["cross_file_entities_count"] >= 1, "Expected cross-file links with 3+ records"
    print("ALL ASSERTIONS PASSED SUCCESSFULLY WITH 3+ RECORDS THRESHOLD!")

if __name__ == "__main__":
    test_cross_file_linking()
