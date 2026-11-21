import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  CurrencyCode,
  DateFormatCode,
  DEFAULT_REGIONAL_SETTINGS,
  LanguageCode,
  RegionalSettings,
  TimeFormatCode,
  TranslationDictionary,
} from './types';
import { formatCurrency, formatDate, formatDateTime, formatMoneyInput } from './formatters';
import { ptBR } from './locales/pt-BR';
import { en } from './locales/en';
import { es } from './locales/es';

const DICTIONARIES: Record<LanguageCode, TranslationDictionary> = {
  'pt-BR': ptBR,
  en,
  es,
};

interface I18nContextValue {
  language: LanguageCode;
  currency: CurrencyCode;
  dateFormat: DateFormatCode;
  timeFormat: TimeFormatCode;
  t: (key: string, vars?: Record<string, string | number>) => string;
  formatCurrency: (value: number | string | null | undefined) => string;
  formatMoneyInput: (rawDigits: string) => string;
  formatDate: (input: string | Date | null | undefined) => string;
  formatDateTime: (input: string | Date | null | undefined) => string;
  setRegionalSettings: (next: Partial<RegionalSettings>) => void;
  saveRegionalSettings: (next: Partial<RegionalSettings>) => Promise<boolean>;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [regional, setRegional] = useState<RegionalSettings>(DEFAULT_REGIONAL_SETTINGS);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const res = await fetch('/api/status');
        if (!res.ok || !active) return;
        const data = await res.json();
        setRegional({
          language: (['pt-BR', 'en', 'es'].includes(data.language) ? data.language : 'pt-BR') as LanguageCode,
          currency: (['BRL', 'USD', 'EUR', 'GBP'].includes(data.currency) ? data.currency : 'BRL') as CurrencyCode,
          date_format: (['DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD'].includes(data.date_format)
            ? data.date_format
            : 'DD/MM/YYYY') as DateFormatCode,
          time_format: (['24h', '12h'].includes(data.time_format) ? data.time_format : '24h') as TimeFormatCode,
        });
      } catch {
        // fallback silencioso para defaults
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const setRegionalSettings = useCallback((next: Partial<RegionalSettings>) => {
    setRegional((prev) => ({ ...prev, ...next }));
  }, []);

  const saveRegionalSettings = useCallback(
    async (next: Partial<RegionalSettings>): Promise<boolean> => {
      const merged: RegionalSettings = { ...regional, ...next };
      setRegional(merged);
      try {
        const res = await fetch('/api/settings/regional', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(merged),
        });
        return res.ok;
      } catch {
        return false;
      }
    },
    [regional]
  );

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>): string => {
      const dict = DICTIONARIES[regional.language] || ptBR;
      let text = dict[key] ?? ptBR[key] ?? key;
      if (vars) {
        Object.entries(vars).forEach(([k, v]) => {
          text = text.replace(new RegExp(`\\{\\{${k}\\}\\}`, 'g'), String(v));
        });
      }
      return text;
    },
    [regional.language]
  );

  const value = useMemo<I18nContextValue>(
    () => ({
      language: regional.language,
      currency: regional.currency,
      dateFormat: regional.date_format,
      timeFormat: regional.time_format,
      t,
      formatCurrency: (val) => formatCurrency(val, regional.currency),
      formatMoneyInput: (digits) => formatMoneyInput(digits, regional.currency),
      formatDate: (val) => formatDate(val, regional.date_format),
      formatDateTime: (val) => formatDateTime(val, regional.date_format, regional.time_format),
      setRegionalSettings,
      saveRegionalSettings,
    }),
    [regional, t, setRegionalSettings, saveRegionalSettings]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error('useI18n deve ser usado dentro de I18nProvider.');
  }
  return ctx;
}
