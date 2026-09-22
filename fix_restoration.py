import re
import shutil

# 1. Restore from zip extract
shutil.copy(r'D:\Nexo\temp_extract\Nexo_v0_7_13\main.py', 'main.py')

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# fix_the_mess.py
new_cadastro = """    def cadastro(self, f):
        _, bar = self._build_page_toolbar(f)
        
        mat_add=RoundedActionButton(bar, '+ Novo item', lambda: self._run_normal_action(self.mat_tree, self.new_material), width=130, height=49, fill='#2F67B1', hover='#255894')
        mat_add.pack(side='left')
        
        mat_history=RoundedActionButton(bar, '🕒 Histórico', lambda: self._run_normal_action(self.mat_tree, self.material_history_dialog), width=120, height=49, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        mat_history.pack(side='left', padx=(8, 0))
        
        self.mat_bulk_delete_btn=RoundedActionButton(bar, '🗑 Excluir', lambda: self._run_normal_action(self.mat_tree, self.delete_selected_materials), width=120, height=49, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')
        
        self.mat_search=tk.StringVar(); self.mat_search.trace_add('write',lambda *a:self.refresh_materials())
        
        # Pílula Status
        self.mat_status = tk.StringVar(value='Ativos')
        self.mat_status_wrap = tk.Canvas(bar, bg=self.colors['panel'], bd=0, highlightthickness=0, width=110, height=40, cursor='hand2')
        self.mat_status_wrap.pack(side='right', padx=14)
        def _draw_status(text):
            self.mat_status_wrap.delete('all')
            w = 110; h = 40
            self.mat_status_wrap.create_arc(2, 2, 38, 38, start=90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='pieslice')
            self.mat_status_wrap.create_arc(2, 2, 38, 38, start=90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='arc')
            self.mat_status_wrap.create_arc(w-38, 2, w-2, 38, start=-90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='pieslice')
            self.mat_status_wrap.create_arc(w-38, 2, w-2, 38, start=-90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='arc')
            self.mat_status_wrap.create_rectangle(20, 2, w-20, 38, fill='#FFFFFF', outline='')
            self.mat_status_wrap.create_line(20, 2, w-20, 2, fill='#E2EAF5')
            self.mat_status_wrap.create_line(20, 38, w-20, 38, fill='#E2EAF5')
            self.mat_status_wrap.create_text(45, 20, text=text, fill=self.colors['text'], font=('Segoe UI', 10, 'bold'), anchor='center')
            self.mat_status_wrap.create_text(90, 20, text='▼', fill=self.colors['muted'], font=('Segoe UI', 8), anchor='center')
        
        _draw_status(self.mat_status.get())
        
        def _open_status_menu(e):
            m = tk.Menu(self.winfo_toplevel(), tearoff=0, bg=self.colors['panel'], fg=self.colors['text'], font=('Segoe UI', 10), activebackground=self.colors['accent_soft'], activeforeground=self.colors['accent'], bd=1)
            for opt in ['Ativos', 'Inativos', 'Todos']:
                m.add_command(label=opt, command=lambda o=opt: (self.mat_status.set(o), _draw_status(o), self.refresh_materials()))
            m.post(e.x_root, e.y_root)
            
        self.mat_status_wrap.bind('<Button-1>', _open_status_menu)
        
        self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,22)

        _,table_host=self._build_page_table_panel(f)
        
        self.mat_header=tk.Canvas(table_host,bg=self.colors['panel'],bd=0,highlightthickness=0,height=36)
        self.mat_header.pack(fill='x',padx=2,pady=(0,0))
        
        self.mat_tree=ttk.Treeview(table_host,columns=('code','name','brand','qty','unit','value','category','date','mod_date','status','edit','delete','options'),show='tree')
        self.mat_tree.tag_configure('inactive', foreground='#9AA9BF')
        self.mat_tree.column('#0',width=60,minwidth=60,stretch=False)
        
        for k,w in [('code',100),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135),('status',90),('edit',40),('delete',40),('options',40)]:
            self.mat_tree.column(k,width=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date','status') else 'w',stretch=(k=='name'))
            
        self.mat_hsb = PillScrollbar(table_host, self.mat_tree)
        self.mat_tree.pack(fill='both',expand=True)

        self._mat_header_specs=[('code','Código',100),('name','Item',220),('brand','Marca',150),('qty','Quantidade',110),('unit','Un.',65),('value','Valor',100),('category','Categoria',130),('date','Data de criação',135),('mod_date','Última modificação',135),('status','Status',90),('edit','',40),('delete','',40),('options','',40)]
        self._mat_header_imgs={}
        
        def redraw_mat_header(_event=None):
            c=self.mat_header; c.delete('all')
            w=max(c.winfo_width(),2); h=max(c.winfo_height(),2)
            r=min(h/2,18); fill='#EEF4FB'
            c.create_rectangle(r,0,w-r,h,fill=fill,outline='')
            c.create_rectangle(0,r,w,h-r,fill=fill,outline='')
            c.create_arc(0,0,2*r,2*r,start=90,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,0,w,2*r,start=0,extent=90,fill=fill,outline=fill)
            c.create_arc(0,h-2*r,2*r,h,start=180,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,h-2*r,w,h,start=270,extent=90,fill=fill,outline=fill)
            x0=0
            cols=[('#0','')]+[(f'#{i}',txt) for i,(key,txt, _) in enumerate(self._mat_header_specs,1)]
            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.mat_tree.column(col,'width'))
                except Exception: cw=0
                if col=='#0':
                    x0+=cw; continue
                if col=='#11':
                    img=self._mat_header_imgs.get('edit')
                    if img: c.create_image(x0+cw/2,h/2,image=img,anchor='center')
                elif col=='#12':
                    img=self._mat_header_imgs.get('delete')
                    if img: c.create_image(x0+cw/2,h/2,image=img,anchor='center')
                elif col=='#13':
                    pass
                else:
                    align = 'w' if col in ('#1', '#2', '#3') else 'center'
                    anchor_x = x0+12 if align == 'w' else x0+cw/2
                    c.create_text(anchor_x,h/2,text=txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor=align)
                
                if col not in ('#0', '#11', '#12', '#13'):
                    c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                x0+=cw
        self._redraw_mat_header=redraw_mat_header
        self.mat_header.bind('<Configure>',redraw_mat_header)
        self.mat_tree.bind('<Configure>',lambda e:redraw_mat_header())
        self.after_idle(redraw_mat_header)
        
        self._setup_canvas_header_drag(self.mat_header, self.mat_tree, ['edit','delete','options'], redraw_mat_header, 'mat')

        self.mat_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.mat_tree,'material'))
        self.mat_tree.bind('<Double-1>',lambda e:self.edit_selected_material())
        
        self.mat_icon_ov=self._attach_row_icon_overlay(
            self.mat_tree, table_host, 10, 11,
            self.edit_selected_material, self.delete_selected_material)
            
        self._action_buttons[self.mat_tree]={'normal':[mat_add,mat_history],'bulk':[self.mat_bulk_delete_btn]}
        self.mat_empty_overlay = tk.Label(table_host, text='Nenhum insumo encontrado.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"""

