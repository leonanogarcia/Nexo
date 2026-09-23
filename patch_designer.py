import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# --- RECIPES PAGE REPLACEMENT ---
rec_page_pattern = r"    def recipes_page\(self, f\):.*?def recipe_form\(self, edit_id=None, imported_items=None, imported_source=None\):"
new_rec_page = """    def recipes_page(self, f):
        _, bar=self._build_page_toolbar(f)
        
        rec_add=RoundedActionButton(bar,'＋ Nova Receita',lambda: self._run_normal_action(self.rec_tree, self.new_recipe),width=150,height=40,fill='#F28C28',hover='#D96F0B')
        rec_add.pack(side='left')
        
        self.rec_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self.delete_selected_recipes(), width=95, height=40, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030')
        
        rec_import=RoundedActionButton(bar,'Importar Word/PDF',lambda: self._run_normal_action(self.rec_tree, self.import_recipe_document),width=155,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557')
        rec_import.pack(side='left',padx=10)
        
        rec_export=RoundedActionButton(bar,'Exportar Receita',lambda: self._run_normal_action(self.rec_tree, self.export_selected_recipe),width=145,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557')
        rec_export.pack(side='left',padx=10)
        
        rec_original=RoundedActionButton(bar,'Documento original',lambda: self._run_normal_action(self.rec_tree, self.open_original_document),width=165,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557')
        rec_original.pack(side='left',padx=10)
        
        rec_history=RoundedActionButton(bar,'Histórico',lambda: self._run_normal_action(self.rec_tree, self.recipe_history_dialog),width=125,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557')
        rec_history.pack(side='left',padx=10)

        self.rec_search = tk.StringVar()
        self.rec_search.trace_add('write', lambda *a: self.refresh_recipes())
        self.rec_search_wrap = self._styled_search_entry(bar, self.rec_search, 280)
        
        self.rec_status = tk.StringVar(value='Ativos')
        self.rec_status.trace_add('write', lambda *a: self.refresh_recipes())
        self.rec_status_wrap = RoundedDropdown(bar, self.rec_status, ['Ativos', 'Inativos', 'Todos'], width=110)
        self.rec_status_wrap.pack(side='right', padx=14)

        _, table_host = self._build_page_table_panel(f)
        
        self.rec_header=tk.Canvas(table_host,bg=self.colors['panel'],bd=0,highlightthickness=0,height=36)
        self.rec_header.pack(fill='x',padx=2,pady=(0,0))
        
        self.rec_tree=ttk.Treeview(table_host,columns=('code','name','yield','unit','cost','edit','delete','dummy'),show='tree')
        self.rec_tree.tag_configure('inactive', foreground='#9AA9BF')
        self.rec_tree.column('#0',width=60,minwidth=60,stretch=False)
        
        for k,w in [('code',100),('name',380),('yield',120),('unit',65),('cost',120),('edit',30),('delete',30)]:
            self.rec_tree.column(k,width=w,minwidth=w,anchor='center' if k in ('yield','unit','cost') else 'w',stretch=False)
        self.rec_tree.column('dummy', width=0, minwidth=0, stretch=True)
        
        self.rec_hsb = PillScrollbar(table_host, self.rec_tree)
        original_scroll_rec = self.rec_hsb._on_scroll
        def hsb_scroll_rec(first, last):
            original_scroll_rec(first, last)
            self.after_idle(self._redraw_rec_header) if hasattr(self, '_redraw_rec_header') else None
        self.rec_tree.configure(xscrollcommand=hsb_scroll_rec)
        self.rec_tree.pack(fill='both',expand=True)
        
        self._rec_header_specs=[('code','Código',100),('name','Receita',380),('yield','Rendimento',120),('unit','Un.',65),('cost','Custo total',120),('edit','',30),('delete','',30)]
        self._rec_header_imgs={}
        
        def redraw_rec_header(_event=None):
            c=self.rec_header; c.delete('all')
            w=max(c.winfo_width(),2); h=max(c.winfo_height(),2)
            r=min(h/2,18); fill='#EEF4FB'
            c.create_rectangle(r,0,w-r,h,fill=fill,outline='')
            c.create_rectangle(0,r,w,h-r,fill=fill,outline='')
            c.create_arc(0,0,2*r,2*r,start=90,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,0,w,2*r,start=0,extent=90,fill=fill,outline=fill)
            c.create_arc(0,h-2*r,2*r,h,start=180,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,h-2*r,w,h,start=270,extent=90,fill=fill,outline=fill)
            try:
                total_w = sum(int(self.rec_tree.column(col, 'width')) for col in ['#0'] + list(self.rec_tree['columns']))
                x_offset = float(self.rec_tree.xview()[0]) * total_w
            except Exception: x_offset = 0
            x0 = -x_offset
            cols=[('#0','')]+[(f'#{i}',txt) for i,(key,txt, _) in enumerate(self._rec_header_specs,1)]
            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.rec_tree.column(col,'width'))
                except Exception: cw=0
                if col in ('#0', '#6', '#7'):
                    x0+=cw; continue
                align = 'w' if col in ('#1', '#2') else 'center'
                anchor_x = x0+12 if align == 'w' else x0+cw/2
                c.create_text(anchor_x,h/2,text=txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor=align)
                c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                x0+=cw
            try: cw0=int(self.rec_tree.column('#0','width'))
            except Exception: cw0=60
            if cw0 > 0:
                c.create_rectangle(r, 0, cw0, h, fill=fill, outline='')
                c.create_rectangle(0, r, cw0, h-r, fill=fill, outline='')
                c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=fill, outline=fill)
                c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=fill, outline=fill)
                c.create_line(cw0, 6, cw0, h-6, fill=self.colors.get('line', '#E5ECF5'))
                key = str(self.rec_tree)
                checked = self._checked_rows.get(key, set())
                children = self.rec_tree.get_children()
                is_all_checked = len(checked) == len(children) and len(children) > 0
                txt_chk = '☑' if is_all_checked else '☐'
                color_chk = '#2B3D55' if is_all_checked else '#A0ABB9'
                if getattr(self, '_dark', False): color_chk = '#FFFFFF' if is_all_checked else '#60769D'
                c.create_text(cw0/2, h/2, text=txt_chk, fill=color_chk, font=('Segoe UI', 13), anchor='center', tags=('header_chk',))
                c.create_rectangle(0, 0, cw0-2, h, fill='', outline='', tags=('header_chk',))
                c.tag_bind('header_chk', '<Button-1>', lambda e: self._toggle_all_checkboxes(self.rec_tree))
            
            # RIGHT side cover
            try: cw6=int(self.rec_tree.column('#6','width'))
            except: cw6=0
            try: cw7=int(self.rec_tree.column('#7','width'))
            except: cw7=0
            total_r = cw6 + cw7
            if total_r > 0:
                start_x = w - total_r
                c.create_rectangle(start_x, 0, w-r, h, fill=fill, outline='')
                c.create_rectangle(start_x, r, w, h-r, fill=fill, outline='')
                c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=fill, outline=fill)
                c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=fill, outline=fill)
                c.create_line(start_x, 6, start_x, h-6, fill=self.colors.get('line', '#E5ECF5'))
        
        self._redraw_rec_header=redraw_rec_header
        self.rec_header.bind('<Configure>', redraw_rec_header)
        self.rec_tree.bind('<Configure>', lambda e: self.rec_tree.after_idle(redraw_rec_header))
        self.after_idle(redraw_rec_header)
        
        self._setup_canvas_header_drag(self.rec_header, self.rec_tree, ['edit','delete'], redraw_rec_header, 'rec')

        self.rec_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.rec_tree,'recipe'))
        self.rec_tree.bind('<Double-1>',lambda e:self.edit_selected_recipe())
        
        self.rec_icon_ov=self._attach_row_icon_overlay(self.rec_tree, table_host, 5, 6, self.edit_selected_recipe, self.delete_selected_recipe)
        self._action_buttons[self.rec_tree]={'normal':[rec_add,rec_import,rec_export,rec_original,rec_history],'bulk':[self.rec_bulk_delete_btn]}
        self._update_action_states()

    def recipe_form(self, edit_id=None, imported_items=None, imported_source=None):"""

