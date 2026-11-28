import { Badge } from '@/components/ui/badge';
import {
  getAlertLevelLabel,
  getPriorityLabel,
  getRoleLabel,
  getStatusLabel,
  getTicketTypeLabel,
} from '@/lib/labels';
import type { AlertLevel, FuncionarioRole, TicketPriority, TicketStatus } from '@/types/api';

export function PriorityBadge({ priority }: { priority: TicketPriority | string }) {
  const variant =
    priority === 'HIGH' ? 'destructive' : priority === 'MEDIUM' ? 'warning' : 'success';
  return <Badge variant={variant}>{getPriorityLabel(priority)}</Badge>;
}

export function StatusBadge({ status }: { status: TicketStatus | string }) {
  const variant =
    status === 'RECEIVED'
      ? 'info'
      : status === 'IN_PROGRESS'
        ? 'warning'
        : status === 'RESOLVED'
          ? 'success'
          : 'secondary';
  return <Badge variant={variant}>{getStatusLabel(status)}</Badge>;
}

export function TicketTypeBadge({ ticketType }: { ticketType: string }) {
  return <Badge variant="outline">{getTicketTypeLabel(ticketType)}</Badge>;
}

export function AlertLevelBadge({ level }: { level: AlertLevel | string }) {
  const variant =
    level === 'OVERDUE'
      ? 'destructive'
      : level === 'DUE_SOON'
        ? 'warning'
        : level === 'NORMAL'
          ? 'success'
          : 'secondary';
  return <Badge variant={variant}>{getAlertLevelLabel(level)}</Badge>;
}

export function RoleBadge({ role }: { role: FuncionarioRole | string }) {
  const variant = role === 'MASTER' ? 'default' : role === 'SUPERVISOR' ? 'info' : 'secondary';
  return <Badge variant={variant}>{getRoleLabel(role)}</Badge>;
}
