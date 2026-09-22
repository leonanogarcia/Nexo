import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_cadastro = """    def cadastro(self, f):
        _, bar = self._build_page_toolbar(f)
        
        mat_add=RoundedActionButton(bar, '+  Novo item', lambda: self._run_normal_action(self.mat_tree, self.new_material), width=177, height=49, fill='#2F67B1', hover='#255894')
        mat_add.pack(side='left')
        
        mat_history=RoundedActionButton(bar, '   Histórico', lambda: self._run_normal_action(self.mat_tree, self.material_history_dialog), width=148, height=49, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        mat_history.pack(side='left', padx=(10, 0))
        
        self.mat_bulk_delete_btn=RoundedActionButton(bar, 'Excluir', lambda: self._run_normal_action(self.mat_tree, self.delete_selected_materials), width=120, height=49, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')
        
        self.mat_search=tk.StringVar(); self.mat_search.trace_add('write',lambda *a:self.refresh_materials())
        
        # Pílula Status
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
                m.add_command(label=opt, command=lambda o=opt: (self.mat_status.set(o), _draw_status(o), self.refresh_materials()))
            m.post(e.x_root, e.y_root)
            
        self.mat_status_wrap.bind('<Button-1>', _open_status_menu)
        
        self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,22)
        self.mat_search_wrap.pack_configure(side='right',padx=(14,0),fill='none',expand=False)

        _,table_host=self._build_page_table_panel(f)
        
        self.mat_header=tk.Canvas(table_host,bg=self.colors['panel'],bd=0,highlightthickness=0,height=36)
        self.mat_header.pack(fill='x',padx=2,pady=(0,0))
        
        self.mat_tree=ttk.Treeview(table_host,columns=('code','name','brand','qty','unit','value','category','date','mod_date','status','edit','delete','options'),show='tree')
        self.mat_tree.tag_configure('inactive', foreground='#9AA9BF')
        self.mat_tree.column('#0',width=60,minwidth=60,stretch=False)
        
        for k,w in [('code',100),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135),('status',90),('edit',40),('delete',40),('options',40)]:
            self.mat_tree.column(k,width=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date','status') else 'w',stretch=False)
            
        self.mat_tree.pack(fill='both',expand=True)

        self._mat_header_specs=[('code','Código',100),('name','Item',220),('brand','Marca',150),('qty','Quantidade',110),('unit','Un.',65),('value','Valor',100),('category','Categoria',130),('date','Data de criação',135),('mod_date','Última modificação',135),('status','Status',90),('edit','',40),('delete','',40),('options','',40)]
        self._mat_header_imgs={}
        
        def redraw_mat_header(_event=None):
            self._draw_canvas_header(self.mat_header, self.mat_tree, self._mat_header_specs, self._mat_header_imgs, 'mat')
            
        self.mat_header.bind('<Configure>', redraw_mat_header)
        self.mat_tree.bind('<Configure>', redraw_mat_header)
        
        self._setup_canvas_header_drag(self.mat_header, self.mat_tree, ['edit','delete','options'], redraw_mat_header, 'mat')

        self.mat_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.mat_tree,'material'))
        self.mat_tree.bind('<Double-1>',lambda e:self.edit_selected_material())
        
        self.mat_icon_ov=self._attach_row_icon_overlay(
            self.mat_tree, table_host, 10, 11,
            self.edit_selected_material, self.delete_selected_material)
            
        self.mat_empty_overlay = tk.Label(table_host, text='Nenhum insumo encontrado.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"""

# find where def cadastro ends and material_form begins
code = re.sub(r"    def cadastro\(self, f\):.*?def material_form\(self, edit_id=None\):", new_cadastro + "\n\n    def material_form(self, edit_id=None):", code, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