text = re.sub(rec_page_pattern, new_rec_page, text, flags=re.DOTALL)


# --- REFRESH RECIPES REPLACEMENT ---
ref_rec_pattern = r"    def refresh_recipes\(self\):.*?self\._reset_checked\(self\.rec_tree\)"
new_ref_rec = """    def refresh_recipes(self):
        if not hasattr(self,'rec_tree'):return
        for x in self.rec_tree.get_children():self.rec_tree.delete(x)
        
        query = '%'+self.rec_search.get().strip()+'%' if hasattr(self,'rec_search') else '%'
        status_filter = self.rec_status.get() if hasattr(self, 'rec_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        
        with db() as c:rows=c.execute(f'SELECT id,code,name,yield_qty,yield_unit,COALESCE(active,1) as active FROM base_recipes WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()
        for r in rows:
            try:cost=recipe_cost(r['id'])
            except Exception:cost=0
            with db() as c:comps=c.execute('SELECT m.name,bri.qty,bri.unit,COALESCE(m.archived,0) as arc FROM base_recipe_items bri JOIN materials m ON m.id=bri.material_id WHERE bri.recipe_id=? ORDER BY bri.id',(r['id'],)).fetchall()
            has_arc = any(comp['arc'] for comp in comps)
            name_disp = f"⚠️ {r['name']}" if has_arc else r['name']
            
            is_active = r['active']
            iid=self.rec_tree.insert('','end',text='',values=(r['code'],name_disp,fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'',''), tags=() if is_active else ('inactive',))
            for comp in comps:
                comp_name = f"{comp['name']} (⚠️ Excluído)" if comp['arc'] else comp['name']
                self.rec_tree.insert(iid,'end',text='',values=('',f'↳ {comp_name}',fmt_num(comp['qty']),comp['unit'],'-','',''))
        self._reset_checked(self.rec_tree)
        if hasattr(self, 'rec_icon_ov'): self.rec_icon_ov._redraw()
        if hasattr(self, '_redraw_rec_header'): self._redraw_rec_header()"""

