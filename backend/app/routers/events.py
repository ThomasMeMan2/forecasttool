"""
Events management endpoints (Phase 2)
Handles global events and ID-specific events
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Project, TimeSeries, GlobalEvent, IDSpecificEvent
from app.schemas import (
    GlobalEventCreate,
    GlobalEventResponse,
    GlobalEventUpdate,
    IDSpecificEventCreate,
    IDSpecificEventResponse,
    IDSpecificEventUpdate,
    MessageResponse,
)

router = APIRouter()


# ============= Global Events =============


@router.post(
    "/{project_id}/global-events",
    response_model=GlobalEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_global_event(
    project_id: int,
    event: GlobalEventCreate,
    db: Session = Depends(get_db),
):
    """
    Create a global event that affects all timeseries in the project.

    Examples: holidays, marketing campaigns, price changes, economic events
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Create event
    db_event = GlobalEvent(
        project_id=project_id,
        event_name=event.event_name,
        event_date=event.event_date,
        event_type=event.event_type,
        impact_value=event.impact_value,
        description=event.description,
        created_by=1,  # TODO: Use authenticated user ID
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


@router.get("/{project_id}/global-events", response_model=List[GlobalEventResponse])
async def list_global_events(
    project_id: int,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all global events for a project, optionally filtered by type"""
    query = db.query(GlobalEvent).filter(GlobalEvent.project_id == project_id)

    if event_type:
        query = query.filter(GlobalEvent.event_type == event_type)

    events = query.order_by(GlobalEvent.event_date.desc()).all()
    return events


@router.get(
    "/{project_id}/global-events/{event_id}", response_model=GlobalEventResponse
)
async def get_global_event(
    project_id: int, event_id: int, db: Session = Depends(get_db)
):
    """Get a specific global event"""
    event = (
        db.query(GlobalEvent)
        .filter(GlobalEvent.id == event_id, GlobalEvent.project_id == project_id)
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    return event


@router.put(
    "/{project_id}/global-events/{event_id}", response_model=GlobalEventResponse
)
async def update_global_event(
    project_id: int,
    event_id: int,
    event_update: GlobalEventUpdate,
    db: Session = Depends(get_db),
):
    """Update a global event"""
    db_event = (
        db.query(GlobalEvent)
        .filter(GlobalEvent.id == event_id, GlobalEvent.project_id == project_id)
        .first()
    )

    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    # Update fields
    if event_update.event_name is not None:
        db_event.event_name = event_update.event_name
    if event_update.event_date is not None:
        db_event.event_date = event_update.event_date
    if event_update.event_type is not None:
        db_event.event_type = event_update.event_type
    if event_update.impact_value is not None:
        db_event.impact_value = event_update.impact_value
    if event_update.description is not None:
        db_event.description = event_update.description

    db.commit()
    db.refresh(db_event)

    return db_event


@router.delete("/{project_id}/global-events/{event_id}", response_model=MessageResponse)
async def delete_global_event(
    project_id: int, event_id: int, db: Session = Depends(get_db)
):
    """Delete a global event"""
    db_event = (
        db.query(GlobalEvent)
        .filter(GlobalEvent.id == event_id, GlobalEvent.project_id == project_id)
        .first()
    )

    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    db.delete(db_event)
    db.commit()

    return MessageResponse(
        message="Global event deleted successfully", detail={"event_id": event_id}
    )


# ============= ID-Specific Events =============


@router.post(
    "/{project_id}/id-events",
    response_model=IDSpecificEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_id_specific_event(
    project_id: int,
    event: IDSpecificEventCreate,
    db: Session = Depends(get_db),
):
    """
    Create an event that affects a specific timeseries.

    Examples: stockout, store closure, product promotion, equipment failure
    """
    # Verify project and timeseries exist
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    timeseries = (
        db.query(TimeSeries)
        .filter(
            TimeSeries.id == event.timeseries_id,
            TimeSeries.project_id == project_id,
        )
        .first()
    )
    if not timeseries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Timeseries not found"
        )

    # Create event
    db_event = IDSpecificEvent(
        project_id=project_id,
        timeseries_id=event.timeseries_id,
        event_name=event.event_name,
        event_date=event.event_date,
        event_type=event.event_type,
        impact_value=event.impact_value,
        description=event.description,
        created_by=1,  # TODO: Use authenticated user ID
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


@router.get(
    "/{project_id}/id-events", response_model=List[IDSpecificEventResponse]
)
async def list_id_specific_events(
    project_id: int,
    timeseries_id: Optional[int] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List ID-specific events, optionally filtered by timeseries or type"""
    query = db.query(IDSpecificEvent).filter(
        IDSpecificEvent.project_id == project_id
    )

    if timeseries_id:
        query = query.filter(IDSpecificEvent.timeseries_id == timeseries_id)
    if event_type:
        query = query.filter(IDSpecificEvent.event_type == event_type)

    events = query.order_by(IDSpecificEvent.event_date.desc()).all()
    return events


@router.get(
    "/{project_id}/id-events/{event_id}", response_model=IDSpecificEventResponse
)
async def get_id_specific_event(
    project_id: int, event_id: int, db: Session = Depends(get_db)
):
    """Get a specific ID-specific event"""
    event = (
        db.query(IDSpecificEvent)
        .filter(
            IDSpecificEvent.id == event_id, IDSpecificEvent.project_id == project_id
        )
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    return event


@router.put(
    "/{project_id}/id-events/{event_id}", response_model=IDSpecificEventResponse
)
async def update_id_specific_event(
    project_id: int,
    event_id: int,
    event_update: IDSpecificEventUpdate,
    db: Session = Depends(get_db),
):
    """Update an ID-specific event"""
    db_event = (
        db.query(IDSpecificEvent)
        .filter(
            IDSpecificEvent.id == event_id, IDSpecificEvent.project_id == project_id
        )
        .first()
    )

    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    # Update fields
    if event_update.event_name is not None:
        db_event.event_name = event_update.event_name
    if event_update.event_date is not None:
        db_event.event_date = event_update.event_date
    if event_update.event_type is not None:
        db_event.event_type = event_update.event_type
    if event_update.impact_value is not None:
        db_event.impact_value = event_update.impact_value
    if event_update.description is not None:
        db_event.description = event_update.description

    db.commit()
    db.refresh(db_event)

    return db_event


@router.delete("/{project_id}/id-events/{event_id}", response_model=MessageResponse)
async def delete_id_specific_event(
    project_id: int, event_id: int, db: Session = Depends(get_db)
):
    """Delete an ID-specific event"""
    db_event = (
        db.query(IDSpecificEvent)
        .filter(
            IDSpecificEvent.id == event_id, IDSpecificEvent.project_id == project_id
        )
        .first()
    )

    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    db.delete(db_event)
    db.commit()

    return MessageResponse(
        message="ID-specific event deleted successfully", detail={"event_id": event_id}
    )
