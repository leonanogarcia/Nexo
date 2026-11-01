import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ConversionItem,
  DeleteCheckResponse,
  MaterialOption,
  RecipeHistoryRow,
  RecipeItem,
} from '../types';
import {
  CapsuleInput,
  ChevronDownIcon,
  ChevronRightIcon,
  ClockIcon,
  DuplicateIcon,
  GearPolygonIcon,
  NexoCheckbox,
  PlusIcon,
  RoundedActionButton,
  RoundedDropdown,
  RoundedEntry,
  RulerConversionIcon,
  TrashIcon,
} from './DesignSystem';
import { ConversionsModal } from './ConversionsModal';

interface RecipesPageProps {
  units: string[];
  initialHiddenCols: string[];
  onNotify: (msg: string, type?: 'success' | 'warning' | 'error') => void;
  dark: boolean;
}

const REC_COLUMNS: { key: string; label: string; width: number; minWidth: number; align?: 'left' | 'center' | 'right' }[] = [
  { key: 'code', label: 'Código', width: 95, minWidth: 80, align: 'center' },
  { key: 'name', label: 'Nome da Receita', width: 340, minWidth: 220, align: 'left' },
  { key: 'yield', label: 'Rendimento', width: 130, minWidth: 100, align: 'center' },
  { key: 'total_cost', label: 'Custo Total', width: 130, minWidth: 100, align: 'right' },
  { key: 'portion_cost', label: 'Custo / Porção', width: 130, minWidth: 100, align: 'right' },
  { key: 'date', label: 'Data', width: 110, minWidth: 90, align: 'center' },
  { key: 'status', label: 'Status', width: 100, minWidth: 80, align: 'center' },
];

