'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import api from '@/lib/api';
import { Dataset, TimeSeries } from '@/types';
import {
  Upload,
  FileText,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Play,
} from 'lucide-react';

interface DataUploadProps {
  projectId: number;
  datasets: Dataset[];
  timeseries: TimeSeries[];
  onDataUploaded: () => void;
  onGenerateForecast: () => void;
}

export default function DataUpload({
  projectId,
  datasets,
  timeseries,
  onDataUploaded,
  onGenerateForecast,
}: DataUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [generatingForecast, setGeneratingForecast] = useState(false);
  const [forecastParams, setForecastParams] = useState({
    horizon: 12,
    confidence_level: 90,
  });

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      setUploadError(null);
      setUploadSuccess(false);

      try {
        setUploading(true);
        await api.uploadDataset(projectId, file);
        setUploadSuccess(true);
        onDataUploaded();

        // Reset success message after 3 seconds
        setTimeout(() => setUploadSuccess(false), 3000);
      } catch (err: any) {
        setUploadError(
          err.response?.data?.detail || 'Failed to upload dataset'
        );
      } finally {
        setUploading(false);
      }
    },
    [projectId, onDataUploaded]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    multiple: false,
    disabled: uploading,
  });

  const handleGenerateForecast = async () => {
    try {
      setGeneratingForecast(true);
      setUploadError(null);

      await api.generateForecasts(projectId, {
        horizon: forecastParams.horizon,
        confidence_level: forecastParams.confidence_level,
      });

      onGenerateForecast();
    } catch (err: any) {
      setUploadError(
        err.response?.data?.detail || 'Failed to generate forecast'
      );
    } finally {
      setGeneratingForecast(false);
    }
  };

  const latestDataset = datasets[0];

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="card p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Upload Data
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Upload a CSV file with columns: <code className="bg-gray-100 px-2 py-1 rounded">id</code>,{' '}
          <code className="bg-gray-100 px-2 py-1 rounded">timestamp</code>,{' '}
          <code className="bg-gray-100 px-2 py-1 rounded">quantity</code>
        </p>

        {uploadError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 flex items-start">
            <AlertCircle size={20} className="text-red-600 mr-2 flex-shrink-0 mt-0.5" />
            <p className="text-red-800">{uploadError}</p>
          </div>
        )}

        {uploadSuccess && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4 flex items-start">
            <CheckCircle size={20} className="text-green-600 mr-2 flex-shrink-0 mt-0.5" />
            <p className="text-green-800">Dataset uploaded successfully!</p>
          </div>
        )}

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer ${
            isDragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-gray-400'
          } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input {...getInputProps()} />
          <Upload
            size={48}
            className={`mx-auto mb-4 ${
              isDragActive ? 'text-primary-600' : 'text-gray-400'
            }`}
          />
          {uploading ? (
            <p className="text-gray-600">Uploading...</p>
          ) : isDragActive ? (
            <p className="text-primary-600 font-medium">Drop CSV file here</p>
          ) : (
            <div>
              <p className="text-gray-600 font-medium mb-1">
                Drop CSV file here or click to browse
              </p>
              <p className="text-sm text-gray-500">Maximum file size: 50MB</p>
            </div>
          )}
        </div>
      </div>

      {/* Current Dataset Info */}
      {latestDataset && (
        <div className="card p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Current Dataset
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <p className="text-sm text-gray-600 mb-1">Filename</p>
              <p className="font-medium text-gray-900">{latestDataset.filename}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Rows</p>
              <p className="font-medium text-gray-900">
                {latestDataset.row_count.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Quality Score</p>
              <p className="font-medium text-gray-900">
                {latestDataset.quality_score?.toFixed(0) || 'N/A'}/100
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Uploaded</p>
              <p className="font-medium text-gray-900">
                {new Date(latestDataset.uploaded_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          {/* Quality Issues */}
          {(latestDataset.has_missing_values ||
            latestDataset.has_duplicates ||
            latestDataset.has_outliers) && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start">
                <AlertCircle size={20} className="text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-yellow-800 mb-2">
                    Data Quality Warnings:
                  </p>
                  <ul className="text-sm text-yellow-700 space-y-1">
                    {latestDataset.has_missing_values && (
                      <li>• Contains missing values</li>
                    )}
                    {latestDataset.has_duplicates && (
                      <li>• Contains duplicate entries</li>
                    )}
                    {latestDataset.has_outliers && (
                      <li>• Contains potential outliers</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Timeseries List */}
      {timeseries.length > 0 && (
        <div className="card p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Timeseries ({timeseries.length})
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Data Points
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Frequency
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date Range
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {timeseries.slice(0, 10).map((ts) => (
                  <tr key={ts.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {ts.ts_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {ts.data_points || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {ts.frequency || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {ts.data_start_date && ts.data_end_date
                        ? `${new Date(ts.data_start_date).toLocaleDateString()} - ${new Date(
                            ts.data_end_date
                          ).toLocaleDateString()}`
                        : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {timeseries.length > 10 && (
              <p className="text-sm text-gray-500 mt-2 text-center">
                Showing first 10 of {timeseries.length} timeseries
              </p>
            )}
          </div>
        </div>
      )}

      {/* Generate Forecast */}
      {timeseries.length > 0 && (
        <div className="card p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Generate Forecast
          </h2>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="label">Forecast Horizon (periods)</label>
              <input
                type="number"
                min="1"
                max="52"
                value={forecastParams.horizon}
                onChange={(e) =>
                  setForecastParams({
                    ...forecastParams,
                    horizon: parseInt(e.target.value) || 12,
                  })
                }
                className="input"
              />
              <p className="text-xs text-gray-500 mt-1">
                How many periods to forecast (1-52)
              </p>
            </div>

            <div>
              <label className="label">Confidence Level (%)</label>
              <select
                value={forecastParams.confidence_level}
                onChange={(e) =>
                  setForecastParams({
                    ...forecastParams,
                    confidence_level: parseInt(e.target.value),
                  })
                }
                className="input"
              >
                <option value="80">80%</option>
                <option value="90">90%</option>
                <option value="95">95%</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Prediction interval confidence
              </p>
            </div>
          </div>

          <button
            onClick={handleGenerateForecast}
            disabled={generatingForecast}
            className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generatingForecast ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Generating...
              </>
            ) : (
              <>
                <Play size={20} />
                Generate Forecasts
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
