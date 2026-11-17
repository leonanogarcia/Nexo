import React, { useEffect, useRef, useState } from 'react';
import { FeedbackType, RoundedActionButton, RoundedDropdown } from './DesignSystem';

interface DocumentItem {
  id: number;
  entity_type: string;
  entity_id: number;
  original_name: string;
  uploaded_at: string;
  ext: string;
  exists: boolean;
}

interface ViewerState {
  kind: 'image' | 'pdf' | 'text' | 'download_only';
  name: string;
  raw_url?: string;
  content?: string;
}

interface DocumentAttachmentsModalProps {
  open: boolean;
  entityType: 'RECIPE_BASE' | 'PRODUCT';
  entityId: number;
  entityName: string;
  onClose: () => void;
  onNotify: (msg: string, type?: FeedbackType) => void;
}

export const DocumentAttachmentsModal: React.FC<DocumentAttachmentsModalProps> = ({
  open,
  entityType,
  entityId,
  entityName,
  onClose,
  onNotify,
}) => {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [downloadFmt, setDownloadFmt] = useState<'Original' | 'PDF' | 'Word (.docx)' | 'JPG'>('Original');
  const [viewer, setViewer] = useState<ViewerState | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/documents/${entityType}/${entityId}`);
      if (!res.ok) throw new Error('Não foi possível listar os anexos.');
      const data = await res.json();
      setDocs(data.documents || []);
    } catch (e: any) {
      onNotify(e.message || 'Erro ao carregar anexos.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open && entityId) {
      setViewer(null);
      void loadDocs();
    }
  }, [open, entityType, entityId]);

  if (!open) return null;

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;

    setUploading(true);
    try {
      const dataUrl: string = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ''));
        reader.onerror = () => reject(new Error('Falha ao ler o arquivo.'));
        reader.readAsDataURL(file);
      });
      const res = await fetch(`/api/documents/${entityType}/${entityId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: file.name,
          data_base64: dataUrl,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Erro ao anexar documento.');
      onNotify(data.message || 'Documento anexado com sucesso!', 'success');
      await loadDocs();
    } catch (err: any) {
      onNotify(err.message || 'Erro ao enviar documento.', 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleOpenViewer = async (doc: DocumentItem) => {
    try {
      const res = await fetch(`/api/documents/file/${doc.id}/view`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Não foi possível abrir o documento.');
      setViewer(data);
    } catch (err: any) {
      onNotify(err.message || 'Erro ao abrir visualização.', 'error');
    }
  };

  const handleDownload = (doc: DocumentItem) => {
    const fmtMap: Record<string, string> = {
      Original: 'original',
      PDF: 'pdf',
      'Word (.docx)': 'docx',
      JPG: 'jpg',
    };
    const fmtCode = fmtMap[downloadFmt] || 'original';
    const stem = doc.original_name.replace(/\.[^/.]+$/, '') || 'documento';
    const targetName = fmtCode === 'original' ? doc.original_name : `${stem}.${fmtCode}`;
    const a = document.createElement('a');
    a.href = `/api/documents/file/${doc.id}/download?fmt=${fmtCode}`;
    a.download = targetName;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const handleDelete = async (doc: DocumentItem) => {
    try {
      const res = await fetch(`/api/documents/file/${doc.id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Não foi possível remover o anexo.');
      if (viewer?.name === doc.original_name) setViewer(null);
      onNotify('Anexo removido.', 'success');
      await loadDocs();
    } catch (err: any) {
      onNotify(err.message || 'Erro ao excluir anexo.', 'error');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#0B132B]/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="w-full max-w-4xl max-h-[88vh] rounded-[26px] bg-white dark:bg-[#111F3B] border border-[#E2EAF5] dark:border-[#24385E] shadow-2xl p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-[#F0F4FA] dark:border-[#1E3156] pb-3">
          <div>
            <h3 className="text-[16px] font-bold text-[#18223A] dark:text-[#F4F7FF]">
              Anexos & Viewer — {entityName}
            </h3>
            <p className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
              Anexe, baixe ou visualize receitas e fichas em PDF, Word (.docx), TXT ou imagem (independente da IA).
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center text-[#94A3B8] hover:text-[#18223A] dark:hover:text-white hover:bg-[#F1F5F9] dark:hover:bg-[#1E293B] cursor-pointer"
          >
            ✕
          </button>
        </div>

        <div className="flex items-center justify-between gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.webp"
            onChange={handleFileSelected}
            className="hidden"
          />
          <RoundedActionButton
            label={uploading ? 'Enviando...' : '+ Anexar Arquivo'}
            onClick={() => fileInputRef.current?.click()}
            variant="primary"
            height={34}
          />
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1.5">
              <span className="text-[11.5px] font-semibold text-[#60769D] dark:text-[#93A4C6]">
                Baixar como:
              </span>
              <RoundedDropdown
                value={downloadFmt}
                onChange={(v) => setDownloadFmt(v as any)}
                options={['Original', 'PDF', 'Word (.docx)', 'JPG']}
                width={135}
                height={30}
              />
            </div>
            <span className="text-[11.5px] text-[#60769D] dark:text-[#93A4C6]">
              {docs.length} arquivo(s) anexado(s)
            </span>
          </div>
        </div>

        <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-12 gap-4 overflow-hidden">
          {/* Lista de Anexos */}
          <div className="md:col-span-5 overflow-y-auto pr-1 space-y-2">
            {loading ? (
              <p className="text-[12.5px] text-[#60769D] py-4">Carregando anexos...</p>
            ) : docs.length === 0 ? (
              <div className="p-4 rounded-[16px] bg-[#F8FAFD] dark:bg-[#0E1B35] border border-[#E6EEF8] dark:border-[#1E3156] text-[12px] text-[#60769D] dark:text-[#93A4C6]">
                Nenhum documento anexado ainda. Clique em <strong>+ Anexar Arquivo</strong> acima.
              </div>
            ) : (
              docs.map((doc) => (
                <div
                  key={doc.id}
                  className="p-3 rounded-[16px] bg-[#F8FAFD] dark:bg-[#0E1B35] border border-[#E6EEF8] dark:border-[#1E3156] space-y-2"
                >
                  <div className="text-[12.5px] font-bold text-[#18223A] dark:text-[#F4F7FF] truncate" title={doc.original_name}>
                    {doc.original_name}
                  </div>
                  <div className="text-[10.5px] text-[#8C9BB5]">
                    {doc.uploaded_at.replace('T', ' ').slice(0, 16)}
                  </div>
                  <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                    <RoundedActionButton
                      label="Visualizar"
                      onClick={() => handleOpenViewer(doc)}
                      variant="primary"
                      height={28}
                    />
                    <RoundedActionButton
                      label="Baixar"
                      onClick={() => handleDownload(doc)}
                      variant="secondary"
                      height={28}
                    />
                    <button
                      type="button"
                      onClick={() => handleDelete(doc)}
                      className="px-2.5 h-[28px] rounded-full text-[11px] font-semibold text-[#DC2626] hover:bg-[#FEE2E2] dark:hover:bg-[#3F1518] transition-colors cursor-pointer"
                    >
                      Excluir
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Painel Viewer Integrado */}
          <div className="md:col-span-7 rounded-[18px] bg-[#F8FAFD] dark:bg-[#0E1B35] border border-[#E6EEF8] dark:border-[#1E3156] p-3 flex flex-col overflow-hidden min-h-[260px]">
            {!viewer ? (
              <div className="flex-1 flex items-center justify-center text-center text-[12.5px] text-[#60769D] dark:text-[#93A4C6] px-6">
                Selecione um anexo e clique em <strong>Visualizar</strong> para abrir o Viewer integrado.
              </div>
            ) : (
              <>
                <div className="text-[12px] font-bold text-[#18223A] dark:text-[#F4F7FF] pb-2 border-b border-[#E6EEF8] dark:border-[#1E3156] truncate">
                  {viewer.name}
                </div>
                <div className="flex-1 min-h-0 overflow-auto pt-2 flex items-center justify-center">
                  {viewer.kind === 'image' && viewer.raw_url && (
                    <img
                      src={viewer.raw_url}
                      alt={viewer.name}
                      className="max-w-full max-h-full object-contain rounded-[12px]"
                    />
                  )}
                  {viewer.kind === 'pdf' && viewer.raw_url && (
                    <iframe
                      src={viewer.raw_url}
                      title={viewer.name}
                      className="w-full h-full min-h-[340px] rounded-[12px] border-0 bg-white"
                    />
                  )}
                  {viewer.kind === 'text' && (
                    <pre className="w-full h-full overflow-auto whitespace-pre-wrap text-[12px] text-[#18223A] dark:text-[#F4F7FF] font-sans leading-relaxed p-2">
                      {viewer.content}
                    </pre>
                  )}
                  {viewer.kind === 'download_only' && (
                    <div className="text-[12.5px] text-[#60769D] text-center">
                      Este formato não possui prévia visual. Use o botão <strong>Baixar</strong>.
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        <div className="flex justify-end pt-1">
          <RoundedActionButton label="Fechar" onClick={onClose} variant="secondary" height={34} />
        </div>
      </div>
    </div>
  );
};
