# 05. Módulos: Receitas e Produtos

## 1. Form Modals (`recipe_form`, `product_form`)
- **Complexity:** These are composite forms. They contain standard inputs at the top (Name, Yield/Rendimento, Notes) and an internal Treeview at the bottom for ingredients.
- **Component Rules:** These forms MUST be migrated/built using the Design System (Capsule inputs, RoundedDropdowns) while ensuring data fetching is never broken.

## 2. Functional Dependencies (Critical)
- **Material Fetching:** The recipe form MUST dynamically load active materials from the database to populate the ingredient selection.
- **Product Fetching:** The product form MUST dynamically load active recipes/materials.
- *Rule of Integrity:* Modifying the UI components for selection MUST preserve the underlying data-binding. An ingredient dropdown cannot be empty if there are active materials in the DB.

## 3. Calculations
- Yield (`Rendimento`) and Unit Costs must recalculate dynamically based on the ingredient's `purchase_value` and `purchase_qty`.
- Profit margins in Products must reflect real-time cost accumulations.
