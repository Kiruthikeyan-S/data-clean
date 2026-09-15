"""
Business Entity Classifier — 3-Layer Classification Engine

Classifies cleaned DataFrame columns into business entity types
(Store, Item, Customer, Transaction) using:
  Layer 1: Column-Name Keyword Matching (with aliases)
  Layer 2: Value-Pattern Analysis (cell value inspection)
  Layer 3: Context / Co-occurrence Rules (column combination logic)

Falls back to LLM when rule-based confidence is below threshold.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set, Tuple

import pandas as pd

from backend.models.entity_schemas import (
    get_entity_schemas,
    EntitySchema,
    EntityType,
    CONFIDENCE_THRESHOLD,
)


@dataclass
class EntityClassificationResult:
    """
    Result of entity classification for a single file/DataFrame.

    Attributes:
        file_type: Overall classification — 'store', 'item', 'customer',
                   'transaction', 'mixed', or 'unknown'.
        entities_detected: Mapping of entity name → confidence score.
        column_assignments: Mapping of column name → assigned entity name.
        primary_entity: The dominant entity if single-type; None for mixed.
        is_mixed: True when the file contains columns from 2+ entities.
        confidence: Overall classification confidence (0.0–1.0).
        method: 'rule_based' or 'llm_fallback'.
        details: Human-readable explanation of the classification.
        entity_confidence: Per-entity confidence scores (alias for UI).
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


# ─── Helpers ────────────────────────────────────────────────────────

def _normalize_col(col: str) -> str:
    """Lowercase, strip, replace spaces/hyphens with underscores."""
    return re.sub(r"[\s\-]+", "_", str(col).strip().lower())


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
                        weight = 0.9
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
_PRICE_RE = re.compile(r"^\d+\.\d{1,2}$")
_DATE_RE = re.compile(
    r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$|^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$"
)
_PHONE_RE = re.compile(r"^\+?\d{10,15}$")


def _analyse_values(
    df: pd.DataFrame,
    columns: List[str],
    entity_scores: Dict[str, Dict[str, float]],
    column_assignments: Dict[str, str],
) -> None:
    """
    Inspect sampled cell values to boost entity confidence.
    Mutates *entity_scores* and *column_assignments* in-place.
    """
    for raw_col in columns:
        try:
            sample = df[raw_col].dropna().astype(str).head(20).tolist()
        except Exception:
            continue

        if not sample:
            continue

        # Email pattern → Customer
        email_hits = sum(1 for v in sample if _EMAIL_RE.match(v.strip()))
        if email_hits >= len(sample) * 0.5:
            entity_scores["customer"][raw_col] = (
                entity_scores["customer"].get(raw_col, 0) + 0.15
            )
            column_assignments[raw_col] = "customer"

        # Phone pattern → Customer
        phone_hits = sum(
            1 for v in sample if _PHONE_RE.match(re.sub(r"[\s\-()]", "", v.strip()))
        )
        if phone_hits >= len(sample) * 0.5:
            entity_scores["customer"][raw_col] = (
                entity_scores["customer"].get(raw_col, 0) + 0.10
            )
            if raw_col not in column_assignments:
                column_assignments[raw_col] = "customer"

        # Price/decimal pattern → Item
        price_hits = sum(1 for v in sample if _PRICE_RE.match(v.strip()))
        if price_hits >= len(sample) * 0.4:
            entity_scores["item"][raw_col] = (
                entity_scores["item"].get(raw_col, 0) + 0.10
            )
            if raw_col not in column_assignments:
                column_assignments[raw_col] = "item"

        # Date pattern (combined with quantity column presence → Transaction)
        date_hits = sum(1 for v in sample if _DATE_RE.match(v.strip()))
        if date_hits >= len(sample) * 0.5:
            qty_cols = {
                _normalize_col(c)
                for c in columns
                if _normalize_col(c)
                in {"quantity", "qty", "units", "units_sold", "items_purchased"}
            }
            if qty_cols:
                entity_scores["transaction"][raw_col] = (
                    entity_scores["transaction"].get(raw_col, 0) + 0.15
                )
                column_assignments[raw_col] = "transaction"


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

    # Key rule: if file has FK columns from Store AND Customer AND
    # transaction-like columns (date, quantity, amount) → it's a
    # denormalized Transaction log (mixed file).
    store_fks = schemas["store"].foreign_key_columns & norm_cols
    customer_fks = schemas["customer"].foreign_key_columns & norm_cols
    item_fks = schemas["item"].foreign_key_columns & norm_cols
    txn_signals = {"purchase_date", "order_date", "transaction_date",
                   "sale_date", "quantity", "qty", "total_amount",
                   "order_total", "grand_total"} & norm_cols

    if store_fks and customer_fks and txn_signals:
        # Boost Transaction confidence for date/qty/amount columns
        for nc in txn_signals:
            if nc in col_map:
                raw = col_map[nc]
                entity_scores["transaction"][raw] = (
                    entity_scores["transaction"].get(raw, 0) + 0.20
                )
                column_assignments[raw] = "transaction"

    # Check predefined co-occurrence rule-sets
    for entity_name, schema in schemas.items():
        for rule_set in schema.co_occurrence_rules:
            if rule_set.issubset(norm_cols):
                for nc in rule_set:
                    if nc in col_map:
                        raw = col_map[nc]
                        entity_scores[entity_name][raw] = (
                            entity_scores[entity_name].get(raw, 0) + 0.10
                        )

    # Resolve weak/ambiguous columns by surrounding context
    # e.g., if "city" is unassigned but store_id is present → assign to Store
    for raw_col in columns:
        norm = _normalize_col(raw_col)
        if raw_col in column_assignments:
            continue
        # Count how many entities have strong columns in this file
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


