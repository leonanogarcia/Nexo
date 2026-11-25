
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { NavKey, CompanyBrandSettings } from '../types';
import { useI18n } from '../i18n/I18nContext';

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
        className={`w-[44px] h-[24px] rounded-full transition-colors duration-200 ease-in-out cursor-pointer focus:outline-none shrink-0 relative m-0 border-0 select-none ${disabled ? 'opacity-50 cursor-not-allowed' : ''
          } ${!checked ? 'bg-[#CBD5E1] dark:bg-[#334155]' : ''}`}
      >
        <span
          className={`block absolute top-1/2 -translate-y-1/2 w-[20px] h-[20px] rounded-full transition-all duration-200 ease-in-out shadow-sm pointer-events-none bg-white ${checked ? 'left-[22px]' : 'left-[2px]'
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

export const EditPencilIcon: React.FC<{ color?: string; size?: number; className?: string }> = ({
  color = 'currentColor',
  size = 16,
  className = '',
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path
      d="M4.2 15.6L14.3 5.5L18.5 9.7L8.4 19.8L3.8 20.4C3.5 20.45 3.35 20.3 3.4 20L4.2 15.6Z"
      fill={color}
    />
    <path
      d="M15.7 4.1L17.4 2.4C18 1.8 19 1.8 19.6 2.4L21.6 4.4C22.2 5 22.2 6 21.6 6.6L19.9 8.3L15.7 4.1Z"
      fill={color}
    />
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

export const PaperclipIcon: React.FC<{ color?: string; size?: number; className?: string }> = ({
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
    strokeWidth="2.1"
    strokeLinecap="butt"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
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
      baseFill: '#4C6287',
      hoverFill: '#3D5070',
      text: '#FFFFFF',
      border: '#3D5070',
      darkBaseFill: '#334A73',
      darkHoverFill: '#466191',
      darkText: '#FFFFFF',
      darkBorder: '#466191',
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
      className={`rounded-full font-bold text-[13px] px-4 border shadow-sm inline-flex items-center justify-center text-center gap-1.5 transition-all duration-150 shrink-0 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {icon && <span className="inline-flex items-center justify-center shrink-0">{icon}</span>}
      <span
        className={`${width ? 'truncate' : 'whitespace-nowrap'} leading-[1.35]`}
        title={label}
      >
        {label}
      </span>
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
  disabled?: boolean;
}

interface FloatingRect {
  top?: number;
  bottom?: number;
  left: number;
  right?: number;
  width: number;
  maxHeight: number;
}

function useFloatingDropdownPosition(
  anchorRef: React.RefObject<HTMLElement | null>,
  open: boolean,
  preferredMaxHeight = 240
): FloatingRect | null {
  const [pos, setPos] = useState<FloatingRect | null>(null);

  useEffect(() => {
    if (!open) {
      setPos(null);
      return;
    }
    const update = () => {
      const el = anchorRef.current;
      if (!el) return;
      const r = el.getBoundingClientRect();
      const gap = 6;
      const spaceBelow = window.innerHeight - r.bottom - 12;
      const spaceAbove = r.top - 12;
      const openUp = spaceBelow < Math.min(preferredMaxHeight, 170) && spaceAbove > spaceBelow;
      if (openUp) {
        setPos({
          bottom: window.innerHeight - r.top + gap,
          left: r.left,
          right: window.innerWidth - r.right,
          width: r.width,
          maxHeight: Math.max(120, Math.min(preferredMaxHeight, spaceAbove)),
        });
      } else {
        setPos({
          top: r.bottom + gap,
          left: r.left,
          right: window.innerWidth - r.right,
          width: r.width,
          maxHeight: Math.max(120, Math.min(preferredMaxHeight, spaceBelow)),
        });
      }
    };
    update();
    window.addEventListener('scroll', update, true);
    window.addEventListener('resize', update);
    return () => {
      window.removeEventListener('scroll', update, true);
      window.removeEventListener('resize', update);
    };
  }, [anchorRef, open, preferredMaxHeight]);

  return pos;
}

const normalizeDropdownSearch = (s: string) =>
  s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

