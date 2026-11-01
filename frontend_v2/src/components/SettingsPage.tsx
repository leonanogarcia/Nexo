import React, { useState, useEffect } from 'react';
import {
  RoundedActionButton,
  CapsuleInput,
  RoundedDropdown,
  NexoCheckbox,
} from './DesignSystem';

export interface SettingsPageProps {
  onNotify: (msg: string, type?: 'success' | 'warning' | 'error') => void;
  dark: boolean;
  onThemeToggle: (isDark: boolean) => void;
}

type SettingsCategoryKey = 'geral' | 'ia' | 'metricas' | 'unidades' | 'banco';

// --- Clean Monochrome Vector Icons (Design System Nexo) ---

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

export const TrendingCostsIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
    <polyline points="17 6 23 6 23 12" />
  </svg>
);

export const RulerUnitsIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21.3 8.7 8.7 21.3c-1 1-2.5 1-3.4 0l-2.6-2.6c-1-1-1-2.5 0-3.4L15.3 2.7c1-1 2.5-1 3.4 0l2.6 2.6c1 1 1 2.5 0 3.4Z" />
    <path d="m14.5 3.5 2 2" />
    <path d="m11.5 6.5 3 3" />
    <path d="m8.5 9.5 2 2" />
    <path d="m5.5 12.5 3 3" />
  </svg>
);

export const ScalesUnitsIcon = RulerUnitsIcon;

export const DatabaseBiIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="9" ry="3" />
    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
  </svg>
);

export const BuildingCompanyIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="13.5" cy="6.5" r=".5" fill="currentColor" />
    <circle cx="17.5" cy="10.5" r=".5" fill="currentColor" />
    <circle cx="8.5" cy="7.5" r=".5" fill="currentColor" />
    <circle cx="6.5" cy="12.5" r=".5" fill="currentColor" />
    <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.03-.23-.29-.38-.64-.38-1.02 0-.83.67-1.5 1.5-1.5H16c3.31 0 6-2.69 6-6 0-5.5-4.5-9.95-10-9.95z" />
  </svg>
);

export const GlobeLanguageIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="2" y1="12" x2="22" y2="12" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </svg>
);

interface SettingsTabSpec {
  key: SettingsCategoryKey;
  label: string;
  icon: React.ReactNode;
}

const SETTINGS_TABS: SettingsTabSpec[] = [
  { key: 'geral', label: 'Geral', icon: <CogSettingsIcon className="w-[19px] h-[19px] shrink-0" /> },
  { key: 'ia', label: 'Inteligência Artificial', icon: <AiChipIcon className="w-[22px] h-[22px] shrink-0" /> },
  { key: 'metricas', label: 'Métricas de Custo', icon: <TrendingCostsIcon className="w-[19px] h-[19px] shrink-0" /> },
  { key: 'unidades', label: 'Unidades de Medida', icon: <ScalesUnitsIcon className="w-[19px] h-[19px] shrink-0" /> },
  { key: 'banco', label: 'Banco de Dados & BI', icon: <DatabaseBiIcon className="w-[19px] h-[19px] shrink-0" /> },
];

