# 11. Arquivo de Traduções (i18n) & Região — Estado Atual (Pausado)

> **Status:** Pausado temporariamente após a **Etapa 4** para priorizar testes práticos e melhorias de UX/UI. Use este documento para retomar exatamente de onde paramos sem perder regras, arquivos ou etapas.

---

## 1. Regras e Princípios Definidos

1. **Idioma e Região são independentes:**
   - **Idioma da interface:** `pt-BR`, `en`, `es` (`frontend/src/i18n/types.ts`).
   - **Moeda, formato de data e formato de hora:** configuráveis separadamente (`frontend/src/i18n/formatters.ts` + `I18nContext.tsx`), permitindo usar o app em português com dólar/euro ou em inglês/espanhol com real (`R$`), etc.
2. **Banco de Dados Intacto:**
   - Alterar o idioma traduz **apenas a interface do Nexo** e nunca altera nomes de insumos, receitas ou produtos cadastrados no banco.
3. **Textos Simples para o Usuário:**
   - Avisos e textos de ajuda na tela devem ser curtos, claros e em linguagem humana (evitar jargão técnico desnecessário).
4. **Paridade entre Dicionários:**
   - Toda chave adicionada em `pt-BR.ts` deve existir com a mesma estrutura em `en.ts` e `es.ts` para manter tipagem e zero `tsc` errors.
5. **Formatação Centralizada:**
   - Usar `t(...)`, `formatCurrency(...)`, `formatDate(...)` e `formatMoneyInput(...)` fornecidos por `useI18n()` (`frontend/src/i18n/I18nContext.tsx`) em vez de strings ou `R$` fixos.

---

## 2. Arquivos Base Existentes

- `frontend/src/i18n/types.ts` — tipos (`LanguageCode`, `CurrencyCode`, `DateFormatCode`, `TimeFormatCode`, `CURRENCY_META`).
- `frontend/src/i18n/formatters.ts` — formatação de moeda, data, hora e máscara monetária.
- `frontend/src/i18n/I18nContext.tsx` — provider global e hook `useI18n()`.
- `frontend/src/i18n/locales/pt-BR.ts` — dicionário base em Português (Brasil).
- `frontend/src/i18n/locales/en.ts` — dicionário em Inglês.
- `frontend/src/i18n/locales/es.ts` — dicionário em Espanhol.

---

## 3. Progresso das Etapas

### Concluídas
- **Etapa 1 — Infraestrutura i18n & Persistência Regional:** criação da estrutura `frontend/src/i18n/` e integração com configurações regionais no backend (`backend/routes/settings.py`).
- **Etapa 2 — Shell & Design System:** `frontend/src/App.tsx` e `frontend/src/components/DesignSystem.tsx` (navegação lateral, máscaras monetárias via `useI18n`).
- **Etapa 3 — Configurações (Idioma & Região):** `frontend/src/components/SettingsPage.tsx` com seletores independentes de idioma, moeda, data, hora e modal explicativo.
- **Etapa 4 — Dashboard (`HomePage.tsx`):** `frontend/src/components/HomePage.tsx` integrada com `t`, `formatCurrency` e `formatDate`.

### Pendentes (para quando retomar)
- **Etapa 5 — Módulos Principais:**
  - `frontend/src/components/MaterialsPage.tsx` (incluindo modal de item parecido e rascunhos no topo da tabela);
  - `frontend/src/components/RecipesPage.tsx` (incluindo switch opcional de equipamento, rascunhos e botão de conversão);
  - `frontend/src/components/ProductsPage.tsx` (incluindo rascunhos e botão de conversão).
- **Etapa 6 — Modais Auxiliares:**
  - `frontend/src/components/ConversionsModal.tsx` (incluindo o mini-manual `(?) Ajuda`);
  - `frontend/src/components/DocumentAttachmentsModal.tsx`;
  - `frontend/src/components/AiPreviewModals.tsx`.
- **Etapa 7 — Revisão & Validação Final:**
  - Garantir paridade total de chaves entre `pt-BR.ts`, `en.ts` e `es.ts`;
  - Conferir `RoundedDropdown` / `CapsuleQuantityUnit` (`Un.` / `Unidade` / `Nenhum resultado` / `Sem opções`);
  - Testar troca ao vivo entre `pt-BR`, `en` e `es` em todas as telas e validar com `tsc --noUnusedLocals --noEmit` + `vite build`.
