import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Building2, Edit3, Loader2, Plus } from 'lucide-react';
import { Controller, useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';
import { createArea, listAreas, updateArea } from '@/api/areas';
import { EmptyState } from '@/components/common/EmptyState';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { normalizeApiError } from '@/lib/errors';
import { useAuthStore } from '@/stores/authStore';
import type { AreaOut } from '@/types/api';

const areaSchema = z.object({
  code: z
    .string()
    .trim()
    .min(2, 'El código debe tener al menos 2 caracteres.')
    .max(50, 'Máximo 50 caracteres.'),
  name: z
    .string()
    .trim()
    .min(2, 'El nombre debe tener al menos 2 caracteres.')
    .max(100, 'Máximo 100 caracteres.'),
  description: z.string().trim().optional(),
  manager_email: z.union([z.string().trim().email('Correo inválido.'), z.literal('')]).optional(),
  is_active: z.boolean(),
});

type AreaFormValues = z.infer<typeof areaSchema>;

export function AreasPage() {
  const queryClient = useQueryClient();
  const role = useAuthStore((state) => state.user?.role ?? state.role);
  const canEdit = role === 'MASTER';

  const [modalOpen, setModalOpen] = useState(false);
  const [editingArea, setEditingArea] = useState<AreaOut | null>(null);

  const areasQuery = useQuery({
    queryKey: ['areas'],
    queryFn: listAreas,
  });

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<AreaFormValues>({
    resolver: zodResolver(areaSchema),
    defaultValues: {
      code: '',
      name: '',
      description: '',
      manager_email: '',
      is_active: true,
    },
  });

  const openCreateModal = () => {
    setEditingArea(null);
    reset({ code: '', name: '', description: '', manager_email: '', is_active: true });
    setModalOpen(true);
  };

  const openEditModal = (area: AreaOut) => {
    setEditingArea(area);
    reset({
      code: area.code,
      name: area.name,
      description: area.description ?? '',
      manager_email: area.manager_email ?? '',
      is_active: area.is_active,
    });
    setModalOpen(true);
  };

  const saveMutation = useMutation({
    mutationFn: async (values: AreaFormValues) => {
      if (editingArea) {
        return updateArea(editingArea.id, {
          name: values.name,
          description: values.description || null,
          manager_email: values.manager_email || null,
          is_active: values.is_active,
        });
      }
      return createArea({
        code: values.code.toUpperCase(),
        name: values.name,
        description: values.description || null,
        manager_email: values.manager_email || null,
        is_active: values.is_active,
      });
    },
    onSuccess: (saved) => {
      toast.success(
        editingArea ? `Área "${saved.name}" actualizada.` : `Área "${saved.name}" creada.`,
      );
      queryClient.invalidateQueries({ queryKey: ['areas'] });
      setModalOpen(false);
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).message);
    },
  });

  const areas = areasQuery.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Catálogo de Áreas</h1>
          <p className="text-sm text-muted-foreground">
            Áreas responsables de atender y resolver PQRS.
          </p>
        </div>

        {canEdit ? (
          <Button onClick={openCreateModal}>
            <Plus className="h-4 w-4" aria-hidden="true" />
            Nueva área
          </Button>
        ) : null}
      </div>

      {!canEdit ? (
        <Alert variant="info">
          <AlertTitle>Modo solo lectura</AlertTitle>
          <AlertDescription>
            En el backend actual, la creación y edición de áreas está restringida al rol{' '}
            <strong>MASTER</strong>. Puedes consultar el catálogo completo como Supervisor.
          </AlertDescription>
        </Alert>
      ) : null}

      {areasQuery.isLoading ? (
        <div className="space-y-3" aria-busy="true" aria-label="Cargando áreas">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : areasQuery.isError ? (
        <Alert variant="destructive" role="alert">
          <AlertTitle>Error al cargar áreas</AlertTitle>
          <AlertDescription>{normalizeApiError(areasQuery.error).message}</AlertDescription>
        </Alert>
      ) : areas.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No hay áreas registradas"
          description="Crea la primera área responsable para enrutar PQRS."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {areas.map((area) => (
            <Card key={area.id}>
              <CardContent className="flex h-full flex-col justify-between gap-4 pt-6">
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-xs font-mono text-muted-foreground">{area.code}</p>
                      <h2 className="text-base font-semibold">{area.name}</h2>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge variant={area.is_active ? 'success' : 'secondary'}>
                        {area.is_active ? 'Activa' : 'Inactiva'}
                      </Badge>
                      {area.is_default ? <Badge variant="info">Por defecto</Badge> : null}
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {area.description || 'Sin descripción registrada.'}
                  </p>
                  {area.manager_email ? (
                    <p className="text-xs text-muted-foreground">
                      Responsable: <span className="font-medium">{area.manager_email}</span>
                    </p>
                  ) : null}
                </div>

                {canEdit ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openEditModal(area)}
                    className="w-full"
                  >
                    <Edit3 className="h-4 w-4" aria-hidden="true" />
                    Editar área
                  </Button>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent>
          <form
            onSubmit={handleSubmit((values) => saveMutation.mutate(values))}
            className="space-y-4"
          >
            <DialogHeader>
              <DialogTitle>{editingArea ? 'Editar área' : 'Crear nueva área'}</DialogTitle>
              <DialogDescription>
                {editingArea
                  ? 'Actualiza los datos de contacto o estado del área.'
                  : 'Define el código único y nombre del área.'}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-2">
              <Label htmlFor="area-code">Código *</Label>
              <Input
                id="area-code"
                disabled={Boolean(editingArea)}
                placeholder="Ej. FACTURACION"
                {...register('code')}
              />
              {errors.code ? (
                <p className="text-xs text-destructive">{errors.code.message}</p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="area-name">Nombre *</Label>
              <Input id="area-name" placeholder="Ej. Facturación y Cartera" {...register('name')} />
              {errors.name ? (
                <p className="text-xs text-destructive">{errors.name.message}</p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="area-email">Correo del responsable</Label>
              <Input
                id="area-email"
                type="email"
                placeholder="lider@entidad.gov.co"
                {...register('manager_email')}
              />
              {errors.manager_email ? (
                <p className="text-xs text-destructive">{errors.manager_email.message}</p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="area-description">Descripción</Label>
              <Textarea id="area-description" rows={3} {...register('description')} />
            </div>

            <div className="flex items-center justify-between rounded-md border p-3">
              <div>
                <Label htmlFor="area-active">Área activa</Label>
                <p className="text-xs text-muted-foreground">
                  Disponible para recibir nuevas PQRS.
                </p>
              </div>
              <Controller
                name="is_active"
                control={control}
                render={({ field }) => (
                  <Switch id="area-active" checked={field.value} onCheckedChange={field.onChange} />
                )}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={saveMutation.isPending}>
                {saveMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    Guardando...
                  </>
                ) : editingArea ? (
                  'Guardar cambios'
                ) : (
                  'Crear área'
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
