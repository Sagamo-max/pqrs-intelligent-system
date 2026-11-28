import type {
  AlertLevel,
  DocumentType,
  FuncionarioRole,
  TicketPriority,
  TicketStatus,
  TicketType,
} from '@/types/api';

export const TICKET_TYPE_LABELS: Record<TicketType, string> = {
  PETITION: 'Petición',
  COMPLAINT: 'Queja',
  CLAIM: 'Reclamo',
  SUGGESTION: 'Sugerencia',
  INFORMATION_REQUEST: 'Solicitud de información',
  CONSULTATION: 'Consulta',
};

export const TICKET_PRIORITY_LABELS: Record<TicketPriority, string> = {
  HIGH: 'Alta',
  MEDIUM: 'Media',
  LOW: 'Baja',
};

export const TICKET_STATUS_LABELS: Record<TicketStatus, string> = {
  RECEIVED: 'Recibida',
  IN_PROGRESS: 'En proceso',
  RESOLVED: 'Resuelta',
  CLOSED: 'Cerrada',
};

export const ALERT_LEVEL_LABELS: Record<AlertLevel, string> = {
  OVERDUE: 'Vencida',
  DUE_SOON: 'Próxima a vencer',
  NORMAL: 'A tiempo',
  NO_DUE_DATE: 'Sin fecha límite',
};

export const ROLE_LABELS: Record<FuncionarioRole, string> = {
  ANALISTA: 'Analista',
  SUPERVISOR: 'Supervisor',
  MASTER: 'Master',
};

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  CC: 'Cédula de Ciudadanía (CC)',
  CE: 'Cédula de Extranjería (CE)',
  NIT: 'NIT',
  PASSPORT: 'Pasaporte',
  TI: 'Tarjeta de Identidad (TI)',
};

export function getTicketTypeLabel(value: string): string {
  return TICKET_TYPE_LABELS[value as TicketType] ?? value;
}

export function getPriorityLabel(value: string): string {
  return TICKET_PRIORITY_LABELS[value as TicketPriority] ?? value;
}

export function getStatusLabel(value: string): string {
  return TICKET_STATUS_LABELS[value as TicketStatus] ?? value;
}

export function getAlertLevelLabel(value: string): string {
  return ALERT_LEVEL_LABELS[value as AlertLevel] ?? value;
}

export function getRoleLabel(value: string): string {
  return ROLE_LABELS[value as FuncionarioRole] ?? value;
}
