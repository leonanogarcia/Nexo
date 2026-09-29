# 05. Módulos: Receitas e Produtos

## 1. Janela de Receitas (Recipe Form)
- **Dimensões do Modal:** O Modal de Receitas deve ter o tamanho exato de `900x760`.
- **Campos do Cabeçalho:**
  - `Nome *`: Texto livre (CapsuleEntry, width 30).
  - `Rendimento`: Numérico (CapsuleEntry, width 16).
  - `Unidade`: Lista suspensa (RoundedDropdown, width 10).
  - `Observações`: Texto livre (CapsuleEntry, width 30).
- **Tabela de Composição Interna (Treeview):**
  - Colunas: `item` (Item, 360px), `qty` (Quantidade, 100px), `unit` (Un., 70px), `cost` (Custo, 110px).
- **Regras Funcionais de Composição:**
  - O campo de Seleção de Insumo deve carregar TODOS os insumos dinamicamente do banco de dados (tabela `materials`).
  - O clique duplo na tabela aciona a edição do item (preenchendo os campos novamente para alteração).
  - O cálculo de custo de cada item chama a função `material_cost` para recalcular o impacto financeiro com base no Rendimento/Quantidade.
- **Botões de Ação Inferiores:**
  - Usar `FlatEmojiButton` (✏️ e 🗑️) para edição e deleção de itens do grid interno.
  - Usar `RoundedActionButton` ("Salvar" Laranja, "Cancelar" Cinza) no rodapé.

## 2. Janela de Produtos (Product Form)
- **Dimensões do Modal:** O Modal de Produtos deve ter o tamanho exato de `920x680`.
- **Campos do Cabeçalho:**
  - `Nome *`: Texto livre.
  - `Peso/Rendimento`: Numérico.
  - `Unidade`: Lista Suspensa.
  - `Preço de venda`: Monetário (`masked_money_entry`).
  - `Observações`: Texto livre.
- **Tabela de Composição Interna (Treeview):**
  - Colunas: `type` (Origem, 120px), `item` (Componente, 330px), `qty` (Qtd., 90px), `unit` (Un., 70px), `cost` (Custo, 100px).
- **Regras de Origem (Níveis do Produto):**
  - Um produto é composto por 3 origens possíveis: `INSUMO`, `RECEITA` ou `PRODUTO`.
  - A lógica interna faz um mapeamento (`typemap`) para puxar do banco correto (`materials`, `base_recipes`, `products`).
  - **Prevenção de Loop Infinito:** O formulário proíbe que o produto atual seja adicionado a si mesmo na composição (regra `if r['id'] == current_pid: continue`).

## 4. Conformidade com o Design System
- **ATUALIZAÇÃO NECESSÁRIA:** Atualmente, as janelas internas de Receitas e Produtos ainda usam `ttk.Combobox` quadrados para unidades e insumos. 
- **REGRA DE OURO:** Qualquer refatoração nesses formulários OBRIGA a troca desses componentes pelos do Design System (`RoundedDropdown`, `CapsuleEntry`), mas garantindo matematicamente que o binding de dados (`<<ComboboxSelected>>` ou rastreador `.trace`) não seja quebrado, pois o formulário inteiro depende dessa ligação de variáveis.

## 5. Interações com a Árvore (Treeview)
- **Expansão Exclusiva por Seta (Chevron):** A ação de abrir ou fechar itens filhos em uma tabela árvore (como os componentes de uma receita) DEVE ser feita EXCLUSIVAMENTE pelo clique em um ícone vetorial (chevron) localizado na lateral esquerda da linha mãe.
- **Duplo-Clique Exclusivo para Edição:** O duplo-clique em qualquer linha do Treeview SERVE APENAS para invocar o painel de edição do item correspondente. É ESTRITAMENTE PROIBIDO atrelar comportamento de expansão/recolhimento de árvore ao duplo-clique para evitar conflitos de intenção do usuário.
- **Limpeza Visual de Itens Filhos:** Linhas que representam sub-itens (filhos expandidos) não devem herdar elementos de UI globais da linha mãe que não fazem sentido (por exemplo, a caixa de multisseleção ou ícones de edição geral), garantindo que fique claro visualmente que são apenas parte da composição.


## 6. Sincronismo de IA (Importação Automática)
- **O Botão Camaleão:** O botão de entrada no módulo de receitas possui comportamento duplo:
  - **IA Desligada (Modo Manual):** O botão se chama 📎 Anexar Documento. O usuário faz upload de um arquivo (foto/pdf), que é apenas anexado ao registro no banco para visualização futura (via botão secundário "Ver Documento Original"). Nenhuma extração é feita.
  - **IA Ligada (Modo Smart):** O botão se chama ✨ Importar via IA. Ao anexar, além de salvar a foto, o sistema aciona a API de IA configurada (ex: Gemini) para converter a foto em um JSON estruturado com ingredientes, rendimento e unidades.
- **Janela de Revisão Humana:**
  - NUNCA inserir dados gerados por IA diretamente no banco. 
  - Sempre exibir uma tela intermediária "Revisão da IA". O sistema compara os ingredientes lidos com o banco materials. Se não encontrar correspondência perfeita (De-Para), a linha é destacada em Laranja, exigindo que o usuário mapeie manualmente via dropdown antes de permitir o salvamento.
