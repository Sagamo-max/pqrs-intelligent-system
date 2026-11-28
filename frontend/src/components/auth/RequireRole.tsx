import * as React from 'react';
import { ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuthStore } from '@/stores/authStore';
import type { FuncionarioRole } from '@/types/api';

interface RequireRoleProps {
  allowedRoles: FuncionarioRole[];
  children: React.ReactNode;
}

export function RequireRole({ allowedRoles, children }: RequireRoleProps) {
  const user = useAuthStore((state) => state.user);
  const role = useAuthStore((state) => state.role);
  const effectiveRole = user?.role ?? role;

  if (!effectiveRole || !allowedRoles.includes(effectiveRole)) {
    return (
      <div className="flex min-h-[360px] items-center justify-center p-6">
        <Card className="max-w-md border-destructive/40" role="alert">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <ShieldAlert className="h-5 w-5" aria-hidden="true" />
              Acceso restringido (403)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Tu rol actual ({effectiveRole ?? 'Sin rol'}) no tiene permisos para acceder a esta
              sección administrativa.
            </p>
          </CardContent>
          <CardFooter>
            <Button asChild>
              <Link to="/admin/dashboard">Volver al panel</Link>
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