code = re.sub(r"    def cadastro\(self, f\):.*?def material_form\(self, edit_id=None\):", new_cadastro + "\n\n    def material_form(self, edit_id=None):", code, flags=re.DOTALL)


# fix_search.py
old_search = """    def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)
        wrap.pack(side='left',padx=(14,0))
        return wrap.entry"""
new_search = """    def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)
        wrap.pack(side='right',padx=(14,0),fill='none',expand=False)
        return wrap"""
code = code.replace(old_search, new_search)

# Add PillScrollbar class
pill_scrollbar_class = """class PillScrollbar(tk.Canvas):
    def __init__(self, parent, tree, **kwargs):
        super().__init__(parent, height=8, bg=parent.cget('bg'), bd=0, highlightthickness=0, **kwargs)
        self.tree = tree
        self.tree.configure(xscrollcommand=self.set_scroll)
        self.bind('<Configure>', self._redraw)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self._pos = (0.0, 1.0)
        self._drag_data = {'x': 0, 'start_pos': 0.0}

    def set_scroll(self, first, last):
        first, last = float(first), float(last)
        self._pos = (first, last)
        if first == 0.0 and last == 1.0:
            self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side='bottom', fill='x', pady=(0, 4), padx=12)
        self._redraw()

    def _redraw(self, e=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10: return
        self.delete('all')
        first, last = self._pos
        x1 = first * w
        x2 = last * w
        r = h / 2
        fill = '#333333'
        self.create_arc(x1, 0, x1+2*r, h, start=90, extent=180, fill=fill, outline='')
        self.create_arc(x2-2*r, 0, x2, h, start=-90, extent=180, fill=fill, outline='')
        self.create_rectangle(x1+r, 0, x2-r, h, fill=fill, outline='')

    def _on_press(self, e):
        w = self.winfo_width()
        first, last = self._pos
        x1 = first * w
        x2 = last * w
        if x1 <= e.x <= x2:
            self._drag_data['x'] = e.x
            self._drag_data['start_pos'] = first
        else:
            new_first = max(0.0, min(1.0 - (last-first), (e.x / w) - (last-first)/2))
            self.tree.xview_moveto(new_first)

    def _on_drag(self, e):
        w = self.winfo_width()
        dx = e.x - self._drag_data['x']
        first, last = self._pos
        delta_pos = dx / w
        new_first = max(0.0, min(1.0 - (last-first), self._drag_data['start_pos'] + delta_pos))
        self.tree.xview_moveto(new_first)

"""
code = code.replace("class RoundedActionButton", pill_scrollbar_class + "class RoundedActionButton")

