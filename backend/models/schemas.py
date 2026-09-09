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

class ChartDataPoint(BaseModel):
    label: str
    value: float
    percentage: Optional[float] = None
    color: Optional[str] = None

class DatasetChart(BaseModel):
    id: str
    title: str
    chart_type: str  # "pie", "bar", "donut"
    column_name: str
    data: List[ChartDataPoint]

class MatplotlibPlot(BaseModel):
    id: str
    title: str
    description: str
    plot_type: str  # "cluster", "distribution", "correlation", "box"
    image_base64: str
    columns_analyzed: List[str] = []

class DataVisualizations(BaseModel):
    has_charts: bool = False
    summary_insights: List[str] = []
    charts: List[DatasetChart] = []
    matplotlib_plots: List[MatplotlibPlot] = []

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
    file_size_bytes: int = 0
    processed_at: Optional[str] = None
    quality_score: float = 100.0

class ProcessResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    mime_type: str
    classification: str  # "structured" | "unstructured"
    status: str          # "completed" | "validation_error" | "failed"
    processed_at: Optional[str] = None
    file_size_bytes: int = 0
    steps: List[StepStatus]
    summary: ProcessSummary
    cleansing_report: Optional[CleansingReport] = None
    visualizations: Optional[DataVisualizations] = None
    fields: Optional[List[ProcessedField]] = None
    structured_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    columns: Optional[List[str]] = None
    raw_text: Optional[str] = None
    errors: Optional[List[ValidationErrorItem]] = None
