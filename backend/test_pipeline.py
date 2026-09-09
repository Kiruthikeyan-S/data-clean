import json
import pytest
from backend.utils.file_detector import detect_file_type, classify_data_type
from backend.normalization.normalizer import (
    normalize_name,
    normalize_date,
    normalize_email,
    normalize_phone,
    normalize_number
)
from backend.cleaning.text_cleaner import clean_text_data
from backend.pipeline import process_file_pipeline

def test_file_detector():
    res_csv = detect_file_type("data.csv")
    assert res_csv["file_type"] == "csv"
    assert classify_data_type("csv") == "structured"
    
    res_pdf = detect_file_type("scan.pdf")
    assert res_pdf["file_type"] == "pdf"
    assert classify_data_type("pdf") == "unstructured"

def test_normalizers():
    assert normalize_name("RAVI KUMAR") == "Ravi Kumar"
    assert normalize_email("RAVI@GMAIL.COM") == "ravi@gmail.com"
    assert normalize_phone("+91-98765 43210") == "+919876543210"
    assert normalize_number("₹10,000") == 10000
    # Date test
    assert normalize_date("12/05/2001") == "2001-05-12"

def test_text_cleaner():
    raw = "  Hello   world \r\n\r\n\r\n  Duplicate\n  Duplicate  "
    cleaned = clean_text_data(raw)
    assert "Duplicate" in cleaned
    assert "Hello world" in cleaned

def test_structured_csv_pipeline():
    csv_bytes = b"Name, Age, Email , Income \nJohn Doe , 30 , john@example.com , $50000\n\n   \nJohn Doe , 30 , john@example.com , $50000\nJane Smith, 25, NA, \xe2\x82\xb960000"
    resp = process_file_pipeline("test.csv", "text/csv", csv_bytes)
    assert resp.status == "completed"
    assert resp.classification == "structured"
    assert len(resp.structured_data) == 2  # duplicate dropped

def test_unstructured_txt_pipeline():
    raw_text = """
    Customer Profile
    Name: Ravi Kumar
    Date of Birth: 12/05/2001
    Email: ravi@gmail.com
    Phone: +91 98765 43210
    Address: Chennai, Tamil Nadu
    Total Amount: INR 15,000
    """
    resp = process_file_pipeline("profile.txt", "text/plain", raw_text.encode("utf-8"))
    assert resp.status == "completed"
    assert resp.classification == "unstructured"
    assert resp.fields is not None
    
    field_map = {f.key: f.value for f in resp.fields}
    assert field_map["name"] == "Ravi Kumar"
    assert field_map["dob"] == "2001-05-12"
    assert field_map["email"] == "ravi@gmail.com"
    assert field_map["phone"] == "+919876543210"
    assert field_map["amount"] == 15000
