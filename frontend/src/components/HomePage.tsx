import React, { useEffect, useMemo, useState } from 'react';
import {
  ColumnResizeHandle,
  FeedbackType,
  NexoColumnDef,
  OpenSectionIcon,
  RoundedActionButton,
  RoundedDropdown,
  RoundedEntry,
  useNexoColumnWidths,
} from './DesignSystem';
import { NavKey } from '../types';
import { useI18n } from '../i18n/I18nContext';

interface HomePageProps {
  onNavigate: (tab: NavKey) => void;
  onNotify: (msg: string, type?: FeedbackType) => void;
}

interface BiPreferences {
  default_period: string;
  chart_style: 'auto' | 'bar' | 'line' | string;
  cost_variation_alert_pct: number;
  target_margin_pct: number;
  include_inactive: boolean;
  color_palette: 'nexo' | 'brand' | 'contrast' | 'corporate' | 'custom' | string;
  custom_primary_color: string;
  custom_secondary_color: string;
  brand_color: string;
}

interface DashboardData {
  period: string;
  bi_preferences: BiPreferences;
  kpis: {
    products: number;
    recipes: number;
    materials: number;
  };
  avg_product_cost: number;
  avg_product_cost_fmt: string;
  avg_margin_pct: number | null;
  purchases_by_category: {
    category: string;
    total: number;
    total_fmt: string;
    pct: number;
  }[];
  price_variations: {
    name: string;
    min_fmt: string;
    max_fmt: string;
    pct: number;
    is_alert: boolean;
  }[];
  recent_purchases: {
    id: number;
    date: string;
    description: string;
    type: string;
    value: number;
    value_fmt: string;
  }[];
  purchase_pie_slices: {
    name: string;
    value: number;
    value_fmt: string;
    pct: number;
  }[];
  cost_pie_slices: {
    name: string;
    value: number;
    value_fmt: string;
    pct: number;
  }[];
  cost_evolution_series: {
    month: string;
    avg_cost: number;
  }[];
  below_target_margin: {
    id: number;
    name: string;
    unit_cost_fmt: string;
    sale_price_fmt: string;
    margin_pct: number;
  }[];
  profit_ranking: {
    id: number;
    name: string;
    profit: number;
    profit_fmt: string;
    margin_pct: number;
  }[];
  highest_cost_products: {
    id: number;
    name: string;
    unit_cost: number;
    unit_cost_fmt: string;
    sale_price_fmt: string;
  }[];
  pending_items: {
    key: string;
    label: string;
    count: number;
    target_tab: NavKey;
  }[];
}

interface BiDetailsData {
  period: string;
  months: string[];
  insumo: {
    id: string;
    item: string;
    mes: string;
    min: number;
    min_fmt: string;
    max: number;
    max_fmt: string;
    media: number;
    media_fmt: string;
    variacao_pct: number;
  }[];
  marca: {
    id: string;
    item: string;
    marca: string;
    mes: string;
    min: number;
    min_fmt: string;
    max: number;
    max_fmt: string;
    media: number;
    media_fmt: string;
  }[];
  custos: {
    id: string;
    tipo: string;
    item: string;
    mes: string;
    custo: number;
    custo_fmt: string;
  }[];
}

function getBiPaletteColors(prefs?: BiPreferences): string[] {
  if (!prefs) return ['#F28C28', '#18223A', '#2F72FF', '#18C39B', '#9C5CFF'];
  switch (prefs.color_palette) {
    case 'brand':
      return [prefs.brand_color || '#F28C28', '#18223A', '#2563EB', '#18C39B', '#60769D'];
    case 'contrast':
      return ['#E11D48', '#2563EB', '#F59E0B', '#059669', '#7C3AED'];
    case 'corporate':
      return ['#1E3A8A', '#0284C7', '#0D9488', '#6366F1', '#475569'];
    case 'custom':
      return [
        prefs.custom_primary_color || '#F28C28',
        prefs.custom_secondary_color || '#18223A',
        '#2563EB',
        '#18C39B',
        '#94A3B8',
      ];
    default:
      return ['#F28C28', '#2F72FF', '#18C39B', '#9C5CFF', '#FF5E74'];
  }
}

