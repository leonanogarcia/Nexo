# 07. Módulo: Dashboard e Toolbar Principal

## 1. Estrutura da Toolbar (Bandeja Superior)
A Toolbar é o painel horizontal de controle principal do usuário (localizada acima da tabela de itens).
- **Componente Base:** O container deve ser obrigatoriamente um `RoundedPanel` com cor equivalente a `colors['panel']`, sem bordas rígidas, com raio `radius=22`.
- **Gordura Visual (Margens):** A altura não deve conter excesso de espaço morto. As margens de padding vertical (`pady`) devem ser enxutas (ex: `pady=11` para margem interna) permitindo que o layout respire sem consumir espaço desnecessário da tabela inferior. A propriedade `expand=True` da tabela adjacente garante o preenchimento do restante da tela.

## 2. Anatomia dos Botões de Ação (CTAs)
Os botões "+ Novo item" e "Histórico" ditam o fluxo principal da aplicação e obedecem a regras rígidas de hierarquia e comportamento:
- **Componente:** `RoundedActionButton`.
- **Hierarquia de Tamanho:** Devem possuir a altura cravada de **42px**. Eles são as ações primárias (CTAs) e nunca devem ser achatados para o tamanho de campos de texto comuns (32px), nem devem ser exagerados ao tamanho touchscreen (49px).
- **Engenharia de Hover (Anti-Bug):** A transição de cor (Hover) deve alternar explicitamente entre duas memórias imutáveis (`_base_fill` e `_hover_fill`). É terminantemente proibido o uso de cópias dinâmicas (`_fill0 = self._fill`) durante os eventos `<Enter>` e `<Leave>`, garantindo que o clique não gere o bug de cor "travada". O laranja de foco deve possuir alto contraste (ex: `#BA5200`).

## 3. Pesquisa e Filtros (Os Componentes VIPs)
A barra de controle direita dita as buscas e status da tabela.
- **Componente de Pesquisa:** Utiliza a classe exclusiva e dedicada `RoundedEntry` (com R maiúsculo) por possuir renderização interna vetorial do ícone de lupa, diferentemente dos inputs genéricos do sistema.
- **Componente de Filtro:** Utiliza a classe `RoundedDropdown` (ex: "Ativos").
- **REGRA ABSOLUTA DE ALINHAMENTO:** Tanto o `RoundedEntry` (Pesquisa) quanto o `RoundedDropdown` (Status) formam uma dupla visual e devem **OBRIGATORIAMENTE possuir a exata mesma altura geométrica de 32px** (`height=32`). É inadmissível divergência de tamanho entre componentes na mesma sub-bandeja.
- **Posicionamento Interno Dinâmico:** O ícone de lupa dentro do `RoundedEntry` não pode ter posições rígidas. Seu eixo Y deve ser centralizado dinamicamente via matemática (`cy = height / 2`) para que, caso a altura de 32px seja ajustada no futuro, o ícone continue organicamente alinhado sem sofrer cortes.

## 4. Regras Iconográficas Especiais (Engrenagem de Tabela)
É expressamente proibido o uso de ícones de texto ou emojis (ex: ⚙️) em componentes estruturais do sistema.
O seletor de colunas (engrenagem) deve ser matematicamente desenhado no Canvas, herdando a estética do polígono da Sidebar (16 pontas), com o centro obrigatoriamente vazado (pintado na cor do fundo) para manter a anatomia da peça.
