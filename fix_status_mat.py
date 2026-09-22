import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add status filter to cadastro bar
code = re.sub(
    r"self\.mat_search=tk\.StringVar\(\); self\.mat_search\.trace_add\('write',lambda \*a:self\.refresh_materials\(\)\)",
    r"self.mat_search=tk.StringVar(); self.mat_search.trace_add('write',lambda *a:self.refresh_materials())\n        self.mat_status=tk.StringVar(value='Ativos'); self.mat_status.trace_add('write',lambda *a:self.refresh_materials())",
    code
)
code = re.sub(
    r"self\.mat_search_wrap=self\._styled_search_entry\(bar,self\.mat_search,22\)",
    r"self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,22)\n        self.mat_status_cb=ttk.Combobox(bar,textvariable=self.mat_status,values=['Ativos','Inativos','Todos'],state='readonly',width=10)\n        self.mat_status_cb.pack(side='right',padx=14)",
    code
)

# 2. Update material tree columns
code = re.sub(
    r"self\.mat_tree=ttk\.Treeview\(table_host,columns=\('code','name','brand','qty','unit','value','category','date','mod_date','edit','delete'\),show='tree'\)",
    r"self.mat_tree=ttk.Treeview(table_host,columns=('code','name','brand','qty','unit','value','category','date','mod_date','status','edit','delete'),show='tree')",
    code
)
code = re.sub(
    r"for k,w in \[\('code',100\),\('name',220\),\('brand',150\),\('qty',110\),\('unit',65\),\('value',100\),\('category',130\),\('date',135\),\('mod_date',135\)\]:",
    r"for k,w in [('code',100),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135),('status',90)]:",
    code
)
code = re.sub(
    r"self\.mat_tree\.column\(k,width=w,anchor='center' if k in \('qty','unit','value','category','date','mod_date'\) else 'w',stretch=False\)",
    r"self.mat_tree.column(k,width=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date','status') else 'w',stretch=False)",
    code
)
code = re.sub(
    r"self\._mat_header_specs=\[\('code','.*?mod_date','.*?tima modifica.*?o',135\),\('edit','',46\),\('delete','',46\)\]",
    r"self._mat_header_specs=[('code','Código',100),('name','Item',220),('brand','Marca',150),('qty','Quantidade',110),('unit','Un.',65),('value','Valor',100),('category','Categoria',130),('date','Data de criação',135),('mod_date','Última modificação',135),('status','Status',90),('edit','',46),('delete','',46)]",
    code
)

# 3. Update refresh_materials
old_refresh_mats = """        with db() as c:
            rows = c.execute('''SELECT 
code,name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,
                                       substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10)
                                FROM materials WHERE COALESCE(active,1)=1 AND (name LIKE ? OR COALESCE(brand,'') LIKE ? OR code LIKE ?) ORDER BY name''', (query,query,query)).fetchall()
        for r in rows:
            r_list = list(r)
            val = r_list[5]
            val_str = f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            r_list[5] = val_str
            self.mat_tree.insert('', 'end', text='?', values=tuple(r_list)+('',''))"""

new_refresh_mats = """        status_filter = self.mat_status.get() if hasattr(self, 'mat_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1" if status_filter == 'Ativos' else ("COALESCE(active,1)=0" if status_filter == 'Inativos' else "1=1")
        with db() as c:
            rows = c.execute(f'''SELECT 
code,name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,
                                       substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10), COALESCE(active,1), id
                                FROM materials WHERE {status_cond} AND (name LIKE ? OR COALESCE(brand,'') LIKE ? OR code LIKE ?) ORDER BY name''', (query,query,query)).fetchall()
        for r in rows:
            r_list = list(r)
            val = r_list[5]
            val_str = f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            r_list[5] = val_str
            is_active = r_list.pop(9)
            mat_id = r_list.pop(9)
            status_str = 'Ativo' if is_active else 'Inativo'
            self.mat_tree.insert('', 'end', iid=str(mat_id), text='?', values=tuple(r_list)+(status_str, '',''))"""

code = code.replace(old_refresh_mats, new_refresh_mats)

# 4. Inactive cannot be edited
code = re.sub(
    r"    def edit_selected_material\(self\):\s*\n\s*s = self\.mat_tree\.selection\(\)\s*\n\s*if not s:\s*\n\s*messagebox\.showwarning\('Cadastro','Selecione um item para editar.', parent=self\); return\s*\n\s*code = self\.mat_tree\.item\(s\[0\]\)\['values'\]\[0\]\s*\n\s*with db\(\) as c: r = c\.execute\('SELECT id FROM materials WHERE code=\?',\(code,\)\)\.fetchone\(\)\s*\n\s*if r: self\.material_form\(r\['id'\]\)",
    r"    def edit_selected_material(self):\n        s = self.mat_tree.selection()\n        if not s:\n            messagebox.showwarning('Cadastro','Selecione um item para editar.', parent=self); return\n        code = self.mat_tree.item(s[0])['values'][0]\n        with db() as c: r = c.execute('SELECT id, active FROM materials WHERE code=?',(code,)).fetchone()\n        if r:\n            if not r['active']:\n                messagebox.showwarning('Item Inativo','Itens inativos nao podem ser editados.', parent=self); return\n            self.material_form(r['id'])",
    code
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
