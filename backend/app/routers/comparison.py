"""
Forecast Comparison endpoints (Phase 4)
Compare multiple forecasts side-by-side with statistical tests
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
import numpy as np

from ..database import get_db
from ..services.auth import get_current_user, verify_project_access
from ..models import User, Forecast, ForecastComparison

router = APIRouter()


# ============= Schemas =============

class ComparisonCreate(BaseModel):
    comparison_name: str
    forecast_ids: List[int]


class ComparisonResponse(BaseModel):
    id: int
    project_id: int
    comparison_name: str
    forecast_ids: List[int]
    comparison_metrics: Dict[str, Any]
    winner_forecast_id: int | None
    created_at: str

    class Config:
        from_attributes = True


# ============= Endpoints =============

@router.post("/{project_id}/comparisons", response_model=ComparisonResponse, status_code=status.HTTP_201_CREATED)
async def create_comparison(
    project_id: int,
    comparison_data: ComparisonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a forecast comparison.

    Compares multiple forecasts and calculates relative performance metrics.
    """
    verify_project_access(project_id, current_user, db)

    if len(comparison_data.forecast_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 forecasts are required for comparison"
        )

    # Load forecasts
    forecasts = []
    for fid in comparison_data.forecast_ids:
        forecast = db.query(Forecast).filter(
            Forecast.id == fid,
            Forecast.project_id == project_id
        ).first()

        if not forecast:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Forecast {fid} not found"
            )

        forecasts.append(forecast)

    # Calculate comparison metrics
    comparison_metrics = _calculate_comparison_metrics(forecasts)

    # Determine winner (lowest MAPE)
    winner_id = None
    if all(f.mape is not None for f in forecasts):
        winner = min(forecasts, key=lambda f: f.mape if f.mape else float('inf'))
        winner_id = winner.id

    # Create comparison record
    comparison = ForecastComparison(
        project_id=project_id,
        comparison_name=comparison_data.comparison_name,
        forecast_ids=comparison_data.forecast_ids,
        comparison_metrics=comparison_metrics,
        winner_forecast_id=winner_id,
        created_by=current_user.id
    )

    db.add(comparison)
    db.commit()
    db.refresh(comparison)

    return ComparisonResponse(
        id=comparison.id,
        project_id=comparison.project_id,
        comparison_name=comparison.comparison_name,
        forecast_ids=comparison.forecast_ids,
        comparison_metrics=comparison.comparison_metrics,
        winner_forecast_id=comparison.winner_forecast_id,
        created_at=comparison.created_at.isoformat()
    )


@router.get("/{project_id}/comparisons", response_model=List[ComparisonResponse])
async def list_comparisons(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all forecast comparisons for a project.
    """
    verify_project_access(project_id, current_user, db)

    comparisons = db.query(ForecastComparison).filter(
        ForecastComparison.project_id == project_id
    ).order_by(ForecastComparison.created_at.desc()).all()

    return [
        ComparisonResponse(
            id=comp.id,
            project_id=comp.project_id,
            comparison_name=comp.comparison_name,
            forecast_ids=comp.forecast_ids,
            comparison_metrics=comp.comparison_metrics,
            winner_forecast_id=comp.winner_forecast_id,
            created_at=comp.created_at.isoformat()
        )
        for comp in comparisons
    ]


@router.get("/{project_id}/comparisons/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison(
    project_id: int,
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific comparison with detailed results.
    """
    verify_project_access(project_id, current_user, db)

    comparison = db.query(ForecastComparison).filter(
        ForecastComparison.id == comparison_id,
        ForecastComparison.project_id == project_id
    ).first()

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison not found"
        )

    return ComparisonResponse(
        id=comparison.id,
        project_id=comparison.project_id,
        comparison_name=comparison.comparison_name,
        forecast_ids=comparison.forecast_ids,
        comparison_metrics=comparison.comparison_metrics,
        winner_forecast_id=comparison.winner_forecast_id,
        created_at=comparison.created_at.isoformat()
    )


@router.delete("/{project_id}/comparisons/{comparison_id}")
async def delete_comparison(
    project_id: int,
    comparison_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a forecast comparison.
    """
    verify_project_access(project_id, current_user, db)

    comparison = db.query(ForecastComparison).filter(
        ForecastComparison.id == comparison_id,
        ForecastComparison.project_id == project_id
    ).first()

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison not found"
        )

    db.delete(comparison)
    db.commit()

    return {"message": "Comparison deleted successfully"}


# ============= Helper Functions =============

def _calculate_comparison_metrics(forecasts: List[Forecast]) -> Dict[str, Any]:
    """
    Calculate statistical comparison metrics between forecasts.
    """
    metrics = {
        "forecast_count": len(forecasts),
        "forecasts": []
    }

    # Collect metrics for each forecast
    for forecast in forecasts:
        forecast_metrics = {
            "id": forecast.id,
            "model": forecast.model_used,
            "ensemble_models": forecast.ensemble_models,
            "horizon": forecast.forecast_horizon,
            "mape": forecast.mape,
            "rmse": forecast.rmse,
            "mae": forecast.mae,
            "confidence_score": forecast.confidence_score,
            "fva": forecast.forecast_value_added,
        }
        metrics["forecasts"].append(forecast_metrics)

    # Calculate statistics across forecasts
    mapes = [f.mape for f in forecasts if f.mape is not None]
    rmses = [f.rmse for f in forecasts if f.rmse is not None]
    maes = [f.mae for f in forecasts if f.mae is not None]

    if mapes:
        metrics["mape_stats"] = {
            "min": float(np.min(mapes)),
            "max": float(np.max(mapes)),
            "mean": float(np.mean(mapes)),
            "std": float(np.std(mapes))
        }

    if rmses:
        metrics["rmse_stats"] = {
            "min": float(np.min(rmses)),
            "max": float(np.max(rmses)),
            "mean": float(np.mean(rmses)),
            "std": float(np.std(rmses))
        }

    if maes:
        metrics["mae_stats"] = {
            "min": float(np.min(maes)),
            "max": float(np.max(maes)),
            "mean": float(np.mean(maes)),
            "std": float(np.std(maes))
        }

    return metrics
