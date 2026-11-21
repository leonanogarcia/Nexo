export type LanguageCode = 'pt-BR' | 'en' | 'es';
export type CurrencyCode = 'BRL' | 'USD' | 'EUR' | 'GBP';
export type DateFormatCode = 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD';
export type TimeFormatCode = '24h' | '12h';

export interface RegionalSettings {
  language: LanguageCode;
  currency: CurrencyCode;
  date_format: DateFormatCode;
  time_format: TimeFormatCode;
}

export const DEFAULT_REGIONAL_SETTINGS: RegionalSettings = {
  language: 'pt-BR',
  currency: 'BRL',
  date_format: 'DD/MM/YYYY',
  time_format: '24h',
};

export interface CurrencyMeta {
  code: CurrencyCode;
  symbol: string;
  label: string;
  decimalSeparator: ',' | '.';
  thousandsSeparator: '.' | ',';
}

export const CURRENCY_META: Record<CurrencyCode, CurrencyMeta> = {
  BRL: {
    code: 'BRL',
    symbol: 'R$',
    label: 'Real Brasileiro (R$)',
    decimalSeparator: ',',
    thousandsSeparator: '.',
  },
  USD: {
    code: 'USD',
    symbol: '$',
    label: 'US Dollar ($)',
    decimalSeparator: '.',
    thousandsSeparator: ',',
  },
  EUR: {
    code: 'EUR',
    symbol: '€',
    label: 'Euro (€)',
    decimalSeparator: ',',
    thousandsSeparator: '.',
  },
  GBP: {
    code: 'GBP',
    symbol: '£',
    label: 'British Pound (£)',
    decimalSeparator: '.',
    thousandsSeparator: ',',
  },
};

export type TranslationDictionary = Record<string, string>;
