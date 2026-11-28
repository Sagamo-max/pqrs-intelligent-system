import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  Building2,
  ChevronLeft,
  ChevronRight,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  ShieldCheck,
  Users,
  X,
} from 'lucide-react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { logout as apiLogout } from '@/api/auth';
import { RoleBadge } from '@/components/common/StatusBadges';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';
import type { FuncionarioRole } from '@/types/api';

interface NavItem {
  label: string;
  to: string;
  icon: typeof LayoutDashboard;
  roles: FuncionarioRole[];
}

const NAV_ITEMS: NavItem[] = [
  {
    label: 'Dashboard',
    to: '/admin/dashboard',
    icon: LayoutDashboard,
    roles: ['ANALISTA', 'SUPERVISOR', 'MASTER'],
  },
  {
    label: 'PQRS',
    to: '/admin/pqrs',
    icon: FileText,
    roles: ['ANALISTA', 'SUPERVISOR', 'MASTER'],
  },
  {
    label: 'Alertas SLA',
    to: '/admin/alertas',
    icon: AlertTriangle,
    roles: ['ANALISTA', 'SUPERVISOR', 'MASTER'],
  },
  {
    label: 'Áreas',
    to: '/admin/areas',
    icon: Building2,
    roles: ['SUPERVISOR', 'MASTER'],
  },
  {
    label: 'Funcionarios',
    to: '/admin/funcionarios',
    icon: Users,
    roles: ['MASTER'],
  },
];

export function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { user, role, refreshToken, logout } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const effectiveRole: FuncionarioRole = user?.role ?? role ?? 'ANALISTA';
  const visibleItems = NAV_ITEMS.filter((item) => item.roles.includes(effectiveRole));

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!mobileOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMobileOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileOpen]);

  const handleLogout = async () => {
    try {
      if (refreshToken) {
        await apiLogout(refreshToken);
      }
    } catch {
      // Si el token ya expiró en servidor, igual cerramos sesión local.
    } finally {
      logout();
      queryClient.clear();
      toast.success('Sesión cerrada correctamente.');
      navigate('/login', { replace: true });
    }
  };

  const renderLinks = (isCollapsed: boolean) => (
    <nav aria-label="Navegación administrativa" className="flex-1 space-y-1 p-3">
      {visibleItems.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            title={isCollapsed ? item.label : undefined}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                isCollapsed && 'justify-center px-2',
              )
            }
          >
            <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
            {!isCollapsed ? <span>{item.label}</span> : null}
          </NavLink>
        );
      })}
    </nav>
  );

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <a href="#main-content" className="sr-skip-link">
        Saltar al contenido principal
      </a>

      {/* Sidebar Desktop */}
      <aside
        className={cn(
          'hidden border-r bg-card transition-all duration-200 md:flex md:flex-col',
          collapsed ? 'w-[72px]' : 'w-64',
        )}
      >
        <div className="flex h-16 items-center justify-between border-b px-4">
          <Link
            to="/admin/dashboard"
            className={cn(
              'flex items-center gap-2.5 font-bold tracking-tight',
              collapsed && 'mx-auto',
            )}
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <ShieldCheck className="h-5 w-5" aria-hidden="true" />
            </span>
            {!collapsed ? <span>SmartPQRS</span> : null}
          </Link>
          {!collapsed ? (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setCollapsed(true)}
              aria-label="Colapsar menú lateral"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            </Button>
          ) : null}
        </div>

        {renderLinks(collapsed)}

        <div className="border-t p-3">
          {collapsed ? (
            <Button
              variant="ghost"
              size="icon"
              className="w-full"
              onClick={() => setCollapsed(false)}
              aria-label="Expandir menú lateral"
            >
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </Button>
          ) : (
            <Link
              to="/radicar"
              className="block rounded-md border border-dashed px-3 py-2 text-center text-xs font-medium text-muted-foreground transition-colors hover:border-primary hover:text-foreground"
            >
              Ir al portal ciudadano →
            </Link>
          )}
        </div>
      </aside>

      {/* Drawer móvil */}
      {mobileOpen ? (
        <div
          className="fixed inset-0 z-50 flex md:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Menú de navegación"
        >
          <div
            className="fixed inset-0 bg-black/60"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <aside className="relative z-10 flex w-72 max-w-[85vw] flex-col bg-card shadow-xl">
            <div className="flex h-16 items-center justify-between border-b px-4">
              <Link to="/admin/dashboard" className="flex items-center gap-2 font-bold">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <ShieldCheck className="h-4 w-4" aria-hidden="true" />
                </span>
                <span>SmartPQRS</span>
              </Link>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMobileOpen(false)}
                aria-label="Cerrar menú"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </Button>
            </div>
            {renderLinks(false)}
          </aside>
        </div>
      ) : null}

      {/* Contenido principal */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b bg-card/95 px-4 backdrop-blur sm:px-6">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Abrir menú de navegación"
              aria-expanded={mobileOpen}
            >
              <Menu className="h-5 w-5" aria-hidden="true" />
            </Button>
            <div className="hidden sm:block">
              <p className="text-sm font-semibold text-foreground">Consola Operativa PQRS</p>
              <p className="text-xs text-muted-foreground">Triaje inteligente y cumplimiento SLA</p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <ThemeToggle />

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2" aria-label="Menú de usuario">
                  <span className="max-w-[120px] truncate text-sm font-medium">
                    {user?.full_name || user?.username || 'Funcionario'}
                  </span>
                  <RoleBadge role={effectiveRole} />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <span className="text-sm font-medium text-foreground">
                      {user?.full_name || user?.username}
                    </span>
                    <span className="text-xs font-normal text-muted-foreground">
                      @{user?.username} · {effectiveRole}
                    </span>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                  <LogOut className="h-4 w-4" aria-hidden="true" />
                  Cerrar sesión
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <main id="main-content" className="flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
