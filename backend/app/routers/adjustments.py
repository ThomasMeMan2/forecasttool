"""
Forecast adjustments endpoints (Phase 2)
Allows manual adjustments to forecast values with audit trail
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Forecast, ForecastAdjustment
from app.schemas import (
    ForecastAdjustmentCreate,
    ForecastAdjustmentResponse,
    MessageResponse,
)

router = APIRouter()


@router.post(
    "/{project_id}/adjustments",
    response_model=ForecastAdjustmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_adjustment(
    project_id: int,
    adjustment: ForecastAdjustmentCreate,
    db: Session = Depends(get_db),
):
    """
    Create a manual adjustment to a forecast value.
    Adjustments are tracked with reasoning for audit purposes.
    """
    # Verify forecast exists
    forecast = (
        db.query(Forecast)
        .filter(
            Forecast.id == adjustment.forecast_id, Forecast.project_id == project_id
        )
        .first()
    )
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    # Create adjustment
    db_adjustment = ForecastAdjustment(
        forecast_id=adjustment.forecast_id,
        period_timestamp=adjustment.period_timestamp,
        original_value=adjustment.original_value,
        adjusted_value=adjustment.adjusted_value,
        adjustment_reason=adjustment.adjustment_reason,
        created_by=1,  # TODO: Use authenticated user
    )

    db.add(db_adjustment)
    db.commit()
    db.refresh(db_adjustment)

    return db_adjustment


@router.get(
    "/{project_id}/forecasts/{forecast_id}/adjustments",
    response_model=List[ForecastAdjustmentResponse],
)
async def list_adjustments(
    project_id: int, forecast_id: int, db: Session = Depends(get_db)
):
    """List all adjustments for a specific forecast"""
    # Verify forecast exists
    forecast = (
        db.query(Forecast)
        .filter(Forecast.id == forecast_id, Forecast.project_id == project_id)
        .first()
    )
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Forecast not found"
        )

    adjustments = (
        db.query(ForecastAdjustment)
        .filter(ForecastAdjustment.forecast_id == forecast_id)
        .order_by(ForecastAdjustment.period_timestamp)
        .all()
    )

    return adjustments


@router.delete(
    "/{project_id}/adjustments/{adjustment_id}", response_model=MessageResponse
)
async def delete_adjustment(
    project_id: int, adjustment_id: int, db: Session = Depends(get_db)
):
    """Delete an adjustment (revert to original forecast)"""
    db_adjustment = (
        db.query(ForecastAdjustment).filter(ForecastAdjustment.id == adjustment_id).first()
    )

    if not db_adjustment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Adjustment not found"
        )

    # Verify it belongs to the project
    forecast = db.query(Forecast).filter(Forecast.id == db_adjustment.forecast_id).first()
    if not forecast or forecast.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Adjustment not found"
        )

    db.delete(db_adjustment)
    db.commit()

    return MessageResponse(
        message="Adjustment deleted successfully", detail={"adjustment_id": adjustment_id}
    )
