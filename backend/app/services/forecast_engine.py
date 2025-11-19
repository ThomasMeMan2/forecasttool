"""
Forecasting engine using StatsForecast
"""
import polars as pl
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, AutoETS, SeasonalNaive
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np


class ForecastEngine:
    """
    Automated forecasting engine using StatsForecast.

    For Phase 1 MVP:
    - Uses AutoARIMA as primary model
    - Includes SeasonalNaive as benchmark
    - Generates prediction intervals (80%, 90%)
    - Calculates accuracy metrics
    """

    def __init__(self):
        self.models_config = {
            "AutoARIMA": AutoARIMA(season_length=1),  # Will auto-detect seasonality
            "SeasonalNaive": SeasonalNaive(season_length=7),  # Weekly baseline
        }

    def generate_forecast(
        self,
        data: pl.DataFrame,
        ts_id: str,
        horizon: int = 12,
        confidence_levels: List[int] = [80, 90],
    ) -> Dict[str, Any]:
        """
        Generate forecast for a single timeseries.

        Args:
            data: Polars DataFrame with columns [id, timestamp, quantity]
            ts_id: Timeseries identifier
            horizon: Forecast horizon (number of periods)
            confidence_levels: List of confidence levels for prediction intervals

        Returns:
            Dict with forecast results, metrics, and metadata
        """
        try:
            # Filter data for specific ts_id
            ts_data = data.filter(pl.col("id") == ts_id).sort("timestamp")

            if ts_data.height < 10:
                return {
                    "success": False,
                    "error": "Insufficient data points (minimum 10 required)",
                    "ts_id": ts_id,
                }

            # Prepare data for StatsForecast
            # StatsForecast expects: unique_id, ds (timestamp), y (target)
            sf_data = ts_data.select(
                [
                    pl.lit(ts_id).alias("unique_id"),
                    pl.col("timestamp").alias("ds"),
                    pl.col("quantity").alias("y"),
                ]
            ).to_pandas()

            # Remove any missing values
            sf_data = sf_data.dropna()

            if len(sf_data) < 10:
                return {
                    "success": False,
                    "error": "Insufficient non-missing data points",
                    "ts_id": ts_id,
                }

            # Detect frequency
            frequency = self._detect_frequency_code(sf_data)

            # Initialize StatsForecast
            sf = StatsForecast(
                models=[AutoARIMA(season_length=self._get_season_length(frequency))],
                freq=frequency,
                n_jobs=1,
            )

            # Generate forecast
            forecast_df = sf.forecast(df=sf_data, h=horizon, level=confidence_levels)

            # Calculate accuracy metrics using historical data (if enough data)
            metrics = self._calculate_metrics(sf_data, sf, horizon)

            # Format forecast results
            forecast_points = self._format_forecast_points(
                forecast_df, confidence_levels
            )

            # Determine if manual review is needed
            requires_review = self._check_review_needed(sf_data, metrics)

            # Generate anomaly flags
            anomaly_flags = self._detect_anomalies(sf_data, forecast_points)

            return {
                "success": True,
                "ts_id": ts_id,
                "model_used": "AutoARIMA",
                "forecast_horizon": horizon,
                "confidence_levels": confidence_levels,
                "forecast_points": forecast_points,
                "metrics": metrics,
                "requires_manual_review": requires_review,
                "anomaly_flags": anomaly_flags,
                "confidence_score": self._calculate_confidence_score(metrics, sf_data),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Forecasting error: {str(e)}",
                "ts_id": ts_id,
            }

    def generate_multiple_forecasts(
        self, data: pl.DataFrame, ts_ids: List[str], horizon: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Generate forecasts for multiple timeseries.

        Args:
            data: Full dataset with multiple timeseries
            ts_ids: List of timeseries identifiers to forecast
            horizon: Forecast horizon

        Returns:
            List of forecast results
        """
        results = []

        for ts_id in ts_ids:
            forecast_result = self.generate_forecast(data, ts_id, horizon)
            results.append(forecast_result)

        return results

    def _detect_frequency_code(self, df: pd.DataFrame) -> str:
        """
        Detect frequency code for StatsForecast.

        Returns:
            Frequency string: 'D' (daily), 'W' (weekly), 'M' (monthly), 'Q' (quarterly)
        """
        if len(df) < 2:
            return "D"  # Default to daily

        # Calculate median difference between timestamps
        df_sorted = df.sort_values("ds")
        diffs = df_sorted["ds"].diff().dt.days.median()

        if 0.8 <= diffs <= 1.5:
            return "D"  # Daily
        elif 6 <= diffs <= 8:
            return "W"  # Weekly
        elif 28 <= diffs <= 32:
            return "MS"  # Monthly
        elif 88 <= diffs <= 95:
            return "QS"  # Quarterly
        else:
            return "D"  # Default to daily

    def _get_season_length(self, frequency: str) -> int:
        """Get appropriate season length based on frequency"""
        season_map = {"D": 7, "W": 52, "MS": 12, "QS": 4}
        return season_map.get(frequency, 1)

    def _format_forecast_points(
        self, forecast_df: pd.DataFrame, confidence_levels: List[int]
    ) -> List[Dict[str, Any]]:
        """Format forecast dataframe into list of points with intervals"""
        forecast_points = []

        for idx, row in forecast_df.iterrows():
            point = {
                "timestamp": row.name[1].isoformat()
                if hasattr(row.name[1], "isoformat")
                else str(row.name[1]),
                "mean": float(row["AutoARIMA"]),
            }

            # Add confidence intervals
            for level in confidence_levels:
                point[f"lower_{level}"] = float(row[f"AutoARIMA-lo-{level}"])
                point[f"upper_{level}"] = float(row[f"AutoARIMA-hi-{level}"])

            forecast_points.append(point)

        return forecast_points

    def _calculate_metrics(
        self, historical_data: pd.DataFrame, model: StatsForecast, horizon: int
    ) -> Dict[str, float]:
        """
        Calculate accuracy metrics using time-series cross-validation.

        For MVP, we'll use a simple train-test split.
        """
        try:
            # Only calculate if we have enough data
            if len(historical_data) < horizon + 20:
                return {"mape": None, "rmse": None, "mae": None}

            # Split data: use last 'horizon' points as test set
            train_data = historical_data.iloc[:-horizon].copy()
            test_data = historical_data.iloc[-horizon:].copy()

            # Generate forecast on training data
            forecast = model.forecast(df=train_data, h=horizon)

            # Get actual values
            actual = test_data["y"].values

            # Get predicted values
            predicted = forecast["AutoARIMA"].values[: len(actual)]

            # Calculate metrics
            mape = np.mean(np.abs((actual - predicted) / actual)) * 100
            rmse = np.sqrt(np.mean((actual - predicted) ** 2))
            mae = np.mean(np.abs(actual - predicted))

            return {"mape": float(mape), "rmse": float(rmse), "mae": float(mae)}

        except Exception as e:
            return {"mape": None, "rmse": None, "mae": None, "error": str(e)}

    def _calculate_confidence_score(
        self, metrics: Dict[str, float], data: pd.DataFrame
    ) -> float:
        """
        Calculate overall confidence score (0-100).

        Based on:
        - Data quality (length, missing values)
        - Model accuracy metrics
        - Data stability
        """
        score = 100.0

        # Data length penalty
        if len(data) < 30:
            score -= 20
        elif len(data) < 60:
            score -= 10

        # MAPE penalty
        if metrics.get("mape"):
            mape = metrics["mape"]
            if mape > 50:
                score -= 30
            elif mape > 30:
                score -= 20
            elif mape > 15:
                score -= 10

        # Volatility penalty
        cv = data["y"].std() / data["y"].mean() if data["y"].mean() != 0 else 0
        if cv > 1.0:
            score -= 15
        elif cv > 0.5:
            score -= 5

        return max(0, min(100, score))

    def _check_review_needed(
        self, data: pd.DataFrame, metrics: Dict[str, float]
    ) -> bool:
        """
        Determine if forecast requires manual review.

        Review needed if:
        - Insufficient data
        - High error metrics
        - High volatility
        """
        # Insufficient data
        if len(data) < 20:
            return True

        # High MAPE
        if metrics.get("mape") and metrics["mape"] > 30:
            return True

        # High volatility
        cv = data["y"].std() / data["y"].mean() if data["y"].mean() != 0 else 0
        if cv > 0.8:
            return True

        return False

    def _detect_anomalies(
        self, data: pd.DataFrame, forecast_points: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Detect potential anomalies or issues with the forecast.

        Returns list of flag strings.
        """
        flags = []

        # Check for extreme forecast values compared to historical data
        historical_max = data["y"].max()
        historical_min = data["y"].min()
        historical_mean = data["y"].mean()

        for point in forecast_points:
            mean_forecast = point["mean"]

            # Check if forecast is far outside historical range
            if mean_forecast > historical_max * 1.5:
                flags.append("extreme_high_forecast")
                break
            elif mean_forecast < historical_min * 0.5:
                flags.append("extreme_low_forecast")
                break

        # Check for sudden trend change
        if len(forecast_points) > 2:
            recent_mean = data["y"].tail(10).mean()
            forecast_mean = np.mean([p["mean"] for p in forecast_points[:5]])

            change_pct = abs(forecast_mean - recent_mean) / recent_mean * 100
            if change_pct > 50:
                flags.append("sudden_trend_change")

        # Check data quality
        if len(data) < 30:
            flags.append("limited_historical_data")

        return list(set(flags))  # Remove duplicates
