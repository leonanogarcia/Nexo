import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { MaterialOption, ConversionItem } from '../types';
import { RoundedDropdown, RoundedEntry, RoundedActionButton } from './DesignSystem';

// ---------- ConversionsModal (Regra doc 04.3) ----------

export const ConversionsModal: React.FC<{
  initialMaterialId?: number | null;
  onClose: () => void;
  onNotify: (msg: string, type?: 'success' | 'warning' | 'error') => void;
}> = ({ onClose, onNotify }) => {
  const [options, setOptions] = useState<MaterialOption[]>([]);
  const [selectedLabel, setSelectedLabel] = useState('');
  const [conversions, setConversions] = useState<ConversionItem[]>([]);

  const [unitName, setUnitName] = useState('');
  const [baseUnit, setBaseUnit] = useState('g');
  const [factor, setFactor] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Fused capsule unit dropdown
  const [unitDropdownOpen, setUnitDropdownOpen] = useState(false);
  const unitWrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (unitWrapRef.current && !unitWrapRef.current.contains(e.target as Node)) {
        setUnitDropdownOpen(false);
      }
    };
    if (unitDropdownOpen) {
      document.addEventListener('mousedown', handleOutside);
    }
    return () => document.removeEventListener('mousedown', handleOutside);
  }, [unitDropdownOpen]);

  // Table sorting & resizable column state
  const [sortCol, setSortCol] = useState<'name' | 'factor' | null>(null);
  const [sortDir, setSortDir] = useState<'ASC' | 'DESC'>('ASC');
  const [nameColPct, setNameColPct] = useState(68);
  const tableRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/materials/options');
        if (res.ok) {
          const data = await res.json();
          const list: MaterialOption[] = data.items || [];
          setOptions(list);
          // Always opens clean without pre-selection
          setSelectedLabel('');
        }
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  const selectedMaterialId = useMemo(() => {
    if (!selectedLabel) return null;
    const prefix = selectedLabel.split(' - ')[0];
    const id = parseInt(prefix, 10);
    return isNaN(id) ? null : id;
  }, [selectedLabel]);

  const fetchConversions = useCallback(async () => {
    if (!selectedMaterialId) {
      setConversions([]);
      return;
    }
    try {
      const res = await fetch(`/api/materials/${selectedMaterialId}/conversions`);
      if (res.ok) {
        const data = await res.json();
        setConversions(data.items || []);
      }
    } catch (e) {
      console.error(e);
    }
  }, [selectedMaterialId]);

  useEffect(() => {
    fetchConversions();
  }, [fetchConversions]);

  const handleSort = (col: 'name' | 'factor') => {
    if (sortCol === col) {
      setSortDir((d) => (d === 'ASC' ? 'DESC' : 'ASC'));
    } else {
      setSortCol(col);
      setSortDir('ASC');
    }
  };

  const displayedConversions = useMemo(() => {
    if (!sortCol) return conversions;
    const list = [...conversions];
    list.sort((a, b) => {
      let cmp = 0;
      if (sortCol === 'name') {
        cmp = a.name.localeCompare(b.name, 'pt-BR', { sensitivity: 'base' });
      } else if (sortCol === 'factor') {
        cmp = a.factor_to_base - b.factor_to_base;
      }
      return sortDir === 'ASC' ? cmp : -cmp;
    });
    return list;
  }, [conversions, sortCol, sortDir]);

  const handleMouseDownResizer = (e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingRef.current = true;
    const startX = e.clientX;
    const initialPct = nameColPct;
    const tableWidth = tableRef.current ? tableRef.current.clientWidth : 640;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const deltaX = moveEvent.clientX - startX;
      const deltaPct = (deltaX / tableWidth) * 100;
      const newPct = Math.min(84, Math.max(30, initialPct + deltaPct));
      setNameColPct(newPct);
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const handleSaveConversion = async () => {
    setError(null);
    if (!selectedMaterialId) {
      setError('Selecione um insumo primeiro.');
      return;
    }
    if (!unitName.trim()) {
      setError('O nome da medida é obrigatório.');
      return;
    }
    if (!factor.trim()) {
      setError('O campo "Quantidade" é obrigatório.');
      return;
    }
    try {
      const res = await fetch('/api/conversions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          material_id: selectedMaterialId,
          name: unitName.trim(),
          base_unit: baseUnit,
          factor_to_base: factor.trim(),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Não foi possível salvar a conversão.');
        return;
      }
      setUnitName('');
      setFactor('');
      await fetchConversions();
      onNotify('Conversão salva com sucesso!');
    } catch (e: any) {
      setError(e.message || 'Erro ao salvar conversão.');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/45 flex items-center justify-center z-50">
      <div className="w-[700px] max-h-[92vh] rounded-[22px] bg-[#F4F7FC] dark:bg-[#0B1730] border border-[#DDE5F2] dark:border-[#24385E] shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 pt-5 pb-3 flex items-center justify-between border-b border-[#E2EAF5] dark:border-[#1E3156] bg-white dark:bg-[#0F1B35]">
          <div>
            <h2 className="text-[18px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              Conversões de Medidas
            </h2>
            <p className="text-[12px] text-[#687796] dark:text-[#93A4C6] mt-0.5">
              Defina equivalências (ex: xícara, colher, pote) para o cálculo exato do custo em fichas técnicas.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center text-[#687796] hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="px-6 pt-4 pb-4 flex flex-col min-h-0 flex-1">
          {error && (
            <div className="mb-3 px-4 py-2 rounded-full bg-[#FFF5F5] dark:bg-[#3B1822] text-[#C53030] dark:text-[#FF8A9B] text-xs font-medium">
              {error}
            </div>
          )}

          {/* Insumo Selector (Always starts clean with placeholder) */}
          <div className="flex items-center gap-3 mb-3.5">
            <span className="text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] shrink-0">
              Insumo:
            </span>
            <div className="flex-1">
              <RoundedDropdown
                value={selectedLabel}
                onChange={setSelectedLabel}
                options={options.map((o) => o.label)}
                width="100%"
                height={34}
                align="left"
                placeholder="Selecione o insumo..."
              />
            </div>
          </div>

          {/* Intuitive Equation Form Card */}
          <div className="p-3.5 rounded-[16px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-sm mb-3">
            <div className="flex items-end gap-2.5">
              {/* Medida / Nome */}
              <div className="flex-1 min-w-0">
                <label className="block text-[11.5px] font-semibold text-[#687796] dark:text-[#93A4C6] mb-1 pl-1">
                  1 Medida / Nome *
                </label>
                <RoundedEntry
                  value={unitName}
                  onChange={setUnitName}
                  autoCapitalizeFirst={true}
                  spellCheck={true}
                  placeholder="Ex: Xícara de chá, Colher"
                  width="100%"
                  height={34}
                  icon={false}
                />
              </div>

              {/* Vector Geometric Equal Sign - 100% Sub-pixel Vertically Centered */}
              <div
                title="Equivale a"
                className="h-[34px] flex items-center justify-center shrink-0 px-2 select-none"
              >
                <svg
                  width="20"
                  height="14"
                  viewBox="0 0 20 14"
                  fill="none"
                  className="text-[#F28C28]"
                >
                  <rect x="0" y="2" width="20" height="3" rx="1.5" fill="currentColor" />
                  <rect x="0" y="9" width="20" height="3" rx="1.5" fill="currentColor" />
                </svg>
              </div>

              {/* Fused Capsule: [ Quantidade | Unidade ▼ ] */}
              <div className="shrink-0" ref={unitWrapRef}>
                <label className="block text-[11.5px] font-semibold text-[#687796] dark:text-[#93A4C6] mb-1 pl-1">
                  Quantidade * | Unidade *
                </label>
                <div className="relative inline-flex items-center h-[34px] rounded-full bg-white dark:bg-[#0E1B35] border border-[#B0C0D6] dark:border-[#24385E] focus-within:border-[#F28C28] dark:focus-within:border-[#F28C28] transition-colors">
                  {/* Numeric Input */}
                  <input
                    type="text"
                    value={factor}
                    onChange={(e) => setFactor(e.target.value.replace(/[^0-9.,]/g, ''))}
                    placeholder="Ex: 200"
                    className="w-[100px] h-full bg-transparent px-3 text-[13px] text-[#18223A] dark:text-[#F4F7FF] placeholder-[#9AA9BF] focus:outline-none text-center font-medium"
                  />

                  {/* Gray Divider Line */}
                  <div className="w-[1px] h-[18px] bg-[#B0C0D6] dark:bg-[#2A3F66] shrink-0" />

                  {/* Unit Selector Trigger */}
                  <button
                    type="button"
                    onClick={() => setUnitDropdownOpen((o) => !o)}
                    className="h-full px-3 flex items-center justify-center gap-1.5 text-[13px] font-bold text-[#18223A] dark:text-[#F4F7FF] hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer select-none"
                  >
                    <span>{baseUnit}</span>
                    <svg
                      width="10"
                      height="10"
                      viewBox="0 0 12 12"
                      fill="none"
                      className={`text-[#687796] transition-transform duration-150 ${
                        unitDropdownOpen ? 'rotate-180' : ''
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

                  {/* Floating Unit Menu */}
                  {unitDropdownOpen && (
                    <div className="absolute right-0 top-[40px] w-[80px] rounded-[12px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-xl py-1 z-50">
                      {['g', 'kg', 'ml', 'L', 'un', 'mg'].map((u) => (
                        <button
                          key={u}
                          type="button"
                          onClick={() => {
                            setBaseUnit(u);
                            setUnitDropdownOpen(false);
                          }}
                          className={`w-full h-8 px-3 text-[12.5px] flex items-center justify-center transition-colors cursor-pointer hover:bg-[#F8FAFC] dark:hover:bg-[#172746] ${
                            u === baseUnit
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
              </div>

              {/* Action Button */}
              <div className="shrink-0">
                <RoundedActionButton
                  label="Salvar"
                  onClick={handleSaveConversion}
                  variant="primary"
                  height={34}
                  width={85}
                />
              </div>
            </div>

            {/* Live Administrative Helper Preview */}
            {unitName.trim() && factor.trim() && (
              <div className="mt-2.5 pt-2 border-t border-[#F0F4FA] dark:border-[#17294A] flex items-center gap-1.5 text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
                <span className="font-semibold text-[#18223A] dark:text-[#F4F7FF]">Prévia da Ficha Técnica:</span>
                <span>Ao usar</span>
                <span className="font-bold text-[#F28C28]">1 {unitName.trim()}</span>
                <span>na receita, o custo calculará sobre</span>
                <span className="font-bold text-[#18223A] dark:text-[#F4F7FF]">{factor.trim()} {baseUnit}</span>.
              </div>
            )}
          </div>

          {/* Table Area (with Sorting & Resizable Column Divider) */}
          <div
            ref={tableRef}
            className="flex-1 rounded-[16px] bg-white dark:bg-[#111F3B] p-2 flex flex-col min-h-[190px] max-h-[240px] border border-[#E2EAF5] dark:border-[#24385E]"
          >
            {/* Interactive Capsule Header */}
            <div className="h-[34px] rounded-full bg-[#EEF4FB] dark:bg-[#142544] flex items-center text-[12px] font-bold text-[#60769D] dark:text-[#AFC0E2] shrink-0 select-none overflow-hidden relative">
              {/* Left Column Button (Medida Cadastrada) */}
              <button
                type="button"
                onClick={() => handleSort('name')}
                style={{ width: `${nameColPct}%` }}
                className="h-full pl-4 pr-2 flex items-center justify-start text-left hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer truncate"
              >
                <span className="truncate">
                  Medida Cadastrada
                  {sortCol === 'name' && (
                    <span className="ml-1 text-[#F28C28]">{sortDir === 'ASC' ? '↑' : '↓'}</span>
                  )}
                </span>
              </button>

              {/* Draggable Divider Handle */}
              <div
                onMouseDown={handleMouseDownResizer}
                title="Arraste para redimensionar as colunas"
                className="w-[10px] h-full flex items-center justify-center cursor-col-resize hover:bg-[#F28C28]/20 transition-colors z-20 shrink-0"
              >
                <div className="w-[1.5px] h-4 bg-[#B0C0D6] dark:bg-[#344E7A]" />
              </div>

              {/* Right Column Button (Equivalência Real) */}
              <button
                type="button"
                onClick={() => handleSort('factor')}
                style={{ width: `${100 - nameColPct}%` }}
                className="h-full px-3 flex items-center justify-center text-center hover:text-[#BA5200] dark:hover:text-[#F28C28] transition-colors cursor-pointer truncate flex-1"
              >
                <span className="truncate">
                  Equivalência Real
                  {sortCol === 'factor' && (
                    <span className="ml-1 text-[#F28C28]">{sortDir === 'ASC' ? '↑' : '↓'}</span>
                  )}
                </span>
              </button>
            </div>

            {/* Table Rows Body */}
            <div className="flex-1 overflow-y-auto divide-y divide-[#F0F4FA] dark:divide-[#17294A] mt-1">
              {!selectedMaterialId ? (
                <div className="h-full min-h-[160px] flex flex-col items-center justify-center py-6 select-none">
                  <img
                    src="/ui_assets/empty_state_reference_exact.png"
                    alt="Selecione um insumo"
                    className="max-h-[90px] object-contain mb-2.5 pointer-events-none"
                  />
                  <p className="text-[13px] font-medium text-[#687796] dark:text-[#93A4C6]">
                    Selecione um insumo acima para visualizar ou cadastrar conversões.
                  </p>
                </div>
              ) : displayedConversions.length === 0 ? (
                <div className="h-full min-h-[160px] flex flex-col items-center justify-center py-6 select-none">
                  <img
                    src="/ui_assets/empty_state_reference_exact.png"
                    alt="Sem conversões"
                    className="max-h-[90px] object-contain mb-2.5 pointer-events-none"
                  />
                  <p className="text-[13px] font-bold text-[#687796] dark:text-[#93A4C6] mb-0.5">
                    Nenhuma conversão cadastrada para este insumo.
                  </p>
                  <p className="text-[12px] text-[#8A99B5] dark:text-[#687796]">
                    Preencha os campos acima para cadastrar a primeira medida.
                  </p>
                </div>
              ) : (
                displayedConversions.map((c) => (
                  <div
                    key={c.id}
                    className="h-[36px] flex items-center text-[13px] text-[#18223A] dark:text-[#F4F7FF] px-1 hover:bg-[#F8FAFD] dark:hover:bg-[#142340] rounded-lg transition-colors"
                  >
                    {/* Left Cell: Medida */}
                    <div
                      style={{ width: `${nameColPct}%` }}
                      className="pl-3 pr-2 text-left font-medium truncate flex items-center"
                    >
                      <span className="font-bold text-[#F28C28] mr-2 shrink-0 text-[12px]">
                        1
                      </span>
                      <span className="truncate" title={c.name}>
                        {c.name}
                      </span>
                    </div>

                    {/* Subtle divider spacing */}
                    <div className="w-[10px] shrink-0" />

                    {/* Right Cell: Equivalência Real */}
                    <div
                      style={{ width: `${100 - nameColPct}%` }}
                      className="text-center font-semibold text-[#18223A] dark:text-[#F4F7FF] flex-1 px-2"
                    >
                      {c.factor_fmt}{' '}
                      <span className="font-normal text-[#60769D] dark:text-[#93A4C6]">
                        {c.base_unit}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

