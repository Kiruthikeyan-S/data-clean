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

class RecordMatchCandidate(BaseModel):
    candidate_id: str
    record_a_index: int
    record_b_index: int
    record_a: Dict[str, Any]
    record_b: Dict[str, Any]
    matched_fields: List[str]
    matched_field_count: int
    match_confidence: float
    match_status: str = "merge_candidate"  # "merge_candidate" | "high_confidence"
    merged_preview: Dict[str, Any]
    entity_type: Optional[str] = None
    rag_explanation: Optional[str] = None
    rag_matched_record_id: Optional[str] = None

class MergedRecordDetail(BaseModel):
    merge_id: str
    record_a_index: int
    record_b_index: int
    original_record_a: Dict[str, Any]
    original_record_b: Dict[str, Any]
    merged_record: Dict[str, Any]
    filled_fields: List[str]
    matched_using_fields: List[str]
    status: str = "Successfully Merged"
    entity_type: Optional[str] = None

class RecordMatchConflict(BaseModel):
    conflict_id: str
    record_a_index: int
    record_b_index: int
    record_a: Dict[str, Any]
    record_b: Dict[str, Any]
    matched_fields: List[str]
    conflicting_fields: Dict[str, List[Any]]  # {field_name: [valA, valB]}
    status: str = "Review Required"
    entity_type: Optional[str] = None

class RecordMatchingReport(BaseModel):
    total_records: int = 0
    merge_candidates_count: int = 0
    merged_count: int = 0
    conflicts_count: int = 0
    kept_separate_count: int = 0
    final_records_count: int = 0
    candidate_pairs: List[RecordMatchCandidate] = []
    merged_records: List[MergedRecordDetail] = []
    conflicts: List[RecordMatchConflict] = []

class QualityDimension(BaseModel):
    id: str  # "missing_values", "duplicates", "wrong_data_types", "invalid_values", "outliers", "format_differences", "record_matching"
    title: str
    count: int
    status: str  # "Clean", "Fixed", "Detected", "Resolved", "X Candidates"
    summary: str
    affected_columns: List[str] = []
    items: List[AuditDetailItem] = []
    raw_samples: Optional[List[Dict[str, Any]]] = None
    total_denominator: Optional[int] = None
    record_matching: Optional[RecordMatchingReport] = None

class QualityAuditReport(BaseModel):
    dimensions: List[QualityDimension] = []
    total_issues_handled: int = 0
    total_cells: Optional[int] = None
    total_rows: Optional[int] = None
    record_matching: Optional[RecordMatchingReport] = None

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

class SchemaMappingItem(BaseModel):
    """Details of a mapped canonical field and its source aliases."""
    canonical_field: str
    field_type: str
    description: str = ""
    source_aliases: List[str] = []
    is_mapped: bool = False
    rows_populated: int = 0

class EntityTableInfo(BaseModel):
    """Represents a separated table for an identified business entity."""
    entity_type: str
    display_name: str
    icon: str
    columns: List[str]
    records: List[Dict[str, Any]]
    total_rows: int
    deduplicated_rows: int
    duplicates_removed: int
    confidence: float
    schema_mapping_report: Optional[List[SchemaMappingItem]] = None

class EntityClassificationInfo(BaseModel):
    """Describes the business entity classification result for a processed file."""
    entity_type: str = "unknown"  # "store", "item", "customer", "transaction", "mixed", "unknown"
    is_mixed: bool = False
    confidence: float = 0.0
    method: str = "rule_based"  # "rule_based" or "llm_fallback"
    details: str = ""
    entities_detected: Dict[str, float] = {}
    column_assignments: Dict[str, str] = {}
    split_tables: Optional[List[EntityTableInfo]] = None

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
    raw_structured_data: Optional[List[Dict[str, Any]]] = None
    raw_columns: Optional[List[str]] = None
    schema_mapping_report: Optional[List[SchemaMappingItem]] = None
    schema_mapping_coverage: float = 0.0
    data_quality_score: float = 1.0
    raw_text: Optional[str] = None
    errors: Optional[List[ValidationErrorItem]] = None
    entity_info: Optional[EntityClassificationInfo] = None

class BatchProcessResponse(BaseModel):
    batch_id: str
    total_files: int
    results: List[ProcessResponse]
    processing_time_ms: float