export const RecipesPage: React.FC<RecipesPageProps> = ({
  units,
  initialHiddenCols,
  onNotify,
  dark,
}) => {
  const [items, setItems] = useState<RecipeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'Ativos' | 'Inativos' | 'Todos'>('Ativos');

  // Multi-selection & row active focus
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [checkedIds, setCheckedIds] = useState<Set<number>>(new Set());

  // Expandable ingredient rows in table
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  // Column width & visibility persistence
  const [hiddenCols, setHiddenCols] = useState<string[]>(initialHiddenCols || ['code']);
  const [colWidths, setColWidths] = useState<Record<string, number>>(() => {
    const map: Record<string, number> = {};
    REC_COLUMNS.forEach((c) => {
      map[c.key] = c.width;
    });
    return map;
  });

  // Sorting
  const [sortKey, setSortKey] = useState<string>('name');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  // Column visibility menu
  const [colMenuOpen, setColMenuOpen] = useState(false);
  const colMenuRef = useRef<HTMLDivElement>(null);

  // Floating 3-Dots Row Menu
  const [rowMenu, setRowMenu] = useState<{
    item: RecipeItem;
    x: number;
    y: number;
  } | null>(null);
  const rowMenuRef = useRef<HTMLDivElement>(null);

  // Modals state
  const [formModal, setFormModal] = useState<{
    open: boolean;
    editItem: RecipeItem | null;
  }>({ open: false, editItem: null });

  const [historyModal, setHistoryModal] = useState<{
    open: boolean;
    recipe: RecipeItem | null;
  }>({ open: false, recipe: null });

  const [conversionModalOpen, setConversionModalOpen] = useState(false);

  const [deleteModal, setDeleteModal] = useState<{
    open: boolean;
    check: DeleteCheckResponse;
    ids: number[];
  } | null>(null);

  // Close popups on click outside
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

  const visibleColumns = useMemo(
    () => REC_COLUMNS.filter((c) => !hiddenCols.includes(c.key)),
    [hiddenCols]
  );

  const toggleColumnVisibility = async (key: string) => {
    const next = hiddenCols.includes(key)
      ? hiddenCols.filter((k) => k !== key)
      : [...hiddenCols, key];
    setHiddenCols(next);
    try {
      await fetch('/api/settings/rec_hidden_cols', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: next }),
      });
    } catch (e) {
      console.error('Falha ao salvar colunas ocultas de receitas:', e);
    }
  };

  // Fetch recipes list
  const fetchRecipes = useCallback(async () => {
    setLoading(true);
    try {
      const q = new URLSearchParams();
      if (search.trim()) q.set('search', search.trim());
      if (statusFilter === 'Ativos') q.set('status', 'active');
      else if (statusFilter === 'Inativos') q.set('status', 'inactive');

      const res = await fetch(`/api/recipes?${q.toString()}`);
      if (res.ok) {
        const data: RecipeItem[] = await res.json();
        setItems(data);
      }
    } catch (e) {
      console.error(e);
      onNotify('Erro ao carregar receitas do servidor.', 'error');
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, onNotify]);

  useEffect(() => {
    fetchRecipes();
  }, [fetchRecipes]);

  // Sorting Handler
  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortedItems = useMemo(() => {
    const arr = [...items];
    arr.sort((a, b) => {
      let va: any = '';
      let vb: any = '';
      if (sortKey === 'name') {
        va = a.name.toLowerCase();
        vb = b.name.toLowerCase();
      } else if (sortKey === 'code') {
        va = a.code;
        vb = b.code;
      } else if (sortKey === 'yield') {
        va = a.yield_qty;
        vb = b.yield_qty;
      } else if (sortKey === 'total_cost') {
        va = a.total_cost;
        vb = b.total_cost;
      } else if (sortKey === 'portion_cost') {
        va = a.portion_cost;
        vb = b.portion_cost;
      } else if (sortKey === 'date') {
        va = a.created_at;
        vb = b.created_at;
      } else if (sortKey === 'status') {
        va = a.active ? 1 : 0;
        vb = b.active ? 1 : 0;
      }
      if (va < vb) return sortDir === 'asc' ? -1 : 1;
      if (va > vb) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return arr;
  }, [items, sortKey, sortDir]);

  // Selection Logic
  const allIds = useMemo(() => sortedItems.map((i) => i.id), [sortedItems]);
  const isAllChecked = allIds.length > 0 && allIds.every((id) => checkedIds.has(id));
  const isPartiallyChecked = allIds.some((id) => checkedIds.has(id)) && !isAllChecked;

  const toggleSelectAll = () => {
    if (isAllChecked) {
      setCheckedIds(new Set());
    } else {
      setCheckedIds(new Set(allIds));
    }
  };

  const toggleRowCheckbox = (id: number) => {
    const next = new Set(checkedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setCheckedIds(next);
  };

  const selectSingleRow = (id: number) => {
    setSelectedId(id);
    setCheckedIds(new Set([id]));
  };

  const toggleExpandRow = (id: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Duplicate recipe action
  const handleDuplicateRecipe = async (recipe: RecipeItem) => {
    try {
      const res = await fetch(`/api/recipes/${recipe.id}/duplicate`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) {
        onNotify(data.detail || 'Não foi possível duplicar a receita.', 'error');
        return;
      }
      await fetchRecipes();
      onNotify(`Receita duplicada como "${data.name}".`, 'success');
    } catch (e: any) {
      onNotify('Erro de conexão ao duplicar receita.', 'error');
    }
  };

  // Toggle active action
  const handleToggleActive = async (recipe: RecipeItem, active: boolean) => {
    try {
      const res = await fetch(`/api/recipes/${recipe.id}/active`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active }),
      });
      const data = await res.json();
      if (!res.ok) {
        onNotify(data.detail || 'Não foi possível alterar o status.', 'error');
        return;
      }
      await fetchRecipes();
      onNotify(data.message, 'success');
    } catch (e) {
      onNotify('Erro ao alterar status da receita.', 'error');
    }
  };

  // Delete Check
  const triggerDeleteCheck = async (targetIds?: number[]) => {
    const ids =
      targetIds && targetIds.length > 0
        ? targetIds
        : checkedIds.size > 0
        ? Array.from(checkedIds)
        : selectedId
        ? [selectedId]
        : [];
    if (ids.length === 0) {
      onNotify('Selecione ao menos uma receita para excluir.', 'warning');
      return;
    }
    try {
      const res = await fetch('/api/recipes/delete-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids }),
      });
      if (res.ok) {
        const check: DeleteCheckResponse = await res.json();
        if (check.total > 0) {
          setDeleteModal({ open: true, check, ids });
        }
      } else {
        onNotify('Falha ao verificar dependências da receita.', 'error');
      }
    } catch (e) {
      onNotify('Erro de conexão com o servidor.', 'error');
    }
  };

  const executeDelete = async () => {
    if (!deleteModal) return;
    try {
      const res = await fetch('/api/recipes/delete-execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: deleteModal.ids }),
      });
      const data = await res.json();
      if (!res.ok) {
        onNotify(data.detail || 'Erro ao processar exclusão.', 'error');
        return;
      }
      setDeleteModal(null);
      setCheckedIds(new Set());
      await fetchRecipes();
      onNotify(data.message, 'success');
    } catch (e) {
      onNotify('Erro de conexão ao excluir receita.', 'error');
    }
  };

  // Open modals
  const openNewRecipe = () => {
    if (checkedIds.size >= 2) setCheckedIds(new Set());
    setFormModal({ open: true, editItem: null });
  };

  const openEditRecipe = (item?: RecipeItem) => {
    const target =
      item ||
      items.find((i) => i.id === selectedId) ||
      (checkedIds.size === 1 ? items.find((i) => checkedIds.has(i.id)) : undefined);
    if (!target) {
      onNotify('Selecione uma receita na tabela para editar.', 'warning');
      return;
    }
    if (!target.active) {
      onNotify('Receitas inativas não podem ser editadas. Ative a receita primeiro.', 'warning');
      return;
    }
    setFormModal({ open: true, editItem: target });
  };

  const openHistory = (item?: RecipeItem) => {
    const target =
      item ||
      items.find((i) => i.id === selectedId) ||
      (checkedIds.size === 1 ? items.find((i) => checkedIds.has(i.id)) : undefined);
    if (!target) {
      onNotify('Selecione uma receita para ver o histórico.', 'warning');
      return;
    }
    setHistoryModal({ open: true, recipe: target });
  };

  // Resizing logic
  const resizingRef = useRef<{ colKey: string; startX: number; startW: number } | null>(null);
  const handleResizeStart = (e: React.MouseEvent, colKey: string) => {
    e.preventDefault();
    e.stopPropagation();
    resizingRef.current = {
      colKey,
      startX: e.clientX,
      startW: colWidths[colKey] || 100,
    };
    const onMouseMove = (ev: MouseEvent) => {
      if (!resizingRef.current) return;
      const { colKey, startX, startW } = resizingRef.current;
      const colDef = REC_COLUMNS.find((c) => c.key === colKey);
      const minW = colDef ? colDef.minWidth : 60;
      const newW = Math.max(minW, startW + (ev.clientX - startX));
      setColWidths((prev) => ({ ...prev, [colKey]: newW }));
    };
    const onMouseUp = () => {
      resizingRef.current = null;
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  const isBulkMode = checkedIds.size >= 2;

  return (
    <div className="flex flex-col h-full w-full">
      {/* 1. Toolbar Principal (RoundedPanel radius=22px, height=64px) */}
      <div className="h-[64px] w-full rounded-[22px] bg-white dark:bg-[#111F3B] px-6 mb-2 flex items-center justify-between shrink-0 shadow-sm transition-colors">
        {/* Left Action Buttons */}
        <div className="flex items-center gap-2.5">
          {!isBulkMode ? (
            <>
              <RoundedActionButton
                label="Nova Receita"
                onClick={openNewRecipe}
                variant="primary"
                icon={<PlusIcon size={16} strokeWidth={2.6} />}
                height={38}
              />
              <RoundedActionButton
                label="Conversões"
                onClick={() => setConversionModalOpen(true)}
                variant="soft"
                icon={<RulerConversionIcon size={16} />}
                height={38}
              />
              <RoundedActionButton
                label="Histórico"
                onClick={() => openHistory()}
                variant="soft"
                icon={<ClockIcon size={16} />}
                height={38}
              />
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

        {/* Right Search & Filter Controls */}
        <div className="flex items-center gap-3.5">
          <RoundedDropdown
            value={statusFilter}
            onChange={(v) => setStatusFilter(v as any)}
            options={['Ativos', 'Inativos', 'Todos']}
            width={105}
          />

          {/* Search Capsule Input */}
          <div className="relative">
            <RoundedEntry
              placeholder="Buscar receita ou ingrediente..."
              value={search}
              onChange={setSearch}
              width={260}
              height={32}
              spellCheck={false}
              className="pl-8 pr-7"
            />
            <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#8C9BB5] dark:text-[#64748B] text-xs pointer-events-none">
              🔍
            </span>
            {search && (
              <button
                type="button"
                onClick={() => setSearch('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8C9BB5] hover:text-[#18223A] dark:hover:text-[#F4F7FF] text-xs"
              >
                ✕
              </button>
            )}
          </div>

          {/* Column Visibility Gear Popup */}
          <div className="relative" ref={colMenuRef}>
            <button
              type="button"
              onClick={() => setColMenuOpen(!colMenuOpen)}
              title="Colunas visíveis"
              className="w-8 h-8 rounded-full flex items-center justify-center text-[#687796] dark:text-[#93A4C6] hover:bg-[#F4F7FC] dark:hover:bg-[#1C2F52] cursor-pointer transition-colors"
            >
              <GearPolygonIcon size={16} />
            </button>

            {colMenuOpen && (
              <div className="absolute right-0 top-10 w-48 rounded-[16px] bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] shadow-xl p-3 z-30 select-none">
                <span className="block text-[11px] font-bold uppercase tracking-wider text-[#8C9BB5] mb-2 px-1">
                  Colunas visíveis
                </span>
                <div className="space-y-1.5">
                  {REC_COLUMNS.map((col) => {
                    const isVisible = !hiddenCols.includes(col.key);
                    return (
                      <label
                        key={col.key}
                        className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-[#F4F7FC] dark:hover:bg-[#162747] cursor-pointer text-[13px] text-[#18223A] dark:text-[#F4F7FF]"
                      >
                        <NexoCheckbox
                          checked={isVisible}
                          onChange={() => toggleColumnVisibility(col.key)}
                        />
                        <span>{col.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 2. Tabela Principal de Receitas Base */}
      <div className="flex-1 min-h-0 w-full rounded-[22px] bg-white dark:bg-[#111F3B] p-3 flex flex-col shadow-sm transition-colors overflow-hidden">
        <div className="flex-1 min-h-0 flex flex-col overflow-x-auto overflow-y-hidden">
          {/* Header Row */}
          <div className="flex items-center h-[38px] rounded-full bg-[#EBF1F9] dark:bg-[#192A4A] text-[#18223A] dark:text-[#F4F7FF] text-[12px] font-bold shrink-0 select-none mb-1">
            {/* Expand all / collapse indicator */}
            <div className="w-[36px] flex items-center justify-center shrink-0">
              <span className="text-[10px] text-[#8C9BB5]">Ficha</span>
            </div>

            {/* Checkbox All */}
            <div className="w-[42px] flex items-center justify-center shrink-0">
              <NexoCheckbox
                checked={isAllChecked}
                indeterminate={isPartiallyChecked}
                onChange={toggleSelectAll}
              />
            </div>

            {visibleColumns.map((col) => {
              const w = colWidths[col.key] || col.width;
              const isSorted = sortKey === col.key;
              return (
                <div
                  key={col.key}
                  style={{ width: `${w}px` }}
                  className="relative flex items-center px-3 h-full shrink-0 group cursor-pointer"
                  onClick={() => handleSort(col.key)}
                >
                  <span
                    className={`truncate ${
                      col.align === 'center'
                        ? 'mx-auto text-center'
                        : col.align === 'right'
                        ? 'ml-auto text-right'
                        : 'text-left'
                    }`}
                  >
                    {col.label}
                  </span>
                  {isSorted && (
                    <span className="ml-1 text-[10px] text-[#F28C28]">
                      {sortDir === 'asc' ? '▲' : '▼'}
                    </span>
                  )}
                  {/* Draggable Resizer */}
                  <div
                    onMouseDown={(e) => handleResizeStart(e, col.key)}
                    onClick={(e) => e.stopPropagation()}
                    className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-4 cursor-col-resize opacity-0 group-hover:opacity-100 flex items-center justify-center"
                  >
                    <span className="w-[1.5px] h-3 bg-[#8C9BB5]" />
                  </div>
                </div>
              );
            })}

            {/* Actions Header */}
            <div className="w-[105px] ml-auto flex items-center justify-end pr-4 shrink-0 text-[#8C9BB5] text-[11px] uppercase tracking-wider font-semibold">
              Ações
            </div>
          </div>

          {/* Table Body / Rows */}
          <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0 space-y-1 pr-1">
            {loading ? (
              <div className="h-48 flex items-center justify-center text-[#687796] text-[13px]">
                Carregando receitas...
              </div>
            ) : sortedItems.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center text-center">
                <img
                  src="/ui_assets/empty_state_reference_exact.png"
                  alt=""
                  className="w-28 h-28 object-contain mb-2 opacity-85"
                />
                <span className="text-[14.5px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  Nenhuma receita encontrada
                </span>
                <span className="text-[12.5px] text-[#687796] dark:text-[#93A4C6] mt-0.5 max-w-sm">
                  {search
                    ? 'Tente ajustar os termos da sua busca.'
                    : 'Clique em "+ Nova Receita" acima para montar a sua primeira ficha técnica.'}
                </span>
              </div>
            ) : (
              sortedItems.map((item) => {
                const isChecked = checkedIds.has(item.id);
                const isSelected = selectedId === item.id;
                const isExpanded = expandedIds.has(item.id);

                const rowBg = isSelected
                  ? 'bg-[#FFE6D0] dark:bg-[#3D2514]'
                  : isChecked
                  ? 'bg-[#F4F7FC] dark:bg-[#162747]'
                  : 'hover:bg-[#F9FBFC] dark:hover:bg-[#162747]/60';

                return (
                  <div key={item.id} className="flex flex-col rounded-[16px] overflow-hidden">
                    {/* Main Row */}
                    <div
                      onClick={() => setSelectedId(item.id)}
                      onDoubleClick={() => openEditRecipe(item)}
                      className={`flex items-center h-[42px] px-0 rounded-[16px] text-[13px] text-[#18223A] dark:text-[#F4F7FF] transition-colors cursor-pointer select-none ${rowBg}`}
                    >
                      {/* Chevron Expand Button */}
                      <div className="w-[36px] flex items-center justify-center shrink-0">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleExpandRow(item.id);
                          }}
                          title={isExpanded ? 'Ocultar ingredientes' : 'Ver ingredientes'}
                          className="w-6 h-6 rounded-full flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/10 text-[#687796] dark:text-[#93A4C6]"
                        >
                          {isExpanded ? <ChevronDownIcon size={14} /> : <ChevronRightIcon size={14} />}
                        </button>
                      </div>

                      {/* Checkbox */}
                      <div className="w-[42px] flex items-center justify-center shrink-0">
                        <NexoCheckbox
                          checked={isChecked}
                          onChange={() => toggleRowCheckbox(item.id)}
                        />
                      </div>

                      {/* Visible Columns */}
                      {visibleColumns.map((col) => {
                        const w = colWidths[col.key] || col.width;
                        let content: React.ReactNode = '-';

                        if (col.key === 'code') {
                          content = (
                            <span className="font-mono text-[11px] font-bold text-[#687796] dark:text-[#93A4C6]">
                              {item.code}
                            </span>
                          );
                        } else if (col.key === 'name') {
                          content = (
                            <span className="font-semibold text-[#18223A] dark:text-[#F4F7FF] truncate">
                              {item.name}
                            </span>
                          );
                        } else if (col.key === 'yield') {
                          content = (
                            <span className="text-[#18223A] dark:text-[#F4F7FF]">
                              <strong>{item.yield_qty_fmt}</strong> {item.yield_unit}
                            </span>
                          );
                        } else if (col.key === 'total_cost') {
                          content = (
                            <span className="font-bold text-[#18223A] dark:text-[#F4F7FF]">
                              {item.total_cost_fmt}
                            </span>
                          );
                        } else if (col.key === 'portion_cost') {
                          content = (
                            <span className="font-semibold text-[#1E833F] dark:text-[#61E3B9]">
                              {item.portion_cost_fmt}
                            </span>
                          );
                        } else if (col.key === 'date') {
                          content = (
                            <span className="text-[12px] text-[#687796] dark:text-[#93A4C6]">
                              {item.created_at}
                            </span>
                          );
                        } else if (col.key === 'status') {
                          content = item.active ? (
                            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#EAFaf1] dark:bg-[#12372E] text-[#1E833F] dark:text-[#61E3B9]">
                              Ativo
                            </span>
                          ) : (
                            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#F1F5F9] dark:bg-[#1E293B] text-[#64748B] dark:text-[#94A3B8]">
                              Inativo
                            </span>
                          );
                        }

                        return (
                          <div
                            key={col.key}
                            style={{ width: `${w}px` }}
                            className={`px-3 truncate shrink-0 ${
                              col.align === 'center'
                                ? 'text-center'
                                : col.align === 'right'
                                ? 'text-right'
                                : 'text-left'
                            }`}
                          >
                            {content}
                          </div>
                        );
                      })}

                      {/* Row Actions */}
                      <div className="w-[105px] ml-auto flex items-center justify-end pr-3 gap-1.5 shrink-0">
                        {/* Edit Button */}
                        <button
                          type="button"
                          disabled={!item.active}
                          onClick={(e) => {
                            e.stopPropagation();
                            selectSingleRow(item.id);
                            openEditRecipe(item);
                          }}
                          title={item.active ? 'Editar' : 'Editar (Desativado)'}
                          className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-30 cursor-pointer disabled:cursor-default"
                        >
                          <img
                            src="/ui_assets/action_edit_reference_exact.png"
                            alt="Editar"
                            className="w-3.5 h-3.5 object-contain"
                          />
                        </button>

                        {/* Delete Button */}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            selectSingleRow(item.id);
                            triggerDeleteCheck([item.id]);
                          }}
                          title="Excluir"
                          className="w-7 h-7 rounded-full flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer"
                        >
                          <img
                            src="/ui_assets/action_delete_reference_exact.png"
                            alt="Excluir"
                            className="w-3.5 h-3.5 object-contain"
                          />
                        </button>

                        {/* 3-Dots Menu Button */}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            selectSingleRow(item.id);
                            const rect = e.currentTarget.getBoundingClientRect();
                            setRowMenu({
                              item,
                              x: rect.right - 180,
                              y: rect.bottom + 4,
                            });
                          }}
                          title="Mais opções"
                          className="w-7 h-7 rounded-full flex flex-col items-center justify-center gap-[2.5px] hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer"
                        >
                          <span className="w-[3px] h-[3px] rounded-full bg-[#333333] dark:bg-[#F4F7FF]" />
                          <span className="w-[3px] h-[3px] rounded-full bg-[#333333] dark:bg-[#F4F7FF]" />
                          <span className="w-[3px] h-[3px] rounded-full bg-[#333333] dark:bg-[#F4F7FF]" />
                        </button>
                      </div>
                    </div>

                    {/* Sub-panel of Ingredients (Expanded) */}
                    {isExpanded && (
                      <div className="mx-3 my-1.5 p-3.5 rounded-[14px] bg-[#F8FAFC] dark:bg-[#0E1A30] border border-[#E2EAF5] dark:border-[#1E3156] flex flex-col">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[11.5px] font-bold uppercase tracking-wider text-[#687796] dark:text-[#93A4C6]">
                            Composição da Receita ({item.items_count} ingredientes)
                          </span>
                          <span className="text-[12px] font-semibold text-[#18223A] dark:text-[#F4F7FF]">
                            Rendimento: <strong>{item.yield_qty_fmt} {item.yield_unit}</strong> • Custo: <strong>{item.total_cost_fmt}</strong>
                          </span>
                        </div>

                        {item.items.length === 0 ? (
                          <span className="text-[12px] text-[#8C9BB5] italic">
                            Nenhum ingrediente adicionado a esta receita ainda.
                          </span>
                        ) : (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
                            {item.items.map((ing, idx) => (
                              <div
                                key={idx}
                                className="flex items-center justify-between p-2 rounded-[10px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] text-[12.5px]"
                              >
                                <div className="flex items-center gap-2 truncate">
                                  <span className="w-1.5 h-1.5 rounded-full bg-[#F28C28]" />
                                  <span className="font-semibold text-[#18223A] dark:text-[#F4F7FF] truncate">
                                    {ing.material_name}
                                  </span>
                                  {ing.material_brand && (
                                    <span className="text-[11px] text-[#687796] dark:text-[#93A4C6]">
                                      ({ing.material_brand})
                                    </span>
                                  )}
                                </div>
                                <div className="flex items-center gap-3 shrink-0 ml-2">
                                  <span className="text-[#475569] dark:text-[#AFC0E2] font-medium">
                                    {ing.qty_fmt} {ing.unit}
                                  </span>
                                  <span className="font-bold text-[#18223A] dark:text-[#F4F7FF]">
                                    {ing.cost_fmt}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
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
              openEditRecipe(target);
            }}
            className="w-full h-[34px] px-3.5 flex items-center gap-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#F4F7FC] dark:hover:bg-[#20375F] disabled:opacity-35 cursor-pointer disabled:cursor-default"
          >
            <img src="/ui_assets/action_edit_reference_exact.png" alt="" className="w-4 h-4" />
            <span>{rowMenu.item.active ? 'Editar' : 'Editar (Desativado)'}</span>
          </button>

          <button
            type="button"
            onClick={() => {
              const target = rowMenu.item;
              setRowMenu(null);
              handleDuplicateRecipe(target);
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
              triggerDeleteCheck([target.id]);
            }}
            className="w-full h-[34px] px-3.5 flex items-center gap-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#F4F7FC] dark:hover:bg-[#20375F] cursor-pointer"
          >
            <img src="/ui_assets/action_delete_reference_exact.png" alt="" className="w-4 h-4" />
            <span>Excluir</span>
          </button>

          <div className="my-1 mx-3 border-t border-[#DDE5F2] dark:border-[#24385E]" />

          <button
            type="button"
            disabled={rowMenu.item.active}
            onClick={() => {
              const target = rowMenu.item;
              setRowMenu(null);
              handleToggleActive(target, true);
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
              handleToggleActive(target, false);
            }}
            className="w-full h-[34px] px-3.5 flex items-center gap-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] hover:bg-[#F4F7FC] dark:hover:bg-[#20375F] disabled:opacity-35 cursor-pointer disabled:cursor-default"
          >
            <span className="w-4 text-center text-[#687796] dark:text-[#AFC0E2]">⏸</span>
            <span>Desativar</span>
          </button>
        </div>
      )}

      {/* Modal: Nova / Editar Receita */}
      {formModal.open && (
        <RecipeFormModal
          editItem={formModal.editItem}
          units={units}
          onClose={() => setFormModal({ open: false, editItem: null })}
          onSaved={async () => {
            setFormModal({ open: false, editItem: null });
            await fetchRecipes();
            onNotify('Receita salva com sucesso!', 'success');
          }}
          onNotify={onNotify}
        />
      )}

      {/* Modal: Histórico de Custos da Receita */}
      {historyModal.open && historyModal.recipe && (
        <RecipeHistoryModal
          recipe={historyModal.recipe}
          onClose={() => setHistoryModal({ open: false, recipe: null })}
          onNotify={onNotify}
        />
      )}

      {/* Modal: Conversões de Medidas */}
      {conversionModalOpen && (
        <ConversionsModal
          onClose={() => setConversionModalOpen(false)}
          onNotify={onNotify}
        />
      )}

      {/* Modal: Exclusão Inteligente de Receitas */}
      {deleteModal && deleteModal.open && (
        <div className="fixed inset-0 bg-black/45 backdrop-blur-[1px] flex items-center justify-center z-50">
          <div className="w-[540px] rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col">
            <h3 className="text-[18px] font-bold text-[#18223A] dark:text-[#F4F7FF] text-center mb-3">
              {deleteModal.check.total === 1 ? 'Excluir Receita' : 'Exclusão em Lote de Receitas'}
            </h3>

            <div className="text-[13px] text-[#18223A] dark:text-[#F4F7FF] space-y-3 mb-5">
              {deleteModal.check.linked.length > 0 && (
                <div className="p-3.5 rounded-[14px] bg-[#FFF8EE] dark:bg-[#2A1E14] border border-[#F28C28]/40">
                  <span className="block font-bold text-[#F28C28] mb-1">
                    ⚠️ Atenção: Receita em uso em Produtos
                  </span>
                  <p className="text-[12.5px] text-[#687796] dark:text-[#CBD5E1] leading-relaxed">
                    {deleteModal.check.linked.length === 1
                      ? `A receita "${deleteModal.check.linked[0].name}" compõe produtos cadastrados. Para não quebrar a ficha técnica desses produtos, ela será inativada/arquivada.`
                      : `${deleteModal.check.linked.length} receitas compõem produtos cadastrados e serão inativadas para manter a integridade dos custos.`}
                  </p>
                </div>
              )}

              {deleteModal.check.unlinked.length > 0 && (
                <p className="text-[13px] text-[#475569] dark:text-[#AFC0E2]">
                  {deleteModal.check.unlinked.length === 1
                    ? `A receita "${deleteModal.check.unlinked[0].name}" será excluída permanentemente.`
                    : `${deleteModal.check.unlinked.length} receitas sem vínculos serão excluídas permanentemente.`}
                </p>
              )}
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-[#E2EAF5] dark:border-[#24385E]">
              <RoundedActionButton
                label="Cancelar"
                onClick={() => setDeleteModal(null)}
                variant="ghost"
                height={38}
              />
              <RoundedActionButton
                label="Confirmar Exclusão"
                onClick={executeDelete}
                variant="danger"
                height={38}
                width={170}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// =====================================================================
// Sub-Component: RecipeFormModal (Nova / Editar Receita com Cálculo Vivo)
// =====================================================================

interface RecipeFormModalProps {
  editItem: RecipeItem | null;
  units: string[];
  onClose: () => void;
  onSaved: () => void;
  onNotify: (msg: string, type?: 'success' | 'warning' | 'error') => void;
}

interface FormIngredientRow {
  material_id: number;
  material_name: string;
  material_brand: string;
  qty: string;
  unit: string;
  cost_fmt: string;
  available_units: string[];
}

const RecipeFormModal: React.FC<RecipeFormModalProps> = ({
  editItem,
  units,
  onClose,
  onSaved,
  onNotify,
}) => {
  const [name, setName] = useState(editItem ? editItem.name : '');
  const [yieldQty, setYieldQty] = useState(editItem ? String(editItem.yield_qty) : '1');
  const [yieldUnit, setYieldUnit] = useState(editItem ? editItem.yield_unit : 'un');
  const [notes, setNotes] = useState(editItem ? editItem.notes : '');

  const [materials, setMaterials] = useState<MaterialOption[]>([]);
  const [ingredients, setIngredients] = useState<FormIngredientRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Live preview totals
  const [totalCostFmt, setTotalCostFmt] = useState(editItem ? editItem.total_cost_fmt : 'R$ 0,00');
  const [portionCostFmt, setPortionCostFmt] = useState(editItem ? editItem.portion_cost_fmt : 'R$ 0,00');

  // Load active materials options
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/materials/options');
        if (res.ok) {
          const data: MaterialOption[] = await res.json();
          setMaterials(data);
        }
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  // Pre-load ingredients if editing
  useEffect(() => {
    if (editItem && editItem.items) {
      const rows: FormIngredientRow[] = editItem.items.map((it) => ({
        material_id: it.material_id,
        material_name: it.material_name,
        material_brand: it.material_brand,
        qty: String(it.qty),
        unit: it.unit,
        cost_fmt: it.cost_fmt,
        available_units: [it.unit, it.material_unit],
      }));
      setIngredients(rows);
    }
  }, [editItem]);

  // Recalculate live preview
  const recalculatePreview = useCallback(async (rows: FormIngredientRow[], yQty: string, yUnit: string) => {
    try {
      const payload = {
        yield_qty: yQty || '1',
        yield_unit: yUnit || 'un',
        items: rows.map((r) => ({
          material_id: r.material_id,
          qty: r.qty || '0',
          unit: r.unit || 'g',
        })),
      };
      const res = await fetch('/api/recipes/preview-cost', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        setTotalCostFmt(data.total_cost_fmt);
        setPortionCostFmt(data.portion_cost_fmt);
        // Update individual ingredient formatted costs
        setIngredients((prev) =>
          prev.map((r, idx) => ({
            ...r,
            cost_fmt: data.items[idx] ? data.items[idx].cost_fmt : 'R$ 0,00',
          }))
        );
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  // Add new ingredient row
  const addIngredientRow = () => {
    if (materials.length === 0) {
      onNotify('Nenhum insumo disponível para adicionar.', 'warning');
      return;
    }
    const firstMat = materials[0];
    const newRow: FormIngredientRow = {
      material_id: firstMat.id,
      material_name: firstMat.name,
      material_brand: '',
      qty: '100',
      unit: firstMat.purchase_unit || 'g',
      cost_fmt: 'R$ 0,00',
      available_units: [firstMat.purchase_unit || 'g'],
    };
    const nextRows = [...ingredients, newRow];
    setIngredients(nextRows);
    recalculatePreview(nextRows, yieldQty, yieldUnit);
  };

  const removeIngredientRow = (idx: number) => {
    const nextRows = ingredients.filter((_, i) => i !== idx);
    setIngredients(nextRows);
    recalculatePreview(nextRows, yieldQty, yieldUnit);
  };

  const updateIngredientRow = async (idx: number, patch: Partial<FormIngredientRow>) => {
    const nextRows = [...ingredients];
    const updated = { ...nextRows[idx], ...patch };

    // If material changed, fetch its conversions to populate available units
    if (patch.material_id && patch.material_id !== nextRows[idx].material_id) {
      const mat = materials.find((m) => m.id === patch.material_id);
      if (mat) {
        updated.material_name = mat.name;
        updated.unit = mat.purchase_unit;
        try {
          const cRes = await fetch(`/api/materials/${mat.id}/conversions`);
          if (cRes.ok) {
            const cList: ConversionItem[] = await cRes.json();
            const cUnits = cList.map((c) => c.name);
            updated.available_units = Array.from(new Set([mat.purchase_unit, ...cUnits]));
          }
        } catch (e) {
          updated.available_units = [mat.purchase_unit];
        }
      }
    }

    nextRows[idx] = updated;
    setIngredients(nextRows);
    recalculatePreview(nextRows, yieldQty, yieldUnit);
  };

  const handleSave = async () => {
    setError(null);
    const n = name.trim();
    if (!n) return setError('O nome da receita é obrigatório.');

    const yq = parseFloat(yieldQty.replace(',', '.'));
    if (isNaN(yq) || yq <= 0) return setError('O rendimento deve ser maior que zero.');

    const yu = yieldUnit.trim();
    if (!yu) return setError('A unidade de rendimento é obrigatória.');

    if (ingredients.length === 0) {
      return setError('Adicione ao menos um ingrediente à receita.');
    }

    const payload = {
      name: n,
      yield_qty: yq,
      yield_unit: yu,
      notes: notes.trim(),
      items: ingredients.map((it) => ({
        material_id: it.material_id,
        qty: parseFloat(it.qty.replace(',', '.')) || 0,
        unit: it.unit,
      })),
    };

    try {
      const url = editItem ? `/api/recipes/${editItem.id}` : '/api/recipes';
      const method = editItem ? 'PUT' : 'POST';
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Não foi possível salvar a receita.');
        return;
      }
      onSaved();
    } catch (e: any) {
      setError(e.message || 'Erro de conexão com o servidor.');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/45 backdrop-blur-[1px] flex items-center justify-center z-50">
      <div className="w-[740px] max-h-[90vh] rounded-[22px] bg-[#F4F7FC] dark:bg-[#0B1730] border border-[#DDE5F2] dark:border-[#24385E] shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 pt-4 pb-3 flex items-center justify-between border-b border-[#E2EAF5] dark:border-[#1E3156]">
          <div className="flex items-center gap-2.5">
            <h2 className="text-[17px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              {editItem ? 'Editar Receita' : 'Nova Receita'}
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
            className="w-7 h-7 rounded-full flex items-center justify-center text-[#687796] hover:bg-black/5 dark:hover:bg-white/10"
          >
            ✕
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {error && (
            <div className="p-3 rounded-[12px] bg-[#FFF5F5] dark:bg-[#3B1822] border border-[#FEB2B2] dark:border-[#6E2533] text-[12.5px] text-[#DC2626] dark:text-[#F87171]">
              {error}
            </div>
          )}

          {/* Section 1: Dados Gerais da Receita */}
          <div className="p-4 rounded-[16px] bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] space-y-3">
            <span className="block text-[11.5px] font-bold uppercase tracking-wider text-[#F28C28]">
              1. Identificação & Rendimento
            </span>

            <div>
              <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                Nome da Receita *
              </label>
              <CapsuleInput
                value={name}
                onChange={setName}
                placeholder="Ex: Massa de Bolo de Cenoura, Recheio de Ninho..."
              />
            </div>

            <div className="grid grid-cols-12 gap-3">
              <div className="col-span-6">
                <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                  Rendimento Total *
                </label>
                <CapsuleInput
                  value={yieldQty}
                  onChange={(v) => {
                    setYieldQty(v);
                    recalculatePreview(ingredients, v, yieldUnit);
                  }}
                  placeholder="Ex: 1200 ou 20"
                />
              </div>
              <div className="col-span-6">
                <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                  Unidade do Rendimento *
                </label>
                <CapsuleInput
                  value={yieldUnit}
                  onChange={(v) => {
                    setYieldUnit(v);
                    recalculatePreview(ingredients, yieldQty, v);
                  }}
                  placeholder="Ex: g, porções, fatias, unidades"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                Observações / Modo de Preparo (Opcional)
              </label>
              <textarea
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Dicas de ponto, forno, tempo de descanso..."
                className="w-full rounded-[14px] bg-[#F9FBFC] dark:bg-[#0E1B35] border border-[#DDE5F2] dark:border-[#24385E] p-2.5 text-[12.5px] text-[#18223A] dark:text-[#F4F7FF] focus:outline-none focus:border-[#F28C28]"
              />
            </div>
          </div>

          {/* Section 2: Composição de Ingredientes */}
          <div className="p-4 rounded-[16px] bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11.5px] font-bold uppercase tracking-wider text-[#F28C28]">
                2. Ingredientes da Ficha Técnica
              </span>
              <button
                type="button"
                onClick={addIngredientRow}
                className="h-[30px] px-3 rounded-full bg-[#FFF0D8] dark:bg-[#3D2514] hover:bg-[#F28C28] text-[#F28C28] hover:text-white dark:text-[#F28C28] dark:hover:text-white text-[12px] font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <span>+ Adicionar Ingrediente</span>
              </button>
            </div>

            {ingredients.length === 0 ? (
              <div className="py-6 text-center text-[#8C9BB5] text-[12.5px]">
                Nenhum ingrediente adicionado. Clique acima para começar a compor a receita.
              </div>
            ) : (
              <div className="space-y-2">
                {ingredients.map((ing, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-[14px] bg-[#F9FBFC] dark:bg-[#0E1A30] border border-[#E2EAF5] dark:border-[#24385E] flex items-center gap-2.5 text-[13px]"
                  >
                    {/* Material Selector */}
                    <div className="flex-1 min-w-0">
                      <select
                        value={ing.material_id}
                        onChange={(e) => updateIngredientRow(idx, { material_id: Number(e.target.value) })}
                        className="w-full h-[36px] rounded-full bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] px-3 text-[12.5px] text-[#18223A] dark:text-[#F4F7FF] focus:outline-none focus:border-[#F28C28]"
                      >
                        {materials.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Qty Input */}
                    <div className="w-[95px] shrink-0">
                      <CapsuleInput
                        value={ing.qty}
                        onChange={(v) => updateIngredientRow(idx, { qty: v })}
                        placeholder="Qtd"
                      />
                    </div>

                    {/* Unit Selector */}
                    <div className="w-[105px] shrink-0">
                      <CapsuleInput
                        value={ing.unit}
                        onChange={(v) => updateIngredientRow(idx, { unit: v })}
                        placeholder="Unidade"
                      />
                    </div>

                    {/* Calculated Cost */}
                    <div className="w-[95px] text-right font-bold text-[#18223A] dark:text-[#F4F7FF] shrink-0 text-[13px]">
                      {ing.cost_fmt}
                    </div>

                    {/* Remove Trash Button */}
                    <button
                      type="button"
                      onClick={() => removeIngredientRow(idx)}
                      title="Remover ingrediente"
                      className="w-7 h-7 rounded-full flex items-center justify-center text-[#DC2626] hover:bg-[#FEE2E2] dark:hover:bg-[#3D1822] cursor-pointer shrink-0"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 3: Summary KPI Card (Live preview) */}
          <div className="p-4 rounded-[16px] bg-[#FFF8EE] dark:bg-[#20170F] border border-[#F28C28]/40 flex items-center justify-around text-center">
            <div>
              <span className="block text-[11px] uppercase tracking-wider font-semibold text-[#8C9BB5]">
                Custo dos Ingredientes
              </span>
              <span className="text-[17px] font-bold text-[#F28C28]">
                {totalCostFmt}
              </span>
            </div>
            <div className="w-[1px] h-8 bg-[#F28C28]/25" />
            <div>
              <span className="block text-[11px] uppercase tracking-wider font-semibold text-[#8C9BB5]">
                Rendimento
              </span>
              <span className="text-[15px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                {yieldQty || '0'} {yieldUnit}
              </span>
            </div>
            <div className="w-[1px] h-8 bg-[#F28C28]/25" />
            <div>
              <span className="block text-[11px] uppercase tracking-wider font-semibold text-[#8C9BB5]">
                Custo por Porção / Unidade
              </span>
              <span className="text-[17px] font-bold text-[#1E833F] dark:text-[#61E3B9]">
                {portionCostFmt}
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-[#E2EAF5] dark:border-[#1E3156] flex items-center justify-between">
          <span className="text-[11.5px] italic text-[#687796] dark:text-[#93A4C6]">
            * campos obrigatórios
          </span>
          <div className="flex items-center gap-2">
            <RoundedActionButton
              label="Salvar Receita"
              onClick={handleSave}
              variant="primary"
              height={36}
            />
            <RoundedActionButton
              label="Cancelar"
              onClick={onClose}
              variant="secondary"
              height={36}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// =====================================================================
// Sub-Component: RecipeHistoryModal (Histórico de Custo da Receita)
// =====================================================================

interface RecipeHistoryModalProps {
  recipe: RecipeItem;
  onClose: () => void;
  onNotify: (msg: string, type?: 'success' | 'warning' | 'error') => void;
}

const RecipeHistoryModal: React.FC<RecipeHistoryModalProps> = ({
  recipe,
  onClose,
  onNotify,
}) => {
  const [rows, setRows] = useState<RecipeHistoryRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/recipes/${recipe.id}/history`);
        if (res.ok) {
          const data = await res.json();
          setRows(data.rows || []);
        }
      } catch (e) {
        console.error(e);
        onNotify('Erro ao carregar histórico da receita.', 'error');
      } finally {
        setLoading(false);
      }
    })();
  }, [recipe.id, onNotify]);

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
    a.download = `historico_receita_${recipe.code || recipe.id}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    onNotify('Histórico da receita exportado com sucesso!', 'success');
  };

  return (
    <div className="fixed inset-0 bg-black/45 backdrop-blur-[1px] flex items-center justify-center z-50">
      <div className="w-[520px] rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#E2EAF5] dark:border-[#1E3156] mb-4">
          <div>
            <h3 className="text-[17px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              Histórico de Custo: {recipe.name}
            </h3>
            <span className="text-[12px] text-[#687796] dark:text-[#93A4C6]">
              {recipe.code} • Rendimento: {recipe.yield_qty_fmt} {recipe.yield_unit}
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
            <span className="w-28 text-right">Custo da Receita</span>
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
            variant="ghost"
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
            width={160}
          />
        </div>
      </div>
    </div>
  );
};

