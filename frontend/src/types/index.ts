export interface StepStatus {
  step_id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  message?: string;
}

export interface ProcessedField {
  key: string;
  label: string;
  raw_value?: any;
  value?: any;
  field_type: string;
  confidence?: number;
  is_valid: boolean;
  error_message?: string;
}

export interface ValidationErrorItem {
  field: string;
  message: string;
  raw_value?: any;
}

export interface CleansingCategory {
  id: string;
  title: string;
  icon_type: string;
  status: string;
  count: number;
  description: string;
  details: string[];
}

export interface AuditDetailItem {
  row_index?: number;
  column: string;
  original_value?: any;
  cleaned_value?: any;
  issue_description: string;
  severity: 'warning' | 'info' | 'error';
}

export interface RecordMatchCandidate {
  candidate_id: string;
  record_a_index: number;
  record_b_index: number;
  record_a: Record<string, any>;
  record_b: Record<string, any>;
  matched_fields: string[];
  matched_field_count: number;
  match_confidence: number;
  match_status: 'merge_candidate' | 'high_confidence' | string;
  merged_preview: Record<string, any>;
  entity_type?: string;
}

export interface MergedRecordDetail {
  merge_id: string;
  record_a_index: number;
  record_b_index: number;
  original_record_a: Record<string, any>;
  original_record_b: Record<string, any>;
  merged_record: Record<string, any>;
  filled_fields: string[];
  matched_using_fields: string[];
  status: string;
  entity_type?: string;
}

export interface RecordMatchConflict {
  conflict_id: string;
  record_a_index: number;
  record_b_index: number;
  record_a: Record<string, any>;
  record_b: Record<string, any>;
  matched_fields: string[];
  conflicting_fields: Record<string, [any, any]>;
  status: string;
  entity_type?: string;
}

export interface RecordMatchingReport {
  total_records: number;
  merge_candidates_count: number;
  merged_count: number;
  conflicts_count: number;
  kept_separate_count: number;
  final_records_count: number;
  candidate_pairs: RecordMatchCandidate[];
  merged_records: MergedRecordDetail[];
  conflicts: RecordMatchConflict[];
}

export interface QualityDimension {
  id: string; // 'missing_values' | 'duplicates' | 'wrong_data_types' | 'invalid_values' | 'outliers' | 'format_differences' | 'record_matching'
  title: string;
  count: number;
  status: string;
  summary: string;
  affected_columns?: string[];
  items: AuditDetailItem[];
  raw_samples?: Array<Record<string, any>>;
  total_denominator?: number;
  record_matching?: RecordMatchingReport;
}

export interface QualityAuditReport {
  dimensions: QualityDimension[];
  total_issues_handled: number;
  total_cells?: number;
  total_rows?: number;
  record_matching?: RecordMatchingReport;
}

export interface DataProfileColumnStats {
  name: string;
  inferred_type: string;
  total_count: number;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  min_value?: any;
  max_value?: any;
  mean_value?: number;
  median_value?: number;
  mode_value?: any;
  sum_value?: number;
  quartiles?: number[];
  top_frequencies?: Record<string, number>;
  invalid_count: number;
  date_range?: { min?: string; max?: string };
  inconsistent_count: number;
}

export interface DataProfile {
  total_rows: number;
  total_columns: number;
  column_stats: Record<string, DataProfileColumnStats>;
  exact_duplicates_count: number;
  approximate_duplicates_count: number;
  identified_entity_type?: string;
  overall_completeness_percentage: number;
}

export interface ChangeProvenanceItem {
  row_index: number;
  column: string;
  original_value?: any;
  cleaned_value?: any;
  operation: string;
  reason: string;
  provenance?: string;
}

export interface FundamentalReportItem {
  id: string;
  number: number;
  title: string;
  status: 'Passed' | 'Warning' | 'Needs Review' | 'Not Applicable' | string;
  issues_detected: number;
  actions_completed: number;
  remaining_issues: number;
  before_count?: number;
  after_count?: number;
  summary: string;
  details: string[];
}

export interface DataCleaningFundamentalsReport {
  fundamentals: FundamentalReportItem[];
  total_actions_completed: number;
  total_issues_detected: number;
  overall_quality_status: 'Passed' | 'Warning' | 'Failed' | string;
}

