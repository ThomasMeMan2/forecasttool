'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Activity, TrendingUp, BarChart3, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

interface DiagnosticsData {
  success: boolean;
  ts_id: string;
  frequency: string;
  diagnostics: {
    acf_results: {
      lags: number[];
      values: number[];
      confidence_interval: number;
      interpretation: string;
    };
    pacf_results: {
      lags: number[];
      values: number[];
      confidence_interval: number;
      interpretation: string;
    };
    decomposition: {
      trend: number[];
      seasonal: number[];
      residual: number[];
      timestamps: string[];
      period: number;
      model: string;
    } | { error: string };
    stationarity: {
      test_statistic: number;
      p_value: number;
      is_stationary: boolean;
      critical_values: {
        '1%': number;
        '5%': number;
        '10%': number;
      };
      interpretation: string;
    };
    summary_stats: {
      count: number;
      mean: number;
      median: number;
      std: number;
      min: number;
      max: number;
      q1: number;
      q3: number;
      skewness: number;
      kurtosis: number;
      cv: number;
    };
  };
}

interface DiagnosticsPanelProps {
  projectId: number;
  tsId: string;
  frequency?: string;
}

export default function DiagnosticsPanel({
  projectId,
  tsId,
  frequency = 'D',
}: DiagnosticsPanelProps) {
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'acf' | 'decomposition' | 'stats'>('stats');

  useEffect(() => {
    loadDiagnostics();
  }, [projectId, tsId, frequency]);

  const loadDiagnostics = async () => {
    try {
      setLoading(true);
      const response = await api.getTimeseriesDiagnostics(projectId, tsId, frequency);
      setDiagnostics(response);
    } catch (err) {
      console.error('Failed to load diagnostics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="card p-8 text-center">
        <Loader2 size={48} className="animate-spin text-primary-600 mx-auto mb-3" />
        <p className="text-gray-600">Running diagnostics...</p>
      </div>
    );
  }

  if (!diagnostics || !diagnostics.success) {
    return (
      <div className="card p-6 text-center">
        <XCircle size={48} className="text-red-500 mx-auto mb-3" />
        <p className="text-gray-600">Failed to load diagnostics</p>
      </div>
    );
  }

  const { diagnostics: diag } = diagnostics;

  // Prepare ACF chart data
  const acfData = diag.acf_results.lags.map((lag, idx) => ({
    lag,
    acf: diag.acf_results.values[idx],
  }));

  // Prepare PACF chart data
  const pacfData = diag.pacf_results.lags.map((lag, idx) => ({
    lag,
    pacf: diag.pacf_results.values[idx],
  }));

  // Prepare decomposition data
  const hasDecomposition = !('error' in diag.decomposition);
  const decompositionData = hasDecomposition
    ? diag.decomposition.timestamps.map((ts, idx) => ({
        timestamp: new Date(ts).toLocaleDateString(),
        trend: diag.decomposition.trend[idx],
        seasonal: diag.decomposition.seasonal[idx],
        residual: diag.decomposition.residual[idx],
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Activity size={20} className="text-primary-600" />
          Advanced Diagnostics
          <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">Phase 3</span>
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Statistical analysis of time series properties
        </p>
      </div>

      {/* Stationarity Test Banner */}
      <div className={`card p-4 ${diag.stationarity.is_stationary ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'}`}>
        <div className="flex items-center gap-3">
          {diag.stationarity.is_stationary ? (
            <CheckCircle size={24} className="text-green-600" />
          ) : (
            <XCircle size={24} className="text-amber-600" />
          )}
          <div className="flex-1">
            <h4 className="font-medium text-gray-900">
              {diag.stationarity.is_stationary ? 'Stationary Data' : 'Non-Stationary Data'}
            </h4>
            <p className="text-sm text-gray-700 mt-1">
              {diag.stationarity.interpretation}
            </p>
            <p className="text-xs text-gray-600 mt-2">
              ADF Test: p-value = {diag.stationarity.p_value.toFixed(4)} |
              Test Statistic = {diag.stationarity.test_statistic.toFixed(4)}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('stats')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'stats'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <BarChart3 size={16} className="inline mr-2" />
            Statistics
          </button>
          <button
            onClick={() => setActiveTab('acf')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'acf'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Activity size={16} className="inline mr-2" />
            ACF / PACF
          </button>
          <button
            onClick={() => setActiveTab('decomposition')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'decomposition'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <TrendingUp size={16} className="inline mr-2" />
            Decomposition
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'stats' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card p-4">
              <p className="text-xs text-gray-600">Count</p>
              <p className="text-2xl font-bold text-gray-900">{diag.summary_stats.count}</p>
            </div>
            <div className="card p-4">
              <p className="text-xs text-gray-600">Mean</p>
              <p className="text-2xl font-bold text-gray-900">{diag.summary_stats.mean.toFixed(2)}</p>
            </div>
            <div className="card p-4">
              <p className="text-xs text-gray-600">Std Dev</p>
              <p className="text-2xl font-bold text-gray-900">{diag.summary_stats.std.toFixed(2)}</p>
            </div>
            <div className="card p-4">
              <p className="text-xs text-gray-600">CV</p>
              <p className="text-2xl font-bold text-gray-900">{diag.summary_stats.cv.toFixed(2)}</p>
            </div>
          </div>

          <div className="card p-6">
            <h4 className="font-medium text-gray-900 mb-4">Distribution</h4>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-600 mb-2">Range</p>
                <p className="text-lg font-semibold">
                  {diag.summary_stats.min.toFixed(2)} → {diag.summary_stats.max.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-2">Quartiles</p>
                <p className="text-lg font-semibold">
                  Q1: {diag.summary_stats.q1.toFixed(2)} |
                  Q2: {diag.summary_stats.median.toFixed(2)} |
                  Q3: {diag.summary_stats.q3.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-2">Skewness</p>
                <p className="text-lg font-semibold">{diag.summary_stats.skewness.toFixed(3)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-2">Kurtosis</p>
                <p className="text-lg font-semibold">{diag.summary_stats.kurtosis.toFixed(3)}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'acf' && (
        <div className="space-y-6">
          {/* ACF Chart */}
          <div className="card p-6">
            <h4 className="font-medium text-gray-900 mb-2">Autocorrelation Function (ACF)</h4>
            <p className="text-sm text-gray-600 mb-4">{diag.acf_results.interpretation}</p>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={acfData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="lag" />
                <YAxis domain={[-1, 1]} />
                <Tooltip />
                <ReferenceLine y={diag.acf_results.confidence_interval} stroke="red" strokeDasharray="3 3" />
                <ReferenceLine y={-diag.acf_results.confidence_interval} stroke="red" strokeDasharray="3 3" />
                <Bar dataKey="acf" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* PACF Chart */}
          <div className="card p-6">
            <h4 className="font-medium text-gray-900 mb-2">Partial Autocorrelation Function (PACF)</h4>
            <p className="text-sm text-gray-600 mb-4">{diag.pacf_results.interpretation}</p>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={pacfData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="lag" />
                <YAxis domain={[-1, 1]} />
                <Tooltip />
                <ReferenceLine y={diag.pacf_results.confidence_interval} stroke="red" strokeDasharray="3 3" />
                <ReferenceLine y={-diag.pacf_results.confidence_interval} stroke="red" strokeDasharray="3 3" />
                <Bar dataKey="pacf" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {activeTab === 'decomposition' && (
        <div className="card p-6">
          {hasDecomposition ? (
            <>
              <h4 className="font-medium text-gray-900 mb-2">Seasonal Decomposition</h4>
              <p className="text-sm text-gray-600 mb-4">
                Model: {diag.decomposition.model} | Period: {diag.decomposition.period}
              </p>

              <div className="space-y-6">
                {/* Trend */}
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Trend Component</h5>
                  <ResponsiveContainer width="100%" height={150}>
                    <LineChart data={decompositionData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="trend" stroke="#3b82f6" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Seasonal */}
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Seasonal Component</h5>
                  <ResponsiveContainer width="100%" height={150}>
                    <LineChart data={decompositionData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="seasonal" stroke="#10b981" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Residual */}
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Residual Component</h5>
                  <ResponsiveContainer width="100%" height={150}>
                    <LineChart data={decompositionData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="residual" stroke="#ef4444" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <XCircle size={48} className="text-amber-500 mx-auto mb-3" />
              <p className="text-gray-600">{diag.decomposition.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
