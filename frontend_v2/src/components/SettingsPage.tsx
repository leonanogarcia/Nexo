
function extractProminentColor(dataUrl: string): Promise<string> {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = 'Anonymous';
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        if (!ctx) return resolve('#F28C28');
        canvas.width = 48;
        canvas.height = 48;
        ctx.drawImage(img, 0, 0, 48, 48);
        const data = ctx.getImageData(0, 0, 48, 48).data;
        let bestR = 242, bestG = 140, bestB = 40;
        let maxSaturation = -1;

        for (let i = 0; i < data.length; i += 4) {
          const r = data[i];
          const g = data[i + 1];
          const b = data[i + 2];
          const a = data[i + 3];

          if (a < 128) continue;
          const max = Math.max(r, g, b);
          const min = Math.min(r, g, b);
          const lum = (max + min) / 2;
          if (lum < 30 || lum > 230) continue;
          const delta = max - min;
          if (delta < 25) continue;

          const sat = delta / (max || 1);
          if (sat > maxSaturation) {
            maxSaturation = sat;
            bestR = r;
            bestG = g;
            bestB = b;
          }
        }
        const hex = '#' + [bestR, bestG, bestB].map((x) => x.toString(16).padStart(2, '0')).join('');
        resolve(hex);
      } catch {
        resolve('#F28C28');
      }
    };
    img.onerror = () => resolve('#F28C28');
    img.src = dataUrl;
  });
}

import React, { useState, useEffect, useRef } from 'react';
import {
  RoundedActionButton,
  CapsuleInput,
  RoundedDropdown,
  NexoCheckbox,
  NexoToggleSwitch,
  TrashIcon,
  PlusIcon,
  RoundedEntry,
  GearPolygonIcon,
} from './DesignSystem';
import { CompanyBrandSettings } from '../types';

export interface SettingsPageProps {
  onNotify: (msg: string, type?: 'success' | 'warning' | 'error') => void;
  dark: boolean;
  onThemeToggle: (isDark: boolean) => void;
  onBrandUpdate?: (brand: CompanyBrandSettings) => void;
}

type SettingsCategoryKey = 'geral' | 'ia' | 'metricas' | 'unidades' | 'banco';

// --- Clean Monochrome Vector Icons (Design System Nexo) ---

export const PencilEditIcon: React.FC<{ className?: string; size?: number; color?: string }> = ({
  className = 'w-3.5 h-3.5',
  size = 14,
  color = 'currentColor',
}) => (
  <svg
    width={size}
    height={size}
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
  </svg>
);

export const InfoCircleIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="16" x2="12" y2="12" />
    <line x1="12" y1="8" x2="12.01" y2="8" />
  </svg>
);

export const CogSettingsIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

export const AiChipIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg className={className} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Corpo central ampliado do microchip */}
    <rect x="16" y="16" width="32" height="32" rx="7" stroke="currentColor" strokeWidth="3.2" fill="none" />
    <text x="32" y="38" textAnchor="middle" fontFamily="system-ui, -apple-system, sans-serif" fontSize="18" fontWeight="900" fill="currentColor" letterSpacing="-0.5">AI</text>
    
    {/* Terminais Topo (2 terminais bem espaçados) */}
    <line x1="24" y1="16" x2="24" y2="8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    <circle cx="24" cy="4.8" r="3.4" stroke="currentColor" strokeWidth="2.8" fill="none" />
    <line x1="40" y1="16" x2="40" y2="8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    <circle cx="40" cy="4.8" r="3.4" stroke="currentColor" strokeWidth="2.8" fill="none" />

    {/* Terminais Base (2 terminais bem espaçados) */}
    <line x1="24" y1="48" x2="24" y2="56" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    <circle cx="24" cy="59.2" r="3.4" stroke="currentColor" strokeWidth="2.8" fill="none" />
    <line x1="40" y1="48" x2="40" y2="56" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    <circle cx="40" cy="59.2" r="3.4" stroke="currentColor" strokeWidth="2.8" fill="none" />

    {/* Terminais Esquerda (2 terminais bem espaçados) */}
    <line x1="16" y1="24" x2="8" y2="24" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    <circle cx="4.8" cy="24" r="3.4" stroke="currentColor" strokeWidth="2.8" fill="none" />
    <line x1="16" y1="40" x2="8" y2="40" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    <circle cx="4.8" cy="40" r="3.4" stroke="currentColor" strokeWidth="2.8" fill="none" />

    {/* Terminais Direita (2 terminais bem espaçados) */}
    <line x1="48" y1="24" x2="56" y2="24" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    <circle cx="59.2" cy="24" r="3.4" stroke="currentColor" strokeWidth="2.8" fill="none" />
    <line x1="48" y1="40" x2="56" y2="40" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    <circle cx="59.2" cy="40" r="3.4" stroke="currentColor" strokeWidth="2.8" fill="none" />
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


export const TrendingCostsIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
    <polyline points="17 6 23 6 23 12" />
  </svg>
);

export const RulerUnitsIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21.3 8.7 8.7 21.3c-1 1-2.5 1-3.4 0l-2.6-2.6c-1-1-1-2.5 0-3.4L15.3 2.7c1-1 2.5-1 3.4 0l2.6 2.6c1 1 1 2.5 0 3.4Z" />
    <path d="m14.5 3.5 2 2" />
    <path d="m11.5 6.5 3 3" />
    <path d="m8.5 9.5 2 2" />
    <path d="m5.5 12.5 3 3" />
  </svg>
);

export const ScalesUnitsIcon = RulerUnitsIcon;

export const DatabaseBiIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="9" ry="3" />
    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
  </svg>
);

export const BuildingCompanyIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="2" width="16" height="20" rx="2" ry="2" />
    <line x1="9" y1="22" x2="9" y2="18" />
    <line x1="15" y1="22" x2="15" y2="18" />
    <line x1="9" y1="6" x2="9" y2="6.01" />
    <line x1="15" y1="6" x2="15" y2="6.01" />
    <line x1="9" y1="10" x2="9" y2="10.01" />
    <line x1="15" y1="10" x2="15" y2="10.01" />
    <line x1="9" y1="14" x2="9" y2="14.01" />
    <line x1="15" y1="14" x2="15" y2="14.01" />
  </svg>
);

export const PaletteAppearanceIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="13.5" cy="6.5" r=".5" fill="currentColor" />
    <circle cx="17.5" cy="10.5" r=".5" fill="currentColor" />
    <circle cx="8.5" cy="7.5" r=".5" fill="currentColor" />
    <circle cx="6.5" cy="12.5" r=".5" fill="currentColor" />
    <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.03-.23-.29-.38-.64-.38-1.02 0-.83.67-1.5 1.5-1.5H16c3.31 0 6-2.69 6-6 0-5.5-4.5-9.95-10-9.95z" />
  </svg>
);

export const GlobeLanguageIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="2" y1="12" x2="22" y2="12" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </svg>
);

export const FlameIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" />
  </svg>
);

export const ZapEnergyIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

export const DropletWaterIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
  </svg>
);

export const CalculatorIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="2" width="16" height="20" rx="2" />
    <line x1="8" y1="6" x2="16" y2="6" />
    <line x1="16" y1="14" x2="16" y2="18" />
    <path d="M16 10h.01" />
    <path d="M12 10h.01" />
    <path d="M8 10h.01" />
    <path d="M12 14h.01" />
    <path d="M8 14h.01" />
    <path d="M12 18h.01" />
    <path d="M8 18h.01" />
  </svg>
);

interface SettingsTabSpec {
  key: SettingsCategoryKey;
  label: string;
  icon: React.ReactNode;
}

const SETTINGS_TABS: SettingsTabSpec[] = [
  { key: 'geral', label: 'Geral', icon: <CogSettingsIcon className="w-[19px] h-[19px] shrink-0" /> },
  { key: 'ia', label: 'Sincronismo de IA', icon: <AiChipIcon className="w-[22px] h-[22px] shrink-0" /> },
  { key: 'metricas', label: 'Métricas de Custo', icon: <TrendingCostsIcon className="w-[19px] h-[19px] shrink-0" /> },
  { key: 'unidades', label: 'Unidades de Medida', icon: <ScalesUnitsIcon className="w-[19px] h-[19px] shrink-0" /> },
  { key: 'banco', label: 'Banco de Dados & BI', icon: <DatabaseBiIcon className="w-[19px] h-[19px] shrink-0" /> },
];

