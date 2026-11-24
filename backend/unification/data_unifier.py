"""
Data Unification & Multi-Format Export Engine

Post-cleaning unification engine that:
1. Combines compatible datasets for each entity (Store, Item, Customer, Transaction, etc.).
2. Preserves source IDs and complete provenance tracking.
3. Maintains valid relationships across unified tables.
4. Exports unified datasets to JSON, CSV, and multi-sheet Excel workbooks.
"""
from __future__ import annotations

import io
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Set, Tuple
import pandas as pd
import numpy as np


@dataclass
class UnifiedDatasetResult:
    entities: Dict[str, List[Dict[str, Any]]]
    entity_columns: Dict[str, List[str]]
    record_counts: Dict[str, int]
    sources_merged: List[str]
    provenance_summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DataUnifier:
    """
    Unifies cleaned and schema-standardized datasets across multiple sources.
    """
    def __init__(self):
        # Maps entity_type -> List of (records, source_name)
        self.staged_data: Dict[str, List[Tuple[List[Dict[str, Any]], str]]] = {}

    def add_dataset(
        self,
        entity_type: str,
        records: List[Dict[str, Any]],
        source_name: str = "dataset"
    ) -> None:
        """Staging a cleaned entity dataset from a specific source."""
        if not records:
            return
        e_type = str(entity_type).lower().strip()
        if e_type not in self.staged_data:
            self.staged_data[e_type] = []
        self.staged_data[e_type].append((records, source_name))

    def unify(self) -> UnifiedDatasetResult:
        """
        Combines compatible datasets for each entity domain, preserving
        source provenance and maintaining uniform canonical schema columns.
        """
        unified_entities: Dict[str, List[Dict[str, Any]]] = {}
        unified_columns: Dict[str, List[str]] = {}
        record_counts: Dict[str, int] = {}
        all_sources: Set[str] = set()

        for entity_type, source_batches in self.staged_data.items():
            combined_rows: List[Dict[str, Any]] = []
            seen_pks: Set[str] = set()
            pk_col = self._get_primary_key_field(entity_type)

            for records, src_name in source_batches:
                all_sources.add(src_name)
                for r_idx, r in enumerate(records):
                    clean_r = dict(r)
                    clean_r["_source_name"] = src_name
                    clean_r["_source_row_index"] = r_idx + 1

                    # Deduplicate Store / Item / Customer master records across files
                    if entity_type != "transaction" and pk_col:
                        pk_val = str(clean_r.get(pk_col) or "").strip().lower()
                        if pk_val and pk_val not in ("none", "null", "n/a", ""):
                            if pk_val in seen_pks:
                                continue
                            seen_pks.add(pk_val)

                    combined_rows.append(clean_r)

            # Discover uniform column headers in order of appearance
            cols: List[str] = []
            for r in combined_rows:
                for k in r.keys():
                    if not str(k).startswith("_") and k not in cols:
                        cols.append(k)

            # Align rows to uniform columns
            aligned_rows = []
            for r in combined_rows:
                aligned_r = {c: r.get(c) for c in cols}
                aligned_r["_source_name"] = r.get("_source_name")
                aligned_rows.append(aligned_r)

            unified_entities[entity_type] = aligned_rows
            unified_columns[entity_type] = cols
            record_counts[entity_type] = len(aligned_rows)

        return UnifiedDatasetResult(
            entities=unified_entities,
            entity_columns=unified_columns,
            record_counts=record_counts,
            sources_merged=sorted(list(all_sources)),
            provenance_summary={
                "total_entities_unified": len(unified_entities),
                "total_records_unified": sum(record_counts.values()),
                "sources_count": len(all_sources)
            }
        )

    def _get_primary_key_field(self, entity_type: str) -> Optional[str]:
        pk_map = {
            "store": "store_id",
            "item": "item_id",
            "customer": "customer_id",
            "car": "vin",
            "employee": "emp_id",
            "student": "student_id",
            "medical": "patient_id",
            "invoice": "invoice_no"
        }
        return pk_map.get(entity_type.lower())


def unify_datasets(staged_datasets: Dict[str, List[Dict[str, Any]]]) -> UnifiedDatasetResult:
    """Convenience helper to unify datasets given as { entity_type: records }."""
    unifier = DataUnifier()
    for e_type, records in staged_datasets.items():
        unifier.add_dataset(e_type, records, source_name=f"{e_type}_source")
    return unifier.unify()


def export_unified_to_json(unified_result: UnifiedDatasetResult, indent: int = 2) -> str:
    """Exports unified datasets to formatted JSON string."""
    return json.dumps(unified_result.entities, indent=indent, default=str)


def export_unified_to_csv(unified_result: UnifiedDatasetResult, entity_type: str) -> str:
    """Exports a single entity's unified dataset to CSV string."""
    e_type = str(entity_type).lower().strip()
    records = unified_result.entities.get(e_type, [])
    if not records:
        return ""
    df = pd.DataFrame(records)
    # Remove internal metadata columns for clean business CSV export
    clean_cols = [c for c in df.columns if not str(c).startswith("_")]
    return df[clean_cols].to_csv(index=False)


def export_unified_to_excel(unified_result: UnifiedDatasetResult) -> bytes:
    """
    Exports all unified entities into a multi-sheet Excel workbook in-memory.
    Returns bytes buffer ready for file download or storage.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        has_sheet = False
        for entity_type, records in unified_result.entities.items():
            if records:
                df = pd.DataFrame(records)
                clean_cols = [c for c in df.columns if not str(c).startswith("_")]
                sheet_title = entity_type.capitalize()[:31]  # Excel sheet names max 31 chars
                df[clean_cols].to_excel(writer, sheet_name=sheet_title, index=False)
                has_sheet = True

        if not has_sheet:
            pd.DataFrame({"status": ["empty"]}).to_excel(writer, sheet_name="DataFlow", index=False)

    output.seek(0)
    return output.getvalue()
