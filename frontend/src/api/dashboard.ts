import { listAlerts } from '@/api/alerts';
import { listAreas } from '@/api/areas';
import { apiClient } from '@/api/client';
import { listTickets } from '@/api/pqrs';
import { getPriorityLabel, getTicketTypeLabel } from '@/lib/labels';
import type { AreaOut, StatsResponse, TicketAlertOut, TicketListOut } from '@/types/api';

export interface ChartDatum {
  name: string;
  value: number;
}

export interface DashboardMetrics {
  totalTickets: number;
  overdueCount: number;
  dueSoonCount: number;
  onTimeCount: number;
  classificationStats: StatsResponse;
  byType: ChartDatum[];
  byPriority: ChartDatum[];
  byArea: ChartDatum[];
  slaBreakdown: ChartDatum[];
  sourceBreakdown: ChartDatum[];
  recentTrend: Array<{ label: string; total: number }>;
  sampleSize: number;
}

export async function getClassificationStats(): Promise<StatsResponse> {
  const { data } = await apiClient.get<StatsResponse>('/pqrs/stats');
  return data;
}

function buildTrend(items: TicketListOut[]): Array<{ label: string; total: number }> {
  const counts = new Map<string, number>();
  for (const item of items) {
    const day = item.created_at ? item.created_at.slice(0, 10) : 'Sin fecha';
    counts.set(day, (counts.get(day) ?? 0) + 1);
  }
  const entries = Array.from(counts.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-7)
    .map(([label, total]) => ({ label: label.slice(5), total }));

  return entries.length > 0 ? entries : [{ label: 'Hoy', total: 0 }];
}

/**
 * TODO(backend-hu19): Reemplazar esta agregación cliente cuando exista
 * `GET /api/v1/dashboard/metricas` en el backend.
 */
export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  const [stats, ticketsPage, overdue, dueSoon, normal, noDueDate, areas] = await Promise.all([
    getClassificationStats(),
    listTickets({ limit: 100, offset: 0 }),
    listAlerts({ level: 'OVERDUE', limit: 200 }),
    listAlerts({ level: 'DUE_SOON', limit: 200 }),
    listAlerts({ level: 'NORMAL', limit: 200 }),
    listAlerts({ level: 'NO_DUE_DATE', limit: 200 }),
    listAreas(),
  ]);

  const typeCounts = new Map<string, number>();
  const priorityCounts = new Map<string, number>();
  const areaCounts = new Map<string, number>();
  const areaNames = new Map<string, string>(areas.map((area: AreaOut) => [area.id, area.name]));

  for (const ticket of ticketsPage.items) {
    const typeName = getTicketTypeLabel(ticket.ticket_type);
    typeCounts.set(typeName, (typeCounts.get(typeName) ?? 0) + 1);

    const priorityName = getPriorityLabel(ticket.priority);
    priorityCounts.set(priorityName, (priorityCounts.get(priorityName) ?? 0) + 1);

    const areaLabel =
      ticket.area?.name ?? (ticket.area?.id ? areaNames.get(ticket.area.id) : undefined) ?? 'Sin área';
    areaCounts.set(areaLabel, (areaCounts.get(areaLabel) ?? 0) + 1);
  }

  const overdueCount = overdue.length;
  const dueSoonCount = dueSoon.length;
  const onTimeCount = normal.length + noDueDate.length;

  const toChartArray = (map: Map<string, number>): ChartDatum[] =>
    Array.from(map.entries())
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);

  const countAlerts = (list: TicketAlertOut[]) => list.length;

  return {
    totalTickets: ticketsPage.total,
    overdueCount,
    dueSoonCount,
    onTimeCount,
    classificationStats: stats,
    byType: toChartArray(typeCounts),
    byPriority: toChartArray(priorityCounts),
    byArea: toChartArray(areaCounts).slice(0, 8),
    slaBreakdown: [
      { name: 'A tiempo', value: countAlerts(normal) + countAlerts(noDueDate) },
      { name: 'Próximas a vencer', value: countAlerts(dueSoon) },
      { name: 'Vencidas', value: countAlerts(overdue) },
    ],
    sourceBreakdown: [
      { name: 'OpenAI', value: stats.all_time.by_source.openai },
      { name: 'Heurística', value: stats.all_time.by_source.heuristic },
      { name: 'Fallback', value: stats.all_time.by_source.fallback },
    ],
    recentTrend: buildTrend(ticketsPage.items),
    sampleSize: ticketsPage.items.length,
  };
}