text = re.sub(ref_rec_pattern, new_ref_rec, text, flags=re.DOTALL)


# --- PRODUCTS PAGE REPLACEMENT ---
prod_page_pattern = r"    def products_page\(self,f\):.*?def product_form\(self, edit_id=None\):"
new_prod_page = """    def products_page(self,f):
        _, bar=self._build_page_toolbar(f)
        
        prod_add=RoundedActionButton(bar,'＋ Novo Produto',lambda: self._run_normal_action(self.prod_tree, self.new_product),width=150,height=40,fill='#F28C28',hover='#D96F0B')
        prod_add.pack(side='left')
        
        self.prod_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self.delete_selected_products(), width=95, height=40, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030')
        
        prod_history=RoundedActionButton(bar,'Histórico',lambda: self._run_normal_action(self.prod_tree, self.product_history_dialog),width=125,height=40,fill='#EFF4FB',hover='#E3EBF6',fg='#1D3557')
        prod_history.pack(side='left',padx=10)

        self.prod_search = tk.StringVar()
        self.prod_search.trace_add('write', lambda *a: self.refresh_products())
        self.prod_search_wrap = self._styled_search_entry(bar, self.prod_search, 280)
        
        self.prod_status = tk.StringVar(value='Ativos')
        self.prod_status.trace_add('write', lambda *a: self.refresh_products())
        self.prod_status_wrap = RoundedDropdown(bar, self.prod_status, ['Ativos', 'Inativos', 'Todos'], width=110)
        self.prod_status_wrap.pack(side='right', padx=14)

        _, table_host = self._build_page_table_panel(f)
        
        self.prod_header=tk.Canvas(table_host,bg=self.colors['panel'],bd=0,highlightthickness=0,height=36)
        self.prod_header.pack(fill='x',padx=2,pady=(0,0))
        
        self.prod_tree=ttk.Treeview(table_host,columns=('code','name','weight','cost','price','margin','edit','delete','dummy'),show='tree')
        self.prod_tree.tag_configure('inactive', foreground='#9AA9BF')
        self.prod_tree.column('#0',width=60,minwidth=60,stretch=False)
        
        for k,w in [('code',100),('name',380),('weight',120),('cost',110),('price',110),('margin',90),('edit',30),('delete',30)]:
            self.prod_tree.column(k,width=w,minwidth=w,anchor='center' if k in ('weight','cost','price','margin') else 'w',stretch=False)
        self.prod_tree.column('dummy', width=0, minwidth=0, stretch=True)
        
        self.prod_hsb = PillScrollbar(table_host, self.prod_tree)
        original_scroll_prod = self.prod_hsb._on_scroll
        def hsb_scroll_prod(first, last):
            original_scroll_prod(first, last)
            self.after_idle(self._redraw_prod_header) if hasattr(self, '_redraw_prod_header') else None
        self.prod_tree.configure(xscrollcommand=hsb_scroll_prod)
        self.prod_tree.pack(fill='both',expand=True)
        
        self._prod_header_specs=[('code','Código',100),('name','Produto',380),('weight','Peso/Rendimento',120),('cost','Custo total',110),('price','Preço',110),('margin','Margem',90),('edit','',30),('delete','',30)]
        self._prod_header_imgs={}
        
        def redraw_prod_header(_event=None):
            c=self.prod_header; c.delete('all')
            w=max(c.winfo_width(),2); h=max(c.winfo_height(),2)
            r=min(h/2,18); fill='#EEF4FB'
            c.create_rectangle(r,0,w-r,h,fill=fill,outline='')
            c.create_rectangle(0,r,w,h-r,fill=fill,outline='')
            c.create_arc(0,0,2*r,2*r,start=90,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,0,w,2*r,start=0,extent=90,fill=fill,outline=fill)
            c.create_arc(0,h-2*r,2*r,h,start=180,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,h-2*r,w,h,start=270,extent=90,fill=fill,outline=fill)
            try:
                total_w = sum(int(self.prod_tree.column(col, 'width')) for col in ['#0'] + list(self.prod_tree['columns']))
                x_offset = float(self.prod_tree.xview()[0]) * total_w
            except Exception: x_offset = 0
            x0 = -x_offset
            cols=[('#0','')]+[(f'#{i}',txt) for i,(key,txt, _) in enumerate(self._prod_header_specs,1)]
            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.prod_tree.column(col,'width'))
                except Exception: cw=0
                if col in ('#0', '#7', '#8'):
                    x0+=cw; continue
                align = 'w' if col in ('#1', '#2') else 'center'
                anchor_x = x0+12 if align == 'w' else x0+cw/2
                c.create_text(anchor_x,h/2,text=txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor=align)
                c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                x0+=cw
            try: cw0=int(self.prod_tree.column('#0','width'))
            except Exception: cw0=60
            if cw0 > 0:
                c.create_rectangle(r, 0, cw0, h, fill=fill, outline='')
                c.create_rectangle(0, r, cw0, h-r, fill=fill, outline='')
                c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=fill, outline=fill)
                c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=fill, outline=fill)
                c.create_line(cw0, 6, cw0, h-6, fill=self.colors.get('line', '#E5ECF5'))
                key = str(self.prod_tree)
                checked = self._checked_rows.get(key, set())
                children = self.prod_tree.get_children()
                is_all_checked = len(checked) == len(children) and len(children) > 0
                txt_chk = '☑' if is_all_checked else '☐'
                color_chk = '#2B3D55' if is_all_checked else '#A0ABB9'
                if getattr(self, '_dark', False): color_chk = '#FFFFFF' if is_all_checked else '#60769D'
                c.create_text(cw0/2, h/2, text=txt_chk, fill=color_chk, font=('Segoe UI', 13), anchor='center', tags=('header_chk',))
                c.create_rectangle(0, 0, cw0-2, h, fill='', outline='', tags=('header_chk',))
                c.tag_bind('header_chk', '<Button-1>', lambda e: self._toggle_all_checkboxes(self.prod_tree))
            
            # RIGHT side cover
            try: cw7=int(self.prod_tree.column('#7','width'))
            except: cw7=0
            try: cw8=int(self.prod_tree.column('#8','width'))
            except: cw8=0
            total_r = cw7 + cw8
            if total_r > 0:
                start_x = w - total_r
                c.create_rectangle(start_x, 0, w-r, h, fill=fill, outline='')
                c.create_rectangle(start_x, r, w, h-r, fill=fill, outline='')
                c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=fill, outline=fill)
                c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=fill, outline=fill)
                c.create_line(start_x, 6, start_x, h-6, fill=self.colors.get('line', '#E5ECF5'))
        
        self._redraw_prod_header=redraw_prod_header
        self.prod_header.bind('<Configure>', redraw_prod_header)
        self.prod_tree.bind('<Configure>', lambda e: self.prod_tree.after_idle(redraw_prod_header))
        self.after_idle(redraw_prod_header)
        
        self._setup_canvas_header_drag(self.prod_header, self.prod_tree, ['edit','delete'], redraw_prod_header, 'prod')

        self.prod_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.prod_tree,'product'))
        self.prod_tree.bind('<Double-1>',lambda e:self.edit_selected_product())
        
        self.prod_icon_ov=self._attach_row_icon_overlay(self.prod_tree, table_host, 6, 7, self.edit_selected_product, self.delete_selected_product)
        self._action_buttons[self.prod_tree]={'normal':[prod_add,prod_history],'bulk':[self.prod_bulk_delete_btn]}
        self._update_action_states()

    def product_form(self, edit_id=None):"""

