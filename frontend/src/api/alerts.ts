import { apiClient } from '@/api/client';
import type { AlertLevel, TicketAlertOut } from '@/types/api';

export interface AlertsParams {
  level?: AlertLevel;
  limit?: number;
  offset?: number;
}

export async function listAlerts(params: AlertsParams = {}): Promise<TicketAlertOut[]> {
  const { data } = await apiClient.get<TicketAlertOut[]>('/pqrs/alerts', {
    params,
  });
  return data;
}
