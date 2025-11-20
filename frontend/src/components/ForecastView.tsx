'use client';

import { useState } from 'react';
import { Forecast, TimeSeries } from '@/types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import { Download, AlertCircle, TrendingUp, CheckCircle } from 'lucide-react';
import api from '@/lib/api';

interface ForecastViewProps {
  projectId: number;
  forecasts: Forecast[];
  timeseries: TimeSeries[];
  onRefresh: () => void;
}

export default function ForecastView({
  projectId,
  forecasts,
  timeseries,
  onRefresh,
}: ForecastViewProps) {
  const [selectedForecast, setSelectedForecast] = useState<Forecast | null>(
    forecasts[0] || null
  );

  const handleExport = async (forecastId: number) => {
    try {
      const blob = await api.exportForecastCSV(projectId, forecastId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `forecast_${forecastId}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (forecasts.length === 0) {
    return (
      <div className="card p-12 text-center">
        <TrendingUp size={64} className="mx-auto text-gray-400 mb-4" />
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          No forecasts yet
        </h2>
        <p className="text-gray-600">
          Upload data and generate forecasts to see results here
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Forecast Selector */}
      <div className="card p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Select Forecast
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {forecasts.map((forecast) => (
            <div
              key={forecast.id}
              onClick={() => setSelectedForecast(forecast)}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedForecast?.id === forecast.id
                  ? 'border-primary-600 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-gray-900">
                  {forecast.ts_id}
                </h3>
                {forecast.requires_manual_review ? (
                  <AlertCircle size={20} className="text-yellow-600" />
                ) : (
                  <CheckCircle size={20} className="text-green-600" />
                )}
              </div>
              <p className="text-sm text-gray-600 mb-1">
                Model: {forecast.model_used}
                {forecast.ensemble_models && forecast.ensemble_models.length > 0 && (
                  <span className="ml-1 text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">
                    {forecast.ensemble_models.length} models
                  </span>
                )}
              </p>
              <p className="text-sm text-gray-600 mb-1">
                Horizon: {forecast.forecast_horizon} periods
              </p>
              {forecast.confidence_score !== null && (
                <p className="text-sm text-gray-600">
                  Confidence: {forecast.confidence_score.toFixed(0)}/100
                </p>
              )}
              {forecast.forecast_value_added !== null && forecast.forecast_value_added !== undefined && (
                <p className={`text-sm font-medium ${forecast.forecast_value_added > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  FVA: {forecast.forecast_value_added > 0 ? '+' : ''}{forecast.forecast_value_added.toFixed(1)}%
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Selected Forecast Details */}
      {selectedForecast && (
        <>
          {/* Metrics */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Forecast Details: {selectedForecast.ts_id}
              </h2>
              <button
                onClick={() => handleExport(selectedForecast.id)}
                className="btn-secondary flex items-center gap-2"
              >
                <Download size={20} />
                Export CSV
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div>
                <p className="text-sm text-gray-600 mb-1">Model</p>
                <p className="font-medium text-gray-900">
                  {selectedForecast.model_used}
                </p>
                {selectedForecast.ensemble_models && selectedForecast.ensemble_models.length > 0 && (
                  <p className="text-xs text-purple-600 mt-1">
                    {selectedForecast.ensemble_models.join(', ')}
                  </p>
                )}
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Confidence Score</p>
                <p className="font-medium text-gray-900">
                  {selectedForecast.confidence_score?.toFixed(0) || 'N/A'}/100
                </p>
              </div>
              {selectedForecast.mape !== null && (
                <div>
                  <p className="text-sm text-gray-600 mb-1">MAPE</p>
                  <p className="font-medium text-gray-900">
                    {selectedForecast.mape.toFixed(2)}%
                  </p>
                </div>
              )}
              {selectedForecast.forecast_value_added !== null && selectedForecast.forecast_value_added !== undefined && (
                <div>
                  <p className="text-sm text-gray-600 mb-1">FVA vs Benchmark</p>
                  <p className={`font-medium ${selectedForecast.forecast_value_added > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {selectedForecast.forecast_value_added > 0 ? '+' : ''}{selectedForecast.forecast_value_added.toFixed(1)}%
                  </p>
                </div>
              )}
            </div>

            {/* Ensemble Weights */}
            {selectedForecast.ensemble_weights && Object.keys(selectedForecast.ensemble_weights).length > 0 && (
              <div className="mb-6 p-4 bg-purple-50 rounded-lg">
                <h4 className="text-sm font-medium text-purple-900 mb-2">Ensemble Weights</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(selectedForecast.ensemble_weights).map(([model, weight]) => (
                    <div key={model} className="text-sm">
                      <span className="text-gray-700">{model}:</span>{' '}
                      <span className="font-medium text-purple-700">{(weight * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Warnings and Flags */}
            {selectedForecast.requires_manual_review && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <div className="flex items-start">
                  <AlertCircle size={20} className="text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-yellow-800 mb-1">
                      Manual Review Required
                    </p>
                    <p className="text-sm text-yellow-700">
                      This forecast has quality concerns and should be reviewed
                      before use.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {selectedForecast.anomaly_flags &&
              selectedForecast.anomaly_flags.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="font-medium text-blue-800 mb-2">
                    Anomaly Flags:
                  </p>
                  <ul className="text-sm text-blue-700 space-y-1">
                    {selectedForecast.anomaly_flags.map((flag, idx) => (
                      <li key={idx}>
                        • {flag.replace(/_/g, ' ').toUpperCase()}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
          </div>

          {/* Chart */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Forecast Visualization
            </h3>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={selectedForecast.forecast_data.map((point) => ({
                    timestamp: new Date(point.timestamp).toLocaleDateString(),
                    mean: point.mean,
                    lower_90: point.lower_90,
                    upper_90: point.upper_90,
                    lower_80: point.lower_80,
                    upper_80: point.upper_80,
                  }))}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis />
                  <Tooltip />
                  <Legend />

                  {/* 90% Confidence Interval */}
                  <Area
                    type="monotone"
                    dataKey="upper_90"
                    stackId="1"
                    stroke="none"
                    fill="#bfdbfe"
                    fillOpacity={0.3}
                    name="90% Upper"
                  />
                  <Area
                    type="monotone"
                    dataKey="lower_90"
                    stackId="1"
                    stroke="none"
                    fill="transparent"
                    name="90% Lower"
                  />

                  {/* 80% Confidence Interval */}
                  <Area
                    type="monotone"
                    dataKey="upper_80"
                    stackId="2"
                    stroke="none"
                    fill="#93c5fd"
                    fillOpacity={0.4}
                    name="80% Upper"
                  />
                  <Area
                    type="monotone"
                    dataKey="lower_80"
                    stackId="2"
                    stroke="none"
                    fill="transparent"
                    name="80% Lower"
                  />

                  {/* Mean Forecast */}
                  <Line
                    type="monotone"
                    dataKey="mean"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    name="Forecast"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-gray-500 mt-4 text-center">
              Shaded areas represent 80% and 90% prediction intervals
            </p>
          </div>

          {/* Forecast Table */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Forecast Values
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Forecast
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      80% Lower
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      80% Upper
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      90% Lower
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      90% Upper
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {selectedForecast.forecast_data.map((point, idx) => (
                    <tr key={idx}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(point.timestamp).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {point.mean.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {point.lower_80.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {point.upper_80.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {point.lower_90.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {point.upper_90.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