export const RoundedDropdown: React.FC<RoundedDropdownProps> = ({
  value,
  onChange,
  options,
  width = 120,
  height = 32,
  align = 'center',
  placeholder = 'Selecione...',
  disabled = false,
}) => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState<number>(-1);
  const wrapRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const optionRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const pos = useFloatingDropdownPosition(wrapRef, open, 240);

  const filteredOptions = useMemo(() => {
    const q = normalizeDropdownSearch(query.trim());
    if (!q) return options;
    return options.filter((opt) => normalizeDropdownSearch(opt).includes(q));
  }, [options, query]);

  const closeMenu = () => {
    setOpen(false);
    setQuery('');
    setActiveIndex(-1);
  };

  const openMenu = () => {
    if (disabled) return;
    setQuery('');
    const idx = options.indexOf(value);
    setActiveIndex(idx >= 0 ? idx : options.length > 0 ? 0 : -1);
    setOpen(true);
    requestAnimationFrame(() => {
      inputRef.current?.focus();
    });
  };

  const selectOption = (opt: string) => {
    onChange(opt);
    closeMenu();
  };

  useEffect(() => {
    if (!open) return;
    if (query.trim()) {
      setActiveIndex(filteredOptions.length > 0 ? 0 : -1);
    }
  }, [query, filteredOptions.length, open]);

  useEffect(() => {
    if (!open || activeIndex < 0) return;
    optionRefs.current[activeIndex]?.scrollIntoView({ block: 'nearest' });
  }, [activeIndex, open]);

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (
        wrapRef.current &&
        !wrapRef.current.contains(target) &&
        (!menuRef.current || !menuRef.current.contains(target))
      ) {
        closeMenu();
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleOutside);
    }
    return () => document.removeEventListener('mousedown', handleOutside);
  }, [open]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!open) {
        openMenu();
      } else if (filteredOptions.length > 0) {
        setActiveIndex((prev) => (prev + 1) % filteredOptions.length);
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (!open) {
        openMenu();
      } else if (filteredOptions.length > 0) {
        setActiveIndex((prev) => (prev <= 0 ? filteredOptions.length - 1 : prev - 1));
      }
    } else if (e.key === 'Enter') {
      if (open) {
        e.preventDefault();
        if (activeIndex >= 0 && filteredOptions[activeIndex] !== undefined) {
          selectOption(filteredOptions[activeIndex]);
        }
      }
    } else if (e.key === 'Escape') {
      if (open) {
        e.preventDefault();
        closeMenu();
      }
    } else if (e.key === 'Tab') {
      if (open) {
        closeMenu();
      }
    }
  };

  return (
    <div
      ref={wrapRef}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: `${height}px`,
      }}
      className="relative inline-block shrink-0"
    >
      <div
        onClick={() => {
          if (!open) openMenu();
        }}
        className={`relative w-full h-full rounded-full bg-white dark:bg-[#0E1B35] border transition-colors flex items-center ${
          open
            ? 'border-[#F28C28]'
            : 'border-[#B0C0D6] dark:border-[#24385E]'
        } ${disabled
          ? 'opacity-60 cursor-not-allowed'
          : 'hover:bg-[#F8FAFC] dark:hover:bg-[#142544] cursor-text'
          } ${align === 'center' ? 'pl-3.5 pr-7 justify-center font-bold' : 'px-4 justify-between font-normal'
          }`}
      >
        {open ? (
          <input
            ref={inputRef}
            type="text"
            value={query}
            disabled={disabled}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={value || placeholder}
            className={`w-full h-full bg-transparent text-[13px] leading-[1.35] focus:outline-none text-[#18223A] dark:text-[#F4F7FF] placeholder-[#9AA9BF] font-normal ${
              align === 'center' ? 'text-center' : 'text-left pr-2'
            }`}
          />
        ) : (
          <button
            type="button"
            disabled={disabled}
            onFocus={() => openMenu()}
            onKeyDown={handleKeyDown}
            className={`w-full h-full flex items-center focus:outline-none ${
              align === 'center' ? 'justify-center' : 'justify-start'
            }`}
          >
            <span
              title={value || placeholder}
              className={`text-[13px] truncate leading-[1.35] ${value
                ? 'text-[#18223A] dark:text-[#F4F7FF]'
                : 'text-[#9AA9BF] font-normal'
                } ${align === 'center' ? 'flex-1 text-center' : 'pr-2'}`}
            >
              {value || placeholder}
            </span>
          </button>
        )}
        <button
          type="button"
          tabIndex={-1}
          disabled={disabled}
          onMouseDown={(e) => {
            e.preventDefault();
            e.stopPropagation();
            if (open) closeMenu();
            else openMenu();
          }}
          className={`text-[#687796] shrink-0 flex items-center justify-center cursor-pointer ${
            align === 'center' ? 'absolute right-3.5' : ''
          }`}
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            className={`transition-transform duration-150 ${open ? 'rotate-180' : ''}`}
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
      </div>

      {open &&
        pos &&
        createPortal(
          <div
            ref={menuRef}
            style={{
              position: 'fixed',
              top: pos.top,
              bottom: pos.bottom,
              left: pos.left,
              width: pos.width,
              maxHeight: pos.maxHeight,
            }}
            className="rounded-[12px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-xl z-[9999] overflow-y-auto py-1"
          >
            {filteredOptions.length === 0 ? (
              <div className="px-4 py-2 text-xs text-[#9AA9BF] text-center">
                {options.length === 0 ? 'Sem opções' : 'Nenhum resultado'}
              </div>
            ) : (
              filteredOptions.map((opt, idx) => {
                const isSelected = opt === value;
                const isActive = idx === activeIndex;
                return (
                  <button
                    key={opt}
                    ref={(el) => {
                      optionRefs.current[idx] = el;
                    }}
                    type="button"
                    onMouseEnter={() => setActiveIndex(idx)}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      selectOption(opt);
                    }}
                    className={`w-full min-h-9 h-auto py-1.5 px-3.5 text-[13px] leading-snug whitespace-normal break-normal flex items-center transition-colors cursor-pointer ${
                      align === 'center' ? 'justify-center text-center' : 'justify-start text-left'
                    } ${
                      isActive
                        ? 'bg-[#EEF4FC] dark:bg-[#1B2F56]'
                        : 'hover:bg-[#F8FAFC] dark:hover:bg-[#172746]'
                    } ${
                      isSelected
                        ? 'text-[#BA5200] dark:text-[#F28C28] font-bold'
                        : 'text-[#18223A] dark:text-[#F4F7FF] font-normal'
                    }`}
                  >
                    <span title={opt}>{opt}</span>
                  </button>
                );
              })
            )}
          </div>,
          document.body
        )}
    </div>
  );
};

