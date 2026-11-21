export type NavKey = 'Geral' | 'Cadastro' | 'Receitas' | 'Produtos' | 'Configurações';

export interface SystemStatus {
  connected: boolean;
  db_name: string;
  db_path: string;
  db_health?: {
    health_status: 'green' | 'yellow' | 'red';
    health_label: string;
    size_fmt: string;
    health_reasons: string[];
  };
  theme: 'light' | 'dark' | 'system';
  company_name: string;
  units: string[];
  mat_hidden_cols: string[];
  rec_hidden_cols?: string[];
  ai_enabled?: boolean;
  language?: 'pt-BR' | 'en' | 'es';
  currency?: 'BRL' | 'USD' | 'EUR' | 'GBP';
  date_format?: 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD';
  time_format?: '24h' | '12h';
  is_packaged?: boolean;
  version: string;
}

export interface MaterialItem {
  id: number;
  code: string;
  barcode: string;
  name: string;
  brand: string;
  qty: number;
  qty_fmt: string;
  unit: string;
  value: number;
  value_fmt: string;
  category: string;
  date: string;
  mod_date: string;
  active: boolean;
  status: string;
}

export interface MaterialOption {
  id: number;
  code: string;
  name: string;
  purchase_unit: string;
  label: string;
}

export interface MaterialHistoryRow {
  id: number | string;
  raw_date: string;
  date_fmt: string;
  qty: number;
  qty_fmt: string;
  unit: string;
  value: number;
  value_fmt: string;
  brand: string;
  is_today: boolean;
}

export interface ConversionItem {
  id: number;
  name: string;
  base_unit: string;
  factor_to_base: number;
  factor_fmt: string;
}

export interface DeleteCheckItem {
  id: number;
  code: string;
  name: string;
  active: boolean;
  refs: number;
}

export interface DeleteCheckResponse {
  linked: DeleteCheckItem[];
  unlinked: DeleteCheckItem[];
  total: number;
}

export interface RecipeIngredient {
  id?: number;
  material_id: number;
  material_name: string;
  material_brand: string;
  material_unit: string;
  qty: number;
  qty_fmt: string;
  unit: string;
  cost: number;
  cost_fmt: string;
  broken?: boolean;
}

export interface RecipeItem {
  id: number;
  code: string;
  name: string;
  yield_qty: number;
  yield_qty_fmt: string;
  yield_unit: string;
  notes: string;
  created_at: string;
  updated_at: string;
  active: boolean;
  status: string;
  total_cost: number;
  total_cost_fmt: string;
  portion_cost: number;
  portion_cost_fmt: string;
  items_count: number;
  has_broken_items?: boolean;
  items: RecipeIngredient[];
}

export interface RecipeHistoryRow {
  id: number | string;
  date: string;
  date_fmt: string;
  cost: number;
  cost_fmt: string;
  is_today: boolean;
}

export interface CompanyBrandSettings {
  company_name: string;
  company_logo: string;
  brand_theme_enabled: boolean;
  brand_color: string;
  apply_brand_to_sidebar: boolean;
  apply_brand_to_buttons: boolean;
  show_company_name?: boolean;
  logo_shape?: 'round' | 'rect';
}