function fmtMoneyBR(val: number): string {
  return `R$ ${val.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

interface DonutChartProps {
  slices: { name: string; value: number; value_fmt: string; pct: number }[];
  palette: string[];
  emptyMessage: string;
}

const BiDonutChart: React.FC<DonutChartProps> = ({ slices, palette, emptyMessage }) => {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  if (!slices || slices.length === 0) {
    return (
      <div className="h-[175px] flex items-center justify-center text-[12.5px] text-[#60769D] dark:text-[#93A4C6]">
        {emptyMessage}
      </div>
    );
  }

  const total = slices.reduce((acc, s) => acc + s.value, 0) || 1;
  const radius = 52;
  const strokeWidth = 22;
  const circumference = 2 * Math.PI * radius;
  let cumulative = 0;

  return (
    <div className="flex flex-col sm:flex-row items-center gap-5 pt-2">
      <div className="relative w-[144px] h-[144px] shrink-0 flex items-center justify-center">
        <svg viewBox="0 0 140 140" className="w-full h-full -rotate-90">
          {slices.map((slice, idx) => {
            const frac = slice.value / total;
            const dash = Math.max(frac * circumference, 2);
            const offset = -cumulative * circumference;
            cumulative += frac;
            const color = palette[idx % palette.length];
            const isHovered = hoverIdx === idx;
            return (
              <circle
                key={slice.name + idx}
                cx="70"
                cy="70"
                r={radius}
                fill="none"
                stroke={color}
                strokeWidth={isHovered ? strokeWidth + 4 : strokeWidth}
                strokeDasharray={`${dash} ${circumference}`}
                strokeDashoffset={offset}
                className="transition-all duration-150 cursor-pointer"
                onMouseEnter={() => setHoverIdx(idx)}
                onMouseLeave={() => setHoverIdx(null)}
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center px-3">
          {hoverIdx !== null && slices[hoverIdx] ? (
            <>
              <span className="text-[12px] font-bold text-[#18223A] dark:text-[#F4F7FF] leading-tight">
                {slices[hoverIdx].pct.toFixed(0)}%
              </span>
              <span className="text-[10px] text-[#60769D] dark:text-[#93A4C6] truncate max-w-[78px]" title={slices[hoverIdx].name}>
                {slices[hoverIdx].name}
              </span>
            </>
          ) : (
            <span className="text-[11px] font-bold text-[#60769D] dark:text-[#93A4C6]">
              100%
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 w-full space-y-2 min-w-0">
        {slices.map((slice, idx) => {
          const color = palette[idx % palette.length];
          const isHovered = hoverIdx === idx;
          return (
            <div
              key={slice.name + idx}
              onMouseEnter={() => setHoverIdx(idx)}
              onMouseLeave={() => setHoverIdx(null)}
              className={`flex items-center justify-between gap-2 px-2 py-1 rounded-full transition-colors cursor-default ${
                isHovered ? 'bg-[#F5F8FD] dark:bg-[#142544]' : ''
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
                <span className="text-[12px] font-semibold text-[#18223A] dark:text-[#F4F7FF] truncate" title={slice.name}>
                  {slice.name}
                </span>
              </div>
              <div className="flex items-center gap-2.5 shrink-0 text-[12px]">
                <span className="text-[#18223A] dark:text-[#F4F7FF] font-semibold">{slice.value_fmt}</span>
                <span className="text-[#60769D] dark:text-[#93A4C6] font-bold w-10 text-right">
                  {slice.pct.toFixed(0)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

interface CostEvolutionChartProps {
  series: { month: string; avg_cost: number }[];
  chartStyle: string;
  primaryColor: string;
  secondaryColor: string;
}

const CostEvolutionChart: React.FC<CostEvolutionChartProps> = ({
  series,
  chartStyle,
  primaryColor,
  secondaryColor,
}) => {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  if (!series || series.length === 0) {
    return (
      <div className="h-[205px] flex items-center justify-center text-[12.5px] text-[#60769D] dark:text-[#93A4C6]">
        Ainda não há histórico suficiente para exibir este gráfico.
      </div>
    );
  }

  const W = 640;
  const H = 205;
  const padL = 78;
  const padR = 24;
  const padT = 22;
  const padB = 30;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;
  const innerPad = 28;
  const innerW = Math.max(10, plotW - innerPad * 2);

  const vals = series.map((s) => s.avg_cost);
  let minV = Math.min(...vals);
  let maxV = Math.max(...vals);
  if (maxV === minV) {
    maxV = minV + Math.max(Math.abs(minV) * 0.2, 10);
    minV = Math.max(0, minV - Math.max(Math.abs(minV) * 0.2, 10));
  }

  const getX = (i: number) =>
    series.length === 1 ? padL + plotW / 2 : padL + innerPad + (i * innerW) / (series.length - 1);
  const getY = (v: number) => padT + plotH - ((v - minV) / (maxV - minV)) * plotH;

  const showBars = chartStyle === 'bar' || (chartStyle === 'auto' && series.length <= 4);
  const showLine = chartStyle === 'line' || chartStyle === 'auto';

  const points = series.map((s, i) => `${getX(i)},${getY(s.avg_cost)}`).join(' ');
  const areaPoints =
    series.length >= 2
      ? `${getX(0)},${padT + plotH} ${points} ${getX(series.length - 1)},${padT + plotH}`
      : '';

  const barWidth = Math.min(22, Math.max(12, innerW / Math.max(series.length * 3, 6)));

  return (
    <div className="relative w-full h-[205px]">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full overflow-visible">
        {[0, 1, 2, 3, 4].map((step) => {
          const y = padT + (plotH * step) / 4;
          const v = maxV - ((maxV - minV) * step) / 4;
          return (
            <g key={step}>
              <line
                x1={padL}
                y1={y}
                x2={W - padR}
                y2={y}
                className="stroke-[#E6EEF8] dark:stroke-[#1E3156]"
                strokeWidth="1"
              />
              <text
                x={padL - 8}
                y={y + 3}
                textAnchor="end"
                className="fill-[#60769D] dark:fill-[#93A4C6] text-[10px]"
              >
                {fmtMoneyBR(v)}
              </text>
            </g>
          );
        })}

        {showBars &&
          series.map((s, i) => {
            const x = getX(i) - barWidth / 2;
            const y = getY(s.avg_cost);
            const h = Math.max(4, padT + plotH - y);
            return (
              <rect
                key={`bar-${s.month}`}
                x={x}
                y={y}
                width={barWidth}
                height={h}
                rx="6"
                fill={chartStyle === 'bar' ? primaryColor : secondaryColor}
                opacity={hoverIdx === i ? 0.95 : chartStyle === 'bar' ? 0.85 : 0.22}
                className="transition-opacity cursor-pointer"
                onMouseEnter={() => setHoverIdx(i)}
                onMouseLeave={() => setHoverIdx(null)}
              />
            );
          })}

        {showLine && series.length >= 2 && (
          <>
            <polygon points={areaPoints} fill={primaryColor} opacity="0.12" pointerEvents="none" />
            <polyline
              fill="none"
              stroke={primaryColor}
              strokeWidth="2.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={points}
              pointerEvents="none"
            />
          </>
        )}

        {series.map((s, i) => {
          const cx = getX(i);
          const cy = getY(s.avg_cost);
          const hitW = Math.max(36, innerW / Math.max(series.length, 1));
          return (
            <g key={s.month}>
              {showLine && (
                <circle
                  cx={cx}
                  cy={cy}
                  r={hoverIdx === i ? 6 : 4.2}
                  fill={primaryColor}
                  stroke="#FFFFFF"
                  strokeWidth="1.5"
                  pointerEvents="none"
                  className="transition-all"
                />
              )}
              <text
                x={cx}
                y={H - 8}
                textAnchor="middle"
                pointerEvents="none"
                className="fill-[#60769D] dark:fill-[#93A4C6] text-[10px]"
              >
                {s.month}
              </text>
              {/* Faixa invisível no topo garantindo hover e clique sem bloqueio da sombra */}
              <rect
                x={cx - hitW / 2}
                y={padT}
                width={hitW}
                height={plotH + 18}
                fill="transparent"
                className="cursor-pointer"
                onMouseEnter={() => setHoverIdx(i)}
                onMouseLeave={() => setHoverIdx(null)}
                onClick={() => setHoverIdx((prev) => (prev === i ? null : i))}
              />
            </g>
          );
        })}
      </svg>

      {hoverIdx !== null && series[hoverIdx] && (
        <div className="absolute top-0 left-20 px-3 py-1 rounded-full bg-[#18223A] dark:bg-[#0E1B35] text-white text-[11px] font-semibold shadow-md pointer-events-none border border-[#24385E]">
          {series[hoverIdx].month}: {fmtMoneyBR(series[hoverIdx].avg_cost)}
        </div>
      )}
    </div>
  );
};

// ---------- BI Details Modal Table Specs (Padrão Único de Tabelas) ----------

type BiTabKey = 'insumo' | 'marca' | 'custos';

interface BiColSpec extends NexoColumnDef {
  align: 'left' | 'center';
}

const BI_INSUMO_COLS: BiColSpec[] = [
  { key: 'item', label: 'Insumo', width: 260, align: 'left' },
  { key: 'mes', label: 'Mês', width: 110, align: 'center' },
  { key: 'min_fmt', label: 'Mínimo', width: 130, align: 'center' },
  { key: 'max_fmt', label: 'Máximo', width: 130, align: 'center' },
  { key: 'media_fmt', label: 'Média', width: 130, align: 'center' },
  { key: 'variacao_pct', label: 'Variação', width: 115, align: 'center' },
];

const BI_MARCA_COLS: BiColSpec[] = [
  { key: 'item', label: 'Insumo', width: 220, align: 'left' },
  { key: 'marca', label: 'Marca', width: 160, align: 'left' },
  { key: 'mes', label: 'Mês', width: 105, align: 'center' },
  { key: 'min_fmt', label: 'Mínimo', width: 120, align: 'center' },
  { key: 'max_fmt', label: 'Máximo', width: 120, align: 'center' },
  { key: 'media_fmt', label: 'Média', width: 120, align: 'center' },
];

const BI_CUSTOS_COLS: BiColSpec[] = [
  { key: 'tipo', label: 'Tipo', width: 120, align: 'left' },
  { key: 'item', label: 'Receita / Produto', width: 320, align: 'left' },
  { key: 'mes', label: 'Mês', width: 120, align: 'center' },
  { key: 'custo_fmt', label: 'Custo', width: 160, align: 'center' },
];

export const HomePage: React.FC<HomePageProps> = ({ onNavigate, onNotify }) => {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<string | null>(null);

  // BI Modal state
  const [biModalOpen, setBiModalOpen] = useState(false);
  const [biTab, setBiTab] = useState<BiTabKey>('insumo');
  const [biDetails, setBiDetails] = useState<BiDetailsData | null>(null);
  const [biLoading, setBiLoading] = useState(false);
  const [biSearch, setBiSearch] = useState('');
  const [biMonthFilter, setBiMonthFilter] = useState('Todos os meses');
  const [biSortCol, setBiSortCol] = useState<string>('mes');
  const [biSortDir, setBiSortDir] = useState<'ASC' | 'DESC'>('DESC');

  const activeCols = useMemo(() => {
    if (biTab === 'marca') return BI_MARCA_COLS;
    if (biTab === 'custos') return BI_CUSTOS_COLS;
    return BI_INSUMO_COLS;
  }, [biTab]);

  const insumoWidths = useNexoColumnWidths('nexo_col_widths_bi_insumo_v1', BI_INSUMO_COLS);
  const marcaWidths = useNexoColumnWidths('nexo_col_widths_bi_marca_v1', BI_MARCA_COLS);
  const custosWidths = useNexoColumnWidths('nexo_col_widths_bi_custos_v1', BI_CUSTOS_COLS);

  const activeWidths = biTab === 'marca' ? marcaWidths : biTab === 'custos' ? custosWidths : insumoWidths;
  const {
    colWidths: biColWidths,
    startResize: startBiResize,
    autoFitColumn: autoFitBiColumn,
    shouldIgnoreSortClick: shouldIgnoreBiSort,
  } = activeWidths;

  const fetchDashboard = async (periodOverride?: string) => {
    setLoading(true);
    try {
      const p = periodOverride ?? selectedPeriod;
      const url = p ? `/api/dashboard?period=${encodeURIComponent(p)}` : '/api/dashboard';
      const res = await fetch(url);
      if (!res.ok) throw new Error('Erro ao carregar o Dashboard.');
      const data: DashboardData = await res.json();
      setDashboard(data);
      if (!selectedPeriod && data.period) {
        setSelectedPeriod(data.period);
      }
    } catch (e: any) {
      onNotify(e.message || 'Erro ao carregar dados do Início.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchDashboard();
  }, []);

  const openBiModal = async (initialTab: BiTabKey) => {
    setBiTab(initialTab);
    setBiSearch('');
    setBiMonthFilter('Todos os meses');
    setBiSortCol('mes');
    setBiSortDir('DESC');
    setBiModalOpen(true);
    setBiLoading(true);
    try {
      const p = selectedPeriod || dashboard?.period || '12m';
      const res = await fetch(`/api/bi/details?period=${encodeURIComponent(p)}`);
      if (!res.ok) throw new Error('Erro ao carregar detalhes de BI.');
      const data: BiDetailsData = await res.json();
      setBiDetails(data);
    } catch (e: any) {
      onNotify(e.message || 'Erro ao carregar detalhes do BI.', 'error');
    } finally {
      setBiLoading(false);
    }
  };

  const filteredBiRows = useMemo(() => {
    if (!biDetails) return [];
    const raw: any[] = biDetails[biTab] || [];
    const q = biSearch.trim().toLowerCase();
    const filtered = raw.filter((row) => {
      if (biMonthFilter !== 'Todos os meses' && row.mes !== biMonthFilter) return false;
      if (!q) return true;
      return Object.values(row).some((v) => String(v ?? '').toLowerCase().includes(q));
    });

    const sorted = [...filtered].sort((a, b) => {
      const av = a[biSortCol];
      const bv = b[biSortCol];
      if (typeof av === 'number' && typeof bv === 'number') {
        return biSortDir === 'ASC' ? av - bv : bv - av;
      }
      const sa = String(av ?? '').toLowerCase();
      const sb = String(bv ?? '').toLowerCase();
      return biSortDir === 'ASC' ? sa.localeCompare(sb) : sb.localeCompare(sa);
    });
    return sorted;
  }, [biDetails, biTab, biSearch, biMonthFilter, biSortCol, biSortDir]);

  const handleBiSort = (colKey: string) => {
    if (shouldIgnoreBiSort()) return;
    if (biSortCol === colKey) {
      setBiSortDir((d) => (d === 'ASC' ? 'DESC' : 'ASC'));
    } else {
      setBiSortCol(colKey);
      setBiSortDir('ASC');
    }
  };

  const handleExportBiCsv = () => {
    if (!filteredBiRows.length) {
      onNotify('Não há registros filtrados para exportar.', 'warning');
      return;
    }
    const headers = activeCols.map((c) => c.label);
    const lines = [
      headers.join(';'),
      ...filteredBiRows.map((row) =>
        activeCols
          .map((c) => {
            const val = c.key === 'variacao_pct' ? `${row[c.key]}%` : String(row[c.key] ?? '');
            return `"${val.replace(/"/g, '""')}"`;
          })
          .join(';')
      ),
    ];
    const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nexo_bi_${biTab}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    onNotify(t('home.bi_exported'), 'success');
  };

  const { t, formatCurrency, formatDate } = useI18n();
  const periodLabelMap: Record<string, string> = {
    '30d': t('home.period.30d'),
    '3m': t('home.period.3m'),
    '6m': t('home.period.6m'),
    '12m': t('home.period.12m'),
    all: t('home.period.all'),
  };
  const periodKeysByLabel: Record<string, string> = {
    [t('home.period.30d')]: '30d',
    [t('home.period.3m')]: '3m',
    [t('home.period.6m')]: '6m',
    [t('home.period.12m')]: '12m',
    [t('home.period.all')]: 'all',
  };
  const palette = getBiPaletteColors(dashboard?.bi_preferences);
  const currentPeriodLabel = periodLabelMap[selectedPeriod || dashboard?.period || '12m'] || t('home.period.12m');
  const alertThreshold = dashboard?.bi_preferences?.cost_variation_alert_pct ?? 10;
  const targetMargin = dashboard?.bi_preferences?.target_margin_pct ?? 30;
  const avgMargin = dashboard?.avg_margin_pct ?? null;

  return (
    <div className="h-full overflow-y-auto pr-1 space-y-4">
      {/* 1. 3 Cards de KPI clicáveis (Produtos, Receitas, Insumos) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        {[
          { label: t('home.kpi.products'), suffix: t('home.kpi.products_suffix'), value: dashboard?.kpis.products ?? 0, target: 'Produtos' as NavKey },
          { label: t('home.kpi.recipes'), suffix: t('home.kpi.recipes_suffix'), value: dashboard?.kpis.recipes ?? 0, target: 'Receitas' as NavKey },
          { label: t('home.kpi.materials'), suffix: t('home.kpi.materials_suffix'), value: dashboard?.kpis.materials ?? 0, target: 'Cadastro' as NavKey },
        ].map((card) => (
          <button
            key={card.label}
            type="button"
            onClick={() => onNavigate(card.target)}
            className="group text-left rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] hover:border-[#F28C28] dark:hover:border-[#F28C28] px-5 py-4 shadow-sm transition-all flex items-center justify-between cursor-pointer"
          >
            <div>
              <div className="text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF]">{card.label}</div>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-[26px] font-extrabold text-[#18223A] dark:text-[#F4F7FF] leading-none">
                  {loading && !dashboard ? '...' : card.value}
                </span>
                <span className="text-[12px] text-[#60769D] dark:text-[#93A4C6]">{card.suffix}</span>
              </div>
            </div>
            <span className="text-[24px] text-[#7790BE] group-hover:text-[#F28C28] group-hover:translate-x-0.5 transition-all select-none">
              ›
            </span>
          </button>
        ))}
      </div>

      {/* 2. Gráfico Custo dos Produtos + Custo médio dos produtos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5">
        <div className="lg:col-span-2 rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
            <h3 className="text-[15px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              {t('home.cost_products')}
            </h3>
            <RoundedDropdown
              value={currentPeriodLabel}
              onChange={(lbl) => {
                const key = periodKeysByLabel[lbl];
                if (key) {
                  setSelectedPeriod(key);
                  fetchDashboard(key);
                }
              }}
              options={Object.keys(periodKeysByLabel)}
              width={165}
              height={30}
            />
          </div>
          <CostEvolutionChart
            series={dashboard?.cost_evolution_series || []}
            chartStyle={dashboard?.bi_preferences?.chart_style || 'auto'}
            primaryColor={palette[0]}
            secondaryColor={palette[1]}
          />
        </div>

        <div className="rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm flex items-center">
          <div className="w-full rounded-[18px] bg-[#F8FAFD] dark:bg-[#142544] border border-[#E2EAF5] dark:border-[#24385E] p-5 space-y-2.5">
            <div className="text-[12px] font-bold text-[#60769D] dark:text-[#93A4C6]">
              {t('home.avg_product_cost')}
            </div>
            <div className="text-[28px] font-extrabold text-[#18223A] dark:text-[#F4F7FF] leading-tight">
              {formatCurrency(dashboard?.avg_product_cost ?? 0)}
            </div>
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="inline-block px-3 py-1 rounded-full text-[11px] font-bold bg-[#E6F9F5] dark:bg-[#123B39] text-[#0F9D7A] dark:text-[#56D4B4]">
                {t('home.calculated_now')}
              </span>
              {avgMargin !== null && (
                <span
                  className={`inline-block px-3 py-1 rounded-full text-[11px] font-bold ${
                    avgMargin >= targetMargin
                      ? 'bg-[#EBFBF0] dark:bg-[#133020] text-[#16A34A] dark:text-[#4ADE80]'
                      : 'bg-[#FEF3C7] dark:bg-[#3B2A0F] text-[#D97706] dark:text-[#FBBF24]'
                  }`}
                >
                  {t('home.avg_margin', { avg: avgMargin.toFixed(1).replace('.', ','), target: targetMargin })}
                </span>
              )}
            </div>
            <div className="text-[11px] text-[#8C9BB5] dark:text-[#64748B]">
              {t('home.based_on_costs')}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Compras por Categoria + Variação de Preços */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        <div className="h-[245px] rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm flex flex-col gap-3">
          <div className="shrink-0">
            <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">{t('home.purchases')}</h3>
            <p className="text-[11px] text-[#60769D] dark:text-[#93A4C6]">{currentPeriodLabel.toLowerCase()}</p>
          </div>
          {!dashboard?.purchases_by_category?.length ? (
            <p className="text-[12px] text-[#8C9BB5] py-3">{t('home.no_purchases')}</p>
          ) : (
            <div className="flex-1 overflow-y-auto pr-1 space-y-2.5">
              {dashboard.purchases_by_category.map((cat, idx) => (
                <div key={cat.category} className="flex items-center justify-between text-[12.5px]">
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: palette[idx % palette.length] }}
                    />
                    <span className="text-[#18223A] dark:text-[#F4F7FF] truncate" title={cat.category}>{cat.category}</span>
                  </div>
                  <div className="flex items-center gap-4 shrink-0">
                    <span className="font-bold text-[#18223A] dark:text-[#F4F7FF]">{formatCurrency(cat.total)}</span>
                    <span className="text-[#60769D] dark:text-[#93A4C6] w-10 text-right">{cat.pct.toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="h-[245px] rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm flex flex-col gap-3">
          <div className="flex items-start justify-between gap-2 shrink-0">
            <div>
              <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">{t('home.price_variation')}</h3>
              <p className="text-[11px] text-[#60769D] dark:text-[#93A4C6]">
                {t('home.price_variation_sub', { pct: alertThreshold })}
              </p>
            </div>
            <button
              type="button"
              onClick={() => openBiModal('insumo')}
              className="inline-flex items-center gap-1.5 text-[12px] font-bold text-[#F28C28] hover:text-[#BA5200] transition-colors cursor-pointer shrink-0"
            >
              <span>{t('home.view_all')}</span>
              <OpenSectionIcon className="w-4 h-4" />
            </button>
          </div>
          {!dashboard?.price_variations?.length ? (
            <p className="text-[12px] text-[#8C9BB5] py-3">{t('home.no_history')}</p>
          ) : (
            <div className="flex-1 overflow-y-auto pr-1 space-y-2.5">
              {dashboard.price_variations.map((v) => (
                <div key={v.name} className="flex items-center justify-between gap-2 text-[12.5px]">
                  <span className="text-[#18223A] dark:text-[#F4F7FF] truncate" title={v.name}>{v.name}</span>
                  <div className="flex items-center gap-2 shrink-0">
                    {v.is_alert && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FEE2E2] dark:bg-[#3F1518] text-[#DC2626] dark:text-[#F87171]">
                        {t('home.alert')}
                      </span>
                    )}
                    <span
                      className={`font-bold ${
                        v.pct > 0.01
                          ? 'text-[#FF5E74]'
                          : 'text-[#24C6A3]'
                      }`}
                    >
                      {v.pct > 0.01 ? '↑' : '↓'} {Math.abs(v.pct).toFixed(1).replace('.', ',')}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 4. Inteligência de Precificação: Abaixo da Meta + Ranking Lucro & Custo */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        <div className="h-[245px] rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm flex flex-col gap-3">
          <div className="flex items-start justify-between gap-2 shrink-0">
            <div>
              <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                {t('home.below_target')}
              </h3>
              <p className="text-[11px] text-[#60769D] dark:text-[#93A4C6]">
                {t('home.below_target_sub', { pct: targetMargin })}
              </p>
            </div>
            <button
              type="button"
              onClick={() => onNavigate('Produtos')}
              className="inline-flex items-center gap-1.5 text-[12px] font-bold text-[#F28C28] hover:text-[#BA5200] transition-colors cursor-pointer shrink-0"
            >
              <span>{t('home.adjust')}</span>
              <OpenSectionIcon className="w-4 h-4" />
            </button>
          </div>
          {!dashboard?.below_target_margin?.length ? (
            <div className="flex-1 flex items-center text-[12px] text-[#16A34A] dark:text-[#4ADE80] font-medium">
              {t('home.all_above_target', { pct: targetMargin })}
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto pr-1 space-y-2.5">
              {dashboard.below_target_margin.map((prod) => (
                <div key={prod.id} className="flex items-center justify-between gap-2 text-[12.5px]">
                  <div className="min-w-0">
                    <div className="font-semibold text-[#18223A] dark:text-[#F4F7FF] truncate" title={prod.name}>
                      {prod.name}
                    </div>
                    <div className="text-[11px] text-[#60769D] dark:text-[#93A4C6]">
                      {t('home.cost_label')}: {prod.unit_cost_fmt} · {t('home.sale_label')}: {prod.sale_price_fmt}
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold shrink-0 ${
                      prod.margin_pct < 0
                        ? 'bg-[#FEE2E2] dark:bg-[#3F1518] text-[#DC2626] dark:text-[#F87171]'
                        : 'bg-[#FEF3C7] dark:bg-[#3B2A0F] text-[#D97706] dark:text-[#FBBF24]'
                    }`}
                  >
                    {prod.margin_pct.toFixed(1).replace('.', ',')}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="h-[245px] rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm flex flex-col gap-3">
          <div className="flex items-start justify-between gap-2 shrink-0">
            <div>
              <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                {t('home.ranking_title')}
              </h3>
              <p className="text-[11px] text-[#60769D] dark:text-[#93A4C6]">
                {t('home.ranking_sub')}
              </p>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto pr-1 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="text-[11px] font-bold uppercase tracking-wide text-[#0F9D7A] dark:text-[#56D4B4]">
                {t('home.highest_profit')}
              </div>
              {!dashboard?.profit_ranking?.length ? (
                <p className="text-[12px] text-[#8C9BB5]">{t('home.no_sale_prices')}</p>
              ) : (
                dashboard.profit_ranking.map((p, idx) => (
                  <div key={p.id} className="flex items-center justify-between gap-2 text-[12px]">
                    <span className="text-[#18223A] dark:text-[#F4F7FF] truncate" title={p.name}>
                      {idx + 1}. {p.name}
                    </span>
                    <span className="font-bold text-[#16A34A] dark:text-[#4ADE80] shrink-0">
                      {p.profit_fmt} ({p.margin_pct.toFixed(0)}%)
                    </span>
                  </div>
                ))
              )}
            </div>

            <div className="space-y-2">
              <div className="text-[11px] font-bold uppercase tracking-wide text-[#BA5200] dark:text-[#F28C28]">
                {t('home.highest_cost')}
              </div>
              {!dashboard?.highest_cost_products?.length ? (
                <p className="text-[12px] text-[#8C9BB5]">{t('home.no_products')}</p>
              ) : (
                dashboard.highest_cost_products.map((p, idx) => (
                  <div key={p.id} className="flex items-center justify-between gap-2 text-[12px]">
                    <span className="text-[#18223A] dark:text-[#F4F7FF] truncate" title={p.name}>
                      {idx + 1}. {p.name}
                    </span>
                    <span className="font-bold text-[#18223A] dark:text-[#F4F7FF] shrink-0">
                      {p.unit_cost_fmt}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 5. Pendências do Cadastro (quando houver) */}
      {!!dashboard?.pending_items?.length && (
        <div className="rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-4 shadow-sm flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B] shrink-0" />
            <span className="text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              {t('home.pending_title')}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {dashboard.pending_items.map((pend) => (
              <button
                key={pend.key}
                type="button"
                onClick={() => onNavigate(pend.target_tab)}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11.5px] font-semibold bg-[#FFFBEB] dark:bg-[#38280E] text-[#B45309] dark:text-[#FCD34D] border border-[#FDE68A] dark:border-[#78350F] hover:border-[#F28C28] transition-colors cursor-pointer"
              >
                <span>{pend.label}</span>
                <OpenSectionIcon className="w-3.5 h-3.5 shrink-0" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 6. Últimas Movimentações */}
      <div className="rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">{t('home.recent_moves')}</h3>
          <button
            type="button"
            onClick={() => onNavigate('Cadastro')}
            className="inline-flex items-center gap-1.5 text-[12px] font-bold text-[#F28C28] hover:text-[#BA5200] transition-colors cursor-pointer"
          >
            <span>{t('home.view_all')}</span>
            <OpenSectionIcon className="w-4 h-4" />
          </button>
        </div>

        <div className="rounded-full bg-[#F8FAFD] dark:bg-[#142544] px-4 py-1.5 grid grid-cols-12 text-[11.5px] font-bold text-[#60769D] dark:text-[#93A4C6]">
          <div className="col-span-3">{t('home.col.date')}</div>
          <div className="col-span-5">{t('home.col.description')}</div>
          <div className="col-span-2 text-center">{t('home.col.type')}</div>
          <div className="col-span-2 text-right">{t('home.col.value')}</div>
        </div>

        {!dashboard?.recent_purchases?.length ? (
          <p className="text-[12px] text-[#8C9BB5] py-2 px-2">{t('home.no_moves')}</p>
        ) : (
          <div className="divide-y divide-[#F0F4FA] dark:divide-[#1E3156]">
            {dashboard.recent_purchases.map((item) => (
              <div key={item.id} className="grid grid-cols-12 items-center px-4 py-2 text-[12.5px]">
                <div className="col-span-3 text-[#60769D] dark:text-[#93A4C6]">{formatDate(item.date)}</div>
                <div className="col-span-5 text-[#18223A] dark:text-[#F4F7FF] truncate pr-2" title={item.description}>
                  {item.description}
                </div>
                <div className="col-span-2 flex justify-center">
                  <span className="px-3 py-0.5 rounded-full text-[11px] font-bold bg-[#E6F9F5] dark:bg-[#123B39] text-[#0F9D7A] dark:text-[#5EE0B8]">
                    {item.type}
                  </span>
                </div>
                <div className="col-span-2 text-right font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  {formatCurrency(item.value)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 5. Dois Gráficos de Rosca de BI + Botão Ver Detalhes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5 pb-2">
        <div className="rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm">
          <div className="flex items-center justify-between gap-2 mb-2">
            <div>
              <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                {t('home.donut.purchases_title')}
              </h3>
              <p className="text-[11px] text-[#60769D] dark:text-[#93A4C6]">{t('home.donut.purchases_sub')}</p>
            </div>
            <RoundedActionButton
              label={t('home.view_details')}
              onClick={() => openBiModal('insumo')}
              variant="primary"
              height={32}
            />
          </div>
          <BiDonutChart
            slices={dashboard?.purchase_pie_slices || []}
            palette={palette}
            emptyMessage={t('home.donut.purchases_empty')}
          />
        </div>

        <div className="rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm">
          <div className="flex items-center justify-between gap-2 mb-2">
            <div>
              <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                {t('home.donut.costs_title')}
              </h3>
              <p className="text-[11px] text-[#60769D] dark:text-[#93A4C6]">{t('home.donut.costs_sub')}</p>
            </div>
            <RoundedActionButton
              label={t('home.view_details')}
              onClick={() => openBiModal('custos')}
              variant="primary"
              height={32}
            />
          </div>
          <BiDonutChart
            slices={dashboard?.cost_pie_slices || []}
            palette={palette}
            emptyMessage={t('home.donut.costs_empty')}
          />
        </div>
      </div>

      {/* 6. Modal de BI Detalhado (3 Abas + Filtro de Mês + Padrão Único de Tabelas) */}
      {biModalOpen && (
        <div className="fixed inset-0 z-50 bg-[#0B132B]/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="w-full max-w-5xl h-[82vh] rounded-[26px] bg-[#F4F7FC] dark:bg-[#0B132B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col gap-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-[16px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  {t('home.bi_modal_title')}
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setBiModalOpen(false)}
                className="w-8 h-8 rounded-full bg-white dark:bg-[#142544] border border-[#DCE4F0] dark:border-[#24385E] text-[#60769D] hover:text-[#BA5200] flex items-center justify-center cursor-pointer"
                title={t('common.close')}
              >
                ✕
              </button>
            </div>

            {/* Abas em Cápsula + Filtro de Mês + Pesquisa 32px */}
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                {(
                  [
                    { key: 'insumo', label: t('home.bi_tab.insumo') },
                    { key: 'marca', label: t('home.bi_tab.marca') },
                    { key: 'custos', label: t('home.bi_tab.custos') },
                  ] as { key: BiTabKey; label: string }[]
                ).map((t) => {
                  const active = biTab === t.key;
                  return (
                    <button
                      key={t.key}
                      type="button"
                      onClick={() => {
                        setBiTab(t.key);
                        setBiSortCol('mes');
                        setBiSortDir('DESC');
                      }}
                      className={`h-[32px] px-4 rounded-full text-[12.5px] font-bold transition-colors cursor-pointer ${
                        active
                          ? 'bg-[#F28C28] text-white shadow-xs'
                          : 'bg-white dark:bg-[#142544] text-[#1D3557] dark:text-[#DDE6FF] border border-[#DCE4F0] dark:border-[#24385E] hover:border-[#F28C28]'
                      }`}
                    >
                      {t.label}
                    </button>
                  );
                })}
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <RoundedDropdown
                  value={biMonthFilter}
                  onChange={setBiMonthFilter}
                  options={['Todos os meses', ...(biDetails?.months || [])]}
                  width={155}
                  height={32}
                />
                <RoundedEntry
                  value={biSearch}
                  onChange={setBiSearch}
                  placeholder="Filtrar..."
                  width={210}
                  height={32}
                />
              </div>
            </div>

            {/* Tabela no Padrão Único do Nexo */}
            <div className="flex-1 min-h-0 rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-3 flex flex-col overflow-hidden">
              {biLoading ? (
                <div className="flex-1 flex items-center justify-center text-[13px] text-[#60769D] dark:text-[#93A4C6]">
                  Carregando dados de BI...
                </div>
              ) : (
                <div className="flex-1 overflow-auto">
                  <div className="min-w-full w-max">
                    {/* Cabeçalho Cápsula 36px */}
                    <div className="h-[36px] rounded-full bg-[#EEF4FB] dark:bg-[#142544] flex items-center sticky top-0 z-20">
                      {activeCols.map((col, idx) => {
                        const isSorted = biSortCol === col.key;
                        const arrow = isSorted ? (biSortDir === 'ASC' ? ' ↑' : ' ↓') : '';
                        const colW = biColWidths[col.key] || col.width;
                        return (
                          <div
                            key={col.key}
                            style={{ width: colW, flexShrink: 0 }}
                            className={`relative h-full flex items-center px-3.5 ${
                              idx < activeCols.length - 1
                                ? 'border-r border-[#E5ECF5] dark:border-[#24385E]'
                                : ''
                            }`}
                          >
                            <button
                              type="button"
                              onClick={() => handleBiSort(col.key)}
                              className={`w-full h-full flex items-center text-[12px] font-bold text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] whitespace-nowrap cursor-pointer ${
                                col.align === 'center' ? 'justify-center' : 'justify-start'
                              }`}
                            >
                              {col.label}
                              {arrow}
                            </button>
                            {idx < activeCols.length - 1 && (
                              <ColumnResizeHandle
                                onMouseDown={(e) => startBiResize(col.key, col.label, col.width, e)}
                                onDoubleClick={(e) =>
                                  autoFitBiColumn(
                                    col.key,
                                    col.label,
                                    filteredBiRows.map((r) =>
                                      col.key === 'variacao_pct' ? `${r[col.key]}%` : String(r[col.key] ?? '')
                                    ),
                                    0,
                                    e
                                  )
                                }
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* Linhas */}
                    {filteredBiRows.length === 0 ? (
                      <div className="py-12 text-center text-[13px] text-[#60769D] dark:text-[#93A4C6]">
                        Nenhum registro encontrado para o filtro selecionado.
                      </div>
                    ) : (
                      <div className="divide-y divide-[#F0F4FA] dark:divide-[#1E3156] mt-1">
                        {filteredBiRows.map((row) => (
                          <div
                            key={row.id}
                            className="h-[38px] flex items-center hover:bg-[#F8FAFD] dark:hover:bg-[#162849] transition-colors"
                          >
                            {activeCols.map((col) => {
                              const colW = biColWidths[col.key] || col.width;
                              const rawVal = row[col.key];
                              const displayText =
                                col.key === 'variacao_pct'
                                  ? `${Number(rawVal || 0).toFixed(1).replace('.', ',')}%`
                                  : String(rawVal ?? '');
                              const isAlertVar =
                                col.key === 'variacao_pct' && Math.abs(Number(rawVal || 0)) >= alertThreshold;
                              return (
                                <div
                                  key={col.key}
                                  style={{ width: colW, flexShrink: 0 }}
                                  title={displayText || undefined}
                                  className={`px-3.5 text-[12.5px] truncate ${
                                    col.align === 'center' ? 'text-center' : 'text-left'
                                  } ${
                                    isAlertVar
                                      ? 'font-bold text-[#DC2626] dark:text-[#F87171]'
                                      : 'text-[#18223A] dark:text-[#F4F7FF]'
                                  }`}
                                >
                                  {displayText}
                                </div>
                              );
                            })}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Rodapé */}
            <div className="flex items-center justify-between pt-1">
              <RoundedActionButton
                label="Exportar CSV"
                onClick={handleExportBiCsv}
                variant="secondary"
                height={34}
              />
              <RoundedActionButton
                label="Fechar"
                onClick={() => setBiModalOpen(false)}
                variant="primary"
                height={34}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
