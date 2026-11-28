import { Skeleton } from '@/components/ui/skeleton';

export function PageLoader() {
  return (
    <div className="space-y-4 p-6" role="status" aria-label="Cargando contenido">
      <Skeleton className="h-8 w-56" />
      <div className="grid gap-4 md:grid-cols-4">
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-28 w-full" />
      </div>
      <Skeleton className="h-64 w-full" />
    </div>
  );
}
