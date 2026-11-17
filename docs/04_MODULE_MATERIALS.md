# 04. Módulo: Insumos (Cadastro)

## 1. Main Table Display (`mat_tree`)
- **Column Order:** Checkbox | Código | Cód. Barras | Item | Marca | Quantidade | Un. | Valor | Categoria | Data | ...
- **Data Mapping Rule:** The `refresh_materials` SQL SELECT statement MUST perfectly match the column indices defined in the UI. If a column is added (like barcode), the SQL query must be updated to prevent data shifting.

## 2. Registration Form Modal (`material_form`)
- **Inputs:** Must strictly use `RoundedDropdown` for selections and `rounded_entry`/`masked_money_entry` for text/numbers.
- **Fields:** Nome, Marca, Quantidade, Unidade, Valor da compra, Categoria, Data, Cód. Barras.
- **Validation:** Quantities > 0, Values >= 0 (Zero only allowed if Category is 'Doação').

## 3. Conversões Customizadas (Dicionário de Medidas)
O sistema possui uma arquitetura de conversão de volume culinário para unidade de compra (ex: Xícara -> g -> kg). As regras dessa engine são:
- **Exclusividade por Insumo:** Uma unidade customizada (ex: "Xícara = 120g") NUNCA é global. Ela pertence estritamente ao Insumo ID para o qual foi criada (ex: "Farinha").
- **Injeção Dinâmica:** No Módulo de Receitas/Produtos, ao selecionar um insumo, a UI DEVE buscar automaticamente todas as conversões dele na tabela custom_units e injetá-las no Dropdown de Unidades, ao lado das medidas padrão (g, kg, l).
- **Cálculo de Custo Reverso:** Quando o usuário cadastra "2 Xícaras" na Ficha Técnica, o Motor de Custos deve interceptar essa unidade, cruzar com a tabela custom_units para descobrir o actor_to_base (ex: 120g), calcular o total em gramas (240g), converter para a unidade de compra do cadastro do Insumo (0.24 kg) e, por fim, calcular o custo final em reais baseado no preço de compra.
- **Design do Modal de Conversão:** A tela de cadastro de conversão é uma ferramenta de inserção rápida. Ela NÃO POSSUI botão de exclusão na tabela (o gerenciamento de exclusão/edição profunda deve ocorrer nas Configurações). O formulário segue um design linear em bloco sólido e utiliza componentes Premium (RoundedDropdown, RoundedActionButton cor Laranja Primário, e sem lupa no placeholder).


---

## Regras Rígidas de Identidade, Anti-Lixo e Notinha Fiscal (v1.9.0)

### 1. Identidade Única do Insumo (`Nome + Marca + Embalagem Base`)
- No banco SQLite (`materials`), `name` **não** é `UNIQUE` — apenas `code` (`INS_0001`, etc.) é único. Isso permite coexistir insumos com o mesmo nome mas embalagens ou marcas distintas (ex.: *Farinha Dona Benta 1 kg* vs *Farinha Dona Benta 500 g* vs *Farinha Anaconda 1 kg*), essenciais para rendimento e liga diferentes na cozinha.
- **Conversão para Unidade Base (`_base_packaging`):** Antes de comparar embalagens, `qty + unit` são convertidos via `units.to_base(qty, unit)`. Portanto `1 kg` e `1000 g` são reconhecidos como a **mesma embalagem**, enquanto `500 g` e `1 kg` são insumos distintos.

### 2. Bloqueio Anti-Duplicado, Anti-Erro de Digitação e Anti-Lixo
Aplicado no backend (`POST /api/materials`, `PUT /api/materials/{id}`, `POST /api/ai/apply-receipt`) e no frontend da Notinha (`AiReceiptPreviewModal`):
- **Qualidade de Texto (`_validate_quality_text` / `checkQualityTextClient`):**
  - Exige mínimo de **2 letras** (`[a-zA-ZÀ-ÿ]`) — bloqueia `.`, `-`, `123`, `x`.
  - Bloqueia caracteres repetidos idênticos (`xxx`, `aaaa`, `000`, `---`, `...`).
  - Bloqueia palavras genéricas de teste/lixo (`teste`, `test`, `asdf`, `qwe`, `nada`, `na`, `n/a`, `nenhum`, `generico`, `sem`, `qualquer`, `abc`, `xyz`).
  - Em **Marca**, ou o usuário informa a marca real ou marca explicitamente a caixinha **`☐ Sem marca`** (ideal para ovos, frutas e granel).
- **Normalização Forte (`_canonical_key`):** Remove acentos (`unicodedata.NFKD`), colapsa espaços extras e converte para minúsculas antes de comparar identidade.
- **Detector de Erro de Digitação (`_check_material_duplicate_or_typo`):** Se `Marca + Embalagem Base` coincidirem com um insumo ativo existente e `difflib.SequenceMatcher` do nome normalizado for `>= 0.85`, bloqueia a criação e alerta sobre possível erro de digitação.

### 3. Fluxo Rígido da Notinha Fiscal (IA)
- **Sugestão Inteligente (`parse_receipt_with_ai`):** Só sugere `action: "update"` automaticamente se **Nome** e **Embalagem na unidade base** coincidirem. Se a embalagem for diferente (`500 g` vs `1 kg`), sugere automaticamente `action: "create"`.
- **Card de 2 Linhas por Item:** Exibe Checkbox, Nome, Marca + `☐ Sem marca`, Ação (`Atualizar existente` ↔ `Criar novo`), Categoria, Qtd, Unidade, Valor, e:
  - Em **`Atualizar existente`**: dropdown para vincular manualmente a qualquer insumo do banco + seletor obrigatório de **Motivo** (pré-preenchido com `Compra via Notinha (IA)`, *Reajuste de preço*, *Promoção / Desconto*, *Compra recorrente*). A atualização altera **apenas** `purchase_value` e `updated_at` e registra a compra em `purchases` (com o motivo), nunca alterando embalagem/marca de um insumo usado em receitas.
  - Em **`Criar novo`**: exige todos os campos obrigatórios preenchidos com qualidade válida antes de permitir aplicar.
