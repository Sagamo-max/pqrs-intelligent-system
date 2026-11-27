import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import { listAlerts } from '@/api/alerts';
import { EmptyState } from '@/components/common/EmptyState';
import { AlertLevelBadge, StatusBadge } from '@/components/common/StatusBadges';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDateCO } from '@/lib/dates';
import { normalizeApiError } from '@/lib/errors';
import { ALERT_LEVEL_LABELS } from '@/lib/labels';
import type { AlertLevel } from '@/types/api';

export function AlertsPage() {
  const [level, setLevel] = useState<string>('CRITICAL');

  const alertsQuery = useQuery({
    queryKey: ['alerts', level],
    queryFn: () =>
      listAlerts({
        level: level === 'CRITICAL' ? undefined : (level as AlertLevel),
        limit: 100,
      }),
  });

  const alerts = alertsQuery.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Alertas de vencimiento SLA</h1>
          <p className="text-sm text-muted-foreground">
            Solicitudes abiertas vencidas o próximas a vencer dentro de los próximos 3 días
            hábiles.
          </p>
        </div>

        <div className="w-full space-y-1.5 sm:w-64">
          <Label htmlFor="alert-level-select">Nivel de alerta</Label>
          <Select value={level} onValueChange={setLevel}>
            <SelectTrigger id="alert-level-select" aria-label="Filtrar nivel de alerta">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="CRITICAL">Críticas (Vencidas + Próximas)</SelectItem>
              {(Object.keys(ALERT_LEVEL_LABELS) as AlertLevel[]).map((key) => (
                <SelectItem key={key} value={key}>
                  {ALERT_LEVEL_LABELS[key]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {alertsQuery.isLoading ? (
        <div className="space-y-3" aria-busy="true" aria-label="Cargando alertas">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : alertsQuery.isError ? (
        <Alert variant="destructive" role="alert">
          <AlertTitle>Error al consultar alertas</AlertTitle>
          <AlertDescription>{normalizeApiError(alertsQuery.error).message}</AlertDescription>
        </Alert>
      ) : alerts.length === 0 ? (
        <EmptyState
          icon={AlertTriangle}
          title="Sin alertas para este filtro"
          description="No hay PQRS que requieran atención urgente en el criterio seleccionado."
        />
      ) : (
        <>
          <div className="hidden overflow-x-auto rounded-lg border bg-card md:block">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-muted/50 text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Radicado</th>
                  <th className="px-4 py-3">Nivel</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3">Fecha límite</th>
                  <th className="px-4 py-3">Días restantes</th>
                  <th className="px-4 py-3 text-right">Detalle</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {alerts.map((item) => (
                  <tr key={item.id} className="hover:bg-muted/30">
                    <td className="px-4 py-3 font-semibold text-primary">
                      {item.tracking_number}
                    </td>
                    <td className="px-4 py-3">
                      <AlertLevelBadge level={item.alert_level} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="px-4 py-3">{formatDateCO(item.due_date)}</td>
                    <td className="px-4 py-3 font-medium">
                      {item.days_remaining === null
                        ? 'Sin SLA'
                        : item.days_remaining < 0
                          ? `Vencida hace ${Math.abs(item.days_remaining)} días`
                          : `${item.days_remaining} días`}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button asChild size="sm" variant="outline">
                        <Link to={`/admin/pqrs/${encodeURIComponent(item.tracking_number)}`}>
                          <Eye className="h-4 w-4" aria-hidden="true" />
                          Revisar
                        </Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid gap-3 md:hidden">
            {alerts.map((item) => (
              <Card key={item.id}>
                <CardContent className="space-y-2.5 pt-5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-primary">{item.tracking_number}</span>
                    <AlertLevelBadge level={item.alert_level} />
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>Vence: {formatDateCO(item.due_date)}</span>
                    <StatusBadge status={item.status} />
                  </div>
                  <div className="pt-2">
                    <Button asChild size="sm" variant="outline" className="w-full">
                      <Link to={`/admin/pqrs/${encodeURIComponent(item.tracking_number)}`}>
                        Revisar detalle
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
