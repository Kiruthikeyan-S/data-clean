"""
Schema Knowledge RAG Module

Stores and retrieves domain schema knowledge, column aliases, and abbreviations:
- cust_nm -> customer_name
- mob_no -> phone
- prod_cd -> product_id
- qty -> quantity
- str_nm -> store_name
- mrp -> price

Allows fast semantic retrieval of canonical target fields for unfamiliar columns.
"""
from __future__ import annotations
import uuid
from typing import Dict, Any, List, Optional, Tuple

from backend.rag.embedder import get_embedding
from backend.rag.vector_store import get_vector_collection, VectorDocument
from backend.models.entity_schemas import get_canonical_fields, EntityType

# Common real-world abbreviations & abbreviations mapped to canonical concepts
DEFAULT_SCHEMA_KNOWLEDGE = [
    # Customer
    {"alias": "cust_nm", "canonical": "name", "entity": "customer", "desc": "Customer full or display name"},
    {"alias": "cust_name", "canonical": "name", "entity": "customer", "desc": "Customer full name"},
    {"alias": "client_name", "canonical": "name", "entity": "customer", "desc": "Client full name"},
    {"alias": "buyer_name", "canonical": "name", "entity": "customer", "desc": "Buyer full name"},
    {"alias": "cust_id", "canonical": "customer_id", "entity": "customer", "desc": "Customer unique identifier"},
    {"alias": "cust_no", "canonical": "customer_id", "entity": "customer", "desc": "Customer account number"},
    {"alias": "client_id", "canonical": "customer_id", "entity": "customer", "desc": "Client account number"},
    {"alias": "mob_no", "canonical": "phone", "entity": "customer", "desc": "Mobile contact number"},
    {"alias": "cell_no", "canonical": "phone", "entity": "customer", "desc": "Cellular phone number"},
    {"alias": "ph_num", "canonical": "phone", "entity": "customer", "desc": "Phone contact number"},
    {"alias": "contact_num", "canonical": "phone", "entity": "customer", "desc": "Contact number"},
    {"alias": "mail_addr", "canonical": "email", "entity": "customer", "desc": "Email address"},
    {"alias": "e_mail", "canonical": "email", "entity": "customer", "desc": "Email address"},
    {"alias": "res_addr", "canonical": "address", "entity": "customer", "desc": "Residential address"},
    {"alias": "street_addr", "canonical": "address", "entity": "customer", "desc": "Street address"},
    {"alias": "zip_cd", "canonical": "postal_code", "entity": "customer", "desc": "Postal ZIP code"},
    {"alias": "pin_cd", "canonical": "postal_code", "entity": "customer", "desc": "PIN code"},

    # Item / Product
    {"alias": "prod_cd", "canonical": "product_id", "entity": "item", "desc": "Product or item unique code"},
    {"alias": "prod_id", "canonical": "product_id", "entity": "item", "desc": "Product identifier"},
    {"alias": "item_cd", "canonical": "product_id", "entity": "item", "desc": "Item code"},
    {"alias": "prod_nm", "canonical": "product_name", "entity": "item", "desc": "Product name"},
    {"alias": "item_nm", "canonical": "product_name", "entity": "item", "desc": "Item name"},
    {"alias": "prod_desc", "canonical": "description", "entity": "item", "desc": "Product description"},
    {"alias": "unit_prc", "canonical": "price", "entity": "item", "desc": "Unit selling price"},
    {"alias": "sell_prc", "canonical": "price", "entity": "item", "desc": "Selling price"},
    {"alias": "cost_prc", "canonical": "cost_price", "entity": "item", "desc": "Cost price / purchase price"},
    {"alias": "mrp_val", "canonical": "price", "entity": "item", "desc": "Maximum retail price"},
    {"alias": "qty", "canonical": "stock", "entity": "item", "desc": "Inventory stock quantity"},
    {"alias": "qty_on_hand", "canonical": "stock", "entity": "item", "desc": "Quantity on hand"},
    {"alias": "stk_qty", "canonical": "stock", "entity": "item", "desc": "Stock quantity"},
    {"alias": "mfg_name", "canonical": "brand", "entity": "item", "desc": "Manufacturer / Brand name"},

    # Store
    {"alias": "str_id", "canonical": "store_id", "entity": "store", "desc": "Store unique identifier"},
    {"alias": "str_nm", "canonical": "store_name", "entity": "store", "desc": "Store name"},
    {"alias": "br_id", "canonical": "store_id", "entity": "store", "desc": "Branch identifier"},
    {"alias": "br_nm", "canonical": "store_name", "entity": "store", "desc": "Branch name"},
    {"alias": "out_id", "canonical": "store_id", "entity": "store", "desc": "Outlet identifier"},
    {"alias": "str_loc", "canonical": "address", "entity": "store", "desc": "Store location address"},
    {"alias": "str_mgr", "canonical": "manager_name", "entity": "store", "desc": "Store manager name"},
    {"alias": "br_mgr", "canonical": "manager_name", "entity": "store", "desc": "Branch manager name"}
]


