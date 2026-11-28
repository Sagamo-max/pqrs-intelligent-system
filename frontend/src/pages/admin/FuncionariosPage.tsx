import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Loader2, UserPlus, Users } from 'lucide-react';
import { Controller, useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';
import { listAreas } from '@/api/areas';
import { createFuncionario } from '@/api/auth';
import { EmptyState } from '@/components/common/EmptyState';
import { RoleBadge } from '@/components/common/StatusBadges';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { normalizeApiError } from '@/lib/errors';
import { ROLE_LABELS } from '@/lib/labels';
import type { FuncionarioOut, FuncionarioRole } from '@/types/api';

const funcionarioSchema = z
  .object({
    username: z.string().trim().min(3, 'Mínimo 3 caracteres.'),
    password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres.'),
    full_name: z.string().trim().optional(),
    role: z.enum(['ANALISTA', 'SUPERVISOR', 'MASTER']),
    area_id: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.role === 'ANALISTA' && !data.area_id) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['area_id'],
        message: 'Un Analista debe tener un área asignada.',
      });
    }
  });

type FuncionarioFormValues = z.infer<typeof funcionarioSchema>;

export function FuncionariosPage() {
  const [createdUsers, setCreatedUsers] = useState<FuncionarioOut[]>([]);

  const areasQuery = useQuery({
    queryKey: ['areas'],
    queryFn: listAreas,
  });

  const {
    register,
    control,
    watch,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FuncionarioFormValues>({
    resolver: zodResolver(funcionarioSchema),
    defaultValues: {
      username: '',
      password: '',
      full_name: '',
      role: 'ANALISTA',
      area_id: '',
    },
  });

  const selectedRole = watch('role');

  const createMutation = useMutation({
    mutationFn: (values: FuncionarioFormValues) =>
      createFuncionario({
        username: values.username,
        password: values.password,
        full_name: values.full_name || null,
        role: values.role,
        area_id: values.role === 'ANALISTA' ? values.area_id || null : null,
      }),
    onSuccess: (created) => {
      toast.success(`Funcionario "${created.username}" creado correctamente.`);
      setCreatedUsers((prev) => [created, ...prev]);
      reset({
        username: '',
        password: '',
        full_name: '',
        role: 'ANALISTA',
        area_id: '',
      });
    },
    onError: (error) => {
      toast.error(normalizeApiError(error).message);
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Gestión de Funcionarios</h1>
        <p className="text-sm text-muted-foreground">
          Crea cuentas de acceso para Analistas, Supervisores y Master (exclusivo rol Master).
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5 text-primary" aria-hidden="true" />
              Registrar funcionario
            </CardTitle>
            <CardDescription>
              El rol Analista requiere seleccionar un área; Supervisor y Master no llevan área.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={handleSubmit((values) => createMutation.mutate(values))}
              className="space-y-4"
              noValidate
            >
              {createMutation.isError ? (
                <Alert variant="destructive" role="alert">
                  <AlertTitle>No fue posible crear el funcionario</AlertTitle>
                  <AlertDescription>
                    {normalizeApiError(createMutation.error).message}
                  </AlertDescription>
                </Alert>
              ) : null}

              <div className="space-y-2">
                <Label htmlFor="func-username">Usuario *</Label>
                <Input
                  id="func-username"
                  placeholder="Ej. analista_cartera"
                  {...register('username')}
                />
                {errors.username ? (
                  <p className="text-xs text-destructive">{errors.username.message}</p>
                ) : null}
              </div>

              <div className="space-y-2">
                <Label htmlFor="func-fullname">Nombre completo</Label>
                <Input
                  id="func-fullname"
                  placeholder="Ej. Laura Gómez"
                  {...register('full_name')}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="func-password">Contraseña inicial *</Label>
                <Input
                  id="func-password"
                  type="password"
                  placeholder="Mínimo 8 caracteres"
                  {...register('password')}
                />
                {errors.password ? (
                  <p className="text-xs text-destructive">{errors.password.message}</p>
                ) : null}
              </div>

              <div className="space-y-2">
                <Label htmlFor="func-role">Rol *</Label>
                <Controller
                  name="role"
                  control={control}
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger id="func-role" aria-label="Rol del funcionario">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {(Object.keys(ROLE_LABELS) as FuncionarioRole[]).map((roleKey) => (
                          <SelectItem key={roleKey} value={roleKey}>
                            {ROLE_LABELS[roleKey]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>

              {selectedRole === 'ANALISTA' ? (
                <div className="space-y-2">
                  <Label htmlFor="func-area">Área asignada *</Label>
                  <Controller
                    name="area_id"
                    control={control}
                    render={({ field }) => (
                      <Select value={field.value ?? ''} onValueChange={field.onChange}>
                        <SelectTrigger id="func-area" aria-label="Área asignada">
                          <SelectValue placeholder="Selecciona un área" />
                        </SelectTrigger>
                        <SelectContent>
                          {(areasQuery.data ?? []).map((area) => (
                            <SelectItem key={area.id} value={area.id}>
                              {area.name} ({area.code})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                  {errors.area_id ? (
                    <p className="text-xs text-destructive">{errors.area_id.message}</p>
                  ) : null}
                </div>
              ) : null}

              <Button type="submit" className="w-full" disabled={createMutation.isPending}>
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    Creando...
                  </>
                ) : (
                  'Crear funcionario'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Funcionarios creados en esta sesión</CardTitle>
            <CardDescription>
              {/* TODO(backend-funcionarios-list): Agregar consumo de GET /api/auth/funcionarios cuando esté disponible */}
              El backend actual solo expone creación (`POST /api/auth/funcionarios`); aquí se
              muestran los usuarios registrados durante tu sesión actual.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {createdUsers.length === 0 ? (
              <EmptyState
                icon={Users}
                title="Sin registros en esta sesión"
                description="Los funcionarios que crees desde el formulario aparecerán listados aquí."
              />
            ) : (
              <ul className="space-y-3">
                {createdUsers.map((item) => (
                  <li
                    key={item.id}
                    className="flex items-center justify-between gap-3 rounded-md border p-3"
                  >
                    <div>
                      <p className="font-semibold">{item.full_name || item.username}</p>
                      <p className="text-xs text-muted-foreground">@{item.username}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <RoleBadge role={item.role} />
                      <Badge variant={item.is_active ? 'success' : 'secondary'}>
                        {item.is_active ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
