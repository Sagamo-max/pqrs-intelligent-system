import { authClient } from '@/api/client';
import type {
  FuncionarioCreate,
  FuncionarioOut,
  LoginRequest,
  LogoutResponse,
  TokenResponse,
} from '@/types/api';

export async function login(payload: LoginRequest): Promise<TokenResponse> {
  const { data } = await authClient.post<TokenResponse>('/login', payload);
  return data;
}

export async function fetchMe(accessTokenOverride?: string): Promise<FuncionarioOut> {
  const { data } = await authClient.get<FuncionarioOut>('/me', {
    headers: accessTokenOverride ? { Authorization: `Bearer ${accessTokenOverride}` } : undefined,
  });
  return data;
}

export async function logout(refreshToken: string): Promise<LogoutResponse> {
  const { data } = await authClient.post<LogoutResponse>('/logout', {
    refresh_token: refreshToken,
  });
  return data;
}

export async function createFuncionario(payload: FuncionarioCreate): Promise<FuncionarioOut> {
  const { data } = await authClient.post<FuncionarioOut>('/funcionarios', payload);
  return data;
}
