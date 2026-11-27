import { format, formatDistanceToNow, isValid, parseISO } from 'date-fns';
import { es } from 'date-fns/locale/es';

function parseDateValue(value: string | null | undefined): Date | null {
  if (!value) return null;
  const parsed = parseISO(value);
  return isValid(parsed) ? parsed : null;
}

export function formatDateCO(value: string | null | undefined): string {
  const date = parseDateValue(value);
  if (!date) return 'Sin fecha';
  return format(date, "d 'de' MMM 'de' yyyy", { locale: es });
}

export function formatDateTimeCO(value: string | null | undefined): string {
  const date = parseDateValue(value);
  if (!date) return 'Sin fecha';
  return format(date, "d 'de' MMM yyyy, HH:mm", { locale: es });
}

export function formatRelativeCO(value: string | null | undefined): string {
  const date = parseDateValue(value);
  if (!date) return 'Fecha no disponible';
  return formatDistanceToNow(date, { addSuffix: true, locale: es });
}
