import os
import pytest
from backend.pipeline import process_file_pipeline
from backend.extractors.pdf_extractor import extract_pdf
from backend.extraction.entity_classifier import classify_domain

PDF_PATH = r"C:\Users\kirut\Downloads\test_case_report_100.pdf"
if not os.path.exists(PDF_PATH):
    PDF_PATH = r"C:\Users\kirut\.gemini\antigravity\brain\ea2a4786-0ee9-4313-bccb-562f813f748d\.user_uploaded\media_1795508833795_4b51d6aa.pdf"


def test_pdf_test_report_100_extraction():
    """
    Test that test_case_report_100.pdf is extracted into exactly 100 test case records,
    is classified as technical_test_report (NOT customer), and has correct columns.
    """
    assert os.path.exists(PDF_PATH), f"Test PDF not found at {PDF_PATH}"

    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    res = process_file_pipeline("test_case_report_100.pdf", "application/pdf", pdf_bytes)

    # 1. Pipeline status
    assert res.status == "completed"

    # 2. Entity classification MUST be technical_test_report (NEVER customer or employee)
    assert res.entity_info is not None
    assert res.entity_info.entity_type == "technical_test_report"
    assert "Test Report" in res.entity_info.display_name
    assert res.entity_info.primary_match_key == "test_case_id"
    assert res.entity_info.confidence >= 0.80

    # 3. Exact 100 records
    assert len(res.structured_data) == 100, f"Expected 100 records, got {len(res.structured_data)}"

    # 4. Verify all TC IDs from TC-001 to TC-100 are present
    tc_ids = [r["test_case_id"] for r in res.structured_data]
    assert len(set(tc_ids)) == 100, "Duplicate or missing test case IDs detected"
    for i in range(1, 101):
        expected_id = f"TC-{i:03d}"
        assert expected_id in tc_ids, f"Missing test case {expected_id}"

    # 5. Verify columns are correct (NEVER ['full_name', 'email', 'phone'])
    expected_cols = ["test_case_id", "category", "description", "input_data", "expected_result", "actual_result", "execution_time", "status", "source_page"]
    for col in expected_cols:
        assert col in res.columns, f"Expected column '{col}' missing from {res.columns}"
    assert "full_name" not in res.columns
    assert "phone" not in res.columns

    # 6. Verify first and last records
    first_tc = res.structured_data[0]
    assert first_tc["test_case_id"] == "TC-001"
    assert first_tc["status"] == "PASS"
    assert "Empty email" in first_tc["description"]

    last_tc = res.structured_data[-1]
    assert last_tc["test_case_id"] == "TC-100"
    assert last_tc["status"] == "PASS"
    assert "TypeScript" in last_tc["description"] or "tsc" in last_tc["description"]

    # 7. Verify document preview has tables and images
    assert res.document_preview is not None
    assert res.document_preview.page_count == 7
    assert len(res.document_preview.page_images) == 7
    assert len(res.document_preview.tables) >= 2


def test_customer_document_not_broken():
    """Verify standard Customer data continues to classify as customer."""
    customer_records = [
        {"customer_id": "CUST-001", "customer_name": "Alice Johnson", "email": "alice@example.com", "phone": "+1-555-0100", "address": "123 Main St"},
        {"customer_id": "CUST-002", "customer_name": "Bob Smith", "email": "bob@example.com", "phone": "+1-555-0101", "address": "456 Oak Ave"},
    ]
    info = classify_domain(customer_records)
    assert info.entity_type == "customer"
    assert "Customer" in info.display_name


def test_invoice_document_not_broken():
    """Verify standard Invoice data continues to classify as invoice."""
    invoice_records = [
        {"invoice_no": "INV-2024-001", "invoice_date": "2024-01-15", "vendor_name": "Acme Corp", "total_amount": 1500.0, "tax_amount": 75.0},
        {"invoice_no": "INV-2024-002", "invoice_date": "2024-01-16", "vendor_name": "Acme Corp", "total_amount": 2500.0, "tax_amount": 125.0},
    ]
    info = classify_domain(invoice_records)
    assert info.entity_type == "invoice"
    assert "Invoice" in info.display_name


def test_test_data_emails_do_not_trigger_customer():
    """Verify that test descriptions with email strings do not classify as Customer."""
    test_text = (
        "Aura Personal AI Voice Assistant – Verification Report\n"
        "Execution Summary: 100 / 100 Test Cases Passed\n"
        "TC-001 Empty email and password email='', password='' emailErr=True 0.2 ms PASS\n"
        "TC-002 Whitespace-only email email=' ', password='***' emailErr=True 0.2 ms PASS\n"
        "TC-003 Register user name='Kiruthik', email='k@aura.ai' Errors: [] 0.2 ms PASS\n"
    )
    info = classify_domain(test_text)
    assert info.entity_type == "technical_test_report"
    assert info.entity_type != "customer"
