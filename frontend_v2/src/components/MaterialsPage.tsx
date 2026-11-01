import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  DeleteCheckResponse,
  MaterialHistoryRow,
  MaterialItem,
} from '../types';
import {
  CapsuleInput,
  ClockIcon,
  DuplicateIcon,
  GearPolygonIcon,
  NexoCheckbox,
  PlusIcon,
  RoundedActionButton,
  RoundedDropdown,
  RoundedEntry,
  TrashIcon,
} from './DesignSystem';

interface MaterialsPageProps {
  units: string[];
  initialHiddenCols: string[];
  onNotify: (msg: string, type?: 'success' | 'warning' | 'error') => void;
  dark: boolean;
}

interface ColumnSpec {
  key: string;
  label: string;
  width: number;
  align: 'left' | 'center';
  hideable: boolean;
}

const COLUMNS: ColumnSpec[] = [
  { key: 'code', label: 'Código', width: 105, align: 'left', hideable: true },
  { key: 'barcode', label: 'Cód. Barras', width: 135, align: 'left', hideable: false },
  { key: 'name', label: 'Item', width: 230, align: 'left', hideable: true },
  { key: 'brand', label: 'Marca', width: 155, align: 'left', hideable: true },
  { key: 'qty', label: 'Quantidade', width: 115, align: 'center', hideable: true },
  { key: 'unit', label: 'Un.', width: 70, align: 'center', hideable: true },
  { key: 'value', label: 'Valor', width: 115, align: 'center', hideable: true },
  { key: 'category', label: 'Categoria', width: 135, align: 'center', hideable: true },
  { key: 'date', label: 'Data de criação', width: 135, align: 'center', hideable: true },
  { key: 'mod_date', label: 'Última modificação', width: 145, align: 'center', hideable: true },
  { key: 'status', label: 'Status', width: 95, align: 'center', hideable: true },
];

