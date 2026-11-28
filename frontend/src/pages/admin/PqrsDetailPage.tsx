import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Bot,
  Building2,
  ChevronDown,
  ChevronUp,
  Clock,
  Flag,
  Loader2,
  ShieldCheck,
  User,
} from 'lucide-react';
import { Controller, useForm } from 'react-hook-form';
import { Link, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { z } from 'zod';
import { listAreas } from '@/api/areas';
import {
  changeTicketPriority,
  changeTicketType,
  getTicketAiAuditHistory,
  getTicketDetail,
  reassignTicketArea,
} from '@/api/pqrs';
import {
  AlertLevelBadge,
  PriorityBadge,
  StatusBadge,
  TicketTypeBadge,
} from '@/components/common/StatusBadges';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
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
import {
  getPriorityLabel,
  getTicketTypeLabel,
  TICKET_PRIORITY_LABELS,
  TICKET_TYPE_LABELS,
} from '@/lib/labels';
import { useAuthStore } from '@/stores/authStore';
import type { TicketPriority, TicketType } from '@/types/api';

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

const reassignAreaSchema = z.object({
  area_id: z.string().min(1, 'Selecciona un área destino.'),
  change_reason: z
    .string()
    .trim()
    .max(500, 'El motivo no puede superar los 500 caracteres.')
    .optional(),
});

const changePrioritySchema = z.object({
  priority: z.enum(['HIGH', 'MEDIUM', 'LOW']),
  change_reason: z
    .string()
    .trim()
    .max(500, 'El motivo no puede superar los 500 caracteres.')
    .optional(),
});

type ChangeTypeValues = z.infer<typeof changeTypeSchema>;
type ReassignAreaValues = z.infer<typeof reassignAreaSchema>;
type ChangePriorityValues = z.infer<typeof changePrioritySchema>;

export function PqrsDetailPage() {
  const { id = '' } = useParams<{ id: string }>();
  const ticketIdentifier = decodeURIComponent(id);
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);
  const role = user?.role ?? useAuthStore.getState().role;
  const canViewFullAudit = role === 'SUPERVISOR' || role === 'MASTER';

  const [typeDialogOpen, setTypeDialogOpen] = useState(false);
  const [areaDialogOpen, setAreaDialogOpen] = useState(false);
  const [priorityDialogOpen, setPriorityDialogOpen] = useState(false);
  const [expandedEvents, setExpandedEvents] = useState<Record<string, boolean>>({});

  const detailQuery = useQuery({
    queryKey: ['ticket-detail', ticketIdentifier],
    queryFn: () => getTicketDetail(ticketIdentifier),
  });

  const areasQuery = useQuery({
    queryKey: ['areas'],
    queryFn: listAreas,
  });

  const aiAuditQuery = useQuery({
    queryKey: ['ticket-ai-audit-history', ticketIdentifier],
    queryFn: () => getTicketAiAuditHistory(ticketIdentifier),
    enabled: canViewFullAudit,
  });

  const detail = detailQuery.data;
  const responsibleUser = user?.username ?? user?.full_name ?? 'funcionario';

  const typeForm = useForm<ChangeTypeValues>({
    resolver: zodResolver(changeTypeSchema),
    values: {
      ticket_type: (detail?.ticket_type ?? 'PETITION') as TicketType,
      change_reason: '',
    },
  });

  const areaForm = useForm<ReassignAreaValues>({
    resolver: zodResolver(reassignAreaSchema),
    values: {
      area_id: detail?.area?.id ?? '',
      change_reason: '',
    },
  });

  const priorityForm = useForm<ChangePriorityValues>({
    resolver: zodResolver(changePrioritySchema),
    values: {
      priority: (detail?.priority ?? 'MEDIUM') as TicketPriority,
      change_reason: '',
    },
  });

  const invalidateRelated = () => {
    queryClient.invalidateQueries({ queryKey: ['ticket-detail', ticketIdentifier] });
    queryClient.invalidateQueries({ queryKey: ['tickets'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
    queryClient.invalidateQueries({ queryKey: ['alerts'] });
  };

  const changeTypeMutation = useMutation({
    mutationFn: (values: ChangeTypeValues) =>
      changeTicketType(detail?.tracking_number ?? ticketIdentifier, {
        ticket_type: values.ticket_type,
        responsible_user: responsibleUser,
        change_reason: values.change_reason || null,
      }),
    onSuccess: (updated) => {
      toast.success(
        `Tipo actualizado a ${getTicketTypeLabel(updated.ticket_type)}. SLA recalculado.`,
      );
      invalidateRelated();
      setTypeDialogOpen(false);
      typeForm.reset({ ticket_type: updated.ticket_type, change_reason: '' });
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).message);
    },
  });

  const reassignAreaMutation = useMutation({
    mutationFn: (values: ReassignAreaValues) =>
      reassignTicketArea(detail?.tracking_number ?? ticketIdentifier, {
        area_id: values.area_id,
        responsible_user: responsibleUser,
        change_reason: values.change_reason || null,
      }),
    onSuccess: (updated) => {
      toast.success(`Área reasignada a ${updated.area?.name ?? 'nueva área'}.`);
      invalidateRelated();
      setAreaDialogOpen(false);
      areaForm.reset({ area_id: updated.area?.id ?? '', change_reason: '' });
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).message);
    },
  });

  const changePriorityMutation = useMutation({
    mutationFn: (values: ChangePriorityValues) =>
      changeTicketPriority(detail?.tracking_number ?? ticketIdentifier, {
        priority: values.priority,
        responsible_user: responsibleUser,
        change_reason: values.change_reason || null,
      }),
    onSuccess: (updated) => {
      toast.success(`Prioridad actualizada a ${getPriorityLabel(updated.priority)}.`);
      invalidateRelated();
      setPriorityDialogOpen(false);
      priorityForm.reset({ priority: updated.priority, change_reason: '' });
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).message);
    },
  });

  const toggleEventDetails = (eventId: string) => {
    setExpandedEvents((prev) => ({ ...prev, [eventId]: !(prev[eventId] ?? true) }));
  };

  if (detailQuery.isLoading) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Cargando detalle de PQRS">
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-36 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (detailQuery.isError || !detail) {
    return (
      <div className="space-y-4">
        <Button asChild variant="ghost" size="sm">
          <Link to="/admin/pqrs">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Volver al listado
          </Link>
        </Button>
        <Alert variant="destructive" role="alert">
          <AlertTitle>No fue posible cargar el detalle de la PQRS</AlertTitle>
          <AlertDescription>{normalizeApiError(detailQuery.error).message}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const activeAreas = (areasQuery.data ?? []).filter((area) => area.is_active);
  const audits = aiAuditQuery.data ?? [];

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
          <h1 className="text-2xl font-bold tracking-tight">Radicado {detail.tracking_number}</h1>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* HU-15: Reasignar área */}
          <Dialog open={areaDialogOpen} onOpenChange={setAreaDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Building2 className="h-4 w-4" aria-hidden="true" />
                Reasignar área
              </Button>
            </DialogTrigger>
            <DialogContent>
              <form
                onSubmit={areaForm.handleSubmit((values) => reassignAreaMutation.mutate(values))}
                className="space-y-4"
              >
                <DialogHeader>
                  <DialogTitle>Reasignar área responsable (HU-15)</DialogTitle>
                  <DialogDescription>
                    Cambia el área encargada sin modificar el estado ni los plazos SLA.
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-2">
                  <Label htmlFor="reassign-area-select">Área destino</Label>
                  <Controller
                    name="area_id"
                    control={areaForm.control}
                    render={({ field }) => (
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger id="reassign-area-select" aria-label="Área destino">
                          <SelectValue placeholder="Selecciona un área" />
                        </SelectTrigger>
                        <SelectContent>
                          {activeAreas.map((area) => (
                            <SelectItem key={area.id} value={area.id}>
                              {area.name} ({area.code})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                  {areaForm.formState.errors.area_id ? (
                    <p className="text-xs text-destructive">
                      {areaForm.formState.errors.area_id.message}
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="area-change-reason">Motivo de reasignación (opcional)</Label>
                  <Textarea
                    id="area-change-reason"
                    rows={3}
                    placeholder="Ej. El caso corresponde a facturación..."
                    {...areaForm.register('change_reason')}
                  />
                </div>

                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setAreaDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit" disabled={reassignAreaMutation.isPending}>
                    {reassignAreaMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                        Reasignando...
                      </>
                    ) : (
                      'Confirmar área'
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          {/* HU-18: Cambiar prioridad */}
          <Dialog open={priorityDialogOpen} onOpenChange={setPriorityDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Flag className="h-4 w-4" aria-hidden="true" />
                Cambiar prioridad
              </Button>
            </DialogTrigger>
            <DialogContent>
              <form
                onSubmit={priorityForm.handleSubmit((values) =>
                  changePriorityMutation.mutate(values),
                )}
                className="space-y-4"
              >
                <DialogHeader>
                  <DialogTitle>Modificar prioridad (HU-18)</DialogTitle>
                  <DialogDescription>
                    Ajusta la prioridad operativa y deja registro auditable de la intervención.
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-2">
                  <Label htmlFor="new-priority-select">Nueva prioridad</Label>
                  <Controller
                    name="priority"
                    control={priorityForm.control}
                    render={({ field }) => (
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger id="new-priority-select" aria-label="Nueva prioridad">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {(Object.keys(TICKET_PRIORITY_LABELS) as TicketPriority[]).map((key) => (
                            <SelectItem key={key} value={key}>
                              {TICKET_PRIORITY_LABELS[key]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="priority-change-reason">Motivo del cambio (opcional)</Label>
                  <Textarea
                    id="priority-change-reason"
                    rows={3}
                    placeholder="Justifica el ajuste de prioridad..."
                    {...priorityForm.register('change_reason')}
                  />
                </div>

                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setPriorityDialogOpen(false)}
                  >
                    Cancelar
                  </Button>
                  <Button type="submit" disabled={changePriorityMutation.isPending}>
                    {changePriorityMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                        Guardando...
                      </>
                    ) : (
                      'Guardar prioridad'
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          {/* HU-18: Cambiar tipo y recalcular SLA */}
          <Dialog open={typeDialogOpen} onOpenChange={setTypeDialogOpen}>
            <DialogTrigger asChild>
              <Button>Cambiar tipo y recalcular SLA</Button>
            </DialogTrigger>
            <DialogContent>
              <form
                onSubmit={typeForm.handleSubmit((values) => changeTypeMutation.mutate(values))}
                className="space-y-4"
              >
                <DialogHeader>
                  <DialogTitle>Reclasificar tipo de PQRS (HU-18)</DialogTitle>
                  <DialogDescription>
                    Recalcula automáticamente la fecha límite según la Ley 1755 de 2015. Si eliges
                    Consulta, requerirá validación humana de SLA.
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-2">
                  <Label htmlFor="new-ticket-type">Nuevo tipo de PQRS</Label>
                  <Controller
                    name="ticket_type"
                    control={typeForm.control}
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
                    {...typeForm.register('change_reason')}
                  />
                </div>

                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setTypeDialogOpen(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit" disabled={changeTypeMutation.isPending}>
                    {changeTypeMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                        Guardando...
                      </>
                    ) : (
                      'Guardar tipo'
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Resumen + SLA */}
      <Card>
        <CardContent className="grid gap-4 pt-6 sm:grid-cols-2 lg:grid-cols-6">
          <div>
            <p className="text-xs text-muted-foreground">Estado</p>
            <div className="mt-1">
              <StatusBadge status={detail.status} />
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Tipo actual</p>
            <div className="mt-1">
              <TicketTypeBadge ticketType={detail.ticket_type} />
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Prioridad</p>
            <div className="mt-1">
              <PriorityBadge priority={detail.priority} />
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Área asignada</p>
            <p className="mt-1 text-sm font-semibold">{detail.area?.name ?? 'Sin asignar'}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Nivel SLA</p>
            <div className="mt-1">
              <AlertLevelBadge level={detail.sla.alert_level} />
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Vencimiento SLA</p>
            <p className="mt-1 flex items-center gap-1.5 text-sm font-semibold">
              <Clock className="h-4 w-4 text-primary" aria-hidden="true" />
              {detail.sla.due_date ? formatDateCO(detail.sla.due_date) : 'Validación manual'}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Solicitante y texto original */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Datos del solicitante</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-xs text-muted-foreground">Nombre</dt>
                <dd className="font-medium">
                  {detail.claimant.first_name} {detail.claimant.last_name}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Documento</dt>
                <dd className="font-medium">
                  {detail.claimant.document_type} {detail.claimant.document_number}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Correo</dt>
                <dd className="font-medium">{detail.claimant.email}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Teléfono</dt>
                <dd className="font-medium">{detail.claimant.phone ?? 'No registrado'}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Texto radicado</CardTitle>
            <CardDescription>
              Radicada el {formatDateCO(detail.sla.filing_date)}
              {detail.sla.days_remaining !== null
                ? ` · ${detail.sla.days_remaining} días para vencimiento`
                : ''}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{detail.original_text}</p>
          </CardContent>
        </Card>
      </div>

      {/* Línea de tiempo IA vs HUMANO (HU-16) */}
      <Card>
        <CardHeader>
          <CardTitle>Línea de tiempo de decisiones (IA / Humano)</CardTitle>
          <CardDescription>
            Historial cronológico de clasificación automática e intervenciones manuales.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {detail.timeline.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No hay eventos registrados en la línea de tiempo todavía.
            </p>
          ) : (
            <ol className="relative space-y-6 border-l-2 border-border pl-6">
              {detail.timeline.map((event) => {
                const isAI = event.source_type === 'AI_DECISION';
                const isOpen = expandedEvents[event.event_id] ?? isAI;
                return (
                  <li key={event.event_id} className="relative">
                    <span
                      className={`absolute -left-[35px] top-0.5 flex h-6 w-6 items-center justify-center rounded-full text-white shadow ${
                        isAI ? 'bg-primary' : 'bg-emerald-600'
                      }`}
                      aria-hidden="true"
                    >
                      {isAI ? <Bot className="h-3.5 w-3.5" /> : <User className="h-3.5 w-3.5" />}
                    </span>

                    <div
                      className={`rounded-lg border p-4 ${
                        isAI
                          ? 'border-blue-300 bg-blue-50/70 dark:border-blue-800 dark:bg-blue-950/40'
                          : 'border-emerald-300 bg-emerald-50/70 dark:border-emerald-800 dark:bg-emerald-950/40'
                      }`}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant={isAI ? 'info' : 'success'}>{event.visual_badge}</Badge>
                          <span className="text-sm font-semibold">{event.title}</span>
                          <span className="text-xs text-muted-foreground">· {event.actor}</span>
                        </div>
                        <time className="text-xs text-muted-foreground">
                          {formatDateTimeCO(event.timestamp)}
                        </time>
                      </div>

                      {event.old_value || event.new_value ? (
                        <p className="mt-1.5 text-xs font-medium text-muted-foreground">
                          {event.modified_field ? `${event.modified_field}: ` : ''}
                          {event.old_value ? `${event.old_value} → ` : ''}
                          {event.new_value ?? ''}
                        </p>
                      ) : null}

                      <Collapsible
                        open={isOpen}
                        onOpenChange={() => toggleEventDetails(event.event_id)}
                      >
                        <CollapsibleTrigger asChild>
                          <Button variant="ghost" size="sm" className="mt-2 h-8 px-2 text-xs">
                            {isOpen ? (
                              <>
                                <ChevronUp className="h-4 w-4" aria-hidden="true" />
                                Ocultar justificación
                              </>
                            ) : (
                              <>
                                <ChevronDown className="h-4 w-4" aria-hidden="true" />
                                Ver justificación
                              </>
                            )}
                          </Button>
                        </CollapsibleTrigger>

                        <CollapsibleContent className="mt-2 space-y-2">
                          <div className="rounded-md border bg-card p-3 text-sm">
                            {event.description}
                          </div>
                          {event.details ? (
                            <pre className="overflow-auto rounded-md border bg-muted p-2.5 text-xs">
                              {JSON.stringify(event.details, null, 2)}
                            </pre>
                          ) : null}
                        </CollapsibleContent>
                      </Collapsible>
                    </div>
                  </li>
                );
              })}
            </ol>
          )}
        </CardContent>
      </Card>

      {/* Auditoría técnica IA (HU-17, solo SUPERVISOR / MASTER) */}
      {canViewFullAudit ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-primary" aria-hidden="true" />
              Auditoría técnica de IA (HU-17)
            </CardTitle>
            <CardDescription>
              Histórico completo de trazabilidad IA (visible para Supervisor y Master).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {aiAuditQuery.isLoading ? (
              <Skeleton className="h-32 w-full" />
            ) : aiAuditQuery.isError ? (
              <Alert variant="destructive" role="alert">
                <AlertTitle>No se pudo cargar la auditoría IA</AlertTitle>
                <AlertDescription>{normalizeApiError(aiAuditQuery.error).message}</AlertDescription>
              </Alert>
            ) : audits.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No hay registros de auditoría IA disponibles para esta PQRS.
              </p>
            ) : (
              audits.map((audit) => (
                <div key={audit.id} className="space-y-4 rounded-lg border p-4">
                  <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                    <div className="rounded-md border p-3">
                      <dt className="text-xs text-muted-foreground">Proveedor</dt>
                      <dd className="mt-1 text-sm font-semibold">{audit.provider}</dd>
                    </div>
                    <div className="rounded-md border p-3">
                      <dt className="text-xs text-muted-foreground">Modelo</dt>
                      <dd className="mt-1 text-sm font-semibold">{audit.ai_model}</dd>
                    </div>
                    <div className="rounded-md border p-3">
                      <dt className="text-xs text-muted-foreground">Confianza</dt>
                      <dd className="mt-1 text-sm font-semibold">
                        {audit.confidence !== null
                          ? `${Math.round(audit.confidence * 100)}%`
                          : 'N/D'}
                      </dd>
                    </div>
                    <div className="rounded-md border p-3">
                      <dt className="text-xs text-muted-foreground">Tokens</dt>
                      <dd className="mt-1 text-sm font-semibold">{audit.tokens_used ?? 'N/D'}</dd>
                    </div>
                    <div className="rounded-md border p-3">
                      <dt className="text-xs text-muted-foreground">Latencia</dt>
                      <dd className="mt-1 text-sm font-semibold">
                        {audit.latency_ms !== null ? `${audit.latency_ms} ms` : 'N/D'}
                      </dd>
                    </div>
                  </dl>

                  <Tabs defaultValue="sanitized">
                    <TabsList>
                      <TabsTrigger value="sanitized">Texto sanitizado (enviado a IA)</TabsTrigger>
                      <TabsTrigger value="original">Texto original</TabsTrigger>
                      {audit.raw_response ? <TabsTrigger value="raw">Raw JSON</TabsTrigger> : null}
                    </TabsList>
                    <TabsContent value="sanitized">
                      <div className="rounded-md border bg-muted/40 p-3 text-sm whitespace-pre-wrap">
                        {audit.sanitized_text}
                      </div>
                    </TabsContent>
                    <TabsContent value="original">
                      <div className="rounded-md border bg-muted/40 p-3 text-sm whitespace-pre-wrap">
                        {audit.original_text}
                      </div>
                    </TabsContent>
                    {audit.raw_response ? (
                      <TabsContent value="raw">
                        <pre className="max-h-64 overflow-auto rounded-md border bg-muted p-3 text-xs">
                          {JSON.stringify(audit.raw_response, null, 2)}
                        </pre>
                      </TabsContent>
                    ) : null}
                  </Tabs>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
