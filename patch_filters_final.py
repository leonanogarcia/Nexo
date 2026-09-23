import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# 1. Add UI components
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


# 2. Modify DB queries
old_ref_rec = "with db() as c:rows=c.execute('SELECT id,code,name,yield_qty,yield_unit FROM base_recipes WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0 ORDER BY name').fetchall()"
new_ref_rec = """query = '%'+self.rec_search.get().strip()+'%' if hasattr(self,'rec_search') else '%'
        status_filter = self.rec_status.get() if hasattr(self, 'rec_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        with db() as c:rows=c.execute(f'SELECT id,code,name,yield_qty,yield_unit,COALESCE(active,1) as active FROM base_recipes WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()"""
text = text.replace(old_ref_rec, new_ref_rec)

old_ref_prod = "with db() as c:rows=c.execute('SELECT id,code,name,weight_qty,weight_unit,sale_price FROM products WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0 ORDER BY name').fetchall()"
new_ref_prod = """query = '%'+self.prod_search.get().strip()+'%' if hasattr(self,'prod_search') else '%'
        status_filter = self.prod_status.get() if hasattr(self, 'prod_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        with db() as c:rows=c.execute(f'SELECT id,code,name,weight_qty,weight_unit,sale_price,COALESCE(active,1) as active FROM products WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()"""
text = text.replace(old_ref_prod, new_ref_prod)


# 3. Insert tags accurately using exact strings
# For Recipes:
old_rec_insert = "iid=self.rec_tree.insert('','end',text='☐',values=(r['code'],name_disp,fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'✏️','🗑️'))"
new_rec_insert = "is_active = r['active']\n            iid=self.rec_tree.insert('','end',text='☐',values=(r['code'],name_disp,fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'✏️','🗑️'), tags=() if is_active else ('inactive',))"
text = text.replace(old_rec_insert, new_rec_insert)

# For Products:
old_prod_insert = "iid=self.prod_tree.insert('','end',text='☐',values=(r['code'],name_disp,(fmt_num(r['weight_qty'])+' '+str(r['weight_unit'] or '')).strip() or '-',fmt(cost),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-','✏️','🗑️'))"
new_prod_insert = "is_active = r['active']\n            iid=self.prod_tree.insert('','end',text='☐',values=(r['code'],name_disp,(fmt_num(r['weight_qty'])+' '+str(r['weight_unit'] or '')).strip() or '-',fmt(cost),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-','✏️','🗑️'), tags=() if is_active else ('inactive',))"
text = text.replace(old_prod_insert, new_prod_insert)

# 4. Add overlay redraws
text = text.replace("self._reset_checked(self.rec_tree)", "self._reset_checked(self.rec_tree)\n        if hasattr(self, 'rec_icon_ov'): self.rec_icon_ov._redraw()")
text = text.replace("self._reset_checked(self.prod_tree)", "self._reset_checked(self.prod_tree)\n        if hasattr(self, 'prod_icon_ov'): self.prod_icon_ov._redraw()")


with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Everything patched safely!")
