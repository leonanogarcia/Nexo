import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace `def settings_page(self,f):` and all its content until `def settings_conversion_dialog(self):`

new_code = '''
    class SettingsTab(tk.Frame):
        def __init__(self, parent, text, key, on_click, app):
            super().__init__(parent, bg=app.colors['bg'], bd=0, highlightthickness=0)
            self.key = key
            self.text = text
            self.on_click = on_click
            self.app = app
            self.is_active = False
            self.pack_propagate(False)
            self.config(height=42, width=200)
            
            self.panel = RoundedPanel(self, fill=app.colors['bg'], border='', radius=21, bg=app.colors['bg'])
            self.panel.pack(fill='both', expand=True, padx=4, pady=2)
            
            self.lbl = tk.Label(self.panel, text=text, bg=app.colors['bg'], fg=app.colors['muted'], font=('Segoe UI', 10))
            self.lbl.pack(side='left', padx=16)
            
            def click(e): self.on_click(self.key)
            def enter(e):
                if not self.is_active:
                    hover_fill = '#F4F7FC' if not getattr(self.app, '_dark', False) else '#162846'
                    self.panel.set_style(fill=hover_fill)
                    self.lbl.config(bg=hover_fill, fg=self.app.colors['text'], cursor='hand2')
                    self.panel._canvas.config(cursor='hand2')
                    self.config(cursor='hand2')
            def leave(e):
                self.set_active(self.is_active)
                
            for w in (self, self.panel, self.panel._canvas, self.lbl):
                w.bind('<Button-1>', click)
                w.bind('<Enter>', enter)
                w.bind('<Leave>', leave)
                
        def set_active(self, active):
            self.is_active = active
            bg = self.app.colors['bg']
            if active:
                fill = '#EFF4FB' if not getattr(self.app, '_dark', False) else '#1D3557'
                fg = '#1D3557' if not getattr(self.app, '_dark', False) else '#EFF4FB'
                font = ('Segoe UI', 10, 'bold')
            else:
                fill = bg
                fg = self.app.colors['muted']
                font = ('Segoe UI', 10, 'normal')
                
            self.panel.set_style(fill=fill, bg=bg)
            self.lbl.config(bg=fill, fg=fg, font=font)

    def settings_page(self,f):
        outer=tk.Frame(f,bg=self.colors['bg'])
        outer.pack(fill='both',expand=True)
        
        # --- NOVO LAYOUT: SIDEBAR E CONTENT ---
        sidebar_frame = tk.Frame(outer, bg=self.colors['bg'], width=220)
        sidebar_frame.pack(side='left', fill='y', padx=(0, 24))
        sidebar_frame.pack_propagate(False)
        
        content_frame = tk.Frame(outer, bg=self.colors['bg'])
        content_frame.pack(side='right', fill='both', expand=True)
        
        self.settings_vars={}
        self._settings_pages = {}
        self._settings_tabs = {}
        
        def on_tab_click(key):
            for k, tab in self._settings_tabs.items():
                if k == key:
                    tab.set_active(True)
                    self._settings_pages[k].pack(fill='both', expand=True)
                else:
                    tab.set_active(False)
                    self._settings_pages[k].pack_forget()

        def add_category(key, title):
            tab = self.SettingsTab(sidebar_frame, title, key, on_tab_click, self)
            tab.pack(fill='x', pady=(0, 4))
            self._settings_tabs[key] = tab
            
            # Content container with scrollbar
            page_outer = tk.Frame(content_frame, bg=self.colors['bg'])
            
            canvas=tk.Canvas(page_outer,bg=self.colors['bg'],highlightthickness=0,bd=0)
            canvas.pack(side='left',fill='both',expand=True)
            sb=ttk.Scrollbar(page_outer,orient='vertical',command=canvas.yview)
            sb.pack(side='right',fill='y')
            canvas.configure(yscrollcommand=sb.set)
            pad=tk.Frame(canvas,bg=self.colors['bg'])
            win=canvas.create_window((0,0),window=pad,anchor='nw')
            def _sync(_=None, c=canvas, p=pad, w=win):
                c.configure(scrollregion=c.bbox('all'))
                c.itemconfigure(w,width=c.winfo_width())
            pad.bind('<Configure>', _sync)
            canvas.bind('<Configure>', _sync)
            
            self._settings_pages[key] = page_outer
            return pad

        def panel(parent_pad, title):
            shell=RoundedPanel(parent_pad, fill=self.colors['panel'], border=self.colors.get('line', '#E5ECF5'), radius=18, bg=self.colors['bg'])
            shell.pack(fill='x', pady=(0,16))
            tk.Label(shell,text=title,bg=self.colors['panel'],fg=self.colors['text'],font=('Segoe UI',12,'bold')).pack(anchor='w',padx=20,pady=(16,6))
            body=tk.Frame(shell,bg=self.colors['panel'])
            body.pack(fill='x',padx=20,pady=(0,20))
            return shell, body

        # --- CONSTRUÇÃO DAS PÁGINAS ---
        # 1. Geral
        pad_geral = add_category('geral', '⚙️ Geral')
        
        _, company=panel(pad_geral, 'Empresa')
        name=tk.StringVar(value=get_setting('company_name','Nexo'));self.settings_vars['company']=name
        logo=tk.StringVar(value=get_setting('company_logo',''));self.settings_vars['logo']=logo
        ttk.Label(company,text='Nome da empresa').grid(row=0,column=0,sticky='w');ttk.Entry(company,textvariable=name,width=36).grid(row=1,column=0,padx=(0,10),sticky='ew')
        ttk.Label(company,text='Logo').grid(row=0,column=1,sticky='w');ttk.Entry(company,textvariable=logo,width=45).grid(row=1,column=1,padx=6,sticky='ew');ttk.Button(company,text='Selecionar',command=lambda:self.select_logo(logo)).grid(row=1,column=2,padx=6)
        ttk.Button(company,text='Salvar identidade',command=self.save_company_settings).grid(row=1,column=3,padx=6)
        tk.Label(company,text='Formatos aceitos: PNG, JPG/JPEG, GIF, BMP, WebP, TIFF e ICO. Mínimo recomendado: 500 px no menor lado.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9),wraplength=980,justify='left').grid(row=2,column=0,columnspan=4,sticky='w',padx=6,pady=(8,0))
        company.columnconfigure(0,weight=1); company.columnconfigure(1,weight=1)

        _, appearance=panel(pad_geral, 'Aparência')
        stored_theme=get_setting('theme','light'); theme=tk.StringVar(value={'light':'Claro','dark':'Escuro','system':'Sistema'}.get(stored_theme,'Escuro'));self.settings_vars['theme']=theme
        ttk.Label(appearance,text='Tema').pack(side='left');ttk.Combobox(appearance,textvariable=theme,values=('Claro','Escuro','Sistema'),state='readonly',width=12).pack(side='left',padx=8);ttk.Button(appearance,text='Aplicar',command=self.apply_theme_from_settings).pack(side='left')

        _, langbox=panel(pad_geral, 'Idioma')
        self.language_var=tk.StringVar(value=get_setting('language','Português (Brasil)'))
        ttk.Label(langbox,text='Idioma').pack(side='left');ttk.Combobox(langbox,textvariable=self.language_var,values=('Português (Brasil)',),state='readonly',width=22).pack(side='left',padx=8)
        tk.Label(langbox,text='Outros idiomas serão adicionados na camada de tradução sem alterar os dados.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).pack(side='left')

        # 2. IA
        pad_ia = add_category('ia', '🧠 Inteligência Artificial')
        _, aibox = panel(pad_ia, 'Sincronismo de Inteligência Artificial')
        ai_enabled = tk.IntVar(value=int(get_setting('ai_enabled', '0')))
        ai_provider = tk.StringVar(value=get_setting('ai_provider', 'Google Gemini'))
        ai_api_key = tk.StringVar(value=get_setting('ai_api_key', ''))
        ai_daily_limit = tk.StringVar(value=get_setting('ai_daily_limit', '50'))
        
        row1 = tk.Frame(aibox, bg=self.colors['panel']); row1.pack(fill='x', pady=(0, 12))
        ttk.Checkbutton(row1, text="Ativar Importação Inteligente (IA)", variable=ai_enabled, style='TCheckbutton').pack(side='left', padx=(0, 16))
        ttk.Label(row1, text="Provedor:").pack(side='left'); ttk.Combobox(row1, textvariable=ai_provider, values=('Google Gemini', 'OpenAI ChatGPT'), state='readonly', width=20).pack(side='left', padx=8)
        
        row2 = tk.Frame(aibox, bg=self.colors['panel']); row2.pack(fill='x', pady=(0, 12))
        ttk.Label(row2, text="Chave API (Secreta):").pack(side='left')
        ttk.Entry(row2, textvariable=ai_api_key, width=55, show='*').pack(side='left', padx=8)
        
        def show_ai_help():
            messagebox.showinfo("Ajuda: Chave de API", "Para Google Gemini:\\n1. Acesse aistudio.google.com\\n2. Faça login com o Google\\n3. Clique em 'Get API Key' e 'Create API Key'\\n4. Cole o código gerado no campo.\\n\\nPara OpenAI:\\n1. Acesse platform.openai.com/api-keys\\n2. Clique em 'Create new secret key'.", parent=self.winfo_toplevel())
            
        ttk.Button(row2, text="Ajuda (i)", width=8, command=show_ai_help).pack(side='left')
        
        row3 = tk.Frame(aibox, bg=self.colors['panel']); row3.pack(fill='x', pady=(0, 12))
        ttk.Label(row3, text="Alerta de Segurança Diário (Limitar em):").pack(side='left')
        ttk.Entry(row3, textvariable=ai_daily_limit, width=10).pack(side='left', padx=8)
        ttk.Label(row3, text="leituras por dia.").pack(side='left')
        
        def save_ai_settings():
            set_setting('ai_enabled', str(ai_enabled.get()))
            set_setting('ai_provider', ai_provider.get())
            set_setting('ai_api_key', ai_api_key.get().strip())
            set_setting('ai_daily_limit', ai_daily_limit.get().strip())
            self.notify("Configurações de IA salvas com sucesso.")
            
        ttk.Button(aibox, text='Salvar Configurações de IA', command=save_ai_settings).pack(anchor='w')
        tk.Label(aibox, text='O Nexo processa imagens apenas para fins de extração de dados e não armazena fotos na nuvem.', bg=self.colors['panel'], fg=self.colors['muted'], font=('Segoe UI', 9)).pack(anchor='w', pady=(8, 0))

        # 3. Métricas
        pad_met = add_category('metricas', '📈 Métricas de Custo')
        _, costs=panel(pad_met, 'Custos operacionais')
        self.cost_vars={}; settings=get_cost_settings()
        for i,n in enumerate(('Gás','Energia','Água')):
            ttk.Label(costs,text=f'{n} (%)').grid(row=0,column=i,sticky='w',padx=6);v=tk.StringVar(value=fmt_num(settings.get(n,20)));self.cost_vars[n]=v;ttk.Entry(costs,textvariable=v,width=12).grid(row=1,column=i,padx=6)
        ttk.Button(costs,text='Salvar custos',command=self.save_cost_settings).grid(row=1,column=3,padx=10)
        tk.Label(costs,text='Esses percentuais entram no custo final do Produto e ficam registrados no histórico.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).grid(row=2,column=0,columnspan=4,sticky='w',padx=6,pady=8)

        # 4. Unidades
        pad_un = add_category('unidades', '⚖️ Unidades de Medida')
        _, units=panel(pad_un, 'Unidades internas')
        self.base_vars={}
        for i,(key,label,vals) in enumerate((('mass_base_unit','Massa',UNITS_MASS),('volume_base_unit','Volume',UNITS_VOLUME),('count_base_unit','Quantidade',UNITS_COUNT))):
            ttk.Label(units,text=label).grid(row=0,column=i,padx=6,sticky='w');v=tk.StringVar(value=get_setting(key,BASE_UNITS_DEFAULT[dimension_of_unit(vals[0]) or 'count']));self.base_vars[key]=v;ttk.Combobox(units,textvariable=v,values=vals,state='readonly',width=10).grid(row=1,column=i,padx=6)
        ttk.Button(units,text='Salvar unidades internas',command=self.save_base_units).grid(row=1,column=3,padx=8)

        _, convbox=panel(pad_un, 'Unidades configuráveis por insumo')
        tk.Label(convbox,text='Ex.: xícara de leite pode equivaler a 240 ml; xícara de farinha pode equivaler a outro valor.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).grid(row=0,column=0,sticky='w',pady=(0,8))
        ttk.Button(convbox,text='Gerenciar conversões',command=self.settings_conversion_dialog).grid(row=1,column=0,sticky='w')

        # 5. DB e BI
        pad_db = add_category('banco', '💾 Banco de Dados & BI')
        _, bibox=panel(pad_db, 'Auditoria & BI')
        self.retention_var=tk.StringVar(value=get_setting('history_retention_months','36'))
        ttk.Label(bibox,text='Retenção do histórico de edições (Meses)').pack(side='left')
        ttk.Entry(bibox,textvariable=self.retention_var,width=10).pack(side='left',padx=8)
        
        def save_retention():
            try:
                v = int(self.retention_var.get().strip())
                if v < 0: raise ValueError()
                set_setting('history_retention_months', str(v))
                self.notify(f"Retenção de histórico definida para {v} meses.")
            except Exception:
                safe_error(self.winfo_toplevel(), "Erro", "Digite um número de meses válido (0 para nunca limpar).")
                
        ttk.Button(bibox,text='Salvar',command=save_retention).pack(side='left')
        tk.Label(bibox,text='Itens mais antigos serão limpos automaticamente na inicialização para otimizar o banco de dados.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).pack(side='left', padx=8)

        _, dbbox=panel(pad_db, 'Fonte de dados')
        ttk.Label(dbbox,text='SQLite atual').grid(row=0,column=0,sticky='w');self.db_path_var=tk.StringVar(value=str(DB_PATH));ttk.Entry(dbbox,textvariable=self.db_path_var,width=70).grid(row=1,column=0,padx=(0,8),sticky='ew')
        ttk.Button(dbbox,text='Escolher arquivo SQLite',command=self.choose_db_file).grid(row=1,column=1)
        ttk.Button(dbbox,text='Aplicar banco',command=self.apply_db_file).grid(row=1,column=2,padx=6)
        self.settings_db_status=tk.Label(dbbox,textvariable=self.status,bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9,'bold'),anchor='w')
        self.settings_db_status.grid(row=3,column=0,columnspan=3,sticky='w',pady=(4,0))
        tk.Label(dbbox,text='SQLite local/arquivo de rede funciona nesta versão. Conectores PostgreSQL/MySQL podem ser adicionados depois.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9),wraplength=980,justify='left').grid(row=2,column=0,columnspan=3,sticky='w',pady=8)
        dbbox.columnconfigure(0,weight=1)

        _, audit=panel(pad_db, 'Auditoria do banco')
        tk.Label(audit,text='Veja as últimas operações, diferencie INSERT/UPDATE/DELETE e confira o antes/depois das edições.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).pack(anchor='w')
        ttk.Button(audit,text='Visualizar banco / auditoria',command=self.audit_database_dialog).pack(anchor='w',pady=(8,0))

        _, docs=panel(pad_db, 'Documentos')
        tk.Label(docs,text=f'Arquivos originais ficam em: {DOCS_DIR}',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).pack(anchor='w')
        
        # Init
        self.refresh_settings_widgets = pad_geral # Fallback for compatibility if needed
        on_tab_click('geral')
'''

# Find block to replace
start_idx = content.find('    def settings_page(self,f):')
end_idx = content.find('    def settings_conversion_dialog(self):')

if start_idx != -1 and end_idx != -1:
    patched = content[:start_idx] + new_code + '\n' + content[end_idx:]
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(patched)
    print("PATCH APPLIED SUCCESSFULLY!")
else:
    print("ERROR: COULD NOT FIND TARGET BLOCKS")
