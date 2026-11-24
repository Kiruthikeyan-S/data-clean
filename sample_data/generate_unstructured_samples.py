"""
Generator for comprehensive unstructured sample datasets.
Creates min 50 unstructured records for each of:
1. Shipping Labels (USPS, FedEx, UPS, DHL)
2. Receipts & Invoices
3. Book & Educational Chapters / Modules
4. Technical Test Reports (TC-001 to TC-050)
5. Business Cards & Professional Profiles
"""

import os
import random

os.makedirs("sample_data/unstructured", exist_ok=True)

# 1. 50 Shipping Labels
carriers = [
    ("USPS", "PRIORITY MAIL 2-DAY", "$8.45"),
    ("USPS", "GROUND ADVANTAGE", "$6.20"),
    ("USPS", "EXPRESS MAIL", "$28.75"),
    ("FEDEX", "STANDARD OVERNIGHT", "$34.50"),
    ("FEDEX", "2DAY", "$18.90"),
    ("UPS", "GROUND", "$12.30"),
    ("UPS", "NEXT DAY AIR", "$42.10"),
    ("DHL", "EXPRESS WORLDWIDE", "$55.00"),
]

senders = [
    ("Apex Supply Co.", "100 Industrial Pkwy, Cleveland, OH 44101"),
    ("Global Tech Direct", "450 Technology Way, Austin, TX 78701"),
    ("Nordic Apparel LLC", "88 Market St, Seattle, WA 98101"),
    ("Pacific Books & Media", "1200 Sunset Blvd, Los Angeles, CA 90028"),
    ("Sunrise Health Products", "300 Sunshine Way, Miami, FL 33101"),
    ("Metro Electronics", "75 5th Ave, New York, NY 10003"),
    ("Peak Gear Outfitters", "1400 Mountain Rd, Denver, CO 80202"),
    ("Precision Tools Inc.", "22 Factory Lane, Detroit, MI 48201"),
]

recipients = [
    ("Alice Walker", "Horizon Labs", "742 Evergreen Terrace, Springfield, IL 62704"),
    ("Robert Davis", "Starlight Media", "120 Maple Ave, Apt 4B, Boston, MA 02115"),
    ("Samantha Patel", "Quantum Innovations", "890 Pine Rd, San Jose, CA 95112"),
    ("David Miller", "Evergreen Consulting", "345 Elm St, Portland, OR 97201"),
    ("Elena Rostova", "BioDynamics Corp", "550 Lakeview Dr, Minneapolis, MN 55401"),
    ("Marcus Johnson", "Apex Financial", "901 Peachtree St, Atlanta, GA 30309"),
    ("Chloe Dupont", "Studio Designworks", "670 Broadway, New York, NY 10012"),
    ("Liam O'Connor", "Emerald Logistics", "210 Riverfront Ave, Chicago, IL 60601"),
    ("Sophia Zhang", "Nexus Cloud Solutions", "404 Silicon Way, San Diego, CA 92101"),
    ("Carlos Mendoza", "Solaris Energy", "180 Desert Palm Way, Phoenix, AZ 85001"),
]

instructions = [
    "Leave at front door if no response",
    "Signature required upon delivery",
    "Fragile - handle with care",
    "Deliver to building reception / loading dock",
    "Do not bend or crush",
    "Keep dry - sensitive electronic components",
    "Deliver between 9 AM and 5 PM weekdays",
]

