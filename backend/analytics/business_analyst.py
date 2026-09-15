"""
Business Analysis Engine — Retail & Entity Intelligence Layer

Extracts actionable KPIs, distributions, top/least performers, and executive insights
for Store, Item, Customer, Transaction, and Mixed datasets.
"""
from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from backend.models.schemas import (
    BusinessAnalysisReport,
    BusinessMetricCard,
    BusinessInsight
)


def _safe_float(val: Any) -> Optional[float]:
    """Extract clean float from cell value, stripping currency symbols and formatting."""
    if val is None or pd.isna(val):
        return None
    try:
        if isinstance(val, (int, float)):
            return float(val)
        cleaned = re.sub(r"[₹\$€£¥,\s]", "", str(val).strip())
        return float(cleaned)
    except Exception:
        return None


def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Find the first matching column name ignoring case, underscores, and spaces."""
    col_map = {re.sub(r"[\s\-_]+", "", c.lower()): c for c in df.columns}
    for cand in candidates:
        norm_cand = re.sub(r"[\s\-_]+", "", cand.lower())
        if norm_cand in col_map:
            return col_map[norm_cand]
        # Partial match
        for key, original in col_map.items():
            if norm_cand in key:
                return original
    return None


def analyze_transaction_data(df: pd.DataFrame) -> BusinessAnalysisReport:
    """Computes KPIs and insights for Transaction / Sales data."""
    metrics: List[BusinessMetricCard] = []
    insights: List[BusinessInsight] = []

    # Find key columns
    amt_col = _find_col(df, ["total_amount", "amount", "total", "grand_total", "net_amount", "order_total", "price", "line_total"])
    qty_col = _find_col(df, ["quantity", "qty", "units", "items_purchased"])
    item_col = _find_col(df, ["product_name", "item_name", "product_id", "item_id", "sku", "product"])
    store_col = _find_col(df, ["store_name", "store_id", "branch_name", "branch_id", "outlet"])
    cust_col = _find_col(df, ["customer_name", "customer_id", "cust_id", "client_name", "email"])
    payment_col = _find_col(df, ["payment_method", "payment_type", "payment_mode", "payment_status"])
    date_col = _find_col(df, ["purchase_date", "order_date", "transaction_date", "date"])

    total_orders = len(df)
    metrics.append(BusinessMetricCard(
        label="Total Transactions",
        value=f"{total_orders:,}",
        subtext=f"Completed sales records",
        icon="receipt"
    ))

    # Revenue & AOV
    total_rev = 0.0
    if amt_col:
        amounts = df[amt_col].map(_safe_float).dropna()
        if not amounts.empty:
            total_rev = float(amounts.sum())
            aov = float(amounts.mean())
            metrics.append(BusinessMetricCard(
                label="Total Revenue",
                value=f"₹{total_rev:,.2f}" if total_rev > 0 else "N/A",
                subtext=f"Gross sales volume",
                icon="dollar"
            ))
            metrics.append(BusinessMetricCard(
                label="Avg Order Value (AOV)",
                value=f"₹{aov:,.2f}",
                subtext=f"Mean spend per order",
                icon="trending_up"
            ))
            insights.append(BusinessInsight(
                title=f"Total Revenue Generated: ₹{total_rev:,.2f}",
                description=f"Generated across {total_orders} orders with an average basket size (AOV) of ₹{aov:,.2f}.",
                badge="Revenue",
                type="positive"
            ))

    # Total Units
    if qty_col:
        qtys = df[qty_col].map(_safe_float).dropna()
        if not qtys.empty:
            total_qty = int(qtys.sum())
            avg_qty = float(qtys.mean())
            metrics.append(BusinessMetricCard(
                label="Total Units Sold",
                value=f"{total_qty:,} pcs",
                subtext=f"Avg {avg_qty:.1f} units/order",
                icon="package"
            ))

    # Top Selling Products
    if item_col:
        top_items = df[item_col].value_counts().head(3)
        if not top_items.empty:
            best_item = top_items.index[0]
            best_count = int(top_items.iloc[0])
            insights.append(BusinessInsight(
                title=f"Top Selling Item: '{best_item}'",
                description=f"Appeared in {best_count} transactions ({round(best_count/total_orders*100)}% of all orders).",
                badge="Best Seller",
                type="positive"
            ))

    # Top Store / Branch
    if store_col:
        store_counts = df[store_col].value_counts()
        if not store_counts.empty:
            top_store = store_counts.index[0]
            insights.append(BusinessInsight(
                title=f"Most Active Branch: '{top_store}'",
                description=f"Recorded {int(store_counts.iloc[0])} transactions across the dataset.",
                badge="Branch Leader",
                type="info"
            ))

    # Payment Methods
    if payment_col:
        pay_counts = df[payment_col].value_counts()
        if not pay_counts.empty:
            top_pay = pay_counts.index[0]
            insights.append(BusinessInsight(
                title=f"Preferred Payment: '{top_pay}'",
                description=f"Used in {int(pay_counts.iloc[0])} transactions ({round(pay_counts.iloc[0]/total_orders*100)}% share).",
                badge="Payment Trend",
                type="info"
            ))

    # Date Range
    if date_col:
        dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
        if not dates.empty:
            d_min = dates.min().strftime('%Y-%m-%d')
            d_max = dates.max().strftime('%Y-%m-%d')
            insights.append(BusinessInsight(
                title=f"Activity Window: {d_min} to {d_max}",
                description=f"Transactions span across {(dates.max() - dates.min()).days + 1} day(s).",
                badge="Timeline",
                type="info"
            ))

    return BusinessAnalysisReport(
        entity_type="transaction",
        headline="Sales & Transaction Performance Intelligence",
        metrics=metrics,
        insights=insights
    )


def analyze_item_data(df: pd.DataFrame) -> BusinessAnalysisReport:
    """Computes catalog and inventory analytics for Item/Product datasets."""
    metrics: List[BusinessMetricCard] = []
    insights: List[BusinessInsight] = []

    price_col = _find_col(df, ["unit_price", "price", "mrp", "cost", "selling_price", "list_price"])
    cat_col = _find_col(df, ["category", "product_category", "item_category", "type", "sub_category"])
    stock_col = _find_col(df, ["stock", "inventory", "units", "quantity", "reorder_level"])
    brand_col = _find_col(df, ["brand", "manufacturer", "vendor"])

    total_items = len(df)
    metrics.append(BusinessMetricCard(
        label="Catalog Items",
        value=f"{total_items:,}",
        subtext="Unique product definitions",
        icon="inventory"
    ))

    # Price Analytics
    if price_col:
        prices = df[price_col].map(_safe_float).dropna()
        if not prices.empty:
            avg_price = float(prices.mean())
            min_price = float(prices.min())
            max_price = float(prices.max())

            metrics.append(BusinessMetricCard(
                label="Average Price",
                value=f"₹{avg_price:,.2f}",
                subtext=f"Range: ₹{min_price:,.0f} – ₹{max_price:,.0f}",
                icon="dollar"
            ))

            insights.append(BusinessInsight(
                title=f"Catalog Pricing Spread: ₹{min_price:,.0f} to ₹{max_price:,.0f}",
                description=f"Average item price is ₹{avg_price:,.2f} with median pricing at ₹{float(prices.median()):,.2f}.",
                badge="Price Analysis",
                type="positive"
            ))

    # Category Breakdown
    if cat_col:
        cat_counts = df[cat_col].value_counts()
        metrics.append(BusinessMetricCard(
            label="Product Categories",
            value=f"{len(cat_counts):,}",
            subtext=f"Top: {cat_counts.index[0]} ({cat_counts.iloc[0]} items)",
            icon="tag"
        ))
        insights.append(BusinessInsight(
            title=f"Dominant Category: '{cat_counts.index[0]}'",
            description=f"Houses {int(cat_counts.iloc[0])} of {total_items} items ({round(cat_counts.iloc[0]/total_items*100)}% catalog share).",
            badge="Category Leader",
            type="info"
        ))

    # Stock & Inventory Alerts
    if stock_col:
        stocks = df[stock_col].map(_safe_float).dropna()
        if not stocks.empty:
            total_stock = int(stocks.sum())
            low_stock_count = int((stocks <= 10).sum())
            metrics.append(BusinessMetricCard(
                label="Total Inventory",
                value=f"{total_stock:,} units",
                subtext=f"{low_stock_count} item(s) low stock" if low_stock_count > 0 else "All items well-stocked",
                icon="warehouse"
            ))
            if low_stock_count > 0:
                insights.append(BusinessInsight(
                    title=f"Inventory Alert: {low_stock_count} item(s) below reorder threshold",
                    description=f"Identified {low_stock_count} product(s) with 10 or fewer units in stock.",
                    badge="Low Stock",
                    type="warning"
                ))

    # Brands
    if brand_col:
        brand_counts = df[brand_col].value_counts()
        insights.append(BusinessInsight(
            title=f"Brand Portfolio: {len(brand_counts)} Brands Represented",
            description=f"Leading brand is '{brand_counts.index[0]}' with {int(brand_counts.iloc[0])} products.",
            badge="Brand Share",
            type="info"
        ))

    return BusinessAnalysisReport(
        entity_type="item",
        headline="Product & Catalog Inventory Intelligence",
        metrics=metrics,
        insights=insights
    )


def analyze_customer_data(df: pd.DataFrame) -> BusinessAnalysisReport:
    """Computes engagement, geographic, and demographic analytics for Customer datasets."""
    metrics: List[BusinessMetricCard] = []
    insights: List[BusinessInsight] = []

    email_col = _find_col(df, ["customer_email", "email"])
    phone_col = _find_col(df, ["customer_phone", "phone", "mobile", "contact"])
    city_col = _find_col(df, ["customer_city", "city", "location", "town"])
    state_col = _find_col(df, ["customer_state", "state", "region"])
    loyalty_col = _find_col(df, ["loyalty_points", "reward_points", "points", "tier", "membership"])

    total_customers = len(df)
    metrics.append(BusinessMetricCard(
        label="Total Customers",
        value=f"{total_customers:,}",
        subtext="Unique registered profiles",
        icon="users"
    ))

    # Reachability Rate (Email + Phone)
    valid_emails = df[email_col].dropna().astype(str).str.contains('@').sum() if email_col else 0
    reachability = round((valid_emails / max(total_customers, 1)) * 100)
    metrics.append(BusinessMetricCard(
        label="Email Reachability",
        value=f"{reachability}%",
        subtext=f"{valid_emails} verified email addresses",
        icon="mail"
    ))

    # City Breakdown
    if city_col:
        city_counts = df[city_col].value_counts()
        if not city_counts.empty:
            metrics.append(BusinessMetricCard(
                label="Geographic Spread",
                value=f"{len(city_counts)} Cities",
                subtext=f"Hub: {city_counts.index[0]} ({city_counts.iloc[0]} customers)",
                icon="map_pin"
            ))
            insights.append(BusinessInsight(
                title=f"Primary Customer Hub: '{city_counts.index[0]}'",
                description=f"Represents {int(city_counts.iloc[0])} profiles ({round(city_counts.iloc[0]/total_customers*100)}% of user base).",
                badge="Top Market",
                type="positive"
            ))

    # Loyalty Points / Membership
    if loyalty_col:
        points = df[loyalty_col].map(_safe_float).dropna()
        if not points.empty:
            avg_points = float(points.mean())
            insights.append(BusinessInsight(
                title=f"Loyalty Program Engagement",
                description=f"Average customer loyalty balance is {avg_points:,.0f} points.",
                badge="Loyalty",
                type="info"
            ))

    insights.append(BusinessInsight(
        title=f"Contact Database Quality: {reachability}% Omnichannel Ready",
        description=f"Database contains {valid_emails} valid contact emails for direct customer retention campaigns.",
        badge="Contactability",
        type="positive" if reachability >= 75 else "info"
    ))

    return BusinessAnalysisReport(
        entity_type="customer",
        headline="Customer Demographics & Reachability Intelligence",
        metrics=metrics,
        insights=insights
    )


def analyze_store_data(df: pd.DataFrame) -> BusinessAnalysisReport:
    """Computes network and location analytics for Store / Branch datasets."""
    metrics: List[BusinessMetricCard] = []
    insights: List[BusinessInsight] = []

    city_col = _find_col(df, ["store_city", "city", "location", "town"])
    state_col = _find_col(df, ["store_state", "state", "region", "zone"])
    sqft_col = _find_col(df, ["sq_ft", "store_size", "size", "area", "footage"])
    manager_col = _find_col(df, ["store_manager", "manager", "branch_manager", "manager_name"])

    total_stores = len(df)
    metrics.append(BusinessMetricCard(
        label="Total Outlets",
        value=f"{total_stores:,}",
        subtext="Operating branch locations",
        icon="store"
    ))

    if city_col:
        city_counts = df[city_col].value_counts()
        metrics.append(BusinessMetricCard(
            label="Cities Covered",
            value=f"{len(city_counts)} Cities",
            subtext=f"Most branches in {city_counts.index[0]}",
            icon="map_pin"
        ))
        insights.append(BusinessInsight(
            title=f"Top Market Concentration: '{city_counts.index[0]}'",
            description=f"Operates {int(city_counts.iloc[0])} store locations ({round(city_counts.iloc[0]/total_stores*100)}% of store network).",
            badge="Top Hub",
            type="positive"
        ))

    if state_col:
        state_counts = df[state_col].value_counts()
        insights.append(BusinessInsight(
            title=f"Regional Network: Active across {len(state_counts)} States/Regions",
            description=f"Largest territory presence is in '{state_counts.index[0]}'.",
            badge="Regional Spread",
            type="info"
        ))

    if sqft_col:
        sizes = df[sqft_col].map(_safe_float).dropna()
        if not sizes.empty:
            total_sqft = float(sizes.sum())
            avg_sqft = float(sizes.mean())
            metrics.append(BusinessMetricCard(
                label="Total Retail Footprint",
                value=f"{total_sqft:,.0f} sq.ft",
                subtext=f"Avg {avg_sqft:,.0f} sq.ft / store",
                icon="building"
            ))

    return BusinessAnalysisReport(
        entity_type="store",
        headline="Store Network & Regional Footprint Intelligence",
        metrics=metrics,
        insights=insights
    )


def analyze_mixed_data(df: pd.DataFrame, split_tables: Optional[List[Any]] = None) -> BusinessAnalysisReport:
    """Computes cross-entity retail analytics across Store, Item, Customer, and Transaction dimensions."""
    # Run transaction analysis as primary backbone
    txn_report = analyze_transaction_data(df)
    
    # Enrich with multi-entity cross-tabulation
    store_col = _find_col(df, ["store_name", "store_id", "branch_name"])
    amt_col = _find_col(df, ["total_amount", "amount", "total", "price", "unit_price"])
    cust_col = _find_col(df, ["customer_name", "customer_id", "cust_id"])
    item_col = _find_col(df, ["product_name", "item_name", "product_id"])

    insights = txn_report.insights

    # Store-to-Revenue linkage
    if store_col and amt_col:
        try:
            df_calc = df.copy()
            df_calc['_amt'] = df_calc[amt_col].map(_safe_float)
            store_rev = df_calc.groupby(store_col)['_amt'].sum().sort_values(ascending=False)
            if not store_rev.empty:
                top_store = store_rev.index[0]
                top_amt = float(store_rev.iloc[0])
                insights.insert(0, BusinessInsight(
                    title=f"Top Revenue Store: '{top_store}' (₹{top_amt:,.2f})",
                    description=f"Generated {round(top_amt / max(float(df_calc['_amt'].sum()), 1) * 100)}% of total enterprise sales.",
                    badge="Enterprise Leader",
                    type="positive"
                ))
        except Exception:
            pass

    # Customer-to-Spend linkage
    if cust_col and amt_col:
        try:
            df_calc = df.copy()
            df_calc['_amt'] = df_calc[amt_col].map(_safe_float)
            cust_rev = df_calc.groupby(cust_col)['_amt'].sum().sort_values(ascending=False)
            if not cust_rev.empty and len(cust_rev) > 1:
                top_cust = cust_rev.index[0]
                top_spend = float(cust_rev.iloc[0])
                insights.append(BusinessInsight(
                    title=f"Highest Value Customer: '{top_cust}'",
                    description=f"Total lifetime spend of ₹{top_spend:,.2f} across purchase history.",
                    badge="VIP Customer",
                    type="positive"
                ))
        except Exception:
            pass

    return BusinessAnalysisReport(
        entity_type="mixed",
        headline="Enterprise Retail & Multi-Entity Business Intelligence",
        metrics=txn_report.metrics,
        insights=insights
    )


def generate_business_analysis(
    df: pd.DataFrame,
    entity_type: str = "unknown",
    split_tables: Optional[List[Any]] = None
) -> BusinessAnalysisReport:
    """
    Main entrypoint: Automatically routes to specialized business analytics
    based on identified entity classification.
    """
    etype = entity_type.lower()
    if etype == "store":
        return analyze_store_data(df)
    elif etype == "item":
        return analyze_item_data(df)
    elif etype == "customer":
        return analyze_customer_data(df)
    elif etype == "transaction":
        return analyze_transaction_data(df)
    elif etype == "mixed":
        return analyze_mixed_data(df, split_tables)
    else:
        # Generic / Unknown dataset
        return BusinessAnalysisReport(
            entity_type="general",
            headline="General Dataset Overview",
            metrics=[
                BusinessMetricCard(
                    label="Total Records",
                    value=f"{len(df):,}",
                    subtext="Cleaned rows",
                    icon="table"
                ),
                BusinessMetricCard(
                    label="Total Features",
                    value=f"{len(df.columns):,}",
                    subtext="Standardized columns",
                    icon="columns"
                )
            ],
            insights=[
                BusinessInsight(
                    title="Dataset Structure Verified",
                    description=f"Cleaned dataset containing {len(df)} rows across {len(df.columns)} verified attributes.",
                    badge="General",
                    type="info"
                )
            ]
        )
