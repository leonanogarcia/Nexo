# 02. Design System & UI Components

## 1. Global Aesthetics & Shapes
- **Zero Sharp Corners:** The user strictly prohibits sharp edges. All UI elements (buttons, input fields, modals, floating menus) MUST have rounded corners.
- **The "Capsule" Standard:** All primary input fields and buttons must use a capsule/pill shape with `radius=20`.
- **Hitboxes:** Clickable canvas areas must have a solid fill color (even if matching the background) to ensure the mouse click registers perfectly. Never use `fill=''`.
- **Transparency:** `#000001` is strictly reserved for OS-level Toplevel window transparency. Never use it for visible elements.

## 2. Color Palette
- **Brand Primary:** Orange `#F28C28`
- **Secondary / Hover:** Light Orange `#F6A45A` (Dark mode) or Dark Brown `#693A16` (Light mode)
- **Backgrounds:** Dynamic via `self.colors['panel']`, `self.colors['field']`, or `#F3F6FA`
- **Borders/Lines:** Soft Grey `#E2EAF5`
- **Text:** Dark Navy `#18223A` or `#1F2A44`, Subtext `#687796`

## 3. Component Library (Strict Usage)
When creating or refactoring ANY interface, the AI MUST use these components:

### A. Buttons (`RoundedActionButton`)
- **Shape:** Pill format (`radius=20`).
- **Primary:** Brand Orange background, White text.
- **Secondary (Cancel/Close):** Dark grey/blue background, White text.
- **Behavior:** Hover states must slightly lighten/darken the button. Text must not disappear on render.

### B. Input Fields (`RoundedPanel` & `CapsuleEntry`)
- **Shape:** Capsule format (`radius=20`).
- **Styling:** Border `#E2EAF5`, background `#FFFFFF`.
- **Dimensions:** Fixed padding to prevent the internal `tk.Entry` from clipping the rounded corners.

### C. Dropdowns (`RoundedDropdown`)
- **Alignment:** Text alignment is configurable (`align='left'` or `align='center'`).
- **Mechanics:** Must pop open a custom Toplevel list. Replaces all native `ttk.Combobox` elements in forms.

### D. Table Headers & Columns
- **Custom Canvas Headers:** Tables DO NOT use native Treeview headers. They use a custom canvas drawn above the treeview with rounded top corners.
- **Dummy Column Rule:** A `dummy` column (`stretch=True`) MUST always precede the action columns (`edit`, `delete`) in the Treeview to push actions to the far right.
- **Action Columns Padding Rule (Obrigatório):** As action buttons (Edit, Delete, Options) are drawn via a fixed-width floating canvas on the right edge (e.g., 90px width for 3 icons), the underlying Treeview MUST define invisible ghost/dummy columns matching exactly the total width of this floating canvas. Example: If the floating overlay has 90px (3x30px icons), the treeview must explicitly define `('options', 30)` alongside `edit` and `delete`, even if empty. If this padding is omitted, the fixed canvas will swallow and hide the last visible data column of the table (like Status or Date).

### E. Empty States
- Always use the injected PIL image (`empty_state_reference_exact.png`). Never use plain text labels for empty tables.

### F. Ações em Lote & Multisseleção (Regra de Ouro)
- **Ocultar Botões Globais:** Quando múltiplas linhas de uma tabela são selecionadas (através das caixas de seleção/checkboxes), todos os botões de ação globais na barra superior (ex: "Conversões", "Nova Receita", "Novo Produto") DEVEM desaparecer.
- **Exclusividade de Ação em Lote:** Apenas os botões que executam ações em lote (ex: "Excluir") devem permanecer visíveis na tela durante a multisseleção.
- **Restauração:** Quando a seleção for limpa (0 itens selecionados), a interface deve restaurar automaticamente todos os botões globais. Isso garante uma experiência limpa (UX) sem ações conflitantes na tela.

## 4. Modals & Business Rules (Obrigatório)
O sistema deve abandonar janelas nativas do Windows (`messagebox`, `simpledialog`) em favor de Modais Customizados no padrão UI do Nexo, implementando as seguintes regras atômicas:

### A. Regra de Edição Silenciosa vs Atualização (CustomEditReasonModal)
- **Criação:** Itens novos são salvos diretamente sem pedir motivo (pois não há histórico prévio).
- **Edição:** Toda edição de Insumos, Receitas ou Produtos deve exibir um Modal com dois botões:
  1. **"Correção de Erro":** Salva as alterações silenciosamente e NÃO gera linha no `edit_history`.
  2. **"Atualização":** Exige texto/motivo e GERA nova linha no `edit_history`.
  - *Cancelamento:* Fechar o modal ou clicar cancelar aborta a transação inteira (nada é salvo).

### B. Regra de Exclusão Inteligente (CustomDeleteAlertModal)
- **Vínculos:** O sistema deve verificar dependências (`base_recipe_items`, `product_items`) antes de qualquer exclusão.
- **Modo Unitário:**
  - Livre: Permite Exclusão Permanente (botão vermelho).
  - Vinculado: Bloqueia exclusão, exibe alerta ⚠️ e permite apenas **Arquivar/Inativar** (botão laranja).
- **Modo em Lote (Multisseleção):**
  - O Modal divide visualmente a lista: 🔴 Itens para Excluir vs 🟡 Itens para Arquivar.
  - A confirmação executa as duas listas de uma vez.
  - *Transação Atômica:* O botão de Cancelar (ou fechar o modal) anula 100% da operação em lote. Nenhum item é alterado.

### C. Política de Retenção de Dados (BI)
- Históricos na tabela `edit_history` são vitais para o BI, mas não podem inchar infinitamente.
- O sistema mantém o parâmetro `history_retention_months` (tabela `system_settings`), editável na tela de Configurações.
- Uma rotina automática rodará na inicialização do app excluindo qualquer linha no `edit_history` cuja idade ultrapasse os meses estipulados.
