"""
Forecast generation and management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import polars as pl
import csv
import io
from app.database import get_db
from app.models import Project, ProjectDataset, TimeSeries, Forecast
from app.schemas import ForecastRequest, ForecastResponse, ForecastPoint, MessageResponse
from app.services.forecast_engine import ForecastEngine

router = APIRouter()


@router.post(
    "/{project_id}/generate",
    response_model=List[ForecastResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_forecasts(
    project_id: int,
    request: ForecastRequest,
    db: Session = Depends(get_db),
):
    """
    Generate forecasts for timeseries in a project.

    Args:
        project_id: Project ID
        request: Forecast parameters (timeseries_ids, horizon, confidence_level)

    Process:
        1. Load the latest dataset
        2. Generate forecasts using AutoARIMA
        3. Calculate accuracy metrics and quality scores
        4. Store forecast results
        5. Return forecast data with prediction intervals
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Get latest dataset
    latest_dataset = (
        db.query(ProjectDataset)
        .filter(ProjectDataset.project_id == project_id, ProjectDataset.type == "history")
        .order_by(ProjectDataset.version.desc())
        .first()
    )

    if not latest_dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dataset found. Please upload data first.",
        )

    # Load data
    try:
        data = pl.read_csv(latest_dataset.file_path)
        # Parse timestamp
        data = data.with_columns(
            pl.col("timestamp").str.strptime(pl.Datetime, format="%+", strict=False)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading dataset: {str(e)}",
        )

    # Determine which timeseries to forecast
    if request.timeseries_ids:
        ts_ids_to_forecast = request.timeseries_ids
    else:
        # Forecast all timeseries in the project
        ts_records = (
            db.query(TimeSeries).filter(TimeSeries.project_id == project_id).all()
        )
        ts_ids_to_forecast = [ts.ts_id for ts in ts_records]

    if not ts_ids_to_forecast:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No timeseries found to forecast",
        )

    # Initialize forecast engine
    engine = ForecastEngine()

    # Generate forecasts
    forecast_results = []

    for ts_id in ts_ids_to_forecast:
        # Get TimeSeries record
        ts_record = (
            db.query(TimeSeries)
            .filter(TimeSeries.project_id == project_id, TimeSeries.ts_id == ts_id)
            .first()
        )

        if not ts_record:
            # Skip if timeseries not found
            continue

        # Generate forecast
        result = engine.generate_forecast(
            data=data,
            ts_id=ts_id,
            horizon=request.horizon,
            confidence_levels=[80, 90],
        )

        if not result["success"]:
            # Log error but continue with other timeseries
            continue

        # Create Forecast record
        forecast_record = Forecast(
            project_id=project_id,
            timeseries_id=ts_record.id,
            model_used=result["model_used"],
            forecast_horizon=request.horizon,
            confidence_level=request.confidence_level,
            forecast_data=result["forecast_points"],
            confidence_score=result["confidence_score"],
            requires_manual_review=result["requires_manual_review"],
            anomaly_flags=result["anomaly_flags"],
            mape=result["metrics"].get("mape"),
            rmse=result["metrics"].get("rmse"),
            mae=result["metrics"].get("mae"),
        )

        db.add(forecast_record)
        db.flush()
        db.refresh(forecast_record)

        # Format response
        forecast_points = [
            ForecastPoint(**point) for point in result["forecast_points"]
        ]

        forecast_response = ForecastResponse(
            id=forecast_record.id,
            project_id=project_id,
            timeseries_id=ts_record.id,
            ts_id=ts_id,
            model_used=result["model_used"],
            forecast_horizon=request.horizon,
            confidence_level=request.confidence_level,
            forecast_data=forecast_points,
            confidence_score=result["confidence_score"],
            requires_manual_review=result["requires_manual_review"],
            anomaly_flags=result["anomaly_flags"],
            mape=result["metrics"].get("mape"),
            rmse=result["metrics"].get("rmse"),
            mae=result["metrics"].get("mae"),
            generated_at=forecast_record.generated_at,
        )

        forecast_results.append(forecast_response)

    db.commit()

    if not forecast_results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No forecasts could be generated. Check data quality.",
        )

    return forecast_results


