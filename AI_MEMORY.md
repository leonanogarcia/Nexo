# Memória de Contexto da IA (Projeto Nexo)

> **ATENÇÃO IA:** Ao iniciar uma nova sessão ou trocar de máquina, LEIA este arquivo inteiro antes de tomar qualquer ação no código. Ele contém as regras fundamentais e o estado atual do projeto.

## 1. Regras de Ouro (Golden Rules)
1. **Excelência acima da Velocidade**: Entregue soluções perfeitas, bem arquitetadas e testadas. Não faça "gambiarras" ou códigos feitos às pressas só para entregar rápido.
2. **Entenda antes de agir**: Quando o usuário pedir, SEMPRE explique o que você entendeu do problema e espere a confirmação do usuário antes de mexer no código.
3. **Preservação de Design**: O design atual (layout, cores, ícones) foi minuciosamente ajustado. Não altere o visual (cores sólidas, bordas arredondadas) sem ordem expressa. Use os padrões de cores dinâmicos (`self.colors['panel']`, `self.colors['muted']`, etc).
4. **Hitbox de Cliques (Tkinter)**: Em botões feitos no Canvas, toda a área clicável deve ter uma cor de preenchimento real (ainda que igual ao fundo do painel `bg`) para capturar o clique perfeitamente. Nunca use `fill=''` se a área precisar ser clicável.
5. **Transparência no Windows**: A transparência de Toplevels é feita usando a chave `#000001`. Nunca use essa cor em nenhum elemento da tela que não deva ser invisível.

## 2. Decisões Técnicas e Arquitetura
- **Menus Customizados (3 pontinhos)**: O sistema abandonou os menus antigos e adotou `tk.Toplevel` customizado com bordas arredondadas e ícones desenhados internamente via PIL.
- **Lógica de Identificação (Banco de Dados)**: Para o usuário, os itens são vistos pelos seus códigos (ex: `INS_0001`), mas o SQLite opera internamente com `id` (inteiro) para amarrar as relações de forma rápida e à prova de falhas. 
- **Lógica de Identificação (Tabelas Tkinter)**: Ao descobrir de qual aba veio um evento, use a comparação direta de objetos (`if tree == getattr(self, 'mat_tree', None):`) e **não** tente adivinhar pelo nome da string do widget.

## 3. Resumo da Última Sessão e Ponto de Parada
- **Últimas Correções Feitas**:
  1. Adicionado uma margem (`padx=24`) do lado direito das abas do sistema para os painéis não encostarem grosseiramente na borda direita da janela.
  2. Resolvido o "Hitbox fantasma" do menu suspenso de 3 pontinhos.
  3. Corrigido um bug crônico onde a função Ativar/Desativar enviava comandos para a tabela de *Produtos* por engano quando disparado de *Insumos*, consertando a identificação da árvore (`mat_tree`).
  4. Melhorado drasticamente o visual do menu quando as opções (Editar, Ativar, Desativar) estão inativas: agora o texto e os ícones (lápis, play, pause) ficam com um tom cinza opaco forte, no padrão Windows de itens desabilitados.
  
## 4. Próximos Passos (Backlog)
- O usuário vai continuar guiando o aperfeiçoamento da ferramenta a partir de seu outro computador. 
- Lembrete: Existe um erro conhecido (IntegrityError) ao tentar excluir (lixeira) um material que já está amarrado a uma Receita/Produto, por falta de tratamento (como ON DELETE CASCADE). Isso deve ser revisado em breve.
