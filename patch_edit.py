import re

with open('main.py', 'rb') as f:
    content = f.read().decode('utf-8')

# We'll hook into _tree_click or the TreeviewSelect event.
# Actually, Nexo binds `<Double-1>` to `self.edit_selected_material` etc.
# We can just show the messagebox inside `edit_selected_recipe` and `edit_selected_product` if the recipe has archived items, BEFORE opening the form!

old_edit_recipe = """    def edit_selected_recipe(self):
        s = self.rec_tree.selection()
        if not s:
            messagebox.showwarning('Receitas','Selecione uma receita para editar.', parent=self); return
        code = self.rec_tree.item(s[0])['values'][0]
        with db() as c: r = c.execute('SELECT id FROM base_recipes WHERE code=?',(code,)).fetchone()
        if r: self.recipe_form(r['id'])"""

new_edit_recipe = """    def edit_selected_recipe(self):
        s = self.rec_tree.selection()
        if not s:
            messagebox.showwarning('Receitas','Selecione uma receita para editar.', parent=self); return
        name_val = self.rec_tree.item(s[0])['values'][1]
        if str(name_val).startswith('⚠️'):
            messagebox.showinfo('Atenção', 'Esta receita contém um ou mais insumos que foram EXCLUÍDOS do sistema.\\n\\nEles aparecerão marcados na lista de ingredientes. Por favor, remova-os ou substitua-os para atualizar a receita corretamente.', parent=self)
        code = self.rec_tree.item(s[0])['values'][0]
        with db() as c: r = c.execute('SELECT id FROM base_recipes WHERE code=?',(code,)).fetchone()
        if r: self.recipe_form(r['id'])"""

content = content.replace(old_edit_recipe, new_edit_recipe)

old_edit_prod = """    def edit_selected_product(self):
        s = self.prod_tree.selection()
        if not s:
            messagebox.showwarning('Produtos','Selecione um produto para editar.', parent=self); return
        code = self.prod_tree.item(s[0])['values'][0]
        with db() as c: r = c.execute('SELECT id FROM products WHERE code=?',(code,)).fetchone()
        if r: self.product_form(r['id'])"""

new_edit_prod = """    def edit_selected_product(self):
        s = self.prod_tree.selection()
        if not s:
            messagebox.showwarning('Produtos','Selecione um produto para editar.', parent=self); return
        name_val = self.prod_tree.item(s[0])['values'][1]
        if str(name_val).startswith('⚠️'):
            messagebox.showinfo('Atenção', 'Este produto contém insumos ou receitas que foram EXCLUÍDOS do sistema.\\n\\nEles aparecerão marcados na lista de composição. Por favor, remova-os ou substitua-os para corrigir o cálculo de custos.', parent=self)
        code = self.prod_tree.item(s[0])['values'][0]
        with db() as c: r = c.execute('SELECT id FROM products WHERE code=?',(code,)).fetchone()
        if r: self.product_form(r['id'])"""

content = content.replace(old_edit_prod, new_edit_prod)

with open('main.py', 'wb') as f:
    f.write(content.encode('utf-8'))
print('Patched edit alerts')
