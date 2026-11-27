import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { Check, CheckCircle2, ChevronLeft, ChevronRight, Copy, Loader2 } from 'lucide-react';
import { Controller, useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { z } from 'zod';
import { createTicket } from '@/api/pqrs';
import { PriorityBadge, StatusBadge, TicketTypeBadge } from '@/components/common/StatusBadges';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { formatDateCO } from '@/lib/dates';
import { normalizeApiError } from '@/lib/errors';
import { DOCUMENT_TYPE_LABELS } from '@/lib/labels';
import { cn } from '@/lib/utils';
import type { DocumentType, TicketResponse } from '@/types/api';

const radicarSchema = z.object({
  full_name: z.string().trim().min(3, 'El nombre completo debe tener al menos 3 caracteres.'),
  document_type: z.enum(['CC', 'CE', 'NIT', 'PASSPORT', 'TI']),
  document_number: z
    .string()
    .trim()
    .min(5, 'El número de documento debe tener al menos 5 caracteres.'),
  email: z.string().trim().email('Ingresa un correo electrónico válido.'),
  phone: z
    .string()
    .trim()
    .regex(/^\d{7,15}$/, 'Ingresa un teléfono numérico válido (7 a 15 dígitos).'),
  free_text: z
    .string()
    .trim()
    .min(15, 'Describe tu solicitud con al menos 15 caracteres.'),
});

type RadicarFormValues = z.infer<typeof radicarSchema>;

const STEPS = [
  { id: 1, title: 'Datos del solicitante' },
  { id: 2, title: 'Detalle de la solicitud' },
  { id: 3, title: 'Confirmación' },
];

export function RadicarPage() {
  const [step, setStep] = useState(1);
  const [serverError, setServerError] = useState<string | null>(null);
  const [requiresAuthNotice, setRequiresAuthNotice] = useState(false);
  const [createdTicket, setCreatedTicket] = useState<TicketResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const {
    register,
    control,
    trigger,
    handleSubmit,
    getValues,
    watch,
    setError,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<RadicarFormValues>({
    resolver: zodResolver(radicarSchema),
    defaultValues: {
      full_name: '',
      document_type: 'CC',
      document_number: '',
      email: '',
      phone: '',
      free_text: '',
    },
  });

  const freeTextLength = watch('free_text')?.length ?? 0;

  const handleNext = async () => {
    setServerError(null);
    if (step === 1) {
      const valid = await trigger([
        'full_name',
        'document_type',
        'document_number',
        'email',
        'phone',
      ]);
      if (valid) setStep(2);
    } else if (step === 2) {
      const valid = await trigger(['free_text']);
      if (valid) setStep(3);
    }
  };

  const onSubmit = async (values: RadicarFormValues) => {
    setServerError(null);
    setRequiresAuthNotice(false);

    try {
      const response = await createTicket({
        claimant: {
          full_name: values.full_name,
          document_type: values.document_type as DocumentType,
          document_number: values.document_number,
          email: values.email,
          phone: values.phone,
        },
        free_text: values.free_text,
      });
      setCreatedTicket(response);
      toast.success(`PQRS radicada con código ${response.tracking_number}`);
    } catch (error) {
      const normalized = normalizeApiError(error);
      if (normalized.status === 401) {
        setRequiresAuthNotice(true);
      }
      if (normalized.status === 422) {
        Object.entries(normalized.fieldErrors).forEach(([field, msg]) => {
          const mappedField = field.replace(/^claimant\./, '') as keyof RadicarFormValues;
          if (mappedField in values) {
            setError(mappedField, { message: msg });
          }
        });
      }
      setServerError(normalized.message);
      toast.error(normalized.message);
    }
  };

  const handleCopyTracking = async () => {
    if (!createdTicket) return;
    try {
      await navigator.clipboard.writeText(createdTicket.tracking_number);
      setCopied(true);
      toast.success('Número de radicado copiado.');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('No se pudo copiar al portapapeles.');
    }
  };

  if (createdTicket) {
    return (
      <div className="container max-w-2xl py-10">
        <Card className="border-emerald-300 dark:border-emerald-800">
          <CardHeader>
            <div className="mb-2 flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
              <CheckCircle2 className="h-6 w-6" aria-hidden="true" />
              <span className="text-sm font-semibold">Radicación exitosa</span>
            </div>
            <CardTitle className="text-2xl">Tu PQRS fue registrada</CardTitle>
            <CardDescription>
              Conserva tu número de radicado para consultar el seguimiento con nuestros
              funcionarios.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-muted/50 p-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Número de radicado
                </p>
                <p className="mt-1 text-2xl font-bold tracking-tight text-primary">
                  {createdTicket.tracking_number}
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={handleCopyTracking}>
                {copied ? (
                  <>
                    <Check className="h-4 w-4" aria-hidden="true" />
                    Copiado
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" aria-hidden="true" />
                    Copiar radicado
                  </>
                )}
              </Button>
            </div>

            <dl className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-md border p-3">
                <dt className="text-xs text-muted-foreground">Estado actual</dt>
                <dd className="mt-1">
                  <StatusBadge status={createdTicket.status} />
                </dd>
              </div>
              <div className="rounded-md border p-3">
                <dt className="text-xs text-muted-foreground">Tipo clasificado</dt>
                <dd className="mt-1">
                  <TicketTypeBadge ticketType={createdTicket.ticket_type} />
                </dd>
              </div>
              <div className="rounded-md border p-3">
                <dt className="text-xs text-muted-foreground">Prioridad asignada</dt>
                <dd className="mt-1">
                  <PriorityBadge priority={createdTicket.priority} />
                </dd>
              </div>
              <div className="rounded-md border p-3">
                <dt className="text-xs text-muted-foreground">Área responsable</dt>
                <dd className="mt-1 text-sm font-medium">
                  {createdTicket.area?.name ?? 'Por asignar'}
                </dd>
              </div>
              <div className="rounded-md border p-3">
                <dt className="text-xs text-muted-foreground">Fecha de radicación</dt>
                <dd className="mt-1 text-sm font-medium">
                  {formatDateCO(createdTicket.filing_date)}
                </dd>
              </div>
              <div className="rounded-md border p-3">
                <dt className="text-xs text-muted-foreground">Fecha límite SLA</dt>
                <dd className="mt-1 text-sm font-medium">
                  {createdTicket.due_date
                    ? formatDateCO(createdTicket.due_date)
                    : 'Pendiente de validación humana'}
                </dd>
              </div>
            </dl>
          </CardContent>
          <CardFooter className="flex flex-wrap gap-3">
            <Button
              onClick={() => {
                setCreatedTicket(null);
                setStep(1);
                reset();
              }}
            >
              Radicar otra PQRS
            </Button>
            <Button asChild variant="outline">
              <Link to="/">Volver al inicio</Link>
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  const values = getValues();

  return (
    <div className="container max-w-2xl py-10">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Radicar una PQRS</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Completa los 3 pasos para registrar tu petición, queja, reclamo o sugerencia.
        </p>
      </div>

      {/* Stepper */}
      <nav aria-label="Progreso de radicación" className="mb-6">
        <ol className="grid grid-cols-3 gap-2">
          {STEPS.map((item) => {
            const isActive = step === item.id;
            const isCompleted = step > item.id;
            return (
              <li
                key={item.id}
                aria-current={isActive ? 'step' : undefined}
                className={cn(
                  'flex items-center gap-2 rounded-md border px-3 py-2 text-xs font-medium sm:text-sm',
                  isActive && 'border-primary bg-primary/10 text-primary',
                  isCompleted &&
                    'border-emerald-400 bg-emerald-50 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-200',
                  !isActive && !isCompleted && 'text-muted-foreground',
                )}
              >
                <span
                  className={cn(
                    'flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : isCompleted
                        ? 'bg-emerald-600 text-white'
                        : 'bg-muted text-muted-foreground',
                  )}
                >
                  {isCompleted ? '✓' : item.id}
                </span>
                <span className="truncate">{item.title}</span>
              </li>
            );
          })}
        </ol>
      </nav>

      <Card>
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <CardHeader>
            <CardTitle>{STEPS[step - 1].title}</CardTitle>
            <CardDescription>
              {step === 1
                ? 'Ingresa tus datos de contacto para notificaciones.'
                : step === 2
                  ? 'Describe claramente los hechos o solicitud. La información sensible se sanitiza antes de clasificarse.'
                  : 'Verifica que toda la información sea correcta antes de enviar.'}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {serverError ? (
              <Alert variant="destructive" role="alert" aria-live="assertive">
                <AlertTitle>No se pudo radicar la PQRS</AlertTitle>
                <AlertDescription className="space-y-2">
                  <p>{serverError}</p>
                  {requiresAuthNotice ? (
                    <p className="text-xs">
                      Nota técnica: el endpoint actual <code>POST /api/v1/pqrs/</code> exige
                      sesión de funcionario en el backend. Puedes iniciar sesión en{' '}
                      <Link to="/login" className="underline font-semibold">
                        Acceso funcionarios
                      </Link>{' '}
                      sin perder los datos ingresados en esta pestaña.
                    </p>
                  ) : null}
                </AlertDescription>
              </Alert>
            ) : null}

            {step === 1 ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="full_name">Nombre completo *</Label>
                  <Input
                    id="full_name"
                    autoComplete="name"
                    placeholder="Ej. María José Rodríguez"
                    aria-invalid={Boolean(errors.full_name)}
                    aria-describedby={errors.full_name ? 'full_name-error' : undefined}
                    {...register('full_name')}
                  />
                  {errors.full_name ? (
                    <p id="full_name-error" className="text-xs text-destructive" aria-live="polite">
                      {errors.full_name.message}
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="document_type">Tipo de documento *</Label>
                  <Controller
                    name="document_type"
                    control={control}
                    render={({ field }) => (
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger id="document_type" aria-label="Tipo de documento">
                          <SelectValue placeholder="Selecciona un tipo" />
                        </SelectTrigger>
                        <SelectContent>
                          {(Object.keys(DOCUMENT_TYPE_LABELS) as DocumentType[]).map((doc) => (
                            <SelectItem key={doc} value={doc}>
                              {DOCUMENT_TYPE_LABELS[doc]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="document_number">Número de documento *</Label>
                  <Input
                    id="document_number"
                    placeholder="Ej. 1020304050"
                    aria-invalid={Boolean(errors.document_number)}
                    aria-describedby={
                      errors.document_number ? 'document_number-error' : undefined
                    }
                    {...register('document_number')}
                  />
                  {errors.document_number ? (
                    <p
                      id="document_number-error"
                      className="text-xs text-destructive"
                      aria-live="polite"
                    >
                      {errors.document_number.message}
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Correo electrónico *</Label>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="correo@ejemplo.com"
                    aria-invalid={Boolean(errors.email)}
                    aria-describedby={errors.email ? 'email-error' : undefined}
                    {...register('email')}
                  />
                  {errors.email ? (
                    <p id="email-error" className="text-xs text-destructive" aria-live="polite">
                      {errors.email.message}
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Teléfono de contacto *</Label>
                  <Input
                    id="phone"
                    type="tel"
                    autoComplete="tel"
                    placeholder="3001234567"
                    aria-invalid={Boolean(errors.phone)}
                    aria-describedby={errors.phone ? 'phone-error' : undefined}
                    {...register('phone')}
                  />
                  {errors.phone ? (
                    <p id="phone-error" className="text-xs text-destructive" aria-live="polite">
                      {errors.phone.message}
                    </p>
                  ) : null}
                </div>
              </div>
            ) : null}

            {step === 2 ? (
              <div className="space-y-2">
                <Label htmlFor="free_text">Descripción de la PQRS *</Label>
                <Textarea
                  id="free_text"
                  rows={7}
                  placeholder="Describe tu petición, queja, reclamo o sugerencia con el mayor detalle posible..."
                  aria-invalid={Boolean(errors.free_text)}
                  aria-describedby={errors.free_text ? 'free_text-error' : 'free_text-hint'}
                  {...register('free_text')}
                />
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span id="free_text-hint">Mínimo 15 caracteres requeridos.</span>
                  <span>{freeTextLength} caracteres</span>
                </div>
                {errors.free_text ? (
                  <p id="free_text-error" className="text-xs text-destructive" aria-live="polite">
                    {errors.free_text.message}
                  </p>
                ) : null}
              </div>
            ) : null}

            {step === 3 ? (
              <div className="space-y-4">
                <div className="rounded-lg border bg-muted/40 p-4">
                  <h2 className="text-sm font-semibold">Resumen del solicitante</h2>
                  <dl className="mt-2 grid gap-2 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="text-xs text-muted-foreground">Nombre</dt>
                      <dd className="font-medium">{values.full_name}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted-foreground">Documento</dt>
                      <dd className="font-medium">
                        {values.document_type} {values.document_number}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted-foreground">Correo</dt>
                      <dd className="font-medium">{values.email}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted-foreground">Teléfono</dt>
                      <dd className="font-medium">{values.phone}</dd>
                    </div>
                  </dl>
                </div>

                <div className="rounded-lg border bg-muted/40 p-4">
                  <h2 className="text-sm font-semibold">Texto de la solicitud</h2>
                  <p className="mt-2 whitespace-pre-wrap text-sm text-foreground">
                    {values.free_text}
                  </p>
                </div>
              </div>
            ) : null}
          </CardContent>

          <CardFooter className="flex items-center justify-between gap-2 border-t pt-6">
            {step > 1 ? (
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep((prev) => Math.max(1, prev - 1))}
                disabled={isSubmitting}
              >
                <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                Anterior
              </Button>
            ) : (
              <span />
            )}

            {step < 3 ? (
              <Button type="button" onClick={handleNext}>
                Siguiente
                <ChevronRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            ) : (
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    Radicando...
                  </>
                ) : (
                  'Confirmar y radicar PQRS'
                )}
              </Button>
            )}
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
