# 01. Core Directives & AI Protocol

## 1. The Prime Directive
**Quality Over Speed.** Never rush a feature or a fix. Architectural integrity, perfect functionality, and strict adherence to the Design System are paramount.

## 2. Rule Consultation (Mandatory)
Before writing or modifying ANY code, the AI **MUST** consult the relevant documentation in this `docs/` folder. These rules are absolute. 
- If creating a new feature, the AI must use the established Design System rules (Capsules, Rounded Components, Brand Colors) detailed in `02_DESIGN_SYSTEM.md`. 
- **NO UGLY DEFAULT COMPONENTS:** The AI is strictly forbidden from using native `tk.Entry`, `ttk.Combobox`, or square `ttk.Button` for new features.

## 3. Proposal Before Modification
If the AI believes a rule should be changed, or if a better architectural pattern is found, the AI **MUST NOT** implement it immediately. The AI must present the idea to the user, explain the rationale, and wait for explicit approval before altering the rule or the code.

## 4. The "Common Sense" Ecosystem Mandate
Every modification must consider the entire ecosystem. Adding a data field implies updating the DB schema, the input form, the visual table, the search query, and the data export functions. Modifying a component (like a dropdown) in one module implies verifying that it does not break data-fetching in other modules (e.g., Recipes).
