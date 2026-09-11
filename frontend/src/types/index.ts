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

// ----------------- Retail Intelligence Types ----------------- //

export interface ExecutiveKPIs {
  total_revenue: number;
  total_units_sold: number;
  total_transactions: number;
  avg_order_value: number;
  unique_customers?: number;
  unique_products?: number;
}

export interface ProductMetric {
  product_name: string;
  units_sold: number;
  revenue: number;
  category?: string;
  stock_level?: number;
  revenue_share_pct?: number;
}

export interface DeadStockItem {
  product_name: string;
  stock_quantity: number;
  days_inactive: string;
  recommendation: string;
}

export interface TrendingProductItem {
  product_name: string;
  velocity: string;
  growth_rate_pct: number;
  revenue: number;
  recommendation: string;
}

export interface CategoryBreakdownItem {
  category: string;
  revenue: number;
  units_sold: number;
}

export interface ProductAnalytics {
  top_selling: ProductMetric[];
  least_selling: ProductMetric[];
  dead_stock: DeadStockItem[];
  trending_products: TrendingProductItem[];
  category_breakdown: CategoryBreakdownItem[];
}

export interface CustomerSegmentSummary {
  segment_name: string;
  customer_count: number;
  percentage: number;
  avg_spend: number;
  actionable_strategy: string;
  badge_color: string;
}

export interface CustomerRFMItem {
  customer_id: string;
  segment: string;
  orders_count: number;
  total_spend: number;
  last_active_days_ago: number;
}

export interface CustomerIntelligence {
  segments_summary: CustomerSegmentSummary[];
  top_customers: CustomerRFMItem[];
  total_profiled_customers: number;
}

export interface MarketBasketPair {
  item_a: string;
  item_b: string;
  co_occurrence_count: number;
  confidence_pct: number;
  recommendation: string;
}

export interface MarketBasketAnalysis {
  pairs: MarketBasketPair[];
  total_basket_transactions: number;
}

export interface DemandForecastItem {
  product_name: string;
  historical_units_sold: number;
  current_stock?: number;
  projected_demand_7d: number;
  projected_demand_30d: number;
  daily_run_rate: number;
  inventory_status: string;
  actionable_advice: string;
  badge_color: string;
}

export interface DemandForecasting {
  forecasts: DemandForecastItem[];
  model_used: string;
}

export interface RetailIntelligenceReport {
  kpis: ExecutiveKPIs;
  product_analytics: ProductAnalytics;
  customer_intelligence: CustomerIntelligence;
  basket_analysis: MarketBasketAnalysis;
  demand_forecasting: DemandForecasting;
  entity_classification?: Record<string, any>;
}

export interface UnifiedWarehouseView {
  title: string;
  source_tables: string[];
  total_records: number;
  columns: string[];
  records: Array<Record<string, any>>;
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
  raw_text?: string;
  errors?: ValidationErrorItem[];
  entity_classification?: Record<string, any>;
  retail_intelligence?: RetailIntelligenceReport;
}

export interface BatchProcessResponse {
  batch_id: string;
  total_files: number;
  results: ProcessResponse[];
  processing_time_ms: number;
  unified_warehouse?: UnifiedWarehouseView;
  batch_intelligence?: RetailIntelligenceReport;
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
