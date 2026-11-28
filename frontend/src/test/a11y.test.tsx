import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import axe from 'axe-core';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AppRoutes } from '@/App';
import { useAuthStore } from '@/stores/authStore';

vi.mock('@/api/dashboard', () => ({
  fetchDashboardMetrics: vi.fn().mockResolvedValue({
    total_pqrs: 12,
    por_tipo: {
      PETITION: 5,
      COMPLAINT: 4,
      CLAIM: 3,
    },
    por_area: [
      {
        area_id: '11111111-1111-1111-1111-111111111111',
        area_code: 'ATENCION_USUARIO',
        area_name: 'Atención al Usuario',
        total: 6,
      },
      {
        area_id: '22222222-2222-2222-2222-222222222222',
        area_code: 'FACTURACION',
        area_name: 'Facturación',
        total: 6,
      },
    ],
    por_prioridad: {
      HIGH: 4,
      MEDIUM: 5,
      LOW: 3,
    },
    cumplimiento_sla: {
      vencidas: 2,
      a_tiempo: 9,
      sin_fecha_sla: 1,
      porcentaje_a_tiempo: 81.82,
    },
    generated_at: '2026-11-27T18:00:00Z',
  }),
  getClassificationStats: vi.fn().mockResolvedValue({
    last_24h: { total: 4, by_source: { openai: 3, heuristic: 1, fallback: 0 } },
    all_time: { total: 12, by_source: { openai: 9, heuristic: 2, fallback: 1 } },
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
  const results = await axe.run(container, {
    rules: {
      // jsdom no implementa canvas/layout completo para calcular contraste de píxeles.
      'color-contrast': { enabled: false },
    },
  });
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
    await screen.findByRole('heading', { name: /Radicar una PQRS/i }, { timeout: 10000 });
    await expectNoCriticalA11yIssues(container);
  }, 15000);

  it('no presenta errores críticos ni serios en /login', async () => {
    const { container } = renderRoute('/login');
    await screen.findByRole('heading', { name: /Iniciar sesión/i }, { timeout: 10000 });
    await expectNoCriticalA11yIssues(container);
  }, 15000);

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
    await waitFor(
      () => {
        expect(
          screen.getByRole('heading', { name: /Dashboard de Triaje PQRS/i }),
        ).toBeInTheDocument();
      },
      { timeout: 10000 },
    );
    await expectNoCriticalA11yIssues(container);
  }, 15000);
});