export interface CleansingReport {
  initial_rows?: number;
  final_rows?: number;
  duplicates_removed: number;
  empty_rows_removed: number;
  nulls_normalized: number;
  whitespace_trimmed: number;
  modifications_count: number;
  change_highlights: string[];
  removed_samples?: Array<Record<string, any>>;
  categories?: CleansingCategory[];
  quality_audit?: QualityAuditReport;
  pre_cleaning_profile?: DataProfile;
  post_cleaning_profile?: DataProfile;
  fundamentals_report?: DataCleaningFundamentalsReport;
  provenance_log?: ChangeProvenanceItem[];
}

export interface ProcessSummary {
  total_records: number;
  valid_records: number;
  invalid_records: number;
  processing_time_ms: number;
  file_type: string;
  classification: string;
}

export interface SchemaMappingItem {
  canonical_field: string;
  field_type: string;
  description?: string;
  source_aliases: string[];
  is_mapped: boolean;
  rows_populated: number;
}

export interface EntityTableInfo {
  entity_type: 'store' | 'item' | 'customer' | 'transaction' | string;
  display_name: string;
  icon: string;
  columns: string[];
  records: Array<Record<string, any>>;
  total_rows: number;
  deduplicated_rows: number;
  duplicates_removed: number;
  confidence: number;
  schema_mapping_report?: SchemaMappingItem[];
}

export interface EntityClassificationInfo {
  entity_type: 'store' | 'item' | 'customer' | 'transaction' | 'car' | 'invoice' | 'employee' | 'student' | 'academic' | 'medical' | 'mixed' | 'unknown' | string;
  display_name?: string;
  primary_match_key?: string;
  is_mixed: boolean;
  confidence: number;
  method: 'rule_based' | 'llm_fallback' | string;
  details: string;
  reasoning?: string;
  extracted_fields?: string[];
  entities_detected: Record<string, number>;
  column_assignments: Record<string, string>;
  split_tables?: EntityTableInfo[];
}

