import shutil
import re

# 1. Start from the clean base from before the session
shutil.copy(r'D:\Nexo\temp_extract\Nexo_v0_7_13\main.py', 'main.py')

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 2. Fix search box packing and placeholder color
code = code.replace(
    """    def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)
        wrap.pack(side='left',padx=(14,0))
        return wrap.entry""",
    """    def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)
        wrap.pack(side='right',padx=(14,0),fill='none',expand=False)
        return wrap"""
)
code = code.replace("fg='#9AA9BF',font=('Segoe UI',10)", "fg='#60769D',font=('Segoe UI',10)")

# 3. Add PillScrollbar class right before RoundedActionButton
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

# 4. Fix icon detection in RoundedActionButton
detect_icon_new = """    def _detect_icon(self,text):
        if '+' in text: return 'plus'
        if '🕒' in text or 'clock' in text.lower(): return 'clock'
        if '🔄' in text: return 'convert'
        if '🗑' in text or 'delete' in text.lower(): return 'delete'
        return None

    def _clean_text(self,text):
        for token in ('+', '🕒', '🔄', '🗑'):
            text = text.replace(token, '')
        return ' '.join(text.split())"""
code = re.sub(r"    def _detect_icon\(self,text\):.*?return ' '\.join\(text\.split\(\)\)", detect_icon_new, code, flags=re.DOTALL)

# 5. Inject overlay functions right before def _setup_canvas_header_drag
# Oh wait, D:\Nexo\temp_extract\Nexo_v0_7_13\main.py does NOT have _setup_canvas_header_drag!
# It has def cadastro(self, f):
# Let's inject ALL these functions right before `def cadastro(self, f):`
overlay_funcs = """    def _setup_canvas_header_drag(self, canvas, tree, fixed_cols, redraw_cmd, state_key):
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

    def _make_row_icon(self, kind):
        from PIL import Image, ImageDraw, ImageTk
        im = Image.new('RGBA', (24, 24), (0,0,0,0))
        d = ImageDraw.Draw(im)
        if kind == 'edit':
            d.polygon([(6,18),(6,14),(14,6),(18,10),(10,18)], fill='#60769D')
        elif kind == 'delete':
            d.rectangle([(8,6),(16,8)], fill='#D93838')
            d.rectangle([(9,8),(15,18)], fill='#D93838')
        return ImageTk.PhotoImage(im)

    def _toggle_active(self, kind, iid, current_active):
        table = {'material': 'materials', 'recipe': 'base_recipes', 'product': 'products'}[kind]
        new_val = 0 if current_active else 1
        with db() as c:
            c.execute(f'UPDATE {table} SET active=?, updated_at=? WHERE id=?', (new_val, now_iso(), iid))
        self.refresh_all()
        self.notify(f"Item {'desativado' if current_active else 'ativado'} com sucesso.")

    def _show_row_menu(self, tree, kind, iid, x, y, edit_cmd, delete_cmd):
        tree.selection_set(iid)
        is_active = 'inactive' not in tree.item(iid, 'tags')
        
        m = tk.Menu(self.winfo_toplevel(), tearoff=0, bg=self.colors['panel'], fg=self.colors['text'], font=('Segoe UI', 10), bd=1)
        
        if is_active:
            m.add_command(label='✏ Editar', command=lambda: edit_cmd())
        else:
            m.add_command(label='✏ Editar (Desabilitado)', state='disabled')
            
        m.add_command(label='🗑 Excluir', command=lambda: delete_cmd())
        m.add_separator()
        
        if is_active:
            m.add_command(label='⏸ Desativar', command=lambda: self._toggle_active(kind, iid, True))
        else:
            m.add_command(label='▶ Ativar', command=lambda: self._toggle_active(kind, iid, False))
            
        m.post(x, y)

    def _attach_row_icon_overlay(self, tree, table_host, edit_col_idx, delete_col_idx, edit_cmd, delete_cmd):
        ov = tk.Canvas(table_host, bd=0, highlightthickness=0, cursor='arrow', bg=self.colors['field'])
        ov.place(relx=1.0, x=0, y=36, width=120, relheight=1.0, height=-36, anchor='ne')
        ov._icon_refs = []
        kind = 'material' if 'mat' in str(tree) else ('recipe' if 'rec' in str(tree) else 'product')

        def _redraw_overlay(*_):
            ov.delete('all')
            ov._icon_refs.clear()
            img_e = self._make_row_icon('edit')
            img_d = self._make_row_icon('delete')
            ex, dx, ox = 20, 60, 100
            selected = set(tree.selection())
            for iid in tree.get_children():
                bb = tree.bbox(iid)
                if not bb: continue
                _, ry, _, rh = bb
                bg_color = self.colors['accent_soft'] if iid in selected else self.colors['field']
                ov.create_rectangle(0, ry, 120, ry + rh, fill=bg_color, outline='')
                cy = ry + rh // 2
                
                is_active = 'inactive' not in tree.item(iid, 'tags')
                
                if img_e:
                    ov._icon_refs.append(img_e)
                    if is_active:
                        ov.create_image(ex, cy, image=img_e, anchor='center', tags=(f'e_{iid}',))
                        ov.tag_bind(f'e_{iid}', '<Button-1>', lambda ev, i=iid: (self._set_single_checked(tree, i), edit_cmd()))
                        ov.tag_bind(f'e_{iid}', '<Enter>', lambda ev, i=iid: ov.config(cursor='hand2'))
                        ov.tag_bind(f'e_{iid}', '<Leave>', lambda ev, i=iid: ov.config(cursor='arrow'))
                    else:
                        ov.create_rectangle(ex-12, cy-12, ex+12, cy+12, fill=bg_color, stipple='gray50', outline='')
                        
                if img_d:
                    ov._icon_refs.append(img_d)
                    ov.create_image(dx, cy, image=img_d, anchor='center', tags=(f'd_{iid}',))
                    ov.tag_bind(f'd_{iid}', '<Button-1>', lambda ev, i=iid: (self._set_single_checked(tree, i), delete_cmd()))
                    ov.tag_bind(f'd_{iid}', '<Enter>', lambda ev, i=iid: ov.config(cursor='hand2'))
                    ov.tag_bind(f'd_{iid}', '<Leave>', lambda ev, i=iid: ov.config(cursor='arrow'))
                    
                dot_c = self.colors.get('text', '#333333')
                ov.create_oval(ox-2, cy-6, ox+2, cy-2, fill=dot_c, outline='', tags=(f'o_{iid}',))
                ov.create_oval(ox-2, cy-1, ox+2, cy+3, fill=dot_c, outline='', tags=(f'o_{iid}',))
                ov.create_oval(ox-2, cy+4, ox+2, cy+8, fill=dot_c, outline='', tags=(f'o_{iid}',))
                
                ov.tag_bind(f'o_{iid}', '<Button-1>', lambda ev, i=iid: self._show_row_menu(tree, kind, i, ev.x_root, ev.y_root, edit_cmd, delete_cmd))
                ov.tag_bind(f'o_{iid}', '<Enter>', lambda ev, i=iid: ov.config(cursor='hand2'))
                ov.tag_bind(f'o_{iid}', '<Leave>', lambda ev, i=iid: ov.config(cursor='arrow'))

        def _sync_scroll(*_):
            ov.yview_moveto(tree.yview()[0])
            
        tree.bind('<Configure>', _redraw_overlay, add='+')
        tree.bind('<<TreeviewSelect>>', _redraw_overlay, add='+')
        ov._redraw = _redraw_overlay
        return ov

    def cadastro(self, f):"""
