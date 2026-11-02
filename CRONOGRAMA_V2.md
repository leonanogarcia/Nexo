# 🧭 CRONOGRAMA OFICIAL — NEXO 2.0
> **Origem do Alinhamento:** Definido e aprovado pelo Leonan na conversa oficial (Passo 45).
> **Regra de Ouro:** Consultar este arquivo sempre para respeitar a ordem oficial acordada.

---

## 📌 As 5 Etapas Oficiais do Projeto

| Etapa | Módulo | Status | Descrição |
| :---: | :--- | :---: | :--- |
| **Etapa 1** | **Aba Insumos (Cadastro)** | ✅ **CONCLUÍDO** | Tabela inteligente, Histórico com HH:MM, Decisão de Salvamento, Duplicar e Exclusão Inteligente |
| **Etapa 2.1** | **Aba Receitas Base (Fichas Técnicas)** | ✅ **CONCLUÍDO** | Fichas técnicas ativas, cálculo dinâmico de custo total e porção, expansão de ingredientes na tabela, conversões culinárias, cápsula unificada [Qtd \| Unidade] e modal compacto |
| **Etapa 2.2** | **Aba Produtos (Precificação e Venda)** | ✅ **CONCLUÍDO** | Precificação de venda, composição flexível (insumos + receitas + produtos), custos operacionais, cálculo de margem % e lucro R$, tabela com divisórias e menu de 3 pontinhos alinhado |
| **Etapa 3** | **Aba Configurações** | 🚀 **EM ANDAMENTO** | Menu lateral fiel (220px), Identidade da Empresa, Logo fluida (Redonda/Livre), Branding Dinâmico, Custos Operacionais, Unidades e Banco SQLite (Fase de Lapidação) |
| **Etapa 4** | **Aba Início (Dashboard + BI)** | ⏳ Pendente | KPIs estratégicos, 2 gráficos de rosca interativos e Modal de BI completo |
| **Etapa 5** | **Recursos Avançados & Empacotamento** | ⏳ Pendente | Sincronismo de IA (leitura de notas/receitas por foto), Backup e Instalador Desktop Oficial Windows |

---

## 🔍 Detalhamento das Etapas

### ✅ Etapa 1: Aba Insumos (Concluída)
* [x] Casca principal da aplicação em React + Tailwind + PyWebView.
* [x] Barra Lateral flutuante (`ReferenceSidebar`) com estilo cápsula e ícones vetorizados.
* [x] Tabela de Insumos com ordenação, redimensionamento, busca com debounce e seleção em lote.
* [x] Modal de Histórico de Compras com data e hora reais (`HH:MM`), badge `[ Atual ]` e botão `Baixar Histórico`.
* [x] Ação `📑 Duplicar` no menu de 3 pontinhos.
* [x] Fluxo de Decisão Inteligente (Marca, Preço/Embalagem e Marca+Preço combinados) para proteção do banco e do BI.
* [x] HUDs animados centrais de Sucesso, Aviso e Erro.

---

### ✅ Etapa 2.1: Aba Receitas Base (Fichas Técnicas) — CONCLUÍDA
* [x] **Backend Completo:**
  * Endpoints REST para CRUD de receitas base, cálculo instantâneo de custo (`preview-cost`), duplicação atômica e histórico.
* [x] **Interface e Tabela Nexo:**
  * Colunas com Código (`RB_0001`), Nome da Receita, Rendimento, Custo Total, Custo / Porção, Data e Status.
  * Expansão da linha (Chevron) exibindo a composição de ingredientes com quantidades e custos individuais na tabela.
  * Ação rápida `📑 Duplicar` no menu 3 pontinhos com cópia automática de todos os ingredientes.
* [x] **Conversões Culinárias na Aba Receitas:**
  * Botão e modal dedicado de Conversões de Medidas integrado na toolbar de Receitas.
* [x] **Modal de Ficha Técnica:**
  * Adição/remoção dinâmica de insumos, seleção de unidades e cards de resumo (Custo Total, Rendimento, Custo / Porção) atualizados em tempo real.
  * Cápsula oficial unificada `CapsuleQuantityUnit` fundindo `[ Quantidade | Unidade ⌵ ]` com divisória fina vertical.
  * Modal refinado e compacto (740px de largura) com rendimento reduzido no topo.
* [x] **Histórico de Custos da Receita:**
  * Modal de evolução do custo com exportação em CSV (`Baixar Histórico`) e botão `[ Fechar ]` padronizado.
