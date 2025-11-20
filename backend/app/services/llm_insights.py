"""
LLM Insights Service for generating natural language insights
Supports OpenAI, Anthropic Claude, and local Ollama models
"""
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMInsightsService:
    """
    Generate natural language insights about time series and forecasts using LLMs.

    Supports multiple providers:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude 3)
    - Ollama (local models for privacy)
    """

    def __init__(self, provider: str = "openai", model: str = "gpt-4-turbo-preview"):
        """
        Initialize LLM service.

        Args:
            provider: 'openai', 'anthropic', or 'ollama'
            model: Specific model name
        """
        self.provider = provider
        self.model = model
        self.client = None

        # Initialize client based on provider
        if provider == "openai":
            try:
                from openai import OpenAI
                api_key = getattr(settings, "openai_api_key", None)
                if api_key:
                    self.client = OpenAI(api_key=api_key)
            except ImportError:
                logger.warning("OpenAI package not installed")
        elif provider == "anthropic":
            try:
                from anthropic import Anthropic
                api_key = getattr(settings, "anthropic_api_key", None)
                if api_key:
                    self.client = Anthropic(api_key=api_key)
            except ImportError:
                logger.warning("Anthropic package not installed")
        elif provider == "ollama":
            # Ollama uses local API
            self.ollama_base_url = getattr(
                settings, "ollama_base_url", "http://localhost:11434"
            )

    def generate_history_summary(
        self, data: pd.DataFrame, ts_id: str, data_characteristics: Dict[str, Any]
    ) -> str:
        """
        Generate a summary of historical data characteristics.

        Args:
            data: Historical time series data
            ts_id: Time series identifier
            data_characteristics: Dict with stats (volatility, trend, seasonality, etc.)

        Returns:
            Natural language summary
        """
        prompt = self._create_history_prompt(data, ts_id, data_characteristics)
        return self._call_llm(prompt)

    def generate_forecast_summary(
        self,
        forecast_data: List[Dict[str, Any]],
        historical_data: pd.DataFrame,
        metrics: Dict[str, float],
        ts_id: str,
    ) -> str:
        """
        Generate a summary of the forecast and its quality.

        Args:
            forecast_data: List of forecast points
            historical_data: Historical time series
            metrics: Accuracy metrics (MAPE, RMSE, etc.)
            ts_id: Time series identifier

        Returns:
            Natural language forecast summary
        """
        prompt = self._create_forecast_prompt(
            forecast_data, historical_data, metrics, ts_id
        )
        return self._call_llm(prompt)

    def generate_quality_assessment(
        self, metrics: Dict[str, float], anomaly_flags: List[str], fva: Optional[float]
    ) -> str:
        """
        Assess forecast quality and provide recommendations.

        Args:
            metrics: Accuracy metrics
            anomaly_flags: List of detected anomalies
            fva: Forecast Value Added percentage

        Returns:
            Quality assessment and recommendations
        """
        prompt = self._create_quality_prompt(metrics, anomaly_flags, fva)
        return self._call_llm(prompt)

    def explain_anomaly(
        self,
        anomaly_type: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Explain why a forecast has been flagged.

        Args:
            anomaly_type: Type of anomaly
            context: Additional context about the data and forecast

        Returns:
            Explanation of the anomaly
        """
        prompt = self._create_anomaly_prompt(anomaly_type, context)
        return self._call_llm(prompt)

    def generate_recommendations(
        self,
        data_quality: Dict[str, Any],
        forecast_quality: Dict[str, Any],
        requires_review: bool,
    ) -> str:
        """
        Generate actionable recommendations for the user.

        Args:
            data_quality: Data quality metrics
            forecast_quality: Forecast quality metrics
            requires_review: Whether manual review is needed

        Returns:
            Recommendations for improving forecasts or using them
        """
        prompt = self._create_recommendations_prompt(
            data_quality, forecast_quality, requires_review
        )
        return self._call_llm(prompt)

    def _create_history_prompt(
        self, data: pd.DataFrame, ts_id: str, characteristics: Dict[str, Any]
    ) -> str:
        """Create prompt for history summary"""
        data_points = len(data)
        mean_val = data["y"].mean()
        std_val = data["y"].std()
        cv = (std_val / mean_val * 100) if mean_val != 0 else 0

        has_trend = characteristics.get("has_trend", False)
        has_seasonality = characteristics.get("has_seasonality", False)
        volatility = characteristics.get("volatility_score", 0)

        prompt = f"""Analyze this time series data and provide a concise 2-3 sentence summary for a non-technical user.

Time Series ID: {ts_id}
Data Points: {data_points}
Average Value: {mean_val:.2f}
Standard Deviation: {std_val:.2f}
Coefficient of Variation: {cv:.1f}%
Trend Present: {"Yes" if has_trend else "No"}
Seasonality Present: {"Yes" if has_seasonality else "No"}
Volatility Score (0-100): {volatility:.1f}

Focus on:
1. Overall pattern description (trend, seasonality, volatility)
2. Data quality assessment
3. Any notable characteristics

Use clear, non-technical language. Be concise and actionable.
"""
        return prompt

    def _create_forecast_prompt(
        self,
        forecast_data: List[Dict[str, Any]],
        historical_data: pd.DataFrame,
        metrics: Dict[str, float],
        ts_id: str,
    ) -> str:
        """Create prompt for forecast summary"""
        horizon = len(forecast_data)
        avg_forecast = sum(p["mean"] for p in forecast_data) / len(forecast_data)
        historical_avg = historical_data["y"].mean()
        change_pct = ((avg_forecast - historical_avg) / historical_avg * 100) if historical_avg != 0 else 0

        mape = metrics.get("mape", 0)

        prompt = f"""Summarize this forecast for a non-technical user in 2-3 sentences.

Time Series: {ts_id}
Forecast Horizon: {horizon} periods
Historical Average: {historical_avg:.2f}
Forecast Average: {avg_forecast:.2f}
Change from History: {change_pct:+.1f}%
Model Accuracy (MAPE): {mape:.1f}% {"(good)" if mape < 15 else "(moderate)" if mape < 30 else "(needs review)"}

Focus on:
1. What the forecast predicts (magnitude and direction)
2. How confident we should be (based on accuracy)
3. Key drivers or patterns

Use clear, business-friendly language. Avoid technical jargon.
"""
        return prompt

    def _create_quality_prompt(
        self, metrics: Dict[str, float], anomaly_flags: List[str], fva: Optional[float]
    ) -> str:
        """Create prompt for quality assessment"""
        mape = metrics.get("mape", 0)

        prompt = f"""Assess this forecast quality and provide recommendations in 2-3 sentences.

Accuracy (MAPE): {mape:.1f}%
Anomaly Flags: {", ".join(anomaly_flags) if anomaly_flags else "None"}
Forecast Value Added: {fva:.1f}% if fva else "Not calculated"}

