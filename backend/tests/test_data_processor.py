"""
Tests for data processing service
"""
import pytest
import polars as pl
import tempfile
import os
from app.services.data_processor import DataProcessor


def test_validate_valid_csv():
    """Test validation of a valid CSV"""
    # Create a temporary CSV file
    csv_content = """id,timestamp,quantity
1,2024-01-01,100
1,2024-01-02,105
2,2024-01-01,200
2,2024-01-02,210
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as tmp_file:
        tmp_file.write(csv_content)
        tmp_file_path = tmp_file.name

    try:
        processor = DataProcessor()
        result = processor.validate_csv(tmp_file_path)

        assert result["is_valid"] is True
        assert result["total_rows"] == 4
        assert result["unique_ids"] == 2
        assert len(result["issues"]) == 0

    finally:
        os.unlink(tmp_file_path)


def test_validate_missing_columns():
    """Test validation with missing required columns"""
    csv_content = """id,timestamp
1,2024-01-01
1,2024-01-02
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as tmp_file:
        tmp_file.write(csv_content)
        tmp_file_path = tmp_file.name

    try:
        processor = DataProcessor()
        result = processor.validate_csv(tmp_file_path)

        assert result["is_valid"] is False
        assert "quantity" in result["issues"][0]

    finally:
        os.unlink(tmp_file_path)


def test_process_data():
    """Test data processing"""
    csv_content = """id,timestamp,quantity
prod_1,2024-01-01,100
prod_1,2024-01-02,105
prod_1,2024-01-03,110
prod_2,2024-01-01,200
prod_2,2024-01-02,210
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as tmp_file:
        tmp_file.write(csv_content)
        tmp_file_path = tmp_file.name

    try:
        processor = DataProcessor()
        result = processor.process_data(tmp_file_path)

        assert result["total_timeseries"] == 2
        assert len(result["timeseries"]) == 2

        # Check first timeseries
        ts1 = next(ts for ts in result["timeseries"] if ts["ts_id"] == "prod_1")
        assert ts1["data_points"] == 3
        assert ts1["frequency"] == "daily"

    finally:
        os.unlink(tmp_file_path)


def test_detect_frequency():
    """Test frequency detection"""
    # Daily data
    daily_df = pl.DataFrame(
        {
            "timestamp": pl.date_range(
                pl.date(2024, 1, 1), pl.date(2024, 1, 10), "1d", eager=True
            )
        }
    )

    processor = DataProcessor()
    freq = processor._detect_frequency(daily_df)
    assert freq == "daily"


def test_calculate_statistics():
    """Test statistical calculations"""
    df = pl.DataFrame({"quantity": [100, 105, 110, 115, 120, 125]})

    processor = DataProcessor()
    stats = processor.calculate_statistics(df)

    assert stats["count"] == 6
    assert stats["mean"] == 112.5
    assert stats["min"] == 100
    assert stats["max"] == 125