export const MaterialsPage: React.FC<MaterialsPageProps> = ({
  units,
  initialHiddenCols,
  onNotify,
  dark,
}) => {
  const [items, setItems] = useState<MaterialItem[]>([]);
  const [loading, setLoading] = useState(false);

  // Filters & Sorting
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'Ativos' | 'Inativos' | 'Todos'>('Ativos');
  const [orderBy, setOrderBy] = useState<string>('name');
  const [orderDir, setOrderDir] = useState<'ASC' | 'DESC'>('ASC');
  const [hiddenCols, setHiddenCols] = useState<string[]>(initialHiddenCols);

  // Selection & Multiselection
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [checkedIds, setCheckedIds] = useState<Set<number>>(new Set());

  // Popups (Column Visibility Gear & Row 3-dots Menu)
  const [colMenuOpen, setColMenuOpen] = useState(false);
  const colMenuRef = useRef<HTMLDivElement>(null);

  const [rowMenu, setRowMenu] = useState<{
    item: MaterialItem;
    x: number;
    y: number;
  } | null>(null);
  const rowMenuRef = useRef<HTMLDivElement>(null);

  // Modals State
  const [formModal, setFormModal] = useState<{
    open: boolean;
    editItem: MaterialItem | null;
  }>({ open: false, editItem: null });

  const [editDecisionModal, setEditDecisionModal] = useState<{
    open: boolean;
    type: 'price_change' | 'brand_change';
    step: 'choice' | 'reason';
    beforeItem: MaterialItem;
    pendingPayload: any;
    priceDiff?: {
      oldPrice: string;
      newPrice: string;
      oldQty: string;
      newQty: string;
      oldUnit: string;
      newUnit: string;
    };
    brandDiff?: {
      oldBrand: string;
      newBrand: string;
      name: string;
    };
    reasonText: string;
  } | null>(null);

  const [deleteModal, setDeleteModal] = useState<{
    open: boolean;
    check: DeleteCheckResponse;
    ids: number[];
  } | null>(null);

  const [historyModal, setHistoryModal] = useState<{
    open: boolean;
    materialId: number;
    materialName: string;
    rows: MaterialHistoryRow[];
  } | null>(null);

  // Form fields for Novo / Editar Insumo
  const todayISO = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const [fName, setFName] = useState('');
  const [fBrand, setFBrand] = useState('');
  const [fQty, setFQty] = useState('');
  const [fUnit, setFUnit] = useState('');
  const [fValue, setFValue] = useState('');
  const [fCategory, setFCategory] = useState('Comestível');
  const [fBarcode, setFBarcode] = useState('');
  const [fDate, setFDate] = useState(todayISO);
  const [formError, setFormError] = useState<string | null>(null);

  // Fetch Materials
  const fetchMaterials = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        search,
        status: statusFilter,
        order_by: orderBy,
        order_dir: orderDir,
      });
      const res = await fetch(`/api/materials?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setItems(data.items || []);
        setCheckedIds(new Set());
      }
    } catch (e) {
      console.error('Erro ao buscar insumos:', e);
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, orderBy, orderDir]);

  useEffect(() => {
    fetchMaterials();
  }, [fetchMaterials]);

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
    () => COLUMNS.filter((c) => !hiddenCols.includes(c.key)),
    [hiddenCols]
  );

  // Toggle column visibility & persist to DB
  const toggleColumnVisibility = async (key: string) => {
    const next = hiddenCols.includes(key)
      ? hiddenCols.filter((k) => k !== key)
      : [...hiddenCols, key];
    setHiddenCols(next);
    try {
      await fetch('/api/settings/mat_hidden_cols', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: next }),
      });
    } catch (e) {
      console.error(e);
    }
  };

  // Sorting
  const handleSort = (key: string) => {
    if (orderBy === key) {
      setOrderDir((d) => (d === 'ASC' ? 'DESC' : 'ASC'));
    } else {
      setOrderBy(key);
      setOrderDir('ASC');
    }
  };

  // Checkbox selection helpers
  const isAllChecked = items.length > 0 && checkedIds.size === items.length;

  const toggleAllCheckboxes = () => {
    if (isAllChecked) {
      setCheckedIds(new Set());
      setSelectedId(null);
    } else {
      const all = new Set(items.map((i) => i.id));
      setCheckedIds(all);
      if (items.length === 1) setSelectedId(items[0].id);
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

  // ---------- Open Novo / Editar Insumo ----------

  const openNewMaterial = () => {
    if (checkedIds.size >= 2) setCheckedIds(new Set());
    setFName('');
    setFBrand('');
    setFQty('');
    setFUnit('');
    setFValue('');
    setFCategory('Comestível');
    setFBarcode('');
    setFDate(new Date().toISOString().slice(0, 10));
    setFormError(null);
    setFormModal({ open: true, editItem: null });
  };

  const openEditMaterial = (item?: MaterialItem) => {
    const target =
      item ||
      items.find((i) => i.id === selectedId) ||
      (checkedIds.size === 1 ? items.find((i) => checkedIds.has(i.id)) : undefined);
    if (!target) {
      onNotify('Selecione um item na tabela para editar.');
      return;
    }
    if (!target.active) {
      onNotify('Itens inativos não podem ser editados. Ative o item primeiro.');
      return;
    }
    setFName(target.name);
    setFBrand(target.brand || '');
    setFQty(target.qty_fmt);
    setFUnit(target.unit);
    setFValue(target.value_fmt);
    setFCategory(target.category || 'Comestível');
    setFBarcode(target.barcode || '');
    setFDate(new Date().toISOString().slice(0, 10));
    setFormError(null);
    setFormModal({ open: true, editItem: target });
  };

  const handleDuplicate = (item: MaterialItem) => {
    if (checkedIds.size >= 2) setCheckedIds(new Set());
    setFName(item.name);
    setFBrand(item.brand || '');
    setFQty(item.qty_fmt);
    setFUnit(item.unit);
    setFValue(item.value_fmt);
    setFCategory(item.category || 'Comestível');
    setFBarcode('');
    setFDate(new Date().toISOString().slice(0, 10));
    setFormError(null);
    setFormModal({ open: true, editItem: null });
  };

  const parseLocalFloat = (str: string): number => {
    let s = String(str || '').replace('R$', '').trim();
    if (!s) return NaN;
    if (s.includes(',') && s.includes('.')) {
      if (s.lastIndexOf(',') > s.lastIndexOf('.')) {
        s = s.replace(/\./g, '').replace(',', '.');
      } else {
        s = s.replace(/,/g, '');
      }
    } else if (s.includes(',')) {
      s = s.replace(',', '.');
    }
    return parseFloat(s);
  };

  const handleSaveForm = async () => {
    setFormError(null);
    const name = fName.trim();
    const brand = fBrand.trim();
    const unit = fUnit.trim();
    const category = fCategory.trim();
    const barcode = fBarcode.trim();
    const purchaseDate = fDate.trim();

    if (!name) return setFormError('O campo "Nome" é obrigatório.');
    if (!fQty.trim()) return setFormError('O campo "Quantidade" é obrigatório.');
    if (!unit) return setFormError('O campo "Unidade" é obrigatório.');
    if (!fValue.trim()) return setFormError('O campo "Valor da compra" é obrigatório.');
    if (!category) return setFormError('O campo "Categoria" é obrigatório.');
    if (!purchaseDate) return setFormError('O campo "Data" é obrigatório.');

    const qtyNum = parseLocalFloat(fQty);
    const valNum = parseLocalFloat(fValue);
    if (isNaN(qtyNum) || qtyNum <= 0) {
      return setFormError('A Quantidade deve ser um número maior que zero.');
    }
    if (isNaN(valNum) || valNum < 0) {
      return setFormError('O Valor da compra deve ser um número válido.');
    }
    if (valNum === 0 && category !== 'Doação') {
      return setFormError('Valor zero só é permitido para itens da categoria Doação.');
    }

    const payload = {
      name,
      brand,
      qty: fQty,
      unit,
      value: fValue,
      category,
      barcode,
      purchase_date: purchaseDate,
    };

    // If editing an existing item -> Smart Decision Workflow
    if (formModal.editItem) {
      const before = formModal.editItem;

      const brandChanged =
        (before.brand || '').trim().toLowerCase() !== brand.toLowerCase();

      const priceChanged =
        Math.abs(before.value - valNum) > 0.001 ||
        Math.abs(before.qty - qtyNum) > 0.0001 ||
        before.unit.trim().toLowerCase() !== unit.toLowerCase();

      // 1. If Brand changed: prompt whether to create as New Insumo or correct brand name
      if (brandChanged) {
        setEditDecisionModal({
          open: true,
          type: 'brand_change',
          step: 'choice',
          beforeItem: before,
          pendingPayload: payload,
          brandDiff: {
            oldBrand: before.brand || '(Sem marca)',
            newBrand: brand || '(Sem marca)',
            name,
          },
          priceDiff: priceChanged
            ? {
                oldPrice: before.value_fmt,
                newPrice: fValue,
                oldQty: before.qty_fmt,
                newQty: fQty,
                oldUnit: before.unit,
                newUnit: unit,
              }
            : undefined,
          reasonText: 'Reajuste de fornecedor / Nova compra',
        });
        return;
      }

      // 2. If Brand did NOT change, but Price/Qty/Unit changed: prompt Nova Compra vs Erro de Digitação
      if (priceChanged) {
        setEditDecisionModal({
          open: true,
          type: 'price_change',
          step: 'choice',
          beforeItem: before,
          pendingPayload: payload,
          priceDiff: {
            oldPrice: before.value_fmt,
            newPrice: fValue,
            oldQty: before.qty_fmt,
            newQty: fQty,
            oldUnit: before.unit,
            newUnit: unit,
          },
          reasonText: 'Reajuste de fornecedor / Nova compra',
        });
        return;
      }

      // 3. Neither brand nor price changed (e.g. only name, category, barcode, etc.):
      // Save directly with mode "correction" - NO annoying modal popup!
      try {
        const res = await fetch(`/api/materials/${before.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...payload,
            edit_mode: 'correction',
            edit_reason: 'Atualização cadastral',
          }),
        });
        const data = await res.json();
        if (!res.ok) {
          setFormError(data.detail || 'Não foi possível atualizar o item.');
          return;
        }
        setFormModal({ open: false, editItem: null });
        await fetchMaterials();
        onNotify('Insumo atualizado com sucesso.', 'success');
      } catch (e: any) {
        setFormError(e.message || 'Erro ao atualizar insumo.');
      }
      return;
    }

    // Creating a new item -> save directly
    try {
      const res = await fetch('/api/materials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setFormError(data.detail || 'Não foi possível salvar o item.');
        return;
      }
      setFormModal({ open: false, editItem: null });
      await fetchMaterials();
      onNotify('Insumo salvo com sucesso.', 'success');
    } catch (e: any) {
      setFormError(e.message || 'Erro de conexão com o servidor.');
    }
  };

  const handleCreateAsNewMaterial = async () => {
    if (!editDecisionModal) return;
    try {
      const res = await fetch('/api/materials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editDecisionModal.pendingPayload),
      });
      const data = await res.json();
      if (!res.ok) {
        setFormError(data.detail || 'Não foi possível salvar o novo insumo.');
        setEditDecisionModal(null);
        return;
      }
      setEditDecisionModal(null);
      setFormModal({ open: false, editItem: null });
      await fetchMaterials();
      onNotify('Novo insumo cadastrado com sucesso.', 'success');
    } catch (e: any) {
      setFormError(e.message || 'Erro de conexão com o servidor.');
      setEditDecisionModal(null);
    }
  };

  const handleCorrectBrandOnly = async () => {
    if (!editDecisionModal) return;
    // If price ALSO changed, transition to price_change confirmation
    if (editDecisionModal.priceDiff) {
      setEditDecisionModal((prev) => (prev ? { ...prev, type: 'price_change', step: 'choice' } : null));
      return;
    }
    await executeEditSave('correction', 'Correção de marca');
  };

  const executeEditSave = async (mode: 'correction' | 'update', reason: string) => {
    if (!editDecisionModal) return;
    if (mode === 'update' && !reason.trim()) {
      return;
    }
    try {
      const res = await fetch(`/api/materials/${editDecisionModal.beforeItem.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...editDecisionModal.pendingPayload,
          edit_mode: mode,
          edit_reason: reason.trim() || (mode === 'correction' ? 'Correção de cadastro' : 'Nova compra'),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setFormError(data.detail || 'Não foi possível atualizar o item.');
        setEditDecisionModal(null);
        return;
      }
      setEditDecisionModal(null);
      setFormModal({ open: false, editItem: null });
      await fetchMaterials();
      onNotify(
        mode === 'update' ? 'Nova compra registrada no histórico com sucesso.' : 'Insumo atualizado com sucesso.',
        'success'
      );
    } catch (e: any) {
      setFormError(e.message || 'Erro ao salvar edição.');
      setEditDecisionModal(null);
    }
  };

  // ---------- Smart Delete / Archive Modal ----------

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
      onNotify('Selecione ao menos um item para excluir.');
      return;
    }
    try {
      const res = await fetch('/api/materials/delete-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids }),
      });
      if (res.ok) {
        const check: DeleteCheckResponse = await res.json();
        if (check.total > 0) {
          setDeleteModal({ open: true, check, ids });
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const confirmDeleteExecute = async () => {
    if (!deleteModal) return;
    try {
      const res = await fetch('/api/materials/delete-execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: deleteModal.ids }),
      });
      const data = await res.json();
      setDeleteModal(null);
      if (res.ok) {
        await fetchMaterials();
        onNotify(data.message || 'Operação concluída com sucesso.');
      }
    } catch (e) {
      console.error(e);
    }
  };

  // ---------- Toggle Active / Inactive ----------

  const handleToggleActive = async (item: MaterialItem, newActive: boolean) => {
    try {
      const res = await fetch(`/api/materials/${item.id}/active`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: newActive }),
      });
      const data = await res.json();
      if (res.ok) {
        await fetchMaterials();
        onNotify(data.message);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // ---------- History Modal ----------

  const openHistoryModal = async (item?: MaterialItem) => {
    const target =
      item ||
      items.find((i) => i.id === selectedId) ||
      (checkedIds.size === 1 ? items.find((i) => checkedIds.has(i.id)) : undefined);
    if (!target) {
      onNotify('Selecione um insumo na tabela para ver o histórico.');
      return;
    }
    try {
      const res = await fetch(`/api/materials/${target.id}/history`);
      if (res.ok) {
        const data = await res.json();
        setHistoryModal({
          open: true,
          materialId: target.id,
          materialName: data.material.name,
          rows: data.rows || [],
        });
      }
    } catch (e) {
      console.error(e);
    }
  };

  const isBulkMode = checkedIds.size >= 2;

  return (
    <div className="flex flex-col h-full w-full">
      {/* 1. Toolbar Principal (RoundedPanel radius=22px, height=64px) */}
      <div className="h-[64px] w-full rounded-[22px] bg-white dark:bg-[#111F3B] px-6 mb-2 flex items-center justify-between shrink-0 shadow-sm transition-colors">
        {/* Left Action Buttons (Regra de Ouro da Multisseleção: oculta botões globais quando >= 2 itens marcados) */}
        <div className="flex items-center gap-2.5">
          {!isBulkMode ? (
            <>
              <RoundedActionButton
                label="Novo item"
                onClick={openNewMaterial}
                variant="primary"
                icon={<PlusIcon size={16} strokeWidth={2.6} />}
                height={38}
              />
              <RoundedActionButton
                label="Histórico"
                onClick={() => openHistoryModal()}
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
                  <div className="absolute right-0 top-[40px] w-[200px] rounded-[12px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-xl py-2.5 z-50">
                    <div className="px-3.5 pb-1.5 text-[10.5px] font-bold tracking-wider text-[#A0ABB9] uppercase">
                      Exibir Colunas
                    </div>
                    {COLUMNS.filter((c) => c.hideable).map((col) => {
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
            {items.length === 0 && !loading ? (
              <div className="flex-1 flex flex-col items-center justify-center py-12 select-none">
                <img
                  src="/ui_assets/empty_state_reference_exact.png"
                  alt="Sem registros"
                  className="max-h-[160px] object-contain mb-3 pointer-events-none"
                />
                <p className="text-[15px] font-bold text-[#687796] dark:text-[#93A4C6] mb-1">
                  Ainda não há registros cadastrados.
                </p>
                <p className="text-[12.5px] text-[#8A99B5] dark:text-[#687796]">
                  Clique em + Novo item para adicionar o primeiro item.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-[#F0F4FA] dark:divide-[#17294A]">
                {items.map((item) => {
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
                      onDoubleClick={() => openEditMaterial(item)}
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
                            case 'barcode':
                              cellContent = item.barcode || '';
                              break;
                            case 'name':
                              cellContent = <span className="font-medium">{item.name}</span>;
                              break;
                            case 'brand':
                              cellContent = item.brand || '';
                              break;
                            case 'qty':
                              cellContent = item.qty_fmt;
                              break;
                            case 'unit':
                              cellContent = item.unit;
                              break;
                            case 'value':
                              cellContent = <span className="font-medium">{item.value_fmt}</span>;
                              break;
                            case 'category':
                              cellContent = item.category;
                              break;
                            case 'date':
                              cellContent = item.date;
                              break;
                            case 'mod_date':
                              cellContent = item.mod_date;
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
                                  {item.status}
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
                            openEditMaterial(item);
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

      {/* Floating 3-Dots Row Context Menu */}
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
              openEditMaterial(target);
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

      {/* =====================================================================
          MODAL 1: Novo item / Editar item (material_form)
         ===================================================================== */}
      {formModal.open && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-[1px] flex items-center justify-center z-40">
          <div className="w-[580px] rounded-[22px] bg-[#F4F7FC] dark:bg-[#0B1730] border border-[#DDE5F2] dark:border-[#24385E] shadow-2xl overflow-visible flex flex-col">
            {/* Modal Title Bar */}
            <div className="px-6 pt-4 pb-2.5 flex items-center justify-between border-b border-[#E2EAF5] dark:border-[#1E3156]">
              <div className="flex items-center gap-2.5">
                <h2 className="text-[17px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  {formModal.editItem ? 'Editar item' : 'Novo item'}
                </h2>
                {formModal.editItem && (
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-[#FFF0D8] text-[#BA5200] dark:bg-[#5A3518] dark:text-[#F28C28]">
                    {formModal.editItem.code}
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => setFormModal({ open: false, editItem: null })}
                className="w-7 h-7 rounded-full flex items-center justify-center text-[#687796] hover:bg-black/5 dark:hover:bg-white/10"
              >
                ✕
              </button>
            </div>

            {/* Form Body */}
            <div className="px-6 py-4 space-y-3">
              {formError && (
                <div className="px-3.5 py-2 rounded-xl bg-[#FFF5F5] dark:bg-[#3B1822] border border-[#FEB2B2] dark:border-[#742A2A] text-[#C53030] dark:text-[#FF8A9B] text-[12px] font-medium">
                  {formError}
                </div>
              )}

              {/* Row 1: Nome * | Marca */}
              <div className="grid grid-cols-12 gap-2.5">
                <div className="col-span-8">
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                    Nome *
                  </label>
                  <CapsuleInput
                    value={fName}
                    onChange={setFName}
                    autoCapitalizeFirst
                    placeholder="Ex: Farinha de trigo"
                  />
                </div>
                <div className="col-span-4">
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                    Marca
                  </label>
                  <CapsuleInput
                    value={fBrand}
                    onChange={setFBrand}
                    autoCapitalizeFirst
                    placeholder="Ex: Dona Benta"
                  />
                </div>
              </div>

              {/* Row 2: Quantidade * | Unidade * | Valor da compra * */}
              <div className="grid grid-cols-12 gap-2.5">
                <div className="col-span-4">
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                    Quantidade *
                  </label>
                  <CapsuleInput
                    value={fQty}
                    onChange={setFQty}
                    type="numeric"
                    placeholder="Ex: 1000"
                  />
                </div>
                <div className="col-span-3">
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                    Unidade *
                  </label>
                  <RoundedDropdown
                    value={fUnit}
                    onChange={setFUnit}
                    options={units}
                    width="100%"
                    height={32}
                    align="left"
                    placeholder="Un."
                  />
                </div>
                <div className="col-span-5">
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                    Valor da compra *
                  </label>
                  <CapsuleInput
                    value={fValue}
                    onChange={setFValue}
                    type="money"
                    placeholder="R$ 0,00"
                  />
                </div>
              </div>

              {/* Row 3: Categoria * | Cód. Barras | Data * */}
              <div className="grid grid-cols-12 gap-2.5">
                <div className="col-span-4">
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                    Categoria *
                  </label>
                  <RoundedDropdown
                    value={fCategory}
                    onChange={setFCategory}
                    options={['Comestível', 'Não comestível', 'Doação']}
                    width="100%"
                    height={32}
                    align="left"
                  />
                </div>
                <div className="col-span-4">
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                    Cód. Barras
                  </label>
                  <CapsuleInput
                    value={fBarcode}
                    onChange={setFBarcode}
                    autoCapitalizeFirst={false}
                    spellCheck={false}
                    placeholder="EAN / Código"
                  />
                </div>
                <div className="col-span-4">
                  <label className="block text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-0.5 pl-1">
                    Data *
                  </label>
                  <CapsuleInput value={fDate} onChange={setFDate} type="date" />
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-3.5 border-t border-[#E2EAF5] dark:border-[#1E3156] flex items-center justify-between">
              <span className="text-[11.5px] italic text-[#687796] dark:text-[#93A4C6]">
                * campo obrigatório
              </span>
              <div className="flex items-center gap-2">
                <RoundedActionButton
                  label="Salvar"
                  onClick={handleSaveForm}
                  variant="primary"
                  height={34}
                />
                <RoundedActionButton
                  label="Cancelar"
                  onClick={() => setFormModal({ open: false, editItem: null })}
                  variant="secondary"
                  height={34}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          MODAL 2: Decisão Inteligente de Alteração (Marca / Preço / Lote)
         ===================================================================== */}
      {editDecisionModal && editDecisionModal.open && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-[1px] flex items-center justify-center z-50">
          <div className="w-[540px] rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col">
            {editDecisionModal.type === 'brand_change' ? (
              <>
                <div className="text-center mb-4">
                  <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-[#FFF0D8] text-[#F28C28] dark:bg-[#3D2514] mb-2 text-[18px]">
                    🏷️
                  </span>
                  <h3 className="text-[18px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    {editDecisionModal.priceDiff
                      ? 'Alteração de Marca e Preço Detectada'
                      : 'Alteração de Marca Detectada'}
                  </h3>
                  <p className="text-[13px] text-[#687796] dark:text-[#93A4C6] mt-0.5">
                    {editDecisionModal.priceDiff
                      ? 'Você modificou a marca e os valores deste insumo no formulário.'
                      : 'Você modificou a marca deste insumo no formulário.'}
                  </p>
                </div>

                {/* Comparison Card */}
                <div className="rounded-[16px] bg-[#F4F7FC] dark:bg-[#0B1730] border border-[#DDE5F2] dark:border-[#1E3156] p-4 mb-4">
                  <div className="text-[12px] font-semibold text-[#687796] dark:text-[#93A4C6] mb-2.5 flex items-center justify-between">
                    <span>
                      Insumo: <strong className="text-[#18223A] dark:text-[#F4F7FF]">{editDecisionModal.brandDiff?.name}</strong>
                    </span>
                    {editDecisionModal.beforeItem.code && (
                      <span className="font-mono text-[11px] px-2 py-0.5 rounded-full bg-[#E2EAF5] dark:bg-[#1E3156] text-[#475569] dark:text-[#AFC0E2]">
                        {editDecisionModal.beforeItem.code}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between gap-3 pt-1">
                    <div className="flex-1 bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] rounded-[12px] p-2.5 text-center">
                      <span className="block text-[10.5px] uppercase tracking-wider font-semibold text-[#8C9BB5]">Anterior</span>
                      <div className="mt-1 flex flex-col items-center">
                        <span className="text-[13.5px] font-bold text-[#18223A] dark:text-[#F4F7FF] truncate max-w-full">
                          {editDecisionModal.brandDiff?.oldBrand}
                        </span>
                        {editDecisionModal.priceDiff && (
                          <span className="text-[12px] font-semibold text-[#475569] dark:text-[#AFC0E2] mt-0.5">
                            R$ {editDecisionModal.priceDiff.oldPrice}{' '}
                            <span className="text-[11px] font-normal">
                              ({editDecisionModal.priceDiff.oldQty} {editDecisionModal.priceDiff.oldUnit})
                            </span>
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="text-[#F28C28] text-[18px] font-bold">➔</span>
                    <div className="flex-1 bg-white dark:bg-[#111F3B] border border-[#F28C28]/40 dark:border-[#F28C28]/50 rounded-[12px] p-2.5 text-center">
                      <span className="block text-[10.5px] uppercase tracking-wider font-semibold text-[#F28C28]">Novo Registro</span>
                      <div className="mt-1 flex flex-col items-center">
                        <span className="text-[13.5px] font-bold text-[#F28C28] truncate max-w-full">
                          {editDecisionModal.brandDiff?.newBrand}
                        </span>
                        {editDecisionModal.priceDiff && (
                          <span className="text-[12px] font-bold text-[#F28C28] mt-0.5">
                            R$ {editDecisionModal.priceDiff.newPrice}{' '}
                            <span className="text-[11px] font-normal">
                              ({editDecisionModal.priceDiff.newQty} {editDecisionModal.priceDiff.newUnit})
                            </span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <p className="text-[13px] font-semibold text-[#18223A] dark:text-[#F4F7FF] mb-3">
                  Como deseja registrar essa mudança?
                </p>

                <div className="flex flex-col gap-2.5 mb-5">
                  {/* Option 1: Cadastrar como Novo Insumo */}
                  <button
                    type="button"
                    onClick={handleCreateAsNewMaterial}
                    className="w-full text-left p-3.5 rounded-[16px] bg-[#FFF8EE] hover:bg-[#FFF2DE] dark:bg-[#2A1E14] dark:hover:bg-[#382618] border border-[#F28C28]/50 hover:border-[#F28C28] transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[13.5px] font-bold text-[#F28C28] flex items-center gap-2">
                        ➕ Cadastrar como Novo Insumo
                        <span className="text-[10.5px] font-medium px-2 py-0.5 rounded-full bg-[#F28C28] text-white">
                          Recomendado
                        </span>
                      </span>
                      <span className="text-[#F28C28] group-hover:translate-x-1 transition-transform font-bold">➔</span>
                    </div>
                    <p className="text-[12px] text-[#687796] dark:text-[#CBD5E1] leading-relaxed">
                      {editDecisionModal.priceDiff ? (
                        <>
                          Cria o insumo <strong>"{editDecisionModal.brandDiff?.name} ({editDecisionModal.brandDiff?.newBrand})"</strong> com valor inicial de <strong>R$ {editDecisionModal.priceDiff.newPrice}</strong>. O insumo anterior ({editDecisionModal.brandDiff?.oldBrand}, R$ {editDecisionModal.priceDiff.oldPrice}) permanece 100% intacto no banco com todo o seu histórico e receitas.
                        </>
                      ) : (
                        <>
                          Cria um novo insumo da marca <strong>"{editDecisionModal.brandDiff?.newBrand}"</strong> e mantém o insumo original ({editDecisionModal.brandDiff?.oldBrand}), suas receitas e histórico intactos.
                        </>
                      )}
                    </p>
                  </button>

                  {/* Option 2: Manter no Mesmo Insumo */}
                  <button
                    type="button"
                    onClick={handleCorrectBrandOnly}
                    className="w-full text-left p-3.5 rounded-[16px] bg-[#F9FBFC] hover:bg-[#F2F6FA] dark:bg-[#0E1A30] dark:hover:bg-[#162747] border border-[#DDE5F2] dark:border-[#24385E] transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[13.5px] font-bold text-[#18223A] dark:text-[#F4F7FF] flex items-center gap-2">
                        {editDecisionModal.priceDiff
                          ? '✏️ Manter no Mesmo Insumo'
                          : '✏️ Apenas Corrigir o Nome da Marca'}
                      </span>
                      <span className="text-[#687796] dark:text-[#93A4C6] group-hover:translate-x-1 transition-transform font-bold">➔</span>
                    </div>
                    <p className="text-[12px] text-[#687796] dark:text-[#CBD5E1] leading-relaxed">
                      {editDecisionModal.priceDiff ? (
                        <>
                          Atualiza a marca para <strong>"{editDecisionModal.brandDiff?.newBrand}"</strong> no mesmo insumo e permite definir se o novo valor de <strong>R$ {editDecisionModal.priceDiff.newPrice}</strong> é uma Nova Compra ou Erro de Digitação.
                        </>
                      ) : (
                        <>
                          Atualiza o nome da marca neste mesmo insumo. Escolha esta opção caso tenha apenas digitado a marca errada.
                        </>
                      )}
                    </p>
                  </button>
                </div>

                <div className="flex justify-end pt-2 border-t border-[#E2EAF5] dark:border-[#24385E]">
                  <RoundedActionButton
                    label="Cancelar e Voltar"
                    onClick={() => setEditDecisionModal(null)}
                    variant="ghost"
                    height={36}
                  />
                </div>
              </>
            ) : editDecisionModal.step === 'choice' ? (
              <>
                <div className="text-center mb-4">
                  <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-[#FFF0D8] text-[#F28C28] dark:bg-[#3D2514] mb-2 text-[18px]">
                    🛒
                  </span>
                  <h3 className="text-[18px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Alteração de Preço / Embalagem
                  </h3>
                  <p className="text-[13px] text-[#687796] dark:text-[#93A4C6] mt-0.5">
                    Identificamos uma alteração no valor ou tamanho da compra.
                  </p>
                </div>

                {/* Comparison Card */}
                <div className="rounded-[16px] bg-[#F4F7FC] dark:bg-[#0B1730] border border-[#DDE5F2] dark:border-[#1E3156] p-4 mb-4">
                  <div className="text-[12px] font-semibold text-[#687796] dark:text-[#93A4C6] mb-2 flex items-center justify-between">
                    <span>
                      Insumo: <strong className="text-[#18223A] dark:text-[#F4F7FF]">{editDecisionModal.beforeItem.name}</strong>
                      {editDecisionModal.beforeItem.brand ? ` (${editDecisionModal.beforeItem.brand})` : ''}
                    </span>
                    {editDecisionModal.beforeItem.code && (
                      <span className="font-mono text-[11px] px-2 py-0.5 rounded-full bg-[#E2EAF5] dark:bg-[#1E3156] text-[#475569] dark:text-[#AFC0E2]">
                        {editDecisionModal.beforeItem.code}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between gap-3 pt-1">
                    <div className="flex-1 bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] rounded-[12px] p-2.5 text-center">
                      <span className="block text-[10.5px] uppercase tracking-wider font-semibold text-[#8C9BB5]">Anterior</span>
                      <span className="block text-[13.5px] font-bold text-[#18223A] dark:text-[#F4F7FF] truncate">
                        R$ {editDecisionModal.priceDiff?.oldPrice}
                      </span>
                      <span className="block text-[11px] text-[#687796] dark:text-[#93A4C6]">
                        ({editDecisionModal.priceDiff?.oldQty} {editDecisionModal.priceDiff?.oldUnit})
                      </span>
                    </div>
                    <span className="text-[#F28C28] text-[18px] font-bold">➔</span>
                    <div className="flex-1 bg-white dark:bg-[#111F3B] border border-[#F28C28]/40 dark:border-[#F28C28]/50 rounded-[12px] p-2.5 text-center">
                      <span className="block text-[10.5px] uppercase tracking-wider font-semibold text-[#F28C28]">Novo Registro</span>
                      <span className="block text-[13.5px] font-bold text-[#F28C28] truncate">
                        R$ {editDecisionModal.priceDiff?.newPrice}
                      </span>
                      <span className="block text-[11px] text-[#F28C28]/80 font-medium">
                        ({editDecisionModal.priceDiff?.newQty} {editDecisionModal.priceDiff?.newUnit})
                      </span>
                    </div>
                  </div>
                </div>

                <p className="text-[13px] font-semibold text-[#18223A] dark:text-[#F4F7FF] mb-3">
                  Essa alteração representa uma nova compra ou correção?
                </p>

                <div className="flex flex-col gap-2.5 mb-5">
                  {/* Option 1: Nova Compra */}
                  <button
                    type="button"
                    onClick={() =>
                      setEditDecisionModal((prev) => (prev ? { ...prev, step: 'reason' } : null))
                    }
                    className="w-full text-left p-3.5 rounded-[16px] bg-[#FFF8EE] hover:bg-[#FFF2DE] dark:bg-[#2A1E14] dark:hover:bg-[#382618] border border-[#F28C28]/50 hover:border-[#F28C28] transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[13.5px] font-bold text-[#F28C28] flex items-center gap-2">
                        🛒 Nova Compra / Reajuste
                        <span className="text-[10.5px] font-medium px-2 py-0.5 rounded-full bg-[#F28C28] text-white">
                          Histórico + BI
                        </span>
                      </span>
                      <span className="text-[#F28C28] group-hover:translate-x-1 transition-transform font-bold">➔</span>
                    </div>
                    <p className="text-[12px] text-[#687796] dark:text-[#CBD5E1] leading-relaxed">
                      Registra esta compra no histórico com data e hora atuais e atualiza os gráficos de evolução de preços do BI.
                    </p>
                  </button>

                  {/* Option 2: Erro de Digitação */}
                  <button
                    type="button"
                    onClick={() => executeEditSave('correction', 'Correção de digitação')}
                    className="w-full text-left p-3.5 rounded-[16px] bg-[#F9FBFC] hover:bg-[#F2F6FA] dark:bg-[#0E1A30] dark:hover:bg-[#162747] border border-[#DDE5F2] dark:border-[#24385E] transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[13.5px] font-bold text-[#18223A] dark:text-[#F4F7FF] flex items-center gap-2">
                        ✏️ Erro de Digitação
                      </span>
                      <span className="text-[#687796] dark:text-[#93A4C6] group-hover:translate-x-1 transition-transform font-bold">➔</span>
                    </div>
                    <p className="text-[12px] text-[#687796] dark:text-[#CBD5E1] leading-relaxed">
                      Apenas corrige o valor ou quantidade digitada anteriormente. Não gera compra duplicada no histórico e não distorce o BI.
                    </p>
                  </button>
                </div>

                <div className="flex justify-end pt-2 border-t border-[#E2EAF5] dark:border-[#24385E]">
                  <RoundedActionButton
                    label="Cancelar e Voltar"
                    onClick={() => setEditDecisionModal(null)}
                    variant="ghost"
                    height={36}
                  />
                </div>
              </>
            ) : (
              <>
                <div className="text-center mb-4">
                  <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-[#FFF0D8] text-[#F28C28] dark:bg-[#3D2514] mb-2 text-[18px]">
                    📝
                  </span>
                  <h3 className="text-[18px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                    Justificativa da Nova Compra
                  </h3>
                  <p className="text-[13px] text-[#687796] dark:text-[#93A4C6] mt-0.5">
                    Informe o motivo para constar no histórico e relatórios de BI:
                  </p>
                </div>

                <div className="flex flex-col mb-5">
                  <textarea
                    rows={3}
                    value={editDecisionModal.reasonText}
                    onChange={(e) => {
                      let text = e.target.value;
                      if (text.length > 0) {
                        text = text.replace(/[a-zA-ZÀ-ÿ]/, (m) => m.toUpperCase());
                      }
                      setEditDecisionModal((prev) =>
                        prev ? { ...prev, reasonText: text } : null
                      );
                    }}
                    spellCheck={true}
                    lang="pt-BR"
                    placeholder="Ex: Reajuste de fornecedor, novo lote adquirido..."
                    className="w-full rounded-[14px] bg-[#F9FBFC] dark:bg-[#0E1B35] border border-[#DDE5F2] dark:border-[#24385E] p-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] focus:outline-none focus:border-[#F28C28]"
                  />
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-[#E2EAF5] dark:border-[#24385E]">
                  <RoundedActionButton
                    label="Voltar"
                    onClick={() =>
                      setEditDecisionModal((prev) => (prev ? { ...prev, step: 'choice' } : null))
                    }
                    variant="soft"
                    height={38}
                    width={100}
                  />
                  <RoundedActionButton
                    label="Salvar Nova Compra"
                    onClick={() => executeEditSave('update', editDecisionModal.reasonText)}
                    variant="primary"
                    height={38}
                    width={180}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* =====================================================================
          MODAL 3: Exclusão Inteligente / Em Lote (CustomDeleteAlertModal)
         ===================================================================== */}
      {deleteModal && deleteModal.open && (
        <div className="fixed inset-0 bg-black/45 flex items-center justify-center z-50">
          <div className="w-[540px] rounded-[20px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col">
            <h3 className="text-[18px] font-bold text-[#18223A] dark:text-[#F4F7FF] text-center mb-4">
              {deleteModal.check.total === 1 ? 'Excluir Item' : 'Exclusão em Lote'}
            </h3>

            <div className="flex-1 text-[13.5px] text-[#18223A] dark:text-[#F4F7FF] space-y-3 my-2">
              {deleteModal.check.total === 1 ? (
                deleteModal.check.unlinked.length === 1 ? (
                  <p className="text-center py-4 text-[14.5px]">
                    Tem certeza que deseja excluir permanentemente o item:
                    <br />
                    <strong className="text-[16px] block mt-2">
                      {deleteModal.check.unlinked[0].name}
                    </strong>
                    ?
                  </p>
                ) : (
                  <div className="space-y-3 text-center">
                    {deleteModal.check.linked[0].active ? (
                      <>
                        <p>
                          O item <strong>'{deleteModal.check.linked[0].name}'</strong> possui
                          vínculos em receitas ou produtos e NÃO pode ser excluído permanentemente
                          para não corromper o histórico.
                        </p>
                        <p className="font-bold text-[#9B2C2C] dark:text-[#F6A45A]">
                          Deseja INATIVAR este item?
                          <br />
                          Ele não aparecerá mais nas listas de ativos, mas será preservado.
                        </p>
                      </>
                    ) : (
                      <>
                        <p>
                          O item <strong>'{deleteModal.check.linked[0].name}'</strong> já está
                          inativo, mas ainda possui vínculos com receitas/produtos.
                        </p>
                        <p className="font-bold text-[#9B2C2C] dark:text-[#F6A45A]">
                          Deseja OCULTÁ-LO definitivamente do sistema?
                        </p>
                      </>
                    )}
                  </div>
                )
              ) : (
                <div className="space-y-3">
                  <p className="font-bold">
                    Você selecionou {deleteModal.check.total} itens:
                  </p>
                  {deleteModal.check.linked.length > 0 && (
                    <div className="p-3 rounded-[14px] bg-[#FFFAF0] dark:bg-[#3D2610] border border-[#FBD38D] dark:border-[#C05621] text-[#C05621] dark:text-[#F6A45A]">
                      <div className="font-bold text-[12.5px] mb-1">
                        ⚠️ {deleteModal.check.linked.length} itens possuem vínculos e serão apenas
                        INATIVADOS:
                      </div>
                      <div className="text-[12px] max-h-24 overflow-y-auto space-y-0.5 pl-2">
                        {deleteModal.check.linked.map((i) => (
                          <div key={i.id}>• {i.name}</div>
                        ))}
                      </div>
                    </div>
                  )}
                  {deleteModal.check.unlinked.length > 0 && (
                    <div className="p-3 rounded-[14px] bg-[#FFF5F5] dark:bg-[#3B1822] border border-[#FEB2B2] dark:border-[#9B2C2C] text-[#C53030] dark:text-[#FF8A9B]">
                      <div className="font-bold text-[12.5px] mb-1">
                        🔴 {deleteModal.check.unlinked.length} itens livres serão EXCLUÍDOS
                        permanentemente:
                      </div>
                      <div className="text-[12px] max-h-24 overflow-y-auto space-y-0.5 pl-2">
                        {deleteModal.check.unlinked.map((i) => (
                          <div key={i.id}>• {i.name}</div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between mt-6 pt-2">
              <RoundedActionButton
                label="Cancelar"
                onClick={() => setDeleteModal(null)}
                variant="soft"
                height={40}
                width={125}
              />
              <button
                type="button"
                onClick={confirmDeleteExecute}
                style={{
                  backgroundColor:
                    deleteModal.check.unlinked.length > 0 ? '#C53030' : '#DD6B20',
                }}
                className="h-[40px] px-6 rounded-full text-white font-bold text-[13.5px] hover:opacity-90 transition-opacity cursor-pointer"
              >
                {deleteModal.check.total === 1
                  ? deleteModal.check.unlinked.length === 1
                    ? 'Excluir Permanentemente'
                    : deleteModal.check.linked[0].active
                    ? 'Inativar / Ocultar'
                    : 'Ocultar Definitivamente'
                  : deleteModal.check.linked.length > 0 && deleteModal.check.unlinked.length > 0
                  ? 'Executar Operação Mista'
                  : deleteModal.check.linked.length > 0
                  ? 'Inativar Itens'
                  : 'Excluir Itens'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          MODAL 4: Histórico do Insumo (CustomHistoryModal - Regra doc 02.4.D)
         ===================================================================== */}
      {historyModal && historyModal.open && (
        <HistoryModalComponent
          materialId={historyModal.materialId}
          materialName={historyModal.materialName}
          rows={historyModal.rows}
          onClose={() => setHistoryModal(null)}
        />
      )}

    </div>
  );
};

// ---------- Sub-Component: CustomHistoryModal ----------

const HistoryModalComponent: React.FC<{
  materialId: number;
  materialName: string;
  rows: MaterialHistoryRow[];
  onClose: () => void;
}> = ({ materialId, materialName, rows, onClose }) => {
  const [filterQuery, setFilterQuery] = useState('');
  const [sortCol, setSortCol] = useState<'date' | 'qty' | 'unit' | 'value' | 'brand' | null>(
    null
  );
  const [sortAsc, setSortAsc] = useState(false);

  const handleSort = (col: 'date' | 'qty' | 'unit' | 'value' | 'brand') => {
    if (sortCol === col) {
      setSortAsc((a) => !a);
    } else {
      setSortCol(col);
      setSortAsc(true);
    }
  };

  const filteredAndSorted = useMemo(() => {
    const q = filterQuery.trim().toLowerCase();
    let list = [...rows];
    if (q) {
      list = list.filter(
        (r) =>
          r.date_fmt.toLowerCase().includes(q) ||
          r.qty_fmt.toLowerCase().includes(q) ||
          r.unit.toLowerCase().includes(q) ||
          r.value_fmt.toLowerCase().includes(q) ||
          r.brand.toLowerCase().includes(q)
      );
    }
    if (sortCol) {
      list.sort((a, b) => {
        let cmp = 0;
        if (sortCol === 'qty') cmp = a.qty - b.qty;
        else if (sortCol === 'value') cmp = a.value - b.value;
        else if (sortCol === 'date') cmp = a.raw_date.localeCompare(b.raw_date);
        else if (sortCol === 'unit') cmp = a.unit.localeCompare(b.unit);
        else if (sortCol === 'brand') cmp = a.brand.localeCompare(b.brand);
        return sortAsc ? cmp : -cmp;
      });
    }
    return list;
  }, [rows, filterQuery, sortCol, sortAsc]);

  const handleExportCsv = () => {
    window.open(`/api/materials/${materialId}/history/export`, '_blank');
  };

  return (
    <div className="fixed inset-0 bg-black/45 flex items-center justify-center z-50">
      <div className="w-[760px] h-[520px] rounded-[22px] bg-[#F4F7FC] dark:bg-[#0B1730] border border-[#DDE5F2] dark:border-[#24385E] shadow-2xl flex flex-col overflow-hidden">
        {/* Top Window Bar */}
        <div className="px-6 pt-4 pb-2 flex items-center justify-between border-b border-[#E2EAF5] dark:border-[#1E3156]">
          <span className="text-xs font-bold text-[#687796] dark:text-[#93A4C6]">
            Histórico de Preços e Compras
          </span>
          <button
            type="button"
            onClick={onClose}
            className="w-7 h-7 rounded-full flex items-center justify-center text-[#687796] hover:bg-black/5 dark:hover:bg-white/10"
          >
            ✕
          </button>
        </div>

        {/* Header Area (Regra doc 02.4.D: Label interno exibe APENAS o Nome do Item sem redundância) */}
        <div className="px-6 pt-4 pb-3 flex items-center justify-between">
          <h2 className="text-[20px] font-bold text-[#18223A] dark:text-[#F4F7FF] truncate">
            {materialName}
          </h2>
          <RoundedEntry
            value={filterQuery}
            onChange={setFilterQuery}
            placeholder="Filtrar..."
            width={190}
            height={32}
          />
        </div>

        {/* Table Area */}
        <div className="flex-1 mx-6 rounded-[18px] bg-white dark:bg-[#111F3B] p-2.5 flex flex-col min-h-0 border border-[#E2EAF5] dark:border-[#24385E]">
          {/* Rounded Header */}
          <div className="h-[36px] rounded-full bg-[#EEF4FB] dark:bg-[#142544] flex items-center text-[12.5px] font-bold text-[#60769D] dark:text-[#AFC0E2] select-none shrink-0">
            {[
              { key: 'date', label: 'Data/Hora', w: 'w-[30%] text-left pl-4' },
              { key: 'qty', label: 'Qtd.', w: 'w-[16%] text-center' },
              { key: 'unit', label: 'Un.', w: 'w-[12%] text-center' },
              { key: 'value', label: 'Custo', w: 'w-[20%] text-center' },
              { key: 'brand', label: 'Marca', w: 'w-[22%] text-left pl-3' },
            ].map((c, idx) => {
              const arrow =
                sortCol === c.key ? (sortAsc ? ' ▲' : ' ▼') : '';
              return (
                <button
                  key={c.key}
                  type="button"
                  onClick={() => handleSort(c.key as any)}
                  className={`h-full ${c.w} hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer ${
                    idx < 4 ? 'border-r border-[#E5ECF5] dark:border-[#24385E]' : ''
                  }`}
                >
                  {c.label}
                  {arrow}
                </button>
              );
            })}
          </div>

          {/* Rows */}
          <div className="flex-1 overflow-y-auto divide-y divide-[#F0F4FA] dark:divide-[#17294A] mt-1">
            {filteredAndSorted.map((r) => (
              <div
                key={String(r.id)}
                className={`h-[36px] flex items-center text-[13px] ${
                  r.is_today
                    ? 'bg-[#FFF9F0] dark:bg-[#231B12] font-semibold text-[#18223A] dark:text-[#F4F7FF]'
                    : 'text-[#18223A] dark:text-[#F4F7FF]'
                }`}
              >
                <div className="w-[30%] pl-4 truncate flex items-center gap-2">
                  <span>{r.date_fmt.replace(' (Hoje)', '')}</span>
                  {r.is_today && (
                    <span className="text-[10.5px] font-bold px-2 py-0.5 rounded-full bg-[#FFF2E2] dark:bg-[#432612] text-[#F28C28] border border-[#FCD9BD] dark:border-[#7A431D]">
                      Atual
                    </span>
                  )}
                </div>
                <div className="w-[16%] text-center">{r.qty_fmt}</div>
                <div className="w-[12%] text-center">{r.unit}</div>
                <div className="w-[20%] text-center font-medium">{r.value_fmt}</div>
                <div className="w-[22%] pl-3 truncate">{r.brand}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 flex items-center justify-between">
          <RoundedActionButton
            label="Fechar"
            onClick={onClose}
            variant="ghost"
            height={36}
          />
          <RoundedActionButton
            icon={
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            }
            label="Baixar Histórico"
            onClick={handleExportCsv}
            variant="green"
            height={36}
            width={170}
          />
        </div>
      </div>
    </div>
  );
};

