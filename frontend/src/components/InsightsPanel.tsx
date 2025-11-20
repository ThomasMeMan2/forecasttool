'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Lightbulb, Sparkles, TrendingUp, AlertCircle, Loader2, X } from 'lucide-react';

interface Insight {
  id: number;
  type: string;
  text: string;
  confidence: number;
  model: string;
  generated_at: string;
}

interface InsightsPanelProps {
  projectId: number;
  timeseriesId?: number;
  forecastId?: number;
  tsId?: string;
}

export default function InsightsPanel({
  projectId,
  timeseriesId,
  forecastId,
  tsId,
}: InsightsPanelProps) {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState<string | null>(null);

  useEffect(() => {
    loadInsights();
  }, [projectId, timeseriesId, forecastId]);

  const loadInsights = async () => {
    try {
      setLoading(true);
      const filters: any = {};
      if (timeseriesId) filters.timeseries_id = timeseriesId;
      if (forecastId) filters.forecast_id = forecastId;

      const response = await api.getProjectInsights(projectId, filters);
      setInsights(response.insights || []);
    } catch (err) {
      console.error('Failed to load insights:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateHistoryInsight = async () => {
    if (!tsId) return;

    try {
      setGenerating('history');
      const response = await api.generateHistoryInsight(projectId, tsId);
      await loadInsights();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to generate insight');
    } finally {
      setGenerating(null);
    }
  };

  const generateForecastInsight = async () => {
    if (!forecastId) return;

    try {
      setGenerating('forecast');
      const response = await api.generateForecastInsight(projectId, forecastId);
      await loadInsights();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to generate insight');
    } finally {
      setGenerating(null);
    }
  };

  const generateQualityInsight = async () => {
    if (!forecastId) return;

    try {
      setGenerating('quality');
      const response = await api.generateQualityInsight(projectId, forecastId);
      await loadInsights();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to generate insight');
    } finally {
      setGenerating(null);
    }
  };

  const deleteInsight = async (insightId: number) => {
    if (!confirm('Delete this insight?')) return;

    try {
      await api.deleteInsight(projectId, insightId);
      await loadInsights();
    } catch (err) {
      alert('Failed to delete insight');
    }
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'history_summary':
        return <TrendingUp size={20} className="text-blue-600" />;
      case 'forecast_summary':
        return <Sparkles size={20} className="text-purple-600" />;
      case 'quality_assessment':
        return <AlertCircle size={20} className="text-amber-600" />;
      default:
        return <Lightbulb size={20} className="text-gray-600" />;
    }
  };

  const getInsightTitle = (type: string) => {
    switch (type) {
      case 'history_summary':
        return 'Historical Data Analysis';
      case 'forecast_summary':
        return 'Forecast Prediction';
      case 'quality_assessment':
        return 'Quality Assessment';
      default:
        return 'Insight';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Lightbulb size={20} className="text-yellow-500" />
            AI Insights
            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">Phase 3</span>
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            AI-powered analysis and recommendations
          </p>
        </div>

        {/* Generate Buttons */}
        <div className="flex gap-2">
          {tsId && (
            <button
              onClick={generateHistoryInsight}
              disabled={generating === 'history'}
              className="btn-secondary text-sm flex items-center gap-2"
            >
              {generating === 'history' ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <TrendingUp size={16} />
              )}
              History
            </button>
          )}

          {forecastId && (
            <>
              <button
                onClick={generateForecastInsight}
                disabled={generating === 'forecast'}
                className="btn-secondary text-sm flex items-center gap-2"
              >
                {generating === 'forecast' ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Sparkles size={16} />
                )}
                Forecast
              </button>

              <button
                onClick={generateQualityInsight}
                disabled={generating === 'quality'}
                className="btn-secondary text-sm flex items-center gap-2"
              >
                {generating === 'quality' ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <AlertCircle size={16} />
                )}
                Quality
              </button>
            </>
          )}
        </div>
      </div>

      {/* Insights List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center py-8">
            <Loader2 size={32} className="animate-spin text-primary-600 mx-auto" />
          </div>
        ) : insights.length === 0 ? (
          <div className="card p-6 text-center">
            <Lightbulb size={48} className="text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No insights yet</p>
            <p className="text-sm text-gray-400 mt-1">
              Generate AI insights using the buttons above
            </p>
          </div>
        ) : (
          insights.map((insight) => (
            <div key={insight.id} className="card p-4 relative group">
              <button
                onClick={() => deleteInsight(insight.id)}
                className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-red-600"
              >
                <X size={18} />
              </button>

              <div className="flex items-start gap-3">
                {getInsightIcon(insight.type)}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-medium text-gray-900">
                      {getInsightTitle(insight.type)}
                    </h4>
                    <span className="text-xs text-gray-500">
                      {insight.model !== 'template' && (
                        <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                          {insight.model}
                        </span>
                      )}
                    </span>
                  </div>

                  <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">
                    {insight.text}
                  </p>

                  <div className="flex items-center gap-3 mt-3 text-xs text-gray-500">
                    <span>
                      Confidence: {Math.round(insight.confidence * 100)}%
                    </span>
                    <span>•</span>
                    <span>
                      {new Date(insight.generated_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
