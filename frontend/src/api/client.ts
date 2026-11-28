import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/authStore';
import type { TokenResponse } from '@/types/api';

const rawBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(
  /\/+$/,
  '',
);

export const API_V1_BASE_URL = rawBaseUrl;

/**
 * El backend expone el router de autenticación en `/api/auth/*` (sin segmento `/v1`),
 * mientras que los recursos PQRS, Áreas, Alertas y Dashboard usan `/api/v1/*` (y `/api/*`).
 */
export const API_ORIGIN = rawBaseUrl.replace(/\/api\/v1$/i, '');
export const AUTH_BASE_URL = `${API_ORIGIN}/api/auth`;

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  const { refreshToken, setTokens, logout } = useAuthStore.getState();
  if (!refreshToken) {
    logout();
    return null;
  }

  refreshPromise = axios
    .post<TokenResponse>(`${AUTH_BASE_URL}/refresh`, {
      refresh_token: refreshToken,
    })
    .then((response) => {
      setTokens(response.data);
      return response.data.access_token;
    })
    .catch(() => {
      logout();
      return null;
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

function attachInterceptors(instance: AxiosInstance): AxiosInstance {
  instance.interceptors.request.use((config) => {
    const token = useAuthStore.getState().accessToken;
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  instance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as RetryableRequestConfig | undefined;
      const status = error.response?.status;
      const requestUrl = originalRequest?.url ?? '';

      const isAuthLifecycleEndpoint =
        requestUrl.includes('/login') ||
        requestUrl.includes('/refresh') ||
        requestUrl.includes('/logout');

      if (
        status === 401 &&
        originalRequest &&
        !originalRequest._retry &&
        !isAuthLifecycleEndpoint
      ) {
        originalRequest._retry = true;
        const newAccessToken = await refreshAccessToken();

        if (newAccessToken) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return instance(originalRequest);
        }

        const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
        if (
          currentPath !== '/login' &&
          currentPath !== '/radicar' &&
          typeof window !== 'undefined'
        ) {
          window.location.replace('/login');
        }
      }

      return Promise.reject(error);
    },
  );

  return instance;
}

export const apiClient = attachInterceptors(
  axios.create({
    baseURL: API_V1_BASE_URL,
    timeout: 15000,
    headers: {
      'Content-Type': 'application/json',
    },
  }),
);

export const authClient = attachInterceptors(
  axios.create({
    baseURL: AUTH_BASE_URL,
    timeout: 15000,
    headers: {
      'Content-Type': 'application/json',
    },
  }),
);
