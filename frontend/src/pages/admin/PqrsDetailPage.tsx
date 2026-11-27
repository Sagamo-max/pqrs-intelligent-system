import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Bot,
  ChevronDown,
  ChevronUp,
  Clock,
  Loader2,
  ShieldCheck,
  User,
} from 'lucide-react';
import { Controller, useForm } from 'react-hook-form';
import { Link, useLocation, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { z } from 'zod';
import { changeTicketType, findTicketByTracking, getTicketAudit } from '@/api/pqrs';
import { PriorityBadge, StatusBadge, TicketTypeBadge } from '@/components/common/StatusBadges';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { formatDateCO, formatDateTimeCO } from '@/lib/dates';
import { normalizeApiError } from '@/lib/errors';
import { getTicketTypeLabel, TICKET_TYPE_LABELS } from '@/lib/labels';
import { useAuthStore } from '@/stores/authStore';
import type { ChangeAuditEvent, TicketListOut, TicketType } from '@/types/api';

const changeTypeSchema = z.object({
  ticket_type: z.enum([
    'PETITION',
    'COMPLAINT',
    'CLAIM',
    'SUGGESTION',
    'INFORMATION_REQUEST',
    'CONSULTATION',
  ]),
  change_reason: z
    .string()
    .trim()
    .max(500, 'El motivo no puede superar los 500 caracteres.')
    .optional(),
});

type ChangeTypeValues = z.infer<typeof changeTypeSchema>;

export function PqrsDetailPage() {
  const { id = '' } = useParams<{ id: string }>();
  const trackingNumber = decodeURIComponent(id);
  const location = useLocation();
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const role = user?.role ?? useAuthStore.getState().role;
  const canViewFullAudit = role === 'SUPERVISOR' || role === 'MASTER';

  const stateTicket = (location.state as { ticket?: TicketListOut } | null)?.ticket ?? null;
  const [dialogOpen, setDialogOpen] = useState(false);
  const [justificationOpen, setJustificationOpen] = useState(true);
  const [humanEvents, setHumanEvents] = useState<ChangeAuditEvent[]>([]);

  const ticketQuery = useQuery({
    queryKey: ['ticket-detail', trackingNumber],
    queryFn: () => findTicketByTracking(trackingNumber),
    initialData: stateTicket ?? undefined,
  });

  const auditQuery = useQuery({
    queryKey: ['ticket-audit', trackingNumber],
    queryFn: () => getTicketAudit(trackingNumber),
  });

  const ticket = ticketQuery.data ?? null;
  const audit = auditQuery.data ?? null;

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChangeTypeValues>({
    resolver: zodResolver(changeTypeSchema),
    values: {
      ticket_type: ((ticket?.ticket_type as TicketType) || 'PETITION') as TicketType,
      change_reason: '',
    },
  });

  const changeTypeMutation = useMutation({
    mutationFn: (values: ChangeTypeValues) =>
      changeTicketType(trackingNumber, {
        ticket_type: values.ticket_type,
        responsible_user: user?.username ?? user?.full_name ?? 'funcionario',
        change_reason: values.change_reason || null,
      }),
    onSuccess: (updated, submitted) => {
      toast.success(
        `Tipo actualizado a ${getTicketTypeLabel(updated.ticket_type)}. SLA recalculado.`,
      );
      setHumanEvents((prev) => [
        {
          id: `session-${Date.now()}`,
          actor: 'HUMANO',
          title: `Reclasificación manual a ${getTicketTypeLabel(updated.ticket_type)}`,
          subtitle: `Responsable: ${user?.username ?? 'funcionario'} · Nuevo SLA: ${formatDateCO(updated.due_date)}`,
          timestamp: new Date().toISOString(),
          justification: submitted.change_reason || 'Sin motivo adicional registrado.',
        },
        ...prev,
      ]);
      queryClient.invalidateQueries({ queryKey: ['ticket-detail', trackingNumber] });
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
      setDialogOpen(false);
      reset({ ticket_type: updated.ticket_type, change_reason: '' });
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).message);
    },
  });

  if (auditQuery.isLoading && !ticket) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Cargando detalle de PQRS">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-36 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <Button asChild variant="ghost" size="sm" className="-ml-2">
            <Link to="/admin/pqrs">
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Volver al listado
            </Link>
          </Button>
          <h1 className="text-2xl font-bold tracking-tight">Radicado {trackingNumber}</h1>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>Cambiar tipo y recalcular SLA</Button>
            </DialogTrigger>
            <DialogContent>
              <form
                onSubmit={handleSubmit((values) => changeTypeMutation.mutate(values))}
                className="space-y-4"
              >
                <DialogHeader>
                  <DialogTitle>Reclasificar tipo de PQRS (HU-18)</DialogTitle>
                  <DialogDescription>
                    Recalcula automáticamente la fecha límite según la Ley 1755 de 2015. Si
                    eliges Consulta, requerirá validación humana de SLA.
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-2">
                  <Label htmlFor="new-ticket-type">Nuevo tipo de PQRS</Label>
                  <Controller
                    name="ticket_type"
                    control={control}
                    render={({ field }) => (
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger id="new-ticket-type" aria-label="Nuevo tipo de PQRS">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {(Object.keys(TICKET_TYPE_LABELS) as TicketType[]).map((key) => (
                            <SelectItem key={key} value={key}>
                              {TICKET_TYPE_LABELS[key]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="change-reason">Motivo del cambio (opcional)</Label>
                  <Textarea
                    id="change-reason"
                    rows={3}
                    placeholder="Explica por qué se ajusta la clasificación..."
                    {...register('change_reason')}
                  />
                  {errors.change_reason ? (
                    <p className="text-xs text-destructive">{errors.change_reason.message}</p>
                  ) : null}
                </div>

                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setDialogOpen(false)}
                  >
                    Cancelar
                  </Button>
                  <Button type="submit" disabled={changeTypeMutation.isPending}>
                    {changeTypeMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                        Guardando...
                      </>
                    ) : (
                      'Guardar cambio'
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          {/* TODO(backend-hu15): Habilitar cuando exista PATCH /api/v1/pqrs/{ticket_id}/area */}
          <Button variant="outline" disabled title="Pendiente endpoint PATCH /pqrs/{id}/area">
            Reasignar área (Pronto)
          </Button>

          {/* TODO(backend-hu18): Habilitar cuando exista PATCH /api/v1/pqrs/{ticket_id}/prioridad */}
          <Button
            variant="outline"
            disabled
            title="Pendiente endpoint PATCH /pqrs/{id}/prioridad"
          >
            Cambiar prioridad (Pronto)
          </Button>
        </div>
      </div>

      {/* Resumen del ticket */}
      <Card>
        <CardContent className="grid gap-4 pt-6 sm:grid-cols-2 lg:grid-cols-5">
          <div>
            <p className="text-xs text-muted-foreground">Estado</p>
            <div className="mt-1">
              {ticket ? <StatusBadge status={ticket.status} /> : <Badge>Consultando</Badge>}
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Tipo actual</p>
            <div className="mt-1">
              <TicketTypeBadge
                ticketType={ticket?.ticket_type ?? audit?.suggested_type ?? 'PETITION'}
              />
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Prioridad</p>
            <div className="mt-1">
              <PriorityBadge
                priority={ticket?.priority ?? audit?.suggested_priority ?? 'MEDIUM'}
              />
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Área asignada</p>
            <p className="mt-1 text-sm font-semibold">
              {ticket?.area?.name ?? audit?.suggested_area_code ?? 'Sin asignar'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Vencimiento SLA</p>
            <p className="mt-1 flex items-center gap-1.5 text-sm font-semibold">
              <Clock className="h-4 w-4 text-primary" aria-hidden="true" />
              {ticket ? formatDateCO(ticket.due_date) : 'Consultar listado'}
            </p>
          </div>
        </CardContent>
      </Card>

      {auditQuery.isError ? (
        <Alert variant="destructive" role="alert">
          <AlertTitle>No fue posible cargar la auditoría de la PQRS</AlertTitle>
          <AlertDescription>{normalizeApiError(auditQuery.error).message}</AlertDescription>
        </Alert>
      ) : null}

      {/* Timeline vertical IA vs HUMANO */}
      <Card>
        <CardHeader>
          <CardTitle>Línea de tiempo de decisiones (IA / Humano)</CardTitle>
          <CardDescription>
            Trazabilidad de clasificación automática y reclasificaciones humanas.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ol className="relative space-y-6 border-l-2 border-border pl-6">
            {humanEvents.map((event) => (
              <li key={event.id} className="relative">
                <span
                  className="absolute -left-[35px] top-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-emerald-600 text-white shadow"
                  aria-hidden="true"
                >
                  <User className="h-3.5 w-3.5" />
                </span>
                <div className="rounded-lg border border-emerald-300 bg-emerald-50/70 p-4 dark:border-emerald-800 dark:bg-emerald-950/40">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="success">HUMANO</Badge>
                      <span className="text-sm font-semibold">{event.title}</span>
                    </div>
                    <time className="text-xs text-muted-foreground">
                      {formatDateTimeCO(event.timestamp)}
                    </time>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{event.subtitle}</p>
                  {event.justification ? (
                    <p className="mt-2 text-sm">{event.justification}</p>
                  ) : null}
                </div>
              </li>
            ))}

            {audit ? (
              <li className="relative">
                <span
                  className="absolute -left-[35px] top-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground shadow"
                  aria-hidden="true"
                >
                  <Bot className="h-3.5 w-3.5" />
                </span>
                <div className="rounded-lg border border-blue-300 bg-blue-50/70 p-4 dark:border-blue-800 dark:bg-blue-950/40">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="info">IA ({audit.provider})</Badge>
                      <span className="text-sm font-semibold">
                        Sugirió {getTicketTypeLabel(audit.suggested_type)} · Área{' '}
                        {audit.suggested_area_code}
                      </span>
                    </div>
                    <time className="text-xs text-muted-foreground">
                      {formatDateTimeCO(audit.created_at)}
                    </time>
                  </div>

                  <Collapsible open={justificationOpen} onOpenChange={setJustificationOpen}>
                    <CollapsibleTrigger asChild>
                      <Button variant="ghost" size="sm" className="mt-2 h-8 px-2 text-xs">
                        {justificationOpen ? (
                          <>
                            <ChevronUp className="h-4 w-4" aria-hidden="true" />
                            Ocultar justificación y textos
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-4 w-4" aria-hidden="true" />
                            Ver justificación y textos
                          </>
                        )}
                      </Button>
                    </CollapsibleTrigger>

                    <CollapsibleContent className="mt-3 space-y-3">
                      <div className="rounded-md border bg-card p-3">
                        <p className="text-xs font-semibold uppercase text-muted-foreground">
                          Justificación de decisión
                        </p>
                        <p className="mt-1 text-sm">{audit.decision_justification}</p>
                      </div>

                      <Tabs defaultValue="sanitized">
                        <TabsList>
                          <TabsTrigger value="sanitized">Texto sanitizado (enviado a IA)</TabsTrigger>
                          <TabsTrigger value="original">Texto original</TabsTrigger>
                        </TabsList>
                        <TabsContent value="sanitized">
                          <div className="rounded-md border bg-card p-3 text-sm whitespace-pre-wrap">
                            {audit.sanitized_text}
                          </div>
                        </TabsContent>
                        <TabsContent value="original">
                          <div className="rounded-md border bg-card p-3 text-sm whitespace-pre-wrap">
                            {audit.original_text}
                          </div>
                        </TabsContent>
                      </Tabs>
                    </CollapsibleContent>
                  </Collapsible>
                </div>
              </li>
            ) : null}
          </ol>

          <p className="mt-4 text-xs text-muted-foreground">
            {/* TODO(backend-hu16): Consumir historial persistido ChangeAudit desde GET /api/v1/pqrs/{id} */}
            Nota: los cambios realizados durante la sesión actual aparecen en la línea de tiempo. El
            historial histórico completo de cambios humanos se mostrará aquí cuando el backend
            exponga <code>GET /api/v1/pqrs/{'{ticket_id}'}</code>.
          </p>
        </CardContent>
      </Card>

      {/* Auditoría IA extendida (HU-17) */}
      {canViewFullAudit && audit ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-primary" aria-hidden="true" />
              Auditoría técnica de IA (HU-17)
            </CardTitle>
            <CardDescription>
              Disponible para roles Supervisor y Master.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-md border p-3">
                <dt className="text-xs text-muted-foreground">Modelo</dt>
                <dd className="mt-1 text-sm font-semibold">{audit.ai_model}</dd>
              </div>
              <div className="rounded-md border p-3">
                <dt className="text-xs text-muted-foreground">Confianza</dt>
                <dd className="mt-1 text-sm font-semibold">
                  {audit.confidence !== null ? `${Math.round(audit.confidence * 100)}%` : 'N/D'}
                </dd>
              </div>
              <div className="rounded-md border p-3">
                <dt className="text-xs text-muted-foreground">Tokens usados</dt>
                <dd className="mt-1 text-sm font-semibold">{audit.tokens_used ?? 'N/D'}</dd>
              </div>
              <div className="rounded-md border p-3">
                <dt className="text-xs text-muted-foreground">Latencia</dt>
                <dd className="mt-1 text-sm font-semibold">
                  {audit.latency_ms !== null ? `${audit.latency_ms} ms` : 'N/D'}
                </dd>
              </div>
            </dl>

            {audit.raw_response ? (
              <div>
                <p className="mb-1.5 text-xs font-semibold text-muted-foreground">
                  Respuesta estructurada (raw_response)
                </p>
                <pre className="max-h-64 overflow-auto rounded-md border bg-muted p-3 text-xs">
                  {JSON.stringify(audit.raw_response, null, 2)}
                </pre>
              </div>
            ) : null}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
