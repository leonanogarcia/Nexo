# 06. Módulos: Sidebar e Configurações

## 1. Sidebar (Menu Lateral)
- **Geometria:** O painel esquerdo possui 150px de área dedicada. O "trilho" colorido (fundo ativo) tem 68px de largura.
- **Comportamento Hover/Active:**
  - Quando ativo, o botão se transforma numa pílula (radius 20px) com altura de 60px.
  - A cor de fundo muda dinamicamente: Modo Claro (marrom escuro `#693A16`), Modo Escuro (azul-marinho escuro `#111C30`, igual ao trilho do modo claro).
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

## 6. Sincronismo de IA (Controle Central)
- O software delega as requisições de Inteligência Artificial para um provedor externo (Google Gemini / OpenAI), gerenciado por esta seção nas configurações:
  - **Chave de Ativação Geral:** Liga/Desliga a funcionalidade em todo o sistema.
  - **Seletor de Provedor e Chave API:** O usuário define a plataforma e insere a própria credencial (API_KEY).
  - **Botão de Ajuda (i):** Fornece o mini-manual (sem links explícitos no alerta visual) ensinando a criar a chave na plataforma escolhida.
- **Escudo Financeiro e Limites (Segurança):**
  - O sistema rastreia localmente quantas requisições de IA foram feitas no dia (reset em 24h).
  - Um input numérico permite definir o "Alerta de Segurança Diário".
  - Se ultrapassar, a requisição NÃO é enviada ao provedor e exibe o alerta claro: *"Atenção: Limite de segurança de {limite} leituras diárias atingido. O Nexo salvou o documento apenas como anexo. Para importar automaticamente, aguarde a renovação no dia seguinte (tempo de recarga 24H) ou altere seu limite nas Configurações da IA."*


---

## Atualizações da Sidebar, Ajuda `ⓘ` e OpenRouter Gratuito (v1.9.0)

### 1. Sidebar Responsiva
- A cápsula vertical da sidebar usa `height: min(500px, calc(100vh - 140px))` com espaçamento e ícones proporcionais via `clamp(...)`, evitando cortes verticais em notebooks menores com escala DPI 125%/150%.

### 2. Botões de Ajuda Contextual (`ⓘ`) em Configurações
- Todas as categorias relevantes de Configurações possuem botões `ⓘ` (`InfoCircleIcon`) com modais explicativos claros em português ("como funciona, para que serve e como usar"):
  - Identidade da Marca;
  - Visão Geral de IA, Chave API e Seleção de Modelos;
  - Métricas de Custo & Jornada da Cozinha;
  - Unidades de Medida (internas e configuráveis por insumo);
  - Banco de Dados & BI (saúde, VACUUM, backup, preferências e auditoria/exportação).

### 3. Política de Modelos OpenRouter (Gratuito Automático vs Pago)
- **Modo Automático Gratuito:** Quando o provedor é `OpenRouter` e o campo **Modelo** está vazio ou configurado como `openrouter/free` / `free` / `auto` / `auto-free`, o Nexo consulta `https://openrouter.ai/api/v1/models` (cache de 10 min), filtra exclusivamente modelos `:free` (e com modalidade `"image"` quando há foto) e faz fallback automático em até 6 candidatos em caso de erro HTTP ou queda de conexão (`URLError`/`WinError 10054`/`TimeoutError`).
- **Modo Específico / Pago:** Quando o usuário informa qualquer modelo específico (ex.: `google/gemini-2.5-flash`, `openai/gpt-4o-mini` ou `openrouter/auto`), o Nexo respeita exatamente aquele modelo sem misturar com o pool gratuito.
