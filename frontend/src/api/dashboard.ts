import { apiClient } from '@/api/client';
import type { DashboardMetricsResponse, StatsResponse } from '@/types/api';

export async function fetchDashboardMetrics(): Promise<DashboardMetricsResponse> {
  const { data } = await apiClient.get<DashboardMetricsResponse>('/dashboard/metricas');
  return data;
}

export async function getClassificationStats(): Promise<StatsResponse> {
  const { data } = await apiClient.get<StatsResponse>('/pqrs/stats');
  return data;
}