// ---------- CapsuleInput (Form fields) ----------

interface CapsuleInputProps {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  type?: 'text' | 'numeric' | 'money' | 'date' | 'password';
  autoCapitalizeFirst?: boolean;
  spellCheck?: boolean;
  className?: string;
  disabled?: boolean;
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
  disabled = false,
}) => {
  const { formatMoneyInput } = useI18n();
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let v = e.target.value;
    if (type === 'money') {
      onChange(formatMoneyInput(v));
      return;
    }
    if (type === 'numeric') {
      v = v.replace(/[^0-9.,]/g, '');
      onChange(v);
      return;
    }
    if (type !== 'password' && autoCapitalizeFirst && v.length > 0) {
      v = v.replace(/[a-zA-ZÀ-ÿ]/, (m) => m.toUpperCase());
    }
    onChange(v);
  };

  return (
    <input
      type={type === 'date' ? 'date' : type === 'password' ? 'password' : 'text'}
      value={value}
      onChange={handleChange}
      placeholder={placeholder}
      disabled={disabled}
      autoComplete={type === 'password' ? 'new-password' : 'off'}
      spellCheck={type === 'text' ? spellCheck : false}
      lang="pt-BR"
      className={`h-[32px] w-full rounded-full bg-white dark:bg-[#0E1B35] border border-[#B0C0D6] dark:border-[#24385E] px-3.5 text-[12.5px] text-[#18223A] dark:text-[#F4F7FF] placeholder-[#9AA9BF] focus:outline-none focus:border-[#F28C28] dark:focus:border-[#F28C28] transition-colors disabled:opacity-60 disabled:cursor-not-allowed ${className}`}
    />
  );
};

