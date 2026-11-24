"""
Business Analytics Engine

Computes validated, chart-ready business analytics across 4 core dimensions:
1. Store Analytics (total stores, store-wise revenue, stock holdings, top/low performers)
2. Item Analytics (fast/slow/non-selling products, low-stock alerts, sales velocity)
3. Customer Analytics (total customers, top spenders, purchase frequency, inactive customers, loyalty distribution)
4. Transaction Analytics (total revenue, transaction count, ATV, sales timeline, payment breakdown)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Set
import pandas as pd
import numpy as np


class BusinessAnalyticsEngine:
    """
    Computes business performance metrics from validated canonical datasets.
    Handles missing values safely without crashing or inventing numbers.
    """

    def _to_float(self, val: Any) -> Optional[float]:
        if val is None or pd.isna(val):
            return None
        s = str(val).strip()
        num_str = re.sub(r"[^\d.-]", "", s.replace(",", ""))
        try:
            if num_str and num_str not in ("-", "."):
                return float(num_str)
        except ValueError:
            pass
        return None

    def calculate_store_analytics(
        self,
        stores: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Store performance analytics."""
        total_stores = len(stores)
        store_sales: Dict[str, float] = {}
        store_txns: Dict[str, int] = {}
        store_names: Dict[str, str] = {}

        for s in stores:
            s_id = str(s.get("store_id") or s.get("Store_ID") or "").strip()
            if s_id:
                store_names[s_id] = str(s.get("store_name") or s.get("Store_Name") or s_id)
                store_sales[s_id] = 0.0
                store_txns[s_id] = 0

        # Aggregate transaction sales by store
        for t in transactions:
            s_id = str(t.get("store_id") or t.get("Store_ID") or "").strip()
            amt = self._to_float(t.get("total_amount") or t.get("Total_Amount")) or 0.0
            if s_id:
                store_sales[s_id] = store_sales.get(s_id, 0.0) + amt
                store_txns[s_id] = store_txns.get(s_id, 0) + 1
                if s_id not in store_names:
                    store_names[s_id] = f"Store {s_id}"

        # Aggregate inventory stock by store
        store_stock: Dict[str, float] = {}
        for itm in items:
            s_id = str(itm.get("store_id") or itm.get("Store_ID") or "").strip()
            stk = self._to_float(itm.get("stock_quantity") or itm.get("Stock_Quantity")) or 0.0
            if s_id:
                store_stock[s_id] = store_stock.get(s_id, 0.0) + stk

        # Store-wise summary list
        store_wise_list = []
        for s_id, sales in store_sales.items():
            store_wise_list.append({
                "store_id": s_id,
                "store_name": store_names.get(s_id, s_id),
                "total_sales": round(sales, 2),
                "transactions_count": store_txns.get(s_id, 0),
                "total_stock": round(store_stock.get(s_id, 0.0), 1)
            })

        store_wise_list.sort(key=lambda x: x["total_sales"], reverse=True)

        best_performing = store_wise_list[:3] if store_wise_list else []
        low_performing = sorted(store_wise_list, key=lambda x: x["total_sales"])[:3] if store_wise_list else []

        return {
            "total_stores": total_stores,
            "store_wise_metrics": store_wise_list,
            "best_performing_stores": best_performing,
            "low_performing_stores": low_performing
        }

    def calculate_item_analytics(
        self,
        items: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Item catalog and product sales velocity analytics."""
        item_sales_volume: Dict[str, float] = {}
        item_sales_revenue: Dict[str, float] = {}
        item_names: Dict[str, str] = {}
        item_categories: Dict[str, str] = {}
        item_stock_levels: Dict[str, float] = {}

        for itm in items:
            i_id = str(itm.get("item_id") or itm.get("Item_ID") or itm.get("product_id") or "").strip()
            if i_id:
                item_names[i_id] = str(itm.get("item_name") or itm.get("Item_Name") or itm.get("product_name") or i_id)
                item_categories[i_id] = str(itm.get("category") or itm.get("Category") or "General")
                stk = self._to_float(itm.get("stock_quantity") or itm.get("Stock_Quantity")) or 0.0
                item_stock_levels[i_id] = stk
                item_sales_volume[i_id] = 0.0
                item_sales_revenue[i_id] = 0.0

        # Calculate sales from transactions
        for t in transactions:
            i_id = str(t.get("item_id") or t.get("Item_ID") or t.get("product_id") or "").strip()
            qty = self._to_float(t.get("quantity") or t.get("Quantity")) or 1.0
            amt = self._to_float(t.get("total_amount") or t.get("Total_Amount"))
            if amt is None:
                unit_p = self._to_float(t.get("unit_price") or t.get("Unit_Price")) or 0.0
                amt = qty * unit_p

            if i_id:
                item_sales_volume[i_id] = item_sales_volume.get(i_id, 0.0) + qty
                item_sales_revenue[i_id] = item_sales_revenue.get(i_id, 0.0) + amt
                if i_id not in item_names:
                    item_names[i_id] = f"Item {i_id}"

        # Categorize product velocity
        catalog_items = []
        for i_id, vol in item_sales_volume.items():
            catalog_items.append({
                "item_id": i_id,
                "item_name": item_names.get(i_id, i_id),
                "category": item_categories.get(i_id, "General"),
                "units_sold": round(vol, 1),
                "total_revenue": round(item_sales_revenue.get(i_id, 0.0), 2),
                "current_stock": round(item_stock_levels.get(i_id, 0.0), 1)
            })

        catalog_items.sort(key=lambda x: x["units_sold"], reverse=True)

        fast_selling = [itm for itm in catalog_items if itm["units_sold"] > 0][:5]
        slow_selling = [itm for itm in catalog_items if 0 < itm["units_sold"] <= 2]
        non_selling = [itm for itm in catalog_items if itm["units_sold"] == 0]
        low_stock = [itm for itm in catalog_items if itm["current_stock"] <= 10]

        return {
            "total_catalog_items": len(items),
            "fast_selling_products": fast_selling,
            "slow_selling_products": slow_selling,
            "non_selling_products": non_selling,
            "low_stock_products": low_stock,
            "top_revenue_items": sorted(catalog_items, key=lambda x: x["total_revenue"], reverse=True)[:5]
        }

    def calculate_customer_analytics(
        self,
        customers: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Customer lifetime spend and loyalty distribution analytics."""
        total_customers = len(customers)
        cust_spend: Dict[str, float] = {}
        cust_orders: Dict[str, int] = {}
        cust_names: Dict[str, str] = {}
        loyalty_distribution: Dict[str, int] = {}

        for c in customers:
            c_id = str(c.get("customer_id") or c.get("Customer_ID") or "").strip()
            if c_id:
                cust_names[c_id] = str(c.get("name") or c.get("full_name") or c.get("Customer_Name") or c_id)
                cust_spend[c_id] = 0.0
                cust_orders[c_id] = 0
            tier = str(c.get("loyalty_tier") or c.get("Loyalty_Status") or "Standard").capitalize()
            loyalty_distribution[tier] = loyalty_distribution.get(tier, 0) + 1

        for t in transactions:
            c_id = str(t.get("customer_id") or t.get("Customer_ID") or "").strip()
            amt = self._to_float(t.get("total_amount") or t.get("Total_Amount")) or 0.0
            if c_id:
                cust_spend[c_id] = cust_spend.get(c_id, 0.0) + amt
                cust_orders[c_id] = cust_orders.get(c_id, 0) + 1
                if c_id not in cust_names:
                    cust_names[c_id] = f"Customer {c_id}"

        customer_list = []
        for c_id, spend in cust_spend.items():
            customer_list.append({
                "customer_id": c_id,
                "customer_name": cust_names.get(c_id, c_id),
                "total_spend": round(spend, 2),
                "orders_count": cust_orders.get(c_id, 0)
            })

        customer_list.sort(key=lambda x: x["total_spend"], reverse=True)

        top_customers = customer_list[:5] if customer_list else []
        inactive_customers = [c for c in customer_list if c["orders_count"] == 0]
        avg_frequency = round(sum(cust_orders.values()) / max(1, len(cust_spend)), 2)

        return {
            "total_customers": total_customers,
            "top_customers_by_spend": top_customers,
            "average_purchase_frequency": avg_frequency,
            "inactive_customers_count": len(inactive_customers),
            "loyalty_tier_distribution": loyalty_distribution
        }

    def calculate_transaction_analytics(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Transaction revenue, ATV, trends, and payment breakdown analytics."""
        total_txns = len(transactions)
        total_revenue = 0.0
        payment_methods: Dict[str, int] = {}
        daily_sales: Dict[str, float] = {}
        daily_counts: Dict[str, int] = {}

        for t in transactions:
            amt = self._to_float(t.get("total_amount") or t.get("Total_Amount")) or 0.0
            total_revenue += amt

            # Payment method breakdown
            pay_m = str(t.get("payment_method") or t.get("Payment_Method") or "Unspecified").title()
            payment_methods[pay_m] = payment_methods.get(pay_m, 0) + 1

            # Sales trends over time
            d_val = str(t.get("transaction_date") or t.get("Transaction_Date") or t.get("purchase_date") or t.get("order_date") or "").strip()
            date_key = d_val[:10] if len(d_val) >= 10 and re.match(r"^\d{4}-\d{2}-\d{2}", d_val) else "Unspecified"
            daily_sales[date_key] = daily_sales.get(date_key, 0.0) + amt
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

        atv = round(total_revenue / max(1, total_txns), 2)

        # Build chart-ready timeline
        sales_timeline = []
        for d_key in sorted(daily_sales.keys()):
            if d_key != "Unspecified":
                sales_timeline.append({
                    "date": d_key,
                    "revenue": round(daily_sales[d_key], 2),
                    "transactions": daily_counts[d_key]
                })

        return {
            "total_revenue": round(total_revenue, 2),
            "total_transactions": total_txns,
            "average_transaction_value": atv,
            "sales_trends_timeline": sales_timeline,
            "payment_method_breakdown": payment_methods
        }

    def generate_full_report(
        self,
        stores: Optional[List[Dict[str, Any]]] = None,
        items: Optional[List[Dict[str, Any]]] = None,
        customers: Optional[List[Dict[str, Any]]] = None,
        transactions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generates comprehensive multi-dimensional business analytics."""
        stores = stores or []
        items = items or []
        customers = customers or []
        transactions = transactions or []

        return {
            "store_analytics": self.calculate_store_analytics(stores, transactions, items),
            "item_analytics": self.calculate_item_analytics(items, transactions),
            "customer_analytics": self.calculate_customer_analytics(customers, transactions),
            "transaction_analytics": self.calculate_transaction_analytics(transactions)
        }


def generate_business_analytics_report(
    stores: Optional[List[Dict[str, Any]]] = None,
    items: Optional[List[Dict[str, Any]]] = None,
    customers: Optional[List[Dict[str, Any]]] = None,
    transactions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Convenience function to generate business analytics."""
    engine = BusinessAnalyticsEngine()
    return engine.generate_full_report(
        stores=stores,
        items=items,
        customers=customers,
        transactions=transactions
    )
