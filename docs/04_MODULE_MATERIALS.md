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
