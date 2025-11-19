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
