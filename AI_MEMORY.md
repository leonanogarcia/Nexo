# Memória de Contexto da IA (Projeto Nexo)

> **ATENÇÃO IA:** As regras absolutas de negócio, design e arquitetura do sistema agora residem na pasta `docs/`. Você **É OBRIGADO** a consultar e respeitar os arquivos dentro de `docs/` antes de tomar qualquer ação no código.

## Documentação Oficial (Single Source of Truth)
- `docs/01_CORE_DIRECTIVES.md`: Protocolos da IA, proibição de usar componentes feios para coisas novas. Regra "Qualidade > Velocidade".
- `docs/02_DESIGN_SYSTEM.md`: Biblioteca de componentes (Cápsulas, Cores, Hitboxes, Toplevels). OBRIGATÓRIO para novas telas.
- `docs/03_DATABASE_SCHEMA.md`: Estrutura do BD, auto-migrações e integridade referencial.
- `docs/04_MODULE_MATERIALS.md`: Regras do módulo de Insumos (Cadastro).
- `docs/05_MODULE_RECIPES_PRODUCTS.md`: Regras de Receitas e Produtos, incluindo a lei inquebrável de dependência funcional (puxar insumos sem falhar).
- `docs/06_MODULE_SETTINGS_SIDEBAR.md`: Layout da Sidebar, estado de foco, responsividade, e configurações do sistema.

## Status Atual
- Em processo de refatoração para aplicar o Design System universalmente. Existem divergências no código atualmente (componentes antigos), mas o que dita a regra ideal é a pasta `docs/`.
- Regra de Conduta: **LEIA -> REPENSE -> PROPONHA -> SÓ ENTÃO EXECUTE (se aprovado)**.

## Histórico Recente (Último Backup v0.7.25)
- **UI Checkboxes:** Substituído checkboxes textuais em nativo por imagens renderizadas PIL (resolvendo problemas de highlight e rendering feio do Windows).
- **Sidebar & Responsividade:** O minsize da janela foi reduzido para (1000x600). A Sidebar ganhou matemática de re-ancoragem (Efeito Sanfona) garantindo que botões (como a Engrenagem de Configurações) jamais vazem os limites, independente do monitor.
- **Engrenagem de Colunas:** Implementado `_show_generic_col_menu` compartilhado globalmente. A engrenagem da tela Cadastro, Receitas e Produtos agora funcionam de forma autônoma para ocultar/mostrar colunas e persistem via banco.
- **Padrão de Ícones & Switches (v1.9.3):** Proibido emojis coloridos na UI; todos os ícones são SVG vetoriais (`currentColor`, traço fino `1.45` em `24×24` / `1.15–1.35` em `32×32`, `w-7 h-7` nos cards e modais de Configurações, com halo/recorte na cor do card quando sobrepostos). Ver `docs/02_DESIGN_SYSTEM.md` (seção 5).

## Regras de Backup e Versionamento (Auto-Commit)
- **12h00 (Backup Diário):** A IA aciona uma verificação de `git status`.
- **18h00 (Nova Versão):** A IA aciona uma verificação de `git status` para gerar uma nova versão.
- **Protocolo de Segurança Absoluto:**
  1. Se não houver alterações, ignorar silenciosamente.
  2. Se houver alterações, **MAS** a IA estiver ativamente escrevendo código ou no meio de uma tarefa com o usuário, a IA **É OBRIGADA** a perguntar e pedir permissão antes de fazer o commit. NUNCA suba código incompleto ou potencialmente quebrado sem aprovação explícita.


## Regra Obrigatória de Empacotamento (`.exe` / Instalador)
- **Antes de gerar qualquer executável ou instalador:** É **OBRIGATÓRIO** ler `docs/08_ROADMAP_INSTALLER.md` e garantir:
  1. **Banco 100% zerado** (nunca empacotar `nexo.db`, `nexo_config.json`, `nexo_file_config.json`, `backups/`, `documentos/` ou `user_data/` de teste);
  2. **IA desligada e chave zerada** (`ai_enabled = "0"`, `ai_api_key = ""`, nenhuma chave pessoal ou provedor pré-configurado);
  3. **Estado limpo para novo usuário** (Canais de Venda desligados por padrão, marca padrão Nexo, zero insumos/receitas/produtos de teste);
  4. **Botão `🔄 Recarregar` oculto** no executável (`status.is_packaged === true` via `getattr(sys, "frozen", False)`).


## Roadmap Planejado para a v2.1 (Lembrete de Continuação)
Quando o usuário pedir para retomar a **v2.1**, lembrar e desenvolver estas **2 frentes grandes** combinadas:
1. **Conectores de Banco de Dados Remoto / Servidor (Empresa, AWS, PostgreSQL, MySQL, Banco Online):**
   - Permitir configurar conexão com servidor da empresa, AWS RDS ou banco online na aba **Configurações → Banco de Dados** (host, porta, banco, usuário, senha protegida, SSL), adaptando a camada SQL do backend, suportando migração do SQLite atual e atualizando os botões **`(i)`** com o passo a passo de configuração.
2. **Sistema Completo de Idiomas (i18n — Português, Inglês e Espanhol) & Preferências Regionais:**
   - **Regra de Ouro:** Dados cadastrados pelo usuário (nomes de insumos, marcas, categorias, receitas, produtos, unidades personalizadas, canais personalizados, histórico digitado, empresa) **JAMAIS** são traduzidos — apenas a interface do Nexo.
   - **3 Controles Independentes** na aba **Configurações → Idioma & Região** (mudar um não altera os outros):
     1. **Idioma:** `Português (Brasil)` (`pt-BR`, padrão), `English` (`en`), `Español` (`es`);
     2. **Moeda:** `BRL (R$)` (padrão), `USD ($)`, `EUR (€)`, `GBP (£)` — troca símbolo e formatação sem conversão cambial;
     3. **Formato de Data e Hora:** `DD/MM/YYYY` (padrão), `MM/DD/YYYY`, `YYYY-MM-DD` e `24h` / `12h`.
   - **Plano em 4 Etapas:**
     - **Etapa 1:** Infraestrutura (`frontend/src/i18n/` com `I18nContext`, `pt-BR`, `en`, `es`, `formatters`) + persistência no backend (`GET /api/status`, `GET /api/settings`, `POST /api/settings/regional`).
     - **Etapa 2:** UI dos 3 seletores em `SettingsPage.tsx` + tradução completa de Configurações.
     - **Etapa 3:** Tradução e formatadores dinâmicos em `DesignSystem`, `HomePage`, `MaterialsPage`, `RecipesPage`, `ProductsPage`, `ConversionsModal`, `DocumentAttachmentsModal` e `AiPreviewModals`.
     - **Etapa 4:** Mensagens da API no backend alinhadas ao idioma ativo.
