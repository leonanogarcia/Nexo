# 06. Módulos: Sidebar e Configurações

## 1. Sidebar (`SidebarIcon`)
- **Dimensions:** Fixed spacing (e.g., 150px available width, 68px side width).
- **Visuals:** Dark/Light mode support. Selected state has a distinct pill background (e.g., `#693A16` or `#F6A45A`) with `radius=20`.
- **Routing:** Each icon strictly routes to its respective module (Cadastro, Receitas, Produtos, Configurações).

## 2. Settings (Configurações)
- **Data Source:** Manipulates `config.json` and updates `nexo.db` status.
- **UI:** Follows the global design system. Modals or panels for settings must use the standard background colors and rounded buttons.
- **Responsiveness:** Changes applied in Settings (like Units) must immediately reflect across the application.