export const NexoTooltip: React.FC<{
  text?: string;
  children: React.ReactNode;
  placement?: 'top' | 'bottom';
  className?: string;
}> = ({ text, children, placement = 'top', className = '' }) => {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState<{ left: number; top: number; actualPlacement: 'top' | 'bottom' } | null>(null);
  const anchorRef = useRef<HTMLSpanElement>(null);

  const show = () => {
    if (!text) return;
    const el = anchorRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const centerX = Math.max(24, Math.min(window.innerWidth - 24, rect.left + rect.width / 2));
    const preferTop = placement === 'top';
    const actualPlacement: 'top' | 'bottom' =
      preferTop && rect.top < 46 ? 'bottom' : !preferTop && window.innerHeight - rect.bottom < 46 ? 'top' : placement;
    const top = actualPlacement === 'top' ? rect.top - 8 : rect.bottom + 8;
    setCoords({ left: centerX, top, actualPlacement });
    setVisible(true);
  };

  const hide = () => setVisible(false);

  if (!text) return <>{children}</>;

  return (
    <span
      ref={anchorRef}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      onMouseDown={hide}
      className={`inline-flex items-center min-w-0 ${className}`}
    >
      {children}
      {visible &&
        coords &&
        createPortal(
          <div
            style={{
              position: 'fixed',
              left: coords.left,
              top: coords.top,
              transform: coords.actualPlacement === 'top' ? 'translate(-50%, -100%)' : 'translate(-50%, 0)',
            }}
            className="pointer-events-none z-[10000] max-w-[280px] px-3 py-1.5 rounded-full bg-[#18223A] dark:bg-[#F4F7FF] text-white dark:text-[#18223A] text-[11.5px] font-semibold leading-snug text-center shadow-lg border border-[#24385E]/40 dark:border-[#DDE5F2]"
          >
            {text}
          </div>,
          document.body
        )}
    </span>
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
  unitPlaceholder?: string;
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
  unitPlaceholder = 'Un.',
  disabled = false,
}) => {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState<number>(-1);
  const wrapRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const unitOptionRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const pos = useFloatingDropdownPosition(wrapRef, open, 190);

  useEffect(() => {
    if (!open || activeIndex < 0) return;
    unitOptionRefs.current[activeIndex]?.scrollIntoView({ block: 'nearest' });
  }, [activeIndex, open]);

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (
        wrapRef.current &&
        !wrapRef.current.contains(target) &&
        (!menuRef.current || !menuRef.current.contains(target))
      ) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleOutside);
    }
    return () => document.removeEventListener('mousedown', handleOutside);
  }, [open]);

  const toggleUnitMenu = () => {
    if (disabled) return;
    setOpen((o) => {
      const next = !o;
      if (next) {
        const idx = unitOptions.indexOf(unitValue);
        setActiveIndex(idx >= 0 ? idx : unitOptions.length > 0 ? 0 : -1);
      }
      return next;
    });
  };

  const handleUnitKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!open) {
        toggleUnitMenu();
      } else if (unitOptions.length > 0) {
        setActiveIndex((prev) => (prev + 1) % unitOptions.length);
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (!open) {
        toggleUnitMenu();
      } else if (unitOptions.length > 0) {
        setActiveIndex((prev) => (prev <= 0 ? unitOptions.length - 1 : prev - 1));
      }
    } else if (e.key === 'Enter' && open) {
      e.preventDefault();
      if (activeIndex >= 0 && unitOptions[activeIndex] !== undefined) {
        onUnitChange(unitOptions[activeIndex]);
        setOpen(false);
      }
    } else if (e.key === 'Escape' && open) {
      e.preventDefault();
      setOpen(false);
    }
  };

  return (
    <div
      ref={wrapRef}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: `${height}px`,
      }}
      className={`relative inline-flex items-center rounded-full bg-white dark:bg-[#0E1B35] border border-[#B0C0D6] dark:border-[#24385E] transition-colors ${disabled
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
        className="flex-1 min-w-[54px] h-full bg-transparent px-2.5 text-[13px] text-[#18223A] dark:text-[#F4F7FF] placeholder-[#9AA9BF] focus:outline-none text-center font-medium"
      />

      {/* Gray Divider Line */}
      <div className="w-[1px] h-[18px] bg-[#B0C0D6] dark:bg-[#2A3F66] shrink-0" />

      {/* Unit Selector Trigger */}
      <NexoTooltip
        text={unitValue && unitValue.length > 6 ? unitValue : undefined}
        className="h-full max-w-[56%]"
      >
        <button
          type="button"
          disabled={disabled}
          onClick={toggleUnitMenu}
          onKeyDown={handleUnitKeyDown}
          className={`h-full min-w-0 max-w-full px-2.5 flex items-center justify-center gap-1.5 text-[12.5px] transition-colors cursor-pointer select-none focus:outline-none ${
            unitValue
              ? 'font-bold text-[#18223A] dark:text-[#F4F7FF] hover:text-[#BA5200] dark:hover:text-[#F28C28]'
              : 'font-normal text-[#9AA9BF] hover:text-[#687796] dark:hover:text-[#CBD5E1]'
          }`}
        >
          <span className="truncate">{unitValue || unitPlaceholder}</span>
          <svg
            width="10"
            height="10"
            viewBox="0 0 12 12"
            fill="none"
            className={`text-[#687796] shrink-0 transition-transform duration-150 ${open ? 'rotate-180' : ''
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
      </NexoTooltip>

      {/* Floating Unit Dropdown */}
      {open &&
        pos &&
        createPortal(
          <div
            ref={menuRef}
            style={{
              position: 'fixed',
              top: pos.top,
              bottom: pos.bottom,
              right: pos.right,
              maxHeight: pos.maxHeight,
            }}
            className="min-w-[110px] w-max max-w-[240px] overflow-y-auto rounded-[12px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-xl py-1 z-[9999]"
          >
            {unitOptions.map((u, idx) => (
              <button
                key={u}
                ref={(el) => {
                  unitOptionRefs.current[idx] = el;
                }}
                type="button"
                onMouseEnter={() => setActiveIndex(idx)}
                onClick={() => {
                  onUnitChange(u);
                  setOpen(false);
                }}
                className={`w-full min-h-8 h-auto py-1.5 px-3 text-[12.5px] leading-snug text-center whitespace-normal break-normal flex items-center justify-center transition-colors cursor-pointer ${
                  idx === activeIndex
                    ? 'bg-[#EEF4FC] dark:bg-[#1B2F56]'
                    : 'hover:bg-[#F8FAFC] dark:hover:bg-[#172746]'
                } ${u === unitValue
                  ? 'text-[#BA5200] dark:text-[#F28C28] font-bold bg-[#FFF7EE] dark:bg-[#2C1C0D]'
                  : 'text-[#18223A] dark:text-[#F4F7FF] font-normal'
                  }`}
              >
                {u}
              </button>
            ))}
          </div>,
          document.body
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

const NAV_ITEMS: { key: NavKey; labelKey: string }[] = [
  { key: 'Geral', labelKey: 'nav.home' },
  { key: 'Cadastro', labelKey: 'nav.materials' },
  { key: 'Receitas', labelKey: 'nav.recipes' },
  { key: 'Produtos', labelKey: 'nav.products' },
  { key: 'Configurações', labelKey: 'nav.settings' },
];

const NexoHomeNavIcon: React.FC<{ className?: string }> = ({ className = 'w-full h-full' }) => (
  <svg
    viewBox="0 0 36 36"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
    className={`text-white pointer-events-none select-none ${className}`}
  >
    <path
      d="M18 4.8L6.6 14.4C6.1 14.9 5.8 15.6 5.8 16.4V27.6C5.8 29.6 7.4 31.2 9.4 31.2H14.3V23C14.3 21.9 15.2 21 16.3 21H19.7C20.8 21 21.7 21.9 21.7 23V31.2H26.6C28.6 31.2 30.2 29.6 30.2 27.6V16.4C30.2 15.6 29.9 14.9 29.4 14.4L18 4.8Z"
      stroke="currentColor"
      strokeWidth="2.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const NexoCadastroNavIcon: React.FC<{ className?: string }> = ({
  className = 'w-full h-full',
}) => (
  <svg
    viewBox="0 0 36 36"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
    className={`text-white pointer-events-none select-none ${className}`}
  >
    {/* Folhinha com corte no canto superior direito (mesmo desenho vetorial do empty state) */}
    <path
      d="M10.2 3H24L30 9V28.8C30 31.1 28.1 33 25.8 33H10.2C7.9 33 6 31.1 6 28.8V7.2C6 4.9 7.9 3 10.2 3Z"
      stroke="currentColor"
      strokeWidth="2.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    {/* Linha 1: check + traço (centralizado) */}
    <path
      d="M11.5 12.2L13.3 14L16.3 10.8"
      stroke="currentColor"
      strokeWidth="2.4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M19 12.5H24.5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    {/* Linha 2: ponto + traço */}
    <circle cx="12.7" cy="18.5" r="1.6" fill="currentColor" />
    <path d="M16.8 18.5H24.5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    {/* Linha 3 (final): traço contínuo com a mesma largura total das linhas de cima */}
    <path d="M12.3 24.5H24.5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
  </svg>
);

const NexoRecipesNavIcon: React.FC<{ className?: string }> = ({ className = 'w-full h-full' }) => (
  <svg
    viewBox="0 0 36 36"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
    className={`text-white pointer-events-none select-none ${className}`}
  >
    <path
      d="M8.5 14.5H27.5C29.4 14.5 31 16.1 31 18V20.6C31 21.4 30.6 22.1 30 22.5C30.6 22.9 31 23.6 31 24.5V27.8C31 29.8 29.4 31.4 27.5 31.4H8.5C6.6 31.4 5 29.8 5 27.8V24.5C5 23.6 5.4 22.9 6 22.5C5.4 22.1 5 21.4 5 20.6V18C5 16.1 6.6 14.5 8.5 14.5Z"
      stroke="currentColor"
      strokeWidth="2.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    {/* Franja de cobertura: 4 arcos (U) ligados entre si formando pontinhas para cima */}
    <path
      d="M5.6 22.2Q8.7 25.6 11.8 22.2Q14.9 25.6 18 22.2Q21.1 25.6 24.2 22.2Q27.3 25.6 30.4 22.2"
      stroke="currentColor"
      strokeWidth="2.4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M11.5 14.5V10.6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    <path d="M18 14.5V10.6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    <path d="M24.5 14.5V10.6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    <circle cx="11.5" cy="6.2" r="1.9" fill="currentColor" />
    <circle cx="18" cy="6.2" r="1.9" fill="currentColor" />
    <circle cx="24.5" cy="6.2" r="1.9" fill="currentColor" />
  </svg>
);

const NexoProductsNavIcon: React.FC<{ className?: string }> = ({ className = 'w-full h-full' }) => (
  <svg
    viewBox="0 0 36 36"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
    className={`text-white pointer-events-none select-none ${className}`}
  >
    {/* Topo do cupcake: arco lateral incompleto com menos sobra nas pontas */}
    <path
      d="M7 20.2C5.8 19.6 5.6 18 5.8 16C6.2 12.2 9.2 9 13 8.4C14 5.6 15.8 4.4 18 4.4C20.2 4.4 22 5.6 23 8.4C26.8 9 29.8 12.2 30.2 16C30.4 18 30.2 19.6 29 20.2"
      stroke="currentColor"
      strokeWidth="2.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    {/* Serrilhado suavizado (menor amplitude entre crista e vale) */}
    <path
      d="M7 20.2L9.7 21.1L12.4 19.6L15.2 21.1L18 19.6L20.8 21.1L23.6 19.6L26.3 21.1L29 20.2"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    {/* Base / forminha um pouco maior e mais larga */}
    <path
      d="M8.4 20.8L10.6 29.8C10.9 30.9 11.8 31.6 13 31.6H23C24.2 31.6 25.1 30.9 25.4 29.8L27.6 20.8"
      stroke="currentColor"
      strokeWidth="2.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const NexoSettingsNavIcon: React.FC<{ className?: string }> = ({ className = 'w-full h-full' }) => (
  <svg
    viewBox="0 0 36 36"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
    className={`text-white pointer-events-none select-none ${className}`}
  >
    {/* 6 dentes matematicamente equidistantes a cada 60° em torno de (18, 18) */}
    <path
      d="M14.67 8.04L14.72 3.77L21.28 3.77L21.33 8.04L24.96 10.14L28.68 8.04L31.96 13.73L28.29 15.91L28.29 20.09L31.96 22.27L28.68 27.96L24.96 25.86L21.33 27.96L21.28 32.23L14.72 32.23L14.67 27.96L11.04 25.86L7.32 27.96L4.04 22.27L7.71 20.09L7.71 15.91L4.04 13.73L7.32 8.04L11.04 10.14Z"
      stroke="currentColor"
      strokeWidth="2.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle cx="18" cy="18" r="3.7" stroke="currentColor" strokeWidth="2.6" />
  </svg>
);

const renderSidebarNavIcon = (key: NavKey) => {
  const cls = 'w-[clamp(31px,4.8vh,37px)] h-[clamp(31px,4.8vh,37px)]';
  if (key === 'Geral') return <NexoHomeNavIcon className={cls} />;
  if (key === 'Cadastro') return <NexoCadastroNavIcon className={cls} />;
  if (key === 'Receitas') return <NexoRecipesNavIcon className={cls} />;
  if (key === 'Produtos') return <NexoProductsNavIcon className={cls} />;
  return <NexoSettingsNavIcon className={cls} />;
};

export const ReferenceSidebar: React.FC<ReferenceSidebarProps> = ({
  active,
  onSelect,
  dark,
  brandSettings,
}) => {
  const [hovered, setHovered] = useState<NavKey | null>(null);
  const { t } = useI18n();

  return (
    <aside className="w-[150px] h-full shrink-0 flex flex-col items-center relative select-none">
      {/* Top Brand / Nexo Logo */}
      <div className="mt-[12px] w-[140px] flex flex-col items-center justify-center px-1 shrink-0 min-h-[72px] max-h-[104px]">
        {brandSettings?.company_logo ? (
          <div className="flex flex-col items-center justify-center max-w-[136px] group">
            {/* Nome da Empresa no Topo (apenas se show_company_name estiver ativo) */}
            {brandSettings.show_company_name !== false &&
              brandSettings.company_name &&
              brandSettings.company_name !== 'Nexo' && (
                <span
                  title={brandSettings.company_name}
                  className="text-[12px] font-extrabold text-center truncate max-w-[132px] px-1 text-[#18223A] dark:text-[#F4F7FF] tracking-tight mb-2 leading-tight"
                >
                  {brandSettings.company_name}
                </span>
              )}

            {/* Imagem da Logo: livre e fluida, sem caixa branca forçada */}
            <div
              className={`relative flex items-center justify-center transition-transform duration-150 group-hover:scale-[1.02] ${brandSettings.logo_shape === 'rect'
                ? 'max-w-[128px] max-h-[96px]'
                : 'w-[94px] h-[94px] rounded-full overflow-hidden shadow-sm'
                }`}
            >
              <img
                src={brandSettings.company_logo}
                alt={brandSettings.company_name || 'Empresa'}
                className={`w-full h-full object-contain ${brandSettings.logo_shape === 'rect' ? 'rounded-lg' : 'rounded-full'
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

      {/* Vertical Capsule Rail (width=58px, responsive height so it never clips on smaller laptops) */}
      <div className="flex-1 w-full flex items-center justify-center pb-4 min-h-0">
        <div
          style={{
            width: '58px',
            height: 'min(500px, calc(100vh - 140px))',
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
          className="rounded-full border flex flex-col items-center justify-between py-[clamp(12px,2.8vh,26px)] relative transition-colors duration-200"
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
                    width: '46px',
                    height: 'clamp(44px, 7.4vh, 56px)',
                    borderRadius: '18px',
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
                  {renderSidebarNavIcon(item.key)}
                </button>

                {/* Capsule Tooltip on Hover */}
                {isHovered && (
                  <div
                    style={{
                      backgroundColor: dark ? '#2A3B5C' : '#101A33',
                    }}
                    className="absolute left-[60px] top-1/2 -translate-y-1/2 h-[26px] px-3 rounded-full text-white font-semibold text-[11.5px] leading-none flex items-center justify-center whitespace-nowrap shadow-lg z-50 pointer-events-none animate-fade-in"
                  >
                    {t(item.labelKey)}
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
      className={`fixed inset-0 z-[100] flex items-center justify-center pointer-events-none transition-opacity duration-300 ${closing ? 'opacity-0' : 'opacity-100'
        }`}
    >
      <div
        className={`w-[290px] p-6 rounded-[24px] bg-white/95 dark:bg-[#111F3B]/95 backdrop-blur-md border border-[#DDE5F2] dark:border-[#24385E] shadow-2xl flex flex-col items-center justify-center select-none transition-all duration-300 pointer-events-auto ${closing
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

// ---------- Nexo Table Standard: Column Resize, Auto-Fit & Persistence ----------

let _measureCanvas: HTMLCanvasElement | null = null;

/**
 * Mede a largura em pixels de um texto com a fonte padrão do Nexo.
 */
export function measureNexoTextWidth(text: string, font = '500 13px "Segoe UI", Inter, system-ui, sans-serif'): number {
  if (typeof document === 'undefined') return text.length * 8;
  if (!_measureCanvas) {
    _measureCanvas = document.createElement('canvas');
  }
  const ctx = _measureCanvas.getContext('2d');
  if (!ctx) return text.length * 8;
  ctx.font = font;
  return ctx.measureText(text).width;
}

/**
 * Largura mínima da coluna garantindo que o título do cabeçalho + seta (↑/↓) nunca trunquem.
 */
export function getNexoHeaderMinWidth(label: string, extraPadding = 32): number {
  const w = measureNexoTextWidth(`${label} ↑`, '700 12.5px "Segoe UI", Inter, system-ui, sans-serif');
  return Math.ceil(w + extraPadding);
}

/**
 * Calcula a largura ideal (estilo Excel) considerando cabeçalho e todas as células visíveis.
 */
export function getNexoAutoFitWidth(
  label: string,
  cellTexts: string[],
  extraCellPadding = 0
): number {
  const headerMin = getNexoHeaderMinWidth(label);
  let maxCell = 0;
  for (const t of cellTexts) {
    if (!t) continue;
    const w = measureNexoTextWidth(t, '600 13px "Segoe UI", Inter, system-ui, sans-serif');
    if (w > maxCell) maxCell = w;
  }
  return Math.ceil(Math.max(headerMin, maxCell + 30 + extraCellPadding));
}

export interface NexoColumnDef {
  key: string;
  label: string;
  width: number;
}

/**
 * Hook padrão de gerenciamento de larguras de colunas das tabelas do Nexo:
 * - Respeita a largura mínima do cabeçalho (nunca trunca o título).
 * - Permite arraste independente por coluna sem esmagar colunas vizinhas.
 * - Permite duplo clique na divisória para auto-ajuste (estilo Excel).
 * - Persiste as larguras no localStorage por tabela.
 */
export function useNexoColumnWidths(storageKey: string, columns: NexoColumnDef[]) {
  const [colWidths, setColWidths] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    let saved: Record<string, number> = {};
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) saved = JSON.parse(raw) || {};
    } catch {
      saved = {};
    }
    for (const col of columns) {
      const minW = getNexoHeaderMinWidth(col.label);
      const savedW = typeof saved[col.key] === 'number' && saved[col.key] > 0 ? saved[col.key] : col.width;
      initial[col.key] = Math.max(minW, savedW);
    }
    return initial;
  });

  const colWidthsRef = useRef(colWidths);
  colWidthsRef.current = colWidths;
  const justResizedRef = useRef(false);

  const persistWidths = (next: Record<string, number>) => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(next));
    } catch {
      // ignore storage errors
    }
  };

  const startResize = (key: string, label: string, defaultWidth: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const startX = e.clientX;
    const startW = colWidthsRef.current[key] ?? Math.max(defaultWidth, getNexoHeaderMinWidth(label));
    const minW = getNexoHeaderMinWidth(label);
    let moved = false;

    const prevCursor = document.body.style.cursor;
    const prevUserSelect = document.body.style.userSelect;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const onMouseMove = (ev: MouseEvent) => {
      const delta = ev.clientX - startX;
      if (Math.abs(delta) > 2) moved = true;
      const nextW = Math.max(minW, Math.round(startW + delta));
      setColWidths((prev) => {
        if (prev[key] === nextW) return prev;
        return { ...prev, [key]: nextW };
      });
    };

    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = prevCursor;
      document.body.style.userSelect = prevUserSelect;
      if (moved) {
        justResizedRef.current = true;
        setTimeout(() => {
          justResizedRef.current = false;
        }, 80);
      }
      persistWidths(colWidthsRef.current);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const autoFitColumn = (
    key: string,
    label: string,
    cellTexts: string[],
    extraCellPadding = 0,
    e?: React.MouseEvent
  ) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    const fitW = getNexoAutoFitWidth(label, cellTexts, extraCellPadding);
    justResizedRef.current = true;
    setTimeout(() => {
      justResizedRef.current = false;
    }, 80);
    setColWidths((prev) => {
      const next = { ...prev, [key]: fitW };
      persistWidths(next);
      return next;
    });
  };

  const shouldIgnoreSortClick = () => justResizedRef.current;

  return {
    colWidths,
    startResize,
    autoFitColumn,
    shouldIgnoreSortClick,
  };
}

/**
 * Área sensível invisível sobre a linha divisória do cabeçalho da tabela (cursor col-resize sem poluição visual).
 */
export const ColumnResizeHandle: React.FC<{
  onMouseDown: (e: React.MouseEvent) => void;
  onDoubleClick: (e: React.MouseEvent) => void;
}> = ({ onMouseDown, onDoubleClick }) => (
  <span
    role="separator"
    aria-orientation="vertical"
    onClick={(e) => e.stopPropagation()}
    onMouseDown={onMouseDown}
    onDoubleClick={onDoubleClick}
    title="Arraste para redimensionar · Duplo clique para auto-ajustar"
    className="absolute right-[-4px] top-0 h-full w-[8px] cursor-col-resize z-30 select-none"
  />
);

/**
 * Ícone padrão Nexo para links de navegação/expansão ("Ver todas", "Ajustar", pendências).
 */
export const OpenSectionIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none">
    <rect
      x="2.75"
      y="2.75"
      width="18.5"
      height="18.5"
      rx="5"
      stroke="currentColor"
      strokeWidth="2.4"
    />
    <path
      d="M3 12.2h6.3a3 3 0 0 1 3 3V21H7.5A4.5 4.5 0 0 1 3 16.5v-4.3z"
      fill="currentColor"
    />
    <path
      d="M12.3 11.7l4.6-4.6m0 0h-3.4m3.4 0v3.4"
      stroke="currentColor"
      strokeOpacity="0.65"
      strokeWidth="2.3"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const NexoEmptyStateIcon: React.FC<{ className?: string }> = ({
  className = 'w-[115px] h-[58px]',
}) => (
  <svg
    viewBox="0 0 116 58"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
    className={`text-[#B0C2DC] dark:text-[#4C648E] pointer-events-none select-none shrink-0 ${className}`}
  >
    {/* Left radiating lines */}
    <path d="M11 16L18 20.5" stroke="currentColor" strokeWidth="3.8" strokeLinecap="round" />
    <path d="M3 29.5H16" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
    <path d="M11 43.5L18 39" stroke="currentColor" strokeWidth="3.8" strokeLinecap="round" />

    {/* Right radiating lines */}
    <path d="M105 16L98 20.5" stroke="currentColor" strokeWidth="3.8" strokeLinecap="round" />
    <path d="M113 29.5H100" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
    <path d="M105 43.5L98 39" stroke="currentColor" strokeWidth="3.8" strokeLinecap="round" />

    {/* Document outline with top-left chamfered corner */}
    <path
      d="M47 3.5H71.5C76.2 3.5 80 7.3 80 12V46C80 50.7 76.2 54.5 71.5 54.5H44.5C39.8 54.5 36 50.7 36 46V14.5L47 3.5Z"
      stroke="currentColor"
      strokeWidth="5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />

    {/* Row 1: short bar */}
    <path d="M59.5 16.5H69.5" stroke="currentColor" strokeWidth="4.6" strokeLinecap="round" />

    {/* Row 2: checkmark + bar */}
    <path
      d="M46.5 25L49 27.5L53.5 22.8"
      stroke="currentColor"
      strokeWidth="4.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path d="M58 27.5H69.5" stroke="currentColor" strokeWidth="4.6" strokeLinecap="round" />

    {/* Row 3: bullet + bar */}
    <circle cx="47.5" cy="38.5" r="3" fill="currentColor" />
    <path d="M53 38.5H69.5" stroke="currentColor" strokeWidth="4.6" strokeLinecap="round" />
  </svg>
);

export const NexoEmptyTableWatermark: React.FC<{
  title: string;
  subtitle: string;
}> = ({ title, subtitle }) => (
  <div className="absolute inset-x-0 top-[48px] bottom-0 flex flex-col items-center justify-center p-4 pointer-events-none select-none z-10 text-center">
    <NexoEmptyStateIcon className="w-[115px] h-[58px] mb-3" />
    <p className="text-[15px] font-bold text-[#687796] dark:text-[#93A4C6] mb-1">
      {title}
    </p>
    <p className="text-[12.5px] text-[#8A99B5] dark:text-[#687796]">
      {subtitle}
    </p>
  </div>
);

export interface ToolbarOverflowAction {
  label: string;
  onClick: () => void;
  icon?: React.ReactNode;
}

export function useToolbarOverflow(
  ref: React.RefObject<HTMLElement | null>,
  minInlineWidth: number
): boolean {
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const check = () => {
      setCollapsed(el.clientWidth > 0 && el.clientWidth < minInlineWidth);
    };
    check();
    const ro = new ResizeObserver(check);
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref, minInlineWidth]);

  return collapsed;
}

