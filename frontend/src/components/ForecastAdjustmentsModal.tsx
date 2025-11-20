'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Edit3, X, Save, Trash2, AlertCircle } from 'lucide-react';
import { ForecastAdjustment } from '@/types';

interface ForecastAdjustmentsModalProps {
  projectId: number;
  forecastId: number;
  forecastData: Array<{ timestamp: string; mean: number }>;
  onClose: () => void;
  onAdjustmentsUpdated?: () => void;
}

export default function ForecastAdjustmentsModal({
  projectId,
  forecastId,
  forecastData,
  onClose,
  onAdjustmentsUpdated,
}: ForecastAdjustmentsModalProps) {
  const [adjustments, setAdjustments] = useState<ForecastAdjustment[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [adjustedValue, setAdjustedValue] = useState<string>('');
  const [adjustmentReason, setAdjustmentReason] = useState<string>('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAdjustments();
  }, [forecastId]);

  const loadAdjustments = async () => {
    try {
      const response = await api.getAdjustments(projectId, forecastId);
      setAdjustments(response.adjustments || []);
    } catch (err) {
      console.error('Failed to load adjustments:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedPeriod || !adjustedValue || !adjustmentReason) {
      alert('Please fill all fields');
      return;
    }

    const selectedForecastPoint = forecastData.find(
      (point) => point.timestamp === selectedPeriod
    );

    if (!selectedForecastPoint) {
      alert('Invalid period selected');
      return;
    }

    try {
      setLoading(true);
      await api.createAdjustment(projectId, {
        forecast_id: forecastId,
        period_timestamp: selectedPeriod,
        original_value: selectedForecastPoint.mean,
        adjusted_value: parseFloat(adjustedValue),
        adjustment_reason: adjustmentReason,
      });

      // Reset form
      setSelectedPeriod('');
      setAdjustedValue('');
      setAdjustmentReason('');

      await loadAdjustments();
      onAdjustmentsUpdated?.();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create adjustment');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (adjustmentId: number) => {
    if (!confirm('Delete this adjustment?')) return;

    try {
      await api.deleteAdjustment(projectId, adjustmentId);
      await loadAdjustments();
      onAdjustmentsUpdated?.();
    } catch (err) {
      alert('Failed to delete adjustment');
    }
  };

  const getOriginalValue = (timestamp: string): number => {
    const point = forecastData.find((p) => p.timestamp === timestamp);
    return point?.mean || 0;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
              <Edit3 size={20} />
              Forecast Adjustments
              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">Phase 2</span>
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Manually override forecast values with business knowledge
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Info Banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle size={20} className="text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-900">
                <p className="font-medium">Adjustment Guidelines</p>
                <ul className="mt-2 space-y-1 list-disc list-inside">
                  <li>All adjustments require a documented reason</li>
                  <li>Original values are preserved for audit trail</li>
                  <li>Adjustments can be reverted at any time</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Create Adjustment Form */}
          <div className="card p-6">
            <h3 className="font-medium text-gray-900 mb-4">Create New Adjustment</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Period *</label>
                  <select
                    value={selectedPeriod}
                    onChange={(e) => {
                      setSelectedPeriod(e.target.value);
                      const point = forecastData.find(
                        (p) => p.timestamp === e.target.value
                      );
                      if (point) {
                        setAdjustedValue(point.mean.toFixed(2));
                      }
                    }}
                    className="input"
                    required
                  >
                    <option value="">Select period...</option>
                    {forecastData.map((point) => (
                      <option key={point.timestamp} value={point.timestamp}>
                        {new Date(point.timestamp).toLocaleDateString()} (
                        Original: {point.mean.toFixed(2)})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">Adjusted Value *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={adjustedValue}
                    onChange={(e) => setAdjustedValue(e.target.value)}
                    className="input"
                    placeholder="Enter new value"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="label">Reason for Adjustment *</label>
                <textarea
                  value={adjustmentReason}
                  onChange={(e) => setAdjustmentReason(e.target.value)}
                  className="input"
                  rows={3}
                  placeholder="Explain why this adjustment is needed..."
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary flex items-center gap-2"
              >
                <Save size={18} />
                Create Adjustment
              </button>
            </form>
          </div>

          {/* Existing Adjustments */}
          <div className="card p-6">
            <h3 className="font-medium text-gray-900 mb-4">
              Existing Adjustments ({adjustments.length})
            </h3>

            {adjustments.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No adjustments yet</p>
            ) : (
              <div className="space-y-3">
                {adjustments.map((adjustment) => (
                  <div
                    key={adjustment.id}
                    className="flex items-start justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-medium text-gray-900">
                          {new Date(adjustment.period_timestamp).toLocaleDateString()}
                        </span>
                        <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                          {adjustment.original_value.toFixed(2)} →{' '}
                          {adjustment.adjusted_value.toFixed(2)}
                        </span>
                        <span
                          className={`text-xs px-2 py-1 rounded ${
                            adjustment.adjusted_value > adjustment.original_value
                              ? 'bg-green-100 text-green-700'
                              : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {adjustment.adjusted_value > adjustment.original_value
                            ? '+'
                            : ''}
                          {(
                            ((adjustment.adjusted_value - adjustment.original_value) /
                              adjustment.original_value) *
                            100
                          ).toFixed(1)}
                          %
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">
                        {adjustment.adjustment_reason}
                      </p>
                      <p className="text-xs text-gray-500">
                        Created: {new Date(adjustment.created_at).toLocaleString()}
                      </p>
                    </div>

                    <button
                      onClick={() => handleDelete(adjustment.id)}
                      className="text-red-600 hover:text-red-700 ml-4"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button onClick={onClose} className="btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
