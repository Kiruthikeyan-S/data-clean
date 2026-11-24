"""
Inventory Demand Forecasting & Stock Prediction Module

Provides statistical demand forecasting and inventory health analysis:
- Product demand velocity and future requirements
- Stock shortage early warnings
- Recommended reorder quantities and urgency ratings
- Upper and lower confidence bounds
- Data sufficiency enforcement (blocks unrealistic claims when history is sparse)
"""
from __future__ import annotations

import re
import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np


@dataclass
class ProductDemandForecast:
    item_id: str
    item_name: str
    current_stock: float
    historical_sales_velocity_daily: float
    predicted_demand: float
    lower_confidence_bound: float
    upper_confidence_bound: float
    stock_shortage_warning: bool
    projected_days_until_stockout: Optional[float]
    recommended_reorder_quantity: float
    reorder_urgency: str  # "critical", "medium", "healthy"
    confidence_score: float
    actionable_recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DemandPredictionReport:
    forecast_horizon_days: int
    data_sufficiency_status: str  # "sufficient", "insufficient", "sparse"
    total_products_analyzed: int
    stock_shortage_alerts_count: int
    recommendations_count: int
    forecasts: List[Dict[str, Any]]
    limitations: Optional[str]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DemandPredictor:
    """
    Predicts product inventory demand over a configurable horizon (e.g. 30 days).
    Enforces minimum history thresholds and calculates statistical confidence intervals.
    """
    def __init__(self, min_history_records: int = 5):
        self.min_history_records = min_history_records

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

    def predict_demand(
        self,
        items: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        forecast_horizon_days: int = 30
    ) -> DemandPredictionReport:
        """
        Generates demand forecasts and stock replenishment recommendations.
        """
        total_txns = len(transactions)

        # 1. Enforce Data Sufficiency Rule
        if total_txns < self.min_history_records:
            return DemandPredictionReport(
                forecast_horizon_days=forecast_horizon_days,
                data_sufficiency_status="insufficient",
                total_products_analyzed=len(items),
                stock_shortage_alerts_count=0,
                recommendations_count=0,
                forecasts=[],
                limitations=(
                    f"Insufficient historical data: Only {total_txns} transaction(s) available. "
                    f"At least {self.min_history_records} historical sales transactions are required "
                    "for reliable statistical demand forecasting. Predictions cannot be made safely."
                ),
                summary={
                    "status": "blocked",
                    "reason": "data_sparsity",
                    "available_transactions": total_txns,
                    "required_transactions": self.min_history_records
                }
            )

        # 2. Index item catalog and stock
        item_stock: Dict[str, float] = {}
        item_names: Dict[str, str] = {}
        for itm in items:
            i_id = str(itm.get("item_id") or itm.get("Item_ID") or itm.get("product_id") or "").strip()
            if i_id:
                item_names[i_id] = str(itm.get("item_name") or itm.get("Item_Name") or itm.get("product_name") or i_id)
                stk = self._to_float(itm.get("stock_quantity") or itm.get("Stock_Quantity")) or 0.0
                item_stock[i_id] = stk

        # 3. Aggregate item transaction history & date intervals
        item_quantities: Dict[str, List[float]] = {}
        dates_seen: List[pd.Timestamp] = []

        for t in transactions:
            i_id = str(t.get("item_id") or t.get("Item_ID") or t.get("product_id") or "").strip()
            qty = self._to_float(t.get("quantity") or t.get("Quantity")) or 1.0
            d_val = str(t.get("transaction_date") or t.get("purchase_date") or t.get("order_date") or "").strip()
            
            try:
                ts = pd.to_datetime(d_val)
                dates_seen.append(ts)
            except Exception:
                pass

            if i_id:
                if i_id not in item_quantities:
                    item_quantities[i_id] = []
                item_quantities[i_id].append(qty)
                if i_id not in item_names:
                    item_names[i_id] = f"Item {i_id}"
                if i_id not in item_stock:
                    item_stock[i_id] = 0.0

        # Calculate time span in days (minimum 7 days to avoid division by zero or inflated spikes)
        if len(dates_seen) >= 2:
            time_span_days = max(7, (max(dates_seen) - min(dates_seen)).days + 1)
        else:
            time_span_days = 30  # Default assumed observation window

        # 4. Generate forecast per product
        forecasts: List[ProductDemandForecast] = []
        shortage_count = 0

        for i_id, qties in item_quantities.items():
            total_sold = sum(qties)
            sales_count = len(qties)
            daily_velocity = round(total_sold / time_span_days, 3)

            # Mean predicted demand
            pred_demand = round(daily_velocity * forecast_horizon_days, 1)

            # Statistical variance & confidence interval (z=1.645 for 90% bounds)
            if sales_count >= 2:
                std_dev = float(np.std(qties, ddof=1))
                std_err = (std_dev / math.sqrt(sales_count)) * math.sqrt(forecast_horizon_days)
                margin = round(1.645 * std_err, 1)
            else:
                margin = round(pred_demand * 0.35, 1)

            lower_bound = round(max(0.0, pred_demand - margin), 1)
            upper_bound = round(pred_demand + margin, 1)

            curr_stock = item_stock.get(i_id, 0.0)

            # Stockout projection
            days_until_stockout = round(curr_stock / daily_velocity, 1) if daily_velocity > 0 else None

            # Stock shortage evaluation
            stock_shortage = curr_stock < upper_bound
            if stock_shortage:
                shortage_count += 1
                safety_buffer = round(daily_velocity * 7, 1)  # 7-day safety buffer
                reorder_qty = round(max(0.0, upper_bound - curr_stock + safety_buffer))
                if curr_stock <= 0 or (days_until_stockout is not None and days_until_stockout <= 7):
                    urgency = "critical"
                    rec_action = f"CRITICAL: Stock will run out in ~{days_until_stockout or 0} days. Reorder {reorder_qty} units immediately."
                else:
                    urgency = "medium"
                    rec_action = f"ATTENTION: Projected demand exceeds current stock. Schedule reorder of {reorder_qty} units."
            else:
                reorder_qty = 0.0
                urgency = "healthy"
                rec_action = "Stock is currently healthy and covers the forecast horizon."

            # Confidence score based on sample size
            confidence_score = min(0.95, round(0.50 + 0.08 * min(5, sales_count), 2))

            forecasts.append(ProductDemandForecast(
                item_id=i_id,
                item_name=item_names.get(i_id, i_id),
                current_stock=curr_stock,
                historical_sales_velocity_daily=daily_velocity,
                predicted_demand=pred_demand,
                lower_confidence_bound=lower_bound,
                upper_confidence_bound=upper_bound,
                stock_shortage_warning=stock_shortage,
                projected_days_until_stockout=days_until_stockout,
                recommended_reorder_quantity=reorder_qty,
                reorder_urgency=urgency,
                confidence_score=confidence_score,
                actionable_recommendation=rec_action
            ))

        forecasts.sort(key=lambda x: (x.reorder_urgency == "critical", x.stock_shortage_warning, -x.predicted_demand), reverse=True)

        return DemandPredictionReport(
            forecast_horizon_days=forecast_horizon_days,
            data_sufficiency_status="sufficient",
            total_products_analyzed=len(forecasts),
            stock_shortage_alerts_count=shortage_count,
            recommendations_count=sum(1 for f in forecasts if f.recommended_reorder_quantity > 0),
            forecasts=[f.to_dict() for f in forecasts],
            limitations="Assumes constant demand velocity; external macroeconomic or marketing spikes not modeled.",
            summary={
                "status": "success",
                "forecast_days": forecast_horizon_days,
                "total_items": len(forecasts),
                "items_needing_reorder": shortage_count
            }
        )


def predict_product_demand(
    items: List[Dict[str, Any]],
    transactions: List[Dict[str, Any]],
    forecast_horizon_days: int = 30
) -> DemandPredictionReport:
    """Convenience function to generate demand forecasts."""
    predictor = DemandPredictor()
    return predictor.predict_demand(
        items=items,
        transactions=transactions,
        forecast_horizon_days=forecast_horizon_days
    )
