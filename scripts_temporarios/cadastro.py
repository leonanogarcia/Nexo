    def cadastro(self, f):
        _, bar = self._build_page_toolbar(f)
        
        mat_add=RoundedActionButton(bar, '+ Novo item', lambda: self._run_normal_action(self.mat_tree, self.new_material), width=130, height=42, fill='#F28C28', hover='#BA5200')
        mat_add.pack(side='left')
        
        mat_history=RoundedActionButton(bar, '<clock> Histórico', lambda: self._run_normal_action(self.mat_tree, self.material_history_dialog), width=120, height=42, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        mat_history.pack(side='left', padx=(8, 0))
        
        self.mat_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self.delete_selected_materials(), width=95, height=40, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030')
        
        self.mat_search=tk.StringVar(); self.mat_search.trace_add('write',lambda *a:self.refresh_materials())
        
        self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,280)
        
        self.mat_status = tk.StringVar(value='Ativos')
        self.mat_status.trace_add('write', lambda *a: self.refresh_materials())
        self.mat_status_wrap = RoundedDropdown(bar, self.mat_status, ['Ativos', 'Inativos', 'Todos'], width=110)
        self.mat_status_wrap.pack(side='right', padx=14)

        _,table_host=self._build_page_table_panel(f)
        
        self.mat_header=tk.Canvas(table_host,bg=self.colors['panel'],bd=0,highlightthickness=0,height=36)
        self.mat_header.pack(fill='x',padx=2,pady=(0,0))
        
        self.mat_tree=ttk.Treeview(table_host,columns=('code','barcode','name','brand','qty','unit','value','category','date','mod_date','status','dummy','edit','delete','options'),show='tree')
        self.mat_tree.tag_configure('inactive', foreground='#9AA9BF')
        self.mat_tree.column('#0',width=60,minwidth=60,stretch=False)
        
        for k,w in [('code',100),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135),('status',90),('edit',30),('delete',30),('options',30)]:
            self.mat_tree.column(k,width=w,minwidth=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date','status') else 'w',stretch=False)
        self.mat_tree.column('dummy', width=0, minwidth=0, stretch=True)
            
        self.mat_hsb = PillScrollbar(table_host, self.mat_tree)
        original_scroll = self.mat_hsb._on_scroll
        def hsb_scroll(first, last):
            original_scroll(first, last)
            self.after_idle(self._redraw_mat_header) if hasattr(self, '_redraw_mat_header') else None
        self.mat_tree.configure(xscrollcommand=hsb_scroll)
        
        self.mat_tree.pack(fill='both',expand=True)

        self._mat_header_specs=[('code','Código',100),('barcode','Cód. Barras',130),('name','Item',220),('brand','Marca',150),('qty','Quantidade',110),('unit','Un.',65),('value','Valor',100),('category','Categoria',130),('date','Data de criação',135),('mod_date','Última modificação',135),('status','Status',90),('dummy','',0),('edit','',30),('delete','',30),('options','',30)]
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
            
            try:
                total_w = sum(int(self.mat_tree.column(col, 'width')) for col in ['#0'] + list(self.mat_tree['columns']))
                x_offset = float(self.mat_tree.xview()[0]) * total_w
            except Exception:
                x_offset = 0
            
            x0 = -x_offset
            
            cols=[('#0','')]+[(f'#{i}',txt) for i,(key,txt, _) in enumerate(self._mat_header_specs,1)]
            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.mat_tree.column(col,'width'))
                except Exception: cw=0
                
                # We skip drawing fixed columns inside the scrolling loop
                if col == '#0': cw = 60
                if col in ('#0', '#12', '#13', '#14'):
                    x0+=cw; continue
                
                align = 'w' if col in ('#1', '#2', '#3') else 'center'
                anchor_x = x0+12 if align == 'w' else x0+cw/2
                c.create_text(anchor_x,h/2,text=txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor=align)
                c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                x0+=cw
                
            # Draw LEFT fixed cover
            try: cw0=int(self.mat_tree.column('#0','width'))
            except Exception: cw0=60
            if cw0 > 0:
                # Cover the left area, but leave top-left and bottom-left corners empty!
                c.create_rectangle(r, 0, cw0, h, fill=fill, outline='')
                c.create_rectangle(0, r, cw0, h-r, fill=fill, outline='')
                c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=fill, outline=fill)
                c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=fill, outline=fill)
                c.create_line(cw0, 6, cw0, h-6, fill=self.colors.get('line', '#E5ECF5'))
                
                # Draw "Select All" checkbox
                key = str(self.mat_tree)
                checked = self._checked_rows.get(key, set())
                children = self.mat_tree.get_children()
                is_all_checked = len(checked) == len(children) and len(children) > 0
                
                txt_chk = '☑' if is_all_checked else '☐'
                color_chk = '#2B3D55' if is_all_checked else '#A0ABB9'
                if getattr(self, '_dark', False): color_chk = '#FFFFFF' if is_all_checked else '#60769D'
                
                chk_id = c.create_text(cw0/2, h/2, text=txt_chk, fill=color_chk, font=('Segoe UI', 13), anchor='center', tags=('header_chk',))
                hitbox_id = c.create_rectangle(0, 0, cw0-2, h, fill='', outline='', tags=('header_chk',))
                c.tag_bind('header_chk', '<Button-1>', lambda e: self._toggle_all_checkboxes(self.mat_tree))
                
            # Draw RIGHT fixed cover
            try:
                cw11 = int(self.mat_tree.column('#11','width'))
                cw12 = int(self.mat_tree.column('#12','width'))
                cw13 = int(self.mat_tree.column('#13','width'))
                fixed_right_w = cw11 + cw12 + cw13
            except Exception:
                fixed_right_w = 120
            
            if fixed_right_w > 0:
                start_x = w - fixed_right_w
                # Cover the right area, but leave top-right and bottom-right corners empty!
                c.create_rectangle(start_x, 0, w-r, h, fill=fill, outline='')
                c.create_rectangle(start_x, r, w, h-r, fill=fill, outline='')
                c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=fill, outline=fill)
                c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=fill, outline=fill)
                c.create_line(start_x, 6, start_x, h-6, fill=self.colors.get('line', '#E5ECF5'))
                
                cx = start_x
                if cw11 > 0:
                    img=self._mat_header_imgs.get('edit')
                    if img: c.create_image(cx+cw11/2, h/2, image=img, anchor='center')
                    cx += cw11
                if cw12 > 0:
                    img=self._mat_header_imgs.get('delete')
                    if img: c.create_image(cx+cw12/2, h/2, image=img, anchor='center')
        self._redraw_mat_header=redraw_mat_header
        self.mat_header.bind('<Configure>', redraw_mat_header)
        self.mat_tree.bind('<Configure>', lambda e: self.mat_tree.after_idle(redraw_mat_header))
        self.after_idle(redraw_mat_header)
        
        self._setup_canvas_header_drag(self.mat_header, self.mat_tree, ['edit','delete','options'], redraw_mat_header, 'mat')

        self.mat_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.mat_tree,'material'))
        self.mat_tree.bind('<Double-1>',lambda e:self.edit_selected_material())
        
        self.mat_icon_ov=self._attach_row_icon_overlay(
            self.mat_tree, table_host, 10, 11,
            self.edit_selected_material, self.delete_selected_material)
            
        self._action_buttons[self.mat_tree]={'normal':[mat_add,mat_history],'bulk':[self.mat_bulk_delete_btn]}
        
        try:
            from PIL import Image, ImageTk
            img_path = UI_ASSETS / 'empty_state_reference_exact.png'
            self._mat_empty_img = ImageTk.PhotoImage(Image.open(img_path))
            
            self.mat_empty_overlay = tk.Frame(table_host, bg=self.colors['field'])
            inner = tk.Frame(self.mat_empty_overlay, bg=self.colors['field'])
            inner.place(relx=0.5, rely=0.5, anchor='center')
            
            l_img = tk.Label(inner, image=self._mat_empty_img, bg=self.colors['field'])
            l_img.pack(pady=(0, 10))
            
            l_title = tk.Label(inner, text='Ainda não há registros cadastrados.', bg=self.colors['field'], fg='#687796', font=('Segoe UI', 11, 'bold'))
            l_title.pack(pady=(0, 4))
            
            l_sub = tk.Label(inner, text='Clique em + Novo item para adicionar o primeiro item.', bg=self.colors['field'], fg='#8A99B5', font=('Segoe UI', 9))
            l_sub.pack()
            
        except Exception:
            self.mat_empty_overlay = tk.Label(table_host, text='Ainda não há registros cadastrados.\nClique em + Novo item para adicionar o primeiro item.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))