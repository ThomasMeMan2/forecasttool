"""
Enhanced Forecasting Engine with Ensemble Support (Phase 2)
Supports multiple models, ensemble forecasting, and benchmarks
"""
import polars as pl
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, AutoETS, SeasonalNaive, Naive, SeasonalWindowAverage
from prophet import Prophet
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import logging

logger = logging.getLogger(__name__)


class EnhancedForecastEngine:
    """
    Enhanced forecasting engine with ensemble support.

    Features:
    - Multiple models: AutoARIMA, AutoETS, Prophet, SeasonalNaive
    - Ensemble forecasting with weighted averaging
    - Benchmark comparisons (Seasonal Naive, SMA)
    - Forecast Value Added (FVA) calculation
    - Event support (holidays, custom regressors)
    """

    def __init__(self):
        self.available_models = {
            "AutoARIMA": "Automatic ARIMA with parameter selection",
            "AutoETS": "Automatic Exponential Smoothing",
            "Prophet": "Facebook Prophet (for strong seasonality)",
            "SeasonalNaive": "Seasonal Naive (benchmark)",
            "SeasonalWindowAverage": "Seasonal Moving Average",
        }

    def generate_ensemble_forecast(
        self,
        data: pl.DataFrame,
        ts_id: str,
        horizon: int = 12,
        confidence_levels: List[int] = [80, 90],
        models: Optional[List[str]] = None,
        events: Optional[pd.DataFrame] = None,
        exclusions: Optional[List[Tuple[datetime, datetime]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate ensemble forecast using multiple models.

        Args:
            data: Polars DataFrame with columns [id, timestamp, quantity]
            ts_id: Timeseries identifier
            horizon: Forecast horizon
            confidence_levels: List of confidence levels
            models: List of model names to use (default: ['AutoARIMA', 'AutoETS'])
            events: Optional DataFrame with events as regressors
            exclusions: Optional list of (start_date, end_date) tuples to exclude

        Returns:
            Dict with ensemble forecast results
        """
        try:
            # Default models for ensemble
            if models is None:
                models = ["AutoARIMA", "AutoETS"]

            # Filter and prepare data
            ts_data = data.filter(pl.col("id") == ts_id).sort("timestamp")

            if ts_data.height < 10:
                return {
                    "success": False,
                    "error": "Insufficient data points (minimum 10 required)",
                    "ts_id": ts_id,
                }

            # Apply exclusions if provided
            if exclusions:
                ts_data = self._apply_exclusions(ts_data, exclusions)

            # Prepare data
            sf_data = ts_data.select(
                [
                    pl.lit(ts_id).alias("unique_id"),
                    pl.col("timestamp").alias("ds"),
                    pl.col("quantity").alias("y"),
                ]
            ).to_pandas()

            sf_data = sf_data.dropna()

            if len(sf_data) < 10:
                return {
                    "success": False,
                    "error": "Insufficient non-missing data points",
                    "ts_id": ts_id,
                }

            # Detect frequency
            frequency = self._detect_frequency_code(sf_data)
            season_length = self._get_season_length(frequency)

            # Generate individual forecasts
            model_forecasts = {}
            model_metrics = {}

            for model_name in models:
                try:
                    forecast, metrics = self._generate_single_forecast(
                        sf_data,
                        model_name,
                        horizon,
                        frequency,
                        season_length,
                        confidence_levels,
                        events,
                    )
                    model_forecasts[model_name] = forecast
                    model_metrics[model_name] = metrics
                except Exception as e:
                    logger.warning(f"Model {model_name} failed: {str(e)}")
                    continue

            if not model_forecasts:
                return {
                    "success": False,
                    "error": "All models failed to generate forecasts",
                    "ts_id": ts_id,
                }

            # Calculate ensemble weights based on historical accuracy
            weights = self._calculate_ensemble_weights(model_metrics)

            # Combine forecasts using weighted average
            ensemble_forecast = self._combine_forecasts(
                model_forecasts, weights, confidence_levels
            )

            # Generate benchmark forecast
            benchmark_forecast = self._generate_benchmark(
                sf_data, horizon, frequency, season_length
            )

            # Calculate Forecast Value Added (FVA)
            fva = self._calculate_fva(ensemble_forecast, benchmark_forecast, sf_data)

            # Format results
            forecast_points = self._format_forecast_points(
                ensemble_forecast, confidence_levels
            )

            # Overall metrics (weighted average of individual metrics)
            avg_metrics = self._aggregate_metrics(model_metrics, weights)

            # Determine if manual review is needed
            requires_review = self._check_review_needed(sf_data, avg_metrics, fva)

            # Generate anomaly flags
            anomaly_flags = self._detect_anomalies(sf_data, forecast_points, fva)

            return {
                "success": True,
                "ts_id": ts_id,
                "model_used": "Ensemble",
                "ensemble_models": list(model_forecasts.keys()),
                "ensemble_weights": weights,
                "forecast_horizon": horizon,
                "confidence_levels": confidence_levels,
                "forecast_points": forecast_points,
                "benchmark_model": "SeasonalNaive",
                "benchmark_forecast": self._format_benchmark(benchmark_forecast),
                "forecast_value_added": fva,
                "metrics": avg_metrics,
                "individual_model_metrics": model_metrics,
                "requires_manual_review": requires_review,
                "anomaly_flags": anomaly_flags,
                "confidence_score": self._calculate_confidence_score(
                    avg_metrics, sf_data, fva
                ),
            }

        except Exception as e:
            logger.error(f"Ensemble forecasting error: {str(e)}")
            return {
                "success": False,
                "error": f"Forecasting error: {str(e)}",
                "ts_id": ts_id,
            }

    def _apply_exclusions(
        self, data: pl.DataFrame, exclusions: List[Tuple[datetime, datetime]]
    ) -> pl.DataFrame:
        """Remove excluded periods from data"""
        for start_date, end_date in exclusions:
            data = data.filter(
                (pl.col("timestamp") < start_date) | (pl.col("timestamp") > end_date)
            )
        return data

    def _generate_single_forecast(
        self,
        data: pd.DataFrame,
        model_name: str,
        horizon: int,
        frequency: str,
        season_length: int,
        confidence_levels: List[int],
        events: Optional[pd.DataFrame] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, float]]:
        """Generate forecast using a single model"""

        if model_name == "Prophet":
            return self._prophet_forecast(
                data, horizon, confidence_levels, events
            )
        else:
            # StatsForecast models
            model_map = {
                "AutoARIMA": AutoARIMA(season_length=season_length),
                "AutoETS": AutoETS(season_length=season_length),
                "SeasonalNaive": SeasonalNaive(season_length=season_length),
                "SeasonalWindowAverage": SeasonalWindowAverage(
                    season_length=season_length, window_size=2
                ),
            }

            model = model_map.get(model_name)
            if not model:
                raise ValueError(f"Unknown model: {model_name}")

            sf = StatsForecast(models=[model], freq=frequency, n_jobs=1)

            forecast_df = sf.forecast(df=data, h=horizon, level=confidence_levels)

            # Calculate metrics
            metrics = self._calculate_metrics(data, sf, horizon, model_name)

            return forecast_df, metrics

    def _prepare_event_regressors(
        self,
        data: pd.DataFrame,
        events: pd.DataFrame,
        horizon: int,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare event regressors for Prophet.

        Creates binary indicator columns for each event type.
        Returns data with regressor columns and future dataframe with same columns.
        """
        # Create a copy of data
        data_with_events = data.copy()

        # Get date range for future predictions
        last_date = pd.to_datetime(data["ds"].max())
        freq = pd.infer_freq(data["ds"])
        if freq is None:
            freq = "D"  # Default to daily

        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(1, unit=freq[0]),
            periods=horizon,
            freq=freq
        )
        future_df = pd.DataFrame({"ds": future_dates})

        # Process each event
        for _, event in events.iterrows():
            event_date = pd.to_datetime(event["event_date"])
            event_type = event.get("event_type", "custom")
            regressor_name = f"event_{event_type}"

            # Add binary indicator for the event
            # Mark event day and surrounding days (window of influence)
            window = 1  # +/- 1 day around event

            # Historical data
            data_with_events[regressor_name] = 0.0
            mask = (
                (data_with_events["ds"] >= event_date - pd.Timedelta(days=window)) &
                (data_with_events["ds"] <= event_date + pd.Timedelta(days=window))
            )
            data_with_events.loc[mask, regressor_name] = 1.0

            # Future data
            future_df[regressor_name] = 0.0
            future_mask = (
                (future_df["ds"] >= event_date - pd.Timedelta(days=window)) &
                (future_df["ds"] <= event_date + pd.Timedelta(days=window))
            )
            future_df.loc[future_mask, regressor_name] = 1.0

        return data_with_events, future_df

    def _prophet_forecast(
        self,
        data: pd.DataFrame,
        horizon: int,
        confidence_levels: List[int],
        events: Optional[pd.DataFrame] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, float]]:
        """Generate forecast using Prophet with event regressors support"""
        # Prepare data for Prophet
        prophet_data = data[["ds", "y"]].copy()

        # Initialize Prophet
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=max(confidence_levels) / 100,
        )

        # Add events as regressors if provided
        future_with_events = None
        if events is not None and not events.empty:
            # Prepare event regressors
            prophet_data, future_with_events = self._prepare_event_regressors(
                prophet_data, events, horizon
            )

            # Add each event type as a regressor
            event_types = [col for col in prophet_data.columns if col.startswith("event_")]
            for event_type in event_types:
                model.add_regressor(event_type)
                logger.info(f"Added event regressor: {event_type}")

        # Fit model
        model.fit(prophet_data)

        # Make future dataframe
        if future_with_events is not None:
            # Use the pre-built future with event regressors
            # Need to merge with make_future_dataframe to get proper dates
            future = model.make_future_dataframe(periods=horizon)

            # Add event regressor columns to future
            event_types = [col for col in prophet_data.columns if col.startswith("event_")]
            for event_type in event_types:
                # Merge with the prepared event data
                future[event_type] = 0.0
                # Set event values for matching dates
                for idx, row in future_with_events.iterrows():
                    mask = future["ds"] == row["ds"]
                    if mask.any() and event_type in row:
                        future.loc[mask, event_type] = row[event_type]
        else:
            future = model.make_future_dataframe(periods=horizon)

        # Predict
        forecast = model.predict(future)

        # Get only future predictions
        forecast = forecast.tail(horizon)

        # Format to match StatsForecast output
        forecast_df = pd.DataFrame(
            {
                "ds": forecast["ds"],
                "Prophet": forecast["yhat"],
                f"Prophet-lo-{confidence_levels[0]}": forecast["yhat_lower"],
                f"Prophet-hi-{confidence_levels[0]}": forecast["yhat_upper"],
            }
        )

        # Calculate metrics
        metrics = {"mape": None, "rmse": None, "mae": None}  # Prophet cross-validation can be added
        if len(data) >= horizon + 20:
            train_data = prophet_data.iloc[:-horizon]
            test_data = prophet_data.iloc[-horizon:]

            model_test = Prophet()
            model_test.fit(train_data)
            pred = model_test.predict(test_data[["ds"]])

            actual = test_data["y"].values
            predicted = pred["yhat"].values

            metrics = {
                "mape": float(np.mean(np.abs((actual - predicted) / actual)) * 100),
                "rmse": float(np.sqrt(np.mean((actual - predicted) ** 2))),
                "mae": float(np.mean(np.abs(actual - predicted))),
            }

        return forecast_df, metrics

    def _calculate_ensemble_weights(
        self, model_metrics: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Calculate ensemble weights based on historical accuracy.
        Models with lower errors get higher weights.
        """
        # Use MAPE for weighting (if available)
        mapes = {}
        for model_name, metrics in model_metrics.items():
            if metrics.get("mape") is not None:
                mapes[model_name] = metrics["mape"]

        if not mapes:
            # Equal weights if no metrics available
            num_models = len(model_metrics)
            return {model: 1.0 / num_models for model in model_metrics.keys()}

        # Inverse error weighting
        inv_errors = {model: 1.0 / (mape + 1) for model, mape in mapes.items()}
        total_inv = sum(inv_errors.values())
        weights = {model: inv / total_inv for model, inv in inv_errors.items()}

        return weights

    def _combine_forecasts(
        self,
        model_forecasts: Dict[str, pd.DataFrame],
        weights: Dict[str, float],
        confidence_levels: List[int],
    ) -> pd.DataFrame:
        """Combine multiple forecasts using weighted average"""
        # Get forecast values from each model
        forecasts_list = []

        for model_name, forecast_df in model_forecasts.items():
            weight = weights.get(model_name, 1.0 / len(model_forecasts))

            # Extract mean forecast
            if model_name == "Prophet":
                mean_col = "Prophet"
            else:
                mean_col = model_name

            forecasts_list.append(forecast_df[mean_col] * weight)

        # Weighted average
        ensemble_mean = sum(forecasts_list)

        # For confidence intervals, use the widest intervals (conservative approach)
        first_forecast = list(model_forecasts.values())[0]
        result_df = pd.DataFrame({"ds": first_forecast["ds"], "mean": ensemble_mean})

        # Combine confidence intervals (take percentiles across models)
        for level in confidence_levels:
            lower_bounds = []
            upper_bounds = []

            for model_name, forecast_df in model_forecasts.items():
                if model_name == "Prophet":
                    lower_col = f"Prophet-lo-{level}"
                    upper_col = f"Prophet-hi-{level}"
                else:
                    lower_col = f"{model_name}-lo-{level}"
                    upper_col = f"{model_name}-hi-{level}"

                if lower_col in forecast_df.columns:
                    lower_bounds.append(forecast_df[lower_col])
                if upper_col in forecast_df.columns:
                    upper_bounds.append(forecast_df[upper_col])

            if lower_bounds and upper_bounds:
                result_df[f"lo-{level}"] = pd.concat(lower_bounds, axis=1).min(axis=1)
                result_df[f"hi-{level}"] = pd.concat(upper_bounds, axis=1).max(axis=1)

        return result_df

    def _generate_benchmark(
        self, data: pd.DataFrame, horizon: int, frequency: str, season_length: int
    ) -> pd.DataFrame:
        """Generate benchmark forecast using Seasonal Naive"""
        sf = StatsForecast(
            models=[SeasonalNaive(season_length=season_length)], freq=frequency
        )
        benchmark_df = sf.forecast(df=data, h=horizon)
        return benchmark_df

    def _calculate_fva(
        self,
        ensemble_forecast: pd.DataFrame,
        benchmark_forecast: pd.DataFrame,
        historical_data: pd.DataFrame,
    ) -> float:
        """
        Calculate Forecast Value Added (FVA).
        FVA = (Benchmark Error - Model Error) / Benchmark Error * 100

        Positive FVA means the model is better than the benchmark.
        """
        # We need historical holdout data to calculate FVA
        # For now, return a placeholder (requires cross-validation)
        # TODO: Implement proper FVA calculation with time-series cross-validation
        return None  # Will be properly calculated in production

    def _format_benchmark(self, benchmark_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Format benchmark forecast for storage"""
        result = []
        for idx, row in benchmark_df.iterrows():
            result.append(
                {
                    "timestamp": row.name[1].isoformat()
                    if hasattr(row.name[1], "isoformat")
                    else str(row.name[1]),
                    "value": float(row["SeasonalNaive"]),
                }
            )
        return result

    def _aggregate_metrics(
        self, model_metrics: Dict[str, Dict[str, float]], weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate weighted average of metrics"""
        agg_metrics = {"mape": 0, "rmse": 0, "mae": 0}

        for model_name, metrics in model_metrics.items():
            weight = weights.get(model_name, 1.0 / len(model_metrics))

            for metric_name in ["mape", "rmse", "mae"]:
                if metrics.get(metric_name) is not None:
                    agg_metrics[metric_name] += metrics[metric_name] * weight

        # Set to None if all were None
        for key in agg_metrics:
            if agg_metrics[key] == 0:
                agg_metrics[key] = None

        return agg_metrics

    def _detect_frequency_code(self, df: pd.DataFrame) -> str:
        """Detect frequency code for forecasting"""
        if len(df) < 2:
            return "D"
        diffs = df["ds"].diff().dt.days.median()
        if 0.8 <= diffs <= 1.5:
            return "D"
        elif 6 <= diffs <= 8:
            return "W"
        elif 28 <= diffs <= 32:
            return "MS"
        elif 88 <= diffs <= 95:
            return "QS"
        else:
            return "D"

    def _get_season_length(self, frequency: str) -> int:
        """Get season length based on frequency"""
        season_map = {"D": 7, "W": 52, "MS": 12, "QS": 4}
        return season_map.get(frequency, 1)

    def _format_forecast_points(
        self, forecast_df: pd.DataFrame, confidence_levels: List[int]
    ) -> List[Dict[str, Any]]:
        """Format forecast dataframe into list of points"""
        forecast_points = []
        for idx, row in forecast_df.iterrows():
            point = {
                "timestamp": row["ds"].isoformat()
                if hasattr(row["ds"], "isoformat")
                else str(row["ds"]),
                "mean": float(row["mean"]),
            }
            for level in confidence_levels:
                if f"lo-{level}" in row:
                    point[f"lower_{level}"] = float(row[f"lo-{level}"])
                if f"hi-{level}" in row:
                    point[f"upper_{level}"] = float(row[f"hi-{level}"])
            forecast_points.append(point)
        return forecast_points

    def _calculate_metrics(
        self, historical_data: pd.DataFrame, model: StatsForecast, horizon: int, model_name: str
    ) -> Dict[str, float]:
        """Calculate accuracy metrics"""
        try:
            if len(historical_data) < horizon + 20:
                return {"mape": None, "rmse": None, "mae": None}

            train_data = historical_data.iloc[:-horizon].copy()
            test_data = historical_data.iloc[-horizon:].copy()

            forecast = model.forecast(df=train_data, h=horizon)
            actual = test_data["y"].values
            predicted = forecast[model_name].values[: len(actual)]

            mape = np.mean(np.abs((actual - predicted) / actual)) * 100
            rmse = np.sqrt(np.mean((actual - predicted) ** 2))
            mae = np.mean(np.abs(actual - predicted))

            return {"mape": float(mape), "rmse": float(rmse), "mae": float(mae)}
        except Exception:
            return {"mape": None, "rmse": None, "mae": None}

    def _calculate_confidence_score(
        self, metrics: Dict[str, float], data: pd.DataFrame, fva: Optional[float]
    ) -> float:
        """Calculate confidence score (0-100)"""
        score = 100.0

        if len(data) < 30:
            score -= 20
        elif len(data) < 60:
            score -= 10

        if metrics.get("mape"):
            mape = metrics["mape"]
            if mape > 50:
                score -= 30
            elif mape > 30:
                score -= 20
            elif mape > 15:
                score -= 10

        # Bonus for positive FVA
        if fva and fva > 10:
            score += 5

        cv = data["y"].std() / data["y"].mean() if data["y"].mean() != 0 else 0
        if cv > 1.0:
            score -= 15
        elif cv > 0.5:
            score -= 5

        return max(0, min(100, score))

    def _check_review_needed(
        self, data: pd.DataFrame, metrics: Dict[str, float], fva: Optional[float]
    ) -> bool:
        """Determine if manual review is needed"""
        if len(data) < 20:
            return True
        if metrics.get("mape") and metrics["mape"] > 30:
            return True
        if fva is not None and fva < -10:  # Model worse than benchmark
            return True
        cv = data["y"].std() / data["y"].mean() if data["y"].mean() != 0 else 0
        if cv > 0.8:
            return True
        return False

    def _detect_anomalies(
        self, data: pd.DataFrame, forecast_points: List[Dict[str, Any]], fva: Optional[float]
    ) -> List[str]:
        """Detect anomalies in forecast"""
        flags = []

        historical_max = data["y"].max()
        historical_min = data["y"].min()

        for point in forecast_points:
            mean_forecast = point["mean"]
            if mean_forecast > historical_max * 1.5:
                flags.append("extreme_high_forecast")
                break
            elif mean_forecast < historical_min * 0.5:
                flags.append("extreme_low_forecast")
                break

        if len(forecast_points) > 2:
            recent_mean = data["y"].tail(10).mean()
            forecast_mean = np.mean([p["mean"] for p in forecast_points[:5]])
            change_pct = abs(forecast_mean - recent_mean) / recent_mean * 100
            if change_pct > 50:
                flags.append("sudden_trend_change")

        if len(data) < 30:
            flags.append("limited_historical_data")

        if fva is not None and fva < -10:
            flags.append("worse_than_benchmark")

        return list(set(flags))
