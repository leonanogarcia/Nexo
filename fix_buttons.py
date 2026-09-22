import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(
    r"self\.mat_bulk_delete_btn=ttk\.Button\(.*?\)",
    "self.mat_bulk_delete_btn=RoundedActionButton(bar, 'Excluir', self.delete_selected_materials, width=120, height=40, fill='#FEE2E2', hover='#FECACA', fg='#DC2626')",
    code
)

code = re.sub(
    r"self\.rec_bulk_delete_btn=ttk\.Button\(.*?\)",
    "self.rec_bulk_delete_btn=RoundedActionButton(bar, 'Excluir', self.delete_selected_recipes, width=120, height=40, fill='#FEE2E2', hover='#FECACA', fg='#DC2626')",
    code
)

code = re.sub(
    r"self\.prod_bulk_delete_btn=ttk\.Button\(.*?\)",
    "self.prod_bulk_delete_btn=RoundedActionButton(bar, 'Excluir', self.delete_selected_products, width=120, height=40, fill='#FEE2E2', hover='#FECACA', fg='#DC2626')",
    code
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
