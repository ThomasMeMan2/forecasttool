"""
LLM Insights API endpoints (Phase 3)
AI-powered natural language insights about data and forecasts
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
from datetime import datetime

from ..database import get_db
from ..models import Project, TimeSeries, Forecast, ProjectInsight
from ..services.llm_insights import LLMInsightsService
from ..config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/{project_id}/timeseries/{ts_id}/insights/history")
async def generate_history_insight(
    project_id: int,
    ts_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Generate AI insights about historical data patterns.

    Uses LLM to analyze:
    - Data trends and patterns
    - Seasonality characteristics
    - Notable features
    - Data quality observations
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
        # Load timeseries data
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
        data = pl.read_csv(latest_dataset.filename)
        ts_data = data.filter(pl.col("unique_id") == ts_id)

        if ts_data.height == 0:
            raise HTTPException(status_code=404, detail=f"No data found for {ts_id}")

        # Convert to pandas for insights service
        ts_data_pd = ts_data.to_pandas()

        # Generate insight
        llm_service = LLMInsightsService()
        insight_text = llm_service.generate_history_summary(ts_data_pd, ts_id)

        # Save insight to database
        insight = ProjectInsight(
            project_id=project_id,
            timeseries_id=timeseries.id,
            insight_type="history_summary",
            insight_text=insight_text,
            confidence=0.8 if settings.enable_llm_insights else 0.5,
            llm_model=settings.llm_model if settings.enable_llm_insights else "template",
            generated_at=datetime.utcnow()
        )

        db.add(insight)
        db.commit()
        db.refresh(insight)

        return {
            "success": True,
            "insight": {
                "id": insight.id,
                "type": insight.insight_type,
                "text": insight.insight_text,
                "confidence": insight.confidence,
                "model": insight.llm_model,
                "generated_at": insight.generated_at.isoformat(),
            }
        }

    except Exception as e:
        logger.error(f"History insight generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")


@router.post("/{project_id}/forecasts/{forecast_id}/insights/forecast")
async def generate_forecast_insight(
    project_id: int,
    forecast_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate AI insights about a forecast.

    Uses LLM to analyze:
    - Forecast direction and magnitude
    - Confidence levels
    - Notable predictions
    - Recommendations
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
        # Load historical data for context
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
        import pandas as pd
        data = pl.read_csv(latest_dataset.filename)
        ts_data = data.filter(pl.col("unique_id") == forecast.ts_id)

        if ts_data.height == 0:
            raise HTTPException(status_code=404, detail="No data found")

        # Convert to pandas
        ts_data_pd = ts_data.to_pandas()

        # Prepare forecast data
        forecast_df = pd.DataFrame(forecast.forecast_data)

        # Generate insight
        llm_service = LLMInsightsService()
        insight_text = llm_service.generate_forecast_summary(
            ts_data_pd,
            forecast_df,
            forecast.ts_id,
            forecast.model_used
        )

        # Save insight
        insight = ProjectInsight(
            project_id=project_id,
            forecast_id=forecast.id,
            insight_type="forecast_summary",
            insight_text=insight_text,
            confidence=0.8 if settings.enable_llm_insights else 0.5,
            llm_model=settings.llm_model if settings.enable_llm_insights else "template",
            generated_at=datetime.utcnow()
        )

        db.add(insight)
        db.commit()
        db.refresh(insight)

        return {
            "success": True,
            "insight": {
                "id": insight.id,
                "type": insight.insight_type,
                "text": insight.insight_text,
                "confidence": insight.confidence,
                "model": insight.llm_model,
                "generated_at": insight.generated_at.isoformat(),
            }
        }

    except Exception as e:
        logger.error(f"Forecast insight generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")


@router.post("/{project_id}/forecasts/{forecast_id}/insights/quality")
async def generate_quality_insight(
    project_id: int,
    forecast_id: int,
    db: Session = Depends(get_db),
):
    """
    Generate AI insights about forecast quality and reliability.

    Uses LLM to assess:
    - Confidence levels
    - Model performance
    - Reliability indicators
    - Risk factors
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
        # Prepare quality metrics
        quality_metrics = {
            "model_used": forecast.model_used,
            "confidence_score": forecast.confidence_score,
            "mape": forecast.mape,
            "rmse": forecast.rmse,
            "mae": forecast.mae,
            "requires_review": forecast.requires_manual_review,
            "anomaly_flags": forecast.anomaly_flags or [],
            "forecast_value_added": forecast.forecast_value_added,
        }

        # Generate insight
        llm_service = LLMInsightsService()
        insight_text = llm_service.generate_quality_assessment(
            forecast.ts_id,
            quality_metrics
        )

        # Save insight
        insight = ProjectInsight(
            project_id=project_id,
            forecast_id=forecast.id,
            insight_type="quality_assessment",
            insight_text=insight_text,
            confidence=0.8 if settings.enable_llm_insights else 0.5,
            llm_model=settings.llm_model if settings.enable_llm_insights else "template",
            generated_at=datetime.utcnow()
        )

        db.add(insight)
        db.commit()
        db.refresh(insight)

        return {
            "success": True,
            "insight": {
                "id": insight.id,
                "type": insight.insight_type,
                "text": insight.insight_text,
                "confidence": insight.confidence,
                "model": insight.llm_model,
                "generated_at": insight.generated_at.isoformat(),
            }
        }

    except Exception as e:
        logger.error(f"Quality insight generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")


@router.get("/{project_id}/insights")
async def get_project_insights(
    project_id: int,
    insight_type: Optional[str] = None,
    timeseries_id: Optional[int] = None,
    forecast_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all insights for a project with optional filtering.
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build query
    query = db.query(ProjectInsight).filter(ProjectInsight.project_id == project_id)

    if insight_type:
        query = query.filter(ProjectInsight.insight_type == insight_type)

    if timeseries_id:
        query = query.filter(ProjectInsight.timeseries_id == timeseries_id)

    if forecast_id:
        query = query.filter(ProjectInsight.forecast_id == forecast_id)

    # Get insights
    insights = query.order_by(ProjectInsight.generated_at.desc()).limit(limit).all()

    return {
        "success": True,
        "count": len(insights),
        "insights": [
            {
                "id": insight.id,
                "project_id": insight.project_id,
                "timeseries_id": insight.timeseries_id,
                "forecast_id": insight.forecast_id,
                "type": insight.insight_type,
                "text": insight.insight_text,
                "confidence": insight.confidence,
                "model": insight.llm_model,
                "generated_at": insight.generated_at.isoformat(),
            }
            for insight in insights
        ]
    }


@router.delete("/{project_id}/insights/{insight_id}")
async def delete_insight(
    project_id: int,
    insight_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete an insight.
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get insight
    insight = (
        db.query(ProjectInsight)
        .filter(
            ProjectInsight.id == insight_id,
            ProjectInsight.project_id == project_id
        )
        .first()
    )

    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    db.delete(insight)
    db.commit()

    return {"success": True, "message": "Insight deleted"}
