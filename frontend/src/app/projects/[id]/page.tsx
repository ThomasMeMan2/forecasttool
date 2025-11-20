'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import api from '@/lib/api';
import { Project, Dataset, TimeSeries, Forecast } from '@/types';
import {
  ArrowLeft,
  Upload,
  TrendingUp,
  FileText,
  Download,
  AlertCircle,
  Calendar,
  Ban,
} from 'lucide-react';
import DataUpload from '@/components/DataUpload';
import ForecastView from '@/components/ForecastView';
import EventsManager from '@/components/EventsManager';
import ExclusionsManager from '@/components/ExclusionsManager';

export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = parseInt(params.id as string);

  const [project, setProject] = useState<Project | null>(null);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [timeseries, setTimeseries] = useState<TimeSeries[]>([]);
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'data' | 'forecast' | 'events' | 'exclusions'>('data');

  useEffect(() => {
    loadProjectData();
  }, [projectId]);

  const loadProjectData = async () => {
    try {
      setLoading(true);
      const [projectData, datasetsData, timeseriesData, forecastsData] =
        await Promise.all([
          api.getProject(projectId),
          api.getDatasets(projectId),
          api.getTimeseries(projectId),
          api.getForecasts(projectId),
        ]);

      setProject(projectData);
      setDatasets(datasetsData);
      setTimeseries(timeseriesData);
      setForecasts(forecastsData);
    } catch (err: any) {
      setError(err.message || 'Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  const handleDataUploaded = () => {
    loadProjectData();
  };

  const handleForecastGenerated = () => {
    loadProjectData();
    setActiveTab('forecast');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-gray-600">Loading project...</p>
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error || 'Project not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <button
            onClick={() => router.push('/')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft size={20} className="mr-1" />
            Back to Projects
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {project.name}
              </h1>
              {project.description && (
                <p className="mt-1 text-sm text-gray-500">
                  {project.description}
                </p>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="mt-6 grid grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center text-gray-600 mb-1">
                <FileText size={20} className="mr-2" />
                <span className="text-sm">Datasets</span>
              </div>
              <p className="text-2xl font-semibold text-gray-900">
                {datasets.length}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center text-gray-600 mb-1">
                <TrendingUp size={20} className="mr-2" />
                <span className="text-sm">Timeseries</span>
              </div>
              <p className="text-2xl font-semibold text-gray-900">
                {timeseries.length}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center text-gray-600 mb-1">
                <TrendingUp size={20} className="mr-2" />
                <span className="text-sm">Forecasts</span>
              </div>
              <p className="text-2xl font-semibold text-gray-900">
                {forecasts.length}
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('data')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'data'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Upload size={16} className="inline mr-2" />
              Data Upload
            </button>
            <button
              onClick={() => setActiveTab('forecast')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'forecast'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <TrendingUp size={16} className="inline mr-2" />
              Forecasts
            </button>
            <button
              onClick={() => setActiveTab('events')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'events'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Calendar size={16} className="inline mr-2" />
              Events
              <span className="ml-1 text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">Phase 2</span>
            </button>
            <button
              onClick={() => setActiveTab('exclusions')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'exclusions'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Ban size={16} className="inline mr-2" />
              Exclusions
              <span className="ml-1 text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">Phase 2</span>
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'data' ? (
          <DataUpload
            projectId={projectId}
            datasets={datasets}
            timeseries={timeseries}
            onDataUploaded={handleDataUploaded}
            onGenerateForecast={handleForecastGenerated}
          />
        ) : activeTab === 'forecast' ? (
          <ForecastView
            projectId={projectId}
            forecasts={forecasts}
            timeseries={timeseries}
            onRefresh={loadProjectData}
          />
        ) : activeTab === 'events' ? (
          <EventsManager
            projectId={projectId}
            timeseries={timeseries}
            onRefresh={loadProjectData}
          />
        ) : (
          <ExclusionsManager
            projectId={projectId}
            timeseries={timeseries}
            onRefresh={loadProjectData}
          />
        )}
      </main>
    </div>
  );
}
