import { apiClient } from '@/api/client';
import type {
  AIAuditOut,
  TicketAreaReassignRequest,
  TicketCreate,
  TicketDetailResponse,
  TicketListFilters,
  TicketListOut,
  TicketListResponse,
  TicketPriorityChangeRequest,
  TicketResponse,
  TicketTypeChangeRequest,
} from '@/types/api';

export async function createTicket(payload: TicketCreate): Promise<TicketResponse> {
  const { data } = await apiClient.post<TicketResponse>('/pqrs/', payload);
  return data;
}

export async function listTickets(filters: TicketListFilters = {}): Promise<TicketListResponse> {
  const params: Record<string, string | number | boolean> = {};
  if (filters.ticket_type) params.ticket_type = filters.ticket_type;
  if (filters.status) params.status = filters.status;
  if (filters.area_id) params.area_id = filters.area_id;
  if (filters.priority) params.priority = filters.priority;
  if (filters.limit !== undefined) params.limit = filters.limit;
  if (filters.offset !== undefined) params.offset = filters.offset;
  if (filters.needs_sla_validation !== undefined) {
    params.needs_sla_validation = filters.needs_sla_validation;
  }

  const { data } = await apiClient.get<TicketListResponse | TicketListOut[]>('/pqrs/', {
    params,
  });

  if (Array.isArray(data)) {
    return {
      items: data,
      total: data.length,
      limit: filters.limit ?? data.length,
      offset: filters.offset ?? 0,
    };
  }
  return data;
}

export async function getTicketDetail(ticketId: string): Promise<TicketDetailResponse> {
  const { data } = await apiClient.get<TicketDetailResponse>(
    `/pqrs/${encodeURIComponent(ticketId)}`,
  );
  return data;
}

export async function getTicketAudit(trackingNumber: string): Promise<AIAuditOut> {
  const { data } = await apiClient.get<AIAuditOut>(
    `/pqrs/${encodeURIComponent(trackingNumber)}/audit`,
  );
  return data;
}

export async function getTicketAiAuditHistory(ticketId: string): Promise<AIAuditOut[]> {
  const { data } = await apiClient.get<AIAuditOut[]>(
    `/pqrs/${encodeURIComponent(ticketId)}/auditoria-ia`,
  );
  return data;
}

export async function reassignTicketArea(
  ticketId: string,
  payload: TicketAreaReassignRequest,
): Promise<TicketResponse> {
  const { data } = await apiClient.patch<TicketResponse>(
    `/pqrs/${encodeURIComponent(ticketId)}/area`,
    payload,
  );
  return data;
}

export async function changeTicketPriority(
  ticketId: string,
  payload: TicketPriorityChangeRequest,
): Promise<TicketResponse> {
  const { data } = await apiClient.patch<TicketResponse>(
    `/pqrs/${encodeURIComponent(ticketId)}/prioridad`,
    payload,
  );
  return data;
}

export async function changeTicketType(
  trackingNumber: string,
  payload: TicketTypeChangeRequest,
): Promise<TicketResponse> {
  const { data } = await apiClient.patch<TicketResponse>(
    `/pqrs/${encodeURIComponent(trackingNumber)}/tipo`,
    payload,
  );
  return data;
}