export const NexoToolbarOverflowMenu: React.FC<{
  actions: ToolbarOverflowAction[];
}> = ({ actions }) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    window.addEventListener('mousedown', onDown);
    return () => window.removeEventListener('mousedown', onDown);
  }, [open]);

  if (!actions.length) return null;

  return (
    <div ref={ref} className="relative flex items-center">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        title="Mais ações"
        className="w-7 h-9 flex items-center justify-center text-[#687796] dark:text-[#93A4C6] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="5" r="2" />
          <circle cx="12" cy="12" r="2" />
          <circle cx="12" cy="19" r="2" />
        </svg>
      </button>
      {open && (
        <div className="absolute left-0 top-[40px] z-50 min-w-[190px] rounded-[16px] bg-white dark:bg-[#132240] border border-[#DDE5F2] dark:border-[#24385E] shadow-xl py-1.5">
          {actions.map((act) => (
            <button
              key={act.label}
              type="button"
              onClick={() => {
                setOpen(false);
                act.onClick();
              }}
              className="w-full px-3.5 py-2 flex items-center gap-2.5 text-[13px] font-medium text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#F4F7FC] dark:hover:bg-[#1E3156] text-left cursor-pointer"
            >
              {act.icon && <span className="shrink-0 text-[#60769D] dark:text-[#AFC0E2]">{act.icon}</span>}
              <span>{act.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export const AlertTriangleIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);

export const LockShieldIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="11" width="16" height="10" rx="2.5" />
    <path d="M8 11V7a4 4 0 0 1 8 0v4" />
  </svg>
);

export const TagBadgeIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.59 13.41 13.42 20.58a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82Z" />
    <circle cx="7.5" cy="7.5" r="1.2" fill="currentColor" stroke="none" />
  </svg>
);

export const CartPurchaseIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="9" cy="20" r="1.5" />
    <circle cx="18" cy="20" r="1.5" />
    <path d="M2 3h3l2.4 12.2a1.5 1.5 0 0 0 1.5 1.2h9.4a1.5 1.5 0 0 0 1.45-1.15L21 7H6" />
  </svg>
);

export const EditPenIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 20h9" />
    <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
  </svg>
);

export const NoteTextIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="8" y1="13" x2="16" y2="13" />
    <line x1="8" y1="17" x2="13" y2="17" />
  </svg>
);

export const RefreshSyncIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12a9 9 0 0 0-15.5-6.36L3 8" />
    <polyline points="3 3 3 8 8 8" />
    <path d="M3 12a9 9 0 0 0 15.5 6.36L21 16" />
    <polyline points="21 21 21 16 16 16" />
  </svg>
);

export const HelpCircleIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);

export const SparklesIcon: React.FC<{ className?: string }> = ({ className = 'w-6 h-6' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d="m12 3 1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9Z" />
    <path d="M19 3v3M20.5 4.5h-3M5 18v2M6 19H4" />
  </svg>
);
