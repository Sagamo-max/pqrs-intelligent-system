import { lazy, Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';
import { RequireAuth } from '@/components/auth/RequireAuth';
import { RequireRole } from '@/components/auth/RequireRole';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { PageLoader } from '@/components/common/PageLoader';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { PublicLayout } from '@/components/layout/PublicLayout';

const LandingPage = lazy(() =>
  import('@/pages/LandingPage').then((module) => ({ default: module.LandingPage })),
);
const RadicarPage = lazy(() =>
  import('@/pages/RadicarPage').then((module) => ({ default: module.RadicarPage })),
);
const LoginPage = lazy(() =>
  import('@/pages/LoginPage').then((module) => ({ default: module.LoginPage })),
);
const DashboardPage = lazy(() =>
  import('@/pages/admin/DashboardPage').then((module) => ({ default: module.DashboardPage })),
);
const PqrsListPage = lazy(() =>
  import('@/pages/admin/PqrsListPage').then((module) => ({ default: module.PqrsListPage })),
);
const PqrsDetailPage = lazy(() =>
  import('@/pages/admin/PqrsDetailPage').then((module) => ({ default: module.PqrsDetailPage })),
);
const AlertsPage = lazy(() =>
  import('@/pages/admin/AlertsPage').then((module) => ({ default: module.AlertsPage })),
);
const AreasPage = lazy(() =>
  import('@/pages/admin/AreasPage').then((module) => ({ default: module.AreasPage })),
);
const FuncionariosPage = lazy(() =>
  import('@/pages/admin/FuncionariosPage').then((module) => ({
    default: module.FuncionariosPage,
  })),
);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

export function AppRoutes() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/radicar" element={<RadicarPage />} />
            <Route path="/login" element={<LoginPage />} />
          </Route>

          <Route
            path="/admin"
            element={
              <RequireAuth>
                <AdminLayout />
              </RequireAuth>
            }
          >
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="pqrs" element={<PqrsListPage />} />
            <Route path="pqrs/:id" element={<PqrsDetailPage />} />
            <Route path="alertas" element={<AlertsPage />} />
            <Route
              path="areas"
              element={
                <RequireRole allowedRoles={['MASTER', 'SUPERVISOR']}>
                  <AreasPage />
                </RequireRole>
              }
            />
            <Route
              path="funcionarios"
              element={
                <RequireRole allowedRoles={['MASTER']}>
                  <FuncionariosPage />
                </RequireRole>
              }
            />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
        <Toaster richColors position="top-right" closeButton />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
