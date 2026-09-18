"""
Business Entity & Domain Classifier — Multi-Domain Classification Engine

Classifies datasets and unstructured documents into business entity / domain types:
- Store / Branch (store_id)
- Item / Product (product_id / sku)
- Customer / Client (phone / email)
- Transaction / Sales (transaction_id)
- Vehicle / Automotive (vin / license_plate)
- Invoice / Billing Document (invoice_no)
- Employee / HR Record (emp_id)
- Student / Academic Record (student_id / roll_no)
- Medical / Patient Record (patient_id / mrn)

Uses:
  Layer 1: Column-Name / Keyword Matching (with comprehensive aliases)
  Layer 2: Value-Pattern Regex Analysis (VIN, MRN, EMP, PAT, INV, STR, emails, phones, etc.)
  Layer 3: Context / Co-occurrence Rules (multi-signal confirmation & FK resolution)
  Layer 4: Groq LLM Semantic Fallback for ambiguous or complex content
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set, Tuple, Union

import pandas as pd

from backend.models.entity_schemas import (
    get_entity_schemas,
    EntitySchema,
    EntityType,
    CONFIDENCE_THRESHOLD,
)
from backend.models.schemas import EntityClassificationInfo, EntityTableInfo


PRIMARY_MATCH_KEYS: Dict[str, str] = {
    EntityType.CAR.value: "vin",
    EntityType.CUSTOMER.value: "phone",
    EntityType.STORE.value: "store_id",
    EntityType.ITEM.value: "product_id",
    EntityType.TRANSACTION.value: "transaction_id",
    EntityType.INVOICE.value: "invoice_no",
    EntityType.EMPLOYEE.value: "emp_id",
    EntityType.STUDENT.value: "student_id",
    EntityType.MEDICAL.value: "patient_id",
}


@dataclass
class EntityClassificationResult:
    """
    Result of entity classification for a single file/DataFrame.

    Attributes:
        file_type: Overall classification — domain name, 'mixed', or 'unknown'.
        entities_detected: Mapping of entity name → confidence score.
        column_assignments: Mapping of column name → assigned entity name.
        primary_entity: The dominant entity if single-type; None for mixed.
        is_mixed: True when the file contains columns from 2+ entities.
        confidence: Overall classification confidence (0.0–1.0).
        method: 'rule_based' or 'llm_fallback'.
        details: Human-readable explanation of the classification.
        entity_confidence: Per-entity confidence scores (alias for UI).
        display_name: Human readable entity title.
        primary_match_key: Domain match key (e.g. 'vin', 'phone', 'emp_id').
        extracted_fields: List of detected domain fields.
        reasoning: Detailed reasoning explanation.
    """
    file_type: str
    entities_detected: Dict[str, float] = field(default_factory=dict)
    column_assignments: Dict[str, str] = field(default_factory=dict)
    primary_entity: Optional[str] = None
    is_mixed: bool = False
    confidence: float = 0.0
    confidence_score: float = 0.0
    method: str = "rule_based"
    details: str = ""
    entity_confidence: Dict[str, float] = field(default_factory=dict)
    display_name: Optional[str] = None
    primary_match_key: Optional[str] = None
    extracted_fields: Optional[List[str]] = None
    reasoning: Optional[str] = None


# ─── Helpers ────────────────────────────────────────────────────────

def _normalize_col(col: str) -> str:
    """Lowercase, strip, replace spaces/hyphens with underscores."""
    return re.sub(r"[\s\-\.]+", "_", str(col).strip().lower())


def _all_keywords(schema: EntitySchema) -> Set[str]:
    """Returns the union of all keyword tiers for a schema."""
    return schema.strong_keywords | schema.medium_keywords | schema.weak_keywords


# ─── Layer 1: Column-Name Keyword Matching ──────────────────────────

def _score_column_keywords(
    columns: List[str],
    schemas: Dict[str, EntitySchema],
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, str]]:
    """
    Score every column against each entity's keyword dictionaries.

    Returns:
        entity_scores: {entity: {col: weight, ...}, ...}
        column_assignments: {col: best_entity}
    """
    entity_scores: Dict[str, Dict[str, float]] = {e: {} for e in schemas}
    column_assignments: Dict[str, str] = {}

    for raw_col in columns:
        col = _normalize_col(raw_col)

        best_entity: Optional[str] = None
        best_weight: float = 0.0

        for entity_name, schema in schemas.items():
            weight = 0.0

            if col in schema.strong_keywords:
                weight = 1.0
            elif col in schema.medium_keywords:
                weight = 0.6
            elif col in schema.weak_keywords:
                weight = 0.3
            else:
                # Check if any alias matches
                for alias in schema.aliases:
                    if col == alias:
                        weight = 0.95
                        break

            if weight > 0:
                entity_scores[entity_name][raw_col] = weight

            if weight > best_weight:
                best_weight = weight
                best_entity = entity_name

        if best_entity and best_weight > 0:
            column_assignments[raw_col] = best_entity

    return entity_scores, column_assignments


# ─── Layer 2: Value-Pattern Analysis ─────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
_PRICE_RE = re.compile(r"^\$?\d+(?:\.\d{1,2})?$")
_DATE_RE = re.compile(
    r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$|^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$"
)
_PHONE_RE = re.compile(r"^\+?\d{10,15}$")
_VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$", re.IGNORECASE)
_PLATE_RE = re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$", re.IGNORECASE)
_EMP_ID_RE = re.compile(r"^EMP[-\s]?\d+$", re.IGNORECASE)
_STU_ID_RE = re.compile(r"^STU[-\s]?\d+$", re.IGNORECASE)
_PAT_ID_RE = re.compile(r"^(?:PAT|MRN)[-\s]?\d+$", re.IGNORECASE)
_INV_ID_RE = re.compile(r"^(?:INV|BILL)[-\s]?\d+$", re.IGNORECASE)
_STR_ID_RE = re.compile(r"^(?:STR|BRN)[-\s]?\d+$", re.IGNORECASE)


def _analyse_values(
    df: pd.DataFrame,
    columns: List[str],
    entity_scores: Dict[str, Dict[str, float]],
    column_assignments: Dict[str, str],
) -> None:
    """
    Inspect sampled cell values to boost entity confidence across all 9 domains.
    Mutates *entity_scores* and *column_assignments* in-place.
    """
    for raw_col in columns:
        try:
            sample = df[raw_col].dropna().astype(str).head(25).tolist()
        except Exception:
            continue

        if not sample:
            continue

        # 1. 17-char VIN pattern → Car
        vin_hits = sum(1 for v in sample if _VIN_RE.match(v.strip()))
        if vin_hits >= max(1, int(len(sample) * 0.4)):
            entity_scores["car"][raw_col] = entity_scores["car"].get(raw_col, 0) + 0.35
            column_assignments[raw_col] = "car"

        # 2. License plate pattern → Car
        plate_hits = sum(1 for v in sample if _PLATE_RE.match(v.strip().replace(" ", "")))
        if plate_hits >= max(1, int(len(sample) * 0.4)):
            entity_scores["car"][raw_col] = entity_scores["car"].get(raw_col, 0) + 0.25
            if raw_col not in column_assignments:
                column_assignments[raw_col] = "car"

        # 3. Patient / MRN pattern → Medical
        pat_hits = sum(1 for v in sample if _PAT_ID_RE.match(v.strip()))
        if pat_hits >= max(1, int(len(sample) * 0.4)):
            entity_scores["medical"][raw_col] = entity_scores["medical"].get(raw_col, 0) + 0.30
            column_assignments[raw_col] = "medical"

        # 4. Student ID / Roll pattern → Student
        stu_hits = sum(1 for v in sample if _STU_ID_RE.match(v.strip()))
        if stu_hits >= max(1, int(len(sample) * 0.4)):
            entity_scores["student"][raw_col] = entity_scores["student"].get(raw_col, 0) + 0.30
            column_assignments[raw_col] = "student"

        # 5. Employee ID pattern → Employee
        emp_hits = sum(1 for v in sample if _EMP_ID_RE.match(v.strip()))
        if emp_hits >= max(1, int(len(sample) * 0.4)):
            entity_scores["employee"][raw_col] = entity_scores["employee"].get(raw_col, 0) + 0.30
            column_assignments[raw_col] = "employee"

        # 6. Invoice ID pattern → Invoice
        inv_hits = sum(1 for v in sample if _INV_ID_RE.match(v.strip()))
        if inv_hits >= max(1, int(len(sample) * 0.4)):
            entity_scores["invoice"][raw_col] = entity_scores["invoice"].get(raw_col, 0) + 0.30
            column_assignments[raw_col] = "invoice"

        # 7. Store / Branch ID pattern → Store
        str_hits = sum(1 for v in sample if _STR_ID_RE.match(v.strip()))
        if str_hits >= max(1, int(len(sample) * 0.4)):
            entity_scores["store"][raw_col] = entity_scores["store"].get(raw_col, 0) + 0.25
            column_assignments[raw_col] = "store"

        # 8. Email pattern → Customer (or Employee if dept/role present)
        email_hits = sum(1 for v in sample if _EMAIL_RE.match(v.strip()))
        if email_hits >= max(1, int(len(sample) * 0.4)):
            target_entity = "employee" if any("emp" in _normalize_col(c) or "department" in _normalize_col(c) for c in columns) else "customer"
            entity_scores[target_entity][raw_col] = entity_scores[target_entity].get(raw_col, 0) + 0.15
            column_assignments[raw_col] = target_entity

        # 9. Phone pattern → Customer
        phone_hits = sum(1 for v in sample if _PHONE_RE.match(re.sub(r"[\s\-()]", "", v.strip())))
        if phone_hits >= max(1, int(len(sample) * 0.4)):
            entity_scores["customer"][raw_col] = entity_scores["customer"].get(raw_col, 0) + 0.10
            if raw_col not in column_assignments:
                column_assignments[raw_col] = "customer"

        # 10. Price/decimal pattern → Item / Transaction / Car
        price_hits = sum(1 for v in sample if _PRICE_RE.match(v.strip().replace(",", "")))
        if price_hits >= max(1, int(len(sample) * 0.4)):
            if any("vin" in _normalize_col(c) or "make" in _normalize_col(c) for c in columns):
                entity_scores["car"][raw_col] = entity_scores["car"].get(raw_col, 0) + 0.10
            elif any("inv" in _normalize_col(c) or "vendor" in _normalize_col(c) for c in columns):
                entity_scores["invoice"][raw_col] = entity_scores["invoice"].get(raw_col, 0) + 0.10
            else:
                entity_scores["item"][raw_col] = entity_scores["item"].get(raw_col, 0) + 0.10


# ─── Layer 3: Context / Co-occurrence Rules ──────────────────────────

def _apply_context_rules(
    columns: List[str],
    schemas: Dict[str, EntitySchema],
    entity_scores: Dict[str, Dict[str, float]],
    column_assignments: Dict[str, str],
) -> None:
    """
    Apply co-occurrence rules to resolve ambiguous columns.
    Mutates *entity_scores* and *column_assignments* in-place.
    """
    norm_cols = {_normalize_col(c) for c in columns}
    col_map = {_normalize_col(c): c for c in columns}

    # Detect which entity FK columns are present
    fk_present: Dict[str, bool] = {}
    for entity_name, schema in schemas.items():
        fk_present[entity_name] = bool(schema.foreign_key_columns & norm_cols)

    # Key retail rule: if file has FK columns from Store AND Customer AND
    # transaction-like columns (date, quantity, amount) → it's a denormalized Transaction log.
    if "store" in schemas and "customer" in schemas and "transaction" in schemas:
        store_fks = schemas["store"].foreign_key_columns & norm_cols
        customer_fks = schemas["customer"].foreign_key_columns & norm_cols
        txn_signals = {"purchase_date", "order_date", "transaction_date",
                       "sale_date", "quantity", "qty", "total_amount",
                       "order_total", "grand_total"} & norm_cols

        if store_fks and customer_fks and txn_signals:
            for nc in txn_signals:
                if nc in col_map:
                    raw = col_map[nc]
                    entity_scores["transaction"][raw] = (
                        entity_scores["transaction"].get(raw, 0) + 0.20
                    )
                    column_assignments[raw] = "transaction"

    # Check predefined co-occurrence rule-sets across all schemas
    for entity_name, schema in schemas.items():
        for rule_set in schema.co_occurrence_rules:
            if rule_set.issubset(norm_cols):
                for nc in rule_set:
                    if nc in col_map:
                        raw = col_map[nc]
                        entity_scores[entity_name][raw] = (
                            entity_scores[entity_name].get(raw, 0) + 0.15
                        )

    # Resolve weak/ambiguous columns by surrounding context
    for raw_col in columns:
        norm = _normalize_col(raw_col)
        if raw_col in column_assignments:
            continue
        entity_strong_counts: Dict[str, int] = {}
        for ename, schema in schemas.items():
            cnt = len(schema.strong_keywords & norm_cols)
            if cnt > 0:
                entity_strong_counts[ename] = cnt
        if entity_strong_counts:
            best = max(entity_strong_counts, key=entity_strong_counts.get)
            if norm in schemas[best].weak_keywords:
                entity_scores[best][raw_col] = (
                    entity_scores[best].get(raw_col, 0) + 0.15
                )
                column_assignments[raw_col] = best


# ─── Confidence Calculation ──────────────────────────────────────────

def _calculate_confidence(
    entity_scores: Dict[str, Dict[str, float]],
    total_columns: int,
) -> Dict[str, float]:
    """
    Calculate per-entity confidence as a fraction of total columns.
    """
    if total_columns == 0:
        return {e: 0.0 for e in entity_scores}

    confidences: Dict[str, float] = {}
    for entity_name, col_scores in entity_scores.items():
        if not col_scores:
            confidences[entity_name] = 0.0
            continue
        raw = sum(col_scores.values()) / total_columns
        confidences[entity_name] = min(round(raw, 4), 0.99)

    return confidences


# ─── Main Tabular Classification Entry Point ─────────────────────────

def classify_columns(
    columns: List[str],
    df: pd.DataFrame,
) -> EntityClassificationResult:
    """
    Classify DataFrame columns into business entity types using a
    3-layer scoring engine across all 9 supported domain entities.

    Args:
        columns: List of column names from the DataFrame.
        df: The cleaned pandas DataFrame.

    Returns:
        EntityClassificationResult with entity type, confidence, and
        per-column assignments.
    """
    schemas = get_entity_schemas()

    if not columns or df.empty:
        return EntityClassificationResult(
            file_type="unknown",
            confidence=0.0,
            confidence_score=0.0,
            method="rule_based",
            details="Empty dataset — no columns to classify.",
            reasoning="Empty dataset with no columns or rows.",
        )

    # Layer 1 — keyword matching
    entity_scores, column_assignments = _score_column_keywords(columns, schemas)

    # Layer 2 — value patterns
    _analyse_values(df, columns, entity_scores, column_assignments)

    # Layer 3 — co-occurrence context
    _apply_context_rules(columns, schemas, entity_scores, column_assignments)

    # Context refinement: reassign weak columns to the dominant entity if one entity clearly dominates
    norm_cols = {_normalize_col(c) for c in columns}
    strong_counts: Dict[str, int] = {}
    for ename, schema in schemas.items():
        strong_counts[ename] = len(schema.strong_keywords & norm_cols)

    dominant_entities = [e for e, count in strong_counts.items() if count >= 2]
    if len(dominant_entities) == 1:
        dom = dominant_entities[0]
        for raw_col in columns:
            norm = _normalize_col(raw_col)
            if norm in schemas[dom].weak_keywords or norm in schemas[dom].medium_keywords:
                column_assignments[raw_col] = dom
                entity_scores[dom][raw_col] = max(entity_scores[dom].get(raw_col, 0), 0.5)

    # Recalculate confidence after refinements
    confidences = _calculate_confidence(entity_scores, len(columns))

    # Count columns assigned to each entity
    assigned_counts: Dict[str, int] = {}
    for col, ename in column_assignments.items():
        assigned_counts[ename] = assigned_counts.get(ename, 0) + 1

    # Check for primary domain keys present
    pk_present = {
        "car": any(k in norm_cols for k in ("vin", "vehicle_identification_number", "chassis_number", "chassis_no", "license_plate")),
        "invoice": any(k in norm_cols for k in ("invoice_no", "invoice_num", "invoice_number", "bill_to", "vendor_name", "billed_to")),
        "medical": any(k in norm_cols for k in ("patient_id", "mrn", "medical_record_number", "diagnosis", "prescription")),
        "student": any(k in norm_cols for k in ("student_id", "roll_no", "reg_no", "roll_number", "cgpa")),
        "employee": any(k in norm_cols for k in ("emp_id", "employee_id", "department", "designation", "salary")),
        "store": any(k in norm_cols for k in ("store_id", "store_name", "branch_id", "outlet_id")),
        "item": any(k in norm_cols for k in ("product_id", "item_id", "sku", "sku_id", "barcode")),
        "customer": any(k in norm_cols for k in ("customer_id", "cust_id", "client_id", "customer_name")),
        "transaction": any(k in norm_cols for k in ("transaction_id", "order_id", "purchase_id"))
    }

    # Entities that have genuine substantial presence (>= 2 columns assigned OR (>= 1 column AND PK present))
    strong_entities = []
    for ename in schemas:
        col_count = assigned_counts.get(ename, 0)
        has_pk = pk_present.get(ename, False)
        if col_count >= 2 or (col_count >= 1 and has_pk):
            strong_entities.append(ename)

    # If an entity has its PK present and holds majority of columns, it dominates over generic overlaps
    dominant_by_pk = [e for e in strong_entities if pk_present.get(e, False)]
    if len(dominant_by_pk) == 1:
        dom_e = dominant_by_pk[0]
        # Reassign overlapping columns from generic/non-PK entities to this dominant entity
        for raw_col in columns:
            norm = _normalize_col(raw_col)
            if norm in schemas[dom_e].strong_keywords or norm in schemas[dom_e].medium_keywords:
                column_assignments[raw_col] = dom_e
                entity_scores[dom_e][raw_col] = max(entity_scores[dom_e].get(raw_col, 0), 0.9)
        confidences = _calculate_confidence(entity_scores, len(columns))
        # Recount strong entities after dominant re-assignment
        strong_entities = [dom_e]

    # A dataset is MIXED only if at least 2 distinct entities have strong independent presence
    if len(strong_entities) >= 2:
        overall_conf = sum(confidences[e] for e in strong_entities) / len(strong_entities)
        details_parts = []
        for e in sorted(strong_entities, key=lambda x: -confidences[x]):
            matched = [c for c, assigned in column_assignments.items() if assigned == e]
            if matched:
                details_parts.append(
                    f"{schemas[e].display_name} ({confidences[e]:.0%}): "
                    f"{', '.join(matched[:4])}"
                )
        return EntityClassificationResult(
            file_type="mixed",
            entities_detected=confidences,
            column_assignments=column_assignments,
            primary_entity=None,
            is_mixed=True,
            confidence=round(min(overall_conf, 0.99), 4),
            confidence_score=round(min(overall_conf, 0.99), 4),
            method="rule_based",
            details="Mixed file — " + "; ".join(details_parts),
            reasoning=f"Identified multiple domain entities: {', '.join(strong_entities)}",
            entity_confidence=confidences,
            display_name="Multi-Entity Dataset",
            primary_match_key=None,
            extracted_fields=columns
        )

    # Single entity qualification
    qualifying = {
        e: c for e, c in confidences.items() if c >= 0.30 or strong_counts.get(e, 0) >= 1
    }

    if qualifying:
        primary = max(qualifying, key=lambda e: (strong_counts.get(e, 0), confidences[e]))
        schema_def = schemas.get(primary)
        disp_name = schema_def.display_name if schema_def else primary.capitalize()
        match_key = PRIMARY_MATCH_KEYS.get(primary)
        
        # Boost single entity confidence if strong match keys present
        final_conf = confidences[primary]
        if strong_counts.get(primary, 0) >= 2:
            final_conf = max(final_conf, 0.92)
        elif strong_counts.get(primary, 0) == 1:
            final_conf = max(final_conf, 0.85)

        return EntityClassificationResult(
            file_type=primary,
            entities_detected=confidences,
            column_assignments=column_assignments,
            primary_entity=primary,
            is_mixed=False,
            confidence=round(min(final_conf, 0.99), 4),
            confidence_score=round(min(final_conf, 0.99), 4),
            method="rule_based",
            details=f"Classified as {disp_name} ({final_conf:.0%} confidence)",
            reasoning=f"Found {strong_counts.get(primary, 0)} strong keyword signals and matching domain value patterns for {disp_name}.",
            entity_confidence=confidences,
            display_name=disp_name,
            primary_match_key=match_key,
            extracted_fields=[c for c, e in column_assignments.items() if e == primary] or columns
        )

    # Below threshold — mark as unknown (LLM fallback recommended)
    best = max(confidences, key=confidences.get) if confidences else None
    best_conf = confidences.get(best, 0) if best else 0
    return EntityClassificationResult(
        file_type="unknown",
        entities_detected=confidences,
        column_assignments=column_assignments,
        primary_entity=best if best_conf > 0 else None,
        is_mixed=False,
        confidence=best_conf,
        confidence_score=best_conf,
        method="rule_based",
        details=f"Low confidence ({best_conf:.0%}). Rule-based classification inconclusive.",
        reasoning="Insufficient domain keywords or value patterns to determine entity with high confidence.",
        entity_confidence=confidences,
        display_name="General / Unclassified Data",
        primary_match_key=None,
        extracted_fields=columns
    )


# ─── Universal Domain Classifier (Any Format: DataFrame, Dict, List, Text) ────

def classify_domain(
    content: Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any], str],
    columns: Optional[List[str]] = None,
    api_key: Optional[str] = None,
) -> EntityClassificationInfo:
    """
    Universal Domain & Entity Classifier for any content format.
    Accepts:
    - pd.DataFrame (tabular files: CSV, Excel, Parquet)
    - List[Dict[str, Any]] (multi-record structured data)
    - Dict[str, Any] (key-value entity fields)
    - str (raw or cleaned unstructured text from PDF, OCR, Word, Email, Text)

    Returns:
        EntityClassificationInfo with detected domain type, confidence, primary match key,
        reasoning, and extracted fields.
    """
    from backend.extraction.ai_extractor import classify_columns_with_llm, classify_domain_with_llm

    schemas = get_entity_schemas()

    # ─── Case 1: DataFrame Input ───
    if isinstance(content, pd.DataFrame):
        df = content
        cols = columns or list(df.columns)
        res = classify_columns(cols, df)

        # LLM fallback if inconclusive
        if res.confidence < CONFIDENCE_THRESHOLD and res.file_type == "unknown":
            sample_vals = {c: df[c].dropna().astype(str).head(5).tolist() for c in cols if c in df.columns}
            llm_res = classify_with_llm_fallback(cols, sample_vals, classify_columns_with_llm)
            if llm_res and llm_res.confidence > res.confidence:
                res = llm_res

        return EntityClassificationInfo(
            entity_type=res.file_type,
            is_mixed=res.is_mixed,
            confidence=res.confidence,
            method=res.method,
            details=res.details,
            reasoning=res.reasoning or res.details,
            display_name=res.display_name or (schemas[res.file_type].display_name if res.file_type in schemas else "General Data"),
            primary_match_key=res.primary_match_key or PRIMARY_MATCH_KEYS.get(res.file_type),
            extracted_fields=res.extracted_fields or cols,
            entities_detected=res.entities_detected,
            column_assignments=res.column_assignments,
            split_tables=None
        )

    # ─── Case 2: List of Dicts Input ───
    if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
        df = pd.DataFrame(content)
        cols = columns or list(df.columns)
        return classify_domain(df, cols, api_key=api_key)

    # ─── Case 3: Dict of Key-Value Fields ───
    if isinstance(content, dict):
        keys = list(content.keys())
        df = pd.DataFrame([content])
        return classify_domain(df, keys, api_key=api_key)

    # ─── Case 4: Raw / Cleaned Unstructured Text ───
    if isinstance(content, str):
        text = content.strip()
        if not text:
            return EntityClassificationInfo(
                entity_type="unknown",
                confidence=0.0,
                method="rule_based",
                details="Empty document text.",
                reasoning="No textual content available to classify.",
                display_name="General Data",
                primary_match_key=None,
                extracted_fields=[]
            )

        text_lower = text.lower()
        domain_scores: Dict[str, float] = {e: 0.0 for e in schemas}
        domain_hits: Dict[str, List[str]] = {e: [] for e in schemas}

        # Scan text for domain strong and medium keywords & regexes
        for ename, schema in schemas.items():
            for kw in schema.strong_keywords:
                # Use word boundary or colon check (e.g. 'vin:', 'make:')
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    domain_scores[ename] += 1.0
                    domain_hits[ename].append(kw)

            for kw in schema.medium_keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    domain_scores[ename] += 0.4
                    domain_hits[ename].append(kw)

            # Check value patterns in text
            for pat in schema.value_patterns:
                if pat.search(text):
                    domain_scores[ename] += 1.5
                    domain_hits[ename].append(f"pattern_{ename}")

        # Check for 17-character VIN specifically in text
        if _VIN_RE.search(text):
            domain_scores["car"] += 2.0
            domain_hits["car"].append("17-char VIN pattern")

        # Normalize domain scores into confidences
        max_score = max(domain_scores.values()) if domain_scores else 0.0
        best_domain = max(domain_scores, key=domain_scores.get) if max_score > 0 else "unknown"

        if max_score >= 1.8:
            conf = min(0.95, round(0.70 + (max_score * 0.05), 2))
            disp_name = schemas[best_domain].display_name
            match_key = PRIMARY_MATCH_KEYS.get(best_domain)
            hits_str = ", ".join(domain_hits[best_domain][:4])
            return EntityClassificationInfo(
                entity_type=best_domain,
                is_mixed=False,
                confidence=conf,
                method="rule_based",
                details=f"Classified as {disp_name} ({conf:.0%} confidence)",
                reasoning=f"Matched domain keywords and patterns ({hits_str}) in document text.",
                display_name=disp_name,
                primary_match_key=match_key,
                extracted_fields=domain_hits[best_domain],
                entities_detected={k: round(min(v / max(max_score, 1.0), 0.99), 2) for k, v in domain_scores.items() if v > 0}
            )

        # Fallback to LLM Domain Classifier for unstructured text
        try:
            llm_result = classify_domain_with_llm(text, api_key=api_key)
            if llm_result and isinstance(llm_result, dict) and "detected_type" in llm_result:
                det_type = llm_result.get("detected_type", "unknown").lower()
                conf = float(llm_result.get("confidence", 0.85))
                reason = llm_result.get("reasoning", f"LLM classified as {det_type}")
                m_key = llm_result.get("primary_match_key") or PRIMARY_MATCH_KEYS.get(det_type)
                disp = schemas[det_type].display_name if det_type in schemas else det_type.capitalize()
                ext_flds = llm_result.get("extracted_fields", [])

                return EntityClassificationInfo(
                    entity_type=det_type,
                    is_mixed=False,
                    confidence=conf,
                    method="llm_fallback",
                    details=f"Classified as {disp} ({conf:.0%} confidence, LLM)",
                    reasoning=reason,
                    display_name=disp,
                    primary_match_key=m_key,
                    extracted_fields=ext_flds,
                    entities_detected={det_type: conf}
                )
        except Exception as llm_err:
            print(f"LLM domain classification fallback error: {llm_err}")

        # Inconclusive text
        return EntityClassificationInfo(
            entity_type="unknown",
            is_mixed=False,
            confidence=0.30,
            method="rule_based",
            details="General unstructured document — domain unclassified.",
            reasoning="Document text lacks sufficient domain-specific signals.",
            display_name="General Data",
            primary_match_key=None,
            extracted_fields=[]
        )

    # Default fallback
    return EntityClassificationInfo(
        entity_type="unknown",
        confidence=0.0,
        method="rule_based",
        details="Unrecognized content structure.",
        reasoning="Content format could not be parsed.",
        display_name="General Data",
        primary_match_key=None,
        extracted_fields=[]
    )


# ─── LLM Fallback Wrapper ───────────────────────────────────────────

def classify_with_llm_fallback(
    columns: List[str],
    sample_values: Dict[str, List],
    groq_classify_fn: Callable,
) -> EntityClassificationResult:
    """
    Use LLM to classify columns when rule-based confidence is low.

    Args:
        columns: Column names.
        sample_values: {column_name: [sample cell values]}.
        groq_classify_fn: Callable that accepts (columns, sample_values)
                          and returns a dict with classification.

    Returns:
        EntityClassificationResult populated from LLM response.
    """
    schemas = get_entity_schemas()
    try:
        llm_result = groq_classify_fn(columns, sample_values)
        if not llm_result or not isinstance(llm_result, dict):
            return EntityClassificationResult(
                file_type="unknown",
                confidence=0.0,
                confidence_score=0.0,
                method="llm_fallback",
                details="LLM returned empty or invalid response.",
            )

        file_type = llm_result.get("file_type", "unknown").lower()
        col_assignments = llm_result.get("column_assignments", {})
        entity_confs = llm_result.get("entity_confidence", {})
        is_mixed = file_type == "mixed"
        disp_name = schemas[file_type].display_name if file_type in schemas else file_type.capitalize()
        m_key = PRIMARY_MATCH_KEYS.get(file_type)

        return EntityClassificationResult(
            file_type=file_type,
            entities_detected=entity_confs,
            column_assignments=col_assignments,
            primary_entity=None if is_mixed else file_type,
            is_mixed=is_mixed,
            confidence=max(entity_confs.values()) if entity_confs else 0.85,
            confidence_score=max(entity_confs.values()) if entity_confs else 0.85,
            method="llm_fallback",
            details=llm_result.get(
                "details", f"LLM classified as {disp_name}"
            ),
            reasoning=llm_result.get("reasoning", f"LLM identified domain structure as {disp_name}"),
            entity_confidence=entity_confs,
            display_name=disp_name,
            primary_match_key=m_key,
            extracted_fields=columns
        )
    except Exception as e:
        return EntityClassificationResult(
            file_type="unknown",
            confidence=0.0,
            confidence_score=0.0,
            method="llm_fallback",
            details=f"LLM fallback failed: {e}",
        )


def infer_entity_from_collection_name(name: str) -> Optional[str]:
    """
    Infers entity type from a collection key, sheet name, or filename.
    """
    if not name:
        return None
    s = re.sub(r"[^a-zA-Z0-9]+", "_", str(name).strip().lower())
    if any(k in s for k in ("car", "vehicle", "auto", "automobile", "vin", "fleet")):
        return EntityType.CAR.value
    if any(k in s for k in ("invoice", "bill", "billing", "receipt", "payable", "receivable")):
        return EntityType.INVOICE.value
    if any(k in s for k in ("employee", "staff", "hr", "payroll", "worker", "personnel")):
        return EntityType.EMPLOYEE.value
    if any(k in s for k in ("student", "academic", "scholar", "enrollment", "course", "grade")):
        return EntityType.STUDENT.value
    if any(k in s for k in ("patient", "medical", "clinic", "hospital", "doctor", "health", "clinical")):
        return EntityType.MEDICAL.value
    if any(k in s for k in ("store", "branch", "outlet", "warehouse", "location")):
        return EntityType.STORE.value
    if any(k in s for k in ("product", "item", "inventory", "sku", "merchandise", "catalog", "article")):
        return EntityType.ITEM.value
    if any(k in s for k in ("customer", "cust", "client", "member", "user", "buyer", "shopper", "patron", "subscriber")):
        return EntityType.CUSTOMER.value
    if any(k in s for k in ("transaction", "order", "sale", "purchase", "payment")):
        return EntityType.TRANSACTION.value
    return None

