import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle2, Clock, FileText, RefreshCw } from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { fetchDashboardMetrics, getClassificationStats } from '@/api/dashboard';
import { EmptyState } from '@/components/common/EmptyState';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDateTimeCO } from '@/lib/dates';
import { normalizeApiError } from '@/lib/errors';
import { getPriorityLabel, getTicketTypeLabel } from '@/lib/labels';
import { useAuthStore } from '@/stores/authStore';

const SLA_COLORS = ['#15803d', '#b91c1c', '#64748b'];
const SOURCE_COLORS = ['#1d4ed8', '#0f766e', '#d97706'];

export function DashboardPage() {
  const user = useAuthStore((state) => state.user);

  const metricsQuery = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: fetchDashboardMetrics,
  });

  const statsQuery = useQuery({
    queryKey: ['classification-stats'],
    queryFn: getClassificationStats,
  });

  if (metricsQuery.isLoading) {
    return (
      <div className="space-y-6" aria-busy="true" aria-label="Cargando métricas">
        <Skeleton className="h-9 w-64" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-80 w-full" />
          <Skeleton className="h-80 w-full" />
        </div>
      </div>
    );
  }

  if (metricsQuery.isError || !metricsQuery.data) {
    const normalized = normalizeApiError(metricsQuery.error);
    return (
      <Alert variant="destructive" role="alert">
        <AlertTitle>No fue posible cargar el dashboard</AlertTitle>
        <AlertDescription className="mt-2 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span>{normalized.message}</span>
          <Button variant="outline" size="sm" onClick={() => metricsQuery.refetch()}>
            Reintentar
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  const data = metricsQuery.data;
  const stats = statsQuery.data;

  const byType = Object.entries(data.por_tipo).map(([key, value]) => ({
    name: getTicketTypeLabel(key),
    value,
  }));

  const byPriority = Object.entries(data.por_prioridad).map(([key, value]) => ({
    name: getPriorityLabel(key),
    value,
  }));

  const byArea = data.por_area.map((item) => ({
    name: item.area_name,
    value: item.total,
  }));

  const slaBreakdown = [
    { name: 'A tiempo', value: data.cumplimiento_sla.a_tiempo },
    { name: 'Vencidas', value: data.cumplimiento_sla.vencidas },
    { name: 'Sin fecha SLA', value: data.cumplimiento_sla.sin_fecha_sla },
  ].filter((item) => item.value > 0);

  const sourceBreakdown = stats
    ? [
        { name: 'OpenAI', value: stats.all_time.by_source.openai },
        { name: 'Heurística', value: stats.all_time.by_source.heuristic },
        { name: 'Fallback', value: stats.all_time.by_source.fallback },
      ]
    : [];

  const sparklineData = [
    { label: 'A tiempo', total: data.cumplimiento_sla.a_tiempo },
    { label: 'Sin SLA', total: data.cumplimiento_sla.sin_fecha_sla },
    { label: 'Vencidas', total: data.cumplimiento_sla.vencidas },
    { label: 'Total', total: data.total_pqrs },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard de Triaje PQRS</h1>
          <p className="text-sm text-muted-foreground">
            Métricas en tiempo real · Actualizado {formatDateTimeCO(data.generated_at)}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            metricsQuery.refetch();
            statsQuery.refetch();
          }}
          disabled={metricsQuery.isFetching}
        >
          <RefreshCw
            className={`h-4 w-4 ${metricsQuery.isFetching ? 'animate-spin' : ''}`}
            aria-hidden="true"
          />
          Actualizar
        </Button>
      </div>

      {user?.role === 'ANALISTA' ? (
        <Alert variant="info">
          <AlertTitle>Vista filtrada por área</AlertTitle>
          <AlertDescription>
            Como Analista, las métricas mostradas corresponden exclusivamente a las PQRS asignadas a
            tu área.
          </AlertDescription>
        </Alert>
      ) : null}

      <section aria-label="Indicadores clave" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total PQRS</CardTitle>
            <FileText className="h-4 w-4 text-primary" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.total_pqrs}</div>
            <p className="text-xs text-muted-foreground">Registradas en el alcance actual</p>
            <div className="mt-2 h-10 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={sparklineData}>
                  <Area
                    type="monotone"
                    dataKey="total"
                    stroke="#1d4ed8"
                    fill="#3b82f6"
                    fillOpacity={0.2}
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Vencidas</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {data.cumplimiento_sla.vencidas}
            </div>
            <p className="text-xs text-muted-foreground">Requieren atención inmediata</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">A tiempo</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-success" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-success">{data.cumplimiento_sla.a_tiempo}</div>
            <p className="text-xs text-muted-foreground">
              Cumplimiento SLA: {data.cumplimiento_sla.porcentaje_a_tiempo.toFixed(1)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Sin fecha SLA
            </CardTitle>
            <Clock className="h-4 w-4 text-warning" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">
              {data.cumplimiento_sla.sin_fecha_sla}
            </div>
            <p className="text-xs text-muted-foreground">Pendientes de validación humana</p>
          </CardContent>
        </Card>
      </section>

      {data.total_pqrs === 0 ? (
        <EmptyState
          title="Aún no hay PQRS registradas"
          description="Cuando existan solicitudes radicadas podrás visualizar las distribuciones por tipo, área, prioridad y cumplimiento SLA."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Distribución por tipo de PQRS</CardTitle>
              <CardDescription>Totales agrupados por categoría</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={byType} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="value" name="Cantidad" fill="#1d4ed8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Cumplimiento SLA</CardTitle>
              <CardDescription>
                {data.cumplimiento_sla.porcentaje_a_tiempo.toFixed(1)}% dentro del plazo legal
              </CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={slaBreakdown}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                    label
                  >
                    {slaBreakdown.map((entry, idx) => (
                      <Cell key={entry.name} fill={SLA_COLORS[idx % SLA_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Distribución por área</CardTitle>
              <CardDescription>Solicitudes asignadas por dependencia</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={byArea}
                  layout="vertical"
                  margin={{ top: 8, right: 16, left: 24, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="value" name="PQRS" fill="#0f766e" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Prioridad y motor de triaje</CardTitle>
              <CardDescription>
                {stats
                  ? `Últimas 24h: ${stats.last_24h.total} clasificaciones`
                  : 'Distribución por nivel de prioridad'}
              </CardDescription>
            </CardHeader>
            <CardContent className={stats ? 'grid gap-4 sm:grid-cols-2' : 'h-72'}>
              <div className={stats ? 'h-60' : 'h-full'}>
                <p className="mb-2 text-xs font-semibold text-muted-foreground">Por prioridad</p>
                <ResponsiveContainer width="100%" height="90%">
                  <BarChart data={byPriority}>
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="value" name="PQRS" fill="#d97706" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              {stats ? (
                <div className="h-60">
                  <p className="mb-2 text-xs font-semibold text-muted-foreground">
                    Fuente de clasificación
                  </p>
                  <ResponsiveContainer width="100%" height="90%">
                    <PieChart>
                      <Pie
                        data={sourceBreakdown}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={68}
                        label
                      >
                        {sourceBreakdown.map((entry, idx) => (
                          <Cell key={entry.name} fill={SOURCE_COLORS[idx % SOURCE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
