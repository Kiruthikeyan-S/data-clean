"""
Relationship Validation Engine

Validates referential integrity and foreign key constraints across business entities:
1. Item.Store_ID -> Store.Store_ID
2. Transaction.Store_ID -> Store.Store_ID
3. Transaction.Customer_ID -> Customer.Customer_ID
4. Transaction.Item_ID -> Item.Item_ID

Supports:
- Transaction-item relationships for multiple items in a single transaction (line-item support).
- Detection of missing referenced IDs, orphan records, conflicting relationships, and duplicate primary IDs.
- Structured RelationshipValidationReport output.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Set, Tuple
import pandas as pd


@dataclass
class RelationshipViolation:
    relationship: str
    source_entity: str
    target_entity: str
    violation_type: str  # "orphan_foreign_key", "missing_foreign_key", "duplicate_primary_key", "conflicting_relationship"
    source_record_id: str
    foreign_key_column: str
    invalid_value: Any
    severity: str  # "error", "warning"
    description: str
    remediation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RelationshipValidationReport:
    total_relationships_checked: int
    valid_relationships_count: int
    violations_count: int
    integrity_percentage: float
    violations: List[Dict[str, Any]]
    entity_counts: Dict[str, int]
    referential_summary: Dict[str, Any]
    multi_item_transactions_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RelationshipValidator:
    """
    Validates cross-entity relationships, primary key uniqueness,
    and foreign key referential integrity across Store, Item, Customer, and Transaction.
    """

    def _normalize_id(self, val: Any) -> Optional[str]:
        if val is None or pd.isna(val):
            return None
        s = str(val).strip()
        if not s or s.lower() in ("null", "none", "nan", "n/a", "-", "--", "undefined"):
            return None
        return s

    def validate_entities(
        self,
        stores: Optional[List[Dict[str, Any]]] = None,
        items: Optional[List[Dict[str, Any]]] = None,
        customers: Optional[List[Dict[str, Any]]] = None,
        transactions: Optional[List[Dict[str, Any]]] = None
    ) -> RelationshipValidationReport:
        """
        Validates the complete entity network across Store, Item, Customer, and Transaction datasets.
        """
        stores = stores or []
        items = items or []
        customers = customers or []
        transactions = transactions or []

        violations: List[RelationshipViolation] = []
        total_checks = 0
        valid_checks = 0

        # ─── 1. Primary Key Uniqueness Indexing ─────────────────────────
        # Store IDs
        store_pks: Set[str] = set()
        seen_stores: Dict[str, int] = {}
        for idx, s in enumerate(stores):
            s_id = self._normalize_id(s.get("store_id") or s.get("Store_ID") or s.get("id"))
            if s_id:
                if s_id in seen_stores:
                    violations.append(RelationshipViolation(
                        relationship="Store.Store_ID (Primary Key)",
                        source_entity="store",
                        target_entity="store",
                        violation_type="duplicate_primary_key",
                        source_record_id=s_id,
                        foreign_key_column="store_id",
                        invalid_value=s_id,
                        severity="error",
                        description=f"Duplicate primary key '{s_id}' detected in Store dataset (Row #{idx+1})",
                        remediation="Deduplicate store rows or assign unique store codes"
                    ))
                else:
                    seen_stores[s_id] = idx + 1
                    store_pks.add(s_id)

        # Customer IDs
        customer_pks: Set[str] = set()
        seen_customers: Dict[str, int] = {}
        for idx, c in enumerate(customers):
            c_id = self._normalize_id(c.get("customer_id") or c.get("Customer_ID") or c.get("id"))
            if c_id:
                if c_id in seen_customers:
                    violations.append(RelationshipViolation(
                        relationship="Customer.Customer_ID (Primary Key)",
                        source_entity="customer",
                        target_entity="customer",
                        violation_type="duplicate_primary_key",
                        source_record_id=c_id,
                        foreign_key_column="customer_id",
                        invalid_value=c_id,
                        severity="error",
                        description=f"Duplicate primary key '{c_id}' detected in Customer dataset (Row #{idx+1})",
                        remediation="Deduplicate customer profile rows"
                    ))
                else:
                    seen_customers[c_id] = idx + 1
                    customer_pks.add(c_id)

        # Item IDs & SKUs
        item_pks: Set[str] = set()
        seen_items: Dict[str, int] = {}
        for idx, itm in enumerate(items):
            i_id = self._normalize_id(itm.get("item_id") or itm.get("Item_ID") or itm.get("product_id") or itm.get("sku") or itm.get("id"))
            if i_id:
                if i_id in seen_items:
                    violations.append(RelationshipViolation(
                        relationship="Item.Item_ID (Primary Key)",
                        source_entity="item",
                        target_entity="item",
                        violation_type="duplicate_primary_key",
                        source_record_id=i_id,
                        foreign_key_column="item_id",
                        invalid_value=i_id,
                        severity="error",
                        description=f"Duplicate product/item identifier '{i_id}' detected in Item dataset (Row #{idx+1})",
                        remediation="Ensure product SKU or item IDs are unique per catalog item"
                    ))
                else:
                    seen_items[i_id] = idx + 1
                    item_pks.add(i_id)

        # ─── 2. Validate Item.Store_ID -> Store.Store_ID ───────────────
        if stores and items:
            for idx, itm in enumerate(items):
                i_id = self._normalize_id(itm.get("item_id") or itm.get("product_id") or itm.get("id") or f"Item-#{idx+1}")
                s_fk = self._normalize_id(itm.get("store_id") or itm.get("Store_ID"))
                if s_fk:
                    total_checks += 1
                    if s_fk not in store_pks:
                        violations.append(RelationshipViolation(
                            relationship="Item.Store_ID -> Store.Store_ID",
                            source_entity="item",
                            target_entity="store",
                            violation_type="orphan_foreign_key",
                            source_record_id=str(i_id),
                            foreign_key_column="store_id",
                            invalid_value=s_fk,
                            severity="error",
                            description=f"Item '{i_id}' references unknown Store_ID '{s_fk}'",
                            remediation="Register referenced Store in master dataset or update item store mapping"
                        ))
                    else:
                        valid_checks += 1

        # ─── 3. Validate Transactions & Multi-Item Line Items ───────────
        multi_item_txns_count = 0
        seen_txn_customers: Dict[str, str] = {}
        seen_txn_stores: Dict[str, str] = {}
        seen_txn_ids: Set[str] = set()

        for idx, txn in enumerate(transactions):
            t_id = self._normalize_id(txn.get("transaction_id") or txn.get("Transaction_ID") or txn.get("order_id") or txn.get("id") or f"TXN-#{idx+1}")
            
            # Check duplicate transaction IDs
            if t_id:
                if t_id in seen_txn_ids:
                    # Could be legitimate multi-item transaction line item
                    multi_item_txns_count += 1
                else:
                    seen_txn_ids.add(t_id)

            # A. Check Transaction.Store_ID -> Store.Store_ID
            if stores:
                total_checks += 1
                s_fk = self._normalize_id(txn.get("store_id") or txn.get("Store_ID"))
                if not s_fk:
                    violations.append(RelationshipViolation(
                        relationship="Transaction.Store_ID -> Store.Store_ID",
                        source_entity="transaction",
                        target_entity="store",
                        violation_type="missing_foreign_key",
                        source_record_id=str(t_id),
                        foreign_key_column="store_id",
                        invalid_value=None,
                        severity="error",
                        description=f"Transaction '{t_id}' has missing Store_ID foreign key",
                        remediation="Assign valid Store_ID where purchase took place"
                    ))
                elif s_fk not in store_pks:
                    violations.append(RelationshipViolation(
                        relationship="Transaction.Store_ID -> Store.Store_ID",
                        source_entity="transaction",
                        target_entity="store",
                        violation_type="orphan_foreign_key",
                        source_record_id=str(t_id),
                        foreign_key_column="store_id",
                        invalid_value=s_fk,
                        severity="error",
                        description=f"Transaction '{t_id}' references unknown Store_ID '{s_fk}'",
                        remediation="Verify store code or register branch location"
                    ))
                else:
                    valid_checks += 1
                    # Conflicting store check for same transaction ID
                    if t_id in seen_txn_stores and seen_txn_stores[t_id] != s_fk:
                        violations.append(RelationshipViolation(
                            relationship="Transaction.Store_ID (Consistency)",
                            source_entity="transaction",
                            target_entity="store",
                            violation_type="conflicting_relationship",
                            source_record_id=str(t_id),
                            foreign_key_column="store_id",
                            invalid_value=[seen_txn_stores[t_id], s_fk],
                            severity="error",
                            description=f"Transaction '{t_id}' is associated with multiple conflicting stores ({seen_txn_stores[t_id]} vs {s_fk})",
                            remediation="A single order cannot be billed to multiple independent store branches"
                        ))
                    else:
                        seen_txn_stores[t_id] = s_fk

            # B. Check Transaction.Customer_ID -> Customer.Customer_ID
            if customers:
                total_checks += 1
                c_fk = self._normalize_id(txn.get("customer_id") or txn.get("Customer_ID"))
                if not c_fk:
                    violations.append(RelationshipViolation(
                        relationship="Transaction.Customer_ID -> Customer.Customer_ID",
                        source_entity="transaction",
                        target_entity="customer",
                        violation_type="missing_foreign_key",
                        source_record_id=str(t_id),
                        foreign_key_column="customer_id",
                        invalid_value=None,
                        severity="warning",
                        description=f"Transaction '{t_id}' has no associated Customer_ID (guest checkout or anonymous sale)",
                        remediation="Assign customer account ID or link to guest profile"
                    ))
                elif c_fk not in customer_pks:
                    violations.append(RelationshipViolation(
                        relationship="Transaction.Customer_ID -> Customer.Customer_ID",
                        source_entity="transaction",
                        target_entity="customer",
                        violation_type="orphan_foreign_key",
                        source_record_id=str(t_id),
                        foreign_key_column="customer_id",
                        invalid_value=c_fk,
                        severity="error",
                        description=f"Transaction '{t_id}' references unknown Customer_ID '{c_fk}'",
                        remediation="Register customer before linking purchase history"
                    ))
                else:
                    valid_checks += 1
                    # Conflicting customer check for same transaction ID
                    if t_id in seen_txn_customers and seen_txn_customers[t_id] != c_fk:
                        violations.append(RelationshipViolation(
                            relationship="Transaction.Customer_ID (Consistency)",
                            source_entity="transaction",
                            target_entity="customer",
                            violation_type="conflicting_relationship",
                            source_record_id=str(t_id),
                            foreign_key_column="customer_id",
                            invalid_value=[seen_txn_customers[t_id], c_fk],
                            severity="error",
                            description=f"Transaction '{t_id}' is attributed to multiple conflicting customers ({seen_txn_customers[t_id]} vs {c_fk})",
                            remediation="Ensure order is assigned to a single purchaser account"
                        ))
                    else:
                        seen_txn_customers[t_id] = c_fk

            # C. Check Transaction.Item_ID -> Item.Item_ID
            if items:
                # Handle single item_id or multi-item list
                raw_item_val = txn.get("item_id") or txn.get("Item_ID") or txn.get("product_id") or txn.get("sku") or txn.get("items")
                item_references = []
                if isinstance(raw_item_val, list):
                    multi_item_txns_count += 1
                    for sub in raw_item_val:
                        if isinstance(sub, dict):
                            s_id = self._normalize_id(sub.get("item_id") or sub.get("product_id") or sub.get("sku"))
                            if s_id: item_references.append(s_id)
                        else:
                            s_id = self._normalize_id(sub)
                            if s_id: item_references.append(s_id)
                elif raw_item_val:
                    i_norm = self._normalize_id(raw_item_val)
                    if i_norm:
                        item_references.append(i_norm)

                for itm_ref in item_references:
                    total_checks += 1
                    if itm_ref not in item_pks:
                        violations.append(RelationshipViolation(
                            relationship="Transaction.Item_ID -> Item.Item_ID",
                            source_entity="transaction",
                            target_entity="item",
                            violation_type="orphan_foreign_key",
                            source_record_id=str(t_id),
                            foreign_key_column="item_id",
                            invalid_value=itm_ref,
                            severity="error",
                            description=f"Transaction '{t_id}' references unknown Item/SKU '{itm_ref}'",
                            remediation="Add SKU to product catalog or update product ID"
                        ))
                    else:
                        valid_checks += 1

        integrity_pct = round(100.0 * (valid_checks / max(1, total_checks)), 2) if total_checks > 0 else 100.0

        entity_counts = {
            "stores": len(stores),
            "items": len(items),
            "customers": len(customers),
            "transactions": len(transactions)
        }

        referential_summary = {
            "total_foreign_keys_checked": total_checks,
            "valid_foreign_keys": valid_checks,
            "total_violations": len(violations),
            "orphan_foreign_keys": sum(1 for v in violations if v.violation_type == "orphan_foreign_key"),
            "missing_foreign_keys": sum(1 for v in violations if v.violation_type == "missing_foreign_key"),
            "duplicate_primary_keys": sum(1 for v in violations if v.violation_type == "duplicate_primary_key"),
            "conflicting_relationships": sum(1 for v in violations if v.violation_type == "conflicting_relationship"),
            "integrity_percentage": integrity_pct
        }

        return RelationshipValidationReport(
            total_relationships_checked=total_checks,
            valid_relationships_count=valid_checks,
            violations_count=len(violations),
            integrity_percentage=integrity_pct,
            violations=[v.to_dict() for v in violations],
            entity_counts=entity_counts,
            referential_summary=referential_summary,
            multi_item_transactions_count=multi_item_txns_count
        )


def validate_relationships(
    stores: Optional[List[Dict[str, Any]]] = None,
    items: Optional[List[Dict[str, Any]]] = None,
    customers: Optional[List[Dict[str, Any]]] = None,
    transactions: Optional[List[Dict[str, Any]]] = None
) -> RelationshipValidationReport:
    """Convenience function to validate entity relationships."""
    validator = RelationshipValidator()
    return validator.validate_entities(stores=stores, items=items, customers=customers, transactions=transactions)