# fix_icons.py + fix_icons_and_bulk.py (RoundedActionButton text cleaner)
code = re.sub(r"    def _detect_icon\(self,text\):.*?return ' '\.join\(text\.split\(\)\)", """    def _detect_icon(self,text):
        if '+' in text: return 'plus'
        if '🕒' in text or 'clock' in text.lower(): return 'clock'
        if '🔄' in text: return 'convert'
        if '🗑' in text or 'delete' in text.lower(): return 'delete'
        return None

    def _clean_text(self,text):
        for token in ('+', '🕒', '🔄', '🗑', '<', '-', '"', 'Y-'):
            text = text.replace(token, '')
        return ' '.join(text.split())""", code, flags=re.DOTALL)

# RoundedEntry placeholder color
code = code.replace("fg='#9AA9BF',font=('Segoe UI',10)", "fg='#60769D',font=('Segoe UI',10)")


# Add PillScrollbar to recipes_page and products_page
code = code.replace("self.rec_search_wrap=self._styled_search_entry(bar,self.rec_search,58)\n        self.rec_search_wrap.pack_configure(side='left',padx=(14,0),fill='x',expand=True)", "self.rec_search_wrap=self._styled_search_entry(bar,self.rec_search,58)\n        self.rec_search_wrap.pack_configure(side='left',padx=(14,0),fill='x',expand=True)")
# Wait, for recipes/products, search wrap uses wrap.pack_configure which works now.

old_rec_col = """        for k, w in [('code',95),('name',280),('yield',120),('unit',65),('cost',120)]:
            self.rec_tree.column(k,width=w,anchor='center' if k in ('yield','unit','cost') else 'w',stretch=False)
        for k in ('edit','delete','options'):
            self.rec_tree.column(k,width=40,anchor='center',stretch=False)
        self.rec_tree.pack(fill='both',expand=True)"""
