"""
Advanced Diagnostics Service (Phase 3)
Provides statistical diagnostics for time series analysis:
- ACF/PACF plots
- Seasonal decomposition
- Stationarity tests
- Residuals analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from statsmodels.tsa.stattools import acf, pacf, adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
import logging

logger = logging.getLogger(__name__)


class DiagnosticsService:
    """
    Advanced diagnostics for time series analysis.

    Provides:
    - Autocorrelation (ACF) and Partial Autocorrelation (PACF)
    - Seasonal decomposition (trend, seasonal, residual)
    - Stationarity tests (Augmented Dickey-Fuller)
    - Summary statistics
    """

    def __init__(self):
        pass

    def generate_full_diagnostics(
        self, data: pd.DataFrame, frequency: str = "D"
    ) -> Dict[str, Any]:
        """
        Generate complete diagnostics for a time series.

        Args:
            data: DataFrame with 'ds' (timestamp) and 'y' (values)
            frequency: Frequency of data ('D', 'W', 'MS', etc.)

        Returns:
            Dict with all diagnostic results
        """
        try:
            # Ensure data is sorted and indexed by date
            data = data.sort_values("ds").set_index("ds")
            values = data["y"].values

            diagnostics = {
                "success": True,
                "acf_results": self._calculate_acf(values),
                "pacf_results": self._calculate_pacf(values),
                "decomposition": self._seasonal_decomposition(data, frequency),
                "stationarity": self._test_stationarity(values),
                "summary_stats": self._calculate_summary_stats(values),
            }

            return diagnostics

        except Exception as e:
            logger.error(f"Diagnostics generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    def _calculate_acf(
        self, values: np.ndarray, nlags: Optional[int] = None
    ) -> Dict[str, Any]:
        """Calculate autocorrelation function"""
        try:
            if nlags is None:
                nlags = min(40, len(values) // 2 - 1)

            acf_values = acf(values, nlags=nlags, fft=True)

            # Calculate confidence intervals (95%)
            conf_int = 1.96 / np.sqrt(len(values))

            return {
                "lags": list(range(len(acf_values))),
                "values": acf_values.tolist(),
                "confidence_interval": conf_int,
                "interpretation": self._interpret_acf(acf_values),
            }
        except Exception as e:
            logger.error(f"ACF calculation failed: {str(e)}")
            return {"error": str(e)}

    def _calculate_pacf(
        self, values: np.ndarray, nlags: Optional[int] = None
    ) -> Dict[str, Any]:
        """Calculate partial autocorrelation function"""
        try:
            if nlags is None:
                nlags = min(40, len(values) // 2 - 1)

            pacf_values = pacf(values, nlags=nlags)

            # Calculate confidence intervals
            conf_int = 1.96 / np.sqrt(len(values))

            return {
                "lags": list(range(len(pacf_values))),
                "values": pacf_values.tolist(),
                "confidence_interval": conf_int,
                "interpretation": self._interpret_pacf(pacf_values),
            }
        except Exception as e:
            logger.error(f"PACF calculation failed: {str(e)}")
            return {"error": str(e)}

    def _seasonal_decomposition(
        self, data: pd.DataFrame, frequency: str
    ) -> Dict[str, Any]:
        """Perform seasonal decomposition"""
        try:
            # Determine period based on frequency
            period_map = {"D": 7, "W": 52, "MS": 12, "QS": 4}
            period = period_map.get(frequency, 7)

            # Need at least 2 full periods
            if len(data) < 2 * period:
                return {
                    "error": f"Insufficient data for decomposition (need at least {2 * period} points)"
                }

            # Perform decomposition
            decomposition = seasonal_decompose(
                data["y"], model="additive", period=period, extrapolate_trend="freq"
            )

            return {
                "trend": decomposition.trend.fillna(0).tolist(),
                "seasonal": decomposition.seasonal.fillna(0).tolist(),
                "residual": decomposition.resid.fillna(0).tolist(),
                "timestamps": data.index.astype(str).tolist(),
                "period": period,
                "model": "additive",
            }

        except Exception as e:
            logger.error(f"Decomposition failed: {str(e)}")
            return {"error": str(e)}

    def _test_stationarity(self, values: np.ndarray) -> Dict[str, Any]:
        """Perform Augmented Dickey-Fuller test for stationarity"""
        try:
            result = adfuller(values, autolag="AIC")

            return {
                "test_statistic": float(result[0]),
                "p_value": float(result[1]),
                "n_lags": int(result[2]),
                "n_observations": int(result[3]),
                "critical_values": {
                    "1%": float(result[4]["1%"]),
                    "5%": float(result[4]["5%"]),
                    "10%": float(result[4]["10%"]),
                },
                "is_stationary": result[1] < 0.05,  # p-value < 0.05
                "interpretation": self._interpret_stationarity(result),
            }

        except Exception as e:
            logger.error(f"Stationarity test failed: {str(e)}")
            return {"error": str(e)}

    def _calculate_summary_stats(self, values: np.ndarray) -> Dict[str, Any]:
        """Calculate comprehensive summary statistics"""
        try:
            return {
                "count": int(len(values)),
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "q1": float(np.percentile(values, 25)),
                "q3": float(np.percentile(values, 75)),
                "skewness": float(pd.Series(values).skew()),
                "kurtosis": float(pd.Series(values).kurtosis()),
                "cv": float(np.std(values) / np.mean(values))
                if np.mean(values) != 0
                else 0,
            }
        except Exception as e:
            logger.error(f"Summary stats calculation failed: {str(e)}")
            return {"error": str(e)}

    def _interpret_acf(self, acf_values: np.ndarray) -> str:
        """Provide interpretation of ACF pattern"""
        # Check for significant autocorrelation
        conf_int = 1.96 / np.sqrt(len(acf_values) * 10)  # Approximate
        significant_lags = np.sum(np.abs(acf_values[1:]) > conf_int)

        if significant_lags > len(acf_values) * 0.3:
            return "Strong autocorrelation detected - data shows persistent patterns"
        elif significant_lags > len(acf_values) * 0.1:
            return "Moderate autocorrelation - some temporal dependencies present"
        else:
            return "Weak autocorrelation - data appears relatively independent over time"

    def _interpret_pacf(self, pacf_values: np.ndarray) -> str:
        """Provide interpretation of PACF pattern"""
        # Find first significant lag
        conf_int = 1.96 / np.sqrt(len(pacf_values) * 10)
        significant = np.where(np.abs(pacf_values[1:]) > conf_int)[0]

        if len(significant) == 0:
            return "No significant partial autocorrelation - AR model may not be needed"
        elif len(significant) <= 3:
            return f"Significant PACF up to lag {significant[-1]+1} - AR({significant[-1]+1}) model suggested"
        else:
            return "Multiple significant lags - complex AR structure or seasonality present"

    def _interpret_stationarity(self, adf_result: tuple) -> str:
        """Provide interpretation of stationarity test"""
        p_value = adf_result[1]
        test_stat = adf_result[0]
        critical_5 = adf_result[4]["5%"]

        if p_value < 0.01:
            return "Strong evidence of stationarity (p<0.01) - data is stable over time"
        elif p_value < 0.05:
            return "Moderate evidence of stationarity (p<0.05) - data is likely stable"
        elif p_value < 0.10:
            return "Weak evidence of stationarity (p<0.10) - borderline case"
        else:
            return "Non-stationary data detected - consider differencing or detrending"

    def analyze_residuals(
        self, actual: np.ndarray, predicted: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyze forecast residuals for quality assessment.

        Args:
            actual: Actual values
            predicted: Predicted values

        Returns:
            Dict with residual analysis
        """
        try:
            residuals = actual - predicted

            # Normality test (simple check)
            from scipy import stats

            _, normality_p = stats.normaltest(residuals)

            # Ljung-Box test for residual autocorrelation
            from statsmodels.stats.diagnostic import acorr_ljungbox

            lb_test = acorr_ljungbox(residuals, lags=[10], return_df=True)

            return {
                "residuals": residuals.tolist(),
                "mean": float(np.mean(residuals)),
                "std": float(np.std(residuals)),
                "normality_p_value": float(normality_p),
                "is_normal": normality_p > 0.05,
                "ljung_box_p_value": float(lb_test["lb_pvalue"].iloc[0]),
                "residuals_uncorrelated": float(lb_test["lb_pvalue"].iloc[0]) > 0.05,
                "interpretation": self._interpret_residuals(
                    normality_p, lb_test["lb_pvalue"].iloc[0]
                ),
            }

        except Exception as e:
            logger.error(f"Residual analysis failed: {str(e)}")
            return {"error": str(e)}

    def _interpret_residuals(
        self, normality_p: float, lb_p: float
    ) -> str:
        """Interpret residual analysis results"""
        issues = []

        if normality_p < 0.05:
            issues.append("non-normal residuals")
        if lb_p < 0.05:
            issues.append("autocorrelated residuals")

        if not issues:
            return "Residuals appear well-behaved - good model fit"
        else:
            return f"Residual issues detected: {', '.join(issues)} - model may need improvement"