def seed_schema_knowledge(force: bool = False) -> int:
    """Seeds the schema vector collection with canonical schemas and known alias abbreviations."""
    schema_coll = get_vector_collection("schema")
    if not force and schema_coll.count() >= 50:
        return schema_coll.count()

    if force:
        schema_coll.clear()

    docs_to_add = []

    # 1. Add canonical entity schema definitions
    for e_type in ("store", "item", "customer", "transaction"):
        canonical_fields = get_canonical_fields(e_type)
        for field_name, field_def in canonical_fields.items():
            text = f"Canonical schema field '{field_name}' in {e_type} entity. Represents {field_def.description} (type: {field_def.field_type})."
            doc_id = f"canon_{e_type}_{field_name}"
            vec = get_embedding(field_name)
            docs_to_add.append(VectorDocument(
                doc_id=doc_id,
                vector=vec,
                text=text,
                entity_type=e_type,
                cleaned_record={"canonical_field": field_name, "entity_type": e_type, "field_type": field_def.field_type},
                metadata={"type": "canonical_definition", "canonical_field": field_name}
            ))

            # Add each defined alias
            for alias in field_def.aliases:
                alias_text = f"Column header alias '{alias}' maps to canonical field '{field_name}' in {e_type} schema."
                alias_id = f"alias_{e_type}_{field_name}_{alias}"
                alias_vec = get_embedding(alias)
                docs_to_add.append(VectorDocument(
                    doc_id=alias_id,
                    vector=alias_vec,
                    text=alias_text,
                    entity_type=e_type,
                    cleaned_record={"alias": alias, "canonical_field": field_name, "entity_type": e_type},
                    metadata={"type": "alias_mapping", "canonical_field": field_name, "alias": alias}
                ))

    # 2. Add abbreviation dataset
    for item in DEFAULT_SCHEMA_KNOWLEDGE:
        alias = item["alias"]
        canon = item["canonical"]
        e_type = item["entity"]
        text = f"Abbreviated column header '{alias}' maps to canonical field '{canon}' ({item['desc']}) in {e_type} schema."
        doc_id = f"abbr_{e_type}_{canon}_{alias}"
        vec = get_embedding(alias)
        docs_to_add.append(VectorDocument(
            doc_id=doc_id,
            vector=vec,
            text=text,
            entity_type=e_type,
            cleaned_record={"alias": alias, "canonical_field": canon, "entity_type": e_type},
            metadata={"type": "abbreviation_mapping", "canonical_field": canon, "alias": alias}
        ))

    schema_coll.upsert_batch(docs_to_add)
    return schema_coll.count()


# Initialize schema knowledge automatically on module import
try:
    seed_schema_knowledge()
except Exception:
    pass


def retrieve_schema_mapping_for_column(
    raw_column_name: str,
    entity_type: str = "general",
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Searches the Schema Knowledge Base for a given raw/unfamiliar column header.
    Returns the top candidate canonical target fields with similarity scores.
    """
    if not raw_column_name:
        return []

    schema_coll = get_vector_collection("schema")
    if schema_coll.count() == 0:
        seed_schema_knowledge()

    clean_header = str(raw_column_name).strip().lower()
    query_vec = get_embedding(clean_header)
    
    # Optional filter by entity type if specified
    filter_fn = None
    if entity_type and entity_type != "general":
        filter_fn = lambda d: d.entity_type in (entity_type, "general")

    matches = schema_coll.search(query_vec, top_k=top_k, min_score=0.20, filter_fn=filter_fn)
    
    results = []
    seen_canon = set()
    for doc, score in matches:
        canon_field = doc.cleaned_record.get("canonical_field")
        if canon_field and canon_field not in seen_canon:
            seen_canon.add(canon_field)
            results.append({
                "raw_column": raw_column_name,
                "canonical_field": canon_field,
                "entity_type": doc.entity_type,
                "similarity_score": round(score, 3),
                "explanation": doc.text
            })

    return results


def retrieve_batch_schema_mappings(
    columns: List[str],
    entity_type: str = "general"
) -> Dict[str, Dict[str, Any]]:
    """
    Retrieves the best canonical mapping for a list of unfamiliar columns.
    Returns mapping: {raw_col: {"canonical_field": ..., "score": ..., "explanation": ...}}
    """
    mapping_results: Dict[str, Dict[str, Any]] = {}
    for col in columns:
        candidates = retrieve_schema_mapping_for_column(col, entity_type=entity_type, top_k=1)
        if candidates and candidates[0]["similarity_score"] >= 0.30:
            mapping_results[col] = candidates[0]
    return mapping_results