code = code.replace("    def cadastro(self, f):", overlay_funcs)

# 6. Now, REWRITE def cadastro ENTIRELY to match exactly the perfect UI state
# We replace from `def cadastro(self, f):` until `def material_form(self, edit_id=None):`
new_cadastro = """    def cadastro(self, f):
        _, bar = self._build_page_toolbar(f)
        
        mat_add=RoundedActionButton(bar, '+ Novo item', lambda: self._run_normal_action(self.mat_tree, self.new_material), width=130, height=49, fill='#2F67B1', hover='#255894')
        mat_add.pack(side='left')
        
        mat_history=RoundedActionButton(bar, '🕒 Histórico', lambda: self._run_normal_action(self.mat_tree, self.material_history_dialog), width=120, height=49, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        mat_history.pack(side='left', padx=(8, 0))
        
        self.mat_bulk_delete_btn=RoundedActionButton(bar, '🗑 Excluir', lambda: self._run_normal_action(self.mat_tree, self.delete_selected_materials), width=120, height=49, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')
        
        self.mat_search=tk.StringVar(); self.mat_search.trace_add('write',lambda *a:self.refresh_materials())
        
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
        self.mat_empty_overlay = tk.Label(table_host, text='Nenhum insumo encontrado.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))

"""
code = re.sub(r"    def cadastro\(self, f\):.*?    def material_form\(self, edit_id=None\):", new_cadastro + "    def material_form(self, edit_id=None):", code, flags=re.DOTALL)


