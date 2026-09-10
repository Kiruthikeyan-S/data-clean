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

export interface QualityDimension {
  id: string; // 'missing_values' | 'duplicates' | 'wrong_data_types' | 'invalid_values' | 'outliers' | 'format_differences'
  title: string;
  count: number;
  status: string;
  summary: string;
  affected_columns?: string[];
  items: AuditDetailItem[];
  raw_samples?: Array<Record<string, any>>;
}

export interface QualityAuditReport {
  dimensions: QualityDimension[];
  total_issues_handled: number;
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
}

export interface ProcessSummary {
  total_records: number;
  valid_records: number;
  invalid_records: number;
  processing_time_ms: number;
  file_type: string;
  classification: string;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  percentage?: number;
  color?: string;
}

export interface DatasetChart {
  id: string;
  title: string;
  chart_type: 'pie' | 'bar' | 'donut';
  column_name: string;
  data: ChartDataPoint[];
}

export interface MatplotlibPlot {
  id: string;
  title: string;
  description: string;
  plot_type: string;
  image_base64: string;
  columns_analyzed?: string[];
}

export interface DataVisualizations {
  has_charts: boolean;
  summary_insights: string[];
  charts: DatasetChart[];
  matplotlib_plots?: MatplotlibPlot[];
}

export interface EntityFieldBreakdown {
  store_fields: string[];
  item_fields: string[];
  customer_fields: string[];
  transaction_fields: string[];
}

export interface RetailMetricItem {
  label: string;
  value: string | number;
  subtext?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export interface RetailRankingItem {
  name: string;
  category?: string;
  metric_value: number;
  metric_label: string;
  rank: number;
}

export interface RetailIntelligence {
  entity_type: 'STORE' | 'ITEM' | 'CUSTOMER' | 'COMBINED_TRANSACTION' | 'GENERAL_RETAIL';
  entity_label: string;
  entity_breakdown?: EntityFieldBreakdown;
  best_selling_items: RetailRankingItem[];
  least_selling_items: RetailRankingItem[];
  store_sales: Array<{ store: string; sales: number; unit: string }>;
  customer_patterns: Array<{ segment: string; count: number; share: string }>;
  sales_forecast: Array<{ period: string; value: number; type: string }>;
  inventory_recommendations: Array<{ action: string; item: string; badge: string; type: string; reason: string }>;
  summary_metrics: RetailMetricItem[];
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
  visualizations?: DataVisualizations;
  retail_intelligence?: RetailIntelligence;
  fields?: ProcessedField[];
  structured_data?: Record<string, any> | Array<Record<string, any>>;
  columns?: string[];
  raw_text?: string;
  errors?: ValidationErrorItem[];
}

export interface BatchProcessResponse {
  batch_id: string;
  total_files: number;
  results: ProcessResponse[];
  processing_time_ms: number;
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
