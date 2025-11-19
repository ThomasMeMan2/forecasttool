"""
Data processing and validation service
"""
import polars as pl
from datetime import datetime
from typing import Dict, Any, List
import numpy as np


class DataProcessor:
    """Handles CSV validation, processing, and data quality checks"""

    def validate_csv(self, file_path: str) -> Dict[str, Any]:
        """
        Validate CSV structure and content.

        Expected format: id | timestamp | quantity

        Returns:
            Dict with validation results including is_valid, issues, warnings, etc.
        """
        try:
            # Read CSV
            df = pl.read_csv(file_path)

            issues = []
            warnings = []

            # Check required columns
            required_columns = ["id", "timestamp", "quantity"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                issues.append(
                    f"Missing required columns: {', '.join(missing_columns)}"
                )
                return {
                    "is_valid": False,
                    "issues": issues,
                    "warnings": warnings,
                    "total_rows": 0,
                }

            # Validate data types and content
            total_rows = df.height

            if total_rows == 0:
                issues.append("CSV file is empty")
                return {
                    "is_valid": False,
                    "issues": issues,
                    "warnings": warnings,
                    "total_rows": 0,
                }

            # Parse timestamp column
            try:
                df = df.with_columns(pl.col("timestamp").str.strptime(pl.Datetime, format="%+", strict=False))
            except Exception as e:
                issues.append(f"Invalid timestamp format: {str(e)}")

            # Check for missing values
            missing_ids = df["id"].null_count()
            missing_timestamps = df["timestamp"].null_count()
            missing_quantities = df["quantity"].null_count()

            has_missing_values = (
                missing_ids > 0 or missing_timestamps > 0 or missing_quantities > 0
            )

            if has_missing_values:
                warnings.append(
                    f"Missing values detected: {missing_ids} ids, {missing_timestamps} timestamps, {missing_quantities} quantities"
                )

            # Check for duplicates (same id + timestamp)
            duplicates = df.group_by(["id", "timestamp"]).count()
            duplicate_count = duplicates.filter(pl.col("count") > 1).height
            has_duplicates = duplicate_count > 0

            if has_duplicates:
                warnings.append(f"{duplicate_count} duplicate id-timestamp pairs found")

            # Check for negative quantities
            try:
                negative_count = df.filter(pl.col("quantity") < 0).height
                if negative_count > 0:
                    warnings.append(f"{negative_count} negative quantity values found")
            except Exception:
                pass  # quantity might not be numeric yet

            # Detect outliers using IQR method
            has_outliers = False
            try:
                q1 = df["quantity"].quantile(0.25)
                q3 = df["quantity"].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 3 * iqr
                upper_bound = q3 + 3 * iqr

                outlier_count = df.filter(
                    (pl.col("quantity") < lower_bound)
                    | (pl.col("quantity") > upper_bound)
                ).height

                has_outliers = outlier_count > 0

                if has_outliers:
                    warnings.append(f"{outlier_count} potential outliers detected")
            except Exception:
                pass

            # Calculate quality score (0-100)
            quality_score = 100.0
            if has_missing_values:
                quality_score -= 20
            if has_duplicates:
                quality_score -= 15
            if has_outliers:
                quality_score -= 10
            if len(warnings) > 3:
                quality_score -= 5

            quality_score = max(0, quality_score)

            # Get unique IDs
            unique_ids = df["id"].n_unique()

            return {
                "is_valid": len(issues) == 0,
                "total_rows": total_rows,
                "unique_ids": unique_ids,
                "issues": issues,
                "warnings": warnings,
                "has_missing_values": has_missing_values,
                "has_duplicates": has_duplicates,
                "has_outliers": has_outliers,
                "quality_score": quality_score,
            }

        except Exception as e:
            return {
                "is_valid": False,
                "issues": [f"Error reading CSV: {str(e)}"],
                "warnings": [],
                "total_rows": 0,
            }

    def process_data(self, file_path: str) -> Dict[str, Any]:
        """
        Process CSV data and extract timeseries information.

        Returns:
            Dict with processed timeseries data
        """
        # Read CSV
        df = pl.read_csv(file_path)

        # Parse timestamp
        df = df.with_columns(
            pl.col("timestamp").str.strptime(pl.Datetime, format="%+", strict=False)
        )

        # Sort by id and timestamp
        df = df.sort(["id", "timestamp"])

        # Get unique IDs
        unique_ids = df["id"].unique().to_list()

        # Process each timeseries
        timeseries_data = []

        for ts_id in unique_ids:
            ts_df = df.filter(pl.col("id") == ts_id).sort("timestamp")

            # Calculate basic statistics
            data_start = ts_df["timestamp"].min()
            data_end = ts_df["timestamp"].max()
            data_points = ts_df.height

            # Detect frequency
            frequency = self._detect_frequency(ts_df)

            # Calculate volatility (coefficient of variation)
            mean_val = ts_df["quantity"].mean()
            std_val = ts_df["quantity"].std()
            volatility_score = (
                (std_val / mean_val * 100) if mean_val and mean_val != 0 else 0
            )

            # Count missing values and outliers for this timeseries
            missing_count = ts_df["quantity"].null_count()
            missing_percentage = (missing_count / data_points * 100) if data_points > 0 else 0

            # Simple outlier detection
            q1 = ts_df["quantity"].quantile(0.25)
            q3 = ts_df["quantity"].quantile(0.75)
            iqr = q3 - q1
            outlier_count = ts_df.filter(
                (pl.col("quantity") < q1 - 3 * iqr)
                | (pl.col("quantity") > q3 + 3 * iqr)
            ).height

            timeseries_data.append(
                {
                    "ts_id": str(ts_id),
                    "data_start_date": data_start,
                    "data_end_date": data_end,
                    "data_points": data_points,
                    "frequency": frequency,
                    "volatility_score": min(100, volatility_score),
                    "missing_percentage": missing_percentage,
                    "outlier_count": outlier_count,
                    # Seasonality and trend detection would be done during forecasting
                    "has_seasonality": None,
                    "has_trend": None,
                }
            )

        return {"timeseries": timeseries_data, "total_timeseries": len(timeseries_data)}

    def _detect_frequency(self, df: pl.DataFrame) -> str:
        """
        Detect the frequency of timeseries data.

        Returns:
            'daily', 'weekly', 'monthly', or 'irregular'
        """
        if df.height < 2:
            return "unknown"

        # Calculate differences between consecutive timestamps
        df_sorted = df.sort("timestamp")
        timestamps = df_sorted["timestamp"].to_list()

        diffs = [(timestamps[i + 1] - timestamps[i]).days for i in range(len(timestamps) - 1)]

        if not diffs:
            return "unknown"

        # Calculate median difference
        median_diff = np.median(diffs)

        # Classify based on median difference
        if 0.8 <= median_diff <= 1.2:
            return "daily"
        elif 6 <= median_diff <= 8:
            return "weekly"
        elif 28 <= median_diff <= 32:
            return "monthly"
        elif 88 <= median_diff <= 95:
            return "quarterly"
        else:
            return "irregular"

    def calculate_statistics(self, df: pl.DataFrame) -> Dict[str, Any]:
        """Calculate statistical properties of a timeseries"""
        try:
            quantity_col = df["quantity"]

            stats = {
                "count": df.height,
                "mean": quantity_col.mean(),
                "median": quantity_col.median(),
                "std": quantity_col.std(),
                "min": quantity_col.min(),
                "max": quantity_col.max(),
                "q1": quantity_col.quantile(0.25),
                "q3": quantity_col.quantile(0.75),
            }

            # Convert to Python native types
            return {k: float(v) if v is not None else None for k, v in stats.items()}

        except Exception as e:
            return {"error": str(e)}
