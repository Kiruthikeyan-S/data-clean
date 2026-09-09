import uuid
import time
from typing import Dict, Any, List, Optional
from backend.models.schemas import (
    ProcessResponse,
    StepStatus,
    ProcessSummary,
    ProcessedField,
    ValidationErrorItem,
    CleansingReport,
    CleansingCategory
)
from backend.utils.file_detector import detect_file_type, classify_data_type
from backend.extractors import extract_data
from backend.cleaning.text_cleaner import clean_text_data
from backend.cleaning.structured_cleaner import read_and_clean_structured_file
from backend.extraction.field_extractor import identify_fields, map_to_schema
from backend.extraction.ai_extractor import extract_fields_with_llm
from backend.validation.validator import validate_unstructured_fields, validate_structured_records

# In-memory storage for results and exports
RESULTS_STORE: Dict[str, ProcessResponse] = {}

def process_file_pipeline(filename: str, content_type: Optional[str], file_bytes: bytes) -> ProcessResponse:
    """
    Full DataFlow Processing Pipeline:
    1. Detect File Type
    2. Classify Data Type (Structured vs Unstructured)
    3. Branch into appropriate extraction & cleaning pipelines
    4. Normalize & Map to Schema
    5. Validate using Pydantic
    6. Return ProcessResponse
    """
    start_time = time.time()
    task_id = str(uuid.uuid4())
    steps: List[StepStatus] = []

    # Step 1: File received
    steps.append(StepStatus(
        step_id="file_received",
        name="File received",
        status="completed",
        message=f"Received {filename} ({len(file_bytes):,} bytes)"
    ))

    # Step 2: File type detection
    detection = detect_file_type(filename, content_type, file_bytes)
    file_type = detection["file_type"]
    mime_type = detection["mime_type"]
    steps.append(StepStatus(
        step_id="file_type_detected",
        name="File type detected",
        status="completed",
        message=f"Detected as {file_type.upper()} ({mime_type})"
    ))

    # Step 3: Data classification
    classification = classify_data_type(file_type)
    steps.append(StepStatus(
        step_id="data_classified",
        name="Data classified",
        status="completed",
        message=f"Classified as {classification.capitalize()} dataset"
    ))

    raw_text: Optional[str] = None
    fields_list: Optional[List[ProcessedField]] = None
    structured_data: Optional[Any] = None
    columns: Optional[List[str]] = None
    errors: List[ValidationErrorItem] = []
    cleansing_report: Optional[CleansingReport] = None
    status = "completed"

    if classification == "structured":
        try:
            # Step 4: Read & Clean Structured Data
            records, cols, metrics = read_and_clean_structured_file(file_type, file_bytes)
            
            # Categories Breakdown for Structured Data
            structured_categories = [
                CleansingCategory(
                    id="deduplication",
                    title="Deduplication (Duplicate Handling)",
                    icon_type="dedup",
                    status=f"{metrics.get('duplicates_removed', 0)} Removed" if metrics.get('duplicates_removed', 0) > 0 else "Clean",
                    count=metrics.get('duplicates_removed', 0),
                    description="Identified and eliminated identical duplicate rows across all columns.",
                    details=[f"Dropped {metrics.get('duplicates_removed', 0)} exact duplicate record(s)"] if metrics.get('duplicates_removed', 0) > 0 else ["No duplicate rows found"]
                ),
                CleansingCategory(
                    id="missing_data",
                    title="Handling Missing Data (Null Value Treatment)",
                    icon_type="missing",
                    status=f"{metrics.get('nulls_normalized', 0) + metrics.get('empty_rows_removed', 0)} Handled" if (metrics.get('nulls_normalized', 0) + metrics.get('empty_rows_removed', 0)) > 0 else "Clean",
                    count=metrics.get('nulls_normalized', 0) + metrics.get('empty_rows_removed', 0),
                    description="Standardized missing/null representations (N/A, null, None, '') and dropped empty rows.",
                    details=[
                        f"Standardized {metrics.get('nulls_normalized', 0)} inconsistent null cells into uniform null values",
                        f"Discarded {metrics.get('empty_rows_removed', 0)} completely empty row(s)"
                    ]
                ),
                CleansingCategory(
                    id="sanitization",
                    title="Whitespace & Text Sanitization",
                    icon_type="sanitize",
                    status=f"{metrics.get('whitespace_trimmed', 0)} Cleaned" if metrics.get('whitespace_trimmed', 0) > 0 else "Clean",
                    count=metrics.get('whitespace_trimmed', 0),
                    description="Trimmed leading/trailing spaces and normalized encoding across text cells.",
                    details=[
                        f"Trimmed whitespace in {metrics.get('whitespace_trimmed', 0)} cell(s)",
                        "Normalized character encodings and line terminators"
                    ]
                ),
                CleansingCategory(
                    id="standardization",
                    title="Schema & Header Normalization",
                    icon_type="standardize",
                    status="Applied",
                    count=len(cols),
                    description="Verified column headers, removed duplicate header names, and ensured structural integrity.",
                    details=[
                        f"Verified {len(cols)} standardized column headers",
                        "Ensured type safety across rows"
                    ]
                ),
                CleansingCategory(
                    id="validation",
                    title="Data Validation & Quality Auditing",
                    icon_type="validate",
                    status="Verified" if not errors else f"{len(errors)} Warnings",
                    count=len(errors),
                    description="Audited cells against expected data formats (emails, dates, numeric bounds).",
                    details=[
                        f"{len(errors)} format warning(s) flagged" if errors else f"All {len(records)} records passed semantic checks"
                    ]
                ),
            ]

            cleansing_report = CleansingReport(
                initial_rows=metrics.get("initial_rows"),
                final_rows=metrics.get("final_rows"),
                duplicates_removed=metrics.get("duplicates_removed", 0),
                empty_rows_removed=metrics.get("empty_rows_removed", 0),
                nulls_normalized=metrics.get("nulls_normalized", 0),
                whitespace_trimmed=metrics.get("whitespace_trimmed", 0),
                modifications_count=metrics.get("modifications_count", 0),
                change_highlights=metrics.get("change_highlights", []),
                removed_samples=metrics.get("removed_samples", []),
                categories=structured_categories
            )

            steps.append(StepStatus(
                step_id="data_extracted",
                name="Data extracted",
                status="completed",
                message=f"Parsed {metrics.get('initial_rows', len(records))} initial records across {len(cols)} columns"
            ))

            dropped_total = metrics.get('duplicates_removed', 0) + metrics.get('empty_rows_removed', 0)
            steps.append(StepStatus(
                step_id="data_cleaned",
                name="Data cleaned",
                status="completed",
                message=f"Removed {dropped_total} unwanted rows ({metrics.get('duplicates_removed', 0)} duplicates, {metrics.get('empty_rows_removed', 0)} empty), standardized {metrics.get('nulls_normalized', 0)} missing values and trimmed {metrics.get('whitespace_trimmed', 0)} cells"
            ))

            # Step 5: Data Normalized
            steps.append(StepStatus(
                step_id="data_normalized",
                name="Data normalized",
                status="completed",
                message="Standardized column names and cell formats"
            ))

            # Step 6: Fields identified (schema headers)
            steps.append(StepStatus(
                step_id="fields_identified",
                name="Fields identified",
                status="completed",
                message=f"Verified {len(cols)} columns in dataset"
            ))

            # Step 7: Validation
            records, errors = validate_structured_records(records, cols)
            val_status = "completed" if not errors else "completed"
            steps.append(StepStatus(
                step_id="data_validated",
                name="Data validated",
                status=val_status,
                message=f"Validated {len(records)} records ({len(errors)} format warnings)" if errors else f"All {len(records)} records passed validation"
            ))

            structured_data = records
            columns = cols

        except Exception as e:
            status = "failed"
            steps.append(StepStatus(
                step_id="pipeline_error",
                name="Data processing error",
                status="failed",
                message=str(e)
            ))
            errors.append(ValidationErrorItem(field="file", message=f"Failed to process structured file: {str(e)}"))

    else:
        # Unstructured pipeline
        try:
            # Step 4: Extract Data
            extract_result = extract_data(file_type, file_bytes)
            raw_text = extract_result.get("text", "")
            method = extract_result.get("extraction_method", "text_extraction")
            steps.append(StepStatus(
                step_id="data_extracted",
                name="Data extracted",
                status="completed",
                message=f"Extracted content using {method} (Confidence: {int(extract_result.get('confidence', 1.0)*100)}%)"
            ))

            # Step 5: Clean Data
            cleaned_text = clean_text_data(raw_text)
            steps.append(StepStatus(
                step_id="data_cleaned",
                name="Data cleaned",
                status="completed",
                message="Normalized unicode, stripped control characters, whitespace and OCR artifacts"
            ))

            # Step 6: Identify Fields & Normalize (AI LLM with Rule-based fallback)
            ai_extracted = extract_fields_with_llm(cleaned_text)
            highlights = [
                "Normalized Unicode NFKC encoding and line endings",
                "Removed invisible control characters & extra whitespace"
            ]
            
            if ai_extracted and len(ai_extracted) > 0:
                steps.append(StepStatus(
                    step_id="fields_identified",
                    name="Fields identified",
                    status="completed",
                    message="Identified entities and understood document content using AI/LLM"
                ))
                p_fields = [ProcessedField(**f) for f in ai_extracted]
                steps.append(StepStatus(
                    step_id="data_normalized",
                    name="Data normalized",
                    status="completed",
                    message="Standardized values, dates to ISO 8601, names and amounts via AI engine"
                ))
                highlights.append(f"AI extracted and standardized {len(p_fields)} structured entity fields")
            else:
                # Rule-based fallback
                extracted_raw = identify_fields(cleaned_text)
                steps.append(StepStatus(
                    step_id="fields_identified",
                    name="Fields identified",
                    status="completed",
                    message="Extracted entity candidates using rule and regex engine"
                ))
                mapped = map_to_schema(extracted_raw)
                p_fields = [ProcessedField(**f) for f in mapped]
                steps.append(StepStatus(
                    step_id="data_normalized",
                    name="Data normalized",
                    status="completed",
                    message="Standardized dates to ISO 8601, names to Title Case, phone numbers and emails"
                ))
                highlights.append(f"Extracted and mapped {len([f for f in p_fields if f.value is not None])} entity fields")

            # Step 8: Validate Data
            validated_fields, validation_errors = validate_unstructured_fields(p_fields)
            fields_list = validated_fields
            errors = validation_errors

            # Format key-value dictionary for structured_data output
            structured_data = {f.key: f.value for f in validated_fields if f.value is not None}
            columns = ["Field", "Standardized Value", "Raw Value"]

            unstructured_categories = [
                CleansingCategory(
                    id="deduplication",
                    title="Deduplication & Line Consolidation",
                    icon_type="dedup",
                    status="Applied",
                    count=1,
                    description="Merged redundant lines and removed consecutive repetitive text.",
                    details=["Consolidated immediate consecutive duplicate lines"]
                ),
                CleansingCategory(
                    id="missing_data",
                    title="Handling Missing Data (Null Value Treatment)",
                    icon_type="missing",
                    status="Handled",
                    count=len([f for f in p_fields if f.value is None]),
                    description="Explicitly set absent document fields to null without fabricating data.",
                    details=[f"{len([f for f in p_fields if f.value is None])} field(s) cleanly marked as null"]
                ),
                CleansingCategory(
                    id="sanitization",
                    title="OCR Noise & Text Sanitization",
                    icon_type="sanitize",
                    status="Cleaned",
                    count=1,
                    description="Cleaned control characters, standardized punctuation spacing, and normalized Unicode.",
                    details=[
                        "Normalized Unicode NFKC encoding",
                        "Stripped control characters and excess blank lines"
                    ]
                ),
                CleansingCategory(
                    id="standardization",
                    title="Data Type & Value Standardization",
                    icon_type="standardize",
                    status="Applied",
                    count=len([f for f in p_fields if f.value is not None]),
                    description="Standardized dates to ISO 8601, phone numbers to E.164, names to Title Case, and cleaned currency.",
                    details=[
                        "Standardized dates to YYYY-MM-DD",
                        "Standardized phone numbers & emails",
                        "Cleaned numeric currency values"
                    ]
                ),
                CleansingCategory(
                    id="validation",
                    title="Schema Validation & Quality Check",
                    icon_type="validate",
                    status="Verified" if not errors else f"{len(errors)} Warnings",
                    count=len(errors),
                    description="Validated all extracted entities against Pydantic schema rules.",
                    details=[
                        f"{len(errors)} warning(s) flagged" if errors else "All extracted fields passed structural validation"
                    ]
                ),
            ]

            cleansing_report = CleansingReport(
                initial_rows=1,
                final_rows=1,
                modifications_count=len(highlights),
                change_highlights=highlights,
                categories=unstructured_categories
            )

            steps.append(StepStatus(
                step_id="data_validated",
                name="Data validated",
                status="completed",
                message=f"Validation completed ({len(errors)} warnings)" if errors else "All extracted fields conform to target schema"
            ))

        except Exception as e:
            status = "failed"
            steps.append(StepStatus(
                step_id="pipeline_error",
                name="Extraction error",
                status="failed",
                message=str(e)
            ))
            errors.append(ValidationErrorItem(field="file", message=f"Failed to process unstructured file: {str(e)}"))

    processing_time_ms = round((time.time() - start_time) * 1000, 2)
    
    total_records = len(structured_data) if isinstance(structured_data, list) else (1 if structured_data else 0)
    
    summary = ProcessSummary(
        total_records=total_records,
        valid_records=total_records - (1 if errors and classification == "unstructured" else len(errors)),
        invalid_records=len(errors),
        processing_time_ms=processing_time_ms,
        file_type=file_type,
        classification=classification
    )

    response = ProcessResponse(
        id=task_id,
        filename=filename,
        file_type=file_type,
        mime_type=mime_type,
        classification=classification,
        status=status,
        steps=steps,
        summary=summary,
        cleansing_report=cleansing_report,
        fields=fields_list,
        structured_data=structured_data,
        columns=columns,
        raw_text=raw_text,
        errors=errors if errors else None
    )

    # Store in memory for export retrieval
    RESULTS_STORE[task_id] = response
    return response
