# Contexto e Plano de Arquitetura — Nexo v2.0

> **Instrução para o Assistente na nova conversa:**
> Leia este arquivo e os documentos da pasta `docs/` (`01_CORE_DIRECTIVES.md` a `09_TECHNICAL_PATTERNS.md`) antes de iniciar qualquer implementação.
> **Regra de ouro de interação:** Sempre que o usuário (Leonan) disser *"só conversar"* ou *"ainda só conversando"*, **não altere nenhum arquivo** — apenas discuta, tire dúvidas e alinhe a solução até ele autorizar explicitamente (*"pode fazer"*).

---

## 1. Onde Estamos (Fechamento da v1.0.0)

- A versão **v1.0.0** foi finalizada, testada, empacotada para Windows 64-bits (`Nexo_Setup_v1.0.0_x64.exe` + `Uninstall_Nexo.exe`) e congelada na branch **`main`** (pasta `D:\Nexo\Nexo - 1.0`).
- Esta pasta (**`D:\Nexo\Nexo - 2.0`**) está na branch paralela **`v2.0`** (`origin/v2.0` no GitHub) para o desenvolvimento da **Versão 2.0** sem afetar a versão 1.0 estável.
- Na transição para a v1.0.0, o antigo `main.py` monolítico já foi pré-organizado em duas pastas:
  - `backend/`:
    - `paths.py`: Resolve diretórios do Windows. Quando instalado em `C:\Program Files\Nexo`, grava automaticamente o banco (`nexo.db`), configurações (`nexo_config.json`), documentos e backups diários em **`%LOCALAPPDATA%\Nexo`** para funcionar em qualquer conta de usuário **sem precisar de acesso Administrador**.
    - `database.py`: Conexão SQLite, criação de tabelas, migrações automáticas (incluindo `barcode` em `materials`), códigos sequenciais (`INS_`, `RB_`, `PROD_`) e triggers de auditoria.
    - `units.py`: Conversor de unidades (`mg/g/kg/t`, `ml/L/kL`, `un`) e equivalências customizadas por insumo.
    - `calculator.py`: Fórmulas de custo de insumos, receitas base em cascata, rateio de custos operacionais (Gás, Energia, Água), custo unitário de produtos e snapshot de evolução de custos.
    - `document_importer.py`: Leitura e anexos de documentos Word/PDF.
  - `frontend/`: Interface atual em Tkinter seguindo o Padrão Visual Nexo (`components.py`, `app.py` e `pages/`).

---

## 2. Objetivo Central do Nexo v2.0: Separação Real entre Front-end e Back-end

O foco da **v2.0** é transformar o Nexo em uma aplicação com **Back-end e Front-end totalmente desacoplados**:

1. **Back-end (Python API / Serviços):**
   - Manter toda a inteligência de negócio, banco SQLite (`%LOCALAPPDATA%\Nexo`), cálculos de ficha técnica e conversões em Python.
   - Expor essas operações através de uma camada de serviços/API limpa (ex.: **FastAPI** local ou ponte estruturada JSON) para que tanto o Desktop quanto futuros aplicativos possam consumir os mesmos dados e regras.
2. **Novo Front-end Moderno (Desktop Windows instalável, preparado para Web/SaaS no futuro):**
   - Tecnologia discutida e recomendada: **TypeScript + React + Tailwind CSS** (empacotado para Desktop Windows via WebView2 / Tauri / Electron).
   - **Por que essa escolha:**
     - Permite construir o **Design System Nexo em formato Cápsula** (`border-radius: 9999px`, sombras suaves, transições de hover `#BA5200`, tabelas arredondadas, modo Claro/Escuro e gráficos de rosca interativos de BI) de forma nativa, fluida e com nitidez perfeita em qualquer resolução.
     - Prepara o terreno para que o mesmo Front-end possa rodar na nuvem (Web) no futuro sem precisar ser reescrito.

---

## 3. Decisões de Produto e Interface Já Alinhadas (Manter na v2.0)

1. **Aba Início (`home_page`) e BI:**
   - **3 Cards de KPI no topo (sem ícones circulares):** `Produtos`, `Receitas base` e `Insumos` (clicáveis, levando para a respectiva aba).
   - **Sem card de Embalagens:** Itens como fitas, caixas e etiquetas entram no Cadastro de Insumos como **Não Comestíveis (Acabamento)**, compondo o custo direto do produto sem poluir a tela inicial com um mostrador de estoque de embalagens.
   - **Gráficos de Pizza/Rosca no resumo da aba Início:**
     - Card 1: *Distribuição de compras por insumo* + botão cápsula **"Ver detalhes"**.
     - Card 2: *Composição de custos (Receitas e Produtos)* + botão cápsula **"Ver detalhes"**.
   - **Janela Modal de BI:** As tabelas comparativas detalhadas (*Por Insumo*, *Por Marca* e *Receitas e Produtos*) ficam exclusivamente dentro do Modal de BI (aberto pelos botões *"Ver detalhes"*), com busca em cápsula, filtro de mês e cabeçalho Nexo ordenável.
2. **Design System Nexo (`docs/`):**
   - Zero cantos vivos/quadrados em inputs, botões, dropdowns, toggles e cabeçalhos de tabela.
   - Na barra lateral (`ReferenceSidebar`), no Modo Escuro (onde a cápsula da barra é laranja `#F28C28`), o destaque do botão ativo usa o azul marinho escuro **`#111C30`** (mesmo tom da barra do Modo Claro).

---

## 4. Visão de Futuro Próximo (IA de Visão para Notas e Receitas)

A arquitetura separada de Back-end + Front-end da **v2.0** já deve deixar o caminho pronto para o próximo grande recurso planejado pelo Leonan:
- **Leitura inteligente de Cupom Fiscal / Notinha de Compra por foto:** Tirar foto da nota da compra no celular/app -> IA de visão lê os itens, marcas, quantidades e valores -> atualiza o preço ou cadastra o insumo e registra no histórico de compras do Nexo.
- **Leitura inteligente de Receitas por foto/anexo:** Tirar foto de uma receita -> IA extrai ingredientes, quantidades, unidades e rendimento direto para a ficha técnica no Nexo (substituindo o parser antigo por regex em `backend/document_importer.py`).

---

## 5. Padrão do Instalador Windows (`instaladores/`)

Quando empacotarmos versões instaláveis do Nexo para Windows:
- **Nome do arquivo:** `instaladores/Nexo_Setup_v<versao>_x64.exe` + `instaladores/Uninstall_Nexo.exe`.
- **Metadados oficiais:**
  - Produto: `Nexo` | Descrição: `Nexo - Gestão de Custos e Precificação`
  - Autor/Fabricante: `Leonan Garcia`
  - Direitos autorais: `© 2026 Leonan Garcia. Todos os direitos reservados.`
- **Comportamento do Setup:** Exige Admin (UAC) para instalar em `C:\Program Files\Nexo` (com botão *Procurar...* para permitir outro diretório/disco como `D:\`), opção `(•) Todos os usuários (Padrão)` vs `( ) Apenas para mim` (sem duplicar ícone na Área de Trabalho), barra de progresso e fechamento instantâneo ao concluir.
- **Comportamento em Execução:** Roda em qualquer conta de usuário **sem pedir Admin**, gravando o banco `nexo.db` zerado na primeira instalação dentro de `%LOCALAPPDATA%\Nexo`.
