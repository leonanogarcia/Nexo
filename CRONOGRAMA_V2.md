# 🧭 CRONOGRAMA OFICIAL — NEXO 2.0
> **Origem do Alinhamento:** Definido e aprovado pelo Leonan na conversa oficial (Passo 45).
> **Regra de Ouro:** Consultar este arquivo sempre para respeitar a ordem oficial acordada.

---

## 📌 As 5 Etapas Oficiais do Projeto

| Etapa | Módulo | Status | Descrição |
| :---: | :--- | :---: | :--- |
| **Etapa 1** | **Aba Insumos (Cadastro)** | ✅ **CONCLUÍDO** | Tabela inteligente, Histórico com HH:MM, Decisão de Salvamento, Duplicar e Exclusão Inteligente |
| **Etapa 2.1** | **Aba Receitas Base (Fichas Técnicas)** | 🚀 **EM LAPIDAÇÃO** | Fichas técnicas ativas, cálculo dinâmico de custo total e porção, expansão de ingredientes na tabela e conversões culinárias |
| **Etapa 2.2** | **Aba Produtos (Precificação e Venda)** | ⏳ **A SEGUIR** | Precificação de venda, markup, margem de lucro, composição de receitas + embalagens |
| **Etapa 3** | **Aba Configurações** | ⏳ Pendente | Modo Escuro/Claro definitivo, Dados da Empresa/Logo, Custos Operacionais (Gás, Energia, Água), Unidades e Banco SQLite |
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

### 🚀 Etapa 2.1: Aba Receitas Base (Fichas Técnicas) — EM LAPIDAÇÃO
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
* [x] **Histórico de Custos da Receita:**
  * Modal de evolução do custo com exportação em CSV (`Baixar Histórico`).
* [ ] **Testes de Usabilidade e Refinos Visuais:**
  * Alinhamento fino com o usuário sobre comportamento, campos adicionais e validações.

---

### ⏳ Etapa 2.2: Aba Produtos (Precificação e Venda) — A SEGUIR
* [ ] **Composição de Produtos:**
  * Composição mista (Insumos diretos + Receitas Base + Embalagens).
* [ ] **Motor de Precificação:**
  * Regras de markup multiplicador, margem de lucro, taxas de cartão e preço de venda sugerido.

---

### ⏳ Etapa 3: Aba Configurações
* [ ] **Aparência & Tema:**
  * Seletor oficial de tema: **Modo Claro**, **Modo Escuro** e **Automático (Sistema)**.
  * Persistência imediata no SQLite (`settings.theme`) e aplicação global no HTML (`dark` class).
* [ ] **Identificação da Empresa:**
  * Nome fantasia da empresa e upload de logotipo.
* [ ] **Custos Operacionais Globais:**
  * Configuração de taxas percentuais: **Gás**, **Energia Elétrica** e **Água** (utilizados pelo `calculator.py` para calcular custos indiretos em receitas e produtos).
* [ ] **Unidades de Medida Globais:**
  * Visualização das unidades de massa (`mg`, `g`, `kg`, `t`), volume (`ml`, `L`, `kL`) e contagem (`un`).
* [ ] **Banco de Dados & Manutenção:**
  * Exibição do caminho do banco ativo (`%LOCALAPPDATA%\Nexo\nexo.db` ou caminho local).
  * Botão de backup rápido do banco de dados.

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