# ─── Main Entry Point ────────────────────────────────────────────────

def classify_columns(
    columns: List[str],
    df: pd.DataFrame,
) -> EntityClassificationResult:
    """
    Classify DataFrame columns into business entity types using a
    3-layer scoring engine.

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

    # If one entity has strong keywords and others have 0, reassign weak columns to that dominant entity
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

    # Entities that have genuine strong presence (>= 1 strong keyword OR confidence >= 0.25 with >= 2 columns)
    strong_entities = []
    for ename in schemas:
        cols_for_entity = [c for c, e in column_assignments.items() if e == ename]
        has_strong = strong_counts.get(ename, 0) >= 1
        if (has_strong and len(cols_for_entity) >= 1) or (confidences.get(ename, 0) >= 0.25 and len(cols_for_entity) >= 2):
            strong_entities.append(ename)

    # A dataset is MIXED only if at least 2 distinct entities have strong presence
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
            entity_confidence=confidences,
        )

    # Single entity qualification
    qualifying = {
        e: c for e, c in confidences.items() if c >= 0.35 or strong_counts.get(e, 0) >= 1
    }

    if qualifying:
        # Choose the entity with the highest strong keyword count, breaking ties by confidence
        primary = max(qualifying, key=lambda e: (strong_counts.get(e, 0), confidences[e]))
        assigned_cols = sum(1 for c, e in column_assignments.items() if e == primary)
        col_ratio = assigned_cols / max(len(columns), 1)
        has_strong = strong_counts.get(primary, 0) >= 1
        calc_conf = round(min(0.98, max(confidences[primary], 0.75 + (0.20 * col_ratio if has_strong else 0.10))), 4)

        return EntityClassificationResult(
            file_type=primary,
            entities_detected=confidences,
            column_assignments=column_assignments,
            primary_entity=primary,
            is_mixed=False,
            confidence=calc_conf,
            confidence_score=calc_conf,
            method="rule_based",
            details=(
                f"Classified as {schemas[primary].display_name} "
                f"({calc_conf:.0%} confidence)"
            ),
            entity_confidence=confidences,
        )

    # Below threshold — mark as unknown (LLM fallback handled by pipeline)
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
        details=(
            f"Low confidence ({best_conf:.0%}). "
            "Rule-based classification inconclusive — LLM fallback recommended."
        ),
        entity_confidence=confidences,
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

        return EntityClassificationResult(
            file_type=file_type,
            entities_detected=entity_confs,
            column_assignments=col_assignments,
            primary_entity=None if is_mixed else file_type,
            is_mixed=is_mixed,
            confidence=max(entity_confs.values()) if entity_confs else 0.5,
            confidence_score=max(entity_confs.values()) if entity_confs else 0.5,
            method="llm_fallback",
            details=llm_result.get(
                "details", f"LLM classified as {file_type}"
            ),
            entity_confidence=entity_confs,
        )
    except Exception as e:
        return EntityClassificationResult(
            file_type="unknown",
            confidence=0.0,
            confidence_score=0.0,
            method="llm_fallback",
            details=f"LLM fallback failed: {e}",
        )
