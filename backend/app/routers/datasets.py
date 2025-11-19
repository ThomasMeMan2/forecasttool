"""
Dataset upload and management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import polars as pl
import os
from datetime import datetime
from app.database import get_db
from app.models import Project, ProjectDataset, TimeSeries
from app.schemas import DatasetUploadResponse, DataValidationResult, TimeSeriesResponse
from app.services.data_processor import DataProcessor
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post(
    "/{project_id}/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """
    Upload a CSV dataset to a project.

    Expected CSV format:
    - id | timestamp | quantity
    - id: timeseries identifier (string or int)
    - timestamp: date/datetime in ISO format or common formats
    - quantity: numeric value to forecast

    The endpoint will:
    1. Validate the CSV structure
    2. Detect data quality issues (missing values, duplicates, outliers)
    3. Process and store the data
    4. Create TimeSeries records for each unique ID
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported",
        )

    # Check file size
    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_upload_size} bytes",
        )

    # Save file temporarily
    temp_file_path = os.path.join(
        settings.upload_dir, f"temp_{project_id}_{datetime.now().timestamp()}.csv"
    )
    with open(temp_file_path, "wb") as f:
        f.write(content)

    try:
        # Process the CSV data
        processor = DataProcessor()
        validation_result = processor.validate_csv(temp_file_path)

        if not validation_result["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CSV format: {', '.join(validation_result['issues'])}",
            )

        # Process data and create timeseries records
        processed_data = processor.process_data(temp_file_path)

        # Get next version number for this project
        max_version = (
            db.query(ProjectDataset.version)
            .filter(ProjectDataset.project_id == project_id)
            .order_by(ProjectDataset.version.desc())
            .first()
        )
        next_version = (max_version[0] + 1) if max_version else 1

        # Save dataset permanently
        permanent_file_path = os.path.join(
            settings.upload_dir, f"project_{project_id}_v{next_version}.csv"
        )
        os.rename(temp_file_path, permanent_file_path)

        # Create dataset record
        dataset = ProjectDataset(
            project_id=project_id,
            version=next_version,
            type="history",
            filename=file.filename,
            row_count=validation_result["total_rows"],
            file_path=permanent_file_path,
            has_missing_values=validation_result.get("has_missing_values", False),
            has_duplicates=validation_result.get("has_duplicates", False),
            has_outliers=validation_result.get("has_outliers", False),
            quality_score=validation_result.get("quality_score"),
            quality_issues=validation_result.get("issues", []),
        )

        db.add(dataset)
        db.flush()

        # Create/update TimeSeries records
        for ts_data in processed_data["timeseries"]:
            # Check if timeseries already exists
            existing_ts = (
                db.query(TimeSeries)
                .filter(
                    TimeSeries.project_id == project_id,
                    TimeSeries.ts_id == ts_data["ts_id"],
                )
                .first()
            )

            if existing_ts:
                # Update existing timeseries
                existing_ts.data_start_date = ts_data["data_start_date"]
                existing_ts.data_end_date = ts_data["data_end_date"]
                existing_ts.data_points = ts_data["data_points"]
                existing_ts.frequency = ts_data["frequency"]
                existing_ts.has_seasonality = ts_data.get("has_seasonality")
                existing_ts.has_trend = ts_data.get("has_trend")
                existing_ts.volatility_score = ts_data.get("volatility_score")
                existing_ts.missing_percentage = ts_data.get("missing_percentage", 0.0)
                existing_ts.outlier_count = ts_data.get("outlier_count", 0)
            else:
                # Create new timeseries
                new_ts = TimeSeries(
                    project_id=project_id,
                    ts_id=ts_data["ts_id"],
                    data_start_date=ts_data["data_start_date"],
                    data_end_date=ts_data["data_end_date"],
                    data_points=ts_data["data_points"],
                    frequency=ts_data["frequency"],
                    has_seasonality=ts_data.get("has_seasonality"),
                    has_trend=ts_data.get("has_trend"),
                    volatility_score=ts_data.get("volatility_score"),
                    missing_percentage=ts_data.get("missing_percentage", 0.0),
                    outlier_count=ts_data.get("outlier_count", 0),
                )
                db.add(new_ts)

        db.commit()
        db.refresh(dataset)

        return dataset

    except Exception as e:
        # Clean up temp file if it still exists
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}",
        )


@router.get("/{project_id}/datasets", response_model=List[DatasetUploadResponse])
async def list_datasets(project_id: int, db: Session = Depends(get_db)):
    """List all datasets for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    datasets = (
        db.query(ProjectDataset)
        .filter(ProjectDataset.project_id == project_id)
        .order_by(ProjectDataset.version.desc())
        .all()
    )

    return datasets


@router.get("/{project_id}/timeseries", response_model=List[TimeSeriesResponse])
async def list_timeseries(project_id: int, db: Session = Depends(get_db)):
    """List all timeseries in a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    timeseries = (
        db.query(TimeSeries)
        .filter(TimeSeries.project_id == project_id)
        .order_by(TimeSeries.ts_id)
        .all()
    )

    return timeseries


@router.get(
    "/{project_id}/timeseries/{ts_id}/data", response_model=DataValidationResult
)
async def get_timeseries_data(
    project_id: int, ts_id: str, db: Session = Depends(get_db)
):
    """
    Get the raw data for a specific timeseries.
    Returns the data points and statistics.
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
            status_code=status.HTTP_404_NOT_FOUND, detail="No dataset found for project"
        )

    # Read and filter data for specific ts_id
    try:
        df = pl.read_csv(latest_dataset.file_path)
        ts_data = df.filter(pl.col("id") == ts_id)

        if ts_data.height == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Timeseries {ts_id} not found",
            )

        # Calculate statistics
        processor = DataProcessor()
        stats = processor.calculate_statistics(ts_data)

        return DataValidationResult(
            is_valid=True,
            total_rows=ts_data.height,
            unique_ids=1,
            date_range={
                "start": str(ts_data["timestamp"].min()),
                "end": str(ts_data["timestamp"].max()),
            },
            issues=[],
            warnings=[],
            statistics=stats,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading data: {str(e)}",
        )
