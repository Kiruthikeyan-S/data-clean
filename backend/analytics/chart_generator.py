import os
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from backend.models.schemas import DataVisualizations, DatasetChart, ChartDataPoint

CHART_PALETTE = [
    "#2563eb",  # Blue
    "#10b981",  # Emerald
    "#f59e0b",  # Amber
    "#8b5cf6",  # Purple
    "#ec4899",  # Pink
    "#06b6d4",  # Cyan
    "#f97316",  # Orange
    "#6366f1",  # Indigo
    "#14b8a6",  # Teal
    "#84cc16",  # Lime
    "#64748b",  # Slate
]

def generate_visualizations(records: Any, columns: Optional[List[str]] = None) -> DataVisualizations:
    """
    Analyzes dataset to determine if chart visualizations (Pie, Bar, Donut) are possible and meaningful.
    Only generates charts if dataset has >= 2 records and categorical/numerical distributions.
    """
    if not records or not isinstance(records, list) or len(records) < 2:
        return DataVisualizations(has_charts=False, charts=[], summary_insights=[])

    try:
        df = pd.DataFrame(records)
    except Exception:
        return DataVisualizations(has_charts=False, charts=[], summary_insights=[])

    if df.empty or len(df.columns) == 0:
        return DataVisualizations(has_charts=False, charts=[], summary_insights=[])

    charts: List[DatasetChart] = []
    insights: List[str] = []
    total_rows = len(df)

    # 1. Identify Categorical Columns with 2 to 12 distinct non-null values
    categorical_candidates = []
    numerical_candidates = []

    for col in df.columns:
        col_str = str(col)
        # Skip ID columns or unique names
        if any(k in col_str.lower() for k in ["_id", "id_", "identifier", "ssn", "passport", "email", "address", "phone", "name"]):
            continue

        non_null_series = df[col].dropna()
        if len(non_null_series) < 2:
            continue

        unique_count = non_null_series.nunique()

        # Check if categorical (2 to 12 unique values)
        if 2 <= unique_count <= 12 and unique_count < total_rows * 0.7:
            categorical_candidates.append(col_str)

        # Check if numeric
        # Try converting to numeric
        try:
            num_series = pd.to_numeric(non_null_series.astype(str).str.replace(r"[₹\$€£¥,\s%]", "", regex=True), errors="coerce").dropna()
            if len(num_series) >= len(non_null_series) * 0.7 and num_series.nunique() >= 3:
                numerical_candidates.append((col_str, num_series))
        except Exception:
            pass

    # 2. Build Charts from Categorical Columns (up to 8 candidate dimensions)
    for col_name in categorical_candidates[:8]:
        series = df[col_name].dropna().astype(str)
        val_counts = series.value_counts().head(10)
        
        data_points: List[ChartDataPoint] = []
        for i, (val, count) in enumerate(val_counts.items()):
            pct = round((count / len(series)) * 100, 1)
            data_points.append(ChartDataPoint(
                label=str(val),
                value=float(count),
                percentage=pct,
                color=CHART_PALETTE[i % len(CHART_PALETTE)]
            ))

        if len(data_points) >= 2:
            # Default chart type: Pie for 2-3 categories, Donut for 4-5, Bar for 6+
            chart_type = "pie" if len(data_points) <= 3 else ("donut" if len(data_points) <= 5 else "bar")
            formatted_title = f"{col_name.replace('_', ' ').title()} Distribution"
            
            charts.append(DatasetChart(
                id=f"chart_{col_name.lower().replace(' ', '_')}",
                title=formatted_title,
                chart_type=chart_type,
                column_name=col_name,
                data=data_points
            ))

            # Auto insight
            top_val = data_points[0].label
            top_pct = data_points[0].percentage
            insights.append(f"{top_val} is the most frequent {col_name.replace('_', ' ')} ({top_pct}%, {int(data_points[0].value)} records).")

    # 3. Add Numerical insights if available
    for col_name, num_series in numerical_candidates[:3]:
        avg_val = round(num_series.mean(), 2)
        min_val = round(num_series.min(), 2)
        max_val = round(num_series.max(), 2)
        insights.append(f"Average {col_name.replace('_', ' ')} is {avg_val} (min {min_val}, max {max_val}).")

    if len(charts) == 0:
        return DataVisualizations(has_charts=False, charts=[], summary_insights=[])

    return DataVisualizations(
        has_charts=True,
        summary_insights=insights[:6],
        charts=charts
    )
