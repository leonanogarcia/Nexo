import React, { useEffect, useState } from 'react';
import {
  AnimatedSuccessModal,
  FeedbackType,
  ReferenceSidebar,
  RoundedActionButton,
} from './components/DesignSystem';
import { MaterialsPage } from './components/MaterialsPage';
import { RecipesPage } from './components/RecipesPage';
import { ProductsPage } from './components/ProductsPage';
import { NavKey, SystemStatus } from './types';

interface PageHeaderMeta {
  title: string;
  subtitle: string;
  cardTitle?: string;
  cardDescription?: string;
  buttonLabel?: string;
}

const PAGE_HEADERS: Record<NavKey, PageHeaderMeta> = {
  Geral: {
    title: 'Início',
    subtitle: 'Visão geral do seu negócio',
    cardTitle: 'Início — Painel de Gestão e BI',
    cardDescription:
      'Esta aba será desenvolvida na Etapa 4, reunindo os KPIs estratégicos do seu negócio, faturamento, custos médios e gráficos de rosca interativos.',
    buttonLabel: 'Ir para Produtos',
  },
  Cadastro: {
    title: 'Cadastro',
    subtitle: 'Gerencie insumos, compras e fornecedores',
  },
  Receitas: {
    title: 'Receitas',
    subtitle: 'Monte e acompanhe o custo das receitas base',
  },
  Produtos: {
    title: 'Produtos',
    subtitle: 'Custos, composição e precificação dos produtos',
    cardTitle: 'Produtos — Próxima fase da Etapa 2',
    cardDescription:
      'Esta aba é a Parte 2 da Etapa 2. Ela trará a precificação de venda, composição com embalagens e cálculo de margem de lucro, e será construída logo após lapidarmos e aprovarmos a Aba de Receitas Base.',
    buttonLabel: 'Ir para Produtos',
  },
  Configurações: {
    title: 'Configurações',
    subtitle: 'Preferências, dados e parâmetros do Nexo',
    cardTitle: 'Configurações — Próxima Fase (Etapa 3)',
    cardDescription:
      'Esta aba será desenvolvida na Etapa 3 (seleção de tema Claro/Escuro definitivo, dados da empresa, taxas de gás/luz/água e backup).',
    buttonLabel: 'Ir para Produtos',
  },
};

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<NavKey>('Geral');
  const [status, setStatus] = useState<SystemStatus>({
    connected: true,
    db_name: 'nexo.db',
    db_path: '',
    theme: 'light',
    company_name: 'Nexo',
    units: ['mg', 'g', 'kg', 't', 'ml', 'L', 'kL', 'un'],
    mat_hidden_cols: ['code'],
    version: 'v1.4.0',
  });
  const [dark, setDark] = useState(false);
  const [toast, setToast] = useState<{ message: string; type?: FeedbackType } | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/status');
        if (res.ok) {
          const data: SystemStatus = await res.json();
          setStatus(data);
          const isDark = data.theme === 'dark';
          setDark(isDark);
          document.documentElement.classList.toggle('dark', isDark);
        }
      } catch (e) {
        console.error('Falha ao carregar status inicial:', e);
      } finally {
        setLoaded(true);
      }
    })();
  }, []);

  const toggleTheme = async () => {
    const nextDark = !dark;
    setDark(nextDark);
    document.documentElement.classList.toggle('dark', nextDark);
    try {
      await fetch('/api/settings/theme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: nextDark ? 'dark' : 'light' }),
      });
    } catch (e) {
      console.error(e);
    }
  };

  const notify = (msg: string, type: FeedbackType = 'success') => {
    let finalType = type;
    const lower = msg.toLowerCase();
    if (
      type === 'success' &&
      (lower.includes('selecione') ||
        lower.includes('atenção') ||
        lower.includes('aviso') ||
        lower.includes('inativo'))
    ) {
      finalType = 'warning';
    }
    setToast({ message: msg, type: finalType });
  };

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3200);
    return () => clearTimeout(t);
  }, [toast]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F5' || (e.ctrlKey && e.key.toLowerCase() === 'r')) {
        e.preventDefault();
        window.location.reload();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const headerInfo = PAGE_HEADERS[activePage];

  return (
    <div className="w-screen h-screen flex bg-[#F4F7FC] dark:bg-[#081226] text-[#18223A] dark:text-[#F4F7FF] transition-colors duration-200 overflow-hidden">
      {/* Left Floating Capsule Sidebar (150px dedicated width) */}
      <ReferenceSidebar active={activePage} onSelect={setActivePage} dark={dark} />

      {/* Main Content Area */}
      <main className="flex-1 h-full flex flex-col min-w-0 pr-6">
        {/* Clean Header (padx=18, pady=(32,14)) */}
        <header className="pt-8 pb-3.5 px-4 flex items-center justify-between shrink-0">
          <div>
            <h1 className="text-[30px] leading-tight font-bold text-[#18223A] dark:text-[#F4F7FF]">
              {headerInfo.title}
            </h1>
            <p className="text-[13.5px] text-[#687796] dark:text-[#93A4C6] mt-0.5">
              {headerInfo.subtitle}
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Quick Reload Button */}
            <button
              type="button"
              onClick={() => window.location.reload()}
              title="Recarregar tela (F5)"
              className="h-[34px] px-3.5 rounded-full bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] text-[12.5px] font-bold text-[#687796] dark:text-[#93A4C6] hover:text-[#BA5200] hover:border-[#F28C28] flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
            >
              <span>🔄 Recarregar</span>
            </button>
          </div>
        </header>

        {/* Body Area */}
        <div className="flex-1 min-h-0 relative flex flex-col pb-2">
          {/* Animated Feedback Modal (HUD central: Sucesso, Aviso e Erro) */}
          {toast && (
            <AnimatedSuccessModal
              message={toast.message}
              type={toast.type}
              onClose={() => setToast(null)}
            />
          )}

          {loaded && activePage === 'Cadastro' && (
            <MaterialsPage
              units={status.units}
              initialHiddenCols={status.mat_hidden_cols}
              onNotify={notify}
              dark={dark}
            />
          )}

          {loaded && activePage === 'Receitas' && (
            <RecipesPage
              units={status.units}
              initialHiddenCols={status.rec_hidden_cols || ['code']}
              onNotify={notify}
              dark={dark}
            />
          )}

          {loaded && activePage === 'Produtos' && (
            <ProductsPage
              units={status.units}
              initialHiddenCols={(status as any).prod_hidden_cols || ['code']}
              onNotify={notify}
              dark={dark}
            />
          )}

          {loaded && activePage !== 'Cadastro' && activePage !== 'Receitas' && activePage !== 'Produtos' && (
            <div className="flex-1 rounded-[22px] bg-white dark:bg-[#111F3B] p-8 flex flex-col items-center justify-center text-center shadow-sm">
              <div className="w-14 h-14 rounded-full bg-[#FFF0D8] dark:bg-[#5A3518] text-[#F28C28] flex items-center justify-center text-2xl font-bold mb-4">
                ✨
              </div>
              <h2 className="text-[20px] font-bold text-[#18223A] dark:text-[#F4F7FF] mb-2">
                {headerInfo.cardTitle || `${headerInfo.title} — Em breve no cronograma`}
              </h2>
              <p className="text-[14px] text-[#687796] dark:text-[#93A4C6] max-w-lg mb-6 leading-relaxed">
                {headerInfo.cardDescription}
              </p>
              <RoundedActionButton
                label={headerInfo.buttonLabel || 'Ir para Receitas'}
                onClick={() => setActivePage('Receitas')}
                variant="primary"
                height={42}
              />
            </div>
          )}
        </div>

        {/* Footer Status Bar */}
        <footer className="h-[26px] px-2 pb-1.5 flex items-center justify-between text-[11px] text-[#60769D] dark:text-[#93A4C6] shrink-0 select-none">
          <span>
            Banco de dados: {status.connected ? 'Conectado ✓' : 'Desconectado ✕'} · {status.db_name}
          </span>
          <span>Nexo · Gestão de Custos e Precificação · v1.4.0 (Etapa 2.2: Produtos)</span>
        </footer>
      </main>
    </div>
  );
};
