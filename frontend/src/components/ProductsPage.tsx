import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertTriangleIcon,
  CapsuleInput,
  CapsuleQuantityUnit,
  ClockIcon,
  ColumnResizeHandle,
  DuplicateIcon,
  EditPencilIcon,
  GearPolygonIcon,
  NexoCheckbox,
  NexoEmptyStateIcon,
  NexoEmptyTableWatermark,
  NexoToolbarOverflowMenu,
  PaperclipIcon,
  PlusIcon,
  RoundedActionButton,
  RoundedDropdown,
  RoundedEntry,
  TrashIcon,
  FlameIcon,
  ZapEnergyIcon,
  DropletWaterIcon,
  useNexoColumnWidths,
  useToolbarOverflow,
} from './DesignSystem';
import { DocumentAttachmentsModal } from './DocumentAttachmentsModal';
import { AiParsedRecipeResult, AiRecipePreviewModal, QuickCreateMaterialModal } from './AiPreviewModals';

interface ProductsPageProps {
  units: string[];
  initialHiddenCols?: string[];
  onNotify: (msg: string, type?: 'success' | 'warning' | 'error') => void;
  dark: boolean;
  aiEnabled?: boolean;
}

export interface ProductItem {
  id: number;
  code: string;
  name: string;
  weight_qty: number;
  weight_qty_fmt: string;
  weight_unit: string;
  direct_cost: number;
  direct_cost_fmt: string;
  operational_cost: number;
  operational_cost_fmt: string;
  production_cost: number;
  production_cost_fmt: string;
  sale_price: number;
  sale_price_fmt: string;
  profit_val: number;
  profit_val_fmt: string;
  profit_margin_pct: number;
  profit_margin_fmt: string;
  markup: number;
  notes: string;
  active: boolean;
  created_at: string;
  updated_at: string;
  items_count: number;
  has_broken_items?: boolean;
  items?: Array<{
    id: number;
    item_type: string;
    ref_id: number;
    name: string;
    qty: number;
    qty_fmt: string;
    unit: string;
    cost: number;
    cost_fmt: string;
    broken?: boolean;
  }>;
}

interface ProdColumnSpec {
  key: string;
  label: string;
  width: number;
  align: 'left' | 'center';
  hideable: boolean;
}

const PROD_COLUMNS: ProdColumnSpec[] = [
  { key: 'code', label: 'Código', width: 95, align: 'center', hideable: true },
  { key: 'name', label: 'Nome do Produto', width: 230, align: 'left', hideable: false },
  { key: 'weight', label: 'Peso / Rend.', width: 120, align: 'center', hideable: true },
  { key: 'production_cost', label: 'Custo Produção', width: 135, align: 'center', hideable: true },
  { key: 'operational_cost', label: 'Custo Operacional', width: 135, align: 'center', hideable: true },
  { key: 'sale_price', label: 'Preço Venda', width: 125, align: 'center', hideable: true },
  { key: 'profit', label: 'Lucro (R$)', width: 115, align: 'center', hideable: true },
  { key: 'margin', label: 'Margem %', width: 105, align: 'center', hideable: true },
  { key: 'status', label: 'Status', width: 90, align: 'center', hideable: true },
];

