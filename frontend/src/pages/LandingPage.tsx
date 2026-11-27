import { ArrowRight, Bot, Clock, Lock, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function LandingPage() {
  return (
    <div className="container py-12 md:py-20">
      <section className="mx-auto max-w-3xl text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border bg-card px-3.5 py-1.5 text-xs font-medium text-muted-foreground shadow-sm">
          <ShieldCheck className="h-4 w-4 text-primary" aria-hidden="true" />
          Cumplimiento Ley 1755 de 2015 y protección de datos personales
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-5xl">
          Gestión Inteligente de Peticiones, Quejas, Reclamos y Sugerencias
        </h1>
        <p className="mt-4 text-base text-muted-foreground sm:text-lg">
          SmartPQRS clasifica, prioriza y enruta solicitudes ciudadanas con inteligencia artificial
          resiliente, sanitización previa de datos sensibles y cálculo automático de plazos SLA.
        </p>

        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button asChild size="lg" className="w-full sm:w-auto">
            <Link to="/radicar">
              Radicar una PQRS
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="w-full sm:w-auto">
            <Link to="/login">Acceso funcionarios</Link>
          </Button>
        </div>
      </section>

      <section
        aria-label="Capacidades principales"
        className="mt-16 grid gap-6 md:grid-cols-3"
      >
        <Card>
          <CardHeader>
            <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Bot className="h-5 w-5" aria-hidden="true" />
            </div>
            <CardTitle>Triaje IA con cascada segura</CardTitle>
            <CardDescription>
              Clasificación automática por tipo, prioridad y área responsable con respaldo
              heurístico.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Cada decisión conserva su justificación auditable y registra latencia, modelo y fuente
            de clasificación.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-700 dark:text-emerald-400">
              <Lock className="h-5 w-5" aria-hidden="true" />
            </div>
            <CardTitle>Sanitización de PII</CardTitle>
            <CardDescription>
              Enmascaramiento previo de nombres, documentos, teléfonos y correos con Presidio.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Protege la privacidad del ciudadano antes de enviar el contenido al motor de lenguaje.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-700 dark:text-amber-400">
              <Clock className="h-5 w-5" aria-hidden="true" />
            </div>
            <CardTitle>Control de SLA legal</CardTitle>
            <CardDescription>
              Cálculo determinista en días hábiles colombianos y alertas tempranas de vencimiento.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Monitorea solicitudes vencidas o próximas a vencer para garantizar respuestas oportunas.
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
