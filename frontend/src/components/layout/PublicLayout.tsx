import { ShieldCheck } from 'lucide-react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export function PublicLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <a href="#main-content" className="sr-skip-link">
        Saltar al contenido principal
      </a>

      <header className="sticky top-0 z-30 border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85">
        <div className="container flex h-16 items-center justify-between gap-4">
          <Link
            to="/"
            className="flex items-center gap-2.5 text-base font-bold tracking-tight text-foreground"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            </span>
            <span>SmartPQRS</span>
          </Link>

          <nav aria-label="Navegación pública" className="flex items-center gap-2 sm:gap-3">
            <NavLink
              to="/radicar"
              className={({ isActive }) =>
                cn(
                  'rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent',
                  isActive ? 'bg-accent text-foreground' : 'text-muted-foreground',
                )
              }
            >
              Radicar PQRS
            </NavLink>
            <Button asChild variant="default" size="sm">
              <Link to="/login">Acceso funcionarios</Link>
            </Button>
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main id="main-content" className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t bg-card py-6 text-center text-xs text-muted-foreground">
        <div className="container flex flex-col items-center justify-between gap-2 sm:flex-row">
          <p>SmartPQRS — Sistema Inteligente de Triaje y Trazabilidad PQRS (Ley 1755 de 2015)</p>
          <p>Portal ciudadano y administrativo</p>
        </div>
      </footer>
    </div>
  );
}
