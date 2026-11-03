import React, { useEffect, useRef, useState } from 'react';
import { NavKey, CompanyBrandSettings } from '../types';

// ---------- Vector Icons ----------

export interface NexoToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  tooltip?: string;
  className?: string;
  disabled?: boolean;
}

export const NexoToggleSwitch: React.FC<NexoToggleSwitchProps> = ({
  checked,
  onChange,
  tooltip,
  className = '',
  disabled = false,
}) => {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      className={`relative inline-flex items-center ${className}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={(e) => {
          e.stopPropagation();
          if (!disabled) onChange(!checked);
        }}
        style={{
          backgroundColor: checked ? 'var(--nexo-brand-primary, #F28C28)' : undefined,
        }}
        className={`w-[44px] h-[24px] rounded-full transition-colors duration-200 ease-in-out cursor-pointer focus:outline-none shrink-0 relative px-[2px] m-0 border-0 flex items-center select-none ${
          disabled ? 'opacity-50 cursor-not-allowed' : ''
        } ${!checked ? 'bg-[#CBD5E1] dark:bg-[#334155]' : ''}`}
      >
        <span
          className={`block w-[20px] h-[20px] rounded-full transition-transform duration-200 ease-in-out shadow-sm pointer-events-none shrink-0 bg-white ${
            checked ? 'translate-x-[20px]' : 'translate-x-0'
          }`}
        />
      </button>

      {/* Floating Capsule Tooltip no Hover (Padrão Oficial Nexo) */}
      {hovered && tooltip && (
        <div className="absolute right-0 top-[32px] h-[32px] px-4 rounded-full bg-[#101A33] dark:bg-[#2A3B5C] text-white font-bold text-[12px] flex items-center justify-center whitespace-nowrap shadow-lg z-50 pointer-events-none animate-fade-in">
          {tooltip}
        </div>
      )}
    </div>
  );
};

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
    strokeWidth="1.7"
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
    strokeWidth="1.7"
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
    strokeWidth="1.7"
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

export const WorkShiftClockIcon: React.FC<{ className?: string; size?: number; color?: string }> = ({
  className = 'w-6 h-6',
  size,
  color = 'currentColor',
}) => (
  <svg
    width={size}
    height={size}
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {/* Arco do relógio com abertura para a maleta */}
    <path d="M 16.3 7.0 A 7.5 7.5 0 1 0 10.5 16.9" />

    {/* Eixo central e ponteiros em 8h (sem ponteiro de segundos) */}
    <circle cx="9.5" cy="9.5" r="0.8" fill={color} stroke="none" />
    {/* Minutos em 12h */}
    <line x1="9.5" y1="9.5" x2="9.5" y2="4.5" />
    {/* Horas em 8h */}
    <line x1="9.5" y1="9.5" x2="6.38" y2="11.3" />

    {/* Alça superior da maleta */}
    <path d="M 14 11 V 9.2 A 0.8 0.8 0 0 1 14.8 8.4 H 17.2 A 0.8 0.8 0 0 1 18 9.2 V 11" />

    {/* Corpo da maleta de trabalho */}
    <rect x="10.5" y="11" width="11" height="9.8" rx="1.6" />

    {/* Linha divisória horizontal */}
    <line x1="10.5" y1="15.5" x2="14.5" y2="15.5" />
    <line x1="17.5" y1="15.5" x2="21.5" y2="15.5" />

    {/* Fecho central da maleta */}
    <rect x="14.5" y="14.3" width="3" height="2.4" rx="0.6" strokeWidth="1.4" />
  </svg>
);

export const KitchenUtilitiesCostIcon: React.FC<{ className?: string; size?: number; color?: string }> = ({
  className = 'w-6 h-6',
  size,
  color = 'currentColor',
}) => (
  <svg
    width={size}
    height={size}
    className={className}
    viewBox="0 0 24 24"
    fill={color}
  >
    <path fillRule="evenodd" clipRule="evenodd" d="M20.26 19.03 L20.2 18.85 L20.05 18.68 L19.72 18.59 L16.8 19.05 L16.54 19.11 L16.37 19.26 L16.28 19.41 L16.26 19.67 L16.35 19.89 L16.45 20.01 L16.71 20.12 L17.06 20.08 L17.34 20.42 L17.72 20.68 L18.2 20.79 L18.52 20.77 L18.8 20.68 L19.08 20.51 L19.38 20.19 L19.6 19.69 L19.88 19.65 L20.09 19.54 L20.22 19.37 Z M3.89 15.37 L3.72 15.67 L3.72 15.93 L3.8 16.36 L4.06 17.0 L4.47 17.58 L4.94 18.01 L5.59 18.38 L6.36 18.57 L6.64 18.55 L6.84 18.44 L6.97 18.27 L7.01 18.12 L6.99 17.86 L6.88 17.67 L6.64 17.52 L6.0 17.39 L5.63 17.2 L5.24 16.85 L4.9 16.27 L4.77 15.6 L4.56 15.32 L4.25 15.24 L4.04 15.28 Z M11.96 13.11 L11.98 13.82 L11.1 14.16 L10.56 14.7 L10.32 15.37 L10.36 16.06 L10.64 16.62 L11.18 17.07 L13.33 17.78 L13.59 18.08 L13.59 18.55 L13.23 18.92 L12.37 19.05 L11.72 18.83 L11.38 18.12 L10.32 18.12 L10.32 18.4 L10.73 19.37 L11.18 19.76 L11.98 20.06 L11.98 20.79 L13.01 20.79 L13.03 20.06 L13.96 19.71 L14.5 19.13 L14.69 18.55 L14.62 17.73 L14.39 17.26 L13.85 16.81 L11.68 16.1 L11.42 15.78 L11.42 15.37 L11.89 14.94 L12.73 14.85 L13.46 15.22 L13.64 15.8 L14.71 15.8 L14.69 15.47 L14.32 14.55 L13.79 14.1 L13.05 13.84 L13.03 13.09 Z M18.86 9.82 L16.35 13.34 L18.13 13.37 L17.7 15.97 L20.18 12.4 L18.43 12.38 Z M6.32 7.69 L4.51 9.69 L2.66 12.38 L1.69 14.51 L1.5 15.97 L1.95 17.71 L3.24 19.46 L4.84 20.45 L6.73 20.79 L8.36 20.49 L9.78 19.69 L9.38 18.53 L8.13 19.37 L6.71 19.67 L5.31 19.41 L4.15 18.72 L3.18 17.56 L2.68 16.06 L2.83 14.81 L3.48 13.32 L6.47 9.17 L8.43 11.67 L9.83 14.12 L10.71 13.22 L8.19 9.41 L6.79 7.77 Z M16.63 7.88 L16.2 9.36 L17.57 8.72 L19.23 8.78 L20.39 9.41 L21.3 10.83 L21.42 11.95 L21.21 13.17 L19.32 17.0 L17.21 17.0 L15.27 13.02 L15.12 11.41 L15.42 10.35 L14.07 11.21 L14.22 13.22 L15.38 14.42 L15.68 16.08 L16.45 18.01 L19.94 18.08 L20.28 17.73 L20.56 16.55 L22.26 13.37 L22.48 12.2 L22.31 10.44 L21.64 9.15 L20.46 8.12 L18.78 7.6 Z M11.55 3.19 L11.83 4.2 L11.61 5.51 L10.86 6.46 L10.45 6.33 L10.41 5.6 L9.76 6.24 L9.27 7.28 L9.29 8.48 L9.59 9.19 L10.17 9.86 L11.61 10.55 L10.99 9.79 L11.03 8.76 L11.61 7.79 L12.65 7.04 L12.52 7.86 L12.73 8.53 L13.03 8.76 L13.33 8.72 L13.51 8.12 L14.02 9.02 L13.98 9.84 L13.48 10.5 L14.5 10.01 L15.36 9.11 L15.72 8.2 L15.7 7.11 L15.18 6.03 L14.5 5.36 L14.5 6.22 L14.04 6.59 L13.76 5.25 L13.25 4.33 L12.56 3.68 Z" />
  </svg>
);

export const KitchenUtensilsIcon: React.FC<{ className?: string; size?: number; color?: string }> = ({
  className = 'w-5 h-5',
  size,
  color = 'currentColor',
}) => (
  <svg
    width={size}
    height={size}
    className={className}
    viewBox="0 0 24 24"
    fill={color}
  >
    <path fillRule="evenodd" clipRule="evenodd" d="M18.74 1.7 L17.61 1.96 L16.35 2.88 L15.67 4.01 L15.35 5.88 L15.85 8.16 L17.4 11.68 L17.8 13.08 L17.72 21.3 L18.19 22.04 L19.0 22.28 L19.69 22.01 L20.11 21.36 L20.06 13.0 L20.45 11.63 L22.18 7.56 L22.47 5.53 L22.18 4.06 L21.55 2.96 L20.34 2.01 Z M18.43 20.46 L19.4 20.46 L19.45 20.52 L19.45 21.15 L19.37 21.33 L19.27 21.46 L19.08 21.57 L18.98 21.57 L18.95 21.59 L18.87 21.59 L18.69 21.54 L18.61 21.49 L18.48 21.36 L18.4 21.2 L18.37 21.09 L18.37 20.52 Z M18.43 13.68 L19.45 13.71 L19.42 19.78 L18.37 19.75 L18.37 13.73 Z M17.74 2.67 L17.85 2.67 L17.56 3.62 L17.4 4.64 L17.35 6.35 L17.51 8.11 L18.03 11.4 L16.59 8.16 L16.22 7.06 L16.06 6.17 L16.09 5.11 L16.35 4.17 L16.77 3.46 L17.24 2.98 Z M20.0 2.62 L20.69 3.06 L21.08 3.48 L21.42 4.04 L21.74 5.11 L21.76 6.19 L21.58 7.16 L21.26 8.11 L19.79 11.42 L20.32 8.14 L20.48 6.19 L20.37 4.25 L20.19 3.3 L19.95 2.64 Z M18.85 2.41 L18.98 2.41 L19.14 2.54 L19.5 3.38 L19.71 4.48 L19.79 5.43 L19.69 7.64 L18.93 12.5 L18.24 8.43 L18.03 6.32 L18.06 4.96 L18.22 3.83 L18.51 2.88 Z M13.06 1.7 L12.07 1.88 L11.09 2.43 L10.3 3.38 L9.88 4.75 L9.88 13.45 L10.09 13.68 L10.88 13.68 L11.01 13.89 L10.94 14.39 L10.54 14.68 L10.54 21.62 L10.86 22.12 L11.3 22.28 L12.78 22.25 L13.22 21.96 L13.38 21.59 L13.38 1.96 Z M11.25 15.13 L12.7 15.15 L12.7 21.51 L12.54 21.59 L11.36 21.59 L11.22 21.51 Z M11.67 13.68 L12.7 13.71 L12.7 14.39 L12.64 14.44 L11.65 14.42 L11.65 14.31 L11.7 14.1 L11.7 13.94 L11.65 13.76 Z M12.64 2.43 L12.67 13.0 L10.57 12.97 L10.59 4.64 L10.78 3.98 L11.25 3.25 L11.93 2.7 Z M4.55 1.7 L3.26 2.2 L2.39 3.14 L1.76 4.54 L1.5 6.3 L1.92 8.16 L3.37 9.84 L3.63 10.5 L3.37 21.07 L3.89 22.01 L4.73 22.28 L5.49 21.99 L5.99 21.07 L5.73 10.48 L5.97 9.87 L7.44 8.16 L7.78 7.11 L7.83 5.85 L7.44 4.09 L6.76 2.85 L5.86 2.04 Z M4.44 2.41 L5.34 2.54 L6.2 3.27 L6.81 4.38 L7.15 6.01 L6.91 7.64 L6.47 8.37 L5.49 9.35 L5.05 10.34 L5.31 20.96 L5.15 21.36 L4.71 21.59 L4.31 21.46 L4.08 21.09 L4.31 10.4 L3.92 9.42 L2.58 7.93 L2.21 6.64 L2.34 5.06 L2.84 3.75 L3.52 2.88 Z" />
  </svg>
);


export const FlameIcon: React.FC<{ color?: string; size?: number; className?: string }> = ({
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
    strokeWidth="2.2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
  </svg>
);

export const ZapEnergyIcon: React.FC<{ color?: string; size?: number; className?: string }> = ({
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
    strokeWidth="2.2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

export const DropletWaterIcon: React.FC<{ color?: string; size?: number; className?: string }> = ({
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
    strokeWidth="2.2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
  </svg>
);

export const PackageBoxIcon: React.FC<{ color?: string; size?: number; className?: string }> = ({
  color = 'currentColor',
  size = 16,
  className = '',
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="1.7"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M16.5 9.4 7.55 4.24" />
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
    <polyline points="3.29 7 12 12 20.71 7" />
    <line x1="12" y1="22" x2="12" y2="12" />
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
      baseFill: 'var(--nexo-brand-primary, #F28C28)',
      hoverFill: 'var(--nexo-brand-hover, #BA5200)',
      text: '#FFFFFF',
      border: 'var(--nexo-brand-border, #DE7819)',
      darkBaseFill: 'var(--nexo-brand-primary, #F28C28)',
      darkHoverFill: 'var(--nexo-brand-hover, #BA5200)',
      darkText: '#FFFFFF',
      darkBorder: 'var(--nexo-brand-border, #F6A24B)',
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
          <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" strokeWidth="1.7" />
          <line
            x1="12.5"
            y1="12.5"
            x2="17"
            y2="17"
            stroke="currentColor"
            strokeWidth="1.7"
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
            strokeWidth="1.7"
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
            strokeWidth="1.7"
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
  brandSettings?: CompanyBrandSettings;
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
  brandSettings,
}) => {
  const [hovered, setHovered] = useState<NavKey | null>(null);

  return (
    <aside className="w-[150px] h-full shrink-0 flex flex-col items-center relative select-none">
      {/* Top Brand / Nexo Logo */}
      <div className="mt-[16px] w-[140px] flex flex-col items-center justify-center px-1 shrink-0 min-h-[96px]">
        {brandSettings?.company_logo ? (
          <div className="flex flex-col items-center justify-center max-w-[136px] group">
            {/* Nome da Empresa no Topo (apenas se show_company_name estiver ativo) */}
            {brandSettings.show_company_name !== false &&
              brandSettings.company_name &&
              brandSettings.company_name !== 'Nexo' && (
                <span className="text-[12px] font-extrabold text-center truncate max-w-[132px] px-1 text-[#18223A] dark:text-[#F4F7FF] tracking-tight mb-2 leading-tight">
                  {brandSettings.company_name}
                </span>
              )}

            {/* Imagem da Logo: livre e fluida, sem caixa branca forçada */}
            <div
              className={`relative flex items-center justify-center transition-transform duration-150 group-hover:scale-[1.02] ${
                brandSettings.logo_shape === 'rect'
                  ? 'max-w-[128px] max-h-[96px]'
                  : 'w-[94px] h-[94px] rounded-full overflow-hidden shadow-sm'
              }`}
            >
              <img
                src={brandSettings.company_logo}
                alt={brandSettings.company_name || 'Empresa'}
                className={`w-full h-full object-contain ${
                  brandSettings.logo_shape === 'rect' ? 'rounded-lg' : 'rounded-full'
                }`}
              />
            </div>
          </div>
        ) : (
          <img
            src={dark ? '/ui_assets/nexo_logo_dark_clean.png' : '/ui_assets/nexo_logo_light_clean.png'}
            alt="Nexo"
            className="max-w-[130px] max-h-[100px] object-contain pointer-events-none transition-opacity duration-150"
          />
        )}
      </div>

      {/* Vertical Capsule Rail (width=68px, height=500px, centered vertically in remaining space) */}
      <div className="flex-1 w-full flex items-center justify-center pb-6">
        <div
          style={{
            width: '68px',
            height: '500px',
            backgroundColor: (brandSettings?.brand_theme_enabled && brandSettings?.apply_brand_to_sidebar && brandSettings?.brand_color)
              ? brandSettings.brand_color
              : (dark ? '#F28C28' : '#111C30'),
            borderColor: (brandSettings?.brand_theme_enabled && brandSettings?.apply_brand_to_sidebar && brandSettings?.brand_color)
              ? (dark ? '#F6A24B' : '#A9BFE0')
              : (dark ? '#F6A24B' : '#A9BFE0'),
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