Provide:
1. Overall quality rating (High/Medium/Low confidence)
2. Main concerns or strengths
3. Whether to trust this forecast or seek additional review

Be direct and actionable. Help the user make decisions.
"""
        return prompt

    def _create_anomaly_prompt(
        self, anomaly_type: str, context: Dict[str, Any]
    ) -> str:
        """Create prompt for anomaly explanation"""
        prompt = f"""Explain why this forecast has been flagged in simple terms (1-2 sentences).

Anomaly Type: {anomaly_type.replace("_", " ").title()}
Context: {context}

Explain:
1. What this flag means
2. Why it matters for forecast reliability

Use non-technical language. Be brief and clear.
"""
        return prompt

    def _create_recommendations_prompt(
        self,
        data_quality: Dict[str, Any],
        forecast_quality: Dict[str, Any],
        requires_review: bool,
    ) -> str:
        """Create prompt for recommendations"""
        prompt = f"""Provide actionable recommendations for this forecast (2-3 bullet points).

Data Quality Score: {data_quality.get("quality_score", 0)}/100
Forecast Accuracy: {forecast_quality.get("mape", 0):.1f}% MAPE
Requires Manual Review: {"Yes" if requires_review else "No"}

Recommend:
1. How to use this forecast (trust level)
2. Any data improvements needed
3. Next steps

Be specific and actionable. Prioritize practical advice.
"""
        return prompt

    def _call_llm(self, prompt: str, max_tokens: int = 200) -> str:
        """
        Call the LLM with the given prompt.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            Generated text
        """
        try:
            if self.provider == "openai" and self.client:
                return self._call_openai(prompt, max_tokens)
            elif self.provider == "anthropic" and self.client:
                return self._call_anthropic(prompt, max_tokens)
            elif self.provider == "ollama":
                return self._call_ollama(prompt, max_tokens)
            else:
                # Fallback: return a template-based insight
                return self._generate_template_insight(prompt)
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            return self._generate_template_insight(prompt)

    def _call_openai(self, prompt: str, max_tokens: int) -> str:
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful forecasting assistant. Provide clear, concise insights in non-technical language.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    def _call_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Call Anthropic Claude API"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    def _call_ollama(self, prompt: str, max_tokens: int) -> str:
        """Call local Ollama API"""
        import requests

        response = requests.post(
            f"{self.ollama_base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
        )

        if response.status_code == 200:
            return response.json()["response"].strip()
        else:
            raise Exception(f"Ollama API error: {response.status_code}")

    def _generate_template_insight(self, prompt: str) -> str:
        """
        Generate a simple template-based insight when LLM is unavailable.
        This ensures the system always provides some insight.
        """
        # Extract key information from prompt
        if "Time Series ID:" in prompt:
            if "Forecast Horizon:" in prompt:
                return "Forecast generated based on historical patterns. Review the confidence intervals and accuracy metrics to assess reliability."
            else:
                return "Time series data has been analyzed. Review the data quality indicators and statistical properties before generating forecasts."
        elif "Accuracy (MAPE):" in prompt:
            return "Forecast quality assessed. Check accuracy metrics and anomaly flags to determine if manual review is needed."
        else:
            return "Analysis complete. Review the detailed metrics and visualizations for more information."
