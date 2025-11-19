"""
SQLAlchemy models for Forecast Studio
Phase 1 MVP models: Users, Projects, ProjectDatasets, TimeSeries, Forecasts
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    JSON,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """User model for authentication"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    """Project model - isolated forecasting workspace"""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_archived = Column(Boolean, default=False)

    # Relationships
    owner = relationship("User", back_populates="projects")
    datasets = relationship(
        "ProjectDataset", back_populates="project", cascade="all, delete-orphan"
    )
    timeseries = relationship(
        "TimeSeries", back_populates="project", cascade="all, delete-orphan"
    )
    forecasts = relationship(
        "Forecast", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectDataset(Base):
    """Dataset uploads for a project (versioned)"""

    __tablename__ = "project_datasets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    version = Column(Integer, nullable=False)
    type = Column(
        String, nullable=False
    )  # 'history', 'global_events', 'id_events'
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    row_count = Column(Integer)
    file_path = Column(String, nullable=False)  # Path to stored CSV file

    # Data quality metadata
    has_missing_values = Column(Boolean, default=False)
    has_duplicates = Column(Boolean, default=False)
    has_outliers = Column(Boolean, default=False)
    quality_score = Column(Float)  # 0-100 score
    quality_issues = Column(JSON)  # List of specific issues

    # Relationships
    project = relationship("Project", back_populates="datasets")


class TimeSeries(Base):
    """Processed timeseries data (one row per unique ts_id in a project)"""

    __tablename__ = "timeseries"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    ts_id = Column(String, nullable=False, index=True)  # User's identifier (e.g., product_id, store_id)

    # Data characteristics
    data_start_date = Column(DateTime(timezone=True))
    data_end_date = Column(DateTime(timezone=True))
    data_points = Column(Integer)
    frequency = Column(String)  # 'daily', 'weekly', 'monthly', 'quarterly'

    # Statistical properties
    has_seasonality = Column(Boolean)
    has_trend = Column(Boolean)
    volatility_score = Column(Float)  # 0-100

    # Data quality
    missing_percentage = Column(Float)
    outlier_count = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project = relationship("Project", back_populates="timeseries")
    forecasts = relationship(
        "Forecast", back_populates="timeseries", cascade="all, delete-orphan"
    )


class Forecast(Base):
    """Generated forecasts for a timeseries"""

    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    timeseries_id = Column(Integer, ForeignKey("timeseries.id"), nullable=False)

    # Forecast metadata
    model_used = Column(String, nullable=False)
    forecast_horizon = Column(Integer, nullable=False)
    confidence_level = Column(Integer, nullable=False)  # 80, 90, 95

    # Forecast data (stored as JSON array)
    # Each entry: {timestamp, mean, lower_80, upper_80, lower_90, upper_90}
    forecast_data = Column(JSON, nullable=False)

    # Quality metrics
    confidence_score = Column(Float)  # 0-100
    requires_manual_review = Column(Boolean, default=False)
    anomaly_flags = Column(JSON)  # List of flags

    # Model performance metrics
    mape = Column(Float)  # Mean Absolute Percentage Error
    rmse = Column(Float)  # Root Mean Squared Error
    mae = Column(Float)  # Mean Absolute Error

    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="forecasts")
    timeseries = relationship("TimeSeries", back_populates="forecasts")