export const ProductsPage: React.FC<ProductsPageProps> = ({
  units,
  initialHiddenCols,
  onNotify,
  dark,
  aiEnabled = false,
}) => {
  const [docsModal, setDocsModal] = useState<{ open: boolean; product: ProductItem | null }>({ open: false, product: null });
  const [aiProductModalOpen, setAiProductModalOpen] = useState(false);
  const [aiDraft, setAiDraft] = useState<AiParsedRecipeResult | null>(null);
  const toolbarRef = useRef<HTMLDivElement>(null);
  const isToolbarCompact = useToolbarOverflow(toolbarRef, aiEnabled ? 760 : 620);
  const [items, setItems] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'Ativos' | 'Inativos' | 'Todos'>('Ativos');
  const [orderBy, setOrderBy] = useState<string>('name');
  const [orderDir, setOrderDir] = useState<'ASC' | 'DESC'>('ASC');
  const [hiddenCols, setHiddenCols] = useState<string[]>(initialHiddenCols || ['code']);
  const { colWidths, startResize, autoFitColumn, shouldIgnoreSortClick } =
    useNexoColumnWidths('nexo_col_widths_products_v1', PROD_COLUMNS);

  const getProductCellText = (prod: ProductItem, key: string): string => {
    switch (key) {
      case 'code':
        return prod.code || '';
      case 'name':
        return prod.name || '';
      case 'weight':
        return `${prod.weight_qty_fmt} ${prod.weight_unit}`;
      case 'production_cost':
        return prod.production_cost_fmt || '';
      case 'operational_cost':
        return prod.operational_cost_fmt || 'R$ 0,00';
      case 'sale_price':
        return prod.sale_price_fmt || '';
      case 'profit':
        return prod.profit_val_fmt || '';
      case 'margin':
        return prod.profit_margin_fmt || '';
      case 'status':
        return prod.active ? 'Ativo' : 'Inativo';
      default:
        return '';
    }
  };

  // Selection & Multiselection
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [checkedIds, setCheckedIds] = useState<Set<number>>(new Set());

  // Popups (Column Visibility Gear & Row 3-dots Menu)
  const [colMenuOpen, setColMenuOpen] = useState(false);
  const colMenuRef = useRef<HTMLDivElement>(null);

  const [rowMenu, setRowMenu] = useState<{
    item: ProductItem;
    x: number;
    y: number;
  } | null>(null);
  const rowMenuRef = useRef<HTMLDivElement>(null);

  // Modals
  const [formModal, setFormModal] = useState<{
    open: boolean;
    editItem: ProductItem | null;
  }>({ open: false, editItem: null });

  const [historyModal, setHistoryModal] = useState<{
    open: boolean;
    product: ProductItem | null;
  }>({ open: false, product: null });

  const [deleteModal, setDeleteModal] = useState<{
    open: boolean;
    check: {
      total: number;
      linked: Array<{ id: number; name: string; code: string; active: boolean; used_by: string[] }>;
      unlinked: Array<{ id: number; name: string; code: string; active: boolean }>;
    };
    ids: number[];
  } | null>(null);

  // Close floating menus on outside click
  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (colMenuRef.current && !colMenuRef.current.contains(e.target as Node)) {
        setColMenuOpen(false);
      }
      if (rowMenuRef.current && !rowMenuRef.current.contains(e.target as Node)) {
        setRowMenu(null);
      }
    };
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, []);

  // Fetch Products
  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      let st: string | null = null;
      if (statusFilter === 'Ativos') st = 'active';
      else if (statusFilter === 'Inativos') st = 'inactive';

      const params = new URLSearchParams();
      if (search.trim()) params.set('search', search.trim());
      if (st) params.set('status', st);

      const res = await fetch(`/api/products?${params.toString()}`);
      if (!res.ok) throw new Error('Falha ao carregar lista de produtos.');
      const data = await res.json();
      setItems(data.items || []);
    } catch (e: any) {
      console.error(e);
      onNotify(e.message || 'Erro ao carregar produtos.', 'error');
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, onNotify]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  // Sorting Handler
  const handleSort = (key: string) => {
    if (shouldIgnoreSortClick()) return;
    if (orderBy === key) {
      setOrderDir((prev) => (prev === 'ASC' ? 'DESC' : 'ASC'));
    } else {
      setOrderBy(key);
      setOrderDir('ASC');
    }
  };

  const sortedItems = useMemo(() => {
    const arr = [...items];
    arr.sort((a, b) => {
      let va: any = '';
      let vb: any = '';
      if (orderBy === 'code') {
        va = a.code;
        vb = b.code;
      } else if (orderBy === 'name') {
        va = a.name.toLowerCase();
        vb = b.name.toLowerCase();
      } else if (orderBy === 'weight') {
        va = a.weight_qty;
        vb = b.weight_qty;
      } else if (orderBy === 'production_cost') {
        va = a.production_cost;
        vb = b.production_cost;
      } else if (orderBy === 'operational_cost') {
        va = a.operational_cost;
        vb = b.operational_cost;
      } else if (orderBy === 'sale_price') {
        va = a.sale_price;
        vb = b.sale_price;
      } else if (orderBy === 'profit') {
        va = a.profit_val;
        vb = b.profit_val;
      } else if (orderBy === 'margin') {
        va = a.profit_margin_pct;
        vb = b.profit_margin_pct;
      } else if (orderBy === 'status') {
        va = a.active ? 1 : 0;
        vb = b.active ? 1 : 0;
      }
      if (va < vb) return orderDir === 'ASC' ? -1 : 1;
      if (va > vb) return orderDir === 'ASC' ? 1 : -1;
      return 0;
    });
    return arr;
  }, [items, orderBy, orderDir]);

  // Selection Checkbox Handlers
  const isBulkMode = checkedIds.size >= 2;

  const isAllChecked = useMemo(
    () => sortedItems.length > 0 && sortedItems.every((r) => checkedIds.has(r.id)),
    [sortedItems, checkedIds]
  );

  const visibleColumns = useMemo(
    () => PROD_COLUMNS.filter((c) => !hiddenCols.includes(c.key)),
    [hiddenCols]
  );

  const handleToggleSelectAll = () => {
    if (checkedIds.size === sortedItems.length && sortedItems.length > 0) {
      setCheckedIds(new Set());
    } else {
      setCheckedIds(new Set(sortedItems.map((r) => r.id)));
    }
  };

  const selectSingleRow = (id: number) => {
    setSelectedId(id);
    setCheckedIds(new Set([id]));
  };

  const handleToggleRowCheck = (id: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      if (next.size === 1) setSelectedId(Array.from(next)[0]);
      else if (next.size === 0) setSelectedId(null);
      return next;
    });
  };

  // Open History modal
  const openHistory = (item?: ProductItem) => {
    const target =
      item ||
      items.find((i) => i.id === selectedId) ||
      (checkedIds.size === 1 ? items.find((i) => checkedIds.has(i.id)) : undefined);
    if (!target) {
      onNotify('Selecione um produto para ver o histórico.', 'warning');
      return;
    }
    setHistoryModal({ open: true, product: target });
  };

  // Column Visibility Handlers
  const toggleColumnVisibility = async (colKey: string) => {
    let next: string[];
    if (hiddenCols.includes(colKey)) {
      next = hiddenCols.filter((k) => k !== colKey);
    } else {
      next = [...hiddenCols, colKey];
    }
    setHiddenCols(next);
    try {
      await fetch('/api/settings/prod_hidden_cols', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: next }),
      });
    } catch (e) {
      console.error(e);
    }
  };

  // Actions
  const handleDuplicate = async (item: ProductItem) => {
    try {
      const res = await fetch(`/api/products/${item.id}/duplicate`, { method: 'POST' });
      if (!res.ok) throw new Error('Não foi possível duplicar o produto.');
      const data = await res.json();
      onNotify(`Produto duplicado com sucesso: "${data.name}"`, 'success');
      await fetchProducts();
    } catch (e: any) {
      onNotify(e.message || 'Erro ao duplicar produto.', 'error');
    }
  };

  const handleToggleStatus = async (item: ProductItem) => {
    try {
      const res = await fetch(`/api/products/${item.id}/toggle-status`, { method: 'POST' });
      if (!res.ok) throw new Error('Não foi possível alterar status.');
      onNotify(
        item.active
          ? `Produto "${item.name}" foi inativado.`
          : `Produto "${item.name}" foi reativado.`,
        'success'
      );
      await fetchProducts();
    } catch (e: any) {
      onNotify(e.message || 'Erro ao alterar status.', 'error');
    }
  };

  const triggerDeleteCheck = async (ids: number[]) => {
    if (ids.length === 0) return;
    try {
      const res = await fetch('/api/products/check-delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids }),
      });
      if (!res.ok) throw new Error('Falha ao verificar vínculos.');
      const check = await res.json();
      setDeleteModal({ open: true, check, ids });
    } catch (e: any) {
      onNotify(e.message || 'Erro ao checar exclusão.', 'error');
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteModal) return;
    try {
      const res = await fetch('/api/products/batch-delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: deleteModal.ids }),
      });
      if (!res.ok) throw new Error('Falha ao processar exclusão.');
      const data = await res.json();
      onNotify(data.message || 'Operação realizada com sucesso.', 'success');
      setCheckedIds(new Set());
      setDeleteModal(null);
      await fetchProducts();
    } catch (e: any) {
      onNotify(e.message || 'Erro ao excluir produtos.', 'error');
    }
  };

  return (
    <div className="flex flex-col h-full w-full">
      {/* 1. Toolbar Principal (RoundedPanel radius=22px, min-height=64px - Padrão Oficial Nexo) */}
      <div
        ref={toolbarRef}
        className="min-h-[64px] py-2 w-full rounded-[22px] bg-white dark:bg-[#111F3B] px-5 mb-2 flex flex-wrap items-center justify-between gap-2.5 shrink-0 shadow-sm transition-colors"
      >
        {/* Left Action Buttons */}
        <div className="flex items-center gap-2.5">
          {!isBulkMode ? (
            <>
              <RoundedActionButton
                label="Novo Produto"
                onClick={() => setFormModal({ open: true, editItem: null })}
                variant="primary"
                icon={<PlusIcon size={16} strokeWidth={2.6} />}
                height={38}
              />
              {!isToolbarCompact ? (
                <div className="flex items-center gap-3">
                  <RoundedActionButton
                    label="Histórico"
                    onClick={() => openHistory()}
                    variant="soft"
                    icon={<ClockIcon size={16} />}
                    height={38}
                  />
                  {aiEnabled && (
                    <RoundedActionButton
                      label="Ler Ficha (IA)"
                      onClick={() => setAiProductModalOpen(true)}
                      variant="secondary"
                      height={38}
                    />
                  )}
                </div>
              ) : (
                <NexoToolbarOverflowMenu
                  actions={[
                    { label: 'Histórico', onClick: () => openHistory(), icon: <ClockIcon size={15} /> },
                    ...(aiEnabled
                      ? [{ label: 'Ler Ficha (IA)', onClick: () => setAiProductModalOpen(true) }]
                      : []),
                  ]}
                />
              )}
            </>
          ) : (
            <div className="flex items-center gap-2.5">
              <RoundedActionButton
                label="Excluir"
                onClick={() => triggerDeleteCheck(Array.from(checkedIds))}
                variant="danger"
                icon={<TrashIcon size={15} />}
                height={38}
              />
              <span className="text-[12px] font-bold text-[#687796] dark:text-[#93A4C6] bg-[#F4F7FC] dark:bg-[#142544] border border-[#DDE5F2] dark:border-[#24385E] px-3.5 py-1.5 rounded-full shadow-xs">
                {checkedIds.size} selecionados
              </span>
            </div>
          )}
        </div>

        {/* Right Search & Status Controls */}
        <div className="flex items-center gap-3.5">
          <RoundedDropdown
            value={statusFilter}
            onChange={(v) => setStatusFilter(v as any)}
            options={['Ativos', 'Inativos', 'Todos']}
            width={115}
            height={32}
            align="center"
          />
          <RoundedEntry
            value={search}
            onChange={setSearch}
            placeholder="Pesquisar"
            width="clamp(160px, 22vw, 280px)"
            height={32}
          />
        </div>
      </div>

      {/* 2. Table Panel (RoundedPanel radius=22px) */}
      <div className="flex-1 w-full rounded-[22px] bg-white dark:bg-[#111F3B] p-3 flex flex-col min-h-0 shadow-sm relative transition-colors">
        {!loading && sortedItems.length === 0 && (
          <NexoEmptyTableWatermark
            title="Ainda não há produtos cadastrados."
            subtitle="Clique em + Novo Produto para cadastrar seu primeiro produto."
          />
        )}
        <div className="flex-1 w-full overflow-auto flex flex-col relative">
          <div className="min-w-full w-max align-middle flex-1 flex flex-col">
            {/* Capsule Table Header (height=36px, rounded-full) */}
            <div className="h-[36px] rounded-full bg-[#EEF4FB] dark:bg-[#142544] flex items-center sticky top-0 z-20 select-none shrink-0">
              {/* Left Master Checkbox (60px) */}
              <div className="w-[60px] h-full shrink-0 sticky left-0 z-30 bg-white dark:bg-[#111F3B]">
                <div className="w-full h-full flex items-center justify-center border-r border-[#E5ECF5] dark:border-[#24385E] bg-[#EEF4FB] dark:bg-[#142544] rounded-l-full">
                  <NexoCheckbox
                    checked={isAllChecked}
                    onChange={handleToggleSelectAll}
                    title="Selecionar todos"
                  />
                </div>
              </div>

              {/* Dynamic Visible Columns */}
              <div className="flex items-center flex-1 h-full">
                {visibleColumns.map((col) => {
                  const isSorted = orderBy === col.key;
                  const arrow = isSorted ? (orderDir === 'ASC' ? ' ↑' : ' ↓') : '';
                  const colWidth = colWidths[col.key] ?? col.width;
                  return (
                    <button
                      key={col.key}
                      type="button"
                      onClick={() => handleSort(col.key)}
                      style={{
                        width: `${colWidth}px`,
                        flexShrink: 0,
                      }}
                      className={`relative h-full px-3 flex items-center border-r border-[#E5ECF5] dark:border-[#24385E] text-[12.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer group ${
                        col.align === 'left' ? 'justify-start text-left' : 'justify-center text-center'
                      }`}
                    >
                      <span className="whitespace-nowrap">
                        {col.align === 'left' ? `${col.label}${arrow}` : `${arrow}${col.label}`}
                      </span>
                      <ColumnResizeHandle
                        onMouseDown={(e) => startResize(col.key, col.label, col.width, e)}
                        onDoubleClick={(e) =>
                          autoFitColumn(
                            col.key,
                            col.label,
                            sortedItems.map((it) => getProductCellText(it, col.key)),
                            col.key === 'status' || col.key === 'profit' ? 24 : 0,
                            e
                          )
                        }
                      />
                    </button>
                  );
                })}
              </div>

              {/* Right Fixed Gear Capsule Header (90px) */}
              <div
                ref={colMenuRef}
                className="w-[90px] h-full shrink-0 sticky right-0 z-30 bg-white dark:bg-[#111F3B]"
              >
                <div className="w-full h-full flex items-center justify-end pr-2 bg-[#EEF4FB] dark:bg-[#142544] rounded-r-full border-l border-[#E5ECF5] dark:border-[#24385E]">
                  <button
                    type="button"
                    onClick={() => setColMenuOpen((o) => !o)}
                    title="Exibir / ocultar colunas"
                    className="w-[30px] h-[30px] rounded-full flex items-center justify-center text-[#60769D] dark:text-[#AFC0E2] hover:text-[#F28C28] dark:hover:text-[#F28C28] transition-colors cursor-pointer"
                  >
                    <GearPolygonIcon
                      size={16}
                      strokeColor="currentColor"
                      centerFill={dark ? '#142544' : '#EEF4FB'}
                    />
                  </button>
                </div>

                {/* Floating Column Visibility Menu */}
                {colMenuOpen && (
                  <div className="absolute right-0 top-[40px] w-[200px] rounded-[14px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-xl py-2 z-50 select-none">
                    <div className="px-3.5 pb-2 text-[10.5px] font-bold tracking-wider text-[#A0ABB9] uppercase">
                      Exibir Colunas
                    </div>
                    <div className="max-h-[min(320px,48vh)] overflow-y-auto">
                      {PROD_COLUMNS.filter((c) => c.hideable).map((col) => {
                        const isVis = !hiddenCols.includes(col.key);
                        return (
                          <div
                            key={col.key}
                            onClick={() => toggleColumnVisibility(col.key)}
                            className="w-full px-3 py-1.5 flex items-center gap-2 hover:bg-[#EEF4FB] dark:hover:bg-[#172746] text-left transition-colors cursor-pointer select-none"
                          >
                            <NexoCheckbox
                              checked={isVis}
                              onChange={() => toggleColumnVisibility(col.key)}
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
                  </div>
                )}
              </div>
            </div>

            {/* Table Rows Body */}
            <div className="divide-y divide-[#F0F4FA] dark:divide-[#162746] flex-1">
              {loading ? (
                <div className="py-16 text-center text-[#687796] dark:text-[#93A4C6] text-[13px]">
                  Carregando produtos...
                </div>
              ) : sortedItems.length === 0 ? (
                <div className="flex-1 min-h-[240px]" />
              ) : (
                sortedItems.map((prod) => {
                  const isChecked = checkedIds.has(prod.id);
                  const isSelected = selectedId === prod.id || isChecked;
                  const rowBg = isSelected
                    ? 'bg-[#FFF0D8] dark:bg-[#5A3518]'
                    : 'bg-white dark:bg-[#0E1B35] hover:bg-[#F8FAFD] dark:hover:bg-[#132342]';
                  const stickyBg = isSelected
                    ? 'bg-[#FFF0D8] dark:bg-[#5A3518]'
                    : 'bg-white dark:bg-[#0E1B35] hover:bg-[#F8FAFD] dark:hover:bg-[#132342]';

                  return (
                    <div
                      key={prod.id}
                      onClick={() => selectSingleRow(prod.id)}
                      onDoubleClick={() => {
                        if (prod.active) {
                          setFormModal({ open: true, editItem: prod });
                        }
                      }}
                      className={`h-[38px] flex items-center text-[13px] transition-colors relative cursor-pointer ${rowBg} ${
                        !prod.active
                          ? 'text-[#9AA9BF] dark:text-[#60769D]'
                          : 'text-[#18223A] dark:text-[#F4F7FF]'
                      }`}
                    >
                      {/* Left Checkbox */}
                      <div
                        onClick={(e) => e.stopPropagation()}
                        className={`w-[60px] h-full flex items-center justify-center shrink-0 sticky left-0 z-10 transition-colors ${stickyBg}`}
                      >
                        <NexoCheckbox
                          checked={isChecked}
                          onChange={() => handleToggleRowCheck(prod.id)}
                        />
                      </div>

                      {/* Data Cells */}
                      <div className="flex items-center flex-1 h-full">
                        {visibleColumns.map((col) => {
                          let cellContent: React.ReactNode = '';
                          switch (col.key) {
                            case 'code':
                              cellContent = (
                                <span className="font-mono text-[12px] font-semibold text-[#687796] dark:text-[#93A4C6]">
                                  {prod.code}
                                </span>
                              );
                              break;
                            case 'name':
                              cellContent = (
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-[#18223A] dark:text-[#F4F7FF]">
                                    {prod.name}
                                  </span>
                                  {prod.has_broken_items && (
                                    <span
                                      title="Este produto possui componente inativo ou arquivado"
                                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FEF3C7] dark:bg-[#3B2A0F] text-[#B45309] dark:text-[#FBBF24] border border-[#F59E0B]/40 shrink-0"
                                    >
                                      <AlertTriangleIcon className="w-3 h-3 shrink-0" />
                                      <span>Item quebrado</span>
                                    </span>
                                  )}
                                </div>
                              );
                              break;
                            case 'weight':
                              cellContent = `${prod.weight_qty_fmt} ${prod.weight_unit}`;
                              break;
                            case 'production_cost':
                              cellContent = (
                                <span className="font-medium text-[#F28C28]">
                                  {prod.production_cost_fmt}
                                </span>
                              );
                              break;
                            case 'operational_cost':
                              cellContent = (
                                <span className="font-medium text-[#D97706] dark:text-[#FBBF24]">
                                  {prod.operational_cost_fmt || 'R$ 0,00'}
                                </span>
                              );
                              break;
                            case 'sale_price':
                              cellContent = (
                                <span className="font-medium text-[#18223A] dark:text-[#F4F7FF]">
                                  {prod.sale_price_fmt}
                                </span>
                              );
                              break;
                            case 'profit':
                              cellContent = (
                                <span className="px-2 py-0.5 rounded-full text-[11.5px] font-bold bg-[#EBFBF0] dark:bg-[#133020] text-[#16A34A] dark:text-[#4ADE80]">
                                  {prod.profit_val_fmt}
                                </span>
                              );
                              break;
                            case 'margin':
                              cellContent = (
                                <span className="font-semibold text-[#475569] dark:text-[#AFC0E2]">
                                  {prod.profit_margin_fmt}
                                </span>
                              );
                              break;
                            case 'status':
                              cellContent = (
                                <span
                                  className={`px-2.5 py-0.5 rounded-full text-[11.5px] font-semibold ${
                                    prod.active
                                      ? 'bg-[#EAFaf1] text-[#1E833F] dark:bg-[#12372E] dark:text-[#61E3B9]'
                                      : 'bg-[#F1F5F9] text-[#687796] dark:bg-[#172746] dark:text-[#93A4C6]'
                                  }`}
                                >
                                  {prod.active ? 'Ativo' : 'Inativo'}
                                </span>
                              );
                              break;
                          }

                          const fullText = getProductCellText(prod, col.key);
                          return (
                            <div
                              key={col.key}
                              title={fullText || undefined}
                              style={{
                                width: `${colWidths[col.key] ?? col.width}px`,
                                flexShrink: 0,
                              }}
                              className={`px-3 text-[13px] truncate ${
                                col.align === 'left' ? 'text-left' : 'text-center'
                              }`}
                            >
                              {cellContent}
                            </div>
                          );
                        })}
                      </div>

                      {/* Right Sticky Action Overlay (90px: Edit 30px, Delete 30px, Options 30px) */}
                      <div
                        onClick={(e) => e.stopPropagation()}
                        className={`w-[90px] h-full flex items-center justify-around shrink-0 sticky right-0 z-10 transition-colors ${stickyBg}`}
                      >
                        <button
                          type="button"
                          disabled={!prod.active}
                          onClick={() => {
                            selectSingleRow(prod.id);
                            setFormModal({ open: true, editItem: prod });
                          }}
                          title={prod.active ? 'Editar' : 'Editar (Desativado)'}
                          className="w-[28px] h-[28px] rounded-full flex items-center justify-center text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-30 cursor-pointer disabled:cursor-default transition-colors"
                        >
                          <EditPencilIcon size={16} />
                        </button>

                        <button
                          type="button"
                          onClick={() => {
                            selectSingleRow(prod.id);
                            triggerDeleteCheck([prod.id]);
                          }}
                          title="Excluir"
                          className="w-[28px] h-[28px] rounded-full flex items-center justify-center text-[#DC2626] dark:text-[#F87171] hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer transition-colors"
                        >
                          <TrashIcon size={16} />
                        </button>

                        <button
                          type="button"
                          onClick={(e) => {
                            selectSingleRow(prod.id);
                            const rect = e.currentTarget.getBoundingClientRect();
                            setRowMenu({
                              item: prod,
                              x: rect.right - 180,
                              y: rect.bottom + 4,
                            });
                          }}
                          title="Mais opções"
                          className="w-[28px] h-[28px] rounded-full flex flex-col items-center justify-center gap-[2.5px] hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer"
                        >
                          <span className="w-[3px] h-[3px] rounded-full bg-[#333333] dark:bg-[#F4F7FF]" />
                          <span className="w-[3px] h-[3px] rounded-full bg-[#333333] dark:bg-[#F4F7FF]" />
                          <span className="w-[3px] h-[3px] rounded-full bg-[#333333] dark:bg-[#F4F7FF]" />
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Floating 3-Dots Row Menu */}
      {rowMenu && (
        <div
          ref={rowMenuRef}
          style={{
            left: `${Math.max(12, rowMenu.x)}px`,
            top: `${Math.min(window.innerHeight - 205, rowMenu.y)}px`,
          }}
          className="fixed w-[185px] rounded-[10px] bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] shadow-xl py-1.5 z-50 select-none"
        >
          <button
            type="button"
            disabled={!rowMenu.item.active}
            onClick={() => {
              const target = rowMenu.item;
              setRowMenu(null);
              setFormModal({ open: true, editItem: target });
            }}
            className="w-full h-[34px] px-3.5 flex items-center gap-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#F4F7FC] dark:hover:bg-[#20375F] disabled:opacity-35 cursor-pointer disabled:cursor-default"
          >
            <EditPencilIcon size={16} className="text-[#687796] dark:text-[#AFC0E2]" />
            <span>{rowMenu.item.active ? 'Editar' : 'Editar (Desativado)'}</span>
          </button>

          <button
            type="button"
            onClick={() => {
              const target = rowMenu.item;
              setRowMenu(null);
              handleDuplicate(target);
            }}
            className="w-full h-[34px] px-3.5 flex items-center gap-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#F4F7FC] dark:hover:bg-[#20375F] cursor-pointer"
          >
            <DuplicateIcon size={16} className="text-[#687796] dark:text-[#AFC0E2]" />
            <span>Duplicar</span>
          </button>

          <button
            type="button"
            onClick={() => {
              const target = rowMenu.item;
              setRowMenu(null);
              openHistory(target);
            }}
            className="w-full h-[34px] px-3.5 flex items-center gap-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#F4F7FC] dark:hover:bg-[#20375F] cursor-pointer"
          >
            <ClockIcon size={15} />
            <span>Histórico</span>
          </button>

          <button
            type="button"
            onClick={() => {
              const target = rowMenu.item;
              setRowMenu(null);
              setDocsModal({ open: true, product: target });
            }}
            className="w-full h-[34px] px-3.5 flex items-center gap-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#F4F7FC] dark:hover:bg-[#20375F] cursor-pointer"
          >
            <PaperclipIcon size={15} className="text-[#687796] dark:text-[#AFC0E2] shrink-0" />
            <span>Anexos & Viewer</span>
          </button>

          <button
            type="button"
            onClick={() => {
              const target = rowMenu.item;
              setRowMenu(null);
              triggerDeleteCheck([target.id]);
            }}
            className="w-full h-[34px] px-3.5 flex items-center gap-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#F4F7FC] dark:hover:bg-[#20375F] cursor-pointer"
          >
            <TrashIcon size={16} className="text-[#DC2626] dark:text-[#F87171]" />
            <span>Excluir</span>
          </button>

          <div className="my-1 mx-3 border-t border-[#DDE5F2] dark:border-[#24385E]" />

          <button
            type="button"
            disabled={rowMenu.item.active}
            onClick={() => {
              const target = rowMenu.item;
              setRowMenu(null);
              handleToggleStatus(target);
            }}
            className="w-full h-[34px] px-3.5 flex items-center gap-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#F4F7FC] dark:hover:bg-[#20375F] disabled:opacity-35 cursor-pointer disabled:cursor-default"
          >
            <span className="w-4 text-center text-[#687796] dark:text-[#AFC0E2]">▶</span>
            <span>Ativar</span>
          </button>

          <button
            type="button"
            disabled={!rowMenu.item.active}
            onClick={() => {
              const target = rowMenu.item;
              setRowMenu(null);
              handleToggleStatus(target);
            }}
            className="w-full h-[34px] px-3.5 flex items-center gap-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#F4F7FC] dark:hover:bg-[#20375F] disabled:opacity-35 cursor-pointer disabled:cursor-default"
          >
            <span className="w-4 text-center text-[#687796] dark:text-[#AFC0E2]">⏸</span>
            <span>Desativar</span>
          </button>
        </div>
      )}

      {/* Modal: Novo / Editar Produto */}
      {formModal.open && (
        <ProductFormModal
          editItem={formModal.editItem}
          aiDraft={aiDraft}
          units={units}
          onClose={() => {
            setFormModal({ open: false, editItem: null });
            setAiDraft(null);
          }}
          onSaved={async () => {
            setFormModal({ open: false, editItem: null });
            setAiDraft(null);
            await fetchProducts();
            onNotify(
              formModal.editItem
                ? 'Produto atualizado com sucesso!'
                : 'Produto cadastrado com sucesso!',
              'success'
            );
          }}
          onNotify={onNotify}
        />
      )}

      {/* Modal: Anexos & Viewer (independente da IA) */}
      {docsModal.open && docsModal.product && (
        <DocumentAttachmentsModal
          open={docsModal.open}
          entityType="PRODUCT"
          entityId={docsModal.product.id}
          entityName={docsModal.product.name}
          onClose={() => setDocsModal({ open: false, product: null })}
          onNotify={onNotify}
        />
      )}

      {/* Modal: Leitura de Ficha / Montagem com IA (só abre com IA ativa) */}
      <AiRecipePreviewModal
        open={aiProductModalOpen}
        targetKind="product"
        onClose={() => setAiProductModalOpen(false)}
        onApplyToForm={(draft) => {
          setAiDraft(draft);
          setFormModal({ open: true, editItem: null });
        }}
        onNotify={onNotify}
      />

      {/* Modal: Histórico de Custos do Produto */}
      {historyModal.open && historyModal.product && (
        <ProductHistoryModal
          product={historyModal.product}
          onClose={() => setHistoryModal({ open: false, product: null })}
          onNotify={onNotify}
        />
      )}

      {/* Modal: Exclusão Inteligente de Produtos */}
      {deleteModal && deleteModal.open && (
        <div className="fixed inset-0 bg-black/45 backdrop-blur-[1px] flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-[540px] max-h-[90vh] overflow-y-auto rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col">
            <h3 className="text-[18px] font-bold text-[#18223A] dark:text-[#F4F7FF] text-center mb-3">
              {deleteModal.check.total === 1 ? 'Excluir Produto' : 'Exclusão em Lote de Produtos'}
            </h3>

            <div className="text-[13px] text-[#18223A] dark:text-[#F4F7FF] space-y-3 mb-5">
              {deleteModal.check.linked.length > 0 && (
                <div className="p-3.5 rounded-[14px] bg-[#FFF8EE] dark:bg-[#2A1E14] border border-[#F28C28]/40">
                  <span className="flex items-center gap-1.5 font-bold text-[#F28C28] mb-1">
                    <AlertTriangleIcon className="w-4 h-4 shrink-0" />
                    <span>Atenção: Produto em uso em outros Produtos</span>
                  </span>
                  <p className="text-[12.5px] text-[#687796] dark:text-[#CBD5E1] leading-relaxed">
                    {deleteModal.check.linked.length === 1
                      ? `O produto "${deleteModal.check.linked[0].name}" compõe outros produtos/combos cadastrados. Para manter a integridade, ele será inativado/arquivado.`
                      : `${deleteModal.check.linked.length} produtos compõem outros produtos/combos e serão inativados para manter a integridade dos custos.`}
                  </p>
                </div>
              )}

              {deleteModal.check.unlinked.length > 0 && (
                <p className="text-[13px] text-[#475569] dark:text-[#AFC0E2]">
                  {deleteModal.check.unlinked.length === 1
                    ? `O produto "${deleteModal.check.unlinked[0].name}" será excluído permanentemente.`
                    : `${deleteModal.check.unlinked.length} produtos sem vínculos serão excluídos permanentemente.`}
                </p>
              )}
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-[#E2EAF5] dark:border-[#1E3156]">
              <RoundedActionButton
                label="Cancelar"
                onClick={() => setDeleteModal(null)}
                variant="secondary"
                height={36}
              />
              <RoundedActionButton
                label={deleteModal.check.unlinked.length > 0 ? 'Confirmar Exclusão' : 'Confirmar Inativação'}
                onClick={handleConfirmDelete}
                variant="danger"
                height={36}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// =====================================================================
// Sub-Component: ProductFormModal (Criar / Editar Produto)
// =====================================================================

interface FormCompositionRow {
  item_type: 'MATERIAL' | 'RECIPE_BASE' | 'PRODUCT';
  ref_id: number;
  qty: string;
  unit: string;
  cost_fmt: string;
  available_units: string[];
  unresolved_name?: string;
  broken_reason?: string;
}

interface ProductFormModalProps {
  editItem: ProductItem | null;
  aiDraft?: AiParsedRecipeResult | null;
  units: string[];
  onClose: () => void;
  onSaved: () => void;
  onNotify: (msg: string, type?: 'success' | 'warning' | 'error') => void;
}

const ProductFormModal: React.FC<ProductFormModalProps> = ({
  editItem,
  aiDraft,
  units,
  onClose,
  onSaved,
  onNotify,
}) => {
  const [name, setName] = useState(editItem ? editItem.name : (aiDraft?.name || ''));
  const [weightQty, setWeightQty] = useState(editItem ? String(editItem.weight_qty) : (aiDraft ? String(aiDraft.yield_qty || 1) : '1'));
  const [weightUnit, setWeightUnit] = useState(editItem ? editItem.weight_unit : (aiDraft?.yield_unit || 'un'));
  const [salePrice, setSalePrice] = useState(editItem ? editItem.sale_price_fmt : 'R$ 0,00');
  const [notes, setNotes] = useState(editItem ? editItem.notes : (aiDraft?.notes || ''));

  // Options caches
  const [options, setOptions] = useState<{
    materials: Array<{ id: number; code: string; name: string; brand: string; unit: string; label: string }>;
    recipes: Array<{ id: number; code: string; name: string; yield_qty: number; yield_unit: string; label: string }>;
    products: Array<{ id: number; code: string; name: string; unit: string; label: string }>;
  }>({ materials: [], recipes: [], products: [] });

  // Rows (inicializacao imediata a partir dos dados que a tabela ja possui)
  const [items, setItems] = useState<FormCompositionRow[]>(() => {
    if (editItem && editItem.items && editItem.items.length > 0) {
      return editItem.items.map((it) => ({
        item_type: it.item_type as any,
        ref_id: it.ref_id,
        qty: String(it.qty),
        unit: it.unit,
        cost_fmt: it.cost_fmt,
        available_units: [it.unit, 'g', 'kg', 'ml', 'L', 'un'],
        broken_reason: it.broken
          ? `Componente inativo/arquivado: "${it.name}" — substitua por outro, remova ou cancele para cadastrar/reativar`
          : undefined,
      }));
    }
    if (!editItem && aiDraft?.ingredients?.length) {
      return aiDraft.ingredients
        .filter((g) => g.selected)
        .map((g) => ({
          item_type: g.item_type,
          ref_id: g.matched_id || 0,
          qty: String(g.qty || 1),
          unit: g.unit || 'g',
          cost_fmt: '-',
          available_units: [g.unit || 'g', 'g', 'kg', 'ml', 'L', 'un'],
          unresolved_name: g.matched_id ? undefined : g.name,
        }));
    }
    return [];
  });
  const [directCostFmt, setDirectCostFmt] = useState(editItem ? editItem.direct_cost_fmt : 'R$ 0,00');
  const [operationalCostFmt, setOperationalCostFmt] = useState('R$ 0,00');
  const [operationalBreakdown, setOperationalBreakdown] = useState<any[]>([]);
  const [productionCostFmt, setProductionCostFmt] = useState(editItem ? editItem.production_cost_fmt : 'R$ 0,00');
  const [profitValFmt, setProfitValFmt] = useState(editItem ? editItem.profit_val_fmt : 'R$ 0,00');
  const [marginFmt, setMarginFmt] = useState(editItem ? editItem.profit_margin_fmt : '0.0%');
  const [markupVal, setMarkupVal] = useState(editItem ? editItem.markup : 0);

  const [salesChannelsEnabled, setSalesChannelsEnabled] = useState(false);
  const [salesChannels, setSalesChannels] = useState<
    { id: string; name: string; fee_pct: number; fixed_fee: number }[]
  >([]);
  const [selectedChannelId, setSelectedChannelId] = useState<string>('');
  const [targetMarginPct, setTargetMarginPct] = useState<string>('30');

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quickCreateTarget, setQuickCreateTarget] = useState<{ idx: number; name: string; unit: string } | null>(null);

  // Fetch composition options & sales channels settings
  useEffect(() => {
    (async () => {
      try {
        const [optRes, setRes] = await Promise.all([
          fetch('/api/products/composition-options'),
          fetch('/api/settings'),
        ]);
        if (optRes.ok) {
          const data = await optRes.json();
          setOptions(data);
        }
        if (setRes.ok) {
          const sdata = await setRes.json();
          if (sdata.bi?.target_margin_pct !== undefined) {
            setTargetMarginPct(String(sdata.bi.target_margin_pct).replace('.', ','));
          }
          if (sdata.sales_channels?.enabled && Array.isArray(sdata.sales_channels.channels)) {
            setSalesChannelsEnabled(true);
            setSalesChannels(sdata.sales_channels.channels);
            if (sdata.sales_channels.channels.length > 0) {
              setSelectedChannelId(sdata.sales_channels.channels[0].id);
            }
          }
        }
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  // Load existing items if edit
  useEffect(() => {
    if (editItem) {
      (async () => {
        try {
          const res = await fetch(`/api/products/${editItem.id}`);
          if (res.ok) {
            const data = await res.json();
            const rows: FormCompositionRow[] = (data.items || []).map((it: any) => ({
              item_type: it.item_type,
              ref_id: it.ref_id,
              qty: String(it.qty),
              unit: it.unit,
              cost_fmt: it.cost_fmt,
              available_units: [it.unit, 'g', 'kg', 'ml', 'L', 'un'],
            }));
            setItems(rows);
            setDirectCostFmt(data.direct_cost_fmt);
            setOperationalCostFmt(data.operational_cost_fmt || 'R$ 0,00');
            setOperationalBreakdown(data.operational_breakdown?.items || []);
            setProductionCostFmt(data.production_cost_fmt);
            setProfitValFmt(data.profit_val_fmt);
            setMarginFmt(`${data.profit_margin_pct}%`);
          }
        } catch (e) {
          console.error(e);
        }
      })();
    }
  }, [editItem]);

  // Live preview calculation
  const recalculatePreview = useCallback(async (
    rows: FormCompositionRow[],
    priceStr: string
  ) => {
    const validRows = rows.filter(
      (r) => r.ref_id > 0 && parseFloat(r.qty.replace(',', '.')) > 0 && r.unit
    );
    if (validRows.length === 0) {
      setDirectCostFmt('R$ 0,00');
      setOperationalCostFmt('R$ 0,00');
      setOperationalBreakdown([]);
      setProductionCostFmt('R$ 0,00');
      setProfitValFmt('R$ 0,00');
      setMarginFmt('0.0%');
      setMarkupVal(0);
      setItems((prev) =>
        prev.map((r) => ({
          ...r,
          cost_fmt: r.ref_id > 0 && parseFloat(r.qty.replace(',', '.')) > 0 ? r.cost_fmt : '-',
        }))
      );
      return;
    }
    try {
      const payload = {
        sale_price: priceStr || '0',
        items: validRows.map((r) => ({
          item_type: r.item_type,
          ref_id: r.ref_id,
          qty_per_unit: parseFloat(r.qty.replace(',', '.')) || 0,
          unit: r.unit,
        })),
      };
      const res = await fetch('/api/products/preview-cost', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        setDirectCostFmt(data.direct_cost_fmt);
        setOperationalCostFmt(data.operational_cost_fmt);
        setOperationalBreakdown(data.operational_breakdown?.items || []);
        setProductionCostFmt(data.production_cost_fmt);
        setProfitValFmt(data.profit_val_fmt);
        setMarginFmt(data.profit_margin_fmt);
        setMarkupVal(data.markup);

        const costMap: Record<string, string> = {};
        if (data.items) {
          data.items.forEach((it: any) => {
            costMap[`${it.item_type}_${it.ref_id}`] = it.cost_fmt;
          });
        }
        setItems((prev) =>
          prev.map((r) => ({
            ...r,
            cost_fmt:
              r.ref_id > 0 && parseFloat(r.qty.replace(',', '.')) > 0
                ? costMap[`${r.item_type}_${r.ref_id}`] || '-'
                : '-',
          }))
        );
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  const addComponentRow = () => {
    const newRow: FormCompositionRow = {
      item_type: 'MATERIAL',
      ref_id: 0,
      qty: '',
      unit: '',
      cost_fmt: '-',
      available_units: ['un', 'g', 'kg', 'ml', 'L'],
    };
    setItems((prev) => [...prev, newRow]);
  };

  const removeComponentRow = (idx: number) => {
    const next = items.filter((_, i) => i !== idx);
    setItems(next);
    recalculatePreview(next, salePrice);
  };

  const updateComponentRow = (idx: number, patch: Partial<FormCompositionRow>) => {
    const next = [...items];
    const updated = { ...next[idx], ...patch };

    // If item_type or ref_id changed, reset unit appropriately
    if (patch.item_type !== undefined || patch.ref_id !== undefined) {
      if (updated.item_type === 'MATERIAL') {
        const mat = options.materials.find((m) => m.id === updated.ref_id);
        if (mat) {
          const u = mat.unit.toLowerCase();
          const av = ['g', 'kg', 'mg'].includes(u)
            ? ['g', 'kg', 'mg']
            : ['ml', 'l'].includes(u)
            ? ['ml', 'L']
            : ['un'];
          updated.available_units = av;
          updated.unit = av[0];
        }
      } else if (updated.item_type === 'RECIPE_BASE') {
        const rec = options.recipes.find((r) => r.id === updated.ref_id);
        if (rec) {
          const u = (rec.yield_unit || '').toLowerCase();
          const av = ['g', 'kg', 'mg'].includes(u)
            ? ['g', 'kg', 'mg']
            : ['ml', 'l'].includes(u)
            ? ['ml', 'L']
            : [rec.yield_unit || 'un'];
          updated.available_units = av;
          updated.unit = av[0];
        }
      } else if (updated.item_type === 'PRODUCT') {
        updated.available_units = ['un'];
        updated.unit = 'un';
      }
    }

    next[idx] = updated;
    setItems(next);
    recalculatePreview(next, salePrice);
  };

  const failSave = (msg: string, type: 'warning' | 'error' = 'warning') => {
    setError(msg);
    onNotify(msg, type);
  };

  const handleSave = async () => {
    setError(null);
    const n = name.trim();
    if (!n) return failSave('O nome do produto é obrigatório.');

    const brokenRows = items.filter((r) => r.ref_id <= 0 || Boolean(r.broken_reason));
    if (brokenRows.length > 0) {
      const names = brokenRows.map((b) => b.unresolved_name || 'Sem vínculo').join(', ');
      return failSave(`Não é possível salvar com componente quebrado ou inativo. Substitua ou remova: ${names}.`);
    }

    const validRows = items.filter((r) => r.ref_id > 0);
    if (validRows.length === 0) {
      return failSave('Adicione ao menos um componente na composição do produto.');
    }
    for (const r of validRows) {
      const q = parseFloat(r.qty.replace(',', '.'));
      if (isNaN(q) || q <= 0) {
        return failSave('Informe uma quantidade maior que zero para todos os componentes.');
      }
    }

    setSaving(true);
    const payload = {
      name: n,
      weight_qty: weightQty,
      weight_unit: weightUnit,
      sale_price: salePrice,
      cooking_appliance: 'none',
      cooking_time_minutes: 0,
      batch_yield_units: 1,
      notes: notes.trim(),
      items: validRows.map((it) => ({
        item_type: it.item_type,
        ref_id: it.ref_id,
        qty_per_unit: parseFloat(it.qty.replace(',', '.')) || 0,
        unit: it.unit,
      })),
    };

    try {
      const url = editItem ? `/api/products/${editItem.id}` : '/api/products';
      const method = editItem ? 'PUT' : 'POST';
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        failSave(data.detail || 'Não foi possível salvar o produto.', 'error');
        return;
      }
      if (!editItem && aiDraft?.source_file && data.id) {
        try {
          await fetch(`/api/documents/PRODUCT/${data.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(aiDraft.source_file),
          });
        } catch (attachErr) {
          console.error('Erro ao auto-anexar documento do produto:', attachErr);
        }
      }
      onSaved();
    } catch (e: any) {
      failSave(e.message || 'Erro de conexão com o servidor.', 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/45 backdrop-blur-[1px] flex items-center justify-center z-50 p-4">
      <div className="w-full max-w-[740px] max-h-[92vh] rounded-[22px] bg-[#F4F7FC] dark:bg-[#0B1730] border border-[#DDE5F2] dark:border-[#24385E] shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 pt-4 pb-3 flex items-center justify-between border-b border-[#E2EAF5] dark:border-[#1E3156] bg-white dark:bg-[#0F1B35] shrink-0">
          <div className="flex items-center gap-2.5">
            <h2 className="text-[17px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              {editItem ? 'Editar Produto' : 'Novo Produto'}
            </h2>
            {editItem && (
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-[#FFF0D8] text-[#BA5200] dark:bg-[#5A3518] dark:text-[#F28C28]">
                {editItem.code}
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-7 h-7 rounded-full flex items-center justify-center text-[#687796] hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Scrollable Form Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3.5 min-h-0">
          {error && (
            <div className="px-3.5 py-2.5 rounded-xl bg-[#FFF5F5] dark:bg-[#3B1822] border border-[#FEB2B2] dark:border-[#742A2A] text-[#C53030] dark:text-[#FF8A9B] text-[12px] font-medium">
              {error}
            </div>
          )}

          {/* Card 1: Identificação & Precificação Básica */}
          <div className="p-4 rounded-[18px] bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] shadow-sm space-y-3">
            <div className="grid grid-cols-12 gap-2.5">
              <div className="col-span-8">
                <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                  Nome do Produto *
                </label>
                <CapsuleInput
                  value={name}
                  onChange={setName}
                  autoCapitalizeFirst
                  placeholder="Ex: Bolo no Pote Cenoura com Ninho 250ml"
                />
              </div>

              <div className="col-span-4">
                <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                  Peso / Rendimento *
                </label>
                <CapsuleQuantityUnit
                  qtyValue={weightQty}
                  onQtyChange={setWeightQty}
                  unitValue={weightUnit}
                  onUnitChange={setWeightUnit}
                  unitOptions={['un', 'g', 'kg', 'ml', 'L', 'porções', 'potes', 'fatias']}
                  qtyPlaceholder="Ex: 1"
                  width="100%"
                  height={32}
                />
              </div>
            </div>

            <div className="grid grid-cols-12 gap-2.5">
              <div className="col-span-4">
                <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                  Preço de Venda Praticado (R$) *
                </label>
                <CapsuleInput
                  value={salePrice}
                  onChange={(v) => {
                    setSalePrice(v);
                    recalculatePreview(items, v);
                  }}
                  type="money"
                  placeholder="R$ 0,00"
                />
              </div>

              <div className="col-span-8">
                <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                  Observações / Detalhes de Venda (Opcional)
                </label>
                <CapsuleInput
                  value={notes}
                  onChange={setNotes}
                  autoCapitalizeFirst
                  placeholder="Ex: Validade de 5 dias na geladeira, acompanha colher..."
                />
              </div>
            </div>
          </div>

          {/* Card 2: Composição do Produto */}
          <div className="p-4 rounded-[18px] bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] shadow-sm flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  Composição do Produto
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#F0F4FA] dark:bg-[#1A2C4E] text-[#60769D] dark:text-[#AFC0E2]">
                  {items.length} {items.length === 1 ? 'item' : 'itens'}
                </span>
              </div>

              <RoundedActionButton
                label="Adicionar Componente"
                onClick={addComponentRow}
                variant="primary"
                icon={<PlusIcon size={14} strokeWidth={2.4} />}
                height={32}
              />
            </div>

            {items.length === 0 ? (
              <div className="py-8 flex flex-col items-center justify-center text-center select-none">
                <NexoEmptyStateIcon className="w-[115px] h-[58px] mb-2 opacity-80" />
                <p className="text-[13px] font-semibold text-[#687796] dark:text-[#93A4C6] mb-0.5">
                  Nenhum componente adicionado à composição.
                </p>
                <p className="text-[12px] text-[#8C9BB5] dark:text-[#64748B]">
                  Clique em "+ Adicionar Componente" acima para compor com receitas, embalagens ou insumos.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {/* Header cápsula da composição */}
                <div className="h-[30px] rounded-full bg-[#EEF4FB] dark:bg-[#142544] px-3 flex items-center text-[11.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] select-none">
                  <span className="w-[110px] pl-1">Tipo</span>
                  <span className="flex-1 pl-1">Componente</span>
                  <span className="w-[160px] text-center">Quantidade | Unidade</span>
                  <span className="w-[95px] text-center">Custo Prop.</span>
                  <span className="w-[36px] text-center">Ação</span>
                </div>

                {/* Rows de componentes */}
                {items.map((row, idx) => {
                  let componentOptions: Array<{ id: number; label: string }> = [];
                  if (row.item_type === 'MATERIAL') componentOptions = options.materials;
                  else if (row.item_type === 'RECIPE_BASE') componentOptions = options.recipes;
                  else if (row.item_type === 'PRODUCT') {
                    // prevent infinite loop: exclude current editing product
                    componentOptions = options.products.filter((p) => p.id !== editItem?.id);
                  }

                  const selectedComp = componentOptions.find((c) => c.id === row.ref_id);
                  const selectedLabel = selectedComp ? selectedComp.label : '';
                  const isBroken = row.ref_id <= 0 || Boolean(row.broken_reason);

                  return (
                    <div
                      key={idx}
                      className={`p-2 rounded-[14px] border space-y-1.5 ${
                        isBroken
                          ? 'bg-[#FFFBEB] dark:bg-[#2A1F0D] border-[#F59E0B] dark:border-[#B45309]'
                          : 'bg-[#F9FBFC] dark:bg-[#0E1A30] border-[#E2EAF5] dark:border-[#1E3156]'
                      }`}
                    >
                      {isBroken && (
                        <div className="flex items-center justify-between gap-2 px-1">
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#B45309] dark:text-[#FBBF24]">
                            <AlertTriangleIcon className="w-3.5 h-3.5 shrink-0" />
                            <span>
                              {row.broken_reason
                                ? row.broken_reason
                                : row.unresolved_name
                                ? `Não encontrado pela IA: "${row.unresolved_name}" — vincule abaixo ou crie agora`
                                : 'Componente sem vínculo — vincule abaixo ou crie agora'}
                            </span>
                          </span>
                          {!row.broken_reason && (
                            <button
                              type="button"
                              onClick={() =>
                                setQuickCreateTarget({
                                  idx,
                                  name: row.unresolved_name || '',
                                  unit: row.unit || 'g',
                                })
                              }
                              className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#BA5200] hover:bg-[#9C4400] text-white transition-colors cursor-pointer shrink-0"
                            >
                              + Criar insumo
                            </button>
                          )}
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        {/* Dropdown Tipo de Componente */}
                        <div className="w-[110px] shrink-0">
                          <RoundedDropdown
                            value={
                              row.item_type === 'MATERIAL'
                                ? 'Insumo'
                                : row.item_type === 'RECIPE_BASE'
                                ? 'Receita'
                                : 'Produto'
                            }
                            onChange={(lbl) => {
                              const newType =
                                lbl === 'Receita'
                                  ? 'RECIPE_BASE'
                                  : lbl === 'Produto'
                                  ? 'PRODUCT'
                                  : 'MATERIAL';
                              updateComponentRow(idx, {
                                item_type: newType,
                                ref_id: 0,
                                cost_fmt: '-',
                                broken_reason: undefined,
                              });
                            }}
                            options={['Insumo', 'Receita', 'Produto']}
                            width="100%"
                            height={34}
                            align="center"
                          />
                        </div>

                        {/* Dropdown Componente */}
                        <div className="flex-1 min-w-0">
                          <RoundedDropdown
                            value={selectedLabel}
                            onChange={(newLabel) => {
                              const found = componentOptions.find((c) => c.label === newLabel);
                              if (found) {
                                updateComponentRow(idx, {
                                  ref_id: found.id,
                                  unresolved_name: undefined,
                                  broken_reason: undefined,
                                });
                              }
                            }}
                            options={componentOptions.map((c) => c.label)}
                            width="100%"
                            height={34}
                            align="left"
                            placeholder="Selecione o componente..."
                          />
                        </div>

                      {/* Quantidade e Unidade unificadas em cápsula Nexo */}
                      <div className="w-[160px] shrink-0 flex items-center justify-center">
                        <CapsuleQuantityUnit
                          qtyValue={row.qty}
                          onQtyChange={(v) => updateComponentRow(idx, { qty: v })}
                          unitValue={row.unit}
                          onUnitChange={(newUnit) => updateComponentRow(idx, { unit: newUnit })}
                          unitOptions={
                            row.available_units.length > 0
                              ? row.available_units
                              : [row.unit || 'un', 'un', 'g', 'kg', 'ml', 'L']
                          }
                          qtyPlaceholder="Qtd"
                          width={160}
                          height={34}
                        />
                      </div>

                      {/* Custo Calculado */}
                      <div className="w-[95px] h-[34px] rounded-full bg-white dark:bg-[#142340] border border-[#DDE5F2] dark:border-[#24385E] flex items-center justify-center font-bold text-[13px] text-[#18223A] dark:text-[#F4F7FF] shrink-0 shadow-sm">
                        {row.cost_fmt}
                      </div>

                      {/* Remover Linha */}
                      <div className="w-[36px] flex items-center justify-center shrink-0">
                        <button
                          type="button"
                          onClick={() => removeComponentRow(idx)}
                          title="Remover componente"
                          className="w-8 h-8 rounded-full flex items-center justify-center text-[#DC2626] dark:text-[#F87171] hover:bg-[#FEE2E2] dark:hover:bg-[#3D1822] transition-colors cursor-pointer"
                        >
                          <TrashIcon size={16} />
                        </button>
                      </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Informação didática da Composição Comercial */}
          <div className="p-3.5 rounded-[18px] bg-[#EBF3FE] dark:bg-[#132546] border border-[#CBDDF7] dark:border-[#1E3A6E]">
            <p className="text-[12.5px] font-bold text-[#1E3A8A] dark:text-[#93C5FD]">
              Montagem & Embalagem Comercial do Produto
            </p>
            <p className="text-[11.5px] text-[#475569] dark:text-[#94A3B8] mt-0.5">
              Adicione aqui as receitas prontas (massas de bolo, brigadeiros, recheios) e as embalagens/insumos finais. Os custos de gás, forno e tempo de preparo já vêm calculados automaticamente dentro de cada receita!
            </p>
          </div>

          {/* Card 3: Painel de Precificação & Lucro em Tempo Real */}
          <div className="rounded-[18px] bg-[#FFF8EE] dark:bg-[#1B1914] border border-[#F28C28]/35 p-3.5 shadow-sm space-y-3">
            <div className="flex items-center justify-around text-center">
              <div>
                <span className="block text-[11px] uppercase tracking-wider font-bold text-[#8C9BB5] dark:text-[#93A4C6]">
                  Custo de Produção
                </span>
                <span className="text-[17px] font-bold text-[#F28C28]">
                  {productionCostFmt}
                </span>
                <span className="block text-[10.5px] font-semibold text-[#8C9BB5] dark:text-[#93A4C6] mt-0.5">
                  Direto: {directCostFmt} + Op.: {operationalCostFmt}
                </span>
              </div>

              <div className="w-[1px] h-10 bg-[#F28C28]/25" />

              <div>
                <span className="block text-[11px] uppercase tracking-wider font-bold text-[#8C9BB5] dark:text-[#93A4C6]">
                  Preço de Venda
                </span>
                <span className="text-[17px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  {salePrice}
                </span>
                <span className="block text-[10.5px] font-semibold text-[#8C9BB5] dark:text-[#93A4C6] mt-0.5">
                  Valor ao cliente
                </span>
              </div>

              <div className="w-[1px] h-10 bg-[#F28C28]/25" />

              <div>
                <span className="block text-[11px] uppercase tracking-wider font-bold text-[#8C9BB5] dark:text-[#93A4C6]">
                  Lucro Líquido
                </span>
                <span className="text-[17px] font-bold text-[#16A34A] dark:text-[#4ADE80]">
                  {profitValFmt}
                </span>
                <span className="block text-[10.5px] font-semibold text-[#16A34A]/80 dark:text-[#4ADE80]/80 mt-0.5">
                  Por unidade
                </span>
              </div>

              <div className="w-[1px] h-10 bg-[#F28C28]/25" />

              <div>
                <span className="block text-[11px] uppercase tracking-wider font-bold text-[#8C9BB5] dark:text-[#93A4C6]">
                  Margem / Markup
                </span>
                <span className="text-[15px] font-bold text-[#475569] dark:text-[#CBD5E1]">
                  {marginFmt} • {markupVal.toFixed(1)}x
                </span>
                <span className="block text-[10.5px] font-semibold text-[#8C9BB5] dark:text-[#93A4C6] mt-0.5">
                  Retorno sobre venda
                </span>
              </div>
            </div>

            {/* Decomposição Transparente dos Custos Operacionais */}
            {operationalBreakdown && operationalBreakdown.length > 0 && (
              <div className="pt-2.5 border-t border-[#F28C28]/20 flex flex-wrap items-center justify-between gap-2 text-[11.5px]">
                <div className="flex items-center text-[#18223A] dark:text-[#F4F7FF] font-bold">
                  <span>Custos Operacionais inclusos (Gás, Energia e Água):</span>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {operationalBreakdown.map((item: any, idx: number) => {
                    const n = (item.name || '').toLowerCase();
                    const isEnergy = n.includes('energia') || n.includes('elétr') || n.includes('eletr');
                    const isWater = n.includes('água') || n.includes('agua');
                    const isGas = n.includes('gás') || n.includes('gas');
                    const iconSvg = isGas ? (
                      <FlameIcon size={12} className="text-[#F28C28]" />
                    ) : isEnergy ? (
                      <ZapEnergyIcon size={12} className="text-[#F28C28]" />
                    ) : isWater ? (
                      <DropletWaterIcon size={12} className="text-[#F28C28]" />
                    ) : null;

                    return (
                      <span
                        key={item.id || idx}
                        className="px-2.5 py-1 rounded-full bg-white dark:bg-[#111F3B] border border-[#F28C28]/30 font-bold text-[#18223A] dark:text-[#F4F7FF] flex items-center gap-1.5 shadow-xs"
                      >
                        {iconSvg && <span className="flex items-center shrink-0">{iconSvg}</span>}
                        <span>{item.name}:</span>
                        <span className="text-[#F28C28]">{item.cost_fmt}</span>
                        <span className="text-[#8C9BB5] dark:text-[#93A4C6] text-[10px]">({item.rate_label})</span>
                      </span>
                    );
                  })}
                  <span className="px-2.5 py-1 rounded-full bg-[#F28C28] text-white font-extrabold text-[11px] shadow-xs">
                    Total: {operationalCostFmt}
                  </span>
                </div>
              </div>
            )}

            {/* Simulador de Canal de Venda & Sugestor de Preço pela Margem Alvo */}
            {salesChannelsEnabled && salesChannels.length > 0 && (() => {
              const parseBrl = (v: string) => {
                const n = parseFloat(
                  String(v || '0').replace(/R\$\s*/gi, '').replace(/\./g, '').replace(',', '.').trim()
                );
                return Number.isFinite(n) ? n : 0;
              };
              const fmtBrl = (n: number) =>
                `R$ ${n.toFixed(2).replace('.', ',')}`;
              const prodCostNum = parseBrl(productionCostFmt);
              const salePriceNum = parseBrl(salePrice);
              const ch = salesChannels.find((c) => c.id === selectedChannelId) || salesChannels[0];
              const feePct = Number(ch.fee_pct || 0) / 100;
              const fixedFee = Number(ch.fixed_fee || 0);
              const channelFeeTotal = salePriceNum * feePct + fixedFee;
              const netReceived = Math.max(0, salePriceNum - channelFeeTotal);
              const netProfit = netReceived - prodCostNum;
              const netMarginPct = salePriceNum > 0 ? (netProfit / salePriceNum) * 100 : 0;

              const targetM = Math.max(0, Math.min(95, parseBrl(targetMarginPct))) / 100;
              const denom = 1 - (feePct + targetM);
              const suggestedPrice = denom > 0.01 ? (prodCostNum + fixedFee) / denom : null;

              return (
                <div className="pt-3 border-t border-[#F28C28]/20 space-y-2.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-[11.5px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                      Simulador de Canal & Margem Alvo:
                    </span>
                    <div className="flex flex-wrap items-center gap-1.5">
                      {salesChannels.map((item) => {
                        const active = item.id === ch.id;
                        return (
                          <button
                            key={item.id}
                            type="button"
                            onClick={() => setSelectedChannelId(item.id)}
                            className={`px-2.5 py-1 rounded-full text-[11px] font-bold transition-colors cursor-pointer ${
                              active
                                ? 'bg-[#F28C28] text-white shadow-xs'
                                : 'bg-white dark:bg-[#162340] border border-[#E2EAF5] dark:border-[#24385E] text-[#60769D] dark:text-[#93A4C6] hover:border-[#F28C28]'
                            }`}
                          >
                            {item.name} ({Number(item.fee_pct || 0).toFixed(1).replace('.', ',')}%
                            {Number(item.fixed_fee || 0) > 0
                              ? ` + ${fmtBrl(Number(item.fixed_fee))}`
                              : ''}
                            )
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 items-center bg-white/80 dark:bg-[#101C36] border border-[#E2EAF5] dark:border-[#24385E] rounded-[14px] p-3">
                    <div className="flex flex-wrap items-center gap-4 text-[11.5px]">
                      <div>
                        <span className="block text-[10px] uppercase font-bold text-[#8C9BB5]">Taxa do Canal</span>
                        <span className="font-bold text-[#DC2626] dark:text-[#F87171]">-{fmtBrl(channelFeeTotal)}</span>
                      </div>
                      <div>
                        <span className="block text-[10px] uppercase font-bold text-[#8C9BB5]">Receita Líquida</span>
                        <span className="font-bold text-[#18223A] dark:text-[#F4F7FF]">{fmtBrl(netReceived)}</span>
                      </div>
                      <div>
                        <span className="block text-[10px] uppercase font-bold text-[#8C9BB5]">Lucro Real ({ch.name})</span>
                        <span
                          className={`font-bold ${
                            netProfit >= 0
                              ? 'text-[#16A34A] dark:text-[#4ADE80]'
                              : 'text-[#DC2626] dark:text-[#F87171]'
                          }`}
                        >
                          {fmtBrl(netProfit)} ({netMarginPct.toFixed(1).replace('.', ',')}%)
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center justify-end gap-2">
                      <span className="text-[11px] font-semibold text-[#60769D] dark:text-[#93A4C6]">
                        Margem alvo (%):
                      </span>
                      <input
                        type="text"
                        value={targetMarginPct}
                        onChange={(e) => setTargetMarginPct(e.target.value)}
                        className="w-[58px] h-[30px] px-2 rounded-full text-center text-[12px] font-bold bg-[#F8FAFD] dark:bg-[#162340] border border-[#DFE6F0] dark:border-[#24375C] text-[#18223A] dark:text-[#F4F7FF] focus:outline-none focus:border-[#F28C28]"
                      />
                      {suggestedPrice !== null ? (
                        <button
                          type="button"
                          onClick={() => setSalePrice(fmtBrl(suggestedPrice))}
                          title="Aplicar preço sugerido ao Preço de Venda"
                          className="px-3 py-1.5 rounded-full text-[11.5px] font-bold bg-[#18223A] dark:bg-[#F28C28] text-white hover:opacity-90 transition-opacity cursor-pointer"
                        >
                          Sugerir {fmtBrl(suggestedPrice)} • Aplicar
                        </button>
                      ) : (
                        <span className="text-[11px] font-semibold text-[#DC2626]">
                          Taxa + margem ≥ 100%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>

        {/* Modal Actions Footer */}
        <div className="px-6 py-3 border-t border-[#E2EAF5] dark:border-[#1E3156] flex items-center justify-between bg-white dark:bg-[#0F1B35] shrink-0">
          <RoundedActionButton
            label="Cancelar"
            onClick={onClose}
            variant="secondary"
            height={36}
          />
          <RoundedActionButton
            label={saving ? 'Salvando...' : editItem ? 'Salvar Alterações' : 'Salvar Produto'}
            onClick={handleSave}
            disabled={saving}
            variant="primary"
            height={36}
          />
        </div>
      </div>

      <QuickCreateMaterialModal
        open={Boolean(quickCreateTarget)}
        initialName={quickCreateTarget?.name || ''}
        initialUnit={quickCreateTarget?.unit || 'g'}
        onClose={() => setQuickCreateTarget(null)}
        onNotify={onNotify}
        onCreated={async (newId) => {
          const targetIdx = quickCreateTarget?.idx ?? -1;
          try {
            const res = await fetch('/api/products/composition-options');
            if (res.ok) {
              const data = await res.json();
              setOptions(data);
              if (targetIdx >= 0) {
                const nextRows = [...items];
                if (nextRows[targetIdx]) {
                  nextRows[targetIdx] = {
                    ...nextRows[targetIdx],
                    item_type: 'MATERIAL',
                    ref_id: newId,
                    unresolved_name: undefined,
                  };
                  setItems(nextRows);
                }
              }
            }
          } catch (e) {
            console.error(e);
          }
        }}
      />
    </div>
  );
};

// =====================================================================
// Sub-Component: ProductHistoryModal (Histórico de Custos do Produto)
// =====================================================================

interface ProductHistoryModalProps {
  product: ProductItem;
  onClose: () => void;
  onNotify: (msg: string, type?: 'success' | 'warning' | 'error') => void;
}

const ProductHistoryModal: React.FC<ProductHistoryModalProps> = ({
  product,
  onClose,
  onNotify,
}) => {
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/products/${product.id}/history`);
        if (res.ok) {
          const data = await res.json();
          setRows(data.rows || []);
        }
      } catch (e) {
        console.error(e);
        onNotify('Erro ao carregar histórico do produto.', 'error');
      } finally {
        setLoading(false);
      }
    })();
  }, [product.id, onNotify]);

  const handleExportCsv = () => {
    if (rows.length === 0) return;
    const header = 'Data/Hora,Custo\n';
    const body = rows
      .map((r) => `"${r.date_fmt.replace(' (Hoje)', '')}","${r.cost_fmt.replace('R$', '').trim()}"`)
      .join('\n');
    const blob = new Blob([header + body], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `historico_produto_${product.code || product.id}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    onNotify('Histórico do produto exportado com sucesso!', 'success');
  };

  return (
    <div className="fixed inset-0 bg-black/45 backdrop-blur-[1px] flex items-center justify-center z-50 p-4">
      <div className="w-full max-w-[520px] max-h-[90vh] overflow-y-auto rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#E2EAF5] dark:border-[#1E3156] mb-4">
          <div>
            <h3 className="text-[17px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              Histórico de Custo: {product.name}
            </h3>
            <span className="text-[12px] text-[#687796] dark:text-[#93A4C6]">
              {product.code} • Preço de Venda: {product.sale_price_fmt}
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-7 h-7 rounded-full flex items-center justify-center text-[#687796] hover:bg-black/5 dark:hover:bg-white/10"
          >
            ✕
          </button>
        </div>

        {/* Table */}
        <div className="rounded-[14px] bg-[#F4F7FC] dark:bg-[#0B1730] border border-[#DDE5F2] dark:border-[#1E3156] overflow-hidden mb-4">
          <div className="flex items-center h-[36px] bg-[#EBF1F9] dark:bg-[#192A4A] px-4 text-[12px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
            <span className="flex-1">Data / Hora</span>
            <span className="w-28 text-right">Custo Produção</span>
          </div>
          <div className="max-h-[260px] overflow-y-auto divide-y divide-[#E2EAF5] dark:divide-[#1E3156]">
            {loading ? (
              <div className="p-6 text-center text-[12.5px] text-[#687796]">
                Carregando histórico...
              </div>
            ) : rows.length === 0 ? (
              <div className="p-6 text-center text-[12.5px] text-[#8C9BB5]">
                Nenhum histórico registrado ainda.
              </div>
            ) : (
              rows.map((r, i) => (
                <div
                  key={i}
                  className={`flex items-center px-4 py-2.5 text-[12.5px] ${
                    r.is_today
                      ? 'bg-[#FFF8EE] dark:bg-[#20170F] font-bold'
                      : 'text-[#18223A] dark:text-[#F4F7FF]'
                  }`}
                >
                  <div className="flex-1 flex items-center gap-2">
                    <span>{r.date_fmt.replace(' (Hoje)', '')}</span>
                    {r.is_today && (
                      <span className="px-2 py-0.5 rounded-full text-[10.5px] bg-[#FFF0D8] text-[#F28C28] dark:bg-[#3D2514]">
                        Atual
                      </span>
                    )}
                  </div>
                  <span className="w-28 text-right font-bold">{r.cost_fmt}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-2">
          <RoundedActionButton
            label="Fechar"
            onClick={onClose}
            variant="secondary"
            height={36}
          />
          <RoundedActionButton
            label="Baixar Histórico"
            onClick={handleExportCsv}
            variant="green"
            icon={
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            }
            height={36}
          />
        </div>
      </div>
    </div>
  );
};
