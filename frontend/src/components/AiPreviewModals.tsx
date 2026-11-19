import React, { useEffect, useRef, useState } from 'react';
import {
  AlertTriangleIcon,
  CapsuleInput,
  FeedbackType,
  NexoCheckbox,
  RoundedActionButton,
  RoundedDropdown,
} from './DesignSystem';

export interface AiReceiptItem {
  temp_id: number;
  selected: boolean;
  name: string;
  brand: string;
  no_brand?: boolean;
  qty: number;
  unit: string;
  value: number;
  category: string;
  barcode: string;
  action: 'update' | 'create';
  matched_material_id: number | null;
  matched_material_name: string;
  reason?: string;
}

interface ExistingMaterialOption {
  id: number;
  name: string;
  brand?: string;
  purchase_qty?: number;
  purchase_unit: string;
  label: string;
}

const PLACEHOLDER_TEXTS = new Set([
  'teste', 'test', 'asdf', 'qwe', 'qwerty', 'nada', 'na', 'n/a',
  'nenhum', 'nenhuma', 'generico', 'sem', 'qualquer', 'abc', 'xyz',
]);

function checkQualityTextClient(val: string, label: string, isBrand = false, noBrand = false): string | null {
  if (isBrand && noBrand) return null;
  const trimmed = (val || '').trim();
  if (!trimmed) {
    return isBrand ? `${label} obrigatória (ou marque "Sem marca")` : `${label} obrigatório`;
  }
  const letters = trimmed.match(/[a-zA-ZÀ-ÿ]/g) || [];
  if (letters.length < 2) {
    return `${label} inválido (mínimo 2 letras)`;
  }
  const compact = trimmed.replace(/\s+/g, '').toLowerCase();
  if (new Set(compact).size <= 1) {
    return `${label} inválido (caracteres repetidos)`;
  }
  const canon = trimmed
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
  if (PLACEHOLDER_TEXTS.has(canon) || (isBrand && canon === 'sem marca' && !noBrand)) {
    return isBrand ? 'Use a caixinha "Sem marca" em vez de texto genérico' : `Não use texto genérico em ${label}`;
  }
  return null;
}

function getReceiptItemIssues(it: AiReceiptItem): string[] {
  const issues: string[] = [];
  if (it.action === 'create') {
    const nameErr = checkQualityTextClient(it.name, 'Nome');
    if (nameErr) issues.push(nameErr);
    const brandErr = checkQualityTextClient(it.brand, 'Marca', true, Boolean(it.no_brand));
    if (brandErr) issues.push(brandErr);
    if (!it.category?.trim()) issues.push('Categoria obrigatória');
  } else {
    if (!it.matched_material_id) issues.push('Selecione o insumo existente para atualizar');
    if (!it.reason?.trim()) issues.push('Informe o motivo da atualização');
  }
  if (!it.qty || Number(it.qty) <= 0) issues.push('Quantidade deve ser maior que zero');
  if (!it.unit?.trim()) issues.push('Unidade obrigatória');
  if (Number(it.value) < 0 || (Number(it.value) === 0 && it.category !== 'Doação')) {
    issues.push('Valor obrigatório (maior que zero)');
  }
  return issues;
}

interface AiReceiptPreviewModalProps {
  open: boolean;
  units: string[];
  onClose: () => void;
  onApplied: () => void;
  onNotify: (msg: string, type?: FeedbackType) => void;
}