shipping_label_entries = []
for i in range(1, 51):
    carrier, service, postage = carriers[i % len(carriers)]
    sender_name, sender_addr = senders[i % len(senders)]
    rec_name, rec_comp, rec_addr = recipients[i % len(recipients)]
    inst = instructions[i % len(instructions)]
    
    if carrier == "USPS":
        tracking = f"9400111899562541{100000 + i}"
    elif carrier == "FEDEX":
        tracking = f"79498214{200000 + i}"
    elif carrier == "UPS":
        tracking = f"1Z9999999{10000000 + i}"
    else:
        tracking = f"DHL8849102{10000 + i}"

    entry = f"""======================================================================
SHIPPING LABEL #{i:02d} - {carrier} LOGISTICS MANIFEST
======================================================================
CARRIER: {carrier}
SERVICE TYPE: {service}
TRACKING NUMBER: {tracking}
POSTAGE PAID: {postage}
DATE ISSUED: 2026-11-{(i % 28) + 1:02d}

SHIP FROM (SENDER):
  Name: {sender_name}
  Address: {sender_addr}
  Contact Phone: +1-555-{(100 + i):03d}-{(4000 + i):04d}

DELIVER TO (RECIPIENT):
  Recipient Name: {rec_name}
  Company: {rec_comp}
  Delivery Address: {rec_addr}
  Postal Code: {rec_addr.split()[-1]}

PACKAGE DETAILS:
  Weight: {(i * 0.45) % 15 + 0.8:.2f} LBS
  Dimensions: 12 x 9 x 4 IN
  Delivery Instructions: {inst}
  Barcode Checksum: {tracking}*CHK{i:03d}
"""
    shipping_label_entries.append(entry)

