import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import type { FuncionarioOut, FuncionarioRole, TokenResponse } from '@/types/api';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  role: FuncionarioRole | null;
  user: FuncionarioOut | null;
  setTokens: (tokens: TokenResponse) => void;
  setUser: (user: FuncionarioOut | null) => void;
  loginSuccess: (tokens: TokenResponse, user: FuncionarioOut) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      role: null,
      user: null,
      setTokens: (tokens) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          role: tokens.role,
        }),
      setUser: (user) =>
        set((state) => ({
          user,
          role: user?.role ?? state.role,
        })),
      loginSuccess: (tokens, user) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          role: user.role,
          user,
        }),
      logout: () =>
        set({
          accessToken: null,
          refreshToken: null,
          role: null,
          user: null,
        }),
    }),
    {
      name: 'smartpqrs-auth',
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
