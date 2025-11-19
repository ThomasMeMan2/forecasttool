/**
 * TypeScript types for Forecast Studio
 */

export interface Project {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
  dataset_count?: number;
  timeseries_count?: number;
  forecast_count?: number;
}

export interface Dataset {
  id: number;
  project_id: number;
  version: number;
  type: string;
  filename: string;
  uploaded_at: string;
  row_count: number;
  has_missing_values: boolean;
  has_duplicates: boolean;
  has_outliers: boolean;
  quality_score?: number;
  quality_issues?: string[];
}

export interface TimeSeries {
  id: number;
  project_id: number;
  ts_id: string;
  data_start_date?: string;
  data_end_date?: string;
  data_points?: number;
  frequency?: string;
  has_seasonality?: boolean;
  has_trend?: boolean;
  volatility_score?: number;
  missing_percentage?: number;
  outlier_count?: number;
  created_at: string;
  updated_at: string;
}

export interface ForecastPoint {
  timestamp: string;
  mean: number;
  lower_80: number;
  upper_80: number;
  lower_90: number;
  upper_90: number;
}

export interface Forecast {
  id: number;
  project_id: number;
  timeseries_id: number;
  ts_id: string;
  model_used: string;
  forecast_horizon: number;
  confidence_level: number;
  forecast_data: ForecastPoint[];
  confidence_score?: number;
  requires_manual_review: boolean;
  anomaly_flags?: string[];
  mape?: number;
  rmse?: number;
  mae?: number;
  generated_at: string;
}

export interface DataValidationResult {
  is_valid: boolean;
  total_rows: number;
  unique_ids: number;
  date_range?: {
    start: string;
    end: string;
  };
  issues: string[];
  warnings: string[];
  statistics?: Record<string, number>;
}
