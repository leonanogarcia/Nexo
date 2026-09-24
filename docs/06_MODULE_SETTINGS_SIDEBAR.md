# 06. Módulos: Sidebar e Configurações

## 1. Sidebar (Menu Lateral)
- **Geometria:** O painel esquerdo possui 150px de área dedicada. O "trilho" colorido (fundo ativo) tem 68px de largura.
- **Comportamento Hover/Active:**
  - Quando ativo, o botão se transforma numa pílula (radius 20px) com altura de 60px.
  - A cor de fundo muda dinamicamente: Modo Claro (marrom escuro `#693A16`), Modo Escuro (laranja claro `#F6A45A`).
- **Renderização Vectorial (`SidebarIcon`):**
  - Os ícones NÃO são imagens (.png). São desenhados matematicamente no `tk.Canvas` para evitar serrilhados.
  - O ícone "Configurações" (Engrenagem) é renderizado como um polígono perfeito de 16 pontas usando trigonometria (radianos e cossenos) e contorno `width=2.9`.
  - NENHUM ícone externo deve ser usado na Sidebar. Tudo deve ser desenhado em Canvas.

## 2. Janela de Configurações (Settings Page)
- **Estrutura de Exibição:** 
  - A tela não é um formulário simples; ela é uma lista de cartões (painéis).
  - Cada configuração fica dentro de um `RoundedPanel` com título em negrito.
- **Cartões Obrigatórios:**
  1. `Aparência`: Troca Tema (Claro, Escuro, Sistema).
  2. `Empresa`: Define Nome e Logo (aceita PNG, JPG, WebP).
  3. `Custos operacionais`: Define Gás, Energia e Água em % (estes afetam globalmente a precificação dos Produtos).
  4. `Unidades internas` & `Unidades configuráveis`: Puxa as métricas de Massa, Volume e Quantidade base.
  5. `Idioma`: Português (Brasil).
  6. `Fonte de dados`: Permite escolher o caminho do arquivo SQLite ou migrar o banco de dados.
  7. `Auditoria e Documentos`: Visualização avançada.

## 3. Conformidade com o Design System
- **ATUALIZAÇÃO NECESSÁRIA:** A tela de configurações atual usa `ttk.Entry` quadrados e botões cinzas do Windows. 
- **REGRA DE OURO:** No momento da modernização, cada um desses cartões (painéis) DEVE obrigatoriamente ter seus inputs trocados por `CapsuleEntry` e os botões por `RoundedActionButton` laranjas.
