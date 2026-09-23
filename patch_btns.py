import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Fix recipes_page buttons
old_rec_btn = """        rec_add=RoundedActionButton(bar,'＋ Nova Receita',lambda: self._run_normal_action(self.rec_tree, self.new_recipe),width=150,height=40,fill='#F28C28',hover='#D96F0B')
        rec_add.pack(side='left')
        
        self.rec_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self.delete_selected_recipes(), width=95, height=40, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030')
        
        rec_import=RoundedActionButton(bar,'Importar Word/PDF',lambda: self._run_normal_action(self.rec_tree, self.import_recipe_document),width=155,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557')
        rec_import.pack(side='left',padx=10)
        
        rec_export=RoundedActionButton(bar,'Exportar Receita',lambda: self._run_normal_action(self.rec_tree, self.export_selected_recipe),width=145,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557')
        rec_export.pack(side='left',padx=10)
        
        rec_original=RoundedActionButton(bar,'Documento original',lambda: self._run_normal_action(self.rec_tree, self.open_original_document),width=165,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557')
        rec_original.pack(side='left',padx=10)
        
        rec_history=RoundedActionButton(bar,'Histórico',lambda: self._run_normal_action(self.rec_tree, self.recipe_history_dialog),width=125,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557')
        rec_history.pack(side='left',padx=10)"""

new_rec_btn = """        rec_add=RoundedActionButton(bar, '+ Nova Receita', lambda: self._run_normal_action(self.rec_tree, self.new_recipe), width=130, height=49, fill='#F28C28', hover='#D96F0B')
        rec_add.pack(side='left')
        
        self.rec_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self.delete_selected_recipes(), width=95, height=40, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030')
        
        rec_import=RoundedActionButton(bar, 'Importar', lambda: self._run_normal_action(self.rec_tree, self.import_recipe_document), width=95, height=49, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        rec_import.pack(side='left', padx=(8, 0))
        
        rec_export=RoundedActionButton(bar, 'Exportar', lambda: self._run_normal_action(self.rec_tree, self.export_selected_recipe), width=95, height=49, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        rec_export.pack(side='left', padx=(8, 0))
        
        rec_original=RoundedActionButton(bar, 'Doc. Original', lambda: self._run_normal_action(self.rec_tree, self.open_original_document), width=120, height=49, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        rec_original.pack(side='left', padx=(8, 0))
        
        rec_history=RoundedActionButton(bar, '<clock> Histórico', lambda: self._run_normal_action(self.rec_tree, self.recipe_history_dialog), width=120, height=49, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        rec_history.pack(side='left', padx=(8, 0))"""
text = text.replace(old_rec_btn, new_rec_btn)


# Fix products_page buttons
old_prod_btn = """        prod_add=RoundedActionButton(bar,'＋ Novo Produto',lambda: self._run_normal_action(self.prod_tree, self.new_product),width=150,height=40,fill='#F28C28',hover='#D96F0B')
        prod_add.pack(side='left')
        
        self.prod_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self.delete_selected_products(), width=95, height=40, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030')
        
        prod_history=RoundedActionButton(bar,'Histórico',lambda: self._run_normal_action(self.prod_tree, self.product_history_dialog),width=125,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557')
        prod_history.pack(side='left',padx=10)"""

new_prod_btn = """        prod_add=RoundedActionButton(bar, '+ Novo Produto', lambda: self._run_normal_action(self.prod_tree, self.new_product), width=135, height=49, fill='#F28C28', hover='#D96F0B')
        prod_add.pack(side='left')
        
        self.prod_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self.delete_selected_products(), width=95, height=40, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030')
        
        prod_history=RoundedActionButton(bar, '<clock> Histórico', lambda: self._run_normal_action(self.prod_tree, self.product_history_dialog), width=120, height=49, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        prod_history.pack(side='left', padx=(8, 0))"""
text = text.replace(old_prod_btn, new_prod_btn)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched button sizes and spacing.")
