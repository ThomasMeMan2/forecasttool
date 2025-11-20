/**
 * API client for Forecast Studio backend
 */
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // ============= Projects =============
  async getProjects(includeArchived: boolean = false) {
    const response = await this.client.get('/projects/', {
      params: { include_archived: includeArchived },
    });
    return response.data;
  }

  async getProject(projectId: number) {
    const response = await this.client.get(`/projects/${projectId}`);
    return response.data;
  }

  async createProject(data: { name: string; description?: string }) {
    const response = await this.client.post('/projects/', data);
    return response.data;
  }

  async updateProject(
    projectId: number,
    data: { name?: string; description?: string; is_archived?: boolean }
  ) {
    const response = await this.client.put(`/projects/${projectId}`, data);
    return response.data;
  }

  async deleteProject(projectId: number) {
    const response = await this.client.delete(`/projects/${projectId}`);
    return response.data;
  }

  async duplicateProject(projectId: number) {
    const response = await this.client.post(`/projects/${projectId}/duplicate`);
    return response.data;
  }

  // ============= Datasets =============
  async uploadDataset(projectId: number, file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post(
      `/datasets/${projectId}/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  async getDatasets(projectId: number) {
    const response = await this.client.get(`/datasets/${projectId}/datasets`);
    return response.data;
  }

  async getTimeseries(projectId: number) {
    const response = await this.client.get(`/datasets/${projectId}/timeseries`);
    return response.data;
  }

  async getTimeseriesData(projectId: number, tsId: string) {
    const response = await this.client.get(
      `/datasets/${projectId}/timeseries/${tsId}/data`
    );
    return response.data;
  }

  // ============= Forecasts =============
  async generateForecasts(
    projectId: number,
    data: {
      timeseries_ids?: string[];
      horizon?: number;
      confidence_level?: number;
    }
  ) {
    const response = await this.client.post(
      `/forecasts/${projectId}/generate`,
      data
    );
    return response.data;
  }

  async getForecasts(projectId: number, timeseriesId?: number) {
    const response = await this.client.get(`/forecasts/${projectId}/forecasts`, {
      params: timeseriesId ? { timeseries_id: timeseriesId } : {},
    });
    return response.data;
  }

  async getForecast(projectId: number, forecastId: number) {
    const response = await this.client.get(
      `/forecasts/${projectId}/forecasts/${forecastId}`
    );
    return response.data;
  }

  async deleteForecast(projectId: number, forecastId: number) {
    const response = await this.client.delete(
      `/forecasts/${projectId}/forecasts/${forecastId}`
    );
    return response.data;
  }

  async exportForecastCSV(projectId: number, forecastId: number) {
    const response = await this.client.get(
      `/forecasts/${projectId}/forecasts/${forecastId}/export`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  }

  // ============= Phase 2: Events =============
  async createGlobalEvent(projectId: number, data: any) {
    const response = await this.client.post(`/events/${projectId}/global-events`, data);
    return response.data;
  }

  async getGlobalEvents(projectId: number, eventType?: string) {
    const response = await this.client.get(`/events/${projectId}/global-events`, {
      params: eventType ? { event_type: eventType } : {},
    });
    return response.data;
  }

  async updateGlobalEvent(projectId: number, eventId: number, data: any) {
    const response = await this.client.put(`/events/${projectId}/global-events/${eventId}`, data);
    return response.data;
  }

  async deleteGlobalEvent(projectId: number, eventId: number) {
    const response = await this.client.delete(`/events/${projectId}/global-events/${eventId}`);
    return response.data;
  }

  async createIDEvent(projectId: number, data: any) {
    const response = await this.client.post(`/events/${projectId}/id-events`, data);
    return response.data;
  }

  async getIDEvents(projectId: number, timeseriesId?: number, eventType?: string) {
    const params: any = {};
    if (timeseriesId) params.timeseries_id = timeseriesId;
    if (eventType) params.event_type = eventType;
    const response = await this.client.get(`/events/${projectId}/id-events`, { params });
    return response.data;
  }

  async updateIDEvent(projectId: number, eventId: number, data: any) {
    const response = await this.client.put(`/events/${projectId}/id-events/${eventId}`, data);
    return response.data;
  }

  async deleteIDEvent(projectId: number, eventId: number) {
    const response = await this.client.delete(`/events/${projectId}/id-events/${eventId}`);
    return response.data;
  }

  // ============= Phase 2: Exclusions =============
  async createExclusion(projectId: number, data: any) {
    const response = await this.client.post(`/exclusions/${projectId}/exclusions`, data);
    return response.data;
  }

  async getExclusions(projectId: number, timeseriesId?: number, activeOnly: boolean = true) {
    const params: any = { active_only: activeOnly };
    if (timeseriesId) params.timeseries_id = timeseriesId;
    const response = await this.client.get(`/exclusions/${projectId}/exclusions`, { params });
    return response.data;
  }

  async updateExclusion(projectId: number, exclusionId: number, data: any) {
    const response = await this.client.put(`/exclusions/${projectId}/exclusions/${exclusionId}`, data);
    return response.data;
  }

  async deleteExclusion(projectId: number, exclusionId: number) {
    const response = await this.client.delete(`/exclusions/${projectId}/exclusions/${exclusionId}`);
    return response.data;
  }

  // ============= Phase 2: Adjustments =============
  async createAdjustment(projectId: number, data: any) {
    const response = await this.client.post(`/adjustments/${projectId}/adjustments`, data);
    return response.data;
  }

  async getAdjustments(projectId: number, forecastId: number) {
    const response = await this.client.get(`/adjustments/${projectId}/forecasts/${forecastId}/adjustments`);
    return response.data;
  }

  async deleteAdjustment(projectId: number, adjustmentId: number) {
    const response = await this.client.delete(`/adjustments/${projectId}/adjustments/${adjustmentId}`);
    return response.data;
  }

  // ============= Phase 3: Diagnostics =============
  async getTimeseriesDiagnostics(projectId: number, tsId: string, frequency: string = 'D') {
    const response = await this.client.get(`/diagnostics/${projectId}/timeseries/${tsId}/diagnostics`, {
      params: { frequency }
    });
    return response.data;
  }

  async getForecastResiduals(projectId: number, forecastId: number) {
    const response = await this.client.get(`/diagnostics/${projectId}/forecasts/${forecastId}/residuals`);
    return response.data;
  }

  async getTimeseriesSummary(projectId: number, tsId: string) {
    const response = await this.client.get(`/diagnostics/${projectId}/timeseries/${tsId}/summary`);
    return response.data;
  }

  // ============= Phase 3: LLM Insights =============
  async generateHistoryInsight(projectId: number, tsId: string) {
    const response = await this.client.post(`/insights/${projectId}/timeseries/${tsId}/insights/history`);
    return response.data;
  }

  async generateForecastInsight(projectId: number, forecastId: number) {
    const response = await this.client.post(`/insights/${projectId}/forecasts/${forecastId}/insights/forecast`);
    return response.data;
  }

  async generateQualityInsight(projectId: number, forecastId: number) {
    const response = await this.client.post(`/insights/${projectId}/forecasts/${forecastId}/insights/quality`);
    return response.data;
  }

  async getProjectInsights(projectId: number, filters?: {
    insight_type?: string;
    timeseries_id?: number;
    forecast_id?: number;
    limit?: number;
  }) {
    const response = await this.client.get(`/insights/${projectId}/insights`, {
      params: filters
    });
    return response.data;
  }

  async deleteInsight(projectId: number, insightId: number) {
    const response = await this.client.delete(`/insights/${projectId}/insights/${insightId}`);
    return response.data;
  }

  // ============= Phase 3: Enhanced Forecasts =============
  async generateEnhancedForecasts(
    projectId: number,
    data: {
      timeseries_ids?: string[];
      horizon: number;
      confidence_level: number;
    },
    options?: {
      use_events?: boolean;
      use_exclusions?: boolean;
      models?: string[];
    }
  ) {
    const response = await this.client.post(
      `/forecasts/${projectId}/generate-enhanced`,
      data,
      { params: options }
    );
    return response.data;
  }
}

export const api = new ApiClient();
export default api;
