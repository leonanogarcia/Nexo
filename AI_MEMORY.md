# Memória de Contexto da IA (Projeto Nexo)

> **ATENÇÃO IA:** Ao iniciar uma nova sessão ou trocar de máquina, LEIA este arquivo inteiro antes de tomar qualquer ação no código. Ele contém as regras fundamentais e o estado atual do projeto.

## 1. Regras de Ouro (Golden Rules)
1. **Excelência acima da Velocidade**: Entregue soluções perfeitas, bem arquitetadas e testadas. Não faça "gambiarras" ou códigos feitos às pressas só para entregar rápido.
2. **Entenda antes de agir**: Quando o usuário pedir, SEMPRE explique o que você entendeu do problema e espere a confirmação do usuário antes de mexer no código.
3. **Preservação de Design**: O design atual (layout, cores, ícones) foi minuciosamente ajustado. Não altere o visual (cores sólidas, bordas arredondadas) sem ordem expressa. Use os padrões de cores dinâmicos (`self.colors['panel']`, `self.colors['muted']`, etc).
4. **Hitbox de Cliques (Tkinter)**: Em botões feitos no Canvas, toda a área clicável deve ter uma cor de preenchimento real (ainda que igual ao fundo do painel `bg`) para capturar o clique perfeitamente. Nunca use `fill=''` se a área precisar ser clicável.
5. **Transparência no Windows**: A transparência de Toplevels é feita usando a chave `#000001`. Nunca use essa cor em nenhum elemento da tela que não deva ser invisível.
6. **Cantos Arredondados ("Cápsulas")**: O usuário odeia "canto vivo". Tudo deve ser arredondado e fluído. Os campos de digitação (`rounded_entry`) e botões (`RoundedActionButton`) devem ter bordas arredondadas (radius 20) com outline leve cinza.

## 2. Decisões Técnicas e Arquitetura
- **Menus Customizados (3 pontinhos)**: O sistema abandonou os menus antigos e adotou `tk.Toplevel` customizado com bordas arredondadas e ícones desenhados internamente via PIL.
- **Cabeçalhos Premium nas Tabelas**: As abas principais usam um sistema avançado de Canvas (`_redraw_mat_header`, etc.) para renderizar cabeçalhos.
- **Formulários (Modais)**: Substituímos elementos nativos feios (`ttk.Combobox`, `tk.Entry` quadrado) por `RoundedDropdown` e cápsulas personalizadas com `RoundedPanel`.
- **Auto-Migration de BD**: Quando adicionamos colunas novas (ex: `barcode`), injetamos um bloco `PRAGMA table_info` no `init_db()` para fazer o `ALTER TABLE ADD COLUMN` automaticamente na inicialização, garantindo que o app não "quebre" na máquina de outras pessoas via Git Pull.

## 3. Resumo da Última Sessão e Ponto de Parada
- **Últimas Correções Feitas (v0.7.20+)**:
  1. O formulário "Novo Item" do Cadastro foi totalmente modernizado. Trocamos os botões nativos por `RoundedActionButton` laranjas/cinzas e os textboxes por cápsulas arredondadas.
  2. Implementamos o `RoundedDropdown` com alinhamento flexível (`align='left'`) nos campos "Categoria" e "Unidade".
  3. Adicionamos a coluna "Cód. Barras" (`barcode`) na tabela do banco SQLite, na tabela visual do Cadastro (`mat_tree`) e dentro do Modal de edição.
  4. Corrigimos um mega desalinhamento nas tuplas que o SQLite trazia, onde a inserção de `barcode` tinha deslocado o campo de quantidade pra dentro da marca. A consulta do `refresh_materials` foi adaptada.

## 4. Próximos Passos (Backlog de Amanhã)
- O usuário detectou que "tem erros mas vemos amanhã". Possivelmente relacionados aos formulários de Receitas/Produtos que ainda têm os antigos `ttk.Combobox` ou algum vazamento visual no modal recém modificado.
- Lembrete de Arquitetura: Existe um erro conhecido (IntegrityError) ao tentar excluir (lixeira) um material que já está amarrado a uma Receita/Produto, por falta de tratamento (como ON DELETE CASCADE). Isso deve ser revisado em breve.