export const SettingsPage: React.FC<SettingsPageProps> = ({
  onNotify,
  dark,
  onThemeToggle,
}) => {
  const [activeTab, setActiveTab] = useState<SettingsCategoryKey>('geral');
  const [loading, setLoading] = useState(true);

  // --- Categoria 1: Geral ---
  const [companyName, setCompanyName] = useState('Nexo');
  const [companyLogo, setCompanyLogo] = useState('');
  const [themeMode, setThemeMode] = useState<'light' | 'dark' | 'system'>(dark ? 'dark' : 'light');
  const [language, setLanguage] = useState('Português (Brasil)');
  const [savingCompany, setSavingCompany] = useState(false);

  // --- Categoria 2: IA ---
  const [aiEnabled, setAiEnabled] = useState(false);
  const [aiProvider, setAiProvider] = useState('Google Gemini');
  const [aiApiKey, setAiApiKey] = useState('');
  const [aiDailyLimit, setAiDailyLimit] = useState('50');
  const [showAiHelpModal, setShowAiHelpModal] = useState(false);
  const [savingAi, setSavingAi] = useState(false);

  // --- Categoria 3: Métricas de Custo ---
  const [gasPct, setGasPct] = useState('20.0');
  const [energyPct, setEnergyPct] = useState('20.0');
  const [waterPct, setWaterPct] = useState('20.0');
  const [savingCosts, setSavingCosts] = useState(false);

  // --- Categoria 4: Unidades de Medida ---
  const [massBaseUnit, setMassBaseUnit] = useState('mg');
  const [volumeBaseUnit, setVolumeBaseUnit] = useState('ml');
  const [countBaseUnit, setCountBaseUnit] = useState('un');
  const [savingUnits, setSavingUnits] = useState(false);

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
      setThemeMode(data.theme === 'dark' ? 'dark' : 'light');

      // Custos operacionais
      if (data.cost_settings && Array.isArray(data.cost_settings)) {
        const g = data.cost_settings.find((c: any) => c.name.toLowerCase().includes('g'));
        const e = data.cost_settings.find((c: any) => c.name.toLowerCase().includes('energia'));
        const w = data.cost_settings.find((c: any) => c.name.toLowerCase().includes('gua'));
        if (g) setGasPct(String(g.percentage));
        if (e) setEnergyPct(String(e.percentage));
        if (w) setWaterPct(String(w.percentage));
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
  }, []);

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
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        setCompanyLogo(reader.result);
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
      const res = await fetch('/api/settings/company', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: companyName.trim(), logo: companyLogo }),
      });
      if (!res.ok) throw new Error('Falha ao salvar dados da empresa.');
      onNotify('Identidade da empresa salva com sucesso!', 'success');
    } catch (e: any) {
      onNotify(e.message || 'Erro ao salvar identidade da empresa.', 'error');
    } finally {
      setSavingCompany(false);
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
      onNotify('Configurações de Inteligência Artificial salvas com sucesso!', 'success');
    } catch (e: any) {
      onNotify(e.message || 'Erro ao salvar configurações de IA.', 'error');
    } finally {
      setSavingAi(false);
    }
  };

  // --- Handlers: Métricas de Custo ---
  const handleSaveCosts = async () => {
    setSavingCosts(true);
    try {
      const gVal = parseFloat(gasPct.replace(',', '.')) || 0;
      const eVal = parseFloat(energyPct.replace(',', '.')) || 0;
      const wVal = parseFloat(waterPct.replace(',', '.')) || 0;

      const costsPayload = [
        { name: 'Gás', percentage: gVal },
        { name: 'Energia', percentage: eVal },
        { name: 'Água', percentage: wVal },
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

  const totalOperational = (
    (parseFloat(gasPct.replace(',', '.')) || 0) +
    (parseFloat(energyPct.replace(',', '.')) || 0) +
    (parseFloat(waterPct.replace(',', '.')) || 0)
  ).toFixed(1);

  if (loading) {
    return (
      <div className="flex-1 w-full rounded-[22px] bg-white dark:bg-[#111F3B] p-8 flex items-center justify-center text-[#687796] dark:text-[#93A4C6] text-[13px]">
        Carregando configurações...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full min-h-0">
      {/* 1. Header Toolbar */}
      <div className="h-[64px] w-full rounded-[22px] bg-white dark:bg-[#111F3B] px-6 mb-3 flex items-center justify-between shrink-0 shadow-sm transition-colors">
        <div>
          <h2 className="text-[17px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
            Configurações
          </h2>
          <p className="text-[12px] text-[#60769D] dark:text-[#AFC0E2]">
            Preferências, dados e parâmetros do Nexo
          </p>
        </div>
      </div>

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
              {/* Painel: Empresa */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-4 transition-colors">
                <div className="flex items-center gap-2 border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                  <BuildingCompanyIcon className="w-4 h-4 text-[#60769D] dark:text-[#AFC0E2]" />
                  <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Empresa
                  </h3>
                </div>

                <div className="grid grid-cols-12 gap-3 items-end">
                  <div className="col-span-5">
                    <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                      Nome da empresa
                    </label>
                    <CapsuleInput
                      value={companyName}
                      onChange={setCompanyName}
                      placeholder="Ex: Minha Confeitaria"
                    />
                  </div>

                  <div className="col-span-4">
                    <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                      Logo
                    </label>
                    <div className="flex items-center gap-2">
                      <div className="w-9 h-9 rounded-[10px] bg-[#F4F7FC] dark:bg-[#142340] border border-[#DDE5F2] dark:border-[#24385E] flex items-center justify-center overflow-hidden shrink-0">
                        {companyLogo ? (
                          <img src={companyLogo} alt="Logo" className="w-full h-full object-contain" />
                        ) : (
                          <span className="text-[10px] text-[#8C9BB5]">Sem logo</span>
                        )}
                      </div>
                      <label className="inline-flex items-center justify-center px-3 h-[34px] rounded-full text-[12px] font-semibold bg-[#EEF4FB] dark:bg-[#1C2C4E] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#E2EAF5] dark:hover:bg-[#253963] cursor-pointer transition-colors">
                        <span>Selecionar</span>
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
                          className="text-[11.5px] text-[#DC2626] dark:text-[#F87171] hover:underline"
                        >
                          Remover
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="col-span-3 flex justify-end">
                    <RoundedActionButton
                      label={savingCompany ? 'Salvando...' : 'Salvar identidade'}
                      onClick={handleSaveCompany}
                      variant="primary"
                      height={34}
                    />
                  </div>
                </div>

                <p className="text-[11.5px] text-[#8C9BB5] dark:text-[#64748B]">
                  Formatos aceitos: PNG, JPG/JPEG, GIF, BMP, WebP. Mínimo recomendado: 500 px no menor lado.
                </p>
              </div>

              {/* Painel: Aparência */}
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-3.5 transition-colors">
                <div className="flex items-center gap-2 border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                  <PaletteAppearanceIcon className="w-4 h-4 text-[#60769D] dark:text-[#AFC0E2]" />
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
                  <GlobeLanguageIcon className="w-4 h-4 text-[#60769D] dark:text-[#AFC0E2]" />
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
              <div className="flex items-center gap-2.5 border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                <AiChipIcon className="w-6 h-6 text-[#BA5200] dark:text-[#F28C28]" />
                <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  Sincronismo de Inteligência Artificial
                </h3>
              </div>

              {/* Linha 1: Ativação & Provedor */}
              <div className="flex flex-wrap items-center gap-6">
                <label className="flex items-center gap-2.5 cursor-pointer select-none">
                  <NexoCheckbox checked={aiEnabled} onChange={() => setAiEnabled(!aiEnabled)} />
                  <span className="text-[13px] font-semibold text-[#18223A] dark:text-[#F4F7FF]">
                    Ativar Importação Inteligente (IA)
                  </span>
                </label>

                <div className="flex items-center gap-2">
                  <span className="text-[12px] font-semibold text-[#60769D] dark:text-[#93A4C6]">
                    Provedor:
                  </span>
                  <div className="w-[180px]">
                    <RoundedDropdown
                      value={aiProvider}
                      onChange={setAiProvider}
                      options={['Google Gemini', 'OpenAI ChatGPT']}
                      width={180}
                      height={34}
                      disabled={!aiEnabled}
                    />
                  </div>
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
                <div className="pt-5">
                  <RoundedActionButton
                    label="Ajuda (i)"
                    onClick={() => setShowAiHelpModal(true)}
                    variant="secondary"
                    height={34}
                  />
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
            <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-4 transition-colors">
              <div className="flex items-center gap-2 border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                <TrendingCostsIcon className="w-4 h-4 text-[#60769D] dark:text-[#AFC0E2]" />
                <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  Custos operacionais
                </h3>
              </div>

              <div className="grid grid-cols-4 gap-3 items-end">
                <div>
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                    Gás (%)
                  </label>
                  <CapsuleInput
                    value={gasPct}
                    onChange={(v) => setGasPct(v.replace(/[^0-9.,]/g, ''))}
                    placeholder="20"
                  />
                </div>

                <div>
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                    Energia (%)
                  </label>
                  <CapsuleInput
                    value={energyPct}
                    onChange={(v) => setEnergyPct(v.replace(/[^0-9.,]/g, ''))}
                    placeholder="20"
                  />
                </div>

                <div>
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                    Água (%)
                  </label>
                  <CapsuleInput
                    value={waterPct}
                    onChange={(v) => setWaterPct(v.replace(/[^0-9.,]/g, ''))}
                    placeholder="20"
                  />
                </div>

                <div className="flex justify-end">
                  <RoundedActionButton
                    label={savingCosts ? 'Salvando...' : 'Salvar custos'}
                    onClick={handleSaveCosts}
                    variant="primary"
                    height={34}
                  />
                </div>
              </div>

              <div className="p-3 rounded-[16px] bg-[#FFF8EE] dark:bg-[#1C1710] border border-[#F28C28]/30 flex items-center justify-between">
                <span className="text-[12px] font-semibold text-[#18223A] dark:text-[#F4F7FF]">
                  Esses percentuais entram no custo final do Produto e ficam registrados no histórico.
                </span>
                <span className="text-[13.5px] font-extrabold text-[#F28C28]">
                  Total: {totalOperational}%
                </span>
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
                  <ScalesUnitsIcon className="w-4 h-4 text-[#60769D] dark:text-[#AFC0E2]" />
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
              <div className="rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] p-5 shadow-sm space-y-3 transition-colors">
                <div className="flex items-center gap-2 border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
                  <span className="text-base">🥄</span>
                  <h3 className="text-[14px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Unidades configuráveis por insumo
                  </h3>
                </div>

                <p className="text-[12px] text-[#60769D] dark:text-[#AFC0E2]">
                  Ex.: xícara de leite pode equivaler a 240 ml; xícara de farinha pode equivaler a outro valor.
                </p>

                <div>
                  <span className="text-[12px] font-semibold text-[#18223A] dark:text-[#F4F7FF]">
                    Gerenciado diretamente na tabela de Insumos e no botão de Conversões da aba Receitas.
                  </span>
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
                  <DatabaseBiIcon className="w-4 h-4 text-[#60769D] dark:text-[#AFC0E2]" />
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
                    <DatabaseBiIcon className="w-4 h-4 text-[#60769D] dark:text-[#AFC0E2]" />
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

      {/* Modal de Ajuda da IA */}
      {showAiHelpModal && (
        <div className="fixed inset-0 bg-black/45 backdrop-blur-[1px] flex items-center justify-center z-50">
          <div className="w-[500px] rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col space-y-4">
            <h3 className="text-[16px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              Ajuda: Chave de API
            </h3>
            <div className="text-[12.5px] text-[#475569] dark:text-[#CBD5E1] space-y-3 leading-relaxed">
              <div className="p-3 rounded-[14px] bg-[#F4F7FC] dark:bg-[#142340]">
                <strong className="block text-[#18223A] dark:text-[#F4F7FF] mb-1">Para Google Gemini:</strong>
                1. Acesse aistudio.google.com<br />
                2. Faça login com o Google<br />
                3. Clique em "Get API Key" e "Create API Key"<br />
                4. Cole o código gerado no campo.
              </div>
              <div className="p-3 rounded-[14px] bg-[#F4F7FC] dark:bg-[#142340]">
                <strong className="block text-[#18223A] dark:text-[#F4F7FF] mb-1">Para OpenAI ChatGPT:</strong>
                1. Acesse platform.openai.com/api-keys<br />
                2. Faça login e crie sua secret key.
              </div>
            </div>
            <div className="flex justify-end pt-2 border-t border-[#E2EAF5] dark:border-[#1E3156]">
              <RoundedActionButton
                label="Fechar"
                onClick={() => setShowAiHelpModal(false)}
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
