# 03. Database & Data Architecture

## 1. Safety & Migrations
- **Schema Modifications:** Modifying the SQLite database schema must be done with extreme caution.
- **Auto-Migration Rule:** Whenever a new column is required (e.g., `barcode`), the `init_db()` function MUST include a `PRAGMA table_info` check to dynamically execute an `ALTER TABLE ADD COLUMN` if the column is missing. This prevents crashes on other machines pulling the repository.

## 2. Core Schemas
### Materials (`materials`)
- `id` (INTEGER PK), `code` (TEXT UNIQUE), `barcode` (TEXT), `name` (TEXT), `purchase_qty` (REAL), `purchase_unit` (TEXT), `purchase_value` (REAL), `brand` (TEXT), `category` (TEXT), `created_at` (TEXT), `updated_at` (TEXT), `active` (INTEGER), `archived` (BOOLEAN)

### Base Recipes (`base_recipes` & `base_recipe_items`)
- Recipes have a 1-to-N relationship with items (which reference `materials.id`).

### Products (`products` & `product_items`)
- Products have a 1-to-N relationship with items (which reference `base_recipes.id` or `materials.id`).

## 3. Configuration Storage
- System settings (like DB path, default units) are stored in `config.json` via `load_file_config()` and `save_file_config()`.

## 4. Relations & Integrity
- **ON DELETE Rule:** Items should be archived (`archived = 1`) or use cascading rules if deletion is permitted. Attempting to delete a material linked to a recipe currently throws an `IntegrityError`. This is a known architectural rule to be addressed.