export const SettingsPage: React.FC<SettingsPageProps> = ({
  onNotify,
  dark,
  onThemeToggle,
  onBrandUpdate,
}) => {
  const [activeTab, setActiveTab] = useState<SettingsCategoryKey>('geral');
  const [loading, setLoading] = useState(true);

  // --- Categoria 1: Geral & Identidade da Marca ---
  const [companyName, setCompanyName] = useState('Nexo');
  const [companyLogo, setCompanyLogo] = useState('');
  const [brandThemeEnabled, setBrandThemeEnabled] = useState(false);
  const [brandColor, setBrandColor] = useState('#F28C28');
  const [detectedColor, setDetectedColor] = useState('#F28C28');
  const [applyBrandToSidebar, setApplyBrandToSidebar] = useState(true);
  const [applyBrandToButtons, setApplyBrandToButtons] = useState(true);
  const [showCompanyName, setShowCompanyName] = useState(true);
  const [logoShape, setLogoShape] = useState<'round' | 'rect'>('round');
  const [themeMode, setThemeMode] = useState<'light' | 'dark' | 'system'>(dark ? 'dark' : 'light');
  const [language, setLanguage] = useState('Português (Brasil)');
  const [savingCompany, setSavingCompany] = useState(false);
  const [resettingBrand, setResettingBrand] = useState(false);

  // --- Categoria 2: IA ---
  const [aiEnabled, setAiEnabled] = useState(false);
  const [aiProvider, setAiProvider] = useState('Google Gemini');
  const [aiApiKey, setAiApiKey] = useState('');
  const [aiDailyLimit, setAiDailyLimit] = useState('50');
  const [showAiHelpModal, setShowAiHelpModal] = useState(false);
  const [savingAi, setSavingAi] = useState(false);

  // --- Categoria 3: Métricas de Custo & Jornada da Cozinha ---
  const [kitchenDaysMonth, setKitchenDaysMonth] = useState('26');
  const [kitchenHoursDay, setKitchenHoursDay] = useState('8');
  const [gasSupplyType, setGasSupplyType] = useState('cylinder_13');
  const [gasPriceInput, setGasPriceInput] = useState('125,00');
  const [elecBillInput, setElecBillInput] = useState('350,00');
  const [waterBillInput, setWaterBillInput] = useState('80,00');
  const [savingKitchen, setSavingKitchen] = useState(false);
  const [kitchenRates, setKitchenRates] = useState<any>(null);

  const [gasType, setGasType] = useState<'PERCENT' | 'FIXED'>('PERCENT');
  const [gasPct, setGasPct] = useState('20.0');
  const [gasFixed, setGasFixed] = useState('0.00');

  const [energyType, setEnergyType] = useState<'PERCENT' | 'FIXED'>('PERCENT');
  const [energyPct, setEnergyPct] = useState('20.0');
  const [energyFixed, setEnergyFixed] = useState('0.00');

  const [waterType, setWaterType] = useState<'PERCENT' | 'FIXED'>('PERCENT');
  const [waterPct, setWaterPct] = useState('20.0');
  const [waterFixed, setWaterFixed] = useState('0.00');
  const [savingCosts, setSavingCosts] = useState(false);

  // Modal Calculadora Auxiliar
  const [showCostCalcModal, setShowCostCalcModal] = useState(false);
  const [calcTarget, setCalcTarget] = useState<'gas' | 'energy' | 'water'>('gas');

  // Gás Calc state
  const [gasCalcType, setGasCalcType] = useState<'cylinder' | 'bill'>('cylinder');
  const [gasCylinderPrice, setGasCylinderPrice] = useState('120,00');
  const [gasCylinderUnits, setGasCylinderUnits] = useState('300');
  const [gasBillMonthly, setGasBillMonthly] = useState('280,00');
  const [gasBillUnits, setGasBillUnits] = useState('1000');
  const [gasAvgProdCost, setGasAvgProdCost] = useState('4,00');

  // Energia Calc state
  const [energyBillMonthly, setEnergyBillMonthly] = useState('450,00');
  const [energyDaysOpen, setEnergyDaysOpen] = useState('26');
  const [energyUnitsPerDay, setEnergyUnitsPerDay] = useState('50');
  const [energyAvgProdCost, setEnergyAvgProdCost] = useState('5,00');

  // Água Calc state
  const [waterBillMonthly, setWaterBillMonthly] = useState('130,00');
  const [waterDaysOpen, setWaterDaysOpen] = useState('26');
  const [waterUnitsPerDay, setWaterUnitsPerDay] = useState('50');
  const [waterAvgProdCost, setWaterAvgProdCost] = useState('5,00');

  // --- Categoria 4: Unidades de Medida ---
  const [massBaseUnit, setMassBaseUnit] = useState('mg');
  const [volumeBaseUnit, setVolumeBaseUnit] = useState('ml');
  const [countBaseUnit, setCountBaseUnit] = useState('un');
  const [savingUnits, setSavingUnits] = useState(false);

  // --- Gerenciador de Unidades Configuráveis por Insumo ---
  const [conversions, setConversions] = useState<any[]>([]);
  const [loadingConversions, setLoadingConversions] = useState(false);
  const [showCustomUnitsModal, setShowCustomUnitsModal] = useState(false);
  const [conversionSearch, setConversionSearch] = useState('');
  const [selectedConversionIds, setSelectedConversionIds] = useState<Set<number>>(new Set());
  const [isDeletingBatch, setIsDeletingBatch] = useState(false);

  // Ordenação e Visibilidade de Colunas da Tabela de Unidades (Padrão Nexo com Engrenagem e Setinha)
  const [convSortCol, setConvSortCol] = useState<'material_name' | 'unit' | 'unit_name' | 'equivalence' | 'brand' | 'category' | 'code'>('material_name');
  const [convSortDir, setConvSortDir] = useState<'ASC' | 'DESC'>('ASC');
  const [convHiddenCols, setConvHiddenCols] = useState<string[]>(['brand', 'category', 'code']);
  const [convColMenuOpen, setConvColMenuOpen] = useState(false);
  const convColMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (convColMenuRef.current && !convColMenuRef.current.contains(e.target as Node)) {
        setConvColMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, []);

  const toggleConvColumnVisibility = (key: string) => {
    setConvHiddenCols((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const handleConvSort = (colKey: 'material_name' | 'unit' | 'unit_name' | 'equivalence' | 'brand' | 'category' | 'code') => {
    if (convSortCol === colKey) {
      setConvSortDir((d) => (d === 'ASC' ? 'DESC' : 'ASC'));
    } else {
      setConvSortCol(colKey);
      setConvSortDir('ASC');
    }
  };

  // Sub-modal de Criação / Edição de Unidade
  const [showEditConvModal, setShowEditConvModal] = useState(false);
  const [editingConvId, setEditingConvId] = useState<number | null>(null);
  const [convMaterialId, setConvMaterialId] = useState<number | ''>('');
  const [convMaterialName, setConvMaterialName] = useState('');
  const [convUnitName, setConvUnitName] = useState('');
  const [convFactor, setConvFactor] = useState('');
  const [convBaseUnit, setConvBaseUnit] = useState('g');
  const [savingConv, setSavingConv] = useState(false);
  const [availableMaterials, setAvailableMaterials] = useState<any[]>([]);

  // --- Categoria 5: Banco de Dados & BI ---
  const [retentionMonths, setRetentionMonths] = useState('36');
  const [savingRetention, setSavingRetention] = useState(false);
  const [dbPath, setDbPath] = useState('');
  const [dbSize, setDbSize] = useState('0 KB');
  const [backingUp, setBackingUp] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [lastBackup, setLastBackup] = useState<{ name: string; time: string; size: string } | null>(null);

  // Carregar configurações do sistema
  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/settings');
      if (!res.ok) throw new Error('Não foi possível carregar as configurações.');
      const data = await res.json();

      setCompanyName(data.company_name || 'Nexo');
      setCompanyLogo(data.company_logo || '');
      setBrandThemeEnabled(!!data.brand_theme_enabled);
      if (data.brand_color) {
        setBrandColor(data.brand_color);
        setDetectedColor(data.brand_color);
      }
      setApplyBrandToSidebar(data.apply_brand_to_sidebar !== false);
      setApplyBrandToButtons(data.apply_brand_to_buttons !== false);
      setShowCompanyName(data.show_company_name !== false);
      setLogoShape(data.logo_shape === 'rect' ? 'rect' : 'round');
      setThemeMode(data.theme === 'dark' ? 'dark' : 'light');

      // Jornada da Cozinha
      if (data.kitchen) {
        setKitchenDaysMonth(String(data.kitchen.days_month || '26'));
        setKitchenHoursDay(String(data.kitchen.hours_day || '8'));
        setGasSupplyType(data.kitchen.gas_supply_type || 'cylinder_13');
        setGasPriceInput(parseFloat(data.kitchen.gas_price || 125).toFixed(2).replace('.', ','));
        setElecBillInput(parseFloat(data.kitchen.electricity_bill_monthly || 350).toFixed(2).replace('.', ','));
        setWaterBillInput(parseFloat(data.kitchen.water_bill_monthly || 80).toFixed(2).replace('.', ','));
        setKitchenRates(data.kitchen.rates);
      }

      // Custos operacionais
      if (data.cost_settings && Array.isArray(data.cost_settings)) {
        const g = data.cost_settings.find((c: any) => {
          const n = (c.name || '').toLowerCase();
          return n.includes('gás') || n.includes('gas');
        });
        const e = data.cost_settings.find((c: any) => {
          const n = (c.name || '').toLowerCase();
          return n.includes('energia') || n.includes('elétr') || n.includes('eletr');
        });
        const w = data.cost_settings.find((c: any) => {
          const n = (c.name || '').toLowerCase();
          return n.includes('água') || n.includes('agua');
        });
        if (g) {
          setGasType(g.cost_type === 'FIXED' ? 'FIXED' : 'PERCENT');
          setGasPct(String(g.percentage ?? '20.0'));
          setGasFixed(parseFloat(g.fixed_value ?? 0).toFixed(2).replace('.', ','));
        }
        if (e) {
          setEnergyType(e.cost_type === 'FIXED' ? 'FIXED' : 'PERCENT');
          setEnergyPct(String(e.percentage ?? '20.0'));
          setEnergyFixed(parseFloat(e.fixed_value ?? 0).toFixed(2).replace('.', ','));
        }
        if (w) {
          setWaterType(w.cost_type === 'FIXED' ? 'FIXED' : 'PERCENT');
          setWaterPct(String(w.percentage ?? '20.0'));
          setWaterFixed(parseFloat(w.fixed_value ?? 0).toFixed(2).replace('.', ','));
        }
      }

      // Banco de dados
      if (data.database) {
        setDbPath(data.database.path || 'nexo.db');
        setDbSize(data.database.size_fmt || '0 KB');
      }

      // Status geral / chaves adicionais
      const sRes = await fetch('/api/status');
      if (sRes.ok) {
        const sData = await sRes.json();
        if (sData.mass_base_unit) setMassBaseUnit(sData.mass_base_unit);
        if (sData.volume_base_unit) setVolumeBaseUnit(sData.volume_base_unit);
        if (sData.count_base_unit) setCountBaseUnit(sData.count_base_unit);
      }
    } catch (e: any) {
      console.error(e);
      onNotify('Erro ao carregar configurações do sistema.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchConversions();
    fetchMaterialsForConversions();
  }, []);

  useEffect(() => {
    if (activeTab === 'unidades') {
      fetchConversions();
      fetchMaterialsForConversions();
    }
  }, [activeTab]);

  // --- Handlers: Geral ---
  const handleSelectTheme = async (mode: 'light' | 'dark' | 'system') => {
    setThemeMode(mode);
    const targetDark = mode === 'dark';
    onThemeToggle(targetDark);
    try {
      await fetch('/api/settings/theme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: mode }),
      });
      onNotify(`Tema alterado para ${mode === 'dark' ? 'Modo Escuro' : 'Modo Claro'}.`, 'success');
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      onNotify('A imagem do logotipo deve ter no máximo 2 MB.', 'warning');
      return;
    }
    const reader = new FileReader();
    reader.onload = async () => {
      if (typeof reader.result === 'string') {
        const dataUrl = reader.result;
        setCompanyLogo(dataUrl);
        // Extrai cor proeminente da logo
        const color = await extractProminentColor(dataUrl);
        setDetectedColor(color);
        if (!brandThemeEnabled || brandColor === '#F28C28') {
          setBrandColor(color);
        }
        onNotify('Logo carregada e paleta de cores analisada com sucesso!', 'success');
      }
    };
    reader.readAsDataURL(file);
  };

  const handleSaveCompany = async () => {
    if (!companyName.trim()) {
      onNotify('O nome da empresa não pode ficar em branco.', 'warning');
      return;
    }
    setSavingCompany(true);
    try {
      const payload: CompanyBrandSettings = {
        company_name: companyName.trim(),
        company_logo: companyLogo,
        brand_theme_enabled: brandThemeEnabled,
        brand_color: brandColor,
        apply_brand_to_sidebar: applyBrandToSidebar,
        apply_brand_to_buttons: applyBrandToButtons,
        show_company_name: showCompanyName,
        logo_shape: logoShape,
      };

      const res = await fetch('/api/settings/company', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: payload.company_name,
          logo: payload.company_logo,
          brand_theme_enabled: payload.brand_theme_enabled,
          brand_color: payload.brand_color,
          apply_brand_to_sidebar: payload.apply_brand_to_sidebar,
          apply_brand_to_buttons: payload.apply_brand_to_buttons,
          show_company_name: payload.show_company_name,
          logo_shape: payload.logo_shape,
        }),
      });
      if (!res.ok) throw new Error('Falha ao salvar dados da empresa.');
      
      onBrandUpdate?.(payload);
      onNotify('Identidade visual da empresa salva com sucesso!', 'success');
    } catch (e: any) {
      onNotify(e.message || 'Erro ao salvar identidade da empresa.', 'error');
    } finally {
      setSavingCompany(false);
    }
  };

  const handleResetCompanyBrand = async () => {
    setResettingBrand(true);
    try {
      const res = await fetch('/api/settings/company/reset', { method: 'POST' });
      if (!res.ok) throw new Error('Falha ao restaurar padrão do Nexo.');
      const data = await res.json();

      setCompanyName('Nexo');
      setCompanyLogo('');
      setBrandThemeEnabled(false);
      setBrandColor('#F28C28');
      setDetectedColor('#F28C28');
      setApplyBrandToSidebar(true);
      setApplyBrandToButtons(true);
      setShowCompanyName(true);
      setLogoShape('round');

      const defaultBrand: CompanyBrandSettings = {
        company_name: 'Nexo',
        company_logo: '',
        brand_theme_enabled: false,
        brand_color: '#F28C28',
        apply_brand_to_sidebar: true,
        apply_brand_to_buttons: true,
        show_company_name: true,
        logo_shape: 'round',
      };
      onBrandUpdate?.(defaultBrand);

      onNotify(data.message || 'Padrão oficial Nexo restaurado com sucesso!', 'success');
    } catch (e: any) {
      onNotify(e.message || 'Erro ao restaurar padrão Nexo.', 'error');
    } finally {
      setResettingBrand(false);
    }
  };

  // --- Handlers: IA ---
  const handleSaveAi = async () => {
    setSavingAi(true);
    try {
      await fetch('/api/settings/ai_enabled', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: aiEnabled ? '1' : '0' }),
      });
      await fetch('/api/settings/ai_provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: aiProvider }),
      });
      await fetch('/api/settings/ai_api_key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: aiApiKey }),
      });
      await fetch('/api/settings/ai_daily_limit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: aiDailyLimit }),
      });
      onNotify('Configurações de IA salvas com sucesso!', 'success');
    } catch (e: any) {
      onNotify(e.message || 'Erro ao salvar configurações de IA.', 'error');
    } finally {
      setSavingAi(false);
    }
  };

  // --- Handlers: Jornada e Métricas de Custo ---
  const handleSaveKitchen = async () => {
    setSavingKitchen(true);
    try {
      const payload = {
        kitchen_days_month: kitchenDaysMonth,
        kitchen_hours_day: kitchenHoursDay,
        gas_supply_type: gasSupplyType,
        gas_price: gasPriceInput,
        electricity_bill_monthly: elecBillInput,
        water_bill_monthly: waterBillInput,
      };
      const res = await fetch('/api/settings/kitchen-costs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Falha ao salvar parâmetros da cozinha.');
      const d = await res.json();
      if (d.rates) setKitchenRates(d.rates);
      onNotify('Parâmetros da jornada da cozinha salvos com sucesso!', 'success');
      await fetchSettings();
    } catch (e: any) {
      onNotify(e.message || 'Erro ao salvar parâmetros da cozinha.', 'error');
    } finally {
      setSavingKitchen(false);
    }
  };

  const handleSaveCosts = async () => {
    setSavingCosts(true);
    try {
      const gVal = parseFloat(gasPct.replace(',', '.')) || 0;
      const gFixed = parseFloat(gasFixed.replace(',', '.')) || 0;
      const eVal = parseFloat(energyPct.replace(',', '.')) || 0;
      const eFixed = parseFloat(energyFixed.replace(',', '.')) || 0;
      const wVal = parseFloat(waterPct.replace(',', '.')) || 0;
      const wFixed = parseFloat(waterFixed.replace(',', '.')) || 0;

      const costsPayload = [
        { name: 'Gás', cost_type: gasType, percentage: gVal, fixed_value: gFixed },
        { name: 'Energia', cost_type: energyType, percentage: eVal, fixed_value: eFixed },
        { name: 'Água', cost_type: waterType, percentage: wVal, fixed_value: wFixed },
      ];

      const res = await fetch('/api/settings/operational-costs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ costs: costsPayload }),
      });
      if (!res.ok) throw new Error('Falha ao atualizar custos operacionais.');
      onNotify('Custos operacionais salvos com sucesso!', 'success');
      await fetchSettings();
    } catch (e: any) {
      onNotify(e.message || 'Erro ao salvar custos operacionais.', 'error');
    } finally {
      setSavingCosts(false);
    }
  };

  const handleApplyCalcResult = (target: 'gas' | 'energy' | 'water', asType: 'PERCENT' | 'FIXED', value: number) => {
    const formattedVal = asType === 'FIXED' ? value.toFixed(2).replace('.', ',') : value.toFixed(1).replace('.', ',');
    const targetLabel = target === 'gas' ? 'Gás' : target === 'energy' ? 'Energia' : 'Água';
    
    if (target === 'gas') {
      setGasType(asType);
      if (asType === 'FIXED') setGasFixed(formattedVal);
      else setGasPct(formattedVal);
    } else if (target === 'energy') {
      setEnergyType(asType);
      if (asType === 'FIXED') setEnergyFixed(formattedVal);
      else setEnergyPct(formattedVal);
    } else {
      setWaterType(asType);
      if (asType === 'FIXED') setWaterFixed(formattedVal);
      else setWaterPct(formattedVal);
    }

    setShowCostCalcModal(false);
    onNotify(`${asType === 'FIXED' ? `Valor fixo de R$ ${formattedVal}` : `Taxa de ${formattedVal}%`} definido para ${targetLabel}! Clique em 'Salvar custos' para gravar.`, 'success');
  };

  // --- Handlers: Unidades Configuráveis por Insumo ---
  const fetchConversions = async () => {
    try {
      setLoadingConversions(true);
      const res = await fetch('/api/conversions');
      if (res.ok) {
        const data = await res.json();
        setConversions(data.items || []);
      }
    } catch (e) {
      console.error('Erro ao carregar conversões:', e);
    } finally {
      setLoadingConversions(false);
    }
  };

  const fetchMaterialsForConversions = async () => {
    try {
      const res = await fetch('/api/materials?search=&status=Ativos');
      if (res.ok) {
        const data = await res.json();
        setAvailableMaterials(data.items || []);
      }
    } catch (e) {
      console.error('Erro ao carregar insumos:', e);
    }
  };

  const handleDeleteConversion = async (id: number) => {
    if (!window.confirm('Deseja realmente excluir esta unidade configurável?')) return;
    try {
      const res = await fetch(`/api/conversions/${id}`, { method: 'DELETE' });
      if (res.ok) {
        onNotify('Unidade excluída com sucesso!', 'success');
        fetchConversions();
        setSelectedConversionIds(prev => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });
      } else {
        const err = await res.json();
        onNotify(err.detail || 'Erro ao excluir unidade.', 'error');
      }
    } catch (e) {
      onNotify('Erro de conexão ao excluir unidade.', 'error');
    }
  };

  const handleBatchDeleteConversions = async () => {
    if (selectedConversionIds.size === 0) return;
    if (!window.confirm(`Deseja realmente excluir as ${selectedConversionIds.size} unidades selecionadas?`)) return;
    try {
      setIsDeletingBatch(true);
      const res = await fetch('/api/conversions/batch-delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: Array.from(selectedConversionIds) }),
      });
      if (res.ok) {
        const data = await res.json();
        onNotify(`${data.deleted_count || selectedConversionIds.size} unidades excluídas com sucesso!`, 'success');
        setSelectedConversionIds(new Set());
        fetchConversions();
      } else {
        const err = await res.json();
        onNotify(err.detail || 'Erro na exclusão em massa.', 'error');
      }
    } catch (e) {
      onNotify('Erro de conexão ao excluir em massa.', 'error');
    } finally {
      setIsDeletingBatch(false);
    }
  };

  const handleOpenNewConversion = () => {
    setEditingConvId(null);
    const firstMat = availableMaterials.length > 0 ? availableMaterials[0] : null;
    setConvMaterialId(firstMat ? firstMat.id : '');
    setConvMaterialName(firstMat ? firstMat.name : '');
    setConvUnitName('');
    setConvFactor('');
    setConvBaseUnit(firstMat ? firstMat.purchase_unit || 'g' : 'g');
    setShowEditConvModal(true);
  };

  const handleOpenEditConversion = (item: any) => {
    setEditingConvId(item.id);
    setConvMaterialId(item.material_id);
    setConvMaterialName(item.material_name);
    setConvUnitName(item.unit_name);
    setConvFactor(String(item.factor_to_base));
    setConvBaseUnit(item.base_unit);
    setShowEditConvModal(true);
  };

  const handleSaveConversionForm = async () => {
    if (!editingConvId && !convMaterialId) {
      onNotify('Selecione um insumo para a conversão.', 'error');
      return;
    }
    if (!convUnitName.trim()) {
      onNotify('Informe o nome da unidade (ex: Xícara, Colher...).', 'error');
      return;
    }
    const factorNum = parseFloat(convFactor.replace(',', '.'));
    if (isNaN(factorNum) || factorNum <= 0) {
      onNotify('Informe uma quantidade equivalente válida e maior que zero.', 'error');
      return;
    }

    try {
      setSavingConv(true);
      if (editingConvId) {
        const res = await fetch(`/api/conversions/${editingConvId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: convUnitName.trim(),
            base_unit: convBaseUnit,
            factor_to_base: factorNum,
          }),
        });
        if (res.ok) {
          onNotify('Unidade configurável atualizada com sucesso!', 'success');
          setShowEditConvModal(false);
          fetchConversions();
        } else {
          const err = await res.json();
          onNotify(err.detail || 'Erro ao atualizar unidade.', 'error');
        }
      } else {
        const res = await fetch('/api/conversions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            material_id: convMaterialId,
            name: convUnitName.trim(),
            base_unit: convBaseUnit,
            factor_to_base: factorNum,
          }),
        });
        if (res.ok) {
          onNotify('Nova unidade configurável adicionada!', 'success');
          setShowEditConvModal(false);
          fetchConversions();
        } else {
          const err = await res.json();
          onNotify(err.detail || 'Erro ao salvar unidade.', 'error');
        }
      }
    } catch (e) {
      onNotify('Erro de conexão ao salvar unidade.', 'error');
    } finally {
      setSavingConv(false);
    }
  };

  // --- Handlers: Unidades ---
  const handleSaveUnits = async () => {
    setSavingUnits(true);
    try {
      await fetch('/api/settings/mass_base_unit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: massBaseUnit }),
      });
      await fetch('/api/settings/volume_base_unit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: volumeBaseUnit }),
      });
      await fetch('/api/settings/count_base_unit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: countBaseUnit }),
      });
      onNotify('Unidades internas salvas com sucesso!', 'success');
    } catch (e: any) {
      onNotify(e.message || 'Erro ao salvar unidades internas.', 'error');
    } finally {
      setSavingUnits(false);
    }
  };

  // --- Handlers: Banco & Retenção ---
  const handleSaveRetention = async () => {
    setSavingRetention(true);
    try {
      const v = parseInt(retentionMonths.trim(), 10);
      if (isNaN(v) || v < 0) {
        onNotify('Digite um número de meses válido (0 para nunca limpar).', 'warning');
        return;
      }
      await fetch('/api/settings/history_retention_months', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: String(v) }),
      });
      onNotify(`Retenção de histórico definida para ${v} meses.`, 'success');
    } catch (e: any) {
      onNotify(e.message || 'Erro ao salvar retenção de histórico.', 'error');
    } finally {
      setSavingRetention(false);
    }
  };

  const handleBackup = async () => {
    setBackingUp(true);
    try {
      const res = await fetch('/api/settings/database/backup', { method: 'POST' });
      if (!res.ok) throw new Error('Não foi possível gerar a cópia de segurança.');
      const data = await res.json();
      setLastBackup({
        name: data.backup_name,
        time: data.created_at,
        size: data.size_fmt,
      });
      onNotify(`Backup gerado com sucesso: ${data.backup_name}`, 'success');
    } catch (e: any) {
      onNotify(e.message || 'Erro ao realizar backup do banco.', 'error');
    } finally {
      setBackingUp(false);
    }
  };

  const handleVacuum = async () => {
    setOptimizing(true);
    try {
      const res = await fetch('/api/settings/database/vacuum', { method: 'POST' });
      if (!res.ok) throw new Error('Não foi possível otimizar o banco.');
      onNotify('Banco de dados otimizado com sucesso!', 'success');
      await fetchSettings();
    } catch (e: any) {
      onNotify(e.message || 'Erro ao otimizar banco de dados.', 'error');
    } finally {
      setOptimizing(false);
    }
  };

  const totalOperationalPct = (
    (gasType === 'PERCENT' ? (parseFloat(gasPct.replace(',', '.')) || 0) : 0) +
    (energyType === 'PERCENT' ? (parseFloat(energyPct.replace(',', '.')) || 0) : 0) +
    (waterType === 'PERCENT' ? (parseFloat(waterPct.replace(',', '.')) || 0) : 0)
  ).toFixed(1);

  const totalOperationalFixed = (
    (gasType === 'FIXED' ? (parseFloat(gasFixed.replace(',', '.')) || 0) : 0) +
    (energyType === 'FIXED' ? (parseFloat(energyFixed.replace(',', '.')) || 0) : 0) +
    (waterType === 'FIXED' ? (parseFloat(waterFixed.replace(',', '.')) || 0) : 0)
  ).toFixed(2);

  if (loading) {
    return (
      <div className="flex-1 w-full rounded-[22px] bg-white dark:bg-[#111F3B] p-8 flex items-center justify-center text-[#687796] dark:text-[#93A4C6] text-[13px]">
        Carregando configurações...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full min-h-0">


      {/* 2. Layout Principal: Menu Lateral (Inner Sidebar) + Conteúdo */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Menu Lateral de Configurações (220px) */}
        <div className="w-[220px] shrink-0 rounded-[22px] bg-white dark:bg-[#111F3B] p-3 shadow-sm flex flex-col gap-1.5 transition-colors">
          <div className="px-3 py-2 text-[10.5px] font-bold uppercase tracking-wider text-[#A0ABB9]">
            Categorias
          </div>
          {SETTINGS_TABS.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`w-full h-[42px] px-3.5 rounded-[16px] flex items-center gap-2.5 text-[13px] font-medium transition-all cursor-pointer text-left ${
                  isActive
                    ? 'bg-[#EFF4FB] dark:bg-[#1D3557] text-[#BA5200] dark:text-[#F28C28] font-bold shadow-sm'
                    : 'text-[#687796] dark:text-[#AFC0E2] hover:bg-[#F4F7FC] dark:hover:bg-[#162846] hover:text-[#18223A] dark:hover:text-[#F4F7FF]'
                }`}
              >
                <span className="flex items-center justify-center">{tab.icon}</span>
                <span className="truncate">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Área de Conteúdo da Categoria Selecionada */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-4">
          {/* ========================================================= */}
          {/* ABA 1: GERAL (Empresa, Aparência, Idioma) */}
          {/* ========================================================= */}
          {activeTab === 'geral' && (
            <>
              {/* Painel: Empresa e Identidade da Marca */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-4 transition-colors">
                <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                  <div className="flex items-center gap-2">
                    <BuildingCompanyIcon className="w-5 h-5 text-[#BA5200] dark:text-[#F28C28] shrink-0" />
                    <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                      Empresa & Identidade Visual
                    </h3>
                  </div>
                  {/* Status Indicator */}
                  {brandThemeEnabled ? (
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-[#EBF7EE] text-[#16A34A] dark:bg-[#143320] dark:text-[#4ADE80]">
                      Personalização Ativa
                    </span>
                  ) : (
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-[#EFF4FB] text-[#60769D] dark:bg-[#1C2C4E] dark:text-[#93A4C6]">
                      Modo Padrão Nexo
                    </span>
                  )}
                </div>

                {/* Linha 1: Dados Básicos (Nome e Logo com controles de exibição) */}
                <div className="grid grid-cols-12 gap-4 items-start">
                  {/* Campo Nome */}
                  <div className="col-span-6 space-y-2">
                    <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] pl-1">
                      Nome da empresa / restaurante
                    </label>
                    <CapsuleInput
                      value={companyName}
                      onChange={setCompanyName}
                      placeholder="Ex: Minha Confeitaria"
                    />
                    <label className="flex items-center gap-2 pl-1 cursor-pointer select-none">
                      <NexoCheckbox
                        checked={showCompanyName}
                        onChange={() => setShowCompanyName(!showCompanyName)}
                      />
                      <span className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
                        Exibir nome no topo da barra lateral (desmarque se sua logo já tem o nome)
                      </span>
                    </label>
                  </div>

                  {/* Campo Logo e Formato */}
                  <div className="col-span-6 space-y-2">
                    <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] pl-1">
                      Logotipo oficial
                    </label>
                    <div className="flex items-center gap-3">
                      <div className={`w-12 h-12 bg-[#F4F7FC] dark:bg-[#142340] border border-[#DDE5F2] dark:border-[#24385E] flex items-center justify-center overflow-hidden shrink-0 shadow-sm p-1 ${
                        logoShape === 'round' ? 'rounded-full' : 'rounded-[14px]'
                      }`}>
                        {companyLogo ? (
                          <img
                            src={companyLogo}
                            alt="Logo"
                            className={`w-full h-full object-contain ${
                              logoShape === 'round' ? 'rounded-full' : 'rounded-[10px]'
                            }`}
                          />
                        ) : (
                          <span className="text-[10px] text-[#8C9BB5] text-center px-0.5 font-medium">Sem logo</span>
                        )}
                      </div>

                      <label className="inline-flex items-center justify-center px-3.5 h-[36px] rounded-full text-[12px] font-semibold bg-[#EEF4FB] dark:bg-[#1C2C4E] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#E2EAF5] dark:hover:bg-[#253963] cursor-pointer transition-colors shadow-sm">
                        <span>Selecionar logo</span>
                        <input
                          type="file"
                          accept="image/png,image/jpeg,image/webp"
                          onChange={handleLogoUpload}
                          className="hidden"
                        />
                      </label>

                      {companyLogo && (
                        <button
                          type="button"
                          onClick={() => setCompanyLogo('')}
                          className="text-[12px] font-medium text-[#DC2626] dark:text-[#F87171] hover:underline cursor-pointer"
                        >
                          Remover
                        </button>
                      )}
                    </div>

                    {/* Seletor de Formato da Logo: Redonda vs Livre/Retangular */}
                    <div className="flex items-center gap-2 pl-1 pt-0.5">
                      <span className="text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6]">
                        Formato:
                      </span>
                      <button
                        type="button"
                        onClick={() => setLogoShape('round')}
                        className={`h-[28px] px-3 rounded-full text-[11.5px] font-bold border transition-all cursor-pointer ${
                          logoShape === 'round'
                            ? 'bg-[#FFF8EE] dark:bg-[#1C2C4E] border-[#F28C28] text-[#F28C28]'
                            : 'bg-white dark:bg-[#111F3B] border-[#DDE5F2] dark:border-[#24385E] text-[#60769D] dark:text-[#93A4C6]'
                        }`}
                      >
                        ⭕ Redonda / Circular
                      </button>
                      <button
                        type="button"
                        onClick={() => setLogoShape('rect')}
                        className={`h-[28px] px-3 rounded-full text-[11.5px] font-bold border transition-all cursor-pointer ${
                          logoShape === 'rect'
                            ? 'bg-[#FFF8EE] dark:bg-[#1C2C4E] border-[#F28C28] text-[#F28C28]'
                            : 'bg-white dark:bg-[#111F3B] border-[#DDE5F2] dark:border-[#24385E] text-[#60769D] dark:text-[#93A4C6]'
                        }`}
                      >
                        ⬜ Livre / Retangular
                      </button>
                    </div>
                  </div>
                </div>

                {/* Linha 2: Configurações de Personalização Dinâmica */}
                <div className="p-4 rounded-[18px] bg-[#F8FAFD] dark:bg-[#0D182E] border border-[#E2EAF5] dark:border-[#203357] space-y-3.5">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                        Cores da Marca no Sistema
                      </h4>
                      <p className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
                        Adequa automaticamente o Nexo à paleta visual da sua empresa
                      </p>
                    </div>

                    {/* Master Switch */}
                    <div className="flex items-center gap-2">
                      <NexoCheckbox
                        checked={brandThemeEnabled}
                        onChange={() => setBrandThemeEnabled(!brandThemeEnabled)}
                        title="Ativar ou desativar personalização com cores da marca"
                      />
                      <span className="text-[12px] font-semibold text-[#18223A] dark:text-[#F4F7FF]">
                        Ativar identidade da marca
                      </span>
                    </div>
                  </div>

                  {brandThemeEnabled && (
                    <div className="pt-3 border-t border-[#E2EAF5] dark:border-[#203357] space-y-3">
                      {/* Seletor de Cor da Marca */}
                      <div className="flex flex-wrap items-center gap-3">
                        <span className="text-[12px] font-medium text-[#60769D] dark:text-[#93A4C6]">
                          Cor principal da marca:
                        </span>
                        
                        <div className="flex items-center gap-2 bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] px-2.5 py-1 rounded-full shadow-sm">
                          <input
                            type="color"
                            value={brandColor}
                            onChange={(e) => setBrandColor(e.target.value)}
                            className="w-5 h-5 rounded-full border-0 cursor-pointer p-0 bg-transparent"
                            title="Escolher cor personalizada"
                          />
                          <span className="text-[12px] font-mono font-bold text-[#18223A] dark:text-[#F4F7FF]">
                            {brandColor.toUpperCase()}
                          </span>
                        </div>

                        {detectedColor && (
                          <button
                            type="button"
                            onClick={() => setBrandColor(detectedColor)}
                            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11.5px] font-semibold bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#EEF4FB] dark:hover:bg-[#1C2C4E] transition-colors cursor-pointer"
                          >
                            <span
                              className="w-3 h-3 rounded-full shrink-0 border border-black/10"
                              style={{ backgroundColor: detectedColor }}
                            />
                            <span>Usar cor detectada da logo ({detectedColor.toUpperCase()})</span>
                          </button>
                        )}
                      </div>

                      {/* Checkboxes de Controle Granular */}
                      <div className="grid grid-cols-2 gap-3 pt-1">
                        <label className="flex items-center gap-2 cursor-pointer select-none">
                          <NexoCheckbox
                            checked={applyBrandToSidebar}
                            onChange={() => setApplyBrandToSidebar(!applyBrandToSidebar)}
                          />
                          <span className="text-[12px] text-[#18223A] dark:text-[#F4F7FF]">
                            Aplicar cores na <b>Barra Lateral (Sidebar)</b>
                          </span>
                        </label>

                        <label className="flex items-center gap-2 cursor-pointer select-none">
                          <NexoCheckbox
                            checked={applyBrandToButtons}
                            onChange={() => setApplyBrandToButtons(!applyBrandToButtons)}
                          />
                          <span className="text-[12px] text-[#18223A] dark:text-[#F4F7FF]">
                            Aplicar cores nos <b>Botões e Destaques</b>
                          </span>
                        </label>
                      </div>
                    </div>
                  )}
                </div>

                {/* Linha de Ações: Restaurar Padrão Nexo + Salvar */}
                <div className="flex items-center justify-between pt-1">
                  <button
                    type="button"
                    onClick={handleResetCompanyBrand}
                    disabled={resettingBrand}
                    className="inline-flex items-center gap-1.5 px-3.5 h-[36px] rounded-full text-[12px] font-bold text-[#687796] dark:text-[#93A4C6] bg-[#F4F7FC] dark:bg-[#142340] border border-[#DDE5F2] dark:border-[#24385E] hover:text-[#BA5200] hover:border-[#F28C28] dark:hover:text-[#F28C28] transition-colors cursor-pointer"
                    title="Desativa qualquer personalização e restaura o Laranja e Logo clássicos do Nexo"
                  >
                    <span>↺ Restaurar Padrão Nexo</span>
                  </button>

                  <RoundedActionButton
                    label={savingCompany ? 'Salvando...' : 'Salvar identidade'}
                    onClick={handleSaveCompany}
                    variant="primary"
                    height={36}
                  />
                </div>

                <p className="text-[11.5px] text-[#8C9BB5] dark:text-[#64748B]">
                  Formatos aceitos para a logo: PNG, JPG/JPEG, WebP. O ícone e nome do Nexo no Windows permanecem inalterados.
                </p>
              </div>

              {/* Painel: Aparência */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-3.5 transition-colors">
                <div className="flex items-center gap-2 border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                  <PaletteAppearanceIcon className="w-5 h-5 text-[#BA5200] dark:text-[#F28C28] shrink-0" />
                  <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Aparência
                  </h3>
                </div>

                <div className="flex items-center gap-4">
                  <span className="text-[12.5px] font-semibold text-[#18223A] dark:text-[#F4F7FF]">
                    Tema:
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleSelectTheme('light')}
                      className={`h-[34px] px-4 rounded-full text-[12.5px] font-semibold border transition-all cursor-pointer ${
                        themeMode === 'light'
                          ? 'bg-[#FFF8EE] border-[#F28C28] text-[#F28C28]'
                          : 'bg-[#F9FBFC] dark:bg-[#142340] border-[#E2EAF5] dark:border-[#24385E] text-[#687796] dark:text-[#AFC0E2]'
                      }`}
                    >
                      ☀️ Claro
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSelectTheme('dark')}
                      className={`h-[34px] px-4 rounded-full text-[12.5px] font-semibold border transition-all cursor-pointer ${
                        themeMode === 'dark'
                          ? 'bg-[#1C2C4E] border-[#F28C28] text-[#F28C28]'
                          : 'bg-[#F9FBFC] dark:bg-[#142340] border-[#E2EAF5] dark:border-[#24385E] text-[#687796] dark:text-[#AFC0E2]'
                      }`}
                    >
                      🌙 Escuro
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSelectTheme('system')}
                      className={`h-[34px] px-4 rounded-full text-[12.5px] font-semibold border transition-all cursor-pointer ${
                        themeMode === 'system'
                          ? 'bg-[#FFF8EE] border-[#F28C28] text-[#F28C28]'
                          : 'bg-[#F9FBFC] dark:bg-[#142340] border-[#E2EAF5] dark:border-[#24385E] text-[#687796] dark:text-[#AFC0E2]'
                      }`}
                    >
                      💻 Sistema
                    </button>
                  </div>
                </div>
              </div>

              {/* Painel: Idioma */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-3 transition-colors">
                <div className="flex items-center gap-2 border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                  <GlobeLanguageIcon className="w-5 h-5 text-[#BA5200] dark:text-[#F28C28] shrink-0" />
                  <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Idioma
                  </h3>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-[12.5px] font-semibold text-[#18223A] dark:text-[#F4F7FF]">
                    Idioma do Nexo:
                  </span>
                  <div className="w-[200px]">
                    <RoundedDropdown
                      value={language}
                      onChange={setLanguage}
                      options={['Português (Brasil)']}
                      width={200}
                      height={34}
                    />
                  </div>
                  <span className="text-[11.5px] text-[#8C9BB5] dark:text-[#64748B]">
                    Outros idiomas serão adicionados na camada de tradução sem alterar os dados.
                  </span>
                </div>
              </div>
            </>
          )}

          {/* ========================================================= */}
          {/* ABA 2: INTELIGÊNCIA ARTIFICIAL */}
          {/* ========================================================= */}
          {activeTab === 'ia' && (
            <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-4 transition-colors">
              {/* Topo: Título à esquerda e Chavinha Redondinha com Tooltip à direita */}
              <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                <div className="flex items-center gap-2.5">
                  <AiChipIcon className="w-6 h-6 text-[#BA5200] dark:text-[#F28C28]" />
                  <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Sincronismo de IA
                  </h3>
                </div>

                <NexoToggleSwitch
                  checked={aiEnabled}
                  onChange={setAiEnabled}
                  tooltip={aiEnabled ? 'IA ativada (Clique para desativar)' : 'Clique para ativar a IA'}
                />
              </div>

              {/* Linha 1: Provedor de IA */}
              <div className="flex items-center gap-3">
                <span className="text-[12px] font-semibold text-[#60769D] dark:text-[#93A4C6]">
                  Provedor de IA:
                </span>
                <div className="w-[200px]">
                  <RoundedDropdown
                    value={aiProvider}
                    onChange={setAiProvider}
                    options={['Google Gemini', 'OpenAI ChatGPT']}
                    width={200}
                    height={34}
                    disabled={!aiEnabled}
                  />
                </div>
              </div>

              {/* Linha 2: Chave API */}
              <div className="flex items-center gap-2.5">
                <div className="flex-1">
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                    Chave API (Secreta):
                  </label>
                  <CapsuleInput
                    type="password"
                    value={aiApiKey}
                    onChange={setAiApiKey}
                    placeholder="Cole sua chave de API aqui..."
                    disabled={!aiEnabled}
                  />
                </div>
                <div className="pt-5 relative group flex items-center">
                  <button
                    type="button"
                    onClick={() => setShowAiHelpModal(true)}
                    className="p-1 rounded-full text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer focus:outline-none"
                    title="Como obter sua chave de API"
                  >
                    <InfoCircleIcon className="w-[22px] h-[22px]" />
                  </button>
                  {/* Tooltip cápsula oficial no hover */}
                  <div className="absolute right-0 top-[38px] h-[32px] px-4 rounded-full bg-[#101A33] dark:bg-[#2A3B5C] text-white font-bold text-[12px] flex items-center justify-center whitespace-nowrap shadow-lg z-50 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-150">
                    Como obter sua chave de API
                  </div>
                </div>
              </div>

              {/* Linha 3: Limite Diário */}
              <div className="flex items-center gap-3">
                <span className="text-[12.5px] text-[#18223A] dark:text-[#F4F7FF]">
                  Alerta de Segurança Diário (Limitar em):
                </span>
                <div className="w-[80px]">
                  <CapsuleInput
                    value={aiDailyLimit}
                    onChange={(v) => setAiDailyLimit(v.replace(/[^0-9]/g, ''))}
                    placeholder="50"
                    disabled={!aiEnabled}
                  />
                </div>
                <span className="text-[12.5px] text-[#60769D] dark:text-[#93A4C6]">
                  leituras por dia.
                </span>
              </div>

              <div className="pt-2 flex justify-end">
                <RoundedActionButton
                  label={savingAi ? 'Salvando...' : 'Salvar IA'}
                  onClick={handleSaveAi}
                  variant="primary"
                  height={34}
                />
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* ABA 3: MÉTRICAS DE CUSTO */}
          {/* ========================================================= */}
          {activeTab === 'metricas' && (
            <div className="space-y-4">
              {/* CARD 1: JORNADA DE TRABALHO E CUSTOS REAIS DA COZINHA */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-4 transition-colors">
                <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-3">
                  <div className="flex items-center gap-2">
                    <WorkShiftClockIcon className="w-[26px] h-[26px] text-[#BA5200] dark:text-[#F28C28] shrink-0" />
                    <div>
                      <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                        Jornada & Custos Reais da Cozinha
                      </h3>
                      <p className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
                        Informe a rotina de produção da sua doceria e o valor das suas faturas. O Nexo calcula o custo real de cada hora ativa.
                      </p>
                    </div>
                  </div>

                  <RoundedActionButton
                    label={savingKitchen ? 'Salvando...' : 'Salvar Jornada'}
                    onClick={handleSaveKitchen}
                    variant="primary"
                    height={34}
                  />
                </div>

                {/* Grid de Jornada e Faturas */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3.5">
                  {/* Dias no Mês */}
                  <div className="rounded-[16px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] p-3 space-y-1.5">
                    <label className="block text-[11px] font-bold text-[#60769D] dark:text-[#93A4C6]">
                      Dias de produção / mês
                    </label>
                    <div className="relative flex items-center">
                      <input
                        type="text"
                        value={kitchenDaysMonth}
                        onChange={(e) => setKitchenDaysMonth(e.target.value.replace(/[^0-9]/g, ''))}
                        placeholder="26"
                        className="w-full h-[34px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                      <span className="absolute right-3.5 text-[11px] font-bold text-[#8C9BB5]">dias</span>
                    </div>
                    <span className="text-[10px] text-[#8C9BB5] block">Padrão docerias: 24 a 26 dias</span>
                  </div>

                  {/* Horas por Dia */}
                  <div className="rounded-[16px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] p-3 space-y-1.5">
                    <label className="block text-[11px] font-bold text-[#60769D] dark:text-[#93A4C6]">
                      Horas ativas por dia
                    </label>
                    <div className="relative flex items-center">
                      <input
                        type="text"
                        value={kitchenHoursDay}
                        onChange={(e) => setKitchenHoursDay(e.target.value.replace(/[^0-9]/g, ''))}
                        placeholder="8"
                        className="w-full h-[34px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                      <span className="absolute right-3.5 text-[11px] font-bold text-[#8C9BB5]">horas/dia</span>
                    </div>
                    <span className="text-[10px] text-[#8C9BB5] block">Tempo de forno e produção ativa</span>
                  </div>

                  {/* Conta de Luz Mês */}
                  <div className="rounded-[16px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] p-3 space-y-1.5">
                    <label className="block text-[11px] font-bold text-[#60769D] dark:text-[#93A4C6]">
                      Conta de Luz média (R$/mês)
                    </label>
                    <div className="relative flex items-center">
                      <span className="absolute left-3 text-[11px] font-bold text-[#8C9BB5]">R$</span>
                      <input
                        type="text"
                        value={elecBillInput}
                        onChange={(e) => setElecBillInput(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="350,00"
                        className="w-full h-[34px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] pl-8 pr-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                    </div>
                    <span className="text-[10px] text-[#8C9BB5] block">Valor total da última fatura</span>
                  </div>

                  {/* Conta de Água Mês */}
                  <div className="rounded-[16px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] p-3 space-y-1.5">
                    <label className="block text-[11px] font-bold text-[#60769D] dark:text-[#93A4C6]">
                      Conta de Água média (R$/mês)
                    </label>
                    <div className="relative flex items-center">
                      <span className="absolute left-3 text-[11px] font-bold text-[#8C9BB5]">R$</span>
                      <input
                        type="text"
                        value={waterBillInput}
                        onChange={(e) => setWaterBillInput(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="80,00"
                        className="w-full h-[34px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] pl-8 pr-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                    </div>
                    <span className="text-[10px] text-[#8C9BB5] block">Valor da fatura de água</span>
                  </div>
                </div>

                {/* Fornecimento e Preço do Gás */}
                <div className="rounded-[18px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] p-4 flex flex-col md:flex-row items-center justify-between gap-4">
                  <div className="flex flex-col md:flex-row items-start md:items-center gap-3">
                    <div className="flex items-center gap-2">
                      <FlameIcon className="w-4 h-4 text-[#60769D] dark:text-[#AFC0E2]" />
                      <span className="text-[12.5px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                        Tipo de Gás:
                      </span>
                    </div>

                    <div className="flex bg-[#EAF0F9] dark:bg-[#0D182E] p-0.5 rounded-full">
                      <button
                        type="button"
                        onClick={() => setGasSupplyType('cylinder_13')}
                        className={`px-3 py-1 text-[11px] font-bold rounded-full transition-all cursor-pointer ${
                          gasSupplyType === 'cylinder_13'
                            ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                            : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E293B]'
                        }`}
                      >
                        Botijão Comum (13kg)
                      </button>
                      <button
                        type="button"
                        onClick={() => setGasSupplyType('cylinder_45')}
                        className={`px-3 py-1 text-[11px] font-bold rounded-full transition-all cursor-pointer ${
                          gasSupplyType === 'cylinder_45'
                            ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                            : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E293B]'
                        }`}
                      >
                        Botijão Grande (45kg)
                      </button>
                      <button
                        type="button"
                        onClick={() => setGasSupplyType('piped')}
                        className={`px-3 py-1 text-[11px] font-bold rounded-full transition-all cursor-pointer ${
                          gasSupplyType === 'piped'
                            ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                            : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E293B]'
                        }`}
                      >
                        Gás Encanado / Fatura
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <label className="text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6]">
                      {gasSupplyType === 'piped' ? 'Valor da fatura de gás (R$):' : 'Preço pago no botijão (R$):'}
                    </label>
                    <div className="relative flex items-center">
                      <span className="absolute left-3 text-[11px] font-bold text-[#8C9BB5]">R$</span>
                      <input
                        type="text"
                        value={gasPriceInput}
                        onChange={(e) => setGasPriceInput(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="125,00"
                        className="w-28 h-[34px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] pl-8 pr-3 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                    </div>
                  </div>
                </div>

                {/* Banner Resumo de Custo Horário da Cozinha */}
                {(() => {
                  const d = parseFloat(kitchenDaysMonth) || 26;
                  const h = parseFloat(kitchenHoursDay) || 8;
                  const totalH = d * h;
                  const gPrice = parseFloat(gasPriceInput.replace(',', '.')) || 125;
                  const ePrice = parseFloat(elecBillInput.replace(',', '.')) || 350;
                  const wPrice = parseFloat(waterBillInput.replace(',', '.')) || 80;
                  const indirectHour = totalH > 0 ? (ePrice + wPrice) / totalH : 0;
                  const kgPrice = gasSupplyType === 'cylinder_45' ? (gPrice / 45) : (gPrice / 13);
                  const gasHourOven = kgPrice * 0.300;

                  return (
                    <div className="p-3.5 rounded-[18px] bg-[#FFF8EE] dark:bg-[#1E1912] border border-[#F28C28]/35 flex flex-col md:flex-row items-center justify-between gap-3 text-[12px]">
                      <div className="flex items-center gap-2.5">
                        <div className="space-y-0.5">
                          <span className="font-bold text-[#18223A] dark:text-[#F4F7FF]">
                            Sua cozinha funciona ~{totalH.toFixed(0)} horas por mês.
                          </span>
                          <span className="text-[#60769D] dark:text-[#93A4C6] block text-[11px]">
                            Custo indireto de espaço (luz + água): <strong>R$ {indirectHour.toFixed(2).replace('.', ',')} / hora</strong> • Forno a gás ligado: <strong>R$ {gasHourOven.toFixed(2).replace('.', ',')} / hora</strong>.
                          </span>
                        </div>
                      </div>
                      <span className="px-3 py-1 rounded-full bg-[#F28C28] text-white font-extrabold text-[11.5px] shadow-xs shrink-0">
                        Total Cozinha Ativa: R$ {(indirectHour + gasHourOven).toFixed(2).replace('.', ',')} / h
                      </span>
                    </div>
                  );
                })()}
              </div>

              {/* CARD 2: CUSTOS OPERACIONAIS GLOBAIS (FALLBACK / PRODUTOS SIMPLES) */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-4 transition-colors">
                <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-3">
                  <div className="flex items-center gap-2">
                    <KitchenUtilitiesCostIcon className="w-[26px] h-[26px] text-[#BA5200] dark:text-[#F28C28] shrink-0" />
                    <div>
                      <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                        Custos Indiretos Adicionais da Cozinha (Opcional)
                      </h3>
                      <p className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
                        Taxas ou valores fixos adicionais para cobrir custos indiretos de operação, higienização e manutenção da cozinha.
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      setCalcTarget('gas');
                      setShowCostCalcModal(true);
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#F4F7FD] dark:bg-[#182848] text-[#1E293B] dark:text-[#E2E8F0] hover:bg-[#EAEFF8] dark:hover:bg-[#21355E] text-[12px] font-bold transition-all border border-[#D5E1F2] dark:border-[#2B406B] shadow-xs cursor-pointer"
                  >
                    <CalculatorIcon className="w-3.5 h-3.5 text-[#F28C28]" />
                    <span>Calculadora / Simulador</span>
                  </button>
                </div>

                {/* Grid dos 3 Custos Operacionais */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                  {/* Card Gás */}
                  <div className="rounded-[18px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] p-4 flex flex-col justify-between space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FlameIcon className="w-4 h-4 text-[#60769D] dark:text-[#AFC0E2]" />
                        <span className="text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF]">Gás</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setCalcTarget('gas');
                          setShowCostCalcModal(true);
                        }}
                        className="text-[11.5px] font-bold text-[#F28C28] hover:underline flex items-center gap-1 cursor-pointer"
                      >
                        <CalculatorIcon className="w-3 h-3" />
                        Calcular
                      </button>
                    </div>

                    {/* Segmented Switch: % vs R$ */}
                    <div className="flex bg-[#EAF0F9] dark:bg-[#0D182E] p-0.5 rounded-full">
                      <button
                        type="button"
                        onClick={() => setGasType('PERCENT')}
                        className={`flex-1 py-1 text-[11px] font-bold rounded-full transition-all cursor-pointer ${
                          gasType === 'PERCENT'
                            ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                            : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E293B]'
                        }`}
                      >
                        Porcentagem (%)
                      </button>
                      <button
                        type="button"
                        onClick={() => setGasType('FIXED')}
                        className={`flex-1 py-1 text-[11px] font-bold rounded-full transition-all cursor-pointer ${
                          gasType === 'FIXED'
                            ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                            : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E293B]'
                        }`}
                      >
                        Fixo (R$ / un)
                      </button>
                    </div>

                    {/* Input */}
                    <div>
                      <label className="block text-[11px] font-medium text-[#64748B] dark:text-[#94A3B8] mb-1">
                        {gasType === 'PERCENT' ? 'Taxa sobre insumos (%)' : 'Valor por unidade produzida (R$)'}
                      </label>
                      <div className="relative flex items-center">
                        {gasType === 'FIXED' && (
                          <span className="absolute left-3 text-[12px] font-bold text-[#64748B] dark:text-[#94A3B8]">R$</span>
                        )}
                        <input
                          type="text"
                          value={gasType === 'PERCENT' ? gasPct : gasFixed}
                          onChange={(e) => {
                            const val = e.target.value.replace(/[^0-9.,]/g, '');
                            if (gasType === 'PERCENT') setGasPct(val);
                            else setGasFixed(val);
                          }}
                          placeholder={gasType === 'PERCENT' ? '20,0' : '0,50'}
                          className={`w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28] ${
                            gasType === 'FIXED' ? 'pl-9 pr-14' : 'pr-8'
                          }`}
                        />
                        <span className="absolute right-3.5 text-[11.5px] font-bold text-[#8C9BB5] dark:text-[#94A3B8]">
                          {gasType === 'PERCENT' ? '%' : '/ un'}
                        </span>
                      </div>
                    </div>
                    <span className="text-[10.5px] text-[#8C9BB5] dark:text-[#8295BC] leading-tight">
                      {gasType === 'PERCENT'
                        ? 'Multiplica essa taxa pelo valor total de ingredientes.'
                        : 'Soma este valor fixo em reais a cada produto final.'}
                    </span>
                  </div>

                  {/* Card Energia */}
                  <div className="rounded-[18px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] p-4 flex flex-col justify-between space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <ZapEnergyIcon className="w-4 h-4 text-[#60769D] dark:text-[#AFC0E2]" />
                        <span className="text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF]">Energia</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setCalcTarget('energy');
                          setShowCostCalcModal(true);
                        }}
                        className="text-[11.5px] font-bold text-[#F28C28] hover:underline flex items-center gap-1 cursor-pointer"
                      >
                        <CalculatorIcon className="w-3 h-3" />
                        Calcular
                      </button>
                    </div>

                    {/* Segmented Switch: % vs R$ */}
                    <div className="flex bg-[#EAF0F9] dark:bg-[#0D182E] p-0.5 rounded-full">
                      <button
                        type="button"
                        onClick={() => setEnergyType('PERCENT')}
                        className={`flex-1 py-1 text-[11px] font-bold rounded-full transition-all cursor-pointer ${
                          energyType === 'PERCENT'
                            ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                            : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E293B]'
                        }`}
                      >
                        Porcentagem (%)
                      </button>
                      <button
                        type="button"
                        onClick={() => setEnergyType('FIXED')}
                        className={`flex-1 py-1 text-[11px] font-bold rounded-full transition-all cursor-pointer ${
                          energyType === 'FIXED'
                            ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                            : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E293B]'
                        }`}
                      >
                        Fixo (R$ / un)
                      </button>
                    </div>

                    {/* Input */}
                    <div>
                      <label className="block text-[11px] font-medium text-[#64748B] dark:text-[#94A3B8] mb-1">
                        {energyType === 'PERCENT' ? 'Taxa sobre insumos (%)' : 'Valor por unidade produzida (R$)'}
                      </label>
                      <div className="relative flex items-center">
                        {energyType === 'FIXED' && (
                          <span className="absolute left-3 text-[12px] font-bold text-[#64748B] dark:text-[#94A3B8]">R$</span>
                        )}
                        <input
                          type="text"
                          value={energyType === 'PERCENT' ? energyPct : energyFixed}
                          onChange={(e) => {
                            const val = e.target.value.replace(/[^0-9.,]/g, '');
                            if (energyType === 'PERCENT') setEnergyPct(val);
                            else setEnergyFixed(val);
                          }}
                          placeholder={energyType === 'PERCENT' ? '20,0' : '0,35'}
                          className={`w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28] ${
                            energyType === 'FIXED' ? 'pl-9 pr-14' : 'pr-8'
                          }`}
                        />
                        <span className="absolute right-3.5 text-[11.5px] font-bold text-[#8C9BB5] dark:text-[#94A3B8]">
                          {energyType === 'PERCENT' ? '%' : '/ un'}
                        </span>
                      </div>
                    </div>
                    <span className="text-[10.5px] text-[#8C9BB5] dark:text-[#8295BC] leading-tight">
                      {energyType === 'PERCENT'
                        ? 'Multiplica essa taxa pelo valor total de ingredientes.'
                        : 'Soma este valor fixo em reais a cada produto final.'}
                    </span>
                  </div>

                  {/* Card Água */}
                  <div className="rounded-[18px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] p-4 flex flex-col justify-between space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <DropletWaterIcon className="w-4 h-4 text-[#60769D] dark:text-[#AFC0E2]" />
                        <span className="text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF]">Água</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setCalcTarget('water');
                          setShowCostCalcModal(true);
                        }}
                        className="text-[11.5px] font-bold text-[#F28C28] hover:underline flex items-center gap-1 cursor-pointer"
                      >
                        <CalculatorIcon className="w-3 h-3" />
                        Calcular
                      </button>
                    </div>

                    {/* Segmented Switch: % vs R$ */}
                    <div className="flex bg-[#EAF0F9] dark:bg-[#0D182E] p-0.5 rounded-full">
                      <button
                        type="button"
                        onClick={() => setWaterType('PERCENT')}
                        className={`flex-1 py-1 text-[11px] font-bold rounded-full transition-all cursor-pointer ${
                          waterType === 'PERCENT'
                            ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                            : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E293B]'
                        }`}
                      >
                        Porcentagem (%)
                      </button>
                      <button
                        type="button"
                        onClick={() => setWaterType('FIXED')}
                        className={`flex-1 py-1 text-[11px] font-bold rounded-full transition-all cursor-pointer ${
                          waterType === 'FIXED'
                            ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                            : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E293B]'
                        }`}
                      >
                        Fixo (R$ / un)
                      </button>
                    </div>

                    {/* Input */}
                    <div>
                      <label className="block text-[11px] font-medium text-[#64748B] dark:text-[#94A3B8] mb-1">
                        {waterType === 'PERCENT' ? 'Taxa sobre insumos (%)' : 'Valor por unidade produzida (R$)'}
                      </label>
                      <div className="relative flex items-center">
                        {waterType === 'FIXED' && (
                          <span className="absolute left-3 text-[12px] font-bold text-[#64748B] dark:text-[#94A3B8]">R$</span>
                        )}
                        <input
                          type="text"
                          value={waterType === 'PERCENT' ? waterPct : waterFixed}
                          onChange={(e) => {
                            const val = e.target.value.replace(/[^0-9.,]/g, '');
                            if (waterType === 'PERCENT') setWaterPct(val);
                            else setWaterFixed(val);
                          }}
                          placeholder={waterType === 'PERCENT' ? '20,0' : '0,10'}
                          className={`w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28] ${
                            waterType === 'FIXED' ? 'pl-9 pr-14' : 'pr-8'
                          }`}
                        />
                        <span className="absolute right-3.5 text-[11.5px] font-bold text-[#8C9BB5] dark:text-[#94A3B8]">
                          {waterType === 'PERCENT' ? '%' : '/ un'}
                        </span>
                      </div>
                    </div>
                    <span className="text-[10.5px] text-[#8C9BB5] dark:text-[#8295BC] leading-tight">
                      {waterType === 'PERCENT'
                        ? 'Multiplica essa taxa pelo valor total de ingredientes.'
                        : 'Soma este valor fixo em reais a cada produto final.'}
                    </span>
                  </div>
                </div>

                {/* Resumo e Botão Salvar */}
                <div className="p-3.5 rounded-[18px] bg-[#FFF8EE] dark:bg-[#1C1710] border border-[#F28C28]/30 flex flex-col md:flex-row items-center justify-between gap-3">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                        Taxas Operacionais Complementares:
                      </span>
                      <span className="text-[12.5px] font-extrabold text-[#F28C28]">
                        {parseFloat(totalOperationalPct) > 0 ? `${totalOperationalPct}%` : ''}
                        {parseFloat(totalOperationalPct) > 0 && parseFloat(totalOperationalFixed) > 0 ? ' + ' : ''}
                        {parseFloat(totalOperationalFixed) > 0 ? `R$ ${totalOperationalFixed.replace('.', ',')} / un` : ''}
                        {parseFloat(totalOperationalPct) === 0 && parseFloat(totalOperationalFixed) === 0 ? '0,0%' : ''}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#60769D] dark:text-[#93A4C6]">
                      Essas taxas complementam os custos de cocção (gás e energia) calculados nas suas Receitas Base.
                    </p>
                  </div>

                  <RoundedActionButton
                    label={savingCosts ? 'Salvando...' : 'Salvar custos'}
                    onClick={handleSaveCosts}
                    variant="primary"
                    height={36}
                  />
                </div>
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* ABA 4: UNIDADES DE MEDIDA */}
          {/* ========================================================= */}
          {activeTab === 'unidades' && (
            <>
              {/* Unidades internas */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-4 transition-colors">
                <div className="flex items-center gap-2 border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                  <ScalesUnitsIcon className="w-5 h-5 text-[#BA5200] dark:text-[#F28C28] shrink-0" />
                  <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Unidades internas
                  </h3>
                </div>

                <div className="grid grid-cols-4 gap-3 items-end">
                  <div>
                    <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                      Massa
                    </label>
                    <RoundedDropdown
                      value={massBaseUnit}
                      onChange={setMassBaseUnit}
                      options={['mg', 'g', 'kg', 't']}
                      width="100%"
                      height={34}
                    />
                  </div>

                  <div>
                    <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                      Volume
                    </label>
                    <RoundedDropdown
                      value={volumeBaseUnit}
                      onChange={setVolumeBaseUnit}
                      options={['ml', 'L', 'kL']}
                      width="100%"
                      height={34}
                    />
                  </div>

                  <div>
                    <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                      Quantidade
                    </label>
                    <RoundedDropdown
                      value={countBaseUnit}
                      onChange={setCountBaseUnit}
                      options={['un']}
                      width="100%"
                      height={34}
                    />
                  </div>

                  <div className="flex justify-end">
                    <RoundedActionButton
                      label={savingUnits ? 'Salvando...' : 'Salvar unidades internas'}
                      onClick={handleSaveUnits}
                      variant="primary"
                      height={34}
                    />
                  </div>
                </div>
              </div>

              {/* Unidades configuráveis por insumo */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-4 transition-colors">
                <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-3">
                  <div className="flex items-center gap-2.5">
                    <KitchenUtensilsIcon className="w-[22px] h-[22px] text-[#BA5200] dark:text-[#F28C28] shrink-0" />
                    <div>
                      <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                        Unidades configuráveis por insumo
                      </h3>
                      <p className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
                        Ex.: 1 xícara de leite equivale a 240 ml; 1 xícara de farinha equivale a 120 g.
                      </p>
                    </div>
                  </div>

                  <RoundedActionButton
                    label={`Gerenciar Unidades (${conversions.length})`}
                    onClick={() => {
                      fetchConversions();
                      fetchMaterialsForConversions();
                      setShowCustomUnitsModal(true);
                    }}
                    variant="primary"
                    height={36}
                  />
                </div>

                {/* Resumo visual rápido */}
                <div className="rounded-[16px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="space-y-0.5 text-center sm:text-left">
                    <span className="text-[12.5px] font-bold text-[#18223A] dark:text-[#F4F7FF] block">
                      {conversions.length === 0
                        ? 'Nenhuma unidade personalizada cadastrada ainda.'
                        : `${conversions.length} ${conversions.length === 1 ? 'medida personalizada cadastrada' : 'medidas personalizadas cadastradas'}.`}
                    </span>
                    <span className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6] block">
                      Você pode visualizar todas, editar equivalências, excluir individualmente ou em massa na janela de gerenciamento.
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* ========================================================= */}
          {/* ABA 5: BANCO DE DADOS & BI */}
          {/* ========================================================= */}
          {activeTab === 'banco' && (
            <>
              {/* Auditoria & BI */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-3.5 transition-colors">
                <div className="flex items-center gap-2 border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                  <DatabaseBiIcon className="w-5 h-5 text-[#BA5200] dark:text-[#F28C28] shrink-0" />
                  <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Auditoria & BI
                  </h3>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-[12.5px] font-semibold text-[#18223A] dark:text-[#F4F7FF]">
                    Retenção do histórico de edições (Meses):
                  </span>
                  <div className="w-[80px]">
                    <CapsuleInput
                      value={retentionMonths}
                      onChange={(v) => setRetentionMonths(v.replace(/[^0-9]/g, ''))}
                      placeholder="36"
                    />
                  </div>
                  <RoundedActionButton
                    label={savingRetention ? 'Salvando...' : 'Salvar'}
                    onClick={handleSaveRetention}
                    variant="primary"
                    height={34}
                  />
                  <span className="text-[11.5px] text-[#8C9BB5] dark:text-[#64748B] pl-2">
                    Itens mais antigos serão limpos automaticamente na inicialização para otimizar o banco de dados.
                  </span>
                </div>
              </div>

              {/* Fonte de dados */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-3.5 transition-colors">
                <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                  <div className="flex items-center gap-2">
                    <DatabaseBiIcon className="w-5 h-5 text-[#BA5200] dark:text-[#F28C28] shrink-0" />
                    <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                      Fonte de dados
                    </h3>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#EBFBF0] dark:bg-[#133020] text-[#16A34A] dark:text-[#4ADE80]">
                    SQLite Ativo ({dbSize})
                  </span>
                </div>

                <div>
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                    SQLite atual
                  </label>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 min-w-0">
                      <CapsuleInput value={dbPath} onChange={() => {}} disabled />
                    </div>
                    <RoundedActionButton
                      label={backingUp ? 'Gerando Backup...' : 'Fazer Backup'}
                      onClick={handleBackup}
                      variant="primary"
                      height={34}
                    />
                    <RoundedActionButton
                      label={optimizing ? 'Otimizando...' : 'Otimizar (VACUUM)'}
                      onClick={handleVacuum}
                      variant="secondary"
                      height={34}
                    />
                  </div>
                </div>

                {lastBackup && (
                  <div className="p-3 rounded-[14px] bg-[#EAFaf1] dark:bg-[#12372E] text-[12px] text-[#1E833F] dark:text-[#61E3B9] flex items-center justify-between">
                    <span>Backup recente: <strong>{lastBackup.name}</strong> ({lastBackup.size})</span>
                    <span className="text-[11px] opacity-80">{lastBackup.time}</span>
                  </div>
                )}

                <p className="text-[11.5px] text-[#8C9BB5] dark:text-[#64748B]">
                  SQLite local/arquivo de rede funciona nesta versão. Conectores PostgreSQL/MySQL podem ser adicionados depois.
                </p>
              </div>

              {/* Auditoria do banco */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-3 transition-colors">
                <div className="flex items-center gap-2 border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                  <span className="text-base">🔍</span>
                  <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Auditoria do banco
                  </h3>
                </div>

                <p className="text-[12px] text-[#60769D] dark:text-[#AFC0E2]">
                  Veja as últimas operações, diferencie INSERT/UPDATE/DELETE e confira o antes/depois das edições diretamente no histórico de cada módulo.
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Modal Calculadora Auxiliar de Custos Operacionais */}
      {showCostCalcModal && (
        <div className="fixed inset-0 z-50 bg-[#0B132B]/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="w-full max-w-xl rounded-[26px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 relative max-h-[92vh] overflow-y-auto space-y-4">
            {/* Header */}
            <div className="flex items-start justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-3">
              <div className="flex items-center gap-2.5">
                <CalculatorIcon className="w-5 h-5 text-[#BA5200] dark:text-[#F28C28] shrink-0" />
                <div>
                  <h3 className="text-[16px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Calculadora de Custo Operacional
                  </h3>
                  <p className="text-[12px] text-[#60769D] dark:text-[#93A4C6]">
                    Descubra o valor unitário e a porcentagem ideal com base nas suas contas reais.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowCostCalcModal(false)}
                className="w-8 h-8 rounded-full bg-[#F0F4FA] dark:bg-[#1C2C4E] hover:bg-[#E2EAF5] dark:hover:bg-[#253966] text-[#60769D] dark:text-[#93A4C6] flex items-center justify-center text-[15px] font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Abas da Calculadora */}
            <div className="flex bg-[#F0F4FA] dark:bg-[#0D182E] p-1 rounded-full gap-1">
              <button
                type="button"
                onClick={() => setCalcTarget('gas')}
                className={`flex-1 py-1.5 rounded-full text-[12px] font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                  calcTarget === 'gas'
                    ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                    : 'text-[#60769D] dark:text-[#93A4C6] hover:text-[#18223A]'
                }`}
              >
                <FlameIcon className="w-3.5 h-3.5" />
                Gás
              </button>
              <button
                type="button"
                onClick={() => setCalcTarget('energy')}
                className={`flex-1 py-1.5 rounded-full text-[12px] font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                  calcTarget === 'energy'
                    ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                    : 'text-[#60769D] dark:text-[#93A4C6] hover:text-[#18223A]'
                }`}
              >
                <ZapEnergyIcon className="w-3.5 h-3.5" />
                Energia
              </button>
              <button
                type="button"
                onClick={() => setCalcTarget('water')}
                className={`flex-1 py-1.5 rounded-full text-[12px] font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                  calcTarget === 'water'
                    ? 'bg-white dark:bg-[#1F3156] text-[#F28C28] shadow-xs'
                    : 'text-[#60769D] dark:text-[#93A4C6] hover:text-[#18223A]'
                }`}
              >
                <DropletWaterIcon className="w-3.5 h-3.5" />
                Água
              </button>
            </div>

            {/* CONTEÚDO: ABA GÁS */}
            {calcTarget === 'gas' && (() => {
              const isCylinder = gasCalcType === 'cylinder';
              const pPrice = parseFloat(isCylinder ? gasCylinderPrice.replace(',', '.') : gasBillMonthly.replace(',', '.')) || 0;
              const pUnits = parseFloat(isCylinder ? gasCylinderUnits.replace(',', '.') : gasBillUnits.replace(',', '.')) || 0;
              const unitCost = pUnits > 0 ? pPrice / pUnits : 0;
              const avgProd = parseFloat(gasAvgProdCost.replace(',', '.')) || 0;
              const pctEquiv = avgProd > 0 && unitCost > 0 ? (unitCost / avgProd) * 100 : 0;

              return (
                <div className="space-y-4">
                  {/* Seletor Botijão vs Conta */}
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setGasCalcType('cylinder')}
                      className={`flex-1 py-1.5 px-3 rounded-[14px] text-[12px] font-bold border transition-all cursor-pointer text-center ${
                        isCylinder
                          ? 'border-[#F28C28] bg-[#FFF8EE] dark:bg-[#2A1D0F] text-[#F28C28]'
                          : 'border-[#E2EAF5] dark:border-[#24385E] text-[#60769D] dark:text-[#93A4C6]'
                      }`}
                    >
                      Usando Botijão (GLP 13kg/45kg)
                    </button>
                    <button
                      type="button"
                      onClick={() => setGasCalcType('bill')}
                      className={`flex-1 py-1.5 px-3 rounded-[14px] text-[12px] font-bold border transition-all cursor-pointer text-center ${
                        !isCylinder
                          ? 'border-[#F28C28] bg-[#FFF8EE] dark:bg-[#2A1D0F] text-[#F28C28]'
                          : 'border-[#E2EAF5] dark:border-[#24385E] text-[#60769D] dark:text-[#93A4C6]'
                      }`}
                    >
                      Usando Conta Mensal de Gás
                    </button>
                  </div>

                  {/* Campos */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1">
                        {isCylinder ? 'Preço do Botijão (R$)' : 'Valor da Conta Mensal (R$)'}
                      </label>
                      <input
                        type="text"
                        value={isCylinder ? gasCylinderPrice : gasBillMonthly}
                        onChange={(e) => isCylinder ? setGasCylinderPrice(e.target.value.replace(/[^0-9.,]/g, '')) : setGasBillMonthly(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="120,00"
                        className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                    </div>
                    <div>
                      <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1">
                        {isCylinder ? 'Produtos feitos por botijão' : 'Produtos feitos no mês'}
                      </label>
                      <input
                        type="text"
                        value={isCylinder ? gasCylinderUnits : gasBillUnits}
                        onChange={(e) => isCylinder ? setGasCylinderUnits(e.target.value.replace(/[^0-9.,]/g, '')) : setGasBillUnits(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder={isCylinder ? "300" : "1000"}
                        className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                    </div>
                  </div>

                  {/* Conversor para % opcional */}
                  <div className="p-3 rounded-[16px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6]">
                        Deseja usar em porcentagem? Digite o custo médio dos ingredientes de um produto:
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] font-bold text-[#8C9BB5]">R$</span>
                      <input
                        type="text"
                        value={gasAvgProdCost}
                        onChange={(e) => setGasAvgProdCost(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="4,00"
                        className="w-28 h-[32px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[12px] font-bold px-3 focus:outline-none"
                      />
                      <span className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
                        {pctEquiv > 0 ? `Taxa equivalente: ${pctEquiv.toFixed(1).replace('.', ',')}%` : '(informe para calcular a %)'}
                      </span>
                    </div>
                  </div>

                  {/* Resultado e Botões de Aplicação */}
                  <div className="p-4 rounded-[18px] bg-[#FFF8EE] dark:bg-[#231A0F] border border-[#F28C28]/35 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[12px] font-semibold text-[#18223A] dark:text-[#F4F7FF]">
                        Custo de Gás calculado por unidade:
                      </span>
                      <span className="text-[16px] font-extrabold text-[#F28C28]">
                        R$ {unitCost.toFixed(2).replace('.', ',')} / un
                      </span>
                    </div>

                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => handleApplyCalcResult('gas', 'FIXED', unitCost)}
                        className="flex-1 py-2 px-3 rounded-full bg-[#F28C28] hover:bg-[#D97706] text-white text-[12px] font-bold transition-all shadow-xs cursor-pointer text-center"
                      >
                        Aplicar como Valor Fixo (R$ {unitCost.toFixed(2).replace('.', ',')})
                      </button>
                      {pctEquiv > 0 && (
                        <button
                          type="button"
                          onClick={() => handleApplyCalcResult('gas', 'PERCENT', pctEquiv)}
                          className="flex-1 py-2 px-3 rounded-full bg-white dark:bg-[#1F3156] text-[#F28C28] border border-[#F28C28]/40 hover:bg-[#FFF4E5] dark:hover:bg-[#2A1D0F] text-[12px] font-bold transition-all cursor-pointer text-center"
                        >
                          Aplicar como {pctEquiv.toFixed(1).replace('.', ',')}%
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* CONTEÚDO: ABA ENERGIA */}
            {calcTarget === 'energy' && (() => {
              const bill = parseFloat(energyBillMonthly.replace(',', '.')) || 0;
              const days = parseFloat(energyDaysOpen.replace(',', '.')) || 0;
              const dailyUnits = parseFloat(energyUnitsPerDay.replace(',', '.')) || 0;
              const totalMonthlyUnits = days * dailyUnits;
              const unitCost = totalMonthlyUnits > 0 ? bill / totalMonthlyUnits : 0;
              const dailyCost = days > 0 ? bill / days : 0;
              const avgProd = parseFloat(energyAvgProdCost.replace(',', '.')) || 0;
              const pctEquiv = avgProd > 0 && unitCost > 0 ? (unitCost / avgProd) * 100 : 0;

              return (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1">
                        Conta de Luz (R$/mês)
                      </label>
                      <input
                        type="text"
                        value={energyBillMonthly}
                        onChange={(e) => setEnergyBillMonthly(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="450,00"
                        className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                    </div>
                    <div>
                      <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1">
                        Dias abertos no mês
                      </label>
                      <input
                        type="text"
                        value={energyDaysOpen}
                        onChange={(e) => setEnergyDaysOpen(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="26"
                        className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                    </div>
                    <div>
                      <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1">
                        Produtos feitos/dia
                      </label>
                      <input
                        type="text"
                        value={energyUnitsPerDay}
                        onChange={(e) => setEnergyUnitsPerDay(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="50"
                        className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                    </div>
                  </div>

                  {/* Informações intermediárias */}
                  <div className="grid grid-cols-2 gap-2 text-[11.5px] bg-[#F8FAFD] dark:bg-[#14223E] p-3 rounded-[16px] border border-[#E4ECF7] dark:border-[#22355A]">
                    <div>
                      <span className="text-[#60769D] dark:text-[#93A4C6]">Custo de energia diário: </span>
                      <strong className="text-[#18223A] dark:text-[#F4F7FF]">R$ {dailyCost.toFixed(2).replace('.', ',')} / dia</strong>
                    </div>
                    <div>
                      <span className="text-[#60769D] dark:text-[#93A4C6]">Volume mensal estimado: </span>
                      <strong className="text-[#18223A] dark:text-[#F4F7FF]">{totalMonthlyUnits.toLocaleString('pt-BR')} unidades</strong>
                    </div>
                  </div>

                  {/* Conversor para % opcional */}
                  <div className="p-3 rounded-[16px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] space-y-2">
                    <span className="text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6]">
                      Deseja usar em porcentagem? Digite o custo médio dos ingredientes de um produto:
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] font-bold text-[#8C9BB5]">R$</span>
                      <input
                        type="text"
                        value={energyAvgProdCost}
                        onChange={(e) => setEnergyAvgProdCost(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="5,00"
                        className="w-28 h-[32px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[12px] font-bold px-3 focus:outline-none"
                      />
                      <span className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
                        {pctEquiv > 0 ? `Taxa equivalente: ${pctEquiv.toFixed(1).replace('.', ',')}%` : '(informe para calcular a %)'}
                      </span>
                    </div>
                  </div>

                  {/* Resultado e Botões */}
                  <div className="p-4 rounded-[18px] bg-[#FFF8EE] dark:bg-[#231A0F] border border-[#F28C28]/35 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[12px] font-semibold text-[#18223A] dark:text-[#F4F7FF]">
                        Custo de Energia por unidade:
                      </span>
                      <span className="text-[16px] font-extrabold text-[#F28C28]">
                        R$ {unitCost.toFixed(2).replace('.', ',')} / un
                      </span>
                    </div>

                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => handleApplyCalcResult('energy', 'FIXED', unitCost)}
                        className="flex-1 py-2 px-3 rounded-full bg-[#F28C28] hover:bg-[#D97706] text-white text-[12px] font-bold transition-all shadow-xs cursor-pointer text-center"
                      >
                        Aplicar como Valor Fixo (R$ {unitCost.toFixed(2).replace('.', ',')})
                      </button>
                      {pctEquiv > 0 && (
                        <button
                          type="button"
                          onClick={() => handleApplyCalcResult('energy', 'PERCENT', pctEquiv)}
                          className="flex-1 py-2 px-3 rounded-full bg-white dark:bg-[#1F3156] text-[#F28C28] border border-[#CA8A04]/40 hover:bg-[#FEF9C3] dark:hover:bg-[#2B2710] text-[12px] font-bold transition-all cursor-pointer text-center"
                        >
                          Aplicar como {pctEquiv.toFixed(1).replace('.', ',')}%
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* CONTEÚDO: ABA ÁGUA */}
            {calcTarget === 'water' && (() => {
              const bill = parseFloat(waterBillMonthly.replace(',', '.')) || 0;
              const days = parseFloat(waterDaysOpen.replace(',', '.')) || 0;
              const dailyUnits = parseFloat(waterUnitsPerDay.replace(',', '.')) || 0;
              const totalMonthlyUnits = days * dailyUnits;
              const unitCost = totalMonthlyUnits > 0 ? bill / totalMonthlyUnits : 0;
              const dailyCost = days > 0 ? bill / days : 0;
              const avgProd = parseFloat(waterAvgProdCost.replace(',', '.')) || 0;
              const pctEquiv = avgProd > 0 && unitCost > 0 ? (unitCost / avgProd) * 100 : 0;

              return (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1">
                        Conta de Água (R$/mês)
                      </label>
                      <input
                        type="text"
                        value={waterBillMonthly}
                        onChange={(e) => setWaterBillMonthly(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="130,00"
                        className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                    </div>
                    <div>
                      <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1">
                        Dias abertos no mês
                      </label>
                      <input
                        type="text"
                        value={waterDaysOpen}
                        onChange={(e) => setWaterDaysOpen(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="26"
                        className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                    </div>
                    <div>
                      <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1">
                        Produtos feitos/dia
                      </label>
                      <input
                        type="text"
                        value={waterUnitsPerDay}
                        onChange={(e) => setWaterUnitsPerDay(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="50"
                        className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                      />
                    </div>
                  </div>

                  {/* Informações intermediárias */}
                  <div className="grid grid-cols-2 gap-2 text-[11.5px] bg-[#F8FAFD] dark:bg-[#14223E] p-3 rounded-[16px] border border-[#E4ECF7] dark:border-[#22355A]">
                    <div>
                      <span className="text-[#60769D] dark:text-[#93A4C6]">Custo de água diário: </span>
                      <strong className="text-[#18223A] dark:text-[#F4F7FF]">R$ {dailyCost.toFixed(2).replace('.', ',')} / dia</strong>
                    </div>
                    <div>
                      <span className="text-[#60769D] dark:text-[#93A4C6]">Volume mensal estimado: </span>
                      <strong className="text-[#18223A] dark:text-[#F4F7FF]">{totalMonthlyUnits.toLocaleString('pt-BR')} unidades</strong>
                    </div>
                  </div>

                  {/* Conversor para % opcional */}
                  <div className="p-3 rounded-[16px] bg-[#F8FAFD] dark:bg-[#14223E] border border-[#E4ECF7] dark:border-[#22355A] space-y-2">
                    <span className="text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6]">
                      Deseja usar em porcentagem? Digite o custo médio dos ingredientes de um produto:
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] font-bold text-[#8C9BB5]">R$</span>
                      <input
                        type="text"
                        value={waterAvgProdCost}
                        onChange={(e) => setWaterAvgProdCost(e.target.value.replace(/[^0-9.,]/g, ''))}
                        placeholder="5,00"
                        className="w-28 h-[32px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[12px] font-bold px-3 focus:outline-none"
                      />
                      <span className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
                        {pctEquiv > 0 ? `Taxa equivalente: ${pctEquiv.toFixed(1).replace('.', ',')}%` : '(informe para calcular a %)'}
                      </span>
                    </div>
                  </div>

                  {/* Resultado e Botões */}
                  <div className="p-4 rounded-[18px] bg-[#FFF8EE] dark:bg-[#231A0F] border border-[#F28C28]/35 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[12px] font-semibold text-[#18223A] dark:text-[#F4F7FF]">
                        Custo de Água por unidade:
                      </span>
                      <span className="text-[16px] font-extrabold text-[#F28C28]">
                        R$ {unitCost.toFixed(2).replace('.', ',')} / un
                      </span>
                    </div>

                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => handleApplyCalcResult('water', 'FIXED', unitCost)}
                        className="flex-1 py-2 px-3 rounded-full bg-[#F28C28] hover:bg-[#D97706] text-white text-[12px] font-bold transition-all shadow-xs cursor-pointer text-center"
                      >
                        Aplicar como Valor Fixo (R$ {unitCost.toFixed(2).replace('.', ',')})
                      </button>
                      {pctEquiv > 0 && (
                        <button
                          type="button"
                          onClick={() => handleApplyCalcResult('water', 'PERCENT', pctEquiv)}
                          className="flex-1 py-2 px-3 rounded-full bg-white dark:bg-[#1F3156] text-[#F28C28] border border-[#0284C7]/40 hover:bg-[#E0F2FE] dark:hover:bg-[#0C2740] text-[12px] font-bold transition-all cursor-pointer text-center"
                        >
                          Aplicar como {pctEquiv.toFixed(1).replace('.', ',')}%
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* Modal de Ajuda Didático de IA */}
      {showAiHelpModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-[2px] flex items-center justify-center z-50 p-4">
          <div className="w-[560px] max-h-[90vh] overflow-y-auto rounded-[24px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col space-y-4">
            {/* Cabeçalho do Modal */}
            <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-3">
              <div className="flex items-center gap-2.5">
                <AiChipIcon className="w-6 h-6 text-[#BA5200] dark:text-[#F28C28]" />
                <div>
                  <h3 className="text-[16px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Como obter e configurar sua Chave de IA
                  </h3>
                  <p className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
                    Guia prático para ativar a leitura automática de notas e receitas
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowAiHelpModal(false)}
                className="w-8 h-8 rounded-full flex items-center justify-center text-[#94A3B8] hover:text-[#18223A] dark:hover:text-white hover:bg-[#F1F5F9] dark:hover:bg-[#1E293B] transition-colors cursor-pointer"
                title="Fechar"
              >
                ✕
              </button>
            </div>

            {/* O que é e para que serve */}
            <div className="p-3.5 rounded-[16px] bg-[#EFF6FF] dark:bg-[#13233E] border border-[#BFDBFE]/60 dark:border-[#1E3A5F] text-[12px] text-[#1E3A8A] dark:text-[#93C5FD] leading-relaxed flex items-start gap-2.5">
              <InfoCircleIcon className="w-4 h-4 shrink-0 mt-0.5 text-[#2563EB] dark:text-[#60A5FA]" />
              <div>
                <strong>Para que serve a chave de API?</strong><br />
                Ela funciona como uma senha segura pessoal que conecta o Nexo à inteligência artificial para ler e transcrever automaticamente fotos de notas fiscais de compras, cupons de supermercado e fichas técnicas de receitas.
              </div>
            </div>

            {/* Provedores com Passo a Passo */}
            <div className="space-y-3">
              {/* Opção 1: Google Gemini (Recomendado) */}
              <div className="p-4 rounded-[18px] bg-[#F8FAFD] dark:bg-[#0D182E] border border-[#E2EAF5] dark:border-[#203357] space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[13px] text-[#18223A] dark:text-[#F4F7FF]">
                      1. Google Gemini
                    </span>
                    <span className="text-[10.5px] font-extrabold px-2 py-0.5 rounded-full bg-[#EBF7EE] text-[#16A34A] dark:bg-[#143320] dark:text-[#4ADE80]">
                      ⭐ Recomendado · Gratuito para começar
                    </span>
                  </div>
                  <a
                    href="https://aistudio.google.com/app/apikey"
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[11.5px] font-bold text-[#F28C28] hover:underline"
                  >
                    <span>Abrir Google AI Studio</span>
                    <span>↗</span>
                  </a>
                </div>

                <ol className="text-[12px] text-[#475569] dark:text-[#CBD5E1] space-y-1.5 pl-4 list-decimal leading-relaxed">
                  <li>Acesse o <strong>Google AI Studio</strong> com sua conta Google (Gmail).</li>
                  <li>Clique no botão azul <strong>"Create API key"</strong> (Criar chave de API).</li>
                  <li>Copie o código gerado (começa com <code>AIza...</code>) e cole no campo <strong>Chave API</strong> do Nexo.</li>
                </ol>
                <p className="text-[11px] text-[#64748B] dark:text-[#94A3B8] italic pt-1">
                  O plano padrão do Google oferece cotas gratuitas generosas diárias, ideais para o uso do restaurante.
                </p>
              </div>

              {/* Opção 2: OpenAI ChatGPT */}
              <div className="p-4 rounded-[18px] bg-[#F8FAFD] dark:bg-[#0D182E] border border-[#E2EAF5] dark:border-[#203357] space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[13px] text-[#18223A] dark:text-[#F4F7FF]">
                      2. OpenAI ChatGPT
                    </span>
                    <span className="text-[10.5px] font-semibold px-2 py-0.5 rounded-full bg-[#EFF4FB] text-[#60769D] dark:bg-[#1C2C4E] dark:text-[#93A4C6]">
                      Créditos pré-pagos
                    </span>
                  </div>
                  <a
                    href="https://platform.openai.com/api-keys"
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[11.5px] font-bold text-[#60769D] dark:text-[#93A4C6] hover:underline"
                  >
                    <span>Abrir OpenAI Platform</span>
                    <span>↗</span>
                  </a>
                </div>

                <ol className="text-[12px] text-[#475569] dark:text-[#CBD5E1] space-y-1.5 pl-4 list-decimal leading-relaxed">
                  <li>Acesse a plataforma da OpenAI e crie ou faça login na sua conta.</li>
                  <li>Vá em <strong>API Keys</strong> e clique em <strong>"Create new secret key"</strong>.</li>
                  <li>Copie o código gerado (começa com <code>sk-...</code>) e cole no Nexo.</li>
                </ol>
              </div>
            </div>

            {/* Aviso de Segurança e Trava Diária */}
            <div className="p-3 rounded-[16px] bg-[#FFF8EE] dark:bg-[#1A140B] border border-[#F28C28]/30 space-y-1.5 text-[11.5px] text-[#60769D] dark:text-[#C5B39A]">
              <div className="flex items-center gap-2 text-[#BA5200] dark:text-[#F28C28] font-bold">
                <span>🔒</span>
                <span>Segurança e Privacidade Garantidas</span>
              </div>
              <p>
                Sua chave fica guardada exclusivamente no seu computador de forma segura e local. Ela nunca é enviada para nenhum servidor externo do Nexo.
              </p>
              <p className="text-[11px] opacity-90">
                O <strong>Alerta de Segurança Diário</strong> logo abaixo serve como uma trava de proteção para garantir que o sistema nunca ultrapasse o limite de requisições que você definiu.
              </p>
            </div>

            {/* Rodapé de Ação */}
            <div className="flex justify-end pt-2 border-t border-[#E2EAF5] dark:border-[#1E3156]">
              <RoundedActionButton
                label="Entendi, voltar"
                onClick={() => setShowAiHelpModal(false)}
                variant="primary"
                height={36}
              />
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL: GERENCIADOR DE UNIDADES CONFIGURÁVEIS POR INSUMO */}
      {/* ========================================================= */}
      {showCustomUnitsModal && (
        <div className="fixed inset-0 z-50 bg-[#0B132B]/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="w-full max-w-4xl rounded-[26px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 relative max-h-[92vh] flex flex-col space-y-4">
            
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-3 shrink-0">
              <div>
                <h3 className="text-[17px] font-bold text-[#18223A] dark:text-[#F4F7FF] flex items-center gap-2">
                  <span>Unidades Configuráveis por Insumo</span>
                  <span className="text-[11.5px] font-bold px-2 py-0.5 rounded-full bg-[#EFF4FB] dark:bg-[#1D3557] text-[#BA5200] dark:text-[#F28C28]">
                    {conversions.length} {conversions.length === 1 ? 'cadastrada' : 'cadastradas'}
                  </span>
                </h3>
                <p className="text-[12px] text-[#60769D] dark:text-[#93A4C6]">
                  Controle central de todas as medidas customizadas (xícaras, colheres, latas, potes) vinculadas a cada insumo.
                </p>
              </div>

              <button
                type="button"
                onClick={() => {
                  setShowCustomUnitsModal(false);
                  setSelectedConversionIds(new Set());
                }}
                className="w-8 h-8 rounded-full bg-[#F0F4FA] dark:bg-[#1C2C4E] hover:bg-[#E2EAF5] dark:hover:bg-[#253966] text-[#60769D] dark:text-[#93A4C6] flex items-center justify-center text-[15px] font-bold cursor-pointer transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Barra de Ações: Padrão Nexo (Ações na Esquerda, Busca na Direita) */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 shrink-0">
              {/* Esquerda: Botões de Ação */}
              <div className="flex items-center gap-2.5 w-full sm:w-auto">
                {selectedConversionIds.size < 2 ? (
                  <RoundedActionButton
                    label="Nova Unidade"
                    onClick={handleOpenNewConversion}
                    variant="primary"
                    icon={<PlusIcon size={14} />}
                    height={32}
                  />
                ) : (
                  <div className="flex items-center gap-2.5">
                    <RoundedActionButton
                      label="Excluir"
                      onClick={handleBatchDeleteConversions}
                      disabled={isDeletingBatch}
                      variant="danger"
                      icon={<TrashIcon size={15} />}
                      height={32}
                    />
                    <span className="text-[12px] font-bold text-[#687796] dark:text-[#93A4C6] bg-[#F4F7FC] dark:bg-[#142544] border border-[#DDE5F2] dark:border-[#24385E] px-3.5 py-1.5 rounded-full shadow-xs">
                      {selectedConversionIds.size} selecionados
                    </span>
                  </div>
                )}
              </div>

              {/* Direita: Busca oficial Nexo com RoundedEntry (lupa vetorial SVG monocromática) */}
              <div className="w-full sm:w-auto flex justify-end">
                <RoundedEntry
                  value={conversionSearch}
                  onChange={setConversionSearch}
                  placeholder="Pesquisar"
                  width={280}
                  height={32}
                />
              </div>
            </div>

            {/* Tabela de Unidades (Padrão Oficial Nexo) */}
            <div className="flex-1 w-full rounded-[22px] bg-white dark:bg-[#111F3B] p-2.5 flex flex-col min-h-[300px] border border-[#E2EAF5] dark:border-[#203357] shadow-xs relative transition-colors overflow-hidden">
              <div className="flex-1 w-full overflow-auto flex flex-col relative">
                <div className="min-w-full inline-block align-middle flex-1 flex flex-col">
                  {(() => {
                    const q = conversionSearch.toLowerCase().trim();
                    const filtered = conversions.filter(c =>
                      !q || c.material_name.toLowerCase().includes(q) || c.unit_name.toLowerCase().includes(q)
                    );

                    // Ordenação dinâmica idêntica à tabela principal do Nexo
                    const sorted = [...filtered].sort((a, b) => {
                      let cmp = 0;
                      if (convSortCol === 'material_name') {
                        cmp = a.material_name.localeCompare(b.material_name, 'pt-BR', { sensitivity: 'base' });
                      } else if (convSortCol === 'code') {
                        cmp = (a.material_code || '').localeCompare(b.material_code || '', 'pt-BR', { sensitivity: 'base' });
                      } else if (convSortCol === 'brand') {
                        cmp = (a.material_brand || '').localeCompare(b.material_brand || '', 'pt-BR', { sensitivity: 'base' });
                      } else if (convSortCol === 'category') {
                        cmp = (a.material_category || '').localeCompare(b.material_category || '', 'pt-BR', { sensitivity: 'base' });
                      } else if (convSortCol === 'unit') {
                        const uA = a.material_unit || a.base_unit || '';
                        const uB = b.material_unit || b.base_unit || '';
                        cmp = uA.localeCompare(uB, 'pt-BR', { sensitivity: 'base' });
                      } else if (convSortCol === 'unit_name') {
                        cmp = a.unit_name.localeCompare(b.unit_name, 'pt-BR', { sensitivity: 'base' });
                      } else if (convSortCol === 'equivalence') {
                        cmp = a.factor_to_base - b.factor_to_base;
                      }
                      return convSortDir === 'ASC' ? cmp : -cmp;
                    });

                    const isAllSelected = sorted.length > 0 && sorted.every(c => selectedConversionIds.has(c.id));

                    const toggleSelectAll = () => {
                      if (isAllSelected) {
                        setSelectedConversionIds(new Set());
                      } else {
                        const next = new Set(selectedConversionIds);
                        sorted.forEach(c => next.add(c.id));
                        setSelectedConversionIds(next);
                      }
                    };

                    const isColVis = (key: string) => !convHiddenCols.includes(key);

                    if (loadingConversions) {
                      return (
                        <div className="py-20 text-center text-[#60769D] dark:text-[#93A4C6] text-[13px] font-medium">
                          Carregando unidades configuradas...
                        </div>
                      );
                    }

                    if (sorted.length === 0) {
                      return (
                        <div className="py-20 text-center text-[#60769D] dark:text-[#93A4C6] text-[13px] space-y-2 select-none">
                          <p className="font-bold text-[#18223A] dark:text-[#F4F7FF]">
                            {conversionSearch ? 'Nenhuma unidade encontrada para esta busca.' : 'Ainda não há medidas configuradas.'}
                          </p>
                          <p className="text-[12px] opacity-80">
                            {conversionSearch ? 'Tente buscar com outro termo ou limpe o filtro.' : 'Clique no botão "Nova Unidade" acima para vincular uma medida a um insumo.'}
                          </p>
                        </div>
                      );
                    }

                    return (
                      <>
                        {/* Capsule Table Header Oficial Nexo (height=36px, rounded-full) */}
                        <div className="h-[36px] rounded-full bg-[#EEF4FB] dark:bg-[#142544] flex items-center sticky top-0 z-20 select-none shrink-0 mb-1">
                          {/* Left Master Checkbox (60px) */}
                          <div className="w-[60px] h-full flex items-center justify-center shrink-0 border-r border-[#E5ECF5] dark:border-[#24385E] rounded-l-full">
                            <NexoCheckbox
                              checked={isAllSelected}
                              onChange={toggleSelectAll}
                              title="Selecionar todos"
                            />
                          </div>

                          {/* Dynamic Columns with Sort Arrow */}
                          <div className="flex items-center flex-1 h-full">
                            {/* Insumo */}
                            {isColVis('material_name') && (
                              <button
                                type="button"
                                onClick={() => handleConvSort('material_name')}
                                className="flex-[1.4] h-full px-3.5 flex items-center border-r border-[#E5ECF5] dark:border-[#24385E] text-[12.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer group text-left min-w-0"
                              >
                                <span className="truncate">
                                  Insumo{convSortCol === 'material_name' ? (convSortDir === 'ASC' ? ' ↑' : ' ↓') : ''}
                                </span>
                              </button>
                            )}

                            {/* Código */}
                            {isColVis('code') && (
                              <button
                                type="button"
                                onClick={() => handleConvSort('code')}
                                className="w-[95px] h-full px-3 flex items-center justify-center border-r border-[#E5ECF5] dark:border-[#24385E] text-[12.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer group shrink-0"
                              >
                                <span>
                                  Código{convSortCol === 'code' ? (convSortDir === 'ASC' ? ' ↑' : ' ↓') : ''}
                                </span>
                              </button>
                            )}

                            {/* Marca */}
                            {isColVis('brand') && (
                              <button
                                type="button"
                                onClick={() => handleConvSort('brand')}
                                className="w-[125px] h-full px-3 flex items-center border-r border-[#E5ECF5] dark:border-[#24385E] text-[12.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer group text-left shrink-0"
                              >
                                <span className="truncate">
                                  Marca{convSortCol === 'brand' ? (convSortDir === 'ASC' ? ' ↑' : ' ↓') : ''}
                                </span>
                              </button>
                            )}

                            {/* Categoria */}
                            {isColVis('category') && (
                              <button
                                type="button"
                                onClick={() => handleConvSort('category')}
                                className="w-[125px] h-full px-3 flex items-center border-r border-[#E5ECF5] dark:border-[#24385E] text-[12.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer group text-left shrink-0"
                              >
                                <span className="truncate">
                                  Categoria{convSortCol === 'category' ? (convSortDir === 'ASC' ? ' ↑' : ' ↓') : ''}
                                </span>
                              </button>
                            )}

                            {/* Unidade */}
                            {isColVis('unit') && (
                              <button
                                type="button"
                                onClick={() => handleConvSort('unit')}
                                className="w-[85px] h-full px-3 flex items-center justify-center border-r border-[#E5ECF5] dark:border-[#24385E] text-[12.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer group shrink-0"
                              >
                                <span>
                                  Un.{convSortCol === 'unit' ? (convSortDir === 'ASC' ? ' ↑' : ' ↓') : ''}
                                </span>
                              </button>
                            )}

                            {/* Unidade Personalizada */}
                            {isColVis('unit_name') && (
                              <button
                                type="button"
                                onClick={() => handleConvSort('unit_name')}
                                className="flex-1 h-full px-3.5 flex items-center border-r border-[#E5ECF5] dark:border-[#24385E] text-[12.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer group text-left min-w-0"
                              >
                                <span className="truncate">
                                  Unidade Personalizada{convSortCol === 'unit_name' ? (convSortDir === 'ASC' ? ' ↑' : ' ↓') : ''}
                                </span>
                              </button>
                            )}

                            {/* Equivalência Base */}
                            {isColVis('equivalence') && (
                              <button
                                type="button"
                                onClick={() => handleConvSort('equivalence')}
                                className="flex-[1.2] h-full px-3.5 flex items-center border-r border-[#E5ECF5] dark:border-[#24385E] text-[12.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer group text-left min-w-0"
                              >
                                <span className="truncate">
                                  Equivalência Base{convSortCol === 'equivalence' ? (convSortDir === 'ASC' ? ' ↑' : ' ↓') : ''}
                                </span>
                              </button>
                            )}
                          </div>

                          {/* Right Fixed Gear Column Header Oficial Nexo (90px) */}
                          <div
                            ref={convColMenuRef}
                            className="w-[90px] h-full flex items-center justify-end pr-3 shrink-0 sticky right-0 bg-[#EEF4FB] dark:bg-[#142544] rounded-r-full border-l border-[#E5ECF5] dark:border-[#24385E] z-30 relative"
                          >
                            <button
                              type="button"
                              onClick={() => setConvColMenuOpen((o) => !o)}
                              title="Exibir / ocultar colunas"
                              className="w-[28px] h-[28px] rounded-full flex items-center justify-center text-[#60769D] dark:text-[#AFC0E2] hover:text-[#F28C28] dark:hover:text-[#F28C28] transition-colors cursor-pointer"
                            >
                              <GearPolygonIcon
                                size={16}
                                strokeColor="currentColor"
                                centerFill={dark ? '#142544' : '#EEF4FB'}
                              />
                            </button>

                            {/* Menu Flutuante de Exibir Colunas */}
                            {convColMenuOpen && (
                              <div className="absolute right-0 top-[38px] w-[200px] rounded-[14px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-xl py-2 z-50">
                                <div className="px-3.5 pb-1.5 text-[10.5px] font-bold tracking-wider text-[#A0ABB9] uppercase">
                                  Exibir Colunas
                                </div>
                                {[
                                  { key: 'material_name', label: 'Insumo' },
                                  { key: 'code', label: 'Código' },
                                  { key: 'brand', label: 'Marca' },
                                  { key: 'category', label: 'Categoria' },
                                  { key: 'unit', label: 'Unidade' },
                                  { key: 'unit_name', label: 'Unidade Personalizada' },
                                  { key: 'equivalence', label: 'Equivalência Base' },
                                ].map((col) => {
                                  const isVis = isColVis(col.key);
                                  return (
                                    <div
                                      key={col.key}
                                      onClick={() => toggleConvColumnVisibility(col.key)}
                                      className="w-full px-3 py-1.5 flex items-center gap-2 hover:bg-[#EEF4FB] dark:hover:bg-[#172746] text-left transition-colors cursor-pointer select-none"
                                    >
                                      <NexoCheckbox
                                        checked={isVis}
                                        onChange={() => toggleConvColumnVisibility(col.key)}
                                      />
                                      <span
                                        className={`text-[12.5px] ${
                                          isVis
                                            ? 'text-[#18223A] dark:text-[#F4F7FF] font-medium'
                                            : 'text-[#687796] dark:text-[#93A4C6]'
                                        }`}
                                      >
                                        {col.label}
                                      </span>
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Table Rows com separador e altura padronizada Nexo (38px) */}
                        <div className="divide-y divide-[#F0F4FA] dark:divide-[#17294A]">
                          {sorted.map((item) => {
                            const isSelected = selectedConversionIds.has(item.id);
                            const rowBg = isSelected
                              ? 'bg-[#FFF0D8] dark:bg-[#5A3518]'
                              : 'bg-white dark:bg-[#0E1B35] hover:bg-[#F8FAFD] dark:hover:bg-[#132342]';

                            return (
                              <div
                                key={item.id}
                                onClick={() => {
                                  const next = new Set(selectedConversionIds);
                                  if (isSelected) next.delete(item.id);
                                  else next.add(item.id);
                                  setSelectedConversionIds(next);
                                }}
                                onDoubleClick={() => handleOpenEditConversion(item)}
                                className={`h-[38px] flex items-center transition-colors group cursor-pointer ${rowBg} text-[#18223A] dark:text-[#F4F7FF]`}
                              >
                                {/* Left Checkbox Cell (60px) */}
                                <div
                                  className="w-[60px] h-full flex items-center justify-center shrink-0"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <NexoCheckbox
                                    checked={isSelected}
                                    onChange={() => {
                                      const next = new Set(selectedConversionIds);
                                      if (isSelected) next.delete(item.id);
                                      else next.add(item.id);
                                      setSelectedConversionIds(next);
                                    }}
                                  />
                                </div>

                                {/* Insumo */}
                                {isColVis('material_name') && (
                                  <div className="flex-[1.4] px-3.5 flex items-center overflow-hidden min-w-0">
                                    <span className="font-semibold text-[13px] truncate">{item.material_name}</span>
                                  </div>
                                )}

                                {/* Código */}
                                {isColVis('code') && (
                                  <div className="w-[95px] px-3 flex items-center justify-center font-mono text-[12px] text-[#60769D] dark:text-[#93A4C6] shrink-0">
                                    {item.material_code || '-'}
                                  </div>
                                )}

                                {/* Marca */}
                                {isColVis('brand') && (
                                  <div className="w-[125px] px-3 flex items-center text-[12.5px] text-[#475569] dark:text-[#CBD5E1] shrink-0 truncate">
                                    {item.material_brand || '-'}
                                  </div>
                                )}

                                {/* Categoria */}
                                {isColVis('category') && (
                                  <div className="w-[125px] px-3 flex items-center text-[12.5px] text-[#475569] dark:text-[#CBD5E1] shrink-0 truncate">
                                    {item.material_category || '-'}
                                  </div>
                                )}

                                {/* Unidade do Insumo */}
                                {isColVis('unit') && (
                                  <div className="w-[85px] px-3 flex items-center justify-center text-[12.5px] font-medium text-[#475569] dark:text-[#CBD5E1] shrink-0">
                                    {item.material_unit || item.base_unit}
                                  </div>
                                )}

                                {/* Unidade Personalizada */}
                                {isColVis('unit_name') && (
                                  <div className="flex-1 px-3.5 flex items-center overflow-hidden min-w-0">
                                    <span className="font-medium text-[13px] text-[#18223A] dark:text-[#F4F7FF] truncate">
                                      {item.unit_name}
                                    </span>
                                  </div>
                                )}

                                {/* Equivalência Base */}
                                {isColVis('equivalence') && (
                                  <div className="flex-[1.2] px-3.5 text-[12.5px] text-[#475569] dark:text-[#CBD5E1] truncate min-w-0">
                                    1 {item.unit_name} = <strong className="text-[#18223A] dark:text-white font-bold">{item.factor_fmt} {item.base_unit}</strong>
                                  </div>
                                )}

                                {/* Right Actions (90px) com os Ícones Oficiais do Nexo alinhados sob a engrenagem */}
                                <div
                                  className="w-[90px] h-full flex items-center justify-end pr-2.5 gap-1.5 shrink-0"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  {/* Edit Button */}
                                  <button
                                    type="button"
                                    onClick={() => handleOpenEditConversion(item)}
                                    title="Editar"
                                    className="w-[28px] h-[28px] rounded-full flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer transition-colors"
                                  >
                                    <img
                                      src="/ui_assets/action_edit_reference_exact.png"
                                      alt="Editar"
                                      className="w-4 h-4 object-contain"
                                    />
                                  </button>

                                  {/* Delete Button */}
                                  <button
                                    type="button"
                                    onClick={() => handleDeleteConversion(item.id)}
                                    title="Excluir"
                                    className="w-[28px] h-[28px] rounded-full flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer transition-colors"
                                  >
                                    <img
                                      src="/ui_assets/action_delete_reference_exact.png"
                                      alt="Excluir"
                                      className="w-4 h-4 object-contain"
                                    />
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
            </div>

            {/* Rodapé da Janela */}
            <div className="flex items-center justify-between border-t border-[#F0F4FA] dark:border-[#1E3156] pt-3 shrink-0">
              <span className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
                Todas as alterações são sincronizadas imediatamente com a tabela de insumos e receitas.
              </span>
              <RoundedActionButton
                label="Fechar Janela"
                onClick={() => {
                  setShowCustomUnitsModal(false);
                  setSelectedConversionIds(new Set());
                }}
                variant="primary"
                height={36}
              />
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* SUB-MODAL: ADICIONAR / EDITAR UNIDADE CONFIGURÁVEL */}
      {/* ========================================================= */}
      {showEditConvModal && (
        <div
          className="fixed inset-0 z-[100] bg-[#0B132B]/70 backdrop-blur-xs flex items-center justify-center p-4"
          style={{ zIndex: 100 }}
        >
          <div
            className="w-full max-w-md rounded-[24px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-5 space-y-4"
            style={{ zIndex: 101 }}
          >
            
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
              <div>
                <h4 className="text-[15px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  {editingConvId ? 'Editar Unidade Configurável' : 'Nova Unidade por Insumo'}
                </h4>
              </div>
              <button
                type="button"
                onClick={() => setShowEditConvModal(false)}
                className="w-7 h-7 rounded-full bg-[#F0F4FA] dark:bg-[#1C2C4E] hover:bg-[#E2EAF5] dark:hover:bg-[#253966] text-[#60769D] dark:text-[#93A4C6] flex items-center justify-center text-xs font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Campos */}
            <div className="space-y-3">
              {/* Insumo */}
              <div>
                <label className="block text-[11.5px] font-bold text-[#60769D] dark:text-[#93A4C6] mb-1">
                  Insumo
                </label>
                {editingConvId ? (
                  <div className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-[#F4F7FC] dark:bg-[#142340] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3.5 flex items-center">
                    {convMaterialName}
                  </div>
                ) : (
                  <select
                    value={convMaterialId}
                    onChange={(e) => {
                      const mid = Number(e.target.value);
                      setConvMaterialId(mid);
                      const m = availableMaterials.find((x) => x.id === mid);
                      if (m && m.purchase_unit) {
                        setConvBaseUnit(m.purchase_unit);
                      }
                    }}
                    className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                  >
                    {availableMaterials.map((mat) => (
                      <option key={mat.id} value={mat.id}>
                        {mat.name} ({mat.purchase_unit || 'un'})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Nome da Unidade */}
              <div>
                <label className="block text-[11.5px] font-bold text-[#60769D] dark:text-[#93A4C6] mb-1">
                  Nome da Unidade Criada
                </label>
                <input
                  type="text"
                  value={convUnitName}
                  onChange={(e) => setConvUnitName(e.target.value)}
                  placeholder="Ex: Xícara de chá, Colher de sopa, Lata, Pote..."
                  className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                />
              </div>

              {/* Fator e Unidade Base */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11.5px] font-bold text-[#60769D] dark:text-[#93A4C6] mb-1">
                    Equivale a (Quantidade)
                  </label>
                  <input
                    type="text"
                    value={convFactor}
                    onChange={(e) => setConvFactor(e.target.value.replace(/[^0-9.,]/g, ''))}
                    placeholder="Ex: 240, 15, 395..."
                    className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3.5 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                  />
                </div>

                <div>
                  <label className="block text-[11.5px] font-bold text-[#60769D] dark:text-[#93A4C6] mb-1">
                    Unidade de Medida
                  </label>
                  <select
                    value={convBaseUnit}
                    onChange={(e) => setConvBaseUnit(e.target.value)}
                    className="w-full h-[36px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3 focus:outline-none focus:ring-2 focus:ring-[#F28C28]"
                  >
                    <option value="g">Gramas (g)</option>
                    <option value="kg">Quilos (kg)</option>
                    <option value="ml">Mililitros (ml)</option>
                    <option value="l">Litros (l)</option>
                    <option value="un">Unidade (un)</option>
                  </select>
                </div>
              </div>

              {/* Preview da Regra */}
              {convUnitName.trim() && convFactor.trim() && (
                <div className="p-2.5 rounded-[14px] bg-[#FFF8EE] dark:bg-[#1F170D] border border-[#F28C28]/25 text-[12px] text-[#BA5200] dark:text-[#F28C28] text-center font-bold">
                  1 {convUnitName} = {convFactor} {convBaseUnit}
                </div>
              )}
            </div>

            {/* Ações */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#F0F4FA] dark:border-[#1E3156]">
              <button
                type="button"
                onClick={() => setShowEditConvModal(false)}
                className="px-4 py-2 rounded-full text-[12.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] hover:bg-[#F0F4FA] dark:hover:bg-[#1C2C4E] transition-colors cursor-pointer"
              >
                Cancelar
              </button>
              <RoundedActionButton
                label={savingConv ? 'Salvando...' : 'Salvar Unidade'}
                onClick={handleSaveConversionForm}
                variant="primary"
                height={36}
              />
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
