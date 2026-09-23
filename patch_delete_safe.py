with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Fix delete buttons exactly
old_mat = "self.mat_bulk_delete_btn=RoundedActionButton(bar, '🗑️ Excluir', lambda: self._run_normal_action(self.mat_tree, self.delete_selected_materials), width=120, height=40, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')"
new_mat = "self.mat_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self._run_normal_action(self.mat_tree, self.delete_selected_materials), width=110, height=40, fill='#FEF2F2', hover='#FEE2E2', fg='#991B1B')"
if old_mat in text: text = text.replace(old_mat, new_mat)

old_rec = "self.rec_bulk_delete_btn=RoundedActionButton(bar, '🗑️ Excluir', lambda: self._run_normal_action(self.rec_tree, self.delete_selected_recipes), width=120, height=40, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')"
new_rec = "self.rec_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self._run_normal_action(self.rec_tree, self.delete_selected_recipes), width=110, height=40, fill='#FEF2F2', hover='#FEE2E2', fg='#991B1B')"
if old_rec in text: text = text.replace(old_rec, new_rec)

old_prod = "self.prod_bulk_delete_btn=RoundedActionButton(bar, '🗑️ Excluir', lambda: self._run_normal_action(self.prod_tree, self.delete_selected_products), width=120, height=40, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')"
new_prod = "self.prod_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self._run_normal_action(self.prod_tree, self.delete_selected_products), width=110, height=40, fill='#FEF2F2', hover='#FEE2E2', fg='#991B1B')"
if old_prod in text: text = text.replace(old_prod, new_prod)

old_convert = """                elif icon=='convert':
                    line([cx-8*scale, c_y-3*scale, cx+6*scale, c_y-3*scale])
                    line([cx+3*scale, c_y-6*scale, cx+6*scale, c_y-3*scale, cx+3*scale, c_y])
                    line([cx+8*scale, c_y+3*scale, cx-6*scale, c_y+3*scale])
                    line([cx-3*scale, c_y, cx-6*scale, c_y+3*scale, cx-3*scale, c_y+6*scale])"""

new_delete = """                elif icon=='convert':
                    line([cx-8*scale, c_y-3*scale, cx+6*scale, c_y-3*scale])
                    line([cx+3*scale, c_y-6*scale, cx+6*scale, c_y-3*scale, cx+3*scale, c_y])
                    line([cx+8*scale, c_y+3*scale, cx-6*scale, c_y+3*scale])
                    line([cx-3*scale, c_y, cx-6*scale, c_y+3*scale, cx-3*scale, c_y+6*scale])
                elif icon=='delete':
                    line([cx-5*scale, c_y-5*scale, cx+5*scale, c_y-5*scale])
                    line([cx-2*scale, c_y-7*scale, cx+2*scale, c_y-7*scale])
                    line([cx-4*scale, c_y-4*scale, cx-3*scale, c_y+6*scale])
                    line([cx+4*scale, c_y-4*scale, cx+3*scale, c_y+6*scale])
                    line([cx-3*scale, c_y+6*scale, cx+3*scale, c_y+6*scale])
                    line([cx-1*scale, c_y-2*scale, cx-0.5*scale, c_y+4*scale])
                    line([cx+1*scale, c_y-2*scale, cx+0.5*scale, c_y+4*scale])"""

if old_convert in text:
    text = text.replace(old_convert, new_delete)
    
with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Safe patch applied")
