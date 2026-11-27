export type FuncionarioRole = 'ANALISTA' | 'SUPERVISOR' | 'MASTER';

export type TicketType =
  | 'PETITION'
  | 'COMPLAINT'
  | 'CLAIM'
  | 'SUGGESTION'
  | 'INFORMATION_REQUEST'
  | 'CONSULTATION';

export type TicketPriority = 'HIGH' | 'MEDIUM' | 'LOW';

export type TicketStatus = 'RECEIVED' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';

export type AlertLevel = 'OVERDUE' | 'DUE_SOON' | 'NORMAL' | 'NO_DUE_DATE';

export type DocumentType = 'CC' | 'CE' | 'NIT' | 'PASSPORT' | 'TI';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  role: FuncionarioRole;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface LogoutResponse {
  message: string;
}

export interface FuncionarioOut {
  id: string;
  username: string;
  full_name: string | null;
  role: FuncionarioRole;
  area_id: string | null;
  is_active: boolean;
}

export interface FuncionarioCreate {
  username: string;
  password: string;
  full_name?: string | null;
  role: FuncionarioRole;
  area_id?: string | null;
}

export interface AreaSummary {
  id: string;
  code: string;
  name: string;
}

export interface AreaOut {
  id: string;
  code: string;
  name: string;
  description: string | null;
  manager_email: string | null;
  is_active: boolean;
  is_default: boolean;
}

export interface AreaCreate {
  code: string;
  name: string;
  description?: string | null;
  manager_email?: string | null;
  is_active?: boolean;
}

export interface AreaUpdate {
  name?: string | null;
  description?: string | null;
  manager_email?: string | null;
  is_active?: boolean | null;
}

export interface ClaimantCreate {
  full_name: string;
  document_type: DocumentType;
  document_number: string;
  email: string;
  phone: string;
}

export interface TicketCreate {
  claimant: ClaimantCreate;
  free_text: string;
}

export interface TicketResponse {
  tracking_number: string;
  status: TicketStatus | string;
  ticket_type: TicketType;
  priority: TicketPriority;
  filing_date: string;
  due_date: string | null;
  needs_sla_validation: boolean;
  area: AreaSummary | null;
}

export interface TicketTypeChangeRequest {
  ticket_type: TicketType;
  responsible_user: string;
  change_reason?: string | null;
}

export interface TicketListOut {
  id: string;
  tracking_number: string;
  ticket_type: TicketType | string;
  priority: TicketPriority | string;
  status: TicketStatus | string;
  due_date: string | null;
  area: AreaSummary | null;
  created_at: string;
}

export interface TicketListResponse {
  items: TicketListOut[];
  total: number;
  limit: number;
  offset: number;
}

export interface TicketListFilters {
  ticket_type?: TicketType;
  status?: TicketStatus;
  area_id?: string;
  priority?: TicketPriority;
  needs_sla_validation?: boolean;
  limit?: number;
  offset?: number;
}

export interface AIAuditOut {
  id: string;
  ticket_id: string;
  provider: string;
  ai_model: string;
  original_text: string;
  sanitized_text: string;
  decision_justification: string;
  suggested_type: string;
  suggested_priority: string;
  suggested_area_code: string;
  confidence: number | null;
  tokens_used: number | null;
  latency_ms: number | null;
  raw_response: Record<string, unknown> | null;
  created_at: string;
}

export interface TicketAlertOut {
  id: string;
  tracking_number: string;
  status: TicketStatus | string;
  due_date: string | null;
  alert_level: AlertLevel;
  days_remaining: number | null;
}

export interface SourceCount {
  openai: number;
  heuristic: number;
  fallback: number;
}

export interface PeriodStats {
  total: number;
  by_source: SourceCount;
}

export interface StatsResponse {
  last_24h: PeriodStats;
  all_time: PeriodStats;
}

/**
 * TODO(backend-hu16): Agregar tipo para ChangeAudit y detalle completo cuando exista
 * GET /api/v1/pqrs/{tracking_number} con historial humano.
 */
export interface ChangeAuditEvent {
  id: string;
  actor: 'IA' | 'HUMANO';
  title: string;
  subtitle: string;
  timestamp: string;
  justification?: string;
  metadata?: Record<string, string | number | null | undefined>;
}

export interface NormalizedApiError {
  status: number;
  message: string;
  fieldErrors: Record<string, string>;
}
