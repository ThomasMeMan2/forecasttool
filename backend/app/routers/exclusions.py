"""
Manual exclusions endpoints (Phase 2)
Allows users to exclude specific date ranges from forecasting
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Project, TimeSeries, UserExclusion
from app.schemas import (
    UserExclusionCreate,
    UserExclusionResponse,
    UserExclusionUpdate,
    MessageResponse,
)

router = APIRouter()


@router.post(
    "/{project_id}/exclusions",
    response_model=UserExclusionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_exclusion(
    project_id: int,
    exclusion: UserExclusionCreate,
    db: Session = Depends(get_db),
):
    """
    Create a manual exclusion period for a timeseries.
    Excluded periods won't be used in model training.
    """
    # Verify timeseries exists
    timeseries = (
        db.query(TimeSeries)
        .filter(
            TimeSeries.id == exclusion.timeseries_id,
            TimeSeries.project_id == project_id,
        )
        .first()
    )
    if not timeseries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Timeseries not found"
        )

    # Validate dates
    if exclusion.start_date >= exclusion.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date",
        )

    # Create exclusion
    db_exclusion = UserExclusion(
        project_id=project_id,
        timeseries_id=exclusion.timeseries_id,
        start_date=exclusion.start_date,
        end_date=exclusion.end_date,
        reason=exclusion.reason,
        is_active=exclusion.is_active,
        created_by=1,  # TODO: Use authenticated user
    )

    db.add(db_exclusion)
    db.commit()
    db.refresh(db_exclusion)

    return db_exclusion


@router.get("/{project_id}/exclusions", response_model=List[UserExclusionResponse])
async def list_exclusions(
    project_id: int,
    timeseries_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """List exclusions, optionally filtered by timeseries"""
    query = db.query(UserExclusion).filter(UserExclusion.project_id == project_id)

    if timeseries_id:
        query = query.filter(UserExclusion.timeseries_id == timeseries_id)
    if active_only:
        query = query.filter(UserExclusion.is_active == True)

    exclusions = query.order_by(UserExclusion.start_date.desc()).all()
    return exclusions


@router.put(
    "/{project_id}/exclusions/{exclusion_id}", response_model=UserExclusionResponse
)
async def update_exclusion(
    project_id: int,
    exclusion_id: int,
    exclusion_update: UserExclusionUpdate,
    db: Session = Depends(get_db),
):
    """Update an exclusion (e.g., deactivate or modify dates)"""
    db_exclusion = (
        db.query(UserExclusion)
        .filter(
            UserExclusion.id == exclusion_id, UserExclusion.project_id == project_id
        )
        .first()
    )

    if not db_exclusion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exclusion not found"
        )

    # Update fields
    if exclusion_update.start_date is not None:
        db_exclusion.start_date = exclusion_update.start_date
    if exclusion_update.end_date is not None:
        db_exclusion.end_date = exclusion_update.end_date
    if exclusion_update.reason is not None:
        db_exclusion.reason = exclusion_update.reason
    if exclusion_update.is_active is not None:
        db_exclusion.is_active = exclusion_update.is_active

    # Validate dates
    if db_exclusion.start_date >= db_exclusion.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date",
        )

    db.commit()
    db.refresh(db_exclusion)

    return db_exclusion


@router.delete("/{project_id}/exclusions/{exclusion_id}", response_model=MessageResponse)
async def delete_exclusion(
    project_id: int, exclusion_id: int, db: Session = Depends(get_db)
):
    """Delete an exclusion"""
    db_exclusion = (
        db.query(UserExclusion)
        .filter(
            UserExclusion.id == exclusion_id, UserExclusion.project_id == project_id
        )
        .first()
    )

    if not db_exclusion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exclusion not found"
        )

    db.delete(db_exclusion)
    db.commit()

    return MessageResponse(
        message="Exclusion deleted successfully", detail={"exclusion_id": exclusion_id}
    )
