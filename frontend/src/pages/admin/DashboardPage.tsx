import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, Bot, CheckCircle2, Clock, FileText, RefreshCw } from 'lucide-react';
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
import { fetchDashboardMetrics } from '@/api/dashboard';
import { EmptyState } from '@/components/common/EmptyState';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { normalizeApiError } from '@/lib/errors';
import { useAuthStore } from '@/stores/authStore';

const SLA_COLORS = ['#15803d', '#b45309', '#b91c1c'];
const SOURCE_COLORS = ['#1d4ed8', '#0f766e', '#d97706'];

export function DashboardPage() {
  const user = useAuthStore((state) => state.user);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: fetchDashboardMetrics,
  });

  if (isLoading) {
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

  if (isError || !data) {
    const normalized = normalizeApiError(error);
    return (
      <Alert variant="destructive" role="alert">
        <AlertTitle>No fue posible cargar el dashboard</AlertTitle>
        <AlertDescription className="mt-2 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span>{normalized.message}</span>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Reintentar
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  const aiTotal = data.classificationStats.all_time.total;
  const openAiPct =
    aiTotal > 0 ? Math.round((data.classificationStats.all_time.by_source.openai / aiTotal) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard de Triaje PQRS</h1>
          <p className="text-sm text-muted-foreground">
            Resumen operativo por tipo, área, prioridad y cumplimiento SLA.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          <RefreshCw
            className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`}
            aria-hidden="true"
          />
          Actualizar
        </Button>
      </div>

      {user?.role === 'ANALISTA' ? (
        <Alert variant="info">
          <AlertTitle>Vista filtrada por área</AlertTitle>
          <AlertDescription>
            Como Analista, las métricas mostradas corresponden exclusivamente a las PQRS asignadas
            a tu área.
          </AlertDescription>
        </Alert>
      ) : null}

      {/* KPI Cards con sparkline */}
      <section aria-label="Indicadores clave" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total PQRS</CardTitle>
            <FileText className="h-4 w-4 text-primary" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.totalTickets}</div>
            <p className="text-xs text-muted-foreground">Muestra reciente: {data.sampleSize}</p>
            <div className="mt-2 h-10 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.recentTrend}>
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
            <div className="text-2xl font-bold text-destructive">{data.overdueCount}</div>
            <p className="text-xs text-muted-foreground">Requieren atención inmediata</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Próximas a vencer
            </CardTitle>
            <Clock className="h-4 w-4 text-warning" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">{data.dueSoonCount}</div>
            <p className="text-xs text-muted-foreground">Dentro de los próximos 3 días hábiles</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              A tiempo / IA OpenAI
            </CardTitle>
            <CheckCircle2 className="h-4 w-4 text-success" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-success">{data.onTimeCount}</div>
            <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
              <Bot className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
              {openAiPct}% clasificadas vía OpenAI ({aiTotal} totales)
            </p>
          </CardContent>
        </Card>
      </section>

      {data.totalTickets === 0 ? (
        <EmptyState
          title="Aún no hay PQRS registradas"
          description="Cuando existan solicitudes radicadas podrás visualizar las distribuciones por tipo, área, prioridad y cumplimiento SLA."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Distribución por tipo de PQRS</CardTitle>
              <CardDescription>Sobre las últimas {data.sampleSize} solicitudes</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.byType} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
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
              <CardTitle>Estado de cumplimiento SLA</CardTitle>
              <CardDescription>Solicitudes abiertas a tiempo vs críticas</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.slaBreakdown}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                    label
                  >
                    {data.slaBreakdown.map((entry, idx) => (
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
              <CardDescription>Top áreas receptoras</CardDescription>
            </CardHeader>
            <CardContent className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={data.byArea}
                  layout="vertical"
                  margin={{ top: 8, right: 16, left: 24, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.25} />
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="value" name="Tickets" fill="#0f766e" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Prioridad y fuentes de clasificación</CardTitle>
              <CardDescription>
                Últimas 24h: {data.classificationStats.last_24h.total} clasificaciones
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="h-60">
                <p className="mb-2 text-xs font-semibold text-muted-foreground">Por prioridad</p>
                <ResponsiveContainer width="100%" height="90%">
                  <BarChart data={data.byPriority}>
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="value" name="Tickets" fill="#d97706" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="h-60">
                <p className="mb-2 text-xs font-semibold text-muted-foreground">
                  Motor de clasificación
                </p>
                <ResponsiveContainer width="100%" height="90%">
                  <PieChart>
                    <Pie
                      data={data.sourceBreakdown}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={68}
                      label
                    >
                      {data.sourceBreakdown.map((entry, idx) => (
                        <Cell key={entry.name} fill={SOURCE_COLORS[idx % SOURCE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
