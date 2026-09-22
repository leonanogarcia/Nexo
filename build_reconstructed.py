import re

with open('missing_block.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add _setup_canvas_header_drag after _styled_search_entry
header_drag_code = """
    def _setup_canvas_header_drag(self, canvas, tree, fixed_cols, redraw_cmd, state_key):
        canvas._drag_col = None
        canvas._drag_start_x = 0
        canvas._drag_start_w = 0
        def get_col_edge(x):
            cx = 0; cols = ['#0'] + list(tree['columns'])
            for col in cols:
                cw = int(tree.column(col, 'width'))
                cx += cw
                if abs(x - cx) < 8: return col
            return None
        def on_press(e):
            col = get_col_edge(e.x)
            if col and col not in fixed_cols:
                canvas._drag_col = col; canvas._drag_start_x = e.x
                canvas._drag_start_w = int(tree.column(col, 'width'))
                setattr(self, f'_{state_key}_user_resized', True)
        def on_drag(e):
            if canvas._drag_col:
                delta = e.x - canvas._drag_start_x
                new_w = max(40, canvas._drag_start_w + delta)
                tree.column(canvas._drag_col, width=new_w)
                redraw_cmd()
        def on_motion(e):
            canvas.config(cursor='sb_h_double_arrow' if get_col_edge(e.x) and get_col_edge(e.x) not in fixed_cols else 'arrow')
        def on_double_click(e):
            col = get_col_edge(e.x)
            if col and col not in fixed_cols:
                setattr(self, f'_{state_key}_user_resized', False)
                self.winfo_toplevel().event_generate('<Configure>')
        canvas.bind('<Button-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<Motion>', on_motion)
        canvas.bind('<Double-Button-1>', on_double_click)
"""
code = code.replace("    def cadastro(self, f):", header_drag_code + "\n    def cadastro(self, f):")

# 2. Fix the Capsule Dropdown in cadastro
new_status_cb = """
        # Custom Capsule Filter Dropdown
        self.mat_status = tk.StringVar(value='Ativos')
        self.mat_status_wrap = tk.Canvas(bar, bg=self.colors['panel'], bd=0, highlightthickness=0, width=110, height=40, cursor='hand2')
        self.mat_status_wrap.pack(side='right', padx=14)
        def _draw_status(text):
            self.mat_status_wrap.delete('all')
            self.mat_status_wrap.create_polygon(20, 1, 90, 1, 109, 1, 109, 20, 109, 39, 90, 39, 20, 39, 1, 39, 1, 20, 1, 1, smooth=True, fill=self.colors['panel'], outline=self.colors['border'])
            self.mat_status_wrap.create_text(45, 20, text=text, fill=self.colors['text'], font=('Segoe UI', 10, 'bold'), anchor='center')
            self.mat_status_wrap.create_text(90, 20, text='▼', fill=self.colors['muted'], font=('Segoe UI', 8), anchor='center')
        
        _draw_status(self.mat_status.get())
        
        def _open_status_menu(e):
            m = tk.Menu(self.winfo_toplevel(), tearoff=0, bg=self.colors['panel'], fg=self.colors['text'], font=('Segoe UI', 10), activebackground=self.colors['accent_soft'], activeforeground=self.colors['accent'], bd=1)
            for opt in ['Ativos', 'Inativos', 'Todos']:
                m.add_command(label=opt, command=lambda o=opt: (self.mat_status.set(o), _draw_status(o), self.refresh_all()))
            m.post(e.x_root, e.y_root)
            
        self.mat_status_wrap.bind('<Button-1>', _open_status_menu)
"""
# Find `self.mat_search_wrap = self._styled_search_entry` and insert before it
code = code.replace("        self.mat_search_wrap = self._styled_search_entry", new_status_cb + "\n        self.mat_search_wrap = self._styled_search_entry")

# 3. Update mat_tree columns and widths
old_tree = "        self.mat_tree=ttk.Treeview(table_host,columns=('code','name','brand','qty','unit','value','category','date','edit','delete'),show='tree')"
new_tree = "        self.mat_tree=ttk.Treeview(table_host,columns=('code','name','brand','qty','unit','value','category','date','mod_date','status','edit','delete','options'),show='tree')\n        self.mat_tree.tag_configure('inactive', foreground='#9AA9BF')"
code = code.replace(old_tree, new_tree)

# Update column width assignments
old_widths = "for k,w in [('code',100),('name',250),('brand',150),('qty',120),('unit',80),('value',120),('category',150),('date',150)]:\n            self.mat_tree.column(k,width=w,minwidth=w)"
new_widths = "for k,w in [('code',100),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135),('status',90)]:\n            self.mat_tree.column(k,width=w,minwidth=w)"
code = code.replace(old_widths, new_widths)

# Update header specs
old_specs = "self._mat_header_specs=[('code','Código',100),('name','Item',250),('brand','Marca',150),('qty','Quantidade',120),('unit','Un.',80),('value','Valor',120),('category','Categoria',150),('date','Último cadastro',150),('edit','',46),('delete','',46)]"
new_specs = "self._mat_header_specs=[('code','Código',100),('name','Item',220),('brand','Marca',150),('qty','Quantidade',110),('unit','Un.',65),('value','Valor',100),('category','Categoria',130),('date','Data de criação',135),('mod_date','Última modificação',135),('status','Status',90),('edit','',40),('delete','',40),('options','',40)]"
code = code.replace(old_specs, new_specs)

# 4. _bulk_delete_list replacement logic
code = code.replace("if not messagebox.askyesno('Excluir itens',f'Excluir {len(rows)} itens selecionados?',parent=self):return", "")
code = code.replace("with db() as c:\n            for r in rows:c.execute(f'DELETE FROM {table} WHERE id=?',(r['id'],))", "")
code = code.replace("self.refresh_all();self.notify(f'{len(rows)} itens excluídos com sucesso.')", """
        linked = []
        unlinked = []
        for r in rows:
            refs = 0
            with db() as c:
                if kind == 'material':
                    refs = c.execute('SELECT COUNT(*) n FROM base_recipe_ingredients WHERE material_id=?',(r['id'],)).fetchone()['n']
                    refs += c.execute('SELECT COUNT(*) n FROM purchases WHERE material_id=?',(r['id'],)).fetchone()['n']
                elif kind == 'recipe':
                    refs = c.execute('SELECT COUNT(*) n FROM product_components WHERE recipe_id=?',(r['id'],)).fetchone()['n']
                elif kind == 'product':
                    refs = c.execute('SELECT COUNT(*) n FROM sales WHERE product_id=?',(r['id'],)).fetchone()['n']
            if refs: linked.append(r)
            else: unlinked.append(r)
        
        if not linked and not unlinked: return
        
        msg = f'Voce selecionou {len(rows)} itens.\\n'
        if linked:
            msg += f'\\n{len(linked)} itens possuem vinculos/historico e serao apenas INATIVADOS.\\n'
        if unlinked:
            msg += f'\\nOs outros {len(unlinked)} itens sem vinculos serao EXCLUIDOS.\\n'
            
        msg += '\\nDeseja prosseguir com a operacao conjunta? Se escolher Nao, TUDO sera cancelado.'
            
        if not messagebox.askyesno('Confirmar operacao em lote', msg, parent=self): return
        
        with db() as c:
            for r in unlinked:
                c.execute(f'DELETE FROM {table} WHERE id=?',(r['id'],))
            for r in linked:
                c.execute(f'UPDATE {table} SET active=0, updated_at=? WHERE id=?', (now_iso(), r['id']))
                
        self.refresh_all()
        self.notify(f'{len(unlinked)} excluidos, {len(linked)} inativados.')
""")

# 5. delete_selected_material logic
code = code.replace("""if refs:
            messagebox.showwarning('Insumo em uso','Este Insumo está vinculado a Receitas ou Compras.\\nNão pode ser excluído.',parent=self)
            return
        if messagebox.askyesno('Excluir Insumo',f'Excluir o Insumo "{r["name"]}"?',parent=self):
            with db() as c:c.execute('DELETE FROM materials WHERE id=?',(r['id'],))
            self.refresh_all();self.notify('Insumo excluído.')""", """if refs:
            if messagebox.askyesno('Insumo vinculado','Este Insumo possui historico ou vinculos.\\nDeseja inativa-lo? (Se escolher Nao, a operacao e cancelada)',parent=self):
                with db() as c:c.execute('UPDATE materials SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Insumo inativado com sucesso.')
            return
        if messagebox.askyesno('Excluir Insumo',f'Excluir o Insumo "{r["name"]}"?',parent=self):
            with db() as c:c.execute('DELETE FROM materials WHERE id=?',(r['id'],))
            self.refresh_all();self.notify('Insumo excluído.')""")

with open('reconstructed_block.py', 'w', encoding='utf-8') as f:
    f.write(code)
