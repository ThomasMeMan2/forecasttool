'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { UserExclusion, TimeSeries } from '@/types';
import { Ban, Plus, Trash2, Eye, EyeOff } from 'lucide-react';

interface ExclusionsManagerProps {
  projectId: number;
  timeseries: TimeSeries[];
  onRefresh?: () => void;
}

export default function ExclusionsManager({
  projectId,
  timeseries,
  onRefresh,
}: ExclusionsManagerProps) {
  const [exclusions, setExclusions] = useState<UserExclusion[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showInactive, setShowInactive] = useState(false);

  const [formData, setFormData] = useState({
    timeseries_id: 0,
    start_date: '',
    end_date: '',
    reason: '',
  });

  useEffect(() => {
    loadExclusions();
  }, [projectId, showInactive]);

  const loadExclusions = async () => {
    try:
      setLoading(true);
      const data = await api.getExclusions(projectId, undefined, !showInactive);
      setExclusions(data);
    } catch (err) {
      console.error('Failed to load exclusions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.timeseries_id) {
      alert('Please select a timeseries');
      return;
    }

    if (new Date(formData.start_date) >= new Date(formData.end_date)) {
      alert('Start date must be before end date');
      return;
    }

    try {
      await api.createExclusion(projectId, formData);
      setFormData({
        timeseries_id: 0,
        start_date: '',
        end_date: '',
        reason: '',
      });
      setShowAddModal(false);
      loadExclusions();
      onRefresh?.();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create exclusion');
    }
  };

  const toggleActive = async (exclusion: UserExclusion) => {
    try {
      await api.updateExclusion(projectId, exclusion.id, {
        is_active: !exclusion.is_active,
      });
      loadExclusions();
      onRefresh?.();
    } catch (err) {
      alert('Failed to update exclusion');
    }
  };

  const handleDelete = async (exclusionId: number) => {
    if (!confirm('Are you sure you want to delete this exclusion?')) return;

    try {
      await api.deleteExclusion(projectId, exclusionId);
      loadExclusions();
      onRefresh?.();
    } catch (err) {
      alert('Failed to delete exclusion');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Manual Exclusions</h2>
          <p className="text-sm text-gray-600 mt-1">
            Exclude periods from forecast training
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowInactive(!showInactive)}
            className="btn-secondary flex items-center gap-2"
          >
            {showInactive ? <Eye size={18} /> : <EyeOff size={18} />}
            {showInactive ? 'Active Only' : 'Show All'}
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus size={20} />
            Add Exclusion
          </button>
        </div>
      </div>

      {/* Exclusions List */}
      <div className="card p-6">
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : exclusions.length === 0 ? (
          <p className="text-center text-gray-500 py-8">No exclusions yet</p>
        ) : (
          <div className="space-y-3">
            {exclusions.map((exclusion) => {
              const ts = timeseries.find((t) => t.id === exclusion.timeseries_id);
              return (
                <div
                  key={exclusion.id}
                  className={`flex items-start justify-between p-4 rounded-lg ${
                    exclusion.is_active ? 'bg-yellow-50' : 'bg-gray-50 opacity-60'
                  }`}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Ban
                        size={16}
                        className={exclusion.is_active ? 'text-yellow-600' : 'text-gray-400'}
                      />
                      <h3 className="font-medium text-gray-900">
                        {ts?.ts_id || `TS #${exclusion.timeseries_id}`}
                      </h3>
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          exclusion.is_active
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-gray-200 text-gray-600'
                        }`}
                      >
                        {exclusion.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {new Date(exclusion.start_date).toLocaleDateString()} -{' '}
                      {new Date(exclusion.end_date).toLocaleDateString()}
                    </p>
                    <p className="text-sm text-gray-700 mt-1 italic">
                      Reason: {exclusion.reason}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => toggleActive(exclusion)}
                      className="text-blue-600 hover:text-blue-700"
                      title={exclusion.is_active ? 'Deactivate' : 'Activate'}
                    >
                      {exclusion.is_active ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                    <button
                      onClick={() => handleDelete(exclusion.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Add Exclusion Period</h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="label">Timeseries *</label>
                <select
                  value={formData.timeseries_id}
                  onChange={(e) =>
                    setFormData({ ...formData, timeseries_id: parseInt(e.target.value) })
                  }
                  className="input"
                  required
                >
                  <option value={0}>Select timeseries...</option>
                  {timeseries.map((ts) => (
                    <option key={ts.id} value={ts.id}>
                      {ts.ts_id}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Start Date *</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="label">End Date *</label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="label">Reason *</label>
                <textarea
                  value={formData.reason}
                  onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                  className="input"
                  rows={3}
                  placeholder="e.g., COVID-19 lockdown, data collection error, store closure..."
                  required
                />
              </div>

              <div className="flex gap-3">
                <button type="submit" className="btn-primary flex-1">
                  Create Exclusion
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
