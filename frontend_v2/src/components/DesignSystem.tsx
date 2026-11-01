import React, { useEffect, useRef, useState } from 'react';
import { NavKey } from '../types';

// ---------- Vector Icons ----------

export const NexoCheckbox: React.FC<{
  checked: boolean;
  onChange: (e: React.MouseEvent) => void;
  title?: string;
}> = ({ checked, onChange, title }) => {
  return (
    <button
      type="button"
      title={title}
      onClick={(e) => {
        e.stopPropagation();
        onChange(e);
      }}
      className="inline-flex items-center justify-center w-6 h-6 rounded-md focus:outline-none cursor-pointer group"
    >
      <svg width="16" height="16" viewBox="0 0 128 128" className="transition-transform group-active:scale-95">
        <rect
          x="16"
          y="16"
          width="96"
          height="96"
          rx="24"
          fill="#FFFFFF"
          stroke={checked ? '#F28C28' : '#C0C9D8'}
          strokeWidth="12"
        />
        {checked && (
          <path
            d="M36 64 L56 84 L96 44"
            fill="none"
            stroke="#F28C28"
            strokeWidth="14"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}
      </svg>
    </button>
  );
};

/**
 * Engrenagem matemática de 6 dentes com centro vazado
 */
export const GearPolygonIcon: React.FC<{
  className?: string;
  size?: number;
  strokeColor?: string;
  centerFill?: string;
}> = ({ className = '', size = 16, strokeColor = 'currentColor', centerFill = 'transparent' }) => {
  const cx = 21;
  const cy = 21;
  const pts: string[] = [];
  // 6 dentes mecânicos equilibrados (removidos 2 dentes do modelo de 8)
  for (let t = 0; t < 6; t++) {
    const baseAng = t * 60 - 90;
    const anglesAndRadii: [number, number][] = [
      [-16, 10.5],
      [-9, 15.0],
      [9, 15.0],
      [16, 10.5],
    ];
    for (const [dAng, r] of anglesAndRadii) {
      const rad = ((baseAng + dAng) * Math.PI) / 180;
      const x = cx + r * Math.cos(rad);
      const y = cy + r * Math.sin(rad);
      pts.push(`${x.toFixed(2)},${y.toFixed(2)}`);
    }
  }
  return (
    <svg width={size} height={size} viewBox="0 0 42 42" className={className}>
      <polygon
        points={pts.join(' ')}
        fill={strokeColor}
        stroke={strokeColor}
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <circle cx={cx} cy={cy} r="5.5" fill={centerFill} stroke={strokeColor} strokeWidth="1.8" />
    </svg>
  );
};

export const PlusIcon: React.FC<{
  color?: string;
  size?: number;
  strokeWidth?: number;
}> = ({ color = 'currentColor', size = 16, strokeWidth = 2.4 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M12 5V19"
      stroke={color}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M5 12H19"
      stroke={color}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const ClockIcon: React.FC<{ color?: string; size?: number }> = ({
  color = 'currentColor',
  size = 15,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {/* Modern Timeline/History Arc */}
    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
    <path d="M3 3v5h5" />
    {/* Inner Clock Hands */}
    <path d="M12 7v5l3 2" />
  </svg>
);

export const RulerConversionIcon: React.FC<{ color?: string; size?: number }> = ({
  color = 'currentColor',
  size = 15,
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {/* Modern Dynamic Unit Conversion Orbit (Curved Swap) */}
    <path d="m16 3 4 4-4 4" />
    <path d="M20 7H9a4 4 0 0 0-4 4v1" />
    <path d="m8 21-4-4 4-4" />
    <path d="M4 17h11a4 4 0 0 0 4-4v-1" />
  </svg>
);

export const DuplicateIcon: React.FC<{ color?: string; size?: number; className?: string }> = ({
  color = 'currentColor',
  size = 15,
  className = '',
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </svg>
);

export const TrashIcon: React.FC<{ color?: string; size?: number; className?: string }> = ({
  color = 'currentColor',
  size = 15,
  className = '',
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2.2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M3 6h18" />
    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
    <line x1="10" y1="11" x2="10" y2="17" />
    <line x1="14" y1="11" x2="14" y2="17" />
  </svg>
);

export const ChevronRightIcon: React.FC<{ color?: string; size?: number; className?: string }> = ({
  color = 'currentColor',
  size = 14,
  className = '',
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2.4"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="m9 18 6-6-6-6" />
  </svg>
);

export const ChevronDownIcon: React.FC<{ color?: string; size?: number; className?: string }> = ({
  color = 'currentColor',
  size = 14,
  className = '',
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2.4"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="m6 9 6 6 6-6" />
  </svg>
);

// ---------- RoundedActionButton ----------

interface RoundedActionButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'soft' | 'danger' | 'secondary' | 'ghost' | 'green';
  icon?: React.ReactNode;
  height?: number;
  width?: number | string;
  disabled?: boolean;
  className?: string;
}

export const RoundedActionButton: React.FC<RoundedActionButtonProps> = ({
  label,
  onClick,
  variant = 'primary',
  icon,
  height = 38,
  width,
  disabled = false,
  className = '',
}) => {
  const [hovered, setHovered] = useState(false);

  const stylesByVariant: Record<
    string,
    {
      baseFill: string;
      hoverFill: string;
      text: string;
      border: string;
      darkBaseFill?: string;
      darkHoverFill?: string;
      darkText?: string;
      darkBorder?: string;
    }
  > = {
    primary: {
      baseFill: '#F28C28',
      hoverFill: '#BA5200',
      text: '#FFFFFF',
      border: '#DE7819',
      darkBaseFill: '#F28C28',
      darkHoverFill: '#BA5200',
      darkText: '#FFFFFF',
      darkBorder: '#F6A24B',
    },
    soft: {
      baseFill: '#EFF4FB',
      hoverFill: '#E1EBF7',
      text: '#1D3557',
      border: '#CAD8EC',
      darkBaseFill: '#172746',
      darkHoverFill: '#20375F',
      darkText: '#DDE6FF',
      darkBorder: '#273C66',
    },
    danger: {
      baseFill: '#FEE2E2',
      hoverFill: '#FECACA',
      text: '#DC2626',
      border: '#FCA5A5',
      darkBaseFill: '#2D141A',
      darkHoverFill: '#3D1B24',
      darkText: '#F87171',
      darkBorder: '#5C222D',
    },
    secondary: {
      baseFill: '#6B7280',
      hoverFill: '#4B5563',
      text: '#FFFFFF',
      border: '#4B5563',
    },
    green: {
      baseFill: '#EAFaf1',
      hoverFill: '#D4E6DC',
      text: '#1E833F',
      border: '#A7D8B9',
      darkBaseFill: '#12372E',
      darkHoverFill: '#184A3E',
      darkText: '#61E3B9',
      darkBorder: '#1E5244',
    },
    ghost: {
      baseFill: '#FFFFFF',
      hoverFill: '#F3F6FA',
      text: '#687796',
      border: '#DDE5F2',
      darkBaseFill: '#142544',
      darkHoverFill: '#1D335C',
      darkText: '#93A4C6',
      darkBorder: '#24385E',
    },
  };

  const st = stylesByVariant[variant] || stylesByVariant.primary;
  const isDark = document.documentElement.classList.contains('dark');
  const bg = hovered
    ? isDark && st.darkHoverFill
      ? st.darkHoverFill
      : st.hoverFill
    : isDark && st.darkBaseFill
    ? st.darkBaseFill
    : st.baseFill;
  const fg = isDark && st.darkText ? st.darkText : st.text;
  const border = isDark && st.darkBorder ? st.darkBorder : st.border;

  return (
    <button
      type="button"
      disabled={disabled}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => {
        setHovered(false);
        onClick();
      }}
      style={{
        height: `${height}px`,
        width: typeof width === 'number' ? `${width}px` : width,
        backgroundColor: bg,
        color: fg,
        borderColor: border,
      }}
      className={`rounded-full font-bold text-[13px] px-3.5 border shadow-sm inline-flex items-center justify-center gap-1.5 transition-all duration-150 shrink-0 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {icon && <span className="inline-flex items-center shrink-0">{icon}</span>}
      <span className="truncate">{label}</span>
    </button>
  );
};

// ---------- RoundedEntry (Search Box VIP 32px) ----------

interface RoundedEntryProps {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  width?: number | string;
  height?: number;
  icon?: boolean;
  autoCapitalizeFirst?: boolean;
  spellCheck?: boolean;
}

export const RoundedEntry: React.FC<RoundedEntryProps> = ({
  value,
  onChange,
  placeholder = 'Pesquisar',
  width = 280,
  height = 32,
  icon = true,
  autoCapitalizeFirst = false,
  spellCheck = true,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value;
    if (autoCapitalizeFirst && val.length > 0) {
      val = val.replace(/[a-zA-ZÀ-ÿ]/, (m) => m.toUpperCase());
    }
    onChange(val);
  };

  return (
    <div
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: `${height}px`,
      }}
      className="relative inline-flex items-center rounded-full bg-white dark:bg-[#0E1B35] border border-[#B0C0D6] dark:border-[#24385E] transition-colors focus-within:border-[#F28C28] dark:focus-within:border-[#F28C28] shrink-0"
    >
      {icon && (
        <svg
          width="15"
          height="15"
          viewBox="0 0 20 20"
          fill="none"
          className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-[#9AA9BF]"
        >
          <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" strokeWidth="2" />
          <line
            x1="12.5"
            y1="12.5"
            x2="17"
            y2="17"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      )}
      <input
        type="text"
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        spellCheck={spellCheck}
        lang="pt-BR"
        style={{
          paddingLeft: icon ? '38px' : '16px',
          paddingRight: value ? '28px' : '14px',
        }}
        className="w-full h-full bg-transparent rounded-full text-[13px] text-[#18223A] dark:text-[#F4F7FF] placeholder-[#9AA9BF] focus:outline-none"
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange('')}
          title="Limpar busca"
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#9AA9BF] hover:text-[#18223A] dark:hover:text-white text-xs font-bold"
        >
          ✕
        </button>
      )}
    </div>
  );
};

// ---------- RoundedDropdown ----------

interface RoundedDropdownProps {
  value: string;
  onChange: (val: string) => void;
  options: string[];
  width?: number | string;
  height?: number;
  align?: 'left' | 'center';
  placeholder?: string;
}

export const RoundedDropdown: React.FC<RoundedDropdownProps> = ({
  value,
  onChange,
  options,
  width = 120,
  height = 32,
  align = 'center',
  placeholder = 'Selecione...',
}) => {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleOutside);
    }
    return () => document.removeEventListener('mousedown', handleOutside);
  }, [open]);

  return (
    <div
      ref={wrapRef}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: `${height}px`,
      }}
      className="relative inline-block shrink-0"
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`w-full h-full rounded-full bg-white dark:bg-[#0E1B35] hover:bg-[#F8FAFC] dark:hover:bg-[#142544] border border-[#B0C0D6] dark:border-[#24385E] px-4 flex items-center transition-colors cursor-pointer focus:outline-none focus:border-[#F28C28] ${
          align === 'center' ? 'justify-center font-bold' : 'justify-between font-normal'
        }`}
      >
        <span
          className={`text-[13px] truncate ${
            value
              ? 'text-[#18223A] dark:text-[#F4F7FF]'
              : 'text-[#9AA9BF] font-normal'
          } ${align === 'center' ? 'mr-3' : 'pr-2'}`}
        >
          {value || placeholder}
        </span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          className={`text-[#687796] shrink-0 transition-transform duration-150 ${
            align === 'center' ? 'absolute right-3.5' : ''
          } ${open ? 'rotate-180' : ''}`}
        >
          <path
            d="M2 4L6 8L10 4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {open && (
        <div className="absolute left-0 right-0 mt-1.5 rounded-[12px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-lg z-50 max-h-60 overflow-y-auto py-1">
          {options.length === 0 ? (
            <div className="px-4 py-2 text-xs text-[#9AA9BF] text-center">Sem opções</div>
          ) : (
            options.map((opt) => {
              const isSelected = opt === value;
              return (
                <button
                  key={opt}
                  type="button"
                  onClick={() => {
                    onChange(opt);
                    setOpen(false);
                  }}
                  className={`w-full h-9 px-3.5 text-[13px] flex items-center transition-colors cursor-pointer hover:bg-[#F8FAFC] dark:hover:bg-[#172746] ${
                    align === 'center' ? 'justify-center' : 'justify-start text-left'
                  } ${
                    isSelected
                      ? 'text-[#BA5200] dark:text-[#F28C28] font-bold'
                      : 'text-[#18223A] dark:text-[#F4F7FF] font-normal'
                  }`}
                >
                  <span className="truncate">{opt}</span>
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};

// ---------- CapsuleInput (Form fields) ----------

interface CapsuleInputProps {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  type?: 'text' | 'numeric' | 'money' | 'date';
  autoCapitalizeFirst?: boolean;
  spellCheck?: boolean;
  className?: string;
}

export function formatMoneyBR(rawDigits: string): string {
  const digits = rawDigits.replace(/\D/g, '');
  if (!digits) return 'R$ 0,00';
  const cents = parseInt(digits, 10);
  const reais = (cents / 100).toFixed(2);
  const [intPart, decPart] = reais.split('.');
  const formattedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `R$ ${formattedInt},${decPart}`;
}

export const CapsuleInput: React.FC<CapsuleInputProps> = ({
  value,
  onChange,
  placeholder = '',
  type = 'text',
  autoCapitalizeFirst = true,
  spellCheck = true,
  className = '',
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let v = e.target.value;
    if (type === 'money') {
      onChange(formatMoneyBR(v));
      return;
    }
    if (type === 'numeric') {
      v = v.replace(/[^0-9.,]/g, '');
      onChange(v);
      return;
    }
    if (autoCapitalizeFirst && v.length > 0) {
      v = v.replace(/[a-zA-ZÀ-ÿ]/, (m) => m.toUpperCase());
    }
    onChange(v);
  };

  return (
    <input
      type={type === 'date' ? 'date' : 'text'}
      value={value}
      onChange={handleChange}
      placeholder={placeholder}
      spellCheck={type === 'text' ? spellCheck : false}
      lang="pt-BR"
      className={`h-[32px] w-full rounded-full bg-white dark:bg-[#0E1B35] border border-[#B0C0D6] dark:border-[#24385E] px-3.5 text-[12.5px] text-[#18223A] dark:text-[#F4F7FF] placeholder-[#9AA9BF] focus:outline-none focus:border-[#F28C28] dark:focus:border-[#F28C28] transition-colors ${className}`}
    />
  );
};

// ---------- CapsuleQuantityUnit (Fused [ Quantidade | Unidade ▼ ]) ----------

export interface CapsuleQuantityUnitProps {
  qtyValue: string;
  onQtyChange: (val: string) => void;
  unitValue: string;
  onUnitChange: (val: string) => void;
  unitOptions: string[];
  width?: number | string;
  height?: number;
  qtyPlaceholder?: string;
  disabled?: boolean;
}

export const CapsuleQuantityUnit: React.FC<CapsuleQuantityUnitProps> = ({
  qtyValue,
  onQtyChange,
  unitValue,
  onUnitChange,
  unitOptions,
  width = 180,
  height = 34,
  qtyPlaceholder = 'Qtd',
  disabled = false,
}) => {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleOutside);
    }
    return () => document.removeEventListener('mousedown', handleOutside);
  }, [open]);

  return (
    <div
      ref={wrapRef}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: `${height}px`,
      }}
      className={`relative inline-flex items-center rounded-full bg-white dark:bg-[#0E1B35] border border-[#B0C0D6] dark:border-[#24385E] transition-colors ${
        disabled
          ? 'opacity-60 cursor-not-allowed'
          : 'focus-within:border-[#F28C28] dark:focus-within:border-[#F28C28]'
      }`}
    >
      {/* Numeric Input */}
      <input
        type="text"
        disabled={disabled}
        value={qtyValue}
        onChange={(e) => onQtyChange(e.target.value.replace(/[^0-9.,]/g, ''))}
        placeholder={qtyPlaceholder}
        className="flex-1 min-w-0 h-full bg-transparent px-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] placeholder-[#9AA9BF] focus:outline-none text-center font-medium"
      />

      {/* Gray Divider Line */}
      <div className="w-[1px] h-[18px] bg-[#B0C0D6] dark:bg-[#2A3F66] shrink-0" />

      {/* Unit Selector Trigger */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        className="h-full px-3 flex items-center justify-center gap-1.5 text-[12.5px] font-bold text-[#18223A] dark:text-[#F4F7FF] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer select-none shrink-0"
      >
        <span>{unitValue || 'Unidade'}</span>
        <svg
          width="10"
          height="10"
          viewBox="0 0 12 12"
          fill="none"
          className={`text-[#687796] transition-transform duration-150 ${
            open ? 'rotate-180' : ''
          }`}
        >
          <path
            d="M2 4L6 8L10 4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {/* Floating Unit Dropdown */}
      {open && (
        <div className="absolute right-0 top-[40px] min-w-[95px] max-h-[190px] overflow-y-auto rounded-[12px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-xl py-1 z-50">
          {unitOptions.map((u) => (
            <button
              key={u}
              type="button"
              onClick={() => {
                onUnitChange(u);
                setOpen(false);
              }}
              className={`w-full h-8 px-3 text-[12.5px] flex items-center justify-center transition-colors cursor-pointer hover:bg-[#F8FAFC] dark:hover:bg-[#172746] ${
                u === unitValue
                  ? 'text-[#BA5200] dark:text-[#F28C28] font-bold bg-[#FFF7EE] dark:bg-[#2C1C0D]'
                  : 'text-[#18223A] dark:text-[#F4F7FF] font-normal'
              }`}
            >
              {u}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// ---------- ReferenceSidebar (Nexo Capsule Sidebar) ----------

interface ReferenceSidebarProps {
  active: NavKey;
  onSelect: (key: NavKey) => void;
  dark: boolean;
}

const NAV_ITEMS: { key: NavKey; label: string; icon: string }[] = [
  { key: 'Geral', label: 'Início', icon: '/ui_assets/home.png' },
  { key: 'Cadastro', label: 'Cadastro', icon: '/ui_assets/cadastro.png' },
  { key: 'Receitas', label: 'Receitas', icon: '/ui_assets/receitas.png' },
  { key: 'Produtos', label: 'Produtos', icon: '/ui_assets/produtos.png' },
  { key: 'Configurações', label: 'Configurações', icon: '/ui_assets/settings.png' },
];

export const ReferenceSidebar: React.FC<ReferenceSidebarProps> = ({
  active,
  onSelect,
  dark,
}) => {
  const [hovered, setHovered] = useState<NavKey | null>(null);

  return (
    <aside className="w-[150px] h-full shrink-0 flex flex-col items-center relative select-none">
      {/* Top Nexo Logo (x=10, y=26, w=135, h=105) */}
      <div className="mt-[22px] w-[135px] h-[105px] flex items-center justify-center">
        <img
          src={dark ? '/ui_assets/nexo_logo_dark_clean.png' : '/ui_assets/nexo_logo_light_clean.png'}
          alt="Nexo"
          className="max-w-[130px] max-h-[100px] object-contain pointer-events-none transition-opacity duration-150"
        />
      </div>

      {/* Vertical Capsule Rail (width=68px, height=500px, centered vertically in remaining space) */}
      <div className="flex-1 w-full flex items-center justify-center pb-6">
        <div
          style={{
            width: '68px',
            height: '500px',
            backgroundColor: dark ? '#F28C28' : '#111C30',
            borderColor: dark ? '#F6A24B' : '#A9BFE0',
            boxShadow: dark
              ? '0 8px 20px rgba(0, 0, 0, 0.45)'
              : '0 8px 18px rgba(17, 28, 48, 0.16)',
          }}
          className="rounded-full border flex flex-col items-center justify-between py-[26px] relative transition-colors duration-200"
        >
          {NAV_ITEMS.map((item) => {
            const isActive = active === item.key;
            const isHovered = hovered === item.key;
            return (
              <div key={item.key} className="relative flex items-center justify-center w-full">
                <button
                  type="button"
                  onClick={() => onSelect(item.key)}
                  onMouseEnter={() => setHovered(item.key)}
                  onMouseLeave={() => setHovered(null)}
                  style={{
                    width: '44px',
                    height: '60px',
                    borderRadius: '20px',
                    backgroundColor: isActive
                      ? dark
                        ? '#111C30' // Regra doc 06 e CONTEXTO_V2: azul-marinho #111C30 sobre o laranja no modo escuro
                        : '#693A16' // Marrom escuro #693A16 no modo claro
                      : isHovered
                      ? dark
                        ? 'rgba(17, 28, 48, 0.18)'
                        : 'rgba(255, 255, 255, 0.08)'
                      : 'transparent',
                  }}
                  className="flex items-center justify-center transition-all duration-150 cursor-pointer focus:outline-none"
                >
                  <img
                    src={item.icon}
                    alt={item.label}
                    className="w-[34px] h-[34px] object-contain pointer-events-none"
                  />
                </button>

                {/* Capsule Tooltip on Hover */}
                {isHovered && (
                  <div
                    style={{
                      backgroundColor: dark ? '#2A3B5C' : '#101A33',
                    }}
                    className="absolute left-[74px] top-1/2 -translate-y-1/2 h-[32px] px-4 rounded-full text-white font-bold text-[12px] flex items-center justify-center whitespace-nowrap shadow-lg z-50 pointer-events-none animate-fade-in"
                  >
                    {item.label}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
};

// ---------- Animated Feedback Modal (HUD central: Sucesso, Aviso e Erro) ----------

export type FeedbackType = 'success' | 'warning' | 'error';

export interface AnimatedFeedbackModalProps {
  message: string;
  type?: FeedbackType;
  onClose: () => void;
}

export const AnimatedFeedbackModal: React.FC<AnimatedFeedbackModalProps> = ({
  message,
  type = 'success',
  onClose,
}) => {
  const [closing, setClosing] = useState(false);

  useEffect(() => {
    const isWarning = type === 'warning';
    const fadeTimer = setTimeout(() => {
      setClosing(true);
    }, isWarning ? 2300 : 1900);

    const closeTimer = setTimeout(() => {
      onClose();
    }, isWarning ? 2600 : 2200);

    return () => {
      clearTimeout(fadeTimer);
      clearTimeout(closeTimer);
    };
  }, [onClose, type]);

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center pointer-events-none transition-opacity duration-300 ${
        closing ? 'opacity-0' : 'opacity-100'
      }`}
    >
      <div
        className={`w-[290px] p-6 rounded-[24px] bg-white/95 dark:bg-[#111F3B]/95 backdrop-blur-md border border-[#DDE5F2] dark:border-[#24385E] shadow-2xl flex flex-col items-center justify-center select-none transition-all duration-300 pointer-events-auto ${
          closing
            ? 'scale-95'
            : type === 'error'
            ? 'animate-shake-error'
            : 'animate-pop-in'
        }`}
      >
        {/* Type 1: SUCCESS (Green circle drawing + checkmark with 4.6px thickness) */}
        {type === 'success' && (
          <div className="w-[64px] h-[64px] rounded-full flex items-center justify-center bg-[#EAFaf1] dark:bg-[#12372E] mb-3 relative">
            <svg width="56" height="56" viewBox="0 0 56 56" className="transform -rotate-90">
              <circle
                cx="28"
                cy="28"
                r="24"
                fill="none"
                stroke="#22C55E"
                strokeWidth="4.6"
                strokeLinecap="round"
                className="animate-draw-circle"
              />
            </svg>
            <svg
              width="32"
              height="32"
              viewBox="0 0 32 32"
              fill="none"
              className="absolute"
            >
              <path
                d="M7 17.5L13 23.5L25 10"
                fill="none"
                stroke="#22C55E"
                strokeWidth="4.6"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="animate-draw-check"
              />
            </svg>
          </div>
        )}

        {/* Type 2: WARNING (Pulsing Amber Triangle perfectly centered with 4.6px thickness) */}
        {type === 'warning' && (
          <div className="w-[64px] h-[64px] rounded-full flex items-center justify-center bg-[#FEF3C7] dark:bg-[#3D2C0D] mb-3 relative animate-pulse-warning">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              {/* Rounded Triangle centered at (32, 32) */}
              <path
                d="M 29.5 14.5 L 17 41.5 C 15.5 44.5, 17 45.5, 20 45.5 L 44 45.5 C 47 45.5, 48.5 44.5, 47 41.5 L 34.5 14.5 C 33 11.5, 31 11.5, 29.5 14.5 Z"
                fill="none"
                stroke="#F59E0B"
                strokeWidth="4.6"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="animate-draw-triangle"
              />
              {/* Bold Exclamation Bar */}
              <line
                x1="32"
                y1="20"
                x2="32"
                y2="30"
                stroke="#F59E0B"
                strokeWidth="4.6"
                strokeLinecap="round"
                className="animate-draw-exclamation"
              />
              {/* Bold Exclamation Dot */}
              <circle
                cx="32"
                cy="37"
                r="2.6"
                fill="#F59E0B"
                className="animate-draw-exclamation"
              />
            </svg>
          </div>
        )}

        {/* Type 3: ERROR (Red Circle + X with identical 4.6px thickness & Energetic Shake Animation) */}
        {type === 'error' && (
          <div className="w-[64px] h-[64px] rounded-full flex items-center justify-center bg-[#FFF5F5] dark:bg-[#3B1822] mb-3 relative animate-shake-error">
            <svg width="56" height="56" viewBox="0 0 56 56" className="transform -rotate-90">
              <circle
                cx="28"
                cy="28"
                r="24"
                fill="none"
                stroke="#EF4444"
                strokeWidth="4.6"
                strokeLinecap="round"
                className="animate-draw-circle"
              />
            </svg>
            <svg
              width="32"
              height="32"
              viewBox="0 0 32 32"
              fill="none"
              className="absolute"
            >
              <path
                d="M9.5 9.5L22.5 22.5M22.5 9.5L9.5 22.5"
                stroke="#EF4444"
                strokeWidth="4.6"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="animate-draw-cross"
              />
            </svg>
          </div>
        )}

        {/* Message */}
        <p className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF] text-center leading-snug">
          {message}
        </p>
      </div>
    </div>
  );
};

export const AnimatedSuccessModal: React.FC<{
  message: string;
  type?: FeedbackType;
  onClose: () => void;
}> = (props) => <AnimatedFeedbackModal {...props} />;
