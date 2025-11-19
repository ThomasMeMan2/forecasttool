"""
Project management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Project, ProjectDataset, TimeSeries, Forecast
from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectWithStats,
    MessageResponse,
)

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new forecast project.

    For MVP, we're not implementing full authentication yet.
    In production, this would use the authenticated user's ID.
    """
    # For MVP: use dummy user_id = 1
    # In production: user_id = current_user.id
    db_project = Project(user_id=1, name=project.name, description=project.description)

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project


@router.get("/", response_model=List[ProjectWithStats])
async def list_projects(
    include_archived: bool = False, db: Session = Depends(get_db)
):
    """
    List all projects with statistics.

    Args:
        include_archived: Include archived projects in the list
    """
    query = db.query(Project)

    if not include_archived:
        query = query.filter(Project.is_archived == False)

    projects = query.order_by(Project.updated_at.desc()).all()

    # Enrich with statistics
    result = []
    for project in projects:
        dataset_count = (
            db.query(ProjectDataset)
            .filter(ProjectDataset.project_id == project.id)
            .count()
        )
        timeseries_count = (
            db.query(TimeSeries).filter(TimeSeries.project_id == project.id).count()
        )
        forecast_count = (
            db.query(Forecast).filter(Forecast.project_id == project.id).count()
        )

        project_dict = {
            "id": project.id,
            "user_id": project.user_id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "is_archived": project.is_archived,
            "dataset_count": dataset_count,
            "timeseries_count": timeseries_count,
            "forecast_count": forecast_count,
        }
        result.append(project_dict)

    return result


@router.get("/{project_id}", response_model=ProjectWithStats)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project by ID with statistics"""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Get statistics
    dataset_count = (
        db.query(ProjectDataset)
        .filter(ProjectDataset.project_id == project.id)
        .count()
    )
    timeseries_count = (
        db.query(TimeSeries).filter(TimeSeries.project_id == project.id).count()
    )
    forecast_count = (
        db.query(Forecast).filter(Forecast.project_id == project.id).count()
    )

    return {
        "id": project.id,
        "user_id": project.user_id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "is_archived": project.is_archived,
        "dataset_count": dataset_count,
        "timeseries_count": timeseries_count,
        "forecast_count": forecast_count,
    }


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db)
):
    """Update a project's details"""
    db_project = db.query(Project).filter(Project.id == project_id).first()

    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Update fields if provided
    if project_update.name is not None:
        db_project.name = project_update.name
    if project_update.description is not None:
        db_project.description = project_update.description
    if project_update.is_archived is not None:
        db_project.is_archived = project_update.is_archived

    db.commit()
    db.refresh(db_project)

    return db_project


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project and all associated data"""
    db_project = db.query(Project).filter(Project.id == project_id).first()

    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    db.delete(db_project)
    db.commit()

    return MessageResponse(
        message="Project deleted successfully", detail={"project_id": project_id}
    )


@router.post("/{project_id}/duplicate", response_model=ProjectResponse)
async def duplicate_project(project_id: int, db: Session = Depends(get_db)):
    """
    Duplicate a project (including data and settings, but not forecasts).
    Useful for creating variants or testing different approaches.
    """
    original_project = db.query(Project).filter(Project.id == project_id).first()

    if not original_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Create new project
    new_project = Project(
        user_id=original_project.user_id,
        name=f"{original_project.name} (Copy)",
        description=original_project.description,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # TODO: In future phases, copy datasets and timeseries data
    # For MVP, just create an empty project copy

    return new_project
