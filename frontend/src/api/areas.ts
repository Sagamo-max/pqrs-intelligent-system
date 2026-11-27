import { apiClient } from '@/api/client';
import type { AreaCreate, AreaOut, AreaUpdate } from '@/types/api';

export async function listAreas(): Promise<AreaOut[]> {
  const { data } = await apiClient.get<AreaOut[]>('/areas/');
  return data;
}

export async function getArea(areaId: string): Promise<AreaOut> {
  const { data } = await apiClient.get<AreaOut>(`/areas/${encodeURIComponent(areaId)}`);
  return data;
}

export async function createArea(payload: AreaCreate): Promise<AreaOut> {
  const { data } = await apiClient.post<AreaOut>('/areas/', payload);
  return data;
}

/**
 * Nota: El backend implementa `PATCH /api/v1/areas/{area_id}` (no PUT) y exige rol MASTER.
 */
export async function updateArea(areaId: string, payload: AreaUpdate): Promise<AreaOut> {
  const { data } = await apiClient.patch<AreaOut>(
    `/areas/${encodeURIComponent(areaId)}`,
    payload,
  );
  return data;
}