new_rec_col = """        for k, w in [('code',95),('name',280),('yield',120),('unit',65),('cost',120)]:
            self.rec_tree.column(k,width=w,anchor='center' if k in ('yield','unit','cost') else 'w',stretch=(k=='name'))
        for k in ('edit','delete','options'):
            self.rec_tree.column(k,width=40,anchor='center',stretch=False)
        self.rec_hsb = PillScrollbar(table_host, self.rec_tree)
        self.rec_tree.pack(fill='both',expand=True)"""
code = code.replace(old_rec_col, new_rec_col)

old_prod_col = """        for k, w in [('code',95),('name',280),('weight',140),('cost',120),('price',120),('margin',100)]:
            self.prod_tree.column(k,width=w,anchor='center' if k in ('weight','cost','price','margin') else 'w',stretch=False)
        for k in ('edit','delete','options'):
            self.prod_tree.column(k,width=40,anchor='center',stretch=False)
        self.prod_tree.pack(fill='both',expand=True)"""
new_prod_col = """        for k, w in [('code',95),('name',280),('weight',140),('cost',120),('price',120),('margin',100)]:
            self.prod_tree.column(k,width=w,anchor='center' if k in ('weight','cost','price','margin') else 'w',stretch=(k=='name'))
        for k in ('edit','delete','options'):
            self.prod_tree.column(k,width=40,anchor='center',stretch=False)
        self.prod_hsb = PillScrollbar(table_host, self.prod_tree)
        self.prod_tree.pack(fill='both',expand=True)"""
code = code.replace(old_prod_col, new_prod_col)


# fix_deletions.py
new_delete_mat = """    def delete_selected_material(self):
        s=self.mat_tree.selection()
        if not s or self._selection_count(self.mat_tree)!=1:return
        code=self.mat_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM materials WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:
            refs=(c.execute('SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?',(r['id'],)).fetchone()['n']
                  + c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",(r['id'],)).fetchone()['n'])
        if refs:
            if messagebox.askyesno('Insumo vinculado', 'Este Insumo possui vínculos em receitas/produtos. Deseja inativá-lo em vez de excluir?', parent=self):
                with db() as c:c.execute('UPDATE materials SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Insumo inativado com sucesso.')
            return
        if not messagebox.askyesno('Excluir Insumo', f'Excluir "{r["name"]}"? O histórico de compras e custos também será removido.', parent=self):return
        with db() as c:
            c.execute('DELETE FROM purchases WHERE material_id=?', (r['id'],))
            c.execute("DELETE FROM cost_history WHERE entity_type='MATERIAL' AND entity_id=?", (r['id'],))
            c.execute('DELETE FROM custom_units WHERE material_id=?', (r['id'],))
            c.execute('DELETE FROM materials WHERE id=?', (r['id'],))
        self.refresh_all();self.notify('Insumo excluído com sucesso.')"""
code = re.sub(r"    def delete_selected_material\(self\):.*?self\.notify\('Insumo exclu..?do com sucesso\.'\)", new_delete_mat, code, flags=re.DOTALL)

new_del_rec = """    def delete_selected_recipe(self):
        s=self.rec_tree.selection()
        if not s or self._selection_count(self.rec_tree)!=1:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM base_recipes WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:refs=c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='RECIPE_BASE' AND ref_id=?",(r['id'],)).fetchone()['n']
        if refs:
            if messagebox.askyesno('Receita vinculada','Esta Receita Base é usada em Produtos. Deseja inativá-la em vez de excluir?',parent=self):
                with db() as c:c.execute('UPDATE base_recipes SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Receita inativada com sucesso.')
            return
        if not messagebox.askyesno('Excluir Receita',f'Excluir permanentemente "{r["name"]}"?',parent=self):return
        with db() as c:
            c.execute("DELETE FROM cost_history WHERE entity_type='RECIPE_BASE' AND entity_id=?", (r['id'],))
            c.execute('DELETE FROM base_recipes WHERE id=?',(r['id'],))
        self.refresh_all();self.notify('Receita excluída com sucesso.')"""
code = re.sub(r"    def delete_selected_recipe\(self\):.*?self\.notify\('Receita exclu..?da com sucesso\.'\)", new_del_rec, code, flags=re.DOTALL)

