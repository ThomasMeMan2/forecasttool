"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


# ============= User Schemas =============
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ============= Project Schemas =============
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_archived: Optional[bool] = None


class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    is_archived: bool

    model_config = ConfigDict(from_attributes=True)


class ProjectWithStats(ProjectResponse):
    """Project with additional statistics"""

    dataset_count: int = 0
    timeseries_count: int = 0
    forecast_count: int = 0


# ============= Dataset Schemas =============
class DatasetUploadResponse(BaseModel):
    id: int
    project_id: int
    version: int
    type: str
    filename: str
    uploaded_at: datetime
    row_count: int
    has_missing_values: bool
    has_duplicates: bool
    has_outliers: bool
    quality_score: Optional[float] = None
    quality_issues: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


# ============= TimeSeries Schemas =============
class TimeSeriesBase(BaseModel):
    ts_id: str
    data_start_date: Optional[datetime] = None
    data_end_date: Optional[datetime] = None
    data_points: Optional[int] = None
    frequency: Optional[str] = None
    has_seasonality: Optional[bool] = None
    has_trend: Optional[bool] = None
    volatility_score: Optional[float] = None
    missing_percentage: Optional[float] = None
    outlier_count: Optional[int] = None


class TimeSeriesResponse(TimeSeriesBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Forecast Schemas =============
class ForecastRequest(BaseModel):
    """Request to generate forecast"""

    timeseries_ids: Optional[List[str]] = Field(
        None, description="Specific timeseries IDs to forecast. If None, forecast all."
    )
    horizon: int = Field(12, ge=1, le=52, description="Forecast horizon in periods")
    confidence_level: int = Field(
        90, description="Confidence level for prediction intervals (80, 90, or 95)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"timeseries_ids": ["product_1", "product_2"], "horizon": 12, "confidence_level": 90}
        }
    )


class ForecastPoint(BaseModel):
    """Single forecast data point"""

    timestamp: datetime
    mean: float
    lower_80: float
    upper_80: float
    lower_90: float
    upper_90: float


class ForecastResponse(BaseModel):
    id: int
    project_id: int
    timeseries_id: int
    ts_id: str  # Original identifier
    model_used: str
    forecast_horizon: int
    confidence_level: int
    forecast_data: List[ForecastPoint]
    confidence_score: Optional[float] = None
    requires_manual_review: bool
    anomaly_flags: Optional[List[str]] = None
    mape: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Data Validation Schemas =============
class DataValidationResult(BaseModel):
    """Result of data validation"""

    is_valid: bool
    total_rows: int
    unique_ids: int
    date_range: Optional[Dict[str, str]] = None
    issues: List[str] = []
    warnings: List[str] = []
    statistics: Optional[Dict[str, Any]] = None


# ============= Generic Responses =============
class MessageResponse(BaseModel):
    message: str
    detail: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int


# ============= Phase 2: Event Schemas =============
class GlobalEventBase(BaseModel):
    event_name: str = Field(..., min_length=1)
    event_date: datetime
    event_type: Optional[str] = None  # 'holiday', 'campaign', 'price_change', 'custom'
    impact_value: Optional[float] = None
    description: Optional[str] = None


class GlobalEventCreate(GlobalEventBase):
    pass


class GlobalEventUpdate(BaseModel):
    event_name: Optional[str] = None
    event_date: Optional[datetime] = None
    event_type: Optional[str] = None
    impact_value: Optional[float] = None
    description: Optional[str] = None


class GlobalEventResponse(GlobalEventBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IDSpecificEventBase(BaseModel):
    timeseries_id: int
    event_name: str = Field(..., min_length=1)
    event_date: datetime
    event_type: Optional[str] = None  # 'stockout', 'promotion', 'closure', 'custom'
    impact_value: Optional[float] = None
    description: Optional[str] = None


class IDSpecificEventCreate(IDSpecificEventBase):
    pass


class IDSpecificEventUpdate(BaseModel):
    event_name: Optional[str] = None
    event_date: Optional[datetime] = None
    event_type: Optional[str] = None
    impact_value: Optional[float] = None
    description: Optional[str] = None


class IDSpecificEventResponse(IDSpecificEventBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Phase 2: User Exclusion Schemas =============
class UserExclusionBase(BaseModel):
    timeseries_id: int
    start_date: datetime
    end_date: datetime
    reason: str = Field(..., min_length=1)
    is_active: bool = True


class UserExclusionCreate(UserExclusionBase):
    pass


class UserExclusionUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    reason: Optional[str] = None
    is_active: Optional[bool] = None


class UserExclusionResponse(UserExclusionBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Phase 2: Forecast Adjustment Schemas =============
class ForecastAdjustmentBase(BaseModel):
    period_timestamp: datetime
    adjusted_value: float
    adjustment_reason: str = Field(..., min_length=1)


class ForecastAdjustmentCreate(ForecastAdjustmentBase):
    forecast_id: int
    original_value: float


class ForecastAdjustmentResponse(ForecastAdjustmentBase):
    id: int
    forecast_id: int
    original_value: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Phase 2: LLM Insight Schemas =============
class ProjectInsightResponse(BaseModel):
    id: int
    project_id: int
    timeseries_id: Optional[int] = None
    forecast_id: Optional[int] = None
    insight_type: str
    insight_text: str
    confidence: Optional[float] = None
    llm_model: Optional[str] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
