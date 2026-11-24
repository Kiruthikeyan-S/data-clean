import pandas as pd
import pytest
from backend.models.entity_schemas import get_canonical_fields, EntityType
from backend.normalization.schema_mapper import (
    find_canonical_field_for_header,
    SchemaMappingEngine,
    map_dataframe_to_canonical_schema
)

def test_canonical_alias_lookup():
    store_fields = get_canonical_fields(EntityType.STORE.value)
    target, method, conf = find_canonical_field_for_header("store_code", store_fields, "store")
    assert target == "store_id"
    assert method in ("exact", "alias")

    target, method, conf = find_canonical_field_for_header("branch_id", store_fields, "store")
    assert target == "store_id"

    item_fields = get_canonical_fields(EntityType.ITEM.value)
    target, method, conf = find_canonical_field_for_header("product_name", item_fields, "item")
    assert target == "item_name"

    cust_fields = get_canonical_fields(EntityType.CUSTOMER.value)
    target, method, conf = find_canonical_field_for_header("cust_id", cust_fields, "customer")
    assert target == "customer_id"

    target, method, conf = find_canonical_field_for_header("cust_mob", cust_fields, "customer")
    assert target == "phone"

    target, method, conf = find_canonical_field_for_header("ph_no", cust_fields, "customer")
    assert target == "phone"


def test_custom_alias_dictionary():
    engine = SchemaMappingEngine(custom_aliases={"custom_code_x": "store_id"})
    store_fields = get_canonical_fields(EntityType.STORE.value)
    target, method, conf = find_canonical_field_for_header("custom_code_x", store_fields, "store", custom_aliases=engine.custom_aliases)
    assert target == "store_id"
    assert method == "custom_alias"
    assert conf == 1.0


def test_conflict_detection_and_coalesce():
    df = pd.DataFrame({
        "store_id": ["STR_01", "STR_02", "STR_03"],
        "branch_id": ["STR_01", "STR_DIFF", None]  # STR_02 vs STR_DIFF is a conflict!
    })
    engine = SchemaMappingEngine()
    canon_df, report, highlights = engine.map_dataframe(df, "store")
    
    assert "store_id" in canon_df.columns
    rep_item = next(r for r in report if r["canonical_field"] == "store_id")
    assert rep_item["has_conflict"] is True
    assert rep_item["conflict_count"] == 1
    assert "branch_id" in rep_item["source_aliases"]
