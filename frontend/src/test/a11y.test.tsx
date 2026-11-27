import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import axe from 'axe-core';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppRoutes } from '@/App';
import { useAuthStore } from '@/stores/authStore';

vi.mock('@/api/dashboard', () => ({
  fetchDashboardMetrics: vi.fn().mockResolvedValue({
    totalTickets: 12,
    overdueCount: 2,
    dueSoonCount: 3,
    onTimeCount: 7,
    classificationStats: {
      last_24h: { total: 4, by_source: { openai: 3, heuristic: 1, fallback: 0 } },
      all_time: { total: 12, by_source: { openai: 9, heuristic: 2, fallback: 1 } },
    },
    byType: [
      { name: 'Petición', value: 5 },
      { name: 'Queja', value: 4 },
      { name: 'Reclamo', value: 3 },
    ],
    byPriority: [
      { name: 'Alta', value: 4 },
      { name: 'Media', value: 5 },
      { name: 'Baja', value: 3 },
    ],
    byArea: [
      { name: 'Atención al Usuario', value: 6 },
      { name: 'Facturación', value: 6 },
    ],
    slaBreakdown: [
      { name: 'A tiempo', value: 7 },
      { name: 'Próximas a vencer', value: 3 },
      { name: 'Vencidas', value: 2 },
    ],
    sourceBreakdown: [
      { name: 'OpenAI', value: 9 },
      { name: 'Heurística', value: 2 },
      { name: 'Fallback', value: 1 },
    ],
    recentTrend: [
      { label: '11-26', total: 5 },
      { label: '11-27', total: 7 },
    ],
    sampleSize: 12,
  }),
}));

function renderRoute(initialEntry: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function expectNoCriticalA11yIssues(container: HTMLElement) {
  const results = await axe.run(container);
  const blocking = results.violations.filter(
    (violation) => violation.impact === 'critical' || violation.impact === 'serious',
  );
  expect(blocking).toEqual([]);
}

describe('Auditoría de accesibilidad axe-core', () => {
  beforeEach(() => {
    useAuthStore.getState().logout();
  });

  it('no presenta errores críticos ni serios en /radicar', async () => {
    const { container } = renderRoute('/radicar');
    await screen.findByRole('heading', { name: /Radicar una PQRS/i });
    await expectNoCriticalA11yIssues(container);
  });

  it('no presenta errores críticos ni serios en /login', async () => {
    const { container } = renderRoute('/login');
    await screen.findByRole('heading', { name: /Iniciar sesión/i });
    await expectNoCriticalA11yIssues(container);
  });

  it('no presenta errores críticos ni serios en /admin/dashboard', async () => {
    useAuthStore.getState().loginSuccess(
      {
        access_token: 'test-access',
        refresh_token: 'test-refresh',
        token_type: 'bearer',
        role: 'MASTER',
      },
      {
        id: '00000000-0000-0000-0000-000000000001',
        username: 'master_test',
        full_name: 'Master Test',
        role: 'MASTER',
        area_id: null,
        is_active: true,
      },
    );

    const { container } = renderRoute('/admin/dashboard');
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Dashboard de Triaje PQRS/i })).toBeInTheDocument();
    });
    await expectNoCriticalA11yIssues(container);
  });
});