* [x] **Engrenagem Matemática Oficial de 6 Dentes:**
  * Substituição do ícone estrela pelo ícone geométrico de 6 dentes vazado oficial.

---

### ✅ Etapa 2.2: Aba Produtos (Precificação e Venda) — CONCLUÍDA
* [x] **Backend REST de Produtos:**
  * Endpoints para listagem (`/api/products`), criação/edição com composição mista (`MATERIAL`, `RECIPE_BASE`, `PRODUCT`).
  * Cálculo em tempo real de custo direto, custo operacional e preço de venda com margem % e lucro R$.
  * Exclusão inteligente com verificação de vínculo a outros combos/produtos e inativação segura.
  * Histórico de custos e endpoint de duplicação.
* [x] **Interface e Tabela Nexo:**
  * Tabela oficial com cabeçalho de 36px, divisórias verticais finas e colunas com larguras seguras (`Peso / Rend.`, `Custo Produção`, `Preço Venda`, `Lucro (R$)`, `Margem %`).
  * Seleção integrada: clicar na linha marca o checkbox automaticamente (`selectSingleRow`).
  * Duplo clique na linha para abrir o modal de edição imediatamente.
  * Menu flutuante de 3 pontinhos alinhado perfeitamente logo abaixo do botão, com ícones e dimensões oficiais do Nexo.
  * Persistência de preferências de colunas visíveis via `/api/settings/prod_hidden_cols`.

---

### 🚀 Etapa 3: Aba Configurações & Identidade da Marca — EM ANDAMENTO
* [x] **Arquitetura 1:1 Fiel com Menu Lateral Interno (220px):**
  * 5 categorias dedicadas com navegação rápida: Geral, Inteligência Artificial, Métricas de Custo, Unidades de Medida e Banco de Dados & BI.
  * Ícones monocromáticos elegantes do Design System: Engrenagem, Microchip IA vetorial de alta nitidez, Gráfico de Custos, Régua de Medição e Cilindro de Banco.
* [x] **Aparência & Tema:**
  * Seletor de tema: **Modo Claro**, **Modo Escuro** e **Automático (Sistema)**.
  * Persistência imediata no SQLite (`settings.theme`) e sincronização global reativa.
* [x] **Identificação da Empresa & Branding Dinâmico:**
  * Nome da empresa e upload de logotipo com leitura em Canvas e extração automática da cor dominante da marca.
  * Logo flutuante sem caixa branca forçada, com suporte a canal alfa / PNG transparente.
  * Seletor manual de formato de exibição da logo: **Redonda / Circular** (`rounded-full`) vs **Livre / Retangular** (sem distorção via `object-contain`).
  * Opção de ocultar o nome da empresa na barra lateral para evitar redundância quando a logo já contiver o nome.
  * Controles independentes de personalização: aplicar paleta da marca no Sidebar e/ou nos Botões e Destaques.
  * Botão mestre de segurança **"↺ Restaurar Padrão Nexo"** com reset instantâneo de fábrica.
* [x] **Custos Operacionais Globais:**
  * Configuração de taxas percentuais: **Gás**, **Energia Elétrica** e **Água** com totalizador dinâmico e integração ao `calculator.py`.
* [x] **Unidades de Medida Globais:**
  * Visualização e configuração das unidades de massa (`mg`, `g`, `kg`, `t`), volume (`ml`, `L`, `kL`) e contagem (`un`).
* [x] **Banco de Dados & Manutenção:**
  * Status e tamanho do banco de dados SQLite ativo.
  * Retenção de histórico de auditoria configurável em meses.
  * Ações instantâneas de **Backup de Segurança** (salvo com carimbo de data/hora em `backups/`) e **Otimização / Compactação (`VACUUM`)**.

---

### ⏳ Etapa 4: Aba Início (Dashboard + BI)
* [ ] 3 Cards de KPI clicáveis no topo: Insumos, Receitas Base, Produtos.
* [ ] 2 Gráficos de rosca interativos:
  * Distribuição de compras por insumo.
  * Composição de custos (Receitas e Produtos).
* [ ] Modal de BI com tabelas detalhadas por Insumo, por Marca e por Receita/Produto com filtro de mês.

---

### ⏳ Etapa 5: Recursos Avançados & Empacotamento
* [ ] Integração com IA de Visão para leitura de notas fiscais e fotos de receitas.
* [ ] Build PyInstaller standalone e instalador Windows Inno Setup oficial (`Nexo_Setup_v2.0.0_x64.exe`).
