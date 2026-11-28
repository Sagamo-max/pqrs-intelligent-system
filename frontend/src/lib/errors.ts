import axios from 'axios';
import type { NormalizedApiError } from '@/types/api';

interface FastApiValidationItem {
  loc?: Array<string | number>;
  msg?: string;
}

interface FastApiErrorPayload {
  detail?: string | FastApiValidationItem[];
  message?: string;
}

const STATUS_MESSAGES: Record<number, string> = {
  400: 'La solicitud contiene datos inválidos o no cumple las reglas del negocio.',
  401: 'Tu sesión expiró o no tienes credenciales válidas. Inicia sesión nuevamente.',
  403: 'No tienes permisos suficientes para realizar esta acción.',
  404: 'No se encontró el recurso solicitado.',
  409: 'Ya existe un registro con el mismo identificador.',
  422: 'Revisa los campos marcados antes de continuar.',
  429: 'Demasiados intentos en poco tiempo. Espera unos minutos e inténtalo de nuevo.',
  500: 'Ocurrió un error interno en el servidor. Inténtalo de nuevo más tarde.',
};

export function normalizeApiError(error: unknown): NormalizedApiError {
  if (!axios.isAxiosError(error)) {
    return {
      status: 0,
      message: error instanceof Error ? error.message : 'Error inesperado en la aplicación.',
      fieldErrors: {},
    };
  }

  if (!error.response) {
    return {
      status: 0,
      message:
        'No fue posible conectarse con el servidor API. Verifica la URL configurada o tu conexión.',
      fieldErrors: {},
    };
  }

  const status = error.response.status;
  const data = (error.response.data ?? {}) as FastApiErrorPayload;
  const fieldErrors: Record<string, string> = {};

  if (status === 422 && Array.isArray(data.detail)) {
    for (const item of data.detail) {
      const loc = Array.isArray(item.loc)
        ? item.loc.filter((part) => part !== 'body' && part !== 'query').map(String)
        : [];
      const key = loc.join('.') || 'general';
      fieldErrors[key] = item.msg ?? 'Valor inválido';
    }
  }

  const detailMessage =
    typeof data.detail === 'string'
      ? data.detail
      : typeof data.message === 'string'
        ? data.message
        : undefined;

  return {
    status,
    message: detailMessage ?? STATUS_MESSAGES[status] ?? `Error del servidor (${status}).`,
    fieldErrors,
  };
}
