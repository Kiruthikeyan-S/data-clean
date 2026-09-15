import json
from backend.cleaning.structured_cleaner import read_and_clean_structured_file
from backend.pipeline import process_file_pipeline

def test_nested_json_list():
    data = [
        {
            "customer_id": "C001",
            "name": "Ravi Kumar",
            "email": "ravi@example.com",
            "address": {"city": "Chennai", "state": "TN", "zip": "600001"},
            "tags": ["vip", "retail"]
        },
        {
            "customer_id": "C002",
            "name": "Priya Sharma",
            "email": "priya@example.com",
            "address": {"city": "Mumbai", "state": "MH", "zip": "400001"},
            "tags": ["regular"]
        },
        # duplicate
        {
            "customer_id": "C001",
            "name": "Ravi Kumar",
            "email": "ravi@example.com",
            "address": {"city": "Chennai", "state": "TN", "zip": "600001"},
            "tags": ["vip", "retail"]
        }
    ]
    raw_bytes = json.dumps(data).encode("utf-8")
    records, cols, metrics = read_and_clean_structured_file("json", raw_bytes)
    print(f"Nested JSON List Test -> Records: {len(records)}, Columns: {cols}")
    assert len(records) == 2  # 1 duplicate dropped
    assert "address_city" in cols or "address" in cols

def test_nested_json_object():
    data = {
        "customer_id": "C001",
        "name": "Ravi Kumar",
        "email": "ravi@example.com",
        "contact_info": {
            "phone": "+919876543210",
            "city": "Chennai"
        }
    }
    raw_bytes = json.dumps(data).encode("utf-8")
    records, cols, metrics = read_and_clean_structured_file("json", raw_bytes)
    print(f"Single Nested JSON Object Test -> Records: {len(records)}, Columns: {cols}")
    assert len(records) == 1

def test_pipeline_nested_json():
    data = [
        {
            "customer_id": "C001",
            "customer_name": "Ravi Kumar",
            "customer_email": "ravi@gmail.com",
            "location": {"city": "Chennai", "country": "India"}
        }
    ]
    raw_bytes = json.dumps(data).encode("utf-8")
    response = process_file_pipeline("customer_raw.json", "application/json", raw_bytes)
    print(f"Pipeline JSON Test -> Status: {response.status}, Entity: {response.entity_info.entity_type if response.entity_info else 'N/A'}")
    assert response.status == "completed"
    assert response.errors is None

if __name__ == "__main__":
    print("Testing Nested JSON processing...")
    test_nested_json_list()
    test_nested_json_object()
    test_pipeline_nested_json()
    print("\nALL NESTED JSON TESTS PASSED WITHOUT UNHASHABLE TYPE ERRORS!")