new_del_prod = """    def delete_selected_product(self):
        s=self.prod_tree.selection()
        if not s or self._selection_count(self.prod_tree)!=1:return
        code=self.prod_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM products WHERE code=?',(code,)).fetchone()
        if not r:return
        if not messagebox.askyesno('Excluir Produto',f'Excluir permanentemente "{r["name"]}"?',parent=self):return
        with db() as c:
            c.execute("DELETE FROM cost_history WHERE entity_type='PRODUCT' AND entity_id=?", (r['id'],))
            c.execute('DELETE FROM products WHERE id=?',(r['id'],))
        self.refresh_all();self.notify('Produto excluído com sucesso.')"""
code = re.sub(r"    def delete_selected_product\(self\):.*?self\.notify\('Produto exclu..?do com sucesso\.'\)", new_del_prod, code, flags=re.DOTALL)

# Bulk delete fix syntax error!
new_bulk_delete = """    def _bulk_delete_list(self, tree, kind):
        checked=getattr(self,'_checked_rows',{}).get(str(tree),set())
        if len(checked)<2: return
        table={'material':'materials','recipe':'base_recipes','product':'products'}[kind]
        rows=[]
        with db() as c:
            for iid in checked:
                vals=tree.item(iid,'values'); code=vals[0] if vals else ''
                r=c.execute(f'SELECT id,name FROM {table} WHERE code=?',(code,)).fetchone()
                if r: rows.append(r)
        if not rows:return
        
        linked = []
        unlinked = []
        with db() as c:
            for r in rows:
                if kind == 'material':
                    refs = c.execute('SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?',(r['id'],)).fetchone()['n']
                    refs += c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",(r['id'],)).fetchone()['n']
                elif kind == 'recipe':
                    refs = c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='RECIPE_BASE' AND ref_id=?",(r['id'],)).fetchone()['n']
                elif kind == 'product':
                    refs = 0
                if refs > 0: linked.append(r)
                else: unlinked.append(r)
        
        msg = f'Você selecionou {len(rows)} itens.\\n'
        if linked:
            msg += f'\\n{len(linked)} itens possuem vínculos/dependências e serão INATIVADOS:\\n'
            msg += '\\n'.join('  - ' + r['name'] for r in linked) + '\\n'
        if unlinked:
            msg += f'\\nOs outros {len(unlinked)} itens (sem vínculos) serão EXCLUÍDOS permanentemente.\\n'
            
        msg += '\\nDeseja prosseguir? (Se escolher Não, toda a operação será cancelada).'
            
        if not messagebox.askyesno('Confirmar exclusão em lote', msg, parent=self): return
        
        with db() as c:
            for r in unlinked:
                if kind == 'material':
                    c.execute('DELETE FROM purchases WHERE material_id=?', (r['id'],))
                    c.execute("DELETE FROM cost_history WHERE entity_type='MATERIAL' AND entity_id=?", (r['id'],))
                    c.execute('DELETE FROM custom_units WHERE material_id=?', (r['id'],))
                elif kind == 'recipe':
                    c.execute("DELETE FROM cost_history WHERE entity_type='RECIPE_BASE' AND entity_id=?", (r['id'],))
                elif kind == 'product':
                    c.execute("DELETE FROM cost_history WHERE entity_type='PRODUCT' AND entity_id=?", (r['id'],))
                c.execute(f'DELETE FROM {table} WHERE id=?',(r['id'],))
            
            for r in linked:
                c.execute(f'UPDATE {table} SET active=0, updated_at=? WHERE id=?', (now_iso(), r['id']))
                
        self.refresh_all()
        self.notify(f'{len(unlinked)} excluídos, {len(linked)} inativados.')"""

code = re.sub(r"    def _bulk_delete_list\(self, tree, kind\):.*?self\.notify\(f'\{len\(rows\)\} itens exclu..?dos com sucesso\.'\)", new_bulk_delete, code, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
