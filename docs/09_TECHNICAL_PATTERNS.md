# 09. Technical Patterns & UX Rules

Este arquivo documenta as diretrizes técnicas absolutas descobertas durante a evolução do Nexo. A Inteligência Artificial deve checar essas regras para evitar a reintrodução de bugs estruturais (regressão).

## 1. Banco de Dados e SQLite (Persistência)
Sempre que realizar operações de modificação no banco de dados (`INSERT`, `UPDATE` ou cláusulas `ON CONFLICT`) utilizando o SQLite em Python, é **obrigatório** chamar o comando `c.commit()` explicitamente antes de fechar a conexão.
- **Motivo:** O ambiente atual descarta operações executadas apenas em memória na hora em que o aplicativo é reiniciado, causando perda silenciosa de configurações.

## 2. IA e APIs Externas (Modo Resiliência)
Nunca dependa de uma única versão fixa de modelo da IA (ex: `gemini-1.5-flash`). Modelos fixos são frequentemente descontinuados e servidores gratuitos sofrem gargalos severos de processamento (Erro 503), principalmente em tarefas pesadas como Visão Computacional.
- **Padrão:** Utilize sempre apelidos auto-atualizáveis (`gemini-flash-latest`, `gemini-flash-lite-latest`) e implemente uma lógica de **fallback em cascata** com múltiplas tentativas. Se um modelo pesado falhar, o código deve silenciosamente tentar um modelo mais leve antes de devolver o erro à interface.

## 3. Comportamento de Janelas e Menus Tkinter (Fim dos Fantasmas)
O uso indiscriminado da propriedade `attributes('-topmost', True)` deve ser evitado a todo custo, pois força as janelas do Nexo a ficarem sobrepostas a outros aplicativos do Sistema Operacional (ex: navegadores).
- **Janelas Secundárias Comuns:** Para telas de visualização e formulários com barra de título normal, utilize sempre `transient(parent)`. Isso garante que a janela minimize junto com o Nexo e obedeça ao foco do Windows.
- **Menus Personalizados (overrideredirect):** Janelas que removem as bordas nativas exigem o uso do `-topmost` no Windows para funcionarem e não afundarem. No entanto, é **obrigatório** implementar um evento de destruição (`destroy()`) da janela atrelado a cliques externos. 
  - **A Armadilha do Foco (Tkinter Focus Trap):** NUNCA vincule o evento `<FocusOut>` à Janela Principal (`root.bind('<FocusOut>')`) para tentar fechar menus. Qualquer clique em um botão interno troca o foco e faz a Janela Principal disparar o evento instantaneamente, destruindo o menu antes mesmo dele aparecer. O evento de `<FocusOut>` só pode ser atrelado ao próprio menu, ou deve-se usar um rastreador de cliques (`<Button-1>`) fora das coordenadas do menu.

## 4. Filtros de Entrada em Arquivos (Prevenção > Tratamento)
A validação de formatos suportados pelo sistema não deve ocorrer apenas "depois" do carregamento para tentar tratar o erro no Python. 
- **Padrão:** Sempre que o sistema solicitar o anexo de um arquivo (via `filedialog.askopenfilename`), o parâmetro `filetypes` deve restringir as opções *estritamente* aos formatos suportados por aquela função (ex: permitir apenas Imagens e PDFs para o importador da receita). Isso oculta arquivos indesejados da visão do usuário e previne quebra de sistema.


---

## Padrões Técnicos Consolidados na v1.9.0

### 1. Arquitetura Modular Backend (`backend/routes/`) & Frontend (`React.lazy`)
- O monolito antigo `backend/api.py` foi dividido em routers por domínio usando `APIRouter`:
  - `backend/api.py`: entrypoint (FastAPI, CORS, `storage_guard_middleware`, assets/dist e `include_router`).
  - `backend/routes/common.py`: helpers compartilhados (`get_database_health`, validação de qualidade/duplicado, payloads base) exportados explicitamente via `__all__` (obrigatório para nomes com `_`).
  - `backend/routes/settings.py`, `materials.py`, `recipes.py`, `products.py`, `home_bi.py`, `documents_ai.py`.
- No frontend (`App.tsx`), as páginas principais (`HomePage`, `MaterialsPage`, `RecipesPage`, `ProductsPage`, `SettingsPage`) carregam sob demanda com `React.lazy` + `Suspense`, mantendo os chunks abaixo de 200 kB.

### 2. Conexão HTTP Externa de IA (`backend/ai_vision.py`)
- Requisições para provedores OpenAI-compatíveis/OpenRouter usam `ssl.create_default_context()`, `"Accept": "application/json"` e `"Connection": "close"`, tratando tanto `HTTPError` quanto `(URLError, TimeoutError, OSError)` como `RuntimeError` para acionar fallback limpo no modo gratuito.

### 3. Download Multi-Formato no Anexos & Viewer (`GET /api/documents/file/{doc_id}/download?fmt=...`)
- Suporta `fmt=original|pdf|docx|jpg`:
  - `pdf`: gerado via `reportlab` (com transcrição por IA via `transcribe_image_to_text` quando foto + IA ativa, ou imagem/texto direto).
  - `docx`: gerado via `python-docx` (parágrafos editáveis + imagem embutida quando aplicável).
  - `jpg`: gerado/convertido via `Pillow` (card limpo 1080px para documentos de texto ou conversão RGB para imagens, pronto para WhatsApp).

### 4. Higiene de IA e UX de Modais
- Modais de IA (`AiReceiptPreviewModal` e `AiRecipePreviewModal`) devem sempre manter: nome do arquivo selecionado, botão **`↻ Tentar novamente`** (`lastFile`) e faixa de erro inline visível dentro do modal.
- `tsc --noUnusedLocals --noEmit` deve sempre sair com código `0` (zero imports/estados mortos).
