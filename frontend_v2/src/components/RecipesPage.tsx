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
  CapsuleQuantityUnit,
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
  FlameIcon,
  ZapEnergyIcon,
  DropletWaterIcon,
} from './DesignSystem';
import { ConversionsModal } from './ConversionsModal';

interface RecipesPageProps {
  units: string[];
  initialHiddenCols: string[];
  onNotify: (msg: string, type?: 'success' | 'warning' | 'error') => void;
  dark: boolean;
}

interface RecColumnSpec {
  key: string;
  label: string;
  width: number;
  align: 'left' | 'center';
  hideable: boolean;
}

const REC_COLUMNS: RecColumnSpec[] = [
  { key: 'code', label: 'Código', width: 95, align: 'center', hideable: true },
  { key: 'name', label: 'Nome da Receita', width: 280, align: 'left', hideable: false },
  { key: 'yield', label: 'Rendimento', width: 130, align: 'center', hideable: true },
  { key: 'total_cost', label: 'Custo Total', width: 140, align: 'center', hideable: true },
  { key: 'portion_cost', label: 'Custo / Porção', width: 140, align: 'center', hideable: true },
  { key: 'date', label: 'Data', width: 110, align: 'center', hideable: true },
  { key: 'status', label: 'Status', width: 90, align: 'center', hideable: true },
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
  const [orderBy, setOrderBy] = useState<string>('name');
  const [orderDir, setOrderDir] = useState<'ASC' | 'DESC'>('ASC');
  const [hiddenCols, setHiddenCols] = useState<string[]>(initialHiddenCols || ['code']);

  // Selection & Multiselection
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [checkedIds, setCheckedIds] = useState<Set<number>>(new Set());

  // Popups (Column Visibility Gear & Row 3-dots Menu)
  const [colMenuOpen, setColMenuOpen] = useState(false);
  const colMenuRef = useRef<HTMLDivElement>(null);

  const [rowMenu, setRowMenu] = useState<{
    item: RecipeItem;
    x: number;
    y: number;
  } | null>(null);
  const rowMenuRef = useRef<HTMLDivElement>(null);

  // Modals
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
      let cmp = 0;
      switch (orderBy) {
        case 'code':
          cmp = (a.code || '').localeCompare(b.code || '');
          break;
        case 'name':
          cmp = a.name.localeCompare(b.name, 'pt-BR', { sensitivity: 'base' });
          break;
        case 'yield':
          cmp = (a.yield_qty || 0) - (b.yield_qty || 0);
          break;
        case 'total_cost':
          cmp = (a.total_cost || 0) - (b.total_cost || 0);
          break;
        case 'portion_cost':
          cmp = (a.portion_cost || 0) - (b.portion_cost || 0);
          break;
        case 'date':
          cmp = (a.created_at || '').localeCompare(b.created_at || '');
          break;
        case 'status':
          cmp = (a.active ? 1 : 0) - (b.active ? 1 : 0);
          break;
      }
      return orderDir === 'ASC' ? cmp : -cmp;
    });
    return arr;
  }, [items, orderBy, orderDir]);

  // Selection Logic
  const isAllChecked = sortedItems.length > 0 && checkedIds.size === sortedItems.length;

  const toggleAllCheckboxes = () => {
    if (isAllChecked) {
      setCheckedIds(new Set());
      setSelectedId(null);
    } else {
      const all = new Set(sortedItems.map((i) => i.id));
      setCheckedIds(all);
      if (sortedItems.length === 1) setSelectedId(sortedItems[0].id);
    }
  };

  const toggleRowCheckbox = (id: number) => {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      if (next.size === 1) {
        setSelectedId(Array.from(next)[0]);
      } else if (next.size === 0) {
        setSelectedId(null);
      }
      return next;
    });
  };

  const selectSingleRow = (id: number) => {
    setSelectedId(id);
    setCheckedIds(new Set([id]));
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

        {/* Right VIP Search & Filter Controls (Exact 32px height alignment) */}
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
            width={280}
            height={32}
          />
        </div>
      </div>

      {/* 2. Table Panel (RoundedPanel radius=22px) */}
      <div className="flex-1 w-full rounded-[22px] bg-white dark:bg-[#111F3B] p-3 flex flex-col min-h-0 shadow-sm relative transition-colors">
        <div className="flex-1 w-full overflow-auto flex flex-col relative">
          <div className="min-w-full inline-block align-middle flex-1 flex flex-col">
            {/* Capsule Table Header (height=36px, rounded-full) */}
            <div className="h-[36px] rounded-full bg-[#EEF4FB] dark:bg-[#142544] flex items-center sticky top-0 z-20 select-none shrink-0">
              {/* Left Master Checkbox (60px) */}
              <div className="w-[60px] h-full flex items-center justify-center shrink-0 border-r border-[#E5ECF5] dark:border-[#24385E] sticky left-0 bg-[#EEF4FB] dark:bg-[#142544] rounded-l-full z-30">
                <NexoCheckbox
                  checked={isAllChecked}
                  onChange={toggleAllCheckboxes}
                  title="Selecionar todos"
                />
              </div>

              {/* Dynamic Visible Columns */}
              <div className="flex items-center flex-1 h-full">
                {visibleColumns.map((col) => {
                  const isSorted = orderBy === col.key;
                  const arrow = isSorted ? (orderDir === 'ASC' ? ' ↑' : ' ↓') : '';
                  return (
                    <button
                      key={col.key}
                      type="button"
                      onClick={() => handleSort(col.key)}
                      style={{
                        minWidth: `${col.width}px`,
                        flex: col.key === 'name' ? '1.4 1 0%' : '1 1 0%',
                      }}
                      className={`h-full px-3 flex items-center border-r border-[#E5ECF5] dark:border-[#24385E] text-[12.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer group ${
                        col.align === 'left' ? 'justify-start text-left' : 'justify-center text-center'
                      }`}
                    >
                      <span className="truncate">
                        {col.align === 'left' ? `${col.label}${arrow}` : `${arrow}${col.label}`}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Right Fixed Actions Header (90px: edit 30 + delete 30 + gear 30) */}
              <div
                ref={colMenuRef}
                className="w-[90px] h-full flex items-center justify-end pr-2 shrink-0 sticky right-0 bg-[#EEF4FB] dark:bg-[#142544] rounded-r-full border-l border-[#E5ECF5] dark:border-[#24385E] z-30 relative"
              >
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

                {/* Floating Column Visibility Menu */}
                {colMenuOpen && (
                  <div className="absolute right-0 top-[40px] w-[200px] rounded-[12px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-xl py-2.5 z-50 select-none">
                    <div className="px-3.5 pb-1.5 text-[10.5px] font-bold tracking-wider text-[#A0ABB9] uppercase">
                      Exibir Colunas
                    </div>
                    {REC_COLUMNS.filter((c) => c.hideable).map((col) => {
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
                )}
              </div>
            </div>

            {/* Table Body or Empty State */}
            {sortedItems.length === 0 && !loading ? (
              <div className="flex-1 flex flex-col items-center justify-center py-12 select-none">
                <img
                  src="/ui_assets/empty_state_reference_exact.png"
                  alt="Sem registros"
                  className="max-h-[160px] object-contain mb-3 pointer-events-none"
                />
                <p className="text-[15px] font-bold text-[#687796] dark:text-[#93A4C6] mb-1">
                  Ainda não há receitas cadastradas.
                </p>
                <p className="text-[12.5px] text-[#8C9BB5] dark:text-[#687796]">
                  Clique em + Nova Receita para adicionar a primeira ficha técnica.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-[#F0F4FA] dark:divide-[#17294A]">
                {sortedItems.map((item) => {
                  const isChecked = checkedIds.has(item.id);
                  const isSelected = selectedId === item.id || isChecked;
                  const rowBg = isSelected
                    ? 'bg-[#FFF0D8] dark:bg-[#5A3518]'
                    : 'bg-white dark:bg-[#0E1B35] hover:bg-[#F8FAFD] dark:hover:bg-[#132342]';
                  const stickyBg = isSelected
                    ? 'bg-[#FFF0D8] dark:bg-[#5A3518]'
                    : 'bg-white dark:bg-[#0E1B35] group-hover:bg-[#F8FAFD] dark:group-hover:bg-[#132342]';

                  return (
                    <div
                      key={item.id}
                      onClick={() => selectSingleRow(item.id)}
                      onDoubleClick={() => openEditRecipe(item)}
                      className={`h-[38px] flex items-center transition-colors group cursor-pointer ${rowBg} ${
                        !item.active
                          ? 'text-[#9AA9BF] dark:text-[#60769D]'
                          : 'text-[#18223A] dark:text-[#F4F7FF]'
                      }`}
                    >
                      {/* Left Checkbox Cell (60px) */}
                      <div
                        className={`w-[60px] h-full flex items-center justify-center shrink-0 sticky left-0 z-10 transition-colors ${stickyBg}`}
                      >
                        <NexoCheckbox
                          checked={isChecked}
                          onChange={() => toggleRowCheckbox(item.id)}
                        />
                      </div>

                      {/* Data Cells */}
                      <div className="flex items-center flex-1 h-full">
                        {visibleColumns.map((col) => {
                          let cellContent: React.ReactNode = '';
                          switch (col.key) {
                            case 'code':
                              cellContent = (
                                <span className="font-mono text-[12px] font-semibold">
                                  {item.code}
                                </span>
                              );
                              break;
                            case 'name':
                              cellContent = <span className="font-medium">{item.name}</span>;
                              break;
                            case 'yield':
                              cellContent = `${item.yield_qty} ${item.yield_unit}`;
                              break;
                            case 'total_cost':
                              cellContent = <span className="font-medium">{item.total_cost_fmt}</span>;
                              break;
                            case 'portion_cost':
                              cellContent = <span className="font-medium">{item.portion_cost_fmt}</span>;
                              break;
                            case 'date':
                              cellContent = item.created_at ? item.created_at.slice(0, 10) : '';
                              break;
                            case 'status':
                              cellContent = (
                                <span
                                  className={`px-2.5 py-0.5 rounded-full text-[11.5px] font-semibold ${
                                    item.active
                                      ? 'bg-[#EAFaf1] text-[#1E833F] dark:bg-[#12372E] dark:text-[#61E3B9]'
                                      : 'bg-[#F1F5F9] text-[#687796] dark:bg-[#172746] dark:text-[#93A4C6]'
                                  }`}
                                >
                                  {item.active ? 'Ativo' : 'Inativo'}
                                </span>
                              );
                              break;
                          }

                          return (
                            <div
                              key={col.key}
                              style={{
                                minWidth: `${col.width}px`,
                                flex: col.key === 'name' ? '1.4 1 0%' : '1 1 0%',
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
                        {/* Edit Button */}
                        <button
                          type="button"
                          disabled={!item.active}
                          onClick={() => {
                            selectSingleRow(item.id);
                            openEditRecipe(item);
                          }}
                          title={item.active ? 'Editar' : 'Editar (Desativado)'}
                          className="w-[28px] h-[28px] rounded-full flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-30 cursor-pointer disabled:cursor-default"
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
                          onClick={() => {
                            selectSingleRow(item.id);
                            triggerDeleteCheck([item.id]);
                          }}
                          title="Excluir"
                          className="w-[28px] h-[28px] rounded-full flex items-center justify-center hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer"
                        >
                          <img
                            src="/ui_assets/action_delete_reference_exact.png"
                            alt="Excluir"
                            className="w-4 h-4 object-contain"
                          />
                        </button>

                        {/* 3-dots Options Button */}
                        <button
                          type="button"
                          onClick={(e) => {
                            selectSingleRow(item.id);
                            const rect = e.currentTarget.getBoundingClientRect();
                            setRowMenu({
                              item,
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
                })}
              </div>
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

function getCompatibleUnits(purchaseUnit: string, customUnits: string[] = []): string[] {
  const p = (purchaseUnit || '').trim().toLowerCase();
  let baseFamily: string[] = [];
  if (['g', 'kg', 'mg', 't'].includes(p)) {
    // Para culinária, prioriza gramas (g), depois kg e mg
    baseFamily = ['g', 'kg', 'mg'];
  } else if (['ml', 'l', 'kl'].includes(p)) {
    // Para culinária, prioriza ml, depois L
    baseFamily = ['ml', 'L'];
  } else if (p === 'un') {
    baseFamily = ['un'];
  } else {
    baseFamily = [purchaseUnit || 'un'];
  }
  return Array.from(new Set([...baseFamily, ...customUnits]));
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
  const [cookingAppliance, setCookingAppliance] = useState<string>(editItem ? ((editItem as any).cooking_appliance || 'none') : 'none');
  const [cookingTime, setCookingTime] = useState<string>(editItem ? String((editItem as any).cooking_time_minutes || '0') : '0');
  const [notes, setNotes] = useState(editItem ? editItem.notes : '');

  const [materials, setMaterials] = useState<MaterialOption[]>([]);
  const [ingredients, setIngredients] = useState<FormIngredientRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Live preview totals
  const [materialsCostFmt, setMaterialsCostFmt] = useState('R$ 0,00');
  const [operationalCostFmt, setOperationalCostFmt] = useState('R$ 0,00');
  const [operationalBreakdown, setOperationalBreakdown] = useState<any[]>([]);
  const [totalCostFmt, setTotalCostFmt] = useState(editItem ? editItem.total_cost_fmt : 'R$ 0,00');
  const [portionCostFmt, setPortionCostFmt] = useState(editItem ? editItem.portion_cost_fmt : 'R$ 0,00');

  // Load active materials options
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/materials/options');
        if (res.ok) {
          const data = await res.json();
          const list: MaterialOption[] = data.items || [];
          setMaterials(list);
        }
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  // Pre-load ingredients and cooking if editing
  useEffect(() => {
    if (editItem) {
      (async () => {
        try {
          const detRes = await fetch(`/api/recipes/${editItem.id}`);
          if (detRes.ok) {
            const data = await detRes.json();
            if (data.cooking_appliance) setCookingAppliance(data.cooking_appliance);
            if (data.cooking_time_minutes !== undefined) setCookingTime(String(data.cooking_time_minutes));
            if (data.materials_cost_fmt) setMaterialsCostFmt(data.materials_cost_fmt);
            if (data.operational_cost_fmt) setOperationalCostFmt(data.operational_cost_fmt);
            if (data.operational_breakdown?.items) setOperationalBreakdown(data.operational_breakdown.items);
            if (data.total_cost_fmt) setTotalCostFmt(data.total_cost_fmt);
            if (data.portion_cost_fmt) setPortionCostFmt(data.portion_cost_fmt);
          }
        } catch (e) {
          console.error(e);
        }
      })();
    }
    if (editItem && editItem.items) {
      (async () => {
        const rows: FormIngredientRow[] = [];
        for (const it of editItem.items) {
          let customNames: string[] = [];
          try {
            const cRes = await fetch(`/api/materials/${it.material_id}/conversions`);
            if (cRes.ok) {
              const cData = await cRes.json();
              const cList: ConversionItem[] = cData.items || [];
              customNames = cList.map((c) => c.name);
            }
          } catch (e) {
            // fallback
          }
          const availUnits = getCompatibleUnits(it.material_unit, [it.unit, ...customNames]);
          rows.push({
            material_id: it.material_id,
            material_name: it.material_name,
            material_brand: it.material_brand || '',
            qty: String(it.qty),
            unit: it.unit,
            cost_fmt: it.cost_fmt,
            available_units: availUnits,
          });
        }
        setIngredients(rows);
      })();
    }
  }, [editItem]);

  // Recalculate live preview
  const recalculatePreview = useCallback(async (
    rows: FormIngredientRow[],
    yQty: string,
    yUnit: string,
    applianceVal = cookingAppliance,
    timeVal = cookingTime
  ) => {
    const validRows = rows.filter(
      (r) => r.material_id > 0 && parseFloat(r.qty.replace(',', '.')) > 0 && r.unit
    );
    if (validRows.length === 0 && (applianceVal === 'none' || parseFloat(timeVal) <= 0)) {
      setMaterialsCostFmt('R$ 0,00');
      setOperationalCostFmt('R$ 0,00');
      setOperationalBreakdown([]);
      setTotalCostFmt('R$ 0,00');
      setPortionCostFmt('R$ 0,00');
      setIngredients((prev) =>
        prev.map((r) => ({
          ...r,
          cost_fmt: r.material_id > 0 && parseFloat(r.qty.replace(',', '.')) > 0 ? r.cost_fmt : '-',
        }))
      );
      return;
    }
    try {
      const payload = {
        yield_qty: yQty || '1',
        yield_unit: yUnit || 'un',
        cooking_appliance: applianceVal,
        cooking_time_minutes: parseFloat(String(timeVal).replace(',', '.')) || 0,
        items: validRows.map((r) => ({
          material_id: r.material_id,
          qty: parseFloat(r.qty.replace(',', '.')) || 0,
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
        setMaterialsCostFmt(data.materials_cost_fmt || 'R$ 0,00');
        setOperationalCostFmt(data.operational_cost_fmt || 'R$ 0,00');
        setOperationalBreakdown(data.operational_breakdown?.items || []);
        setTotalCostFmt(data.total_cost_fmt);
        setPortionCostFmt(data.portion_cost_fmt);
        const costMap: Record<number, string> = {};
        if (data.items) {
          data.items.forEach((it: any) => {
            costMap[it.material_id] = it.cost_fmt;
          });
        }
        setIngredients((prev) =>
          prev.map((r) => ({
            ...r,
            cost_fmt: costMap[r.material_id] || (r.material_id > 0 && parseFloat(r.qty.replace(',', '.')) > 0 ? r.cost_fmt : '-'),
          }))
        );
      }
    } catch (e) {
      console.error(e);
    }
  }, [cookingAppliance, cookingTime]);

  // Add new ingredient row (always clean, pristine empty line)
  const addIngredientRow = () => {
    if (materials.length === 0) {
      onNotify('Nenhum insumo cadastrado para adicionar à receita.', 'warning');
      return;
    }
    const newRow: FormIngredientRow = {
      material_id: 0,
      material_name: '',
      material_brand: '',
      qty: '',
      unit: '',
      cost_fmt: '-',
      available_units: [],
    };
    setIngredients((prev) => [...prev, newRow]);
  };

  const removeIngredientRow = (idx: number) => {
    const nextRows = ingredients.filter((_, i) => i !== idx);
    setIngredients(nextRows);
    recalculatePreview(nextRows, yieldQty, yieldUnit);
  };

  const updateIngredientRow = async (idx: number, patch: Partial<FormIngredientRow>) => {
    const nextRows = [...ingredients];
    const current = nextRows[idx];
    const updated = { ...current, ...patch };

    // If material changed (or was selected for the first time)
    if (patch.material_id && patch.material_id !== current.material_id) {
      const mat = materials.find((m) => m.id === patch.material_id);
      if (mat) {
        updated.material_name = mat.name;
        let customNames: string[] = [];
        try {
          const cRes = await fetch(`/api/materials/${mat.id}/conversions`);
          if (cRes.ok) {
            const cData = await cRes.json();
            const cList: ConversionItem[] = cData.items || [];
            customNames = cList.map((c) => c.name);
          }
        } catch (e) {
          // fallback
        }
        const availUnits = getCompatibleUnits(mat.purchase_unit, customNames);
        updated.available_units = availUnits;
        if (!updated.unit || !availUnits.includes(updated.unit)) {
          updated.unit = availUnits.includes('g')
            ? 'g'
            : availUnits.includes('ml')
            ? 'ml'
            : availUnits[0] || 'un';
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

    const validItems = ingredients.filter((it) => it.material_id > 0);
    if (validItems.length === 0) {
      return setError('Adicione e selecione ao menos um ingrediente à receita.');
    }
    for (const it of validItems) {
      const q = parseFloat(it.qty.replace(',', '.'));
      if (isNaN(q) || q <= 0) {
        return setError(`Informe uma quantidade válida para "${it.material_name || 'o ingrediente'}".`);
      }
      if (!it.unit) {
        return setError(`Selecione a unidade para "${it.material_name || 'o ingrediente'}".`);
      }
    }

    const payload = {
      name: n,
      yield_qty: yq,
      yield_unit: yu,
      cooking_appliance: cookingAppliance,
      cooking_time_minutes: parseFloat(cookingTime.replace(',', '.')) || 0,
      notes: notes.trim(),
      items: validItems.map((it) => ({
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
      <div className="w-[740px] max-h-[92vh] rounded-[22px] bg-[#F4F7FC] dark:bg-[#0B1730] border border-[#DDE5F2] dark:border-[#24385E] shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 pt-4 pb-3 flex items-center justify-between border-b border-[#E2EAF5] dark:border-[#1E3156] bg-white dark:bg-[#0F1B35] shrink-0">
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

          {/* Card 1: Identificação & Rendimento */}
          <div className="p-4 rounded-[18px] bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] shadow-sm space-y-3">
            <div className="grid grid-cols-12 gap-2.5">
              <div className="col-span-8">
                <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                  Nome da Receita *
                </label>
                <CapsuleInput
                  value={name}
                  onChange={setName}
                  autoCapitalizeFirst
                  placeholder="Ex: Massa de Bolo de Cenoura, Recheio de Ninho..."
                />
              </div>

              <div className="col-span-4">
                <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                  Rendimento da Receita *
                </label>
                <CapsuleQuantityUnit
                  qtyValue={yieldQty}
                  onQtyChange={(v) => {
                    setYieldQty(v);
                    recalculatePreview(ingredients, v, yieldUnit);
                  }}
                  unitValue={yieldUnit}
                  onUnitChange={(u) => {
                    setYieldUnit(u);
                    recalculatePreview(ingredients, yieldQty, u);
                  }}
                  unitOptions={['un', 'porções', 'fatias', 'g', 'kg', 'ml', 'L', 'potes', 'caixas']}
                  qtyPlaceholder="Ex: 12"
                  width="100%"
                  height={32}
                />
              </div>
            </div>

            <div>
              <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                Observações / Modo de Preparo (Opcional)
              </label>
              <CapsuleInput
                value={notes}
                onChange={setNotes}
                autoCapitalizeFirst
                placeholder="Ex: Tempo de forno, temperatura, cuidados de conservação..."
              />
            </div>
          </div>

          {/* Card 2: Ingredientes da Ficha Técnica */}
          <div className="p-4 rounded-[18px] bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] shadow-sm flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  Ingredientes da Ficha Técnica
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#F0F4FA] dark:bg-[#1A2C4E] text-[#60769D] dark:text-[#AFC0E2]">
                  {ingredients.length} {ingredients.length === 1 ? 'item' : 'itens'}
                </span>
              </div>

              <RoundedActionButton
                label="Adicionar Ingrediente"
                onClick={addIngredientRow}
                variant="primary"
                icon={<PlusIcon size={14} strokeWidth={2.4} />}
                height={32}
              />
            </div>

            {ingredients.length === 0 ? (
              <div className="py-8 flex flex-col items-center justify-center text-center select-none">
                <img
                  src="/ui_assets/empty_state_reference_exact.png"
                  alt="Nenhum ingrediente"
                  className="max-h-[80px] object-contain mb-2 pointer-events-none opacity-80"
                />
                <p className="text-[13px] font-semibold text-[#687796] dark:text-[#93A4C6] mb-0.5">
                  Nenhum ingrediente adicionado à receita.
                </p>
                <p className="text-[12px] text-[#8C9BB5] dark:text-[#64748B]">
                  Clique em "+ Adicionar Ingrediente" acima para compor a ficha técnica.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {/* Header cápsula da tabela de ingredientes */}
                <div className="h-[30px] rounded-full bg-[#EEF4FB] dark:bg-[#142544] px-3 flex items-center text-[11.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] select-none">
                  <span className="flex-1 pl-1">Insumo</span>
                  <span className="w-[160px] text-center">Quantidade | Unidade</span>
                  <span className="w-[95px] text-center">Custo Proporcional</span>
                  <span className="w-[36px] text-center">Ação</span>
                </div>

                {/* Rows de ingredientes */}
                {ingredients.map((ing, idx) => {
                  const selectedMat = materials.find((m) => m.id === ing.material_id);
                  const selectedMatLabel = selectedMat ? selectedMat.label : '';

                  return (
                    <div
                      key={idx}
                      className="p-2 rounded-[14px] bg-[#F9FBFC] dark:bg-[#0E1A30] border border-[#E2EAF5] dark:border-[#1E3156] flex items-center gap-2"
                    >
                      {/* Insumo Dropdown com busca / autocomplete do Nexo */}
                      <div className="flex-1 min-w-0">
                        <RoundedDropdown
                          value={selectedMatLabel}
                          onChange={(newLabel) => {
                            const found = materials.find((m) => m.label === newLabel);
                            if (found) {
                              updateIngredientRow(idx, { material_id: found.id });
                            }
                          }}
                          options={materials.map((m) => m.label)}
                          width="100%"
                          height={34}
                          align="left"
                          placeholder="Selecione o insumo..."
                        />
                      </div>

                      {/* Quantidade e Unidade unificadas em cápsula Nexo */}
                      <div className="w-[160px] shrink-0 flex items-center justify-center">
                        <CapsuleQuantityUnit
                          qtyValue={ing.qty}
                          onQtyChange={(v) => updateIngredientRow(idx, { qty: v })}
                          unitValue={ing.unit}
                          onUnitChange={(newUnit) => updateIngredientRow(idx, { unit: newUnit })}
                          unitOptions={
                            ing.available_units.length > 0
                              ? ing.available_units
                              : [ing.unit || 'g', 'g', 'kg', 'ml', 'L', 'un']
                          }
                          qtyPlaceholder="Ex: 200"
                          width={160}
                          height={34}
                        />
                      </div>

                      {/* Custo Calculado */}
                      <div className="w-[95px] h-[34px] rounded-full bg-white dark:bg-[#142340] border border-[#DDE5F2] dark:border-[#24385E] flex items-center justify-center font-bold text-[13px] text-[#18223A] dark:text-[#F4F7FF] shrink-0 shadow-sm">
                        {ing.cost_fmt}
                      </div>

                      {/* Remover Linha com TrashIcon do Nexo */}
                      <div className="w-[36px] flex items-center justify-center shrink-0">
                        <button
                          type="button"
                          onClick={() => removeIngredientRow(idx)}
                          title="Remover ingrediente"
                          className="w-8 h-8 rounded-full flex items-center justify-center text-[#DC2626] dark:text-[#F87171] hover:bg-[#FEE2E2] dark:hover:bg-[#3D1822] transition-colors cursor-pointer"
                        >
                          <TrashIcon size={16} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Card Intermediário: Preparo, Forno & Cocção da Receita */}
          <div className="p-4 rounded-[18px] bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-[#FFF0E6] dark:bg-[#2D1B10] flex items-center justify-center text-[#F28C28]">
                  <FlameIcon size={12} />
                </div>
                <span className="text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  Preparo, Forno & Cocção da Receita (Gás e Eletricidade)
                </span>
              </div>
              <span className="text-[11px] text-[#60769D] dark:text-[#93A4C6]">
                Calculado com base na rotina da sua cozinha
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
              {/* Equipamento */}
              <div className="md:col-span-8">
                <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                  Equipamento Utilizado
                </label>
                <select
                  value={cookingAppliance}
                  onChange={(e) => {
                    const newApp = e.target.value;
                    setCookingAppliance(newApp);
                    recalculatePreview(ingredients, yieldQty, yieldUnit, newApp, cookingTime);
                  }}
                  className="w-full h-[34px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[12.5px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3 focus:outline-none focus:ring-2 focus:ring-[#F28C28] cursor-pointer"
                >
                  <option value="none">Sem cocção ativa (Mistura fria / Sem forno ou fogão)</option>
                  <option value="gas_oven">Forno a Gás (Fogo médio - bolos, tortas, assados)</option>
                  <option value="gas_stove_burner">Boca de Fogão / Panela (Chama média - brigadeiros, caldas)</option>
                  <option value="electric_oven">Forno Elétrico Convector</option>
                  <option value="mixer_planetary">Batedeira Planetária (Massa pesada / Claras)</option>
                  <option value="induction_cooktop">Cooktop de Indução</option>
                  <option value="microwave">Micro-ondas</option>
                </select>
              </div>

              {/* Tempo em minutos */}
              <div className="md:col-span-4">
                <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                  Tempo de Forno / Fogo (minutos)
                </label>
                <div className="relative flex items-center">
                  <input
                    type="text"
                    disabled={cookingAppliance === 'none'}
                    value={cookingAppliance === 'none' ? '0' : cookingTime}
                    onChange={(e) => {
                      const newT = e.target.value.replace(/[^0-9.,]/g, '');
                      setCookingTime(newT);
                      recalculatePreview(ingredients, yieldQty, yieldUnit, cookingAppliance, newT);
                    }}
                    placeholder="40"
                    className="w-full h-[34px] rounded-full border border-[#D5E1F2] dark:border-[#283E6B] bg-white dark:bg-[#101D38] text-[12.5px] font-bold text-[#18223A] dark:text-[#F4F7FF] px-3 pr-11 focus:outline-none focus:ring-2 focus:ring-[#F28C28] disabled:opacity-50"
                  />
                  <span className="absolute right-3 text-[11px] font-bold text-[#8C9BB5]">min</span>
                </div>
              </div>
            </div>

            {/* Informação didática da receita */}
            {cookingAppliance !== 'none' && parseFloat(cookingTime) > 0 ? (
              <div className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6] flex items-center gap-2 pl-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#F28C28] shrink-0" />
                <span>
                  O gasto de gás e energia de <strong>{cookingTime} min</strong> será incorporado a este lote da receita e distribuído no rendimento de <strong>{yieldQty || 1} {yieldUnit}</strong>.
                </span>
              </div>
            ) : (
              <div className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6] flex items-center gap-2 pl-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#8C9BB5] shrink-0" />
                <span>
                  Receita sem cocção ativa. Apenas o custo dos ingredientes será contabilizado no lote.
                </span>
              </div>
            )}
          </div>

          {/* Card 3: Summary KPI Banner (Live preview em tempo real) */}
          <div className="rounded-[18px] bg-[#FFF8EE] dark:bg-[#1B1914] border border-[#F28C28]/35 p-3.5 shadow-sm space-y-3">
            <div className="flex items-center justify-around text-center">
              <div>
                <span className="block text-[11px] uppercase tracking-wider font-bold text-[#8C9BB5] dark:text-[#93A4C6]">
                  Ingredientes
                </span>
                <span className="text-[16px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  {materialsCostFmt}
                </span>
              </div>
              <div className="w-[1px] h-8 bg-[#F28C28]/25" />
              <div>
                <span className="block text-[11px] uppercase tracking-wider font-bold text-[#8C9BB5] dark:text-[#93A4C6]">
                  Cocção (Gás/Luz)
                </span>
                <span className="text-[16px] font-bold text-[#F28C28]">
                  {operationalCostFmt}
                </span>
              </div>
              <div className="w-[1px] h-8 bg-[#F28C28]/25" />
              <div>
                <span className="block text-[11px] uppercase tracking-wider font-bold text-[#8C9BB5] dark:text-[#93A4C6]">
                  Custo Total do Lote
                </span>
                <span className="text-[17px] font-bold text-[#F28C28]">
                  {totalCostFmt}
                </span>
              </div>
              <div className="w-[1px] h-8 bg-[#F28C28]/25" />
              <div>
                <span className="block text-[11px] uppercase tracking-wider font-bold text-[#8C9BB5] dark:text-[#93A4C6]">
                  Custo por {yieldUnit}
                </span>
                <span className="text-[17px] font-bold text-[#16A34A] dark:text-[#4ADE80]">
                  {portionCostFmt}
                </span>
              </div>
            </div>

            {/* Badges de Cocção */}
            {operationalBreakdown && operationalBreakdown.length > 0 && parseFloat(cookingTime) > 0 && cookingAppliance !== 'none' && (
              <div className="pt-2 border-t border-[#F28C28]/20 flex flex-wrap items-center justify-between gap-2 text-[11.5px]">
                <span className="font-bold text-[#18223A] dark:text-[#F4F7FF] flex items-center gap-1">
                  <span>Detalhamento da Cocção da Receita:</span>
                </span>
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
                        key={idx}
                        className="px-2.5 py-0.5 rounded-full bg-white dark:bg-[#111F3B] border border-[#F28C28]/30 font-bold text-[#18223A] dark:text-[#F4F7FF] flex items-center gap-1.5"
                      >
                        {iconSvg && <span className="flex items-center shrink-0">{iconSvg}</span>}
                        <span>{item.name}:</span>
                        <span className="text-[#F28C28]">{item.cost_fmt}</span>
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Modal Actions Footer */}
        <div className="px-6 py-3 border-t border-[#E2EAF5] dark:border-[#1E3156] flex items-center justify-between bg-white dark:bg-[#0F1B35] shrink-0">
          <RoundedActionButton
            label="Cancelar"
            onClick={onClose}
            variant="ghost"
            height={36}
          />
          <RoundedActionButton
            label={editItem ? 'Salvar Alterações' : 'Salvar Receita'}
            onClick={handleSave}
            variant="primary"
            height={36}
            width={160}
          />
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

