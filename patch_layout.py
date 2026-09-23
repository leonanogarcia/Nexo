import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# 1. Add Search and Dropdown to recipes_page
old_rec_ui = """        rec_history=RoundedActionButton(bar,'Histórico',lambda: self._run_normal_action(self.rec_tree, self.recipe_history_dialog),width=125,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557'); rec_history.pack(side='left',padx=10)
        _, table_host = self._build_page_table_panel(f)"""
new_rec_ui = """        rec_history=RoundedActionButton(bar,'Histórico',lambda: self._run_normal_action(self.rec_tree, self.recipe_history_dialog),width=125,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557'); rec_history.pack(side='left',padx=10)
        
        self.rec_search = tk.StringVar()
        self.rec_search.trace_add('write', lambda *a: self.refresh_recipes())
        self.rec_search_wrap = self._styled_search_entry(bar, self.rec_search, 280)
        
        self.rec_status = tk.StringVar(value='Ativos')
        self.rec_status.trace_add('write', lambda *a: self.refresh_recipes())
        self.rec_status_wrap = RoundedDropdown(bar, self.rec_status, ['Ativos', 'Inativos', 'Todos'], width=110)
        self.rec_status_wrap.pack(side='right', padx=14)

        _, table_host = self._build_page_table_panel(f)"""
text = text.replace(old_rec_ui, new_rec_ui)

# 2. Add Search and Dropdown to products_page
old_prod_ui = """        prod_history=RoundedActionButton(bar,'Histórico',lambda: self._run_normal_action(self.prod_tree, self.product_history_dialog),width=125,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557'); prod_history.pack(side='left',padx=10)
        _, table_host = self._build_page_table_panel(f)"""
new_prod_ui = """        prod_history=RoundedActionButton(bar,'Histórico',lambda: self._run_normal_action(self.prod_tree, self.product_history_dialog),width=125,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557'); prod_history.pack(side='left',padx=10)
        
        self.prod_search = tk.StringVar()
        self.prod_search.trace_add('write', lambda *a: self.refresh_products())
        self.prod_search_wrap = self._styled_search_entry(bar, self.prod_search, 280)
        
        self.prod_status = tk.StringVar(value='Ativos')
        self.prod_status.trace_add('write', lambda *a: self.refresh_products())
        self.prod_status_wrap = RoundedDropdown(bar, self.prod_status, ['Ativos', 'Inativos', 'Todos'], width=110)
        self.prod_status_wrap.pack(side='right', padx=14)

        _, table_host = self._build_page_table_panel(f)"""
text = text.replace(old_prod_ui, new_prod_ui)


# 3. Modify refresh_recipes
old_ref_rec = """    def refresh_recipes(self):
        if not hasattr(self,'rec_tree'):return
        for x in self.rec_tree.get_children():self.rec_tree.delete(x)
        with db() as c:rows=c.execute('SELECT id,code,name,yield_qty,yield_unit FROM base_recipes WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0 ORDER BY name').fetchall()
        for r in rows:"""
new_ref_rec = """    def refresh_recipes(self):
        if not hasattr(self,'rec_tree'):return
        for x in self.rec_tree.get_children():self.rec_tree.delete(x)
        
        query = '%'+self.rec_search.get().strip()+'%' if hasattr(self,'rec_search') else '%'
        status_filter = self.rec_status.get() if hasattr(self, 'rec_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        
        with db() as c:rows=c.execute(f'SELECT id,code,name,yield_qty,yield_unit,COALESCE(active,1) as active FROM base_recipes WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()
        for r in rows:
            is_active = r['active']"""
text = text.replace(old_ref_rec, new_ref_rec)

# Safe replace for rec_tree.insert
text = re.sub(
    r"(iid=self\.rec_tree\.insert\('','end',text='[^']+',values=\([^)]+\))(\))",
    r"\1, tags=() if is_active else ('inactive',)\2",
    text
)


# 4. Modify refresh_products
old_ref_prod = """    def refresh_products(self):
        if not hasattr(self,'prod_tree'):return
        for x in self.prod_tree.get_children():self.prod_tree.delete(x)
        with db() as c:rows=c.execute('SELECT id,code,name,weight,price FROM products WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0 ORDER BY name').fetchall()
        for r in rows:"""
new_ref_prod = """    def refresh_products(self):
        if not hasattr(self,'prod_tree'):return
        for x in self.prod_tree.get_children():self.prod_tree.delete(x)
        
        query = '%'+self.prod_search.get().strip()+'%' if hasattr(self,'prod_search') else '%'
        status_filter = self.prod_status.get() if hasattr(self, 'prod_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        
        with db() as c:rows=c.execute(f'SELECT id,code,name,weight,price,COALESCE(active,1) as active FROM products WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()
        for r in rows:
            is_active = r['active']"""
text = text.replace(old_ref_prod, new_ref_prod)

# Safe replace for prod_tree.insert
text = re.sub(
    r"(iid=self\.prod_tree\.insert\('','end',text='[^']+',values=\([^)]+\))(\))",
    r"\1, tags=() if is_active else ('inactive',)\2",
    text
)

# 5. Fix _redraw_overlay in RoundedDropdown and the general _redraw_overlay
# Wait, if we added 'inactive' tags, we need to make sure _redraw_overlay processes it!
# In main.py, _redraw_overlay already checks for 'inactive' not in tags! 
# is_active = 'inactive' not in tags
# So we are good!

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched recipes and products layout to include search/filter!")
