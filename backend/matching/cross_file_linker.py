"""
Cross-File Record Linker & Entity Resolution Module

Operates across all files in a multi-file batch to:
1. Normalize comparison fields (Phone, Email, IDs, SKU, VIN, Name, Address, Location).
2. Perform exact matching on high-confidence identifiers (Phone, Email, Customer ID, Store ID, Product SKU, VIN, Invoice No).
3. Perform fuzzy matching on text fields (Name, Address, Location, Product Title).
4. Compute multi-factor relationship confidence scores (0.0 to 1.0).
5. Categorize semantic relationship types (Customer ↔ Product, Customer ↔ Store, Store ↔ Product, Cross-Source Identity).
6. Stamp records with a shared `entity_id` (e.g. 'ENT-001') without altering or merging original content.
7. Construct a comprehensive `relationship_index` for the visual relationship dashboard.
"""
from __future__ import annotations
import re
from typing import Dict, Any, List, Tuple, Optional, Set
import pandas as pd

from backend.models.schemas import ProcessResponse
from backend.normalization.normalizer import normalize_phone, normalize_email
from backend.matching.record_matcher import string_similarity, normalize_match_val

NULL_STRINGS = {"", "null", "none", "nan", "nat", "n/a", "na", "nil", "undefined", "-", "--", "#n/a", "unknown"}


def is_valid_val(val: Any) -> bool:
    if val is None:
        return False
    v = str(val).strip().lower()
    return v not in NULL_STRINGS


def normalize_address(addr: str) -> str:
    """Normalizes address string by standardizing common abbreviations and casing."""
    if not addr:
        return ""
    a = addr.lower().strip()
    replacements = {
        r"\bst\b": "street",
        r"\bave\b": "avenue",
        r"\brd\b": "road",
        r"\bblvd\b": "boulevard",
        r"\bdr\b": "drive",
        r"\bln\b": "lane",
        r"\bapt\b": "apartment",
        r"\bste\b": "suite",
        r"\bfl\b": "floor"
    }
    for pat, rep in replacements.items():
        a = re.sub(pat, rep, a)
    a = re.sub(r"[^\w\s]", " ", a)
    return " ".join(a.split())


