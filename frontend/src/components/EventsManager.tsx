'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { GlobalEvent, IDSpecificEvent, TimeSeries } from '@/types';
import { Calendar, Plus, Trash2, Edit2, Globe, Target } from 'lucide-react';

interface EventsManagerProps {
  projectId: number;
  timeseries: TimeSeries[];
  onRefresh?: () => void;
}

export default function EventsManager({ projectId, timeseries, onRefresh }: EventsManagerProps) {
  const [activeTab, setActiveTab] = useState<'global' | 'specific'>('global');
  const [globalEvents, setGlobalEvents] = useState<GlobalEvent[]>([]);
  const [idEvents, setIDEvents] = useState<IDSpecificEvent[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    event_name: '',
    event_date: '',
    event_type: 'custom',
    description: '',
    timeseries_id: 0,
  });

  useEffect(() => {
    loadEvents();
  }, [projectId]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const [global, specific] = await Promise.all([
        api.getGlobalEvents(projectId),
        api.getIDEvents(projectId),
      ]);
      setGlobalEvents(global);
      setIDEvents(specific);
    } catch (err) {
      console.error('Failed to load events:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (activeTab === 'global') {
        await api.createGlobalEvent(projectId, {
          event_name: formData.event_name,
          event_date: formData.event_date,
          event_type: formData.event_type,
          description: formData.description,
        });
      } else {
        if (!formData.timeseries_id) {
          alert('Please select a timeseries');
          return;
        }
        await api.createIDEvent(projectId, {
          event_name: formData.event_name,
          event_date: formData.event_date,
          event_type: formData.event_type,
          description: formData.description,
          timeseries_id: formData.timeseries_id,
        });
      }

      // Reset form
      setFormData({
        event_name: '',
        event_date: '',
        event_type: 'custom',
        description: '',
        timeseries_id: 0,
      });
      setShowAddModal(false);
      loadEvents();
      onRefresh?.();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create event');
    }
  };

  const handleDelete = async (eventId: number, type: 'global' | 'specific') => {
    if (!confirm('Are you sure you want to delete this event?')) return;

    try {
      if (type === 'global') {
        await api.deleteGlobalEvent(projectId, eventId);
      } else {
        await api.deleteIDEvent(projectId, eventId);
      }
      loadEvents();
      onRefresh?.();
    } catch (err) {
      alert('Failed to delete event');
    }
  };

  const eventTypeOptions = activeTab === 'global'
    ? ['holiday', 'campaign', 'price_change', 'custom']
    : ['stockout', 'promotion', 'closure', 'custom'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Events Management</h2>
          <p className="text-sm text-gray-600 mt-1">
            Track events that influence forecasts
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus size={20} />
          Add Event
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('global')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'global'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Globe size={16} className="inline mr-2" />
            Global Events ({globalEvents.length})
          </button>
          <button
            onClick={() => setActiveTab('specific')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'specific'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Target size={16} className="inline mr-2" />
            ID-Specific Events ({idEvents.length})
          </button>
        </nav>
      </div>

      {/* Events List */}
      <div className="card p-6">
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <div className="space-y-3">
            {activeTab === 'global' ? (
              globalEvents.length === 0 ? (
                <p className="text-center text-gray-500 py-8">No global events yet</p>
              ) : (
                globalEvents.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-start justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Calendar size={16} className="text-gray-600" />
                        <h3 className="font-medium text-gray-900">{event.event_name}</h3>
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          {event.event_type}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">
                        {new Date(event.event_date).toLocaleDateString()}
                      </p>
                      {event.description && (
                        <p className="text-sm text-gray-500 mt-1">{event.description}</p>
                      )}
                    </div>
                    <button
                      onClick={() => handleDelete(event.id, 'global')}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                ))
              )
            ) : (
              idEvents.length === 0 ? (
                <p className="text-center text-gray-500 py-8">No ID-specific events yet</p>
              ) : (
                idEvents.map((event) => {
                  const ts = timeseries.find(t => t.id === event.timeseries_id);
                  return (
                    <div
                      key={event.id}
                      className="flex items-start justify-between p-4 bg-gray-50 rounded-lg"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Calendar size={16} className="text-gray-600" />
                          <h3 className="font-medium text-gray-900">{event.event_name}</h3>
                          <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                            {event.event_type}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">
                          {ts?.ts_id || `TS #${event.timeseries_id}`} • {new Date(event.event_date).toLocaleDateString()}
                        </p>
                        {event.description && (
                          <p className="text-sm text-gray-500 mt-1">{event.description}</p>
                        )}
                      </div>
                      <button
                        onClick={() => handleDelete(event.id, 'specific')}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  );
                })
              )
            )}
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">
              Add {activeTab === 'global' ? 'Global' : 'ID-Specific'} Event
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="label">Event Name *</label>
                <input
                  type="text"
                  value={formData.event_name}
                  onChange={(e) => setFormData({ ...formData, event_name: e.target.value })}
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="label">Event Date *</label>
                <input
                  type="date"
                  value={formData.event_date}
                  onChange={(e) => setFormData({ ...formData, event_date: e.target.value })}
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="label">Event Type</label>
                <select
                  value={formData.event_type}
                  onChange={(e) => setFormData({ ...formData, event_type: e.target.value })}
                  className="input"
                >
                  {eventTypeOptions.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>

              {activeTab === 'specific' && (
                <div>
                  <label className="label">Timeseries *</label>
                  <select
                    value={formData.timeseries_id}
                    onChange={(e) => setFormData({ ...formData, timeseries_id: parseInt(e.target.value) })}
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
              )}

              <div>
                <label className="label">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input"
                  rows={3}
                />
              </div>

              <div className="flex gap-3">
                <button type="submit" className="btn-primary flex-1">
                  Create Event
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
