# 04. Módulo: Insumos (Cadastro)

## 1. Main Table Display (`mat_tree`)
- **Column Order:** Checkbox | Código | Cód. Barras | Item | Marca | Quantidade | Un. | Valor | Categoria | Data | ...
- **Data Mapping Rule:** The `refresh_materials` SQL SELECT statement MUST perfectly match the column indices defined in the UI. If a column is added (like barcode), the SQL query must be updated to prevent data shifting.

## 2. Registration Form Modal (`material_form`)
- **Inputs:** Must strictly use `RoundedDropdown` for selections and `rounded_entry`/`masked_money_entry` for text/numbers.
- **Fields:** Nome, Marca, Quantidade, Unidade, Valor da compra, Categoria, Data, Cód. Barras.
- **Validation:** Quantities > 0, Values >= 0 (Zero only allowed if Category is 'Doação').
