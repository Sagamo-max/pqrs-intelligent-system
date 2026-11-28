import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Eye, Search } from 'lucide-react';
import { Link } from 'react-router-dom';
import { listAreas } from '@/api/areas';
import { listTickets } from '@/api/pqrs';
import { EmptyState } from '@/components/common/EmptyState';
import { PriorityBadge, StatusBadge, TicketTypeBadge } from '@/components/common/StatusBadges';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDateCO, formatDateTimeCO } from '@/lib/dates';
import { normalizeApiError } from '@/lib/errors';
import { TICKET_PRIORITY_LABELS, TICKET_STATUS_LABELS, TICKET_TYPE_LABELS } from '@/lib/labels';
import type { TicketPriority, TicketStatus, TicketType } from '@/types/api';

const PAGE_SIZE = 15;

export function PqrsListPage() {
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [areaFilter, setAreaFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [offset, setOffset] = useState(0);

  const areasQuery = useQuery({
    queryKey: ['areas'],
    queryFn: listAreas,
  });

  const ticketsQuery = useQuery({
    queryKey: ['tickets', { statusFilter, priorityFilter, areaFilter, typeFilter, offset }],
    queryFn: () =>
      listTickets({
        status: statusFilter !== 'ALL' ? (statusFilter as TicketStatus) : undefined,
        priority: priorityFilter !== 'ALL' ? (priorityFilter as TicketPriority) : undefined,
        area_id: areaFilter !== 'ALL' ? areaFilter : undefined,
        ticket_type: typeFilter !== 'ALL' ? (typeFilter as TicketType) : undefined,
        limit: PAGE_SIZE,
        offset,
      }),
  });

  const filteredItems = useMemo(() => {
    const items = ticketsQuery.data?.items ?? [];
    const term = searchTerm.trim().toLowerCase();
    if (!term) return items;
    return items.filter(
      (item) =>
        item.tracking_number.toLowerCase().includes(term) ||
        (item.area?.name ?? '').toLowerCase().includes(term),
    );
  }, [ticketsQuery.data?.items, searchTerm]);

  const total = ticketsQuery.data?.total ?? 0;
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const resetFilters = () => {
    setStatusFilter('ALL');
    setPriorityFilter('ALL');
    setAreaFilter('ALL');
    setTypeFilter('ALL');
    setSearchTerm('');
    setOffset(0);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Listado de PQRS</h1>
          <p className="text-sm text-muted-foreground">
            Consulta, filtra y accede al detalle de cada radicado.
          </p>
        </div>
        <Button asChild>
          <Link to="/radicar">Nueva PQRS</Link>
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <CardContent className="grid gap-4 pt-6 sm:grid-cols-2 lg:grid-cols-5">
          <div className="space-y-1.5">
            <Label htmlFor="search-tracking">Buscar radicado o área</Label>
            <div className="relative">
              <Search
                className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground"
                aria-hidden="true"
              />
              <Input
                id="search-tracking"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Ej. PQRS-2026..."
                className="pl-9"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="filter-status">Estado</Label>
            <Select
              value={statusFilter}
              onValueChange={(value) => {
                setStatusFilter(value);
                setOffset(0);
              }}
            >
              <SelectTrigger id="filter-status" aria-label="Filtrar por estado">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">Todos</SelectItem>
                {(Object.keys(TICKET_STATUS_LABELS) as TicketStatus[]).map((key) => (
                  <SelectItem key={key} value={key}>
                    {TICKET_STATUS_LABELS[key]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="filter-priority">Prioridad</Label>
            <Select
              value={priorityFilter}
              onValueChange={(value) => {
                setPriorityFilter(value);
                setOffset(0);
              }}
            >
              <SelectTrigger id="filter-priority" aria-label="Filtrar por prioridad">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">Todas</SelectItem>
                {(Object.keys(TICKET_PRIORITY_LABELS) as TicketPriority[]).map((key) => (
                  <SelectItem key={key} value={key}>
                    {TICKET_PRIORITY_LABELS[key]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="filter-type">Tipo</Label>
            <Select
              value={typeFilter}
              onValueChange={(value) => {
                setTypeFilter(value);
                setOffset(0);
              }}
            >
              <SelectTrigger id="filter-type" aria-label="Filtrar por tipo">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">Todos</SelectItem>
                {(Object.keys(TICKET_TYPE_LABELS) as TicketType[]).map((key) => (
                  <SelectItem key={key} value={key}>
                    {TICKET_TYPE_LABELS[key]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="filter-area">Área</Label>
            <Select
              value={areaFilter}
              onValueChange={(value) => {
                setAreaFilter(value);
                setOffset(0);
              }}
            >
              <SelectTrigger id="filter-area" aria-label="Filtrar por área">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">Todas</SelectItem>
                {(areasQuery.data ?? []).map((area) => (
                  <SelectItem key={area.id} value={area.id}>
                    {area.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {ticketsQuery.isLoading ? (
        <div className="space-y-3" aria-busy="true" aria-label="Cargando listado">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : ticketsQuery.isError ? (
        <Alert variant="destructive" role="alert">
          <AlertTitle>Error al cargar las PQRS</AlertTitle>
          <AlertDescription>{normalizeApiError(ticketsQuery.error).message}</AlertDescription>
        </Alert>
      ) : filteredItems.length === 0 ? (
        <EmptyState
          title="No hay PQRS que coincidan"
          description="Prueba ajustando los filtros de búsqueda o estado."
          action={
            <Button variant="outline" onClick={resetFilters}>
              Limpiar filtros
            </Button>
          }
        />
      ) : (
        <>
          {/* Tabla desktop */}
          <div className="hidden overflow-x-auto rounded-lg border bg-card md:block">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-muted/50 text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Radicado</th>
                  <th className="px-4 py-3">Tipo</th>
                  <th className="px-4 py-3">Prioridad</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3">Área</th>
                  <th className="px-4 py-3">Vencimiento</th>
                  <th className="px-4 py-3">Creada</th>
                  <th className="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredItems.map((ticket) => (
                  <tr key={ticket.id} className="hover:bg-muted/30">
                    <td className="px-4 py-3 font-semibold text-primary">
                      {ticket.tracking_number}
                    </td>
                    <td className="px-4 py-3">
                      <TicketTypeBadge ticketType={ticket.ticket_type} />
                    </td>
                    <td className="px-4 py-3">
                      <PriorityBadge priority={ticket.priority} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={ticket.status} />
                    </td>
                    <td className="px-4 py-3">{ticket.area?.name ?? 'Sin asignar'}</td>
                    <td className="px-4 py-3">{formatDateCO(ticket.due_date)}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {formatDateTimeCO(ticket.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button asChild variant="outline" size="sm">
                        <Link
                          to={`/admin/pqrs/${encodeURIComponent(ticket.tracking_number)}`}
                          state={{ ticket }}
                        >
                          <Eye className="h-4 w-4" aria-hidden="true" />
                          Ver
                        </Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Cards móvil */}
          <div className="grid gap-3 md:hidden">
            {filteredItems.map((ticket) => (
              <Card key={ticket.id}>
                <CardContent className="space-y-3 pt-5">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-primary">{ticket.tracking_number}</p>
                      <p className="text-xs text-muted-foreground">
                        {ticket.area?.name ?? 'Sin área'}
                      </p>
                    </div>
                    <StatusBadge status={ticket.status} />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <TicketTypeBadge ticketType={ticket.ticket_type} />
                    <PriorityBadge priority={ticket.priority} />
                  </div>
                  <div className="flex items-center justify-between border-t pt-3 text-xs text-muted-foreground">
                    <span>Vence: {formatDateCO(ticket.due_date)}</span>
                    <Button asChild size="sm" variant="outline">
                      <Link
                        to={`/admin/pqrs/${encodeURIComponent(ticket.tracking_number)}`}
                        state={{ ticket }}
                      >
                        Ver detalle
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Paginación */}
          <div className="flex flex-col items-center justify-between gap-3 sm:flex-row">
            <p className="text-xs text-muted-foreground">
              Mostrando {filteredItems.length} de {total} resultados (página {currentPage} de{' '}
              {totalPages})
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={offset === 0}
                onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_SIZE))}
              >
                <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={offset + PAGE_SIZE >= total}
                onClick={() => setOffset((prev) => prev + PAGE_SIZE)}
              >
                Siguiente
                <ChevronRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