with open("sample_data/unstructured/50_shipping_labels.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(shipping_label_entries))


# 2. 50 Receipts & Invoices
stores = [
    ("Blue Horizon Bistro", "Dining & Hospitality", "45 Waterfront Way, San Francisco, CA"),
    ("TechGear Outlet", "Consumer Electronics", "1024 Circuit Blvd, San Jose, CA"),
    ("Organic Valley Supermarket", "Groceries & Produce", "890 Farmer Ave, Denver, CO"),
    ("Urban Outfitters Depot", "Apparel & Retail", "520 Fashion Square, New York, NY"),
    ("Prime Auto Services", "Automotive & Maintenance", "310 Mechanic Dr, Detroit, MI"),
    ("Green Thumb Nurseries", "Home & Garden", "77 Botanical Way, Portland, OR"),
    ("Apex Office Furniture", "Commercial Equipment", "600 Executive Blvd, Chicago, IL"),
    ("Skyline Books & Cafe", "Books & Beverages", "412 University Ave, Boston, MA"),
]

receipt_entries = []
for i in range(1, 51):
    store_name, category, address = stores[i % len(stores)]
    rcpt_no = f"INV-2026-{8000 + i}"
    date = f"2026-11-{(i % 28) + 1:02d}"
    subtotal = round(25.50 + (i * 14.75) % 350, 2)
    tax = round(subtotal * 0.0825, 2)
    total = round(subtotal + tax, 2)
    pay_method = ["VISA ****4892", "Mastercard ****1204", "AMEX ****8019", "Apple Pay", "Cash"][i % 5]

    entry = f"""----------------------------------------------------------------------
RECEIPT / TAX INVOICE #{i:02d}
----------------------------------------------------------------------
Merchant: {store_name} ({category})
Location: {address}
Receipt No: {rcpt_no}
Transaction Date: {date} 14:{(i * 7) % 60:02d}:{(i * 13) % 60:02d}
Cashier ID: EMP-{(i % 12) + 101}

Purchased Line Items:
  1. Standard Item Pack A         Qty: 1    Price: ${(subtotal * 0.6):.2f}
  2. Supplemental Product B       Qty: 2    Price: ${(subtotal * 0.3):.2f}
  3. Service & Handling           Qty: 1    Price: ${(subtotal * 0.1):.2f}

Subtotal: ${subtotal:.2f}
State Tax (8.25%): ${tax:.2f}
Total Amount: ${total:.2f}
Payment Method: {pay_method}
Authorization Code: AUTH_{(i * 9876) % 90000 + 10000}

Thank you for your patronage! Please retain this receipt for warranty and returns.
"""
    receipt_entries.append(entry)

with open("sample_data/unstructured/50_receipts_invoices.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(receipt_entries))


# 3. 50 Book & Educational Chapters / Modules
chapters = [
    ("Machine Learning Systems", "Foundations of Supervised Learning Algorithms and Empirical Loss Minimization"),
    ("Distributed Data Pipelines", "Partitioning Strategies, Sharding Keys, and Fault-Tolerant Rebalancing"),
    ("Enterprise Schema Normalization", "First through Fifth Normal Forms and Canonical Domain Mappings"),
    ("Entity Matching & Deduplication", "Deterministic and Probabilistic Record Linkage using Jaro-Winkler Metrics"),
    ("Natural Language Processing", "Tokenization, Transformer Architectures, and Multi-Head Attention Mechanisms"),
    ("Computer Vision and OCR", "Spatial Bounding Box Extraction, Deskewing, and Morphological Operations"),
    ("Cloud Native Microservices", "Container Orchestration, Sidecar Patterns, and Ingress Route Optimization"),
    ("Relational Database Optimization", "B-Tree Indexes, Query Execution Plans, and ACID Transaction Isolation"),
    ("Time Series Forecasting", "Autoregressive Integrated Moving Averages and Deep Demand Prediction Models"),
    ("Data Quality Engineering", "Completeness, Uniqueness, Validity, Timeliness, and Accuracy Assessment"),
]

book_entries = []
for i in range(1, 51):
    title, desc = chapters[i % len(chapters)]
    chap_num = i
    page_start = (i - 1) * 18 + 1
    page_end = page_start + 17

    entry = f"""Chapter {chap_num}: {title} (Part {((i - 1) // 10) + 1})
Book: Comprehensive Foundations of Applied Data Science and Intelligent Systems
Author: Dr. Marcus Vance & Dr. Elena Rostova
Page Range: pp. {page_start}-{page_end}

Section {chap_num}.1: Core Theoretical Principles
{desc}. In this comprehensive chapter, students and practitioners examine the structural mathematical foundation, underlying assumptions, and algorithmic trade-offs inherent in modern data architectures.

Section {chap_num}.2: Practical Implementation and Case Studies
Real-world industrial deployment demonstrates that raw data ingestion frequently introduces non-deterministic noise, disparate unicode encodings, and referential integrity discrepancies. We review empirical benchmarks across 10,000 production transactions.

Key Takeaways for Chapter {chap_num}:
  - Standardize schema definitions prior to distributed ingestion.
  - Implement idempotent retry semantics across all pipeline workers.
  - Continuously audit data quality metrics against predetermined SLA thresholds.

Review Exercises: Questions 1 through 10 on page {page_end}.
"""
    book_entries.append(entry)

with open("sample_data/unstructured/50_book_educational_chapters.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(book_entries))


# 4. 50 Technical Test Reports (TC-001 to TC-050)
modules = [
    ("OCR Text Extractor", "Extract text from high-resolution scanned document", "PDF bytes (1.2MB)", "Complete text extracted with confidence >= 95%"),
    ("Barcode Detector", "Identify 1D Code 128 and 2D QR Code barcodes", "PNG image bytes", "Barcode format and payload decoded accurately"),
    ("Unicode Normalizer", "Clean non-printable characters and standardize NFKC", "String with zero-width spaces", "Sanitized string with proper linebreaks"),
    ("Schema Mapper", "Map source attributes to canonical domain schema", "Disparate column dictionary", "Columns standardized to canonical keys"),
    ("Entity Splitter", "Disentangle mixed multi-entity customer-store table", "Combined CSV records", "Isolated Store, Item, Customer and Transaction tables"),
    ("Duplicate Resolver", "Merge duplicate customer records reversibly", "Dual profile records with matching phone", "Single merged record stamped with reversible history"),
    ("Date Standardizer", "Convert international date strings to ISO-8601", "Text dates in MM/DD/YYYY and DD.MM.YYYY", "Normalized to YYYY-MM-DD"),
    ("Phone Formatter", "Standardize diverse phone numbers to E.164", "Raw numbers with dashes, spaces and dots", "Clean standardized phone number with country code"),
    ("Currency Normalizer", "Extract currency symbols and numeric amount", "Strings containing '$1,299.99' and '₹45,000'", "Numeric amount and currency code separated cleanly"),
    ("Referential Integrity Auditor", "Verify foreign key consistency across tables", "Transaction records linked to store IDs", "Zero orphaned records flagged"),
]

test_report_entries = []
for i in range(1, 51):
    mod, desc, inp, exp = modules[(i - 1) % len(modules)]
    tc_id = f"TC-{i:03d}"
    lat = round(0.12 + (i * 0.03) % 0.85, 2)
    act = exp

    entry = f"""TC-{i:03d}
Verification of {mod}: {desc}
Input Payload: {inp}
Expected Output: {exp}
Actual Output: {act}
Execution Latency: {lat} ms PASS"""
    test_report_entries.append(entry)

report_header = """================================================================================
AURA ENTERPRISE INTELLIGENCE SYSTEM - 50-TEST-CASE VERIFICATION REPORT
================================================================================
Test Suite: DataFlow Core Quality, OCR & Extraction Verification Suite
Execution Target: Python 3.14 Enterprise Engine / FastAPI Backend
Summary:
  Total Test Cases: 50
  Passed Test Cases: 50
  Failed Test Cases: 0
  Success Rate: 100.0%
================================================================================

"""
with open("sample_data/unstructured/50_technical_test_reports.txt", "w", encoding="utf-8") as f:
    f.write(report_header + "\n\n".join(test_report_entries))


# 5. 50 Business Cards / Professional Profiles
titles = [
    "Chief Technology Officer", "Lead Data Architect", "Senior Machine Learning Engineer",
    "Director of Product Management", "Principal Cloud Engineer", "Head of Quality Engineering",
    "VP of Business Intelligence", "Senior Frontend Architect", "Database Administrator",
    "Enterprise AI Solutions Architect"
]

companies = [
    ("Aura Dynamics Labs", "auradynamics.io", "San Francisco, CA"),
    ("Quantum Scale Systems", "quantumscale.tech", "Seattle, WA"),
    ("Horizon Analytics Corp", "horizonanalytics.com", "New York, NY"),
    ("Summit Software Inc", "summitsoft.net", "Austin, TX"),
    ("Apex Cloud Solutions", "apexcloud.org", "Chicago, IL"),
]

names = [
    ("Alexander Wright", "a.wright"),
    ("Sophia Chen", "s.chen"),
    ("Marcus Sterling", "m.sterling"),
    ("Elena Rostova", "e.rostova"),
    ("David Kim", "d.kim"),
    ("Rachel Green", "r.green"),
    ("Julian Morales", "j.morales"),
    ("Emily Watson", "e.watson"),
    ("Vikram Singhania", "v.singhania"),
    ("Claire Beaumont", "c.beaumont"),
]

business_cards = []
for i in range(1, 51):
    name_display, email_prefix = names[(i - 1) % len(names)]
    title = titles[(i - 1) % len(titles)]
    comp_name, comp_web, comp_city = companies[(i - 1) % len(companies)]
    
    unique_name = f"{name_display}" if i <= 10 else f"{name_display} {chr(65 + (i % 26))}."
    email = f"{email_prefix}{i}@{comp_web}"
    phone = f"+1 (555) {(200 + i):03d}-{(5000 + i):04d}"
    
    entry = f"""======================================================================
BUSINESS CARD #{i:02d}
======================================================================
Full Name: {unique_name}
Job Title: {title}
Company: {comp_name}
Email Address: {email}
Phone Number: {phone}
Website: https://www.{comp_web}
Office Location: Suite {(i * 10) + 100}, 500 Market Boulevard, {comp_city} 94105
LinkedIn Profile: https://linkedin.com/in/{email_prefix}-{i}
Department: Enterprise Technology & Innovation Group
"""
    business_cards.append(entry)

with open("sample_data/unstructured/50_business_cards.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(business_cards))

print("Successfully generated all 5 unstructured datasets with 50+ records each in sample_data/unstructured/!")