@router.get("/{project_id}/forecasts", response_model=List[ForecastResponse])
async def list_forecasts(
    project_id: int,
    timeseries_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    List all forecasts for a project.

    Args:
        project_id: Project ID
        timeseries_id: Optional filter by specific timeseries
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    query = db.query(Forecast).filter(Forecast.project_id == project_id)

    if timeseries_id:
        query = query.filter(Forecast.timeseries_id == timeseries_id)

    forecasts = query.order_by(Forecast.generated_at.desc()).all()

    # Format responses
    result = []
    for forecast in forecasts:
        ts_record = (
            db.query(TimeSeries).filter(TimeSeries.id == forecast.timeseries_id).first()
        )

        forecast_points = [ForecastPoint(**point) for point in forecast.forecast_data]

        result.append(
            ForecastResponse(
                id=forecast.id,
                project_id=forecast.project_id,
                timeseries_id=forecast.timeseries_id,
                ts_id=ts_record.ts_id if ts_record else "unknown",
                model_used=forecast.model_used,
                forecast_horizon=forecast.forecast_horizon,
                confidence_level=forecast.confidence_level,
                forecast_data=forecast_points,
                confidence_score=forecast.confidence_score,
                requires_manual_review=forecast.requires_manual_review,
                anomaly_flags=forecast.anomaly_flags,
                mape=forecast.mape,
                rmse=forecast.rmse,
                mae=forecast.mae,
                generated_at=forecast.generated_at,
            )
        )

    return result


@router.get("/{project_id}/forecasts/{forecast_id}", response_model=ForecastResponse)
async def get_forecast(
    project_id: int, forecast_id: int, db: Session = Depends(get_db)
):
    """Get a specific forecast by ID"""
    forecast = (
        db.query(Forecast)
        .filter(Forecast.id == forecast_id, Forecast.project_id == project_id)
        .first()
    )

    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    ts_record = (
        db.query(TimeSeries).filter(TimeSeries.id == forecast.timeseries_id).first()
    )

    forecast_points = [ForecastPoint(**point) for point in forecast.forecast_data]

    return ForecastResponse(
        id=forecast.id,
        project_id=forecast.project_id,
        timeseries_id=forecast.timeseries_id,
        ts_id=ts_record.ts_id if ts_record else "unknown",
        model_used=forecast.model_used,
        forecast_horizon=forecast.forecast_horizon,
        confidence_level=forecast.confidence_level,
        forecast_data=forecast_points,
        confidence_score=forecast.confidence_score,
        requires_manual_review=forecast.requires_manual_review,
        anomaly_flags=forecast.anomaly_flags,
        mape=forecast.mape,
        rmse=forecast.rmse,
        mae=forecast.mae,
        generated_at=forecast.generated_at,
    )


@router.delete("/{project_id}/forecasts/{forecast_id}", response_model=MessageResponse)
async def delete_forecast(
    project_id: int, forecast_id: int, db: Session = Depends(get_db)
):
    """Delete a forecast"""
    forecast = (
        db.query(Forecast)
        .filter(Forecast.id == forecast_id, Forecast.project_id == project_id)
        .first()
    )

    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    db.delete(forecast)
    db.commit()

    return MessageResponse(
        message="Forecast deleted successfully", detail={"forecast_id": forecast_id}
    )


@router.get("/{project_id}/forecasts/{forecast_id}/export")
async def export_forecast_csv(
    project_id: int, forecast_id: int, db: Session = Depends(get_db)
):
    """
    Export forecast to CSV format.

    CSV includes: timestamp, mean, lower_80, upper_80, lower_90, upper_90
    """
    forecast = (
        db.query(Forecast)
        .filter(Forecast.id == forecast_id, Forecast.project_id == project_id)
        .first()
    )

    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    # Get timeseries info
    ts_record = (
        db.query(TimeSeries).filter(TimeSeries.id == forecast.timeseries_id).first()
    )

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        ["timestamp", "mean", "lower_80", "upper_80", "lower_90", "upper_90"]
    )

    # Write data
    for point in forecast.forecast_data:
        writer.writerow(
            [
                point["timestamp"],
                point["mean"],
                point["lower_80"],
                point["upper_80"],
                point["lower_90"],
                point["upper_90"],
            ]
        )

    # Return CSV response
    filename = f"forecast_{ts_record.ts_id if ts_record else forecast_id}_{forecast.generated_at.strftime('%Y%m%d')}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
