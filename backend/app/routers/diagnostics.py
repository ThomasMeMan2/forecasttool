"""
Diagnostics API endpoints (Phase 3)
Advanced time series diagnostics and analysis
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
import logging

from ..database import get_db
from ..models import Project, TimeSeries, Forecast
from ..services.diagnostics import DiagnosticsService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{project_id}/timeseries/{ts_id}/diagnostics")
async def get_timeseries_diagnostics(
    project_id: int,
    ts_id: str,
    frequency: str = Query("D", description="Data frequency (D, W, MS, QS)"),
    db: Session = Depends(get_db),
):
    """
    Generate comprehensive diagnostics for a time series.

    Returns:
    - ACF/PACF analysis
    - Seasonal decomposition
    - Stationarity tests
    - Summary statistics
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get timeseries
    timeseries = (
        db.query(TimeSeries)
        .filter(
            TimeSeries.project_id == project_id,
            TimeSeries.ts_id == ts_id
        )
        .first()
    )

    if not timeseries:
        raise HTTPException(status_code=404, detail="Timeseries not found")

    try:
        # Load timeseries data from the latest dataset
        from ..services.data_processing import DataProcessingService
        data_service = DataProcessingService()

        # Get the latest dataset for this project
        from ..models import Dataset
        latest_dataset = (
            db.query(Dataset)
            .filter(Dataset.project_id == project_id)
            .order_by(Dataset.uploaded_at.desc())
            .first()
        )

        if not latest_dataset:
            raise HTTPException(status_code=404, detail="No dataset found for this project")

        # Load and filter data for this timeseries
        import polars as pl
        data = pl.read_csv(latest_dataset.filename)

        # Filter for this specific ts_id
        ts_data = data.filter(pl.col("unique_id") == ts_id)

        if ts_data.height == 0:
            raise HTTPException(status_code=404, detail=f"No data found for timeseries {ts_id}")

        # Convert to pandas for diagnostics (statsmodels requires pandas)
        ts_data_pd = ts_data.select(["ds", "y"]).to_pandas()

        # Generate diagnostics
        diagnostics_service = DiagnosticsService()
        diagnostics = diagnostics_service.generate_full_diagnostics(
            ts_data_pd,
            frequency=frequency
        )

        return {
            "success": True,
            "ts_id": ts_id,
            "project_id": project_id,
            "frequency": frequency,
            "diagnostics": diagnostics,
        }

    except Exception as e:
        logger.error(f"Diagnostics generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Diagnostics generation failed: {str(e)}")


@router.get("/{project_id}/forecasts/{forecast_id}/residuals")
async def get_forecast_residuals(
    project_id: int,
    forecast_id: int,
    db: Session = Depends(get_db),
):
    """
    Analyze residuals for a specific forecast.

    Returns:
    - Residual statistics
    - Normality tests
    - Autocorrelation tests
    - Quality assessment
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get forecast
    forecast = (
        db.query(Forecast)
        .filter(
            Forecast.id == forecast_id,
            Forecast.project_id == project_id
        )
        .first()
    )

    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")

    try:
        # Load actual data for comparison
        from ..models import Dataset
        latest_dataset = (
            db.query(Dataset)
            .filter(Dataset.project_id == project_id)
            .order_by(Dataset.uploaded_at.desc())
            .first()
        )

        if not latest_dataset:
            raise HTTPException(status_code=404, detail="No dataset found")

        import polars as pl
        import numpy as np
        data = pl.read_csv(latest_dataset.filename)

        # Filter for this timeseries
        ts_data = data.filter(pl.col("unique_id") == forecast.ts_id)

        if ts_data.height == 0:
            raise HTTPException(status_code=404, detail="No actual data found")

        # Get actual values (last N points matching forecast horizon)
        actual_values = ts_data.select("y").to_numpy().flatten()

        # Get forecasted values (mean predictions)
        forecast_values = np.array([point["mean"] for point in forecast.forecast_data])

        # Need to align actual and forecast for residuals analysis
        # Use holdout/test set if available, otherwise use in-sample fit
        n_forecast = len(forecast_values)

        if len(actual_values) >= n_forecast:
            # Use last n_forecast points as actuals for comparison
            actual_aligned = actual_values[-n_forecast:]
        else:
            raise HTTPException(
                status_code=400,
                detail="Not enough actual data for residual analysis"
            )

        # Analyze residuals
        diagnostics_service = DiagnosticsService()
        residuals_analysis = diagnostics_service.analyze_residuals(
            actual_aligned,
            forecast_values
        )

        return {
            "success": True,
            "forecast_id": forecast_id,
            "ts_id": forecast.ts_id,
            "analysis": residuals_analysis,
        }

    except Exception as e:
        logger.error(f"Residual analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Residual analysis failed: {str(e)}")


@router.get("/{project_id}/timeseries/{ts_id}/summary")
async def get_timeseries_summary(
    project_id: int,
    ts_id: str,
    db: Session = Depends(get_db),
):
    """
    Get a quick statistical summary of a timeseries.

    Returns basic statistics without heavy computation.
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get timeseries
    timeseries = (
        db.query(TimeSeries)
        .filter(
            TimeSeries.project_id == project_id,
            TimeSeries.ts_id == ts_id
        )
        .first()
    )

    if not timeseries:
        raise HTTPException(status_code=404, detail="Timeseries not found")

    try:
        # Load data
        from ..models import Dataset
        latest_dataset = (
            db.query(Dataset)
            .filter(Dataset.project_id == project_id)
            .order_by(Dataset.uploaded_at.desc())
            .first()
        )

        if not latest_dataset:
            raise HTTPException(status_code=404, detail="No dataset found")

        import polars as pl
        import numpy as np
        data = pl.read_csv(latest_dataset.filename)

        # Filter for this timeseries
        ts_data = data.filter(pl.col("unique_id") == ts_id)

        if ts_data.height == 0:
            raise HTTPException(status_code=404, detail=f"No data found for {ts_id}")

        values = ts_data.select("y").to_numpy().flatten()

        # Calculate summary statistics
        diagnostics_service = DiagnosticsService()
        summary = diagnostics_service._calculate_summary_stats(values)

        return {
            "success": True,
            "ts_id": ts_id,
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Summary calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summary failed: {str(e)}")
