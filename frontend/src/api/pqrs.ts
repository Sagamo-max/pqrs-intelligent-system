import { apiClient } from '@/api/client';
import type {
  AIAuditOut,
  TicketCreate,
  TicketListFilters,
  TicketListOut,
  TicketListResponse,
  TicketResponse,
  TicketTypeChangeRequest,
} from '@/types/api';

/**
 * TODO(backend-public-radicar): `POST /api/v1/pqrs/` actualmente tiene `Depends(get_current_user)`
 * en `backend/app/routers/ticket.py`. Cuando el backend exponga la ruta como pública, /radicar
 * funcionará para ciudadanos sin iniciar sesión.
 */
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

export async function findTicketByTracking(trackingNumber: string): Promise<TicketListOut | null> {
  // TODO(backend-hu16): Reemplazar por `GET /api/v1/pqrs/{tracking_number}` cuando esté disponible.
  const response = await listTickets({ limit: 100, offset: 0 });
  return response.items.find((item) => item.tracking_number === trackingNumber) ?? null;
}

/**
 * Nota: El backend expone `GET /api/v1/pqrs/{tracking_number}/audit` (no `/auditoria-ia`).
 */
export async function getTicketAudit(trackingNumber: string): Promise<AIAuditOut> {
  const { data } = await apiClient.get<AIAuditOut>(
    `/pqrs/${encodeURIComponent(trackingNumber)}/audit`,
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

/**
 * TODO(backend-hu15): Implementar consumo real de `PATCH /api/v1/pqrs/{ticket_id}/area`
 * cuando el endpoint exista en `backend/app/routers/ticket.py`.
 *
 * TODO(backend-hu18): Implementar consumo real de `PATCH /api/v1/pqrs/{ticket_id}/prioridad`
 * cuando el endpoint exista en `backend/app/routers/ticket.py`.
 */
