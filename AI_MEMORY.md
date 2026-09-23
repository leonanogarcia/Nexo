# Memória de Contexto da IA (Projeto Nexo)

> **ATENÇÃO IA:** Ao iniciar uma nova sessão ou trocar de máquina, LEIA este arquivo inteiro antes de tomar qualquer ação no código. Ele contém as regras fundamentais e o estado atual do projeto.

## 1. Regras de Ouro (Golden Rules)
1. **Excelência acima da Velocidade**: Entregue soluções perfeitas, bem arquitetadas e testadas. Não faça "gambiarras" ou códigos feitos às pressas só para entregar rápido.
2. **Entenda antes de agir**: Quando o usuário pedir, SEMPRE explique o que você entendeu do problema e espere a confirmação do usuário antes de mexer no código.
3. **Preservação de Design**: O design atual (layout, cores, ícones) foi minuciosamente ajustado. Não altere o visual (cores sólidas, bordas arredondadas) sem ordem expressa. Use os padrões de cores dinâmicos (`self.colors['panel']`, `self.colors['muted']`, etc).
4. **Hitbox de Cliques (Tkinter)**: Em botões feitos no Canvas, toda a área clicável deve ter uma cor de preenchimento real (ainda que igual ao fundo do painel `bg`) para capturar o clique perfeitamente. Nunca use `fill=''` se a área precisar ser clicável.
5. **Transparência no Windows**: A transparência de Toplevels é feita usando a chave `#000001`. Nunca use essa cor em nenhum elemento da tela que não deva ser invisível.
6. **Cantos Arredondados**: O usuário odeia "canto vivo". Tudo deve ser arredondado e fluído.

## 2. Decisões Técnicas e Arquitetura
- **Menus Customizados (3 pontinhos)**: O sistema abandonou os menus antigos e adotou `tk.Toplevel` customizado com bordas arredondadas e ícones desenhados internamente via PIL.
- **Cabeçalhos Premium nas Tabelas**: As 3 abas principais (Cadastro, Receitas e Produtos) não usam os títulos nativos do `Treeview` (`show='tree'`). Em vez disso, usam um sistema avançado de Canvas (`_redraw_mat_header`, etc.) para renderizar cabeçalhos arredondados.
- **Ícones de Edição Flutuantes**: As ações de Editar e Excluir nas linhas são geradas por `_attach_row_icon_overlay`. A coluna "mola" (`dummy` com `stretch=True`) DEVE SEMPRE estar ANTES dessas colunas na definição do Tkinter, para empurrá-las exatamente para o canto direito da tela.

## 3. Resumo da Última Sessão e Ponto de Parada
- **Últimas Correções Feitas**:
  1. A paleta de cores foi suavizada, trocando botões primários pelo laranja padrão do logo (`#F28C28`) e usando destaques sutis em tons pastéis (`#FFF5F5` para exclusão).
  2. Implementação e refatoração monumental das abas "Receitas" e "Produtos" para utilizarem os mesmos cabeçalhos arredondados, scrollbars de pílula e filtros flutuantes (Pesquisar/Status) de "Cadastro".
  3. Correção do layout das colunas: A coluna "dummy" foi remanejada para ficar antes dos ícones de ação, garantindo alinhamento visual perfeito à direita.
  4. Padronização total da tela vazia (`empty_state`) nas três abas usando imagens injetadas via PIL (`empty_state_reference_exact.png`).
  
## 4. Próximos Passos (Backlog)
- O usuário pediu para atualizar o Git porque um novo "fluxo massivo" de atualizações está planejado para o design e para os formulários de Receitas/Produtos.
- Lembrete: Existe um erro conhecido (IntegrityError) ao tentar excluir (lixeira) um material que já está amarrado a uma Receita/Produto, por falta de tratamento (como ON DELETE CASCADE). Isso deve ser revisado em breve.
