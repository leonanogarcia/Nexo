import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Fix _attach_row_icon_overlay to FORCE cw0=60
ov_pattern = r"        try: cw0 = int\(tree\.column\('#0', 'width'\)\)\s*except: cw0 = 60"
new_ov = "        cw0 = 60"
text = re.sub(ov_pattern, new_ov, text)

# Add empty overlays to recipes_page and products_page
# In recipes_page
rec_page_pattern = r"self\.rec_icon_ov=self\._attach_row_icon_overlay\(.*?self\.delete_selected_recipe\)"
new_rec_page = """self.rec_icon_ov=self._attach_row_icon_overlay(self.rec_tree, table_host, 6, 7, self.edit_selected_recipe, self.delete_selected_recipe)
        self.rec_empty_overlay = tk.Label(table_host, text='Nenhuma receita cadastrada.\\nClique em + Nova Receita para adicionar a primeira receita.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"""
text = re.sub(rec_page_pattern, new_rec_page, text, flags=re.DOTALL)

# In refresh_recipes
ref_rec_pattern = r"        if hasattr\(self, '_redraw_rec_header'\): self\._redraw_rec_header\(\)"
new_ref_rec = """        if hasattr(self, '_redraw_rec_header'): self._redraw_rec_header()
        if hasattr(self, 'rec_empty_overlay'):
            if rows: self.rec_empty_overlay.place_forget()
            else: self.rec_empty_overlay.place(x=0, y=36, relwidth=1, relheight=1, height=-36)"""
text = re.sub(ref_rec_pattern, new_ref_rec, text, flags=re.DOTALL)

# In products_page
prod_page_pattern = r"self\.prod_icon_ov=self\._attach_row_icon_overlay\(.*?self\.delete_selected_product\)"
new_prod_page = """self.prod_icon_ov=self._attach_row_icon_overlay(self.prod_tree, table_host, 7, 8, self.edit_selected_product, self.delete_selected_product)
        self.prod_empty_overlay = tk.Label(table_host, text='Nenhum produto cadastrado.\\nClique em + Novo Produto para adicionar o primeiro produto.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"""
text = re.sub(prod_page_pattern, new_prod_page, text, flags=re.DOTALL)

# In refresh_products
ref_prod_pattern = r"        if hasattr\(self, '_redraw_prod_header'\): self\._redraw_prod_header\(\)"
new_ref_prod = """        if hasattr(self, '_redraw_prod_header'): self._redraw_prod_header()
        if hasattr(self, 'prod_empty_overlay'):
            if rows: self.prod_empty_overlay.place_forget()
            else: self.prod_empty_overlay.place(x=0, y=36, relwidth=1, relheight=1, height=-36)"""
text = re.sub(ref_prod_pattern, new_ref_prod, text, flags=re.DOTALL)


with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched cw0 to 60 in overlay and added empty watermarks!")
