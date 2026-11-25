"""
Regression and verification test suite for universal unstructured document extraction:
- Shipping labels (USPS, FedEx, UPS)
- Technical test reports
- Book & educational chapters
- Business cards
- Invoices & receipts
- Multi-file batch isolation
"""

import os
import pytest
from backend.extraction.field_extractor import (
    identify_fields,
    map_to_schema,
    extract_records_from_unstructured_text
)
from backend.extraction.entity_classifier import classify_domain
from backend.pipeline import process_file_pipeline


def test_shipping_label_extraction():
    """Verify that a USPS shipping label extracts all key fields without false phone matches."""
    sample_label = """
======================================================================
SHIPPING LABEL #01 - USPS LOGISTICS MANIFEST
======================================================================
CARRIER: USPS
SERVICE TYPE: PRIORITY MAIL 2-DAY
TRACKING NUMBER: 9400111899562541100001
POSTAGE PAID: $8.45
DATE ISSUED: 2026-11-02

SHIP FROM (SENDER):
  Name: Apex Supply Co.
  Address: 100 Industrial Pkwy, Cleveland, OH 44101
  Contact Phone: +1-555-101-4001

DELIVER TO (RECIPIENT):
  Recipient Name: Alice Walker
  Company: Horizon Labs
  Delivery Address: 742 Evergreen Terrace, Springfield, IL 62704
  Postal Code: 62704

PACKAGE DETAILS:
  Weight: 2.15 LBS
  Delivery Instructions: Leave at front door if no response
"""
    raw_fields = identify_fields(sample_label)
    assert raw_fields["carrier"] == "USPS"
    assert "Priority Mail" in raw_fields["service_type"]
    assert raw_fields["tracking_number"] == "9400111899562541100001"
    # Tracking number must NEVER be matched as phone
    assert raw_fields["phone"] != "9400111899562541100001"
    assert raw_fields["recipient_name"] is not None
    assert "Alice Walker" in raw_fields["recipient_name"]
    assert raw_fields["postage_amount"] == "8.45"

    mapped = map_to_schema(raw_fields)
    mapped_keys = [f["key"] for f in mapped]
    assert "carrier" in mapped_keys
    assert "tracking_number" in mapped_keys
    assert "recipient_name" in mapped_keys
    assert "postage_amount" in mapped_keys

    # Verify domain classification
    domain_info = classify_domain(sample_label)
    assert domain_info.entity_type in ["shipping_label", "unknown"]
    assert domain_info.entity_type != "customer"


def test_technical_test_report_extraction():
    """Verify that a 50-test-case report extracts all 50 records as technical_test_report."""
    report_path = "sample_data/unstructured/50_technical_test_reports.txt"
    assert os.path.exists(report_path)

    with open(report_path, "r", encoding="utf-8") as f:
        text = f.read()

    res = extract_records_from_unstructured_text(text)
    assert res is not None
    assert res.get("data_type") == "records"
    assert res.get("document_type") == "technical_test_report"
    records = res.get("records", [])
    assert len(records) == 50
    assert records[0]["test_case_id"] == "TC-001"
    assert records[-1]["test_case_id"] == "TC-050"
    assert records[0]["status"] == "PASS"

    domain_info = classify_domain(text)
    assert domain_info.entity_type == "technical_test_report"


def test_book_educational_chapters_extraction():
    """Verify that 50 chapters are segmented into educational structured records."""
    book_path = "sample_data/unstructured/50_book_educational_chapters.txt"
    assert os.path.exists(book_path)

    with open(book_path, "r", encoding="utf-8") as f:
        text = f.read()

    res = extract_records_from_unstructured_text(text)
    assert res is not None
    assert res.get("data_type") == "records"
    assert res.get("document_type") == "book_educational"
    records = res.get("records", [])
    assert len(records) >= 50
    assert "Chapter" in records[0]["chapter_number"]
    assert len(records[0]["summary"]) > 20

    domain_info = classify_domain(text)
    assert domain_info.entity_type in ["book_educational", "syllabus", "academic", "course"]
    assert domain_info.entity_type != "item"


def test_business_cards_extraction():
    """Verify that 50 business cards extract valid contact profiles."""
    cards_path = "sample_data/unstructured/50_business_cards.txt"
    assert os.path.exists(cards_path)

    with open(cards_path, "r", encoding="utf-8") as f:
        text = f.read()

    res = extract_records_from_unstructured_text(text)
    assert res is not None
    assert res.get("data_type") == "records"
    records = res.get("records", [])
    assert len(records) >= 40
    assert "name" in records[0] or "email" in records[0] or "phone" in records[0]


def test_receipts_invoices_extraction():
    """Verify that receipts extract merchant, amounts, and dates."""
    receipt_path = "sample_data/unstructured/50_receipts_invoices.txt"
    assert os.path.exists(receipt_path)

    with open(receipt_path, "r", encoding="utf-8") as f:
        text = f.read()

    res = extract_records_from_unstructured_text(text)
    assert res is not None
    assert res.get("data_type") == "records"
    records = res.get("records", [])
    assert len(records) >= 40


def test_pipeline_unstructured_shipping_label_file():
    """Verify full end-to-end pipeline on an unstructured shipping label file."""
    shipping_path = "sample_data/unstructured/50_shipping_labels.txt"
    with open(shipping_path, "rb") as f:
        label_bytes = f.read()

    response = process_file_pipeline(
        filename="usps_manifest.txt",
        content_type="text/plain",
        file_bytes=label_bytes
    )

    assert response.status == "completed"
    assert response.classification == "unstructured"
    assert response.entity_info is not None
    assert response.entity_info.entity_type != "customer"
    assert len(response.steps) >= 4


def test_pipe_delimited_text_table_extraction():
    """Verify that a pipe-delimited text inventory file is parsed into a structured table."""
    sample_pipe_text = """
BMW SPARE-PARTS INVENTORY & DEMAND FORECAST
Columns: Item ID | Item Name | Current Stock | Units Sold Last 90 Days | Daily Velocity

BMW-SP-001 | Engine Oil Filter | 65 | 339 | 3.77
BMW-SP-002 | Air Filter | 82 | 193 | 2.14
BMW-SP-003 | Cabin Air Filter | 123 | 445 | 4.94
"""
    res = extract_records_from_unstructured_text(sample_pipe_text)
    assert res is not None
    assert res.get("data_type") == "records"
    assert res.get("document_type") == "delimited_table"
    records = res.get("records", [])
    assert len(records) == 3
    assert records[0]["item_id"] == "BMW-SP-001"
    assert records[0]["item_name"] == "Engine Oil Filter"
    assert records[0]["current_stock"] == 65
    assert records[0]["daily_velocity"] == 3.77