text = re.sub(prod_page_pattern, new_prod_page, text, flags=re.DOTALL)


# --- REFRESH PRODUCTS REPLACEMENT ---
ref_prod_pattern = r"    def refresh_products\(self\):.*?self\._reset_checked\(self\.prod_tree\)"
new_ref_prod = """    def refresh_products(self):
        if not hasattr(self,'prod_tree'):return
        for x in self.prod_tree.get_children():self.prod_tree.delete(x)
        
        query = '%'+self.prod_search.get().strip()+'%' if hasattr(self,'prod_search') else '%'
        status_filter = self.prod_status.get() if hasattr(self, 'prod_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        
        with db() as c:rows=c.execute(f'SELECT id,code,name,weight_qty,weight_unit,sale_price,COALESCE(active,1) as active FROM products WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()
        for r in rows:
            try:cost=product_unit_cost(r['id'])
            except Exception:cost=0
            margin=((r['sale_price']-cost)/r['sale_price']*100) if r['sale_price'] else None
            with db() as c:comps=c.execute('SELECT item_type,ref_id,qty_per_unit AS qty,unit FROM product_items WHERE product_id=? ORDER BY id',(r['id'],)).fetchall()
            has_arc = False
            for comp in comps:
                if comp['item_type'] == 'MATERIAL':
                    with db() as cd: m = cd.execute('SELECT COALESCE(archived,0) as arc FROM materials WHERE id=?',(comp['ref_id'],)).fetchone()
                    if m and m['arc']: has_arc = True
                else:
                    with db() as cd: m = cd.execute('SELECT COALESCE(archived,0) as arc FROM base_recipes WHERE id=?',(comp['ref_id'],)).fetchone()
                    if m and m['arc']: has_arc = True
            
            name_disp = f"⚠️ {r['name']}" if has_arc else r['name']
            is_active = r['active']
            
            w_disp = (fmt_num(r['weight_qty'])+' '+str(r['weight_unit'] or '')).strip() or '-'
            iid=self.prod_tree.insert('','end',text='',values=(r['code'],name_disp,w_disp,fmt(cost),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-','',''), tags=() if is_active else ('inactive',))
            
            for comp in comps:
                if comp['item_type'] == 'MATERIAL':
                    with db() as cd: m = cd.execute('SELECT name, COALESCE(archived,0) as arc FROM materials WHERE id=?',(comp['ref_id'],)).fetchone()
                else:
                    with db() as cd: m = cd.execute('SELECT name, COALESCE(archived,0) as arc FROM base_recipes WHERE id=?',(comp['ref_id'],)).fetchone()
                
                if m:
                    n = f"{m['name']} (⚠️ Excluído)" if m['arc'] else m['name']
                    self.prod_tree.insert(iid,'end',text='',values=('',f'↳ {n}',fmt_num(comp['qty']),comp['unit'],'-','-','',''))
        self._reset_checked(self.prod_tree)
        if hasattr(self, 'prod_icon_ov'): self.prod_icon_ov._redraw()
        if hasattr(self, '_redraw_prod_header'): self._redraw_prod_header()"""

text = re.sub(ref_prod_pattern, new_ref_prod, text, flags=re.DOTALL)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Huge refactor to apply designer layout to recipes and products completed.")