# 7. Apply treeview columns to recipes and products, replacing standard scrollbar
old_rec_col = """        for k, w in [('code',95),('name',280),('yield',120),('unit',65),('cost',120)]:
            self.rec_tree.column(k,width=w,anchor='center' if k in ('yield','unit','cost') else 'w',stretch=False)
        for k in ('edit','delete','options'):
            self.rec_tree.column(k,width=40,anchor='center',stretch=False)
        self.rec_tree.pack(fill='both',expand=True)
        self.rec_hsb = ttk.Scrollbar(table_host, orient='horizontal', command=self.rec_tree.xview)
        self.rec_tree.configure(xscrollcommand=self.rec_hsb.set)
        self.rec_hsb.pack(side='bottom', fill='x', pady=(2,0))"""
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
        self.prod_tree.pack(fill='both',expand=True)
        self.prod_hsb = ttk.Scrollbar(table_host, orient='horizontal', command=self.prod_tree.xview)
        self.prod_tree.configure(xscrollcommand=self.prod_hsb.set)
        self.prod_hsb.pack(side='bottom', fill='x', pady=(2,0))"""
new_prod_col = """        for k, w in [('code',95),('name',280),('weight',140),('cost',120),('price',120),('margin',100)]:
            self.prod_tree.column(k,width=w,anchor='center' if k in ('weight','cost','price','margin') else 'w',stretch=(k=='name'))
        for k in ('edit','delete','options'):
            self.prod_tree.column(k,width=40,anchor='center',stretch=False)
        self.prod_hsb = PillScrollbar(table_host, self.prod_tree)
        self.prod_tree.pack(fill='both',expand=True)"""
code = code.replace(old_prod_col, new_prod_col)


# 8. Add `inactive` tags to refresh_materials
old_refresh = """            self.mat_tree.insert('', 'end', iid=str(r['id']), text='☐', values=tuple(r_list))"""
new_refresh = """            is_active = r_list.pop(9)
            mat_id = r_list.pop(9)
            status_str = 'Ativo' if is_active else 'Inativo'
            self.mat_tree.insert('', 'end', iid=str(mat_id), text='☐', values=tuple(r_list)+(status_str, '','',''), tags=() if is_active else ('inactive',))"""
code = code.replace("            self.mat_tree.insert('', 'end', iid=str(r['id']), text='☐', values=tuple(r_list))", new_refresh)
# Wait, also we need to update the SELECT query in refresh_materials
old_query = """SELECT code,name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,
                                       substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10), id
                                FROM materials WHERE name LIKE ? OR COALESCE(brand,'') LIKE ? OR code LIKE ? ORDER BY name"""
new_query = """SELECT code,name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,
                                       substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10), COALESCE(active,1), id
                                FROM materials WHERE {status_cond} AND (name LIKE ? OR COALESCE(brand,'') LIKE ? OR code LIKE ?) ORDER BY name"""
# wait we can just replace the whole refresh_materials function
refresh_mats_new = """    def refresh_materials(self):
        if not hasattr(self,'mat_tree'): return
        for x in self.mat_tree.get_children(): self.mat_tree.delete(x)
        query = '%'+self.mat_search.get().strip()+'%' if hasattr(self,'mat_search') else '%'
        status_filter = self.mat_status.get() if hasattr(self, 'mat_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1" if status_filter == 'Ativos' else ("COALESCE(active,1)=0" if status_filter == 'Inativos' else "1=1")
        with db() as c:
            rows = c.execute(f'''SELECT code,name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,
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
            self.mat_tree.insert('', 'end', iid=str(mat_id), text='☐', values=tuple(r_list)+(status_str, '','',''), tags=() if is_active else ('inactive',))
        self._reset_checked(self.mat_tree)
        if hasattr(self, 'mat_icon_ov'): self.mat_icon_ov._redraw()"""
code = re.sub(r"    def refresh_materials\(self\):.*?self\._reset_checked\(self\.mat_tree\)", refresh_mats_new, code, flags=re.DOTALL)


# 9. Now, fix the database deletion constraints
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

new_bulk_delete = r"""    def _bulk_delete_list(self, tree, kind):
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
        
        msg = f'Você selecionou {len(rows)} itens.\n'
        if linked:
            msg += f'\n{len(linked)} itens possuem vínculos/dependências e serão INATIVADOS:\n'
            msg += '\n'.join('  - ' + r['name'] for r in linked) + '\n'
        if unlinked:
            msg += f'\nOs outros {len(unlinked)} itens (sem vínculos) serão EXCLUÍDOS permanentemente.\n'
            
        msg += '\nDeseja prosseguir? (Se escolher Não, toda a operação será cancelada).'
            
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
