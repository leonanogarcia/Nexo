import { CURRENCY_META, CurrencyCode, DateFormatCode, TimeFormatCode } from './types';

/**
 * Formata um valor numérico para a moeda configurada sem aplicar conversão cambial.
 */
export function formatCurrency(value: number | string | null | undefined, currency: CurrencyCode = 'BRL'): string {
  const num = typeof value === 'number' ? value : Number(String(value ?? 0).replace(',', '.'));
  const safe = Number.isFinite(num) ? num : 0;
  const meta = CURRENCY_META[currency] || CURRENCY_META.BRL;
  const neg = safe < 0 ? '-' : '';
  const abs = Math.abs(safe).toFixed(2);
  const [intPart, decPart] = abs.split('.');
  const groupedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, meta.thousandsSeparator);
  return `${neg}${meta.symbol} ${groupedInt}${meta.decimalSeparator}${decPart}`;
}

/**
 * Formata dígitos digitados em tempo real para campos monetários conforme a moeda configurada.
 */
export function formatMoneyInput(rawDigits: string, currency: CurrencyCode = 'BRL'): string {
  const meta = CURRENCY_META[currency] || CURRENCY_META.BRL;
  const digits = rawDigits.replace(/\D/g, '');
  if (!digits) {
    return `${meta.symbol} 0${meta.decimalSeparator}00`;
  }
  const cents = parseInt(digits, 10);
  const fixed = (cents / 100).toFixed(2);
  const [intPart, decPart] = fixed.split('.');
  const groupedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, meta.thousandsSeparator);
  return `${meta.symbol} ${groupedInt}${meta.decimalSeparator}${decPart}`;
}

/**
 * Extrai ano, mês e dia de uma string ISO/BR ou objeto Date.
 */
function parseDateParts(input: string | Date | null | undefined): {
  year: string;
  month: string;
  day: string;
  hours: number;
  minutes: number;
  hasTime: boolean;
} | null {
  if (!input) return null;
  if (input instanceof Date) {
    if (Number.isNaN(input.getTime())) return null;
    return {
      year: String(input.getFullYear()),
      month: String(input.getMonth() + 1).padStart(2, '0'),
      day: String(input.getDate()).padStart(2, '0'),
      hours: input.getHours(),
      minutes: input.getMinutes(),
      hasTime: true,
    };
  }
  const raw = String(input).trim();
  if (!raw) return null;

  // ISO: YYYY-MM-DD ou YYYY-MM-DDTHH:mm...
  const isoMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/);
  if (isoMatch) {
    return {
      year: isoMatch[1],
      month: isoMatch[2],
      day: isoMatch[3],
      hours: isoMatch[4] ? Number(isoMatch[4]) : 0,
      minutes: isoMatch[5] ? Number(isoMatch[5]) : 0,
      hasTime: Boolean(isoMatch[4]),
    };
  }

  // BR: DD/MM/YYYY [HH:mm]
  const brMatch = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2}))?/);
  if (brMatch) {
    return {
      year: brMatch[3],
      month: brMatch[2],
      day: brMatch[1],
      hours: brMatch[4] ? Number(brMatch[4]) : 0,
      minutes: brMatch[5] ? Number(brMatch[5]) : 0,
      hasTime: Boolean(brMatch[4]),
    };
  }

  return null;
}

/**
 * Formata apenas a data conforme o padrão escolhido (DD/MM/YYYY, MM/DD/YYYY ou YYYY-MM-DD).
 */
export function formatDate(input: string | Date | null | undefined, dateFormat: DateFormatCode = 'DD/MM/YYYY'): string {
  const p = parseDateParts(input);
  if (!p) return typeof input === 'string' ? input : '';
  if (dateFormat === 'MM/DD/YYYY') return `${p.month}/${p.day}/${p.year}`;
  if (dateFormat === 'YYYY-MM-DD') return `${p.year}-${p.month}-${p.day}`;
  return `${p.day}/${p.month}/${p.year}`;
}

/**
 * Formata data e hora conforme os formatos configurados (24h ou 12h).
 */
export function formatDateTime(
  input: string | Date | null | undefined,
  dateFormat: DateFormatCode = 'DD/MM/YYYY',
  timeFormat: TimeFormatCode = '24h'
): string {
  const p = parseDateParts(input);
  if (!p) return typeof input === 'string' ? input : '';
  const datePart = formatDate(input, dateFormat);
  if (!p.hasTime) return datePart;

  if (timeFormat === '12h') {
    const suffix = p.hours >= 12 ? 'PM' : 'AM';
    const h12 = p.hours % 12 || 12;
    return `${datePart} ${String(h12).padStart(2, '0')}:${String(p.minutes).padStart(2, '0')} ${suffix}`;
  }
  return `${datePart} ${String(p.hours).padStart(2, '0')}:${String(p.minutes).padStart(2, '0')}`;
}