export const AiReceiptPreviewModal: React.FC<AiReceiptPreviewModalProps> = ({
  open,
  units,
  onClose,
  onApplied,
  onNotify,
}) => {
  const fileRef = useRef<HTMLInputElement>(null);
  const [parsing, setParsing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [purchaseDate, setPurchaseDate] = useState(new Date().toISOString().slice(0, 10));
  const [items, setItems] = useState<AiReceiptItem[]>([]);
  const [previewImg, setPreviewImg] = useState<string>('');
  const [selectedFileName, setSelectedFileName] = useState('');
  const [lastFile, setLastFile] = useState<File | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [existingMats, setExistingMats] = useState<ExistingMaterialOption[]>([]);

  useEffect(() => {
    if (!open) return;
    (async () => {
      try {
        const res = await fetch('/api/materials/options');
        if (res.ok) {
          const data = await res.json();
          setExistingMats(Array.isArray(data.items) ? data.items : []);
        }
      } catch (e) {
        console.error(e);
      }
    })();
  }, [open]);

  if (!open) return null;

  const processReceiptFile = async (file: File) => {
    setLastFile(file);
    setSelectedFileName(file.name);
    setErrorMsg('');
    setParsing(true);
    try {
      const dataUrl: string = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ''));
        reader.onerror = () => reject(new Error('Falha ao ler a imagem.'));
        reader.readAsDataURL(file);
      });
      setPreviewImg(dataUrl);
      const res = await fetch('/api/ai/parse-receipt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: file.name,
          mime_type: file.type || 'image/jpeg',
          data_base64: dataUrl,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Não foi possível ler a notinha com IA.');
      setPurchaseDate(data.purchase_date || new Date().toISOString().slice(0, 10));
      setItems(Array.isArray(data.items) ? data.items : []);
      if (!data.items?.length) {
        const msg = 'A IA não encontrou itens legíveis nessa imagem.';
        setErrorMsg(msg);
        onNotify(msg, 'warning');
      }
    } catch (err: any) {
      const msg = err?.message || 'Erro ao interpretar notinha.';
      setErrorMsg(msg);
      onNotify(msg, 'error');
    } finally {
      setParsing(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    await processReceiptFile(file);
  };

  const updateItem = (tempId: number, patch: Partial<AiReceiptItem>) => {
    setItems((prev) => prev.map((it) => (it.temp_id === tempId ? { ...it, ...patch } : it)));
  };

  const handleConfirmApply = async () => {
    setErrorMsg('');
    const chosen = items.filter((i) => i.selected);
    if (!chosen.length) {
      const msg = 'Selecione ao menos um item para aplicar.';
      setErrorMsg(msg);
      onNotify(msg, 'warning');
      return;
    }

    for (const it of chosen) {
      const issues = getReceiptItemIssues(it);
      if (issues.length > 0) {
        const msg = `Revise "${it.name || 'Item sem nome'}": ${issues[0]}.`;
        setErrorMsg(msg);
        onNotify(msg, 'warning');
        return;
      }
    }

    setApplying(true);
    try {
      const res = await fetch('/api/ai/apply-receipt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          purchase_date: purchaseDate,
          items: chosen.map((it) => ({
            name: it.name,
            brand: it.no_brand ? 'Sem marca' : it.brand,
            no_brand: Boolean(it.no_brand),
            qty: Number(it.qty) || 1,
            unit: it.unit,
            value: Number(it.value) || 0,
            category: it.category,
            barcode: it.barcode,
            action: it.action,
            matched_material_id: it.matched_material_id,
            reason: it.reason || 'Compra via Notinha (IA)',
          })),
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Erro ao salvar itens da notinha.');
      onNotify(data.message || 'Notinha aplicada com sucesso!', 'success');
      setItems([]);
      setPreviewImg('');
      setSelectedFileName('');
      setLastFile(null);
      setErrorMsg('');
      onApplied();
      onClose();
    } catch (err: any) {
      const msg = err?.message || 'Erro ao aplicar notinha.';
      setErrorMsg(msg);
      onNotify(msg, 'error');
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#0B132B]/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-5xl max-h-[90vh] rounded-[26px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-3">
          <div>
            <h3 className="text-[16px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              Ler Notinha / Cupom Fiscal (IA) — Pré-visualização
            </h3>
            <p className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
              Envie a foto da notinha, confira ou edite os itens extraídos e só então confirme para gravar no banco.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center text-[#94A3B8] hover:text-[#18223A] dark:hover:text-white cursor-pointer"
          >
            ✕
          </button>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 flex-wrap">
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
            />
            <RoundedActionButton
              label={parsing ? 'Lendo com IA...' : previewImg ? 'Trocar Foto da Notinha' : 'Selecionar Foto da Notinha'}
              onClick={() => fileRef.current?.click()}
              variant="primary"
              height={34}
            />
            {selectedFileName && (
              <span className="text-[12px] font-medium text-[#475978] dark:text-[#AFC0E2]">
                Arquivo: <strong className="text-[#18223A] dark:text-[#F4F7FF]">{selectedFileName}</strong>
              </span>
            )}
            {lastFile && !parsing && (
              <RoundedActionButton
                label="↻ Tentar novamente"
                onClick={() => processReceiptFile(lastFile)}
                variant="secondary"
                height={34}
              />
            )}
            <div className="flex items-center gap-2">
              <span className="text-[12px] font-semibold text-[#60769D] dark:text-[#93A4C6]">Data da compra:</span>
              <div className="w-[140px]">
                <CapsuleInput type="date" value={purchaseDate} onChange={setPurchaseDate} />
              </div>
            </div>
          </div>

          <span className="text-[12px] text-[#60769D] dark:text-[#93A4C6]">
            {items.filter((i) => i.selected).length} de {items.length} selecionado(s)
          </span>
        </div>

        {errorMsg && (
          <div className="rounded-[14px] bg-[#FEF2F2] dark:bg-[#3A1619] border border-[#FECACA] dark:border-[#7F1D1D] px-3.5 py-2.5 text-[12px] font-semibold text-[#B91C1C] dark:text-[#FCA5A5]">
            {errorMsg}
          </div>
        )}

        <div className="flex-1 min-h-0 overflow-auto rounded-[18px] bg-[#F8FAFD] dark:bg-[#0E1B35] border border-[#E6EEF8] dark:border-[#1E3156] p-3 space-y-2.5">
          {parsing ? (
            <div className="py-12 text-center text-[13px] font-semibold text-[#BA5200] dark:text-[#F28C28]">
              Analisando a foto da notinha com inteligência artificial...
            </div>
          ) : items.length === 0 ? (
            <div className="py-12 text-center text-[12.5px] text-[#60769D] dark:text-[#93A4C6]">
              Clique em <strong>Selecionar Foto da Notinha</strong> para gerar a pré-visualização dos itens.
            </div>
          ) : (
            items.map((it) => {
              const issues = it.selected ? getReceiptItemIssues(it) : [];
              const hasIssues = issues.length > 0;
              const matchedOpt = existingMats.find((m) => m.id === it.matched_material_id);

              return (
                <div
                  key={it.temp_id}
                  className={`p-3 rounded-[16px] border space-y-2.5 ${
                    !it.selected
                      ? 'opacity-55 bg-white/70 dark:bg-[#111F3B]/70 border-[#E2EAF5] dark:border-[#24385E]'
                      : hasIssues
                      ? 'bg-[#FFFBEB] dark:bg-[#2A1F0D] border-[#F59E0B] dark:border-[#B45309]'
                      : 'bg-white dark:bg-[#111F3B] border-[#E2EAF5] dark:border-[#24385E]'
                  }`}
                >
                  {/* Linha 1: Checkbox, Nome, Marca + Sem marca, Ação */}
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-2 items-center">
                    <div className="md:col-span-1 flex items-center justify-center">
                      <NexoCheckbox
                        checked={it.selected}
                        onChange={() => updateItem(it.temp_id, { selected: !it.selected })}
                      />
                    </div>
                    <div className="md:col-span-4">
                      <CapsuleInput
                        value={it.name}
                        onChange={(v) => updateItem(it.temp_id, { name: v })}
                        placeholder="Nome do insumo *"
                      />
                    </div>
                    <div className="md:col-span-4 flex items-center gap-2">
                      <div className="flex-1 min-w-0">
                        <CapsuleInput
                          value={it.no_brand ? 'Sem marca' : it.brand}
                          onChange={(v) => updateItem(it.temp_id, { brand: v, no_brand: false })}
                          placeholder="Marca *"
                          disabled={Boolean(it.no_brand)}
                        />
                      </div>
                      <label className="flex items-center gap-1.5 text-[11px] font-semibold text-[#60769D] dark:text-[#AFC0E2] cursor-pointer shrink-0 select-none">
                        <NexoCheckbox
                          checked={Boolean(it.no_brand)}
                          onChange={() =>
                            updateItem(it.temp_id, {
                              no_brand: !it.no_brand,
                              brand: !it.no_brand ? 'Sem marca' : '',
                            })
                          }
                        />
                        <span>Sem marca</span>
                      </label>
                    </div>
                    <div className="md:col-span-3">
                      <RoundedDropdown
                        value={it.action === 'update' ? 'Atualizar existente' : 'Criar novo'}
                        onChange={(lbl) =>
                          updateItem(it.temp_id, {
                            action: lbl === 'Atualizar existente' ? 'update' : 'create',
                            reason: it.reason || 'Compra via Notinha (IA)',
                          })
                        }
                        options={['Atualizar existente', 'Criar novo']}
                        width="100%"
                        height={32}
                      />
                    </div>
                  </div>

                  {/* Linha 2: Categoria, Qtd, Unidade, Valor e Vínculo/Motivo ou Status */}
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-2 items-center md:pl-10">
                    <div className="md:col-span-2">
                      <RoundedDropdown
                        value={it.category || 'Comestível'}
                        onChange={(cat) => updateItem(it.temp_id, { category: cat })}
                        options={['Comestível', 'Não comestível', 'Embalagem', 'Doação']}
                        width="100%"
                        height={32}
                      />
                    </div>
                    <div className="md:col-span-1">
                      <CapsuleInput
                        type="numeric"
                        value={String(it.qty)}
                        onChange={(v) => updateItem(it.temp_id, { qty: parseFloat(v.replace(',', '.')) || 0 })}
                        placeholder="Qtd"
                      />
                    </div>
                    <div className="md:col-span-1">
                      <RoundedDropdown
                        value={it.unit}
                        onChange={(u) => updateItem(it.temp_id, { unit: u })}
                        options={units.length ? units : ['un', 'g', 'kg', 'ml', 'L']}
                        width="100%"
                        height={32}
                      />
                    </div>
                    <div className="md:col-span-2">
                      <CapsuleInput
                        type="numeric"
                        value={String(it.value).replace('.', ',')}
                        onChange={(v) => updateItem(it.temp_id, { value: parseFloat(v.replace(',', '.')) || 0 })}
                        placeholder="Valor R$ *"
                      />
                    </div>

                    {it.action === 'update' ? (
                      <>
                        <div className="md:col-span-3">
                          <RoundedDropdown
                            value={matchedOpt ? matchedOpt.label : ''}
                            onChange={(lbl) => {
                              const found = existingMats.find((m) => m.label === lbl);
                              if (found) {
                                updateItem(it.temp_id, {
                                  matched_material_id: found.id,
                                  matched_material_name: found.name,
                                });
                              }
                            }}
                            options={existingMats.map((m) => m.label)}
                            width="100%"
                            height={32}
                            placeholder="Vincular insumo existente..."
                          />
                        </div>
                        <div className="md:col-span-3">
                          <RoundedDropdown
                            value={it.reason || 'Compra via Notinha (IA)'}
                            onChange={(r) => updateItem(it.temp_id, { reason: r })}
                            options={[
                              'Compra via Notinha (IA)',
                              'Reajuste de preço',
                              'Promoção / Desconto',
                              'Compra recorrente',
                            ]}
                            width="100%"
                            height={32}
                          />
                        </div>
                      </>
                    ) : (
                      <div className="md:col-span-6 flex items-center justify-end">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold ${
                            hasIssues
                              ? 'bg-[#FEF3C7] dark:bg-[#3B2A0F] text-[#B45309] dark:text-[#FBBF24]'
                              : 'bg-[#EBFBF0] dark:bg-[#133020] text-[#16A34A] dark:text-[#4ADE80]'
                          }`}
                        >
                          {hasIssues ? (
                            <>
                              <AlertTriangleIcon className="w-3.5 h-3.5 shrink-0" />
                              <span>{issues[0]}</span>
                            </>
                          ) : (
                            '✓ Pronto para criar novo insumo'
                          )}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="flex items-center justify-end gap-2 pt-1">
          <RoundedActionButton label="Cancelar" onClick={onClose} variant="secondary" height={34} />
          <RoundedActionButton
            label={applying ? 'Aplicando...' : 'Confirmar e Aplicar'}
            onClick={handleConfirmApply}
            disabled={applying}
            variant="primary"
            height={34}
          />
        </div>
      </div>
    </div>
  );
};

export interface AiParsedIngredient {
  temp_id: number;
  selected: boolean;
  name: string;
  qty: number;
  unit: string;
  item_type: 'MATERIAL' | 'RECIPE_BASE';
  matched_id: number | null;
  matched_name: string;
}

export interface AiParsedRecipeResult {
  name: string;
  yield_qty: number;
  yield_unit: string;
  notes: string;
  ingredients: AiParsedIngredient[];
  source_file?: {
    filename: string;
    mime_type: string;
    data_base64: string;
  };
}

interface AiRecipePreviewModalProps {
  open: boolean;
  targetKind: 'recipe' | 'product';
  onClose: () => void;
  onApplyToForm: (data: AiParsedRecipeResult) => void;
  onNotify: (msg: string, type?: FeedbackType) => void;
}

export const AiRecipePreviewModal: React.FC<AiRecipePreviewModalProps> = ({
  open,
  targetKind,
  onClose,
  onApplyToForm,
  onNotify,
}) => {
  const fileRef = useRef<HTMLInputElement>(null);
  const [parsing, setParsing] = useState(false);
  const [parsed, setParsed] = useState<AiParsedRecipeResult | null>(null);
  const [selectedFileName, setSelectedFileName] = useState('');
  const [lastFile, setLastFile] = useState<File | null>(null);
  const [sourceFile, setSourceFile] = useState<{ filename: string; mime_type: string; data_base64: string } | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  if (!open) return null;

  const handleClose = () => {
    setErrorMsg('');
    onClose();
  };

  const processFile = async (file: File) => {
    setLastFile(file);
    setSelectedFileName(file.name);
    setErrorMsg('');
    setParsing(true);
    try {
      const dataUrl: string = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ''));
        reader.onerror = () => reject(new Error('Falha ao ler arquivo.'));
        reader.readAsDataURL(file);
      });
      setSourceFile({
        filename: file.name,
        mime_type: file.type || 'application/octet-stream',
        data_base64: dataUrl,
      });
      const res = await fetch('/api/ai/parse-recipe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_kind: targetKind,
          filename: file.name,
          mime_type: file.type || 'image/jpeg',
          data_base64: dataUrl,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Não foi possível ler o arquivo com IA.');
      setParsed(data);
    } catch (err: any) {
      const msg = err?.message || 'Erro ao interpretar receita com IA.';
      setErrorMsg(msg);
      onNotify(msg, 'error');
    } finally {
      setParsing(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    await processFile(file);
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#0B132B]/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-3xl max-h-[88vh] rounded-[26px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-3">
          <div>
            <h3 className="text-[16px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              {targetKind === 'recipe' ? 'Ler Receita com IA — Pré-visualização' : 'Ler Ficha / Montagem com IA — Pré-visualização'}
            </h3>
            <p className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
              Envie foto, PDF, Word (.docx) ou TXT. Confira os dados extraídos antes de preencher a ficha.
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="w-8 h-8 rounded-full flex items-center justify-center text-[#94A3B8] hover:text-[#18223A] dark:hover:text-white cursor-pointer"
          >
            ✕
          </button>
        </div>

        <div className="flex items-center justify-between gap-3 flex-wrap">
          <input
            ref={fileRef}
            type="file"
            accept="image/*,.pdf,.docx,.txt"
            onChange={handleFileChange}
            className="hidden"
          />
          <div className="flex items-center gap-3 flex-wrap">
            <RoundedActionButton
              label={parsing ? 'Analisando com IA...' : 'Selecionar Foto ou Documento'}
              onClick={() => fileRef.current?.click()}
              variant="primary"
              height={34}
            />
            {selectedFileName && (
              <span className="text-[12px] font-medium text-[#475978] dark:text-[#AFC0E2]">
                Arquivo: <strong className="text-[#18223A] dark:text-[#F4F7FF]">{selectedFileName}</strong>
              </span>
            )}
            {lastFile && !parsing && (
              <RoundedActionButton
                label="↻ Tentar novamente"
                onClick={() => processFile(lastFile)}
                variant="secondary"
                height={34}
              />
            )}
          </div>
        </div>

        {errorMsg && (
          <div className="rounded-[14px] bg-[#FEF2F2] dark:bg-[#3A1619] border border-[#FECACA] dark:border-[#7F1D1D] px-3.5 py-2.5 text-[12px] font-semibold text-[#B91C1C] dark:text-[#FCA5A5]">
            {errorMsg}
          </div>
        )}

        <div className="flex-1 min-h-0 overflow-y-auto rounded-[18px] bg-[#F8FAFD] dark:bg-[#0E1B35] border border-[#E6EEF8] dark:border-[#1E3156] p-4 space-y-3">
          {parsing ? (
            <div className="py-10 text-center text-[13px] font-semibold text-[#BA5200] dark:text-[#F28C28]">
              Extraindo ingredientes e rendimento com IA...
            </div>
          ) : !parsed ? (
            <div className="py-10 text-center text-[12.5px] text-[#60769D] dark:text-[#93A4C6]">
              Selecione uma foto ou documento para visualizar o resultado antes de aplicar.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-2">
                  <label className="block text-[11px] font-semibold text-[#60769D] mb-1">Nome identificado</label>
                  <CapsuleInput
                    value={parsed.name}
                    onChange={(v) => setParsed({ ...parsed, name: v })}
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#60769D] mb-1">Rendimento ({parsed.yield_unit})</label>
                  <CapsuleInput
                    type="numeric"
                    value={String(parsed.yield_qty)}
                    onChange={(v) => setParsed({ ...parsed, yield_qty: parseFloat(v.replace(',', '.')) || 1 })}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="text-[11.5px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
                  Ingredientes / Componentes ({parsed.ingredients.length})
                </div>
                {parsed.ingredients.map((ing) => (
                  <div
                    key={ing.temp_id}
                    className="flex items-center justify-between gap-2 p-2.5 rounded-[14px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] text-[12px]"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <NexoCheckbox
                        checked={ing.selected}
                        onChange={() =>
                          setParsed({
                            ...parsed,
                            ingredients: parsed.ingredients.map((x) =>
                              x.temp_id === ing.temp_id ? { ...x, selected: !x.selected } : x
                            ),
                          })
                        }
                      />
                      <span
                        title={`${ing.name} — ${ing.qty} ${ing.unit}`}
                        className="font-semibold text-[#18223A] dark:text-[#F4F7FF] truncate"
                      >
                        {ing.name} — {ing.qty} {ing.unit}
                      </span>
                    </div>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10.5px] font-bold shrink-0 ${ing.matched_id
                        ? 'bg-[#EBFBF0] dark:bg-[#133020] text-[#16A34A] dark:text-[#4ADE80]'
                        : 'bg-[#FEF3C7] dark:bg-[#3B2A0F] text-[#D97706] dark:text-[#FBBF24]'
                        }`}
                    >
                      {ing.matched_id ? `Vinculado: ${ing.matched_name}` : 'Não encontrado no cadastro'}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <RoundedActionButton label="Cancelar" onClick={handleClose} variant="secondary" height={34} />
          <RoundedActionButton
            label="Aplicar na Ficha"
            onClick={() => {
              if (!parsed) {
                const msg = 'Envie um arquivo primeiro.';
                setErrorMsg(msg);
                onNotify(msg, 'warning');
                return;
              }
              onApplyToForm({
                ...parsed,
                source_file: sourceFile || undefined,
              });
              setParsed(null);
              setSelectedFileName('');
              setSourceFile(null);
              setErrorMsg('');
              onClose();
            }}
            variant="primary"
            height={34}
          />
        </div>
      </div>
    </div>
  );
};

interface QuickCreateMaterialModalProps {
  open: boolean;
  initialName: string;
  initialUnit?: string;
  onClose: () => void;
  onCreated: (materialId: number, materialName: string) => void;
  onNotify: (msg: string, type?: FeedbackType) => void;
}

export const QuickCreateMaterialModal: React.FC<QuickCreateMaterialModalProps> = ({
  open,
  initialName,
  initialUnit,
  onClose,
  onCreated,
  onNotify,
}) => {
  const [name, setName] = useState(initialName || '');
  const [brand, setBrand] = useState('');
  const [category, setCategory] = useState('Comestível');
  const [qty, setQty] = useState('1');
  const [unit, setUnit] = useState('un');
  const [value, setValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (!open) return;
    setName(initialName || '');
    setBrand('');
    setCategory('Comestível');
    setQty('1');
    const u = (initialUnit || '').trim();
    const validUnits = ['mg', 'g', 'kg', 't', 'ml', 'L', 'kL', 'un'];
    setUnit(validUnits.includes(u) ? (u === 'g' ? 'kg' : u === 'ml' ? 'L' : u) : 'un');
    setValue('');
    setErr('');
  }, [open, initialName, initialUnit]);

  if (!open) return null;

  const handleSave = async () => {
    setErr('');
    const n = name.trim();
    if (!n) {
      setErr('Informe o nome do insumo.');
      return;
    }
    const q = parseFloat(qty.replace(',', '.'));
    if (isNaN(q) || q <= 0) {
      setErr('Informe uma quantidade comprada maior que zero.');
      return;
    }
    const valNum = parseFloat(value.replace(',', '.'));
    if (category !== 'Doação' && (isNaN(valNum) || valNum <= 0)) {
      setErr('Informe o valor da compra (maior que zero).');
      return;
    }

    setSaving(true);
    try {
      const res = await fetch('/api/materials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: n,
          brand: brand.trim(),
          category,
          qty: q,
          unit,
          value: category === 'Doação' && (isNaN(valNum) || valNum < 0) ? 0 : valNum,
          purchase_date: new Date().toISOString().slice(0, 10),
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.id) {
        throw new Error(data.detail || 'Não foi possível criar o insumo.');
      }
      onNotify(`Insumo "${n}" criado e vinculado!`, 'success');
      onCreated(Number(data.id), n);
      onClose();
    } catch (e: any) {
      setErr(e?.message || 'Erro ao salvar insumo.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] bg-[#0B132B]/65 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-[22px] bg-white dark:bg-[#111F3B] border border-[#DDE5F2] dark:border-[#24385E] shadow-2xl p-5 space-y-3.5">
        <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-2.5">
          <div>
            <h3 className="text-[15px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              Criar Insumo Rápido
            </h3>
            <p className="text-[11px] text-[#60769D] dark:text-[#93A4C6]">
              Cadastre o insumo faltante sem perder a ficha que você está montando.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center text-[#94A3B8] hover:text-[#18223A] dark:hover:text-white cursor-pointer"
          >
            ✕
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-[11px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
              Nome do insumo
            </label>
            <CapsuleInput value={name} onChange={setName} placeholder="Ex: Leite Condensado" />
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <div>
              <label className="block text-[11px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                Categoria
              </label>
              <RoundedDropdown
                value={category}
                onChange={setCategory}
                options={['Comestível', 'Não comestível', 'Embalagem', 'Doação']}
                width="100%"
                height={36}
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                Marca (opcional)
              </label>
              <CapsuleInput value={brand} onChange={setBrand} placeholder="Ex: Moça" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2.5">
            <div>
              <label className="block text-[11px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                Qtd compra
              </label>
              <CapsuleInput type="numeric" value={qty} onChange={setQty} placeholder="1" />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                Unidade
              </label>
              <RoundedDropdown
                value={unit}
                onChange={setUnit}
                options={['mg', 'g', 'kg', 't', 'ml', 'L', 'kL', 'un']}
                width="100%"
                height={36}
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-[#60769D] dark:text-[#93A4C6] mb-1 pl-1">
                Valor (R$)
              </label>
              <CapsuleInput type="money" value={value} onChange={setValue} placeholder="0,00" />
            </div>
          </div>
        </div>

        {err && (
          <div className="rounded-[12px] bg-[#FEF2F2] dark:bg-[#3A1619] border border-[#FECACA] dark:border-[#7F1D1D] px-3 py-2 text-[11.5px] font-semibold text-[#B91C1C] dark:text-[#FCA5A5]">
            {err}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-1">
          <RoundedActionButton label="Cancelar" onClick={onClose} variant="secondary" height={34} />
          <RoundedActionButton
            label={saving ? 'Salvando...' : 'Criar e Vincular'}
            onClick={handleSave}
            disabled={saving}
            variant="primary"
            height={34}
          />
        </div>
      </div>
    </div>
  );
};
