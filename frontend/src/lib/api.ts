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
}

export const api = new ApiClient();
export default api;