def extract_record_keys(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts high-confidence entity match keys from a record:
    - vin: 17-character vehicle identification number or chassis number
    - plate: license plate / registration number
    - phone: normalized E.164 phone string
    - email: normalized lowercase email
    - id_*: customer_id, store_id, product_id, sku, invoice_no, emp_id, student_id, patient_id
    - name: normalized person, vehicle, or store name
    - address: normalized street address
    - location: city/state/region
    """
    keys: Dict[str, Any] = {}
    if not record or not isinstance(record, dict):
        return keys

    for k, v in record.items():
        if not is_valid_val(v):
            continue
        k_clean = str(k).strip().lower().replace("-", "_").replace(" ", "_")
        v_str = str(v).strip()

        # 1. VIN / Vehicle ID match key (Priority 1 for automotive)
        if k_clean in ("vin", "vehicle_identification_number", "chassis_number", "chassis_no", "vehicle_id", "car_id"):
            clean_vin = re.sub(r"[^A-HJ-NPR-Z0-9]", "", v_str.upper())
            if len(clean_vin) == 17:
                keys["vin"] = clean_vin
            elif len(clean_vin) >= 6:
                keys["id_vin"] = clean_vin

        # 2. License Plate
        elif k_clean in ("license_plate", "plate_number", "plate_no", "reg_no", "registration_number"):
            clean_plate = re.sub(r"[\s\-]", "", v_str.upper())
            if len(clean_plate) >= 4:
                keys["plate"] = clean_plate

        # 3. Phone number match key
        elif "phone" in k_clean or "mobile" in k_clean or "contact" in k_clean:
            norm_p = normalize_phone(v_str) or re.sub(r"[^\d+]", "", v_str)
            if norm_p and len(re.sub(r"\D", "", norm_p)) >= 7:
                digits = re.sub(r"\D", "", norm_p)
                keys["phone"] = digits[-10:] if len(digits) >= 10 else digits

        # 4. Email match key
        elif "email" in k_clean:
            norm_e = normalize_email(v_str) or v_str.lower()
            if "@" in norm_e:
                keys["email"] = norm_e

        # 5. Primary Identity & Domain Unique Keys
        elif k_clean in (
            "invoice_no", "invoice_num", "invoice_number", "bill_no", "bill_number",
            "emp_id", "employee_id", "staff_id", "worker_id",
            "student_id", "roll_no", "roll_number", "registration_no", "admission_no",
            "patient_id", "mrn", "medical_record_number", "case_id",
            "customer_id", "cust_id", "user_id", "member_id", "client_id"
        ):
            clean_id = normalize_match_val(v_str).upper()
            if len(clean_id) >= 2:
                key_prefix = k_clean
                if k_clean in ("invoice_no", "invoice_num", "invoice_number", "bill_no", "bill_number"):
                    key_prefix = "invoice_no"
                elif k_clean in ("emp_id", "employee_id", "staff_id", "worker_id"):
                    key_prefix = "emp_id"
                elif k_clean in ("student_id", "roll_no", "roll_number", "registration_no", "admission_no"):
                    key_prefix = "student_id"
                elif k_clean in ("patient_id", "mrn", "medical_record_number", "case_id"):
                    key_prefix = "patient_id"
                elif k_clean in ("customer_id", "cust_id", "user_id", "member_id", "client_id"):
                    key_prefix = "customer_id"

                keys[f"id_{key_prefix}"] = clean_id

        # 6. Name / Title key
        elif k_clean in ("name", "customer_name", "full_name", "store_name", "product_name", "model", "car_model", "student_name", "patient_name", "employee_name"):
            clean_name = normalize_match_val(v_str)
            if len(clean_name) >= 3:
                keys["name"] = clean_name

        # 7. Address key
        elif "address" in k_clean or "street" in k_clean:
            norm_addr = normalize_address(v_str)
            if len(norm_addr) >= 5:
                keys["address"] = norm_addr

        # 8. City / Location key
        elif k_clean in ("city", "location", "town", "branch_city", "store_city"):
            clean_loc = normalize_match_val(v_str)
            if len(clean_loc) >= 2:
                keys["city"] = clean_loc

    return keys


class UnionFind:
    """Disjoint-set data structure to cluster records sharing keys."""
    def __init__(self):
        self.parent: Dict[str, str] = {}

    def find(self, item: str) -> str:
        if item not in self.parent:
            self.parent[item] = item
            return item
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, item_a: str, item_b: str):
        root_a = self.find(item_a)
        root_b = self.find(item_b)
        if root_a != root_b:
            self.parent[root_b] = root_a


def determine_relationship_type(entity_types: Set[str], is_cross_file: bool) -> str:
    """
    Categorizes the business relationship based on the entity domains involved.
    Examples:
    - Customer ↔ Product
    - Customer ↔ Store
    - Store ↔ Product
    - Customer ↔ Transaction
    - Cross-Source Identity Link
    """
    clean_types = {t.lower() for t in entity_types if t and t != "unknown"}
    
    if "customer" in clean_types and ("item" in clean_types or "product" in clean_types):
        return "Customer ↔ Product"
    elif "customer" in clean_types and "store" in clean_types:
        return "Customer ↔ Store"
    elif "store" in clean_types and ("item" in clean_types or "product" in clean_types):
        return "Store ↔ Product"
    elif "customer" in clean_types and ("transaction" in clean_types or "invoice" in clean_types):
        return "Customer ↔ Transaction"
    elif "transaction" in clean_types and ("item" in clean_types or "product" in clean_types):
        return "Transaction ↔ Product"
    elif "car" in clean_types or "vehicle" in clean_types:
        return "Vehicle & Owner Record"
    elif "student" in clean_types or "academic" in clean_types:
        return "Student & Academic Record"
    elif "employee" in clean_types:
        return "Employee & Department Link"
    elif "medical" in clean_types:
        return "Patient & Medical Record"
    elif is_cross_file:
        return "Cross-Source Identity Link"
    else:
        return "Internal Record Cluster"


def calculate_cluster_confidence(grecs: List[Dict[str, Any]]) -> Tuple[float, str, List[str]]:
    """
    Calculates overall match confidence (0.0 - 1.0) and match reason for an entity cluster.
    Exact ID / Phone / Email: 0.95 - 0.99
    Fuzzy Name / Address: 0.85 - 0.92
    """
    keys_found: List[str] = []
    has_exact_phone = False
    has_exact_email = False
    has_exact_id = False
    has_vin_or_plate = False
    fuzzy_name_matches = 0
    fuzzy_address_matches = 0

    for g in grecs:
        k = g.get("keys", {})
        if "phone" in k:
            has_exact_phone = True
            keys_found.append(f"Phone: {k['phone']}")
        if "email" in k:
            has_exact_email = True
            keys_found.append(f"Email: {k['email']}")
        if "vin" in k:
            has_vin_or_plate = True
            keys_found.append(f"VIN: {k['vin']}")
        if "plate" in k:
            has_vin_or_plate = True
            keys_found.append(f"Plate: {k['plate']}")
        for key_name, key_val in k.items():
            if key_name.startswith("id_"):
                has_exact_id = True
                keys_found.append(f"{key_name.replace('id_', '').upper()}: {key_val}")
        if "name" in k:
            fuzzy_name_matches += 1
            keys_found.append(f"Name: {k['name']}")
        if "address" in k:
            fuzzy_address_matches += 1
            keys_found.append(f"Address: {k['address']}")

    # Unique keys
    unique_keys = list(dict.fromkeys(keys_found))

    # Calculate confidence
    exact_count = sum([has_exact_phone, has_exact_email, has_exact_id, has_vin_or_plate])
    if exact_count >= 2:
        confidence = 0.99
        method = "Multi-Key Deterministic Match (Exact)"
    elif has_exact_phone or has_exact_email or has_vin_or_plate:
        confidence = 0.97
        method = "Primary Key Match (Exact)"
    elif has_exact_id:
        confidence = 0.95
        method = "Universal ID Match (Exact)"
    elif fuzzy_name_matches >= 2 and fuzzy_address_matches >= 1:
        confidence = 0.90
        method = "Fuzzy Name & Address Match"
    elif fuzzy_name_matches >= 2:
        confidence = 0.87
        method = "Fuzzy Name Similarity Match"
    else:
        confidence = 0.85
        method = "Heuristic Attribute Match"

    return confidence, method, unique_keys


def link_batch_records(
    results: List[ProcessResponse],
    min_cluster_size: int = 3
) -> Tuple[List[ProcessResponse], Dict[str, Any]]:
    """
    Performs cross-file entity resolution on a batch of ProcessResponses:
    1. Extracts match keys across all records in all files.
    2. Clusters records by shared match keys (Phone, Email, ID, VIN, Name, Address).
    3. Calculates relationship confidence scores and assigns relationship types.
    4. Stamps each record with `entity_id` when 3 or more matching records/links are found.
    5. Builds and returns the comprehensive `relationship_index`.
    """
    if not results:
        return results, {
            "total_entities_linked": 0,
            "cross_file_entities_count": 0,
            "average_confidence": 0.0,
            "relationship_types_breakdown": {},
            "entities": []
        }

    # Flatten all records into a global list with file origin pointers
    global_records: List[Dict[str, Any]] = []
    
    for file_idx, res in enumerate(results):
        filename = res.filename or f"file_{file_idx + 1}"
        file_type = res.file_type or "data"
        entity_domain = res.entity_info.entity_type if res.entity_info else "general"
        
        # Handle structured data (list of dicts)
        if isinstance(res.structured_data, list):
            for row_idx, row in enumerate(res.structured_data):
                if isinstance(row, dict):
                    global_records.append({
                        "global_id": f"f{file_idx}_r{row_idx}",
                        "file_index": file_idx,
                        "filename": filename,
                        "file_type": file_type,
                        "entity_domain": entity_domain,
                        "row_index": row_idx,
                        "record": row,
                        "keys": extract_record_keys(row)
                    })
        # Handle single-entity / unstructured fields extracted as record
        elif res.fields:
            field_dict = {f.key: f.value for f in res.fields if f.value is not None}
            global_records.append({
                "global_id": f"f{file_idx}_r0",
                "file_index": file_idx,
                "filename": filename,
                "file_type": file_type,
                "entity_domain": entity_domain,
                "row_index": 0,
                "record": field_dict,
                "keys": extract_record_keys(field_dict)
            })

    if len(global_records) < min_cluster_size:
        return results, {
            "total_entities_linked": 0,
            "cross_file_entities_count": 0,
            "average_confidence": 0.0,
            "relationship_types_breakdown": {},
            "entities": []
        }

    uf = UnionFind()
    key_to_records: Dict[str, List[str]] = {}

    # Step 1: Exact Key Indexing (Phone, Email, ID, VIN, Plate)
    for grec in global_records:
        gid = grec["global_id"]
        keys = grec["keys"]
        for k_type, k_val in keys.items():
            if k_type not in ("name", "address", "city"):  # Names & Addresses use fuzzy matching
                full_key = f"{k_type}:{k_val}"
                if full_key not in key_to_records:
                    key_to_records[full_key] = []
                key_to_records[full_key].append(gid)

    # Union records that share phone, email, VIN, or domain IDs
    for full_key, gids in key_to_records.items():
        first_gid = gids[0]
        for other_gid in gids[1:]:
            uf.union(first_gid, other_gid)

    # Step 2: Fuzzy Name & Address Linking for records
    unlinked_with_name = [
        grec for grec in global_records
        if "name" in grec["keys"] and not any(k in grec["keys"] for k in ("phone", "email", "vin"))
    ]

    for i in range(len(unlinked_with_name)):
        for j in range(i + 1, len(unlinked_with_name)):
            rec_a = unlinked_with_name[i]
            rec_b = unlinked_with_name[j]
            # Prioritize connecting across different files
            if rec_a["file_index"] != rec_b["file_index"]:
                name_a = rec_a["keys"]["name"]
                name_b = rec_b["keys"]["name"]
                sim = string_similarity(name_a, name_b)
                if sim >= 0.88:
                    uf.union(rec_a["global_id"], rec_b["global_id"])
                elif sim >= 0.80 and "city" in rec_a["keys"] and "city" in rec_b["keys"]:
                    if rec_a["keys"]["city"] == rec_b["keys"]["city"]:
                        uf.union(rec_a["global_id"], rec_b["global_id"])

    # Step 3: Group into Entity Clusters
    clusters: Dict[str, List[Dict[str, Any]]] = {}
    for grec in global_records:
        root = uf.find(grec["global_id"])
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(grec)

    # Filter clusters: only clusters with 3 or more matching records
    entity_counter = 1
    relationship_entities: List[Dict[str, Any]] = []
    type_breakdown: Dict[str, int] = {}
    total_confidence_sum = 0.0

    for root, grecs in clusters.items():
        files_set = {g["filename"] for g in grecs}
        is_cross_file = len(files_set) > 1
        
        # Require 3 or more matched records
        if len(grecs) < min_cluster_size:
            continue

        entity_id = f"ENT-{entity_counter:03d}"
        entity_counter += 1

        confidence, match_method, unique_keys = calculate_cluster_confidence(grecs)
        total_confidence_sum += confidence

        # Determine display name
        entity_name_candidate = None
        for g in grecs:
            rec = g["record"]
            candidate = rec.get("name") or rec.get("customer_name") or rec.get("store_name") or rec.get("product_name") or rec.get("make") or rec.get("model") or rec.get("student_name")
            if candidate and not entity_name_candidate:
                entity_name_candidate = str(candidate).strip()

        # Determine semantic relationship type
        domains_set = {g["entity_domain"] for g in grecs}
        rel_type = determine_relationship_type(domains_set, is_cross_file)
        type_breakdown[rel_type] = type_breakdown.get(rel_type, 0) + 1

        primary_match_label = unique_keys[0] if unique_keys else (f"Name: {entity_name_candidate}" if entity_name_candidate else "Multi-Field Match")

        # Stamp entity_id on every record
        entity_members = []
        for g in grecs:
            g["record"]["entity_id"] = entity_id
            
            # Ensure entity_id is in response columns list
            res_target = results[g["file_index"]]
            if res_target.columns and "entity_id" not in res_target.columns:
                res_target.columns.insert(0, "entity_id")

            entity_members.append({
                "filename": g["filename"],
                "file_type": g["file_type"],
                "entity_domain": g["entity_domain"],
                "row_index": g["row_index"] + 1,
                "record": g["record"]
            })

        relationship_entities.append({
            "entity_id": entity_id,
            "primary_match_key": primary_match_label,
            "display_name": entity_name_candidate or entity_id,
            "relationship_type": rel_type,
            "confidence_score": round(confidence, 2),
            "confidence_percent": f"{int(confidence * 100)}%",
            "match_method": match_method,
            "matched_keys": unique_keys,
            "files_involved": list(files_set),
            "records_count": len(grecs),
            "is_cross_file": is_cross_file,
            "records": entity_members
        })

    # Sort relationship entities: cross-file entities first, then highest records count
    relationship_entities.sort(key=lambda x: (x["is_cross_file"], x["records_count"], x["confidence_score"]), reverse=True)

    avg_conf = round(total_confidence_sum / len(relationship_entities), 2) if relationship_entities else 0.0

    relationship_index = {
        "total_entities_linked": len(relationship_entities),
        "cross_file_entities_count": sum(1 for e in relationship_entities if e["is_cross_file"]),
        "total_records_processed": len(global_records),
        "average_confidence": avg_conf,
        "relationship_types_breakdown": type_breakdown,
        "entities": relationship_entities
    }

    return results, relationship_index
