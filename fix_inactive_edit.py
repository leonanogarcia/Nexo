import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Update edit_selected_recipe
code = re.sub(
    r"    def edit_selected_recipe\(self\):\s*\n\s*s = self\.rec_tree\.selection\(\)\s*\n\s*if not s:\s*\n\s*messagebox\.showwarning\('Receitas','Selecione uma receita para editar.', parent=self\); return\s*\n\s*code = self\.rec_tree\.item\(s\[0\]\)\['values'\]\[0\]\s*\n\s*with db\(\) as c: r = c\.execute\('SELECT id FROM base_recipes WHERE code=\?',\(code,\)\)\.fetchone\(\)\s*\n\s*if r:self\.recipe_form\(r\['id'\]\)",
    r"    def edit_selected_recipe(self):\n        s = self.rec_tree.selection()\n        if not s:\n            messagebox.showwarning('Receitas','Selecione uma receita para editar.', parent=self); return\n        code = self.rec_tree.item(s[0])['values'][0]\n        with db() as c: r = c.execute('SELECT id, active FROM base_recipes WHERE code=?',(code,)).fetchone()\n        if r:\n            if not r['active']:\n                messagebox.showwarning('Item Inativo','Receitas inativas nao podem ser editadas.', parent=self); return\n            self.recipe_form(r['id'])",
    code
)

# Update edit_selected_product
code = re.sub(
    r"    def edit_selected_product\(self\):\s*\n\s*s = self\.prod_tree\.selection\(\)\s*\n\s*if not s:\s*\n\s*messagebox\.showwarning\('Produtos','Selecione um produto para editar.', parent=self\); return\s*\n\s*code = self\.prod_tree\.item\(s\[0\]\)\['values'\]\[0\]\s*\n\s*with db\(\) as c: r = c\.execute\('SELECT id FROM products WHERE code=\?',\(code,\)\)\.fetchone\(\)\s*\n\s*if r:self\.product_form\(r\['id'\]\)",
    r"    def edit_selected_product(self):\n        s = self.prod_tree.selection()\n        if not s:\n            messagebox.showwarning('Produtos','Selecione um produto para editar.', parent=self); return\n        code = self.prod_tree.item(s[0])['values'][0]\n        with db() as c: r = c.execute('SELECT id, active FROM products WHERE code=?',(code,)).fetchone()\n        if r:\n            if not r['active']:\n                messagebox.showwarning('Item Inativo','Produtos inativos nao podem ser editados.', parent=self); return\n            self.product_form(r['id'])",
    code
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