export interface DocumentPageBlock {
  page: number;
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DocumentTableItem {
  title: string;
  headers: string[];
  rows: string[][];
}

export interface BarcodeItem {
  type: string;
  data: string;
  status: string;
  format?: string;
  bbox?: number[][];
}

export interface DocumentPreviewData {
  page_count: number;
  page_images: string[];
  blocks: DocumentPageBlock[];
  tables: DocumentTableItem[];
  key_values: Array<{ fieldName: string; extractedValue: string; confidence: number }>;
  entities: Array<{ type: string; mention: string; conf: string; norm: string }>;
  barcodes?: BarcodeItem[];
  page_stats?: Record<string, any>;
  document_type?: string;
  table_records?: Array<Record<string, any>>;
  summary?: string;
}

export interface QualityProfileReport {
  total_records: number;
  valid_records: number;
  invalid_records: number;
  missing_value_count: number;
  duplicate_count: number;
  invalid_value_count: number;
  quality_percentage: number;
  issues_by_column: Record<string, Array<{
    column: string;
    issue_type: string;
    count: number;
    sample_invalid_values: any[];
    description: string;
    recommended_correction: string;
    severity: string;
  }>>;
  recommended_corrections: Array<{
    column: string;
    issue_type: string;
    severity: string;
    recommendation: string;
  }>;
  column_quality_scores: Record<string, number>;
  referential_integrity_issues: Array<{
    foreign_key_column: string;
    orphan_count: number;
    sample_orphans: any[];
    description: string;
    recommended_correction: string;
  }>;
  summary: Record<string, any>;
}

export interface RelationshipValidationReport {
  total_relationships_checked: number;
  valid_relationships_count: number;
  violations_count: number;
  integrity_percentage: number;
  violations: Array<{
    relationship: string;
    source_entity: string;
    target_entity: string;
    violation_type: string;
    source_record_id: string;
    foreign_key_column: string;
    invalid_value: any;
    severity: string;
    description: string;
    remediation: string;
  }>;
  entity_counts: {
    stores: number;
    items: number;
    customers: number;
    transactions: number;
  };
  referential_summary: Record<string, any>;
  multi_item_transactions_count: number;
}

export interface BusinessAnalyticsReport {
  store_analytics?: {
    total_stores: number;
    store_wise_metrics: Array<{
      store_id: string;
      store_name: string;
      total_sales: number;
      transactions_count: number;
      total_stock: number;
    }>;
    best_performing_stores: any[];
    low_performing_stores: any[];
  };
  item_analytics?: {
    total_catalog_items: number;
    fast_selling_products: any[];
    slow_selling_products: any[];
    non_selling_products: any[];
    low_stock_products: any[];
    top_revenue_items: any[];
  };
  customer_analytics?: {
    total_customers: number;
    top_customers_by_spend: any[];
    average_purchase_frequency: number;
    inactive_customers_count: number;
    loyalty_tier_distribution: Record<string, number>;
  };
  transaction_analytics?: {
    total_revenue: number;
    total_transactions: number;
    average_transaction_value: number;
    sales_trends_timeline: Array<{
      date: string;
      revenue: number;
      transactions: number;
    }>;
    payment_method_breakdown: Record<string, number>;
  };
}

export interface DemandPredictionReport {
  forecast_horizon_days: number;
  data_sufficiency_status: 'sufficient' | 'insufficient' | 'sparse';
  total_products_analyzed: number;
  stock_shortage_alerts_count: number;
  recommendations_count: number;
  forecasts: Array<{
    item_id: string;
    item_name: string;
    current_stock: number;
    historical_sales_velocity_daily: number;
    predicted_demand: number;
    lower_confidence_bound: number;
    upper_confidence_bound: number;
    stock_shortage_warning: boolean;
    projected_days_until_stockout?: number;
    recommended_reorder_quantity: number;
    reorder_urgency: 'critical' | 'medium' | 'healthy';
    confidence_score: number;
    actionable_recommendation: string;
  }>;
  limitations?: string;
  summary: Record<string, any>;
}

export interface ProcessResponse {
  id: string;
  filename: string;
  file_type: string;
  mime_type: string;
  classification: 'structured' | 'unstructured';
  status: 'completed' | 'validation_error' | 'failed';
  steps: StepStatus[];
  summary: ProcessSummary;
  cleansing_report?: CleansingReport;
  fields?: ProcessedField[];
  structured_data?: Record<string, any> | Array<Record<string, any>>;
  columns?: string[];
  raw_structured_data?: Array<Record<string, any>>;
  raw_columns?: string[];
  schema_mapping_report?: SchemaMappingItem[];
  schema_mapping_coverage?: number;
  data_quality_score?: number;
  raw_text?: string;
  errors?: ValidationErrorItem[];
  entity_info?: EntityClassificationInfo;
  document_preview?: DocumentPreviewData;
  barcodes?: BarcodeItem[];
  page_stats?: Record<string, any>;
  quality_profile?: QualityProfileReport;
  relationship_validation?: RelationshipValidationReport;
  business_analytics?: BusinessAnalyticsReport;
  demand_prediction?: DemandPredictionReport;
  merge_history?: any[];
}

export interface RelationshipNode {
  entity_type: string;
  entity_id: string;
  name: string;
}

export interface RelationshipEdge {
  relationship_id: string;
  source: RelationshipNode;
  target: RelationshipNode;
  relationship_type: string; // 'purchased' | 'purchased_at' | 'sold' | 'customer' | 'product' | 'store'
  confidence: number;
  confidence_percent: string;
  match_method: string;
  matched_fields: string[];
  source_files: string[];
  evidence?: string[];
  context?: Record<string, any>;
}

export interface SameEntityMatchRecord {
  filename: string;
  file_type: string;
  row_index: number;
  record: Record<string, any>;
}

export interface SameEntityMatch {
  match_id: string;
  entity_type: string;
  display_name: string;
  primary_key: string;
  confidence: number;
  confidence_percent: string;
  records_count: number;
  files_involved: string[];
  matched_keys: string[];
  records: SameEntityMatchRecord[];
}

export interface RelationshipSummary {
  files_uploaded: number;
  records_scanned: number;
  relationships_found: number;
  records_connected: number;
  average_confidence: number;
}

export interface RelationshipIndexData {
  summary: RelationshipSummary;
  relationship_type_counts: Record<string, number>;
  relationships: RelationshipEdge[];
  entity_matches: SameEntityMatch[];
}

export interface BatchProcessResponse {
  batch_id: string;
  total_files: number;
  successful_files?: number;
  failed_files?: number;
  total_pages?: number;
  processed_pages?: number;
  total_extracted_records?: number;
  failed_file_details?: Array<{ filename: string; error: string }>;
  results: ProcessResponse[];
  processing_time_ms: number;
  relationship_index?: RelationshipIndexData;
  total_entities_linked?: number;
}

export interface HistoryItem {
  id: string;
  filename: string;
  file_type: string;
  classification: string;
  processed_at: string;
  status: string;
  records_count: number;
  result: ProcessResponse;
}
