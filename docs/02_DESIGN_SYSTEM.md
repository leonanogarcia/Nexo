# 02. Design System & UI Components

## 1. Global Aesthetics & Shapes
- **Zero Sharp Corners:** The user strictly prohibits sharp edges. All UI elements (buttons, input fields, modals, floating menus) MUST have rounded corners.
- **The "Capsule" Standard:** All primary input fields and buttons must use a capsule/pill shape with `radius=20`.
- **Hitboxes:** Clickable canvas areas must have a solid fill color (even if matching the background) to ensure the mouse click registers perfectly. Never use `fill=''`.
- **Transparency:** `#000001` is strictly reserved for OS-level Toplevel window transparency. Never use it for visible elements.

## 2. Color Palette
- **Brand Primary:** Orange `#F28C28`
- **Secondary / Hover:** Light Orange `#F6A45A` (Dark mode) or Dark Brown `#693A16` (Light mode)
- **Backgrounds:** Dynamic via `self.colors['panel']`, `self.colors['field']`, or `#F3F6FA`
- **Borders/Lines:** Soft Grey `#E2EAF5`
- **Text:** Dark Navy `#18223A` or `#1F2A44`, Subtext `#687796`

## 3. Component Library (Strict Usage)
When creating or refactoring ANY interface, the AI MUST use these components:

### A. Buttons (`RoundedActionButton`)
- **Shape:** Pill format (`radius=20`).
- **Primary:** Brand Orange background, White text.
- **Secondary (Cancel/Close):** Dark grey/blue background, White text.
- **Behavior:** Hover states must slightly lighten/darken the button. Text must not disappear on render.

### B. Input Fields (`RoundedPanel` & `CapsuleEntry`)
- **Shape:** Capsule format (`radius=20`).
- **Styling:** Border `#E2EAF5`, background `#FFFFFF`.
- **Dimensions:** Fixed padding to prevent the internal `tk.Entry` from clipping the rounded corners.

### C. Dropdowns (`RoundedDropdown`)
- **Alignment:** Text alignment is configurable (`align='left'` or `align='center'`).
- **Mechanics:** Must pop open a custom Toplevel list. Replaces all native `ttk.Combobox` elements in forms.

### D. Table Headers & Columns
- **Custom Canvas Headers:** Tables DO NOT use native Treeview headers. They use a custom canvas drawn above the treeview with rounded top corners.
- **Dummy Column Rule:** A `dummy` column (`stretch=True`) MUST always precede the action columns (`edit`, `delete`) in the Treeview to push actions to the far right.

### E. Empty States
- Always use the injected PIL image (`empty_state_reference_exact.png`). Never use plain text labels for empty tables.
