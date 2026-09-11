from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class StepStatus(BaseModel):
    step_id: str
    name: str
    status: str  # "pending", "in_progress", "completed", "failed"
    message: Optional[str] = None

class ProcessedField(BaseModel):
    key: str
    label: str
    raw_value: Optional[Any] = None
    value: Optional[Any] = None
    field_type: str = "text"
    confidence: Optional[float] = None
    is_valid: bool = True
    error_message: Optional[str] = None

class ValidationErrorItem(BaseModel):
    field: str
    message: str
    raw_value: Optional[Any] = None

class CleansingCategory(BaseModel):
    id: str
    title: str
    icon_type: str  # "dedup", "missing", "sanitize", "standardize", "validate"
    status: str     # "Applied", "Clean", "Verified"
    count: int
    description: str
    details: List[str] = []

class AuditDetailItem(BaseModel):
    row_index: Optional[int] = None
    column: str
    original_value: Optional[Any] = None
    cleaned_value: Optional[Any] = None
    issue_description: str
    severity: str = "warning"  # "warning", "info", "error"

class QualityDimension(BaseModel):
    id: str  # "missing_values", "duplicates", "wrong_data_types", "invalid_values", "outliers", "format_differences"
    title: str
    count: int
    status: str  # "Clean", "Fixed", "Detected", "Resolved"
    summary: str
    affected_columns: List[str] = []
    items: List[AuditDetailItem] = []
    raw_samples: Optional[List[Dict[str, Any]]] = None

class QualityAuditReport(BaseModel):
    dimensions: List[QualityDimension] = []
    total_issues_handled: int = 0

class CleansingReport(BaseModel):
    initial_rows: Optional[int] = None
    final_rows: Optional[int] = None
    duplicates_removed: int = 0
    empty_rows_removed: int = 0
    nulls_normalized: int = 0
    whitespace_trimmed: int = 0
    modifications_count: int = 0
    change_highlights: List[str] = []
    removed_samples: Optional[List[Dict[str, Any]]] = None
    categories: List[CleansingCategory] = []
    quality_audit: Optional[QualityAuditReport] = None

class ProcessSummary(BaseModel):
    total_records: int = 1
    valid_records: int = 1
    invalid_records: int = 0
    processing_time_ms: float = 0.0
    file_type: str
    classification: str

# ----------------- Retail Intelligence Schemas ----------------- #

class ExecutiveKPIs(BaseModel):
    total_revenue: float = 0.0
    total_units_sold: int = 0
    total_transactions: int = 0
    avg_order_value: float = 0.0
    unique_customers: Optional[int] = None
    unique_products: Optional[int] = None

class ProductMetric(BaseModel):
    product_name: str
    units_sold: int = 0
    revenue: float = 0.0
    category: Optional[str] = "General"
    stock_level: Optional[int] = None
    revenue_share_pct: Optional[float] = 0.0

class DeadStockItem(BaseModel):
    product_name: str
    stock_quantity: int
    days_inactive: str = "60+"
    recommendation: str

class TrendingProductItem(BaseModel):
    product_name: str
    velocity: str = "High Velocity"
    growth_rate_pct: float = 0.0
    revenue: float = 0.0
    recommendation: str

class CategoryBreakdownItem(BaseModel):
    category: str
    revenue: float = 0.0
    units_sold: int = 0

class ProductAnalytics(BaseModel):
    top_selling: List[ProductMetric] = []
    least_selling: List[ProductMetric] = []
    dead_stock: List[DeadStockItem] = []
    trending_products: List[TrendingProductItem] = []
    category_breakdown: List[CategoryBreakdownItem] = []

class CustomerSegmentSummary(BaseModel):
    segment_name: str
    customer_count: int
    percentage: float
    avg_spend: float
    actionable_strategy: str
    badge_color: str = "slate"

class CustomerRFMItem(BaseModel):
    customer_id: str
    segment: str
    orders_count: int
    total_spend: float
    last_active_days_ago: int

class CustomerIntelligence(BaseModel):
    segments_summary: List[CustomerSegmentSummary] = []
    top_customers: List[CustomerRFMItem] = []
    total_profiled_customers: int = 0

class MarketBasketPair(BaseModel):
    item_a: str
    item_b: str
    co_occurrence_count: int
    confidence_pct: float
    recommendation: str

class MarketBasketAnalysis(BaseModel):
    pairs: List[MarketBasketPair] = []
    total_basket_transactions: int = 0

class DemandForecastItem(BaseModel):
    product_name: str
    historical_units_sold: int
    current_stock: Optional[int] = None
    projected_demand_7d: int
    projected_demand_30d: int
    daily_run_rate: float
    inventory_status: str
    actionable_advice: str
    badge_color: str = "blue"

class DemandForecasting(BaseModel):
    forecasts: List[DemandForecastItem] = []
    model_used: str = "Moving Average + Growth Trend Extrapolation"

class RetailIntelligenceReport(BaseModel):
    kpis: ExecutiveKPIs
    product_analytics: ProductAnalytics
    customer_intelligence: CustomerIntelligence
    basket_analysis: MarketBasketAnalysis
    demand_forecasting: DemandForecasting
    entity_classification: Optional[Dict[str, Any]] = None

class UnifiedWarehouseView(BaseModel):
    title: str = "Unified Retail Data Warehouse View"
    source_tables: List[str] = []
    total_records: int = 0
    columns: List[str] = []
    records: List[Dict[str, Any]] = []

# ----------------- Pipeline Response Schemas ----------------- #

class ProcessResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    mime_type: str
    classification: str  # "structured" | "unstructured"
    status: str          # "completed" | "validation_error" | "failed"
    steps: List[StepStatus]
    summary: ProcessSummary
    cleansing_report: Optional[CleansingReport] = None
    fields: Optional[List[ProcessedField]] = None
    structured_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    columns: Optional[List[str]] = None
    raw_text: Optional[str] = None
    errors: Optional[List[ValidationErrorItem]] = None
    entity_classification: Optional[Dict[str, Any]] = None
    retail_intelligence: Optional[RetailIntelligenceReport] = None

class BatchProcessResponse(BaseModel):
    batch_id: str
    total_files: int
    results: List[ProcessResponse]
    processing_time_ms: float
    unified_warehouse: Optional[UnifiedWarehouseView] = None
    batch_intelligence: Optional[RetailIntelligenceReport] = None
