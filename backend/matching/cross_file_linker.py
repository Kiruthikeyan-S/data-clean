"""
Cross-File Record Linker & Entity Resolution Module

Operates across all files in a multi-file batch to:
1. Extract match keys (Phone E.164, Email, Universal IDs, Fuzzy Names).
2. Cluster records across different files sharing match keys into logical entities.
3. Stamp records with a shared `entity_id` (e.g. 'ENT-001') without altering or merging original content.
4. Construct a lightweight `relationship_index` mapping entities across all batch files.
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


def extract_record_keys(record: Dict[str, Any]) -> Dict[str, str]:
    """
    Extracts high-confidence entity match keys from a record:
    - vin: 17-character vehicle identification number or chassis number
    - phone: normalized E.164 phone string
    - email: normalized lowercase email
    - id: customer_id, store_id, product_id, invoice_no, emp_id, student_id, patient_id
    - name: normalized person, vehicle, or store name
    """
    keys: Dict[str, str] = {}
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

        # 5. Domain & Universal ID keys
        elif k_clean in (
            "invoice_no", "invoice_num", "invoice_number", "bill_no", "bill_number",
            "emp_id", "employee_id", "staff_id", "worker_id",
            "student_id", "roll_no", "roll_number", "registration_no", "admission_no",
            "patient_id", "mrn", "medical_record_number", "case_id",
            "customer_id", "cust_id", "user_id", "member_id", "client_id",
            "store_id", "branch_id", "outlet_id", "warehouse_id",
            "product_id", "item_id", "sku", "sku_id", "barcode", "upc", "ean"
        ):
            clean_id = normalize_match_val(v_str).upper()
            if len(clean_id) >= 2:
                # Group aliases to canonical key types
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
                elif k_clean in ("store_id", "branch_id", "outlet_id", "warehouse_id"):
                    key_prefix = "store_id"
                elif k_clean in ("product_id", "item_id", "sku", "sku_id", "barcode", "upc", "ean"):
                    key_prefix = "product_id"

                keys[f"id_{key_prefix}"] = clean_id

        # 6. Name key
        elif k_clean in ("name", "customer_name", "full_name", "store_name", "product_name", "model", "car_model"):
            clean_name = normalize_match_val(v_str)
            if len(clean_name) >= 3:
                keys["name"] = clean_name

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


def link_batch_records(
    results: List[ProcessResponse]
) -> Tuple[List[ProcessResponse], Dict[str, Any]]:
    """
    Performs cross-file entity resolution on a batch of ProcessResponses:
    1. Extracts match keys across all records in all files.
    2. Clusters records by shared match keys (Phone, Email, ID, Name).
    3. Stamps each record with `entity_id`.
    4. Builds and returns the comprehensive `relationship_index`.
    """
    if not results:
        return results, {"total_entities_linked": 0, "entities": []}

    # Flatten all records into a global list with file origin pointers
    global_records: List[Dict[str, Any]] = []
    
    for file_idx, res in enumerate(results):
        filename = res.filename or f"file_{file_idx + 1}"
        file_type = res.file_type or "data"
        
        # Handle structured data (list of dicts)
        if isinstance(res.structured_data, list):
            for row_idx, row in enumerate(res.structured_data):
                if isinstance(row, dict):
                    global_records.append({
                        "global_id": f"f{file_idx}_r{row_idx}",
                        "file_index": file_idx,
                        "filename": filename,
                        "file_type": file_type,
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
                "row_index": 0,
                "record": field_dict,
                "keys": extract_record_keys(field_dict)
            })

    if len(global_records) < 2:
        return results, {"total_entities_linked": 0, "entities": []}

    uf = UnionFind()
    key_to_records: Dict[str, List[str]] = {}

    # Step 1: Exact Key Indexing (Phone, Email, ID)
    for grec in global_records:
        gid = grec["global_id"]
        keys = grec["keys"]
        for k_type, k_val in keys.items():
            if k_type != "name":  # Name is handled with fuzzy matching
                full_key = f"{k_type}:{k_val}"
                if full_key not in key_to_records:
                    key_to_records[full_key] = []
                key_to_records[full_key].append(gid)

    # Union records that share phone, email, or domain IDs
    for full_key, gids in key_to_records.items():
        first_gid = gids[0]
        for other_gid in gids[1:]:
            uf.union(first_gid, other_gid)

    # Step 2: Fuzzy Name Linking for records missing phone/email
    unlinked_with_name = [
        grec for grec in global_records
        if "name" in grec["keys"] and not any(k in grec["keys"] for k in ("phone", "email"))
    ]

    for i in range(len(unlinked_with_name)):
        for j in range(i + 1, len(unlinked_with_name)):
            rec_a = unlinked_with_name[i]
            rec_b = unlinked_with_name[j]
            # Only connect across different files
            if rec_a["file_index"] != rec_b["file_index"]:
                name_a = rec_a["keys"]["name"]
                name_b = rec_b["keys"]["name"]
                if string_similarity(name_a, name_b) >= 0.85:
                    uf.union(rec_a["global_id"], rec_b["global_id"])

    # Step 3: Group into Entity Clusters
    clusters: Dict[str, List[Dict[str, Any]]] = {}
    for grec in global_records:
        root = uf.find(grec["global_id"])
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(grec)

    # Filter clusters: only multi-record or cross-file clusters get linked entity IDs
    entity_counter = 1
    relationship_entities: List[Dict[str, Any]] = []

    for root, grecs in clusters.items():
        # Check if cluster spans multiple files or multiple records
        files_set = {g["filename"] for g in grecs}
        is_cross_file = len(files_set) > 1
        
        # Format Entity ID (e.g. ENT-001)
        entity_id = f"ENT-{entity_counter:03d}"
        entity_counter += 1

        # Determine best display label and match key
        matched_keys_found: List[str] = []
        entity_name_candidate = None
        for g in grecs:
            if "vin" in g["keys"]:
                matched_keys_found.append(f"vin: {g['keys']['vin']}")
            if "plate" in g["keys"]:
                matched_keys_found.append(f"plate: {g['keys']['plate']}")
            if "phone" in g["keys"]:
                matched_keys_found.append(f"phone: {g['keys']['phone']}")
            if "email" in g["keys"]:
                matched_keys_found.append(f"email: {g['keys']['email']}")
            for k, v in g["keys"].items():
                if k.startswith("id_"):
                    matched_keys_found.append(f"{k.replace('id_', '')}: {v}")
            if "name" in g["keys"] and not entity_name_candidate:
                entity_name_candidate = g["record"].get("name") or g["record"].get("customer_name") or g["record"].get("store_name") or g["record"].get("make") or g["record"].get("model")

        # Deduplicate matched keys
        seen_keys = set()
        deduped_keys = []
        for mk in matched_keys_found:
            if mk not in seen_keys:
                seen_keys.add(mk)
                deduped_keys.append(mk)

        primary_key_label = deduped_keys[0] if deduped_keys else (f"name: {entity_name_candidate}" if entity_name_candidate else "multi-field match")

        # Stamp entity_id on every record
        entity_members = []
        for g in grecs:
            g["record"]["entity_id"] = entity_id
            
            # Update columns list in response if needed
            res_target = results[g["file_index"]]
            if res_target.columns and "entity_id" not in res_target.columns:
                res_target.columns.insert(0, "entity_id")

            entity_members.append({
                "filename": g["filename"],
                "file_type": g["file_type"],
                "row_index": g["row_index"] + 1,
                "record": g["record"]
            })

        # Only register in relationships index if cross-file or multi-record
        if len(grecs) > 1 or is_cross_file:
            relationship_entities.append({
                "entity_id": entity_id,
                "primary_match_key": primary_key_label,
                "display_name": entity_name_candidate or entity_id,
                "files_involved": list(files_set),
                "records_count": len(grecs),
                "is_cross_file": is_cross_file,
                "records": entity_members
            })

    # Sort relationship entities: cross-file entities first
    relationship_entities.sort(key=lambda x: (x["is_cross_file"], x["records_count"]), reverse=True)

    relationship_index = {
        "total_entities_linked": len(relationship_entities),
        "cross_file_entities_count": sum(1 for e in relationship_entities if e["is_cross_file"]),
        "total_records_processed": len(global_records),
        "entities": relationship_entities
    }

    return results, relationship_index
