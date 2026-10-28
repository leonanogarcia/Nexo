import json
import re
import shutil
import sqlite3
from pathlib import Path
from datetime import date, datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

from backend import (
    paths,
    BASE_DIR, RESOURCE_DIR, USER_DATA_DIR, DATA_DIR, BACKUPS_DIR,
    CONFIG_PATH, DEFAULT_DB_PATH, DB_PATH, DOCS_DIR,
    ICON_PNG, LOGO_PNG, ICON_ICO, UI_ASSETS,
    load_file_config, save_file_config, get_db_path, set_db_path,
    db, now_iso, init_db, next_code, get_setting, set_setting,
    get_cost_settings, record_edit, list_names,
    UNITS_MASS, UNITS_VOLUME, UNITS_COUNT, UNITS, BASE_UNITS_DEFAULT,
    to_float, optional_float, money_to_float, fmt, fmt_num, normalize_text,
    dimension_of_unit, base_unit, unit_factor_to_default_base,
    configured_base_unit, unit_factor_to_internal,
    custom_units_for_material, conversion_to_base, convert_generic, conversion_between,
    material_cost, recipe_cost, item_cost, operational_cost,
    product_unit_cost, product_direct_cost, snapshot_costs,
    save_uploaded_document, latest_document,
    extract_docx_text, extract_pdf_text, parse_recipe_lines,
)
from ..components import (
    _field_palette, rounded_entry, numeric_entry, masked_money_entry,
    safe_error, bind_text_capitalization, FlatEmojiButton,
    Modal, RoundedPanel, PillScrollbar, VerticalPillScrollbar,
    RoundedActionButton, RoundedEntry, SidebarIcon, NavItem,
    ReferenceSidebar, RoundedDropdown, CustomHistoryModal, ListDialog,
    get_work_area,
)

class SettingsPageMixin:
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
        self._settings_canvases = {}
        self._active_settings_key = 'geral'
        
        def on_tab_click(key):
            self._active_settings_key = key
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
            
            # Content container with pill scrollbar
            page_outer = tk.Frame(content_frame, bg=self.colors['bg'])
            
            canvas=tk.Canvas(page_outer,bg=self.colors['bg'],highlightthickness=0,bd=0)
            canvas.pack(side='left',fill='both',expand=True)
            VerticalPillScrollbar(page_outer, canvas)
            pad=tk.Frame(canvas,bg=self.colors['bg'])
            win=canvas.create_window((0,0),window=pad,anchor='nw')
            def _sync(_=None, c=canvas, p=pad, w=win):
                c.configure(scrollregion=c.bbox('all'))
                c.itemconfigure(w,width=c.winfo_width())
            pad.bind('<Configure>', _sync)
            canvas.bind('<Configure>', _sync)
            
            self._settings_pages[key] = page_outer
            self._settings_canvases[key] = canvas
            return pad

        def panel(parent_pad, title):
            shell=RoundedPanel(parent_pad, fill=self.colors['panel'], border=self.colors.get('line', '#E5ECF5'), radius=18, bg=self.colors['bg'])
            shell.pack(fill='x', pady=(0,16))
            tk.Label(shell,text=title,bg=self.colors['panel'],fg=self.colors['text'],font=('Segoe UI',12,'bold')).pack(anchor='w',padx=20,pady=(16,6))
            body=tk.Frame(shell,bg=self.colors['panel'])
            body.pack(fill='x',padx=20,pady=(0,20))
            return shell, body

        def lbl(parent, text, font=('Segoe UI', 9, 'bold'), **kw):
            return tk.Label(parent, text=text, bg=self.colors['panel'], fg=self.colors['text'], font=font, **kw)

        def sub_lbl(parent, text, **kw):
            return tk.Label(parent, text=text, bg=self.colors['panel'], fg=self.colors['muted'], font=('Segoe UI', 9), **kw)

        def pri_btn(parent, text, command, width=140, height=34):
            return RoundedActionButton(parent, text, command, width=width, height=height, fill='#F28C28', hover='#BA5200', fg='#FFFFFF', bg=self.colors['panel'])

        def sec_btn(parent, text, command, width=120, height=34):
            dark = getattr(self, '_dark', False)
            return RoundedActionButton(parent, text, command, width=width, height=height,
                                       fill='#172746' if dark else '#EFF4FB',
                                       hover='#20375F' if dark else '#E3EBF6',
                                       fg='#DDE6FF' if dark else '#1D3557',
                                       bg=self.colors['panel'])

        def capsule_toggle(parent, text, var):
            wrap = tk.Frame(parent, bg=self.colors['panel'], cursor='hand2')
            sw_c = tk.Canvas(wrap, width=44, height=24, bg=self.colors['panel'], bd=0, highlightthickness=0, cursor='hand2')
            sw_c.pack(side='left', padx=(0, 8))
            t_lbl = tk.Label(wrap, text=text, bg=self.colors['panel'], fg=self.colors['text'], font=('Segoe UI', 9, 'bold'), cursor='hand2')
            t_lbl.pack(side='left')

            def _draw(*_):
                sw_c.delete('all')
                on = bool(var.get())
                track = '#F28C28' if on else ('#24385E' if getattr(self, '_dark', False) else '#CBD5E1')
                try:
                    from PIL import Image, ImageDraw, ImageTk
                    scale = 4
                    w, h = 44, 24
                    p_bg = self.colors['panel']
                    im = Image.new('RGB', (w*scale, h*scale), p_bg)
                    d = ImageDraw.Draw(im)
                    d.rounded_rectangle((0, 0, w*scale-1, h*scale-1), radius=(h*scale)//2, fill=track)
                    r = 9 * scale
                    cx = (w - 12) * scale if on else 12 * scale
                    cy = (h * scale) // 2
                    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill='#FFFFFF')
                    im = im.resize((w, h), Image.Resampling.LANCZOS)
                    sw_c._img = ImageTk.PhotoImage(im)
                    sw_c.create_image(0, 0, image=sw_c._img, anchor='nw')
                except Exception:
                    sw_c.create_oval(2, 2, 42, 22, fill=track, outline='')

            def _toggle(_=None):
                var.set(0 if var.get() else 1)

            var.trace_add('write', _draw)
            for w_el in (wrap, sw_c, t_lbl):
                w_el.bind('<Button-1>', _toggle)
            sw_c.after_idle(_draw)
            return wrap

        # --- CONSTRUÇÃO DAS PÁGINAS ---
        # 1. Geral
        pad_geral = add_category('geral', '⚙️ Geral')
        
        _, company=panel(pad_geral, 'Empresa')
        name=tk.StringVar(value=get_setting('company_name','Nexo'));self.settings_vars['company']=name
        logo=tk.StringVar(value=get_setting('company_logo',''));self.settings_vars['logo']=logo
        lbl(company, 'Nome da empresa').grid(row=0, column=0, sticky='w', padx=4, pady=(0, 4))
        w_name, _ = rounded_entry(company, name, width=32)
        w_name.grid(row=1, column=0, padx=(0, 10), sticky='ew')
        lbl(company, 'Logo').grid(row=0, column=1, sticky='w', padx=6, pady=(0, 4))
        w_logo, _ = rounded_entry(company, logo, width=38)
        w_logo.grid(row=1, column=1, padx=6, sticky='ew')
        sec_btn(company, 'Selecionar', lambda: self.select_logo(logo), width=115, height=34).grid(row=1, column=2, padx=6)
        pri_btn(company, 'Salvar identidade', self.save_company_settings, width=155, height=34).grid(row=1, column=3, padx=(6, 0))
        sub_lbl(company, 'Formatos aceitos: PNG, JPG/JPEG, GIF, BMP, WebP, TIFF e ICO. Mínimo recomendado: 500 px no menor lado.', wraplength=980, justify='left').grid(row=2, column=0, columnspan=4, sticky='w', padx=4, pady=(10, 0))
        company.columnconfigure(0,weight=1); company.columnconfigure(1,weight=1)

        _, appearance=panel(pad_geral, 'Aparência')
        stored_theme=get_setting('theme','light'); theme=tk.StringVar(value={'light':'Claro','dark':'Escuro','system':'Sistema'}.get(stored_theme,'Escuro'));self.settings_vars['theme']=theme
        lbl(appearance, 'Tema').pack(side='left', padx=(0, 8))
        RoundedDropdown(appearance, theme, ('Claro','Escuro','Sistema'), width=150, height=32, align='left').pack(side='left', padx=(0, 12))
        pri_btn(appearance, 'Aplicar', self.apply_theme_from_settings, width=105, height=34).pack(side='left')

        _, langbox=panel(pad_geral, 'Idioma')
        self.language_var=tk.StringVar(value=get_setting('language','Português (Brasil)'))
        lbl(langbox, 'Idioma').pack(side='left', padx=(0, 8))
        RoundedDropdown(langbox, self.language_var, ('Português (Brasil)',), width=200, height=32, align='left').pack(side='left', padx=(0, 12))
        sub_lbl(langbox, 'Outros idiomas serão adicionados na camada de tradução sem alterar os dados.').pack(side='left')

        # 2. IA
        pad_ia = add_category('ia', '🧠 Inteligência Artificial')
        _, aibox = panel(pad_ia, 'Sincronismo de Inteligência Artificial')
        ai_enabled = tk.IntVar(value=int(get_setting('ai_enabled', '0')))
        ai_provider = tk.StringVar(value=get_setting('ai_provider', 'Google Gemini'))
        ai_api_key = tk.StringVar(value=get_setting('ai_api_key', ''))
        ai_daily_limit = tk.StringVar(value=get_setting('ai_daily_limit', '50'))
        
        row1 = tk.Frame(aibox, bg=self.colors['panel']); row1.pack(fill='x', pady=(0, 14))
        capsule_toggle(row1, "Ativar Importação Inteligente (IA)", ai_enabled).pack(side='left', padx=(0, 24))
        lbl(row1, "Provedor:").pack(side='left', padx=(0, 8))
        RoundedDropdown(row1, ai_provider, ('Google Gemini', 'OpenAI ChatGPT'), width=200, height=32, align='left').pack(side='left')
        
        row2 = tk.Frame(aibox, bg=self.colors['panel']); row2.pack(fill='x', pady=(0, 14))
        lbl(row2, "Chave API (Secreta):").pack(side='left', padx=(0, 8))
        w_apikey, _ = rounded_entry(row2, ai_api_key, width=46, show='*')
        w_apikey.pack(side='left', padx=(0, 10))
        
        def show_ai_help():
            messagebox.showinfo("Ajuda: Chave de API", "Para Google Gemini:\n1. Acesse aistudio.google.com\n2. Faça login com o Google\n3. Clique em 'Get API Key' e 'Create API Key'\n4. Cole o código gerado no campo.\n\nPara OpenAI:\n1. Acesse platform.openai.com/api-keys\n2. Clique em 'Create new secret key'.", parent=self.winfo_toplevel())
            
        sec_btn(row2, "Ajuda (i)", show_ai_help, width=105, height=34).pack(side='left')
        
        row3 = tk.Frame(aibox, bg=self.colors['panel']); row3.pack(fill='x', pady=(0, 14))
        lbl(row3, "Alerta de Segurança Diário (Limitar em):").pack(side='left', padx=(0, 8))
        numeric_entry(row3, ai_daily_limit, width=10).pack(side='left', padx=(0, 8))
        lbl(row3, "leituras por dia.", font=('Segoe UI', 9)).pack(side='left')
        
        def save_ai_settings():
            set_setting('ai_enabled', str(ai_enabled.get()))
            set_setting('ai_provider', ai_provider.get())
            set_setting('ai_api_key', ai_api_key.get().strip())
            set_setting('ai_daily_limit', ai_daily_limit.get().strip())
            self.notify("Configurações de IA salvas com sucesso.")
            
        pri_btn(aibox, 'Salvar Configurações de IA', save_ai_settings, width=215, height=36).pack(anchor='w', pady=(2, 0))
        sub_lbl(aibox, 'O Nexo processa imagens apenas para fins de extração de dados e não armazena fotos na nuvem.').pack(anchor='w', pady=(8, 0))

        # 3. Métricas
        pad_met = add_category('metricas', '📈 Métricas de Custo')
        _, costs=panel(pad_met, 'Custos operacionais')
        self.cost_vars={}; settings=get_cost_settings()
        for i,n in enumerate(('Gás','Energia','Água')):
            lbl(costs, f'{n} (%)').grid(row=0, column=i, sticky='w', padx=6, pady=(0, 4))
            v=tk.StringVar(value=fmt_num(settings.get(n,20))); self.cost_vars[n]=v
            numeric_entry(costs, v, width=12).grid(row=1, column=i, padx=6)
        pri_btn(costs, 'Salvar custos', self.save_cost_settings, width=140, height=34).grid(row=1, column=3, padx=10)
        sub_lbl(costs, 'Esses percentuais entram no custo final do Produto e ficam registrados no histórico.').grid(row=2, column=0, columnspan=4, sticky='w', padx=6, pady=(10, 0))

        # 4. Unidades
        pad_un = add_category('unidades', '⚖️ Unidades de Medida')
        _, units=panel(pad_un, 'Unidades internas')
        self.base_vars={}
        for i,(key,label,vals) in enumerate((('mass_base_unit','Massa',UNITS_MASS),('volume_base_unit','Volume',UNITS_VOLUME),('count_base_unit','Quantidade',UNITS_COUNT))):
            lbl(units, label).grid(row=0, column=i, padx=6, sticky='w', pady=(0, 4))
            v=tk.StringVar(value=get_setting(key,BASE_UNITS_DEFAULT[dimension_of_unit(vals[0]) or 'count'])); self.base_vars[key]=v
            RoundedDropdown(units, v, vals, width=120, height=32, align='left').grid(row=1, column=i, padx=6)
        pri_btn(units, 'Salvar unidades internas', self.save_base_units, width=190, height=34).grid(row=1, column=3, padx=10)

        _, convbox=panel(pad_un, 'Unidades configuráveis por insumo')
        sub_lbl(convbox, 'Ex.: xícara de leite pode equivaler a 240 ml; xícara de farinha pode equivaler a outro valor.').grid(row=0, column=0, sticky='w', pady=(0, 10))
        pri_btn(convbox, 'Gerenciar conversões', self.settings_conversion_dialog, width=180, height=36).grid(row=1, column=0, sticky='w')

        # 5. DB e BI
        pad_db = add_category('banco', '💾 Banco de Dados & BI')
        _, bibox=panel(pad_db, 'Auditoria & BI')
        self.retention_var=tk.StringVar(value=get_setting('history_retention_months','36'))
        lbl(bibox, 'Retenção do histórico de edições (Meses)').pack(side='left', padx=(0, 8))
        numeric_entry(bibox, self.retention_var, width=10).pack(side='left', padx=(0, 10))
        
        def save_retention():
            try:
                v = int(self.retention_var.get().strip())
                if v < 0: raise ValueError()
                set_setting('history_retention_months', str(v))
                self.notify(f"Retenção de histórico definida para {v} meses.")
            except Exception:
                safe_error(self.winfo_toplevel(), "Erro", "Digite um número de meses válido (0 para nunca limpar).")
                
        pri_btn(bibox, 'Salvar', save_retention, width=100, height=34).pack(side='left', padx=(0, 12))
        sub_lbl(bibox, 'Itens mais antigos serão limpos automaticamente na inicialização para otimizar o banco de dados.').pack(side='left')

        _, dbbox=panel(pad_db, 'Fonte de dados')
        lbl(dbbox, 'SQLite atual').grid(row=0, column=0, sticky='w', padx=4, pady=(0, 4))
        self.db_path_var=tk.StringVar(value=str(paths.get_db_path()))
        w_db, _ = rounded_entry(dbbox, self.db_path_var, width=52)
        w_db.grid(row=1, column=0, padx=(0, 10), sticky='ew')
        sec_btn(dbbox, 'Escolher arquivo SQLite', self.choose_db_file, width=185, height=34).grid(row=1, column=1, padx=4)
        pri_btn(dbbox, 'Aplicar banco', self.apply_db_file, width=135, height=34).grid(row=1, column=2, padx=(6, 0))
        self.settings_db_status=tk.Label(dbbox,textvariable=self.status,bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9,'bold'),anchor='w')
        self.settings_db_status.grid(row=3,column=0,columnspan=3,sticky='w',padx=4,pady=(4,0))
        sub_lbl(dbbox, 'SQLite local/arquivo de rede funciona nesta versão. Conectores PostgreSQL/MySQL podem ser adicionados depois.', wraplength=980, justify='left').grid(row=2, column=0, columnspan=3, sticky='w', padx=4, pady=(10, 4))
        dbbox.columnconfigure(0,weight=1)

        _, audit=panel(pad_db, 'Auditoria do banco')
        sub_lbl(audit, 'Veja as últimas operações, diferencie INSERT/UPDATE/DELETE e confira o antes/depois das edições.').pack(anchor='w', pady=(0, 10))
        pri_btn(audit, 'Visualizar banco / auditoria', self.audit_database_dialog, width=215, height=36).pack(anchor='w')

        _, docs=panel(pad_db, 'Documentos')
        sub_lbl(docs, f'Arquivos originais ficam em: {DOCS_DIR}').pack(anchor='w')
        
        # Init
        self.refresh_settings_widgets = pad_geral # Fallback for compatibility if needed
        on_tab_click('geral')

    def settings_conversion_dialog(self):
        d=Modal(self,'Unidades configuráveis por insumo','860x600')
        material=tk.StringVar();unit=tk.StringVar();base=tk.StringVar(value='ml');factor=tk.StringVar()
        bg_col = d.cget('bg')
        fg_col = self.colors.get('text', '#18223A')
        form=tk.Frame(d,bg=bg_col,padx=16,pady=12);form.pack(fill='x')
        tk.Label(form,text='Insumo *',bg=bg_col,fg=fg_col,font=('Segoe UI',9,'bold')).grid(row=0,column=0,sticky='w',padx=5,pady=(0,4))
        mat_opts=[f'{r["id"]} — {r["name"]}' for r in list_names('materials')]
        cb=RoundedDropdown(form,material,mat_opts,width=260,height=32,align='left')
        cb.grid(row=1,column=0,padx=5)
        tk.Label(form,text='Unidade configurável *',bg=bg_col,fg=fg_col,font=('Segoe UI',9,'bold')).grid(row=0,column=1,sticky='w',padx=5,pady=(0,4))
        w_unit,_=rounded_entry(form,unit,width=16)
        w_unit.grid(row=1,column=1,padx=5)
        tk.Label(form,text='Quantidade equivalente *',bg=bg_col,fg=fg_col,font=('Segoe UI',9,'bold')).grid(row=0,column=2,sticky='w',padx=5,pady=(0,4))
        w_fac=numeric_entry(form,factor,width=14)
        w_fac.grid(row=1,column=2,padx=5)
        tk.Label(form,text='Unidade interna *',bg=bg_col,fg=fg_col,font=('Segoe UI',9,'bold')).grid(row=0,column=3,sticky='w',padx=5,pady=(0,4))
        RoundedDropdown(form,base,('mg','ml','un'),width=110,height=32,align='left').grid(row=1,column=3,padx=5)
        tree=ttk.Treeview(d,columns=('item','unit','factor','base'),show='headings')
        for k,t,w in [('item','Insumo',220),('unit','Unidade',140),('factor','Quantidade equivalente',170),('base','Unidade interna',150)]:tree.heading(k,text=t);tree.column(k,width=w)
        tree.pack(fill='both',expand=True,padx=16,pady=12)
        def load():
            cb._opts=[f'{r["id"]} — {r["name"]}' for r in list_names('materials')]
            cb.after_idle(cb._redraw)
        def refresh():
            for x in tree.get_children():tree.delete(x)
            with db() as c:
                rows=c.execute('''SELECT m.name AS material_name,cu.name AS unit_name,cu.base_unit,cu.factor_to_base FROM custom_units cu JOIN materials m ON m.id=cu.material_id ORDER BY m.name,cu.name''').fetchall()
            for r in rows:tree.insert('','end',values=(r['material_name'],r['unit_name'],r['factor_to_base'],r['base_unit']))
        def add():
            try:
                if ' — ' not in material.get():raise ValueError('Selecione um Insumo do Cadastro.')
                mid=int(material.get().split(' — ')[0]);n=unit.get().strip();b=base.get();f=to_float(factor.get(),'Quantidade equivalente')
                if not n:raise ValueError('O nome da unidade configurável é obrigatório.')
                if f<=0:raise ValueError('A Quantidade equivalente deve ser maior que zero.')
                with db() as c:
                    c.execute('INSERT INTO custom_units(material_id,name,base_unit,factor_to_base) VALUES(?,?,?,?)',(mid,n,b,f))
                    c.commit()
                unit.set('');factor.set('');refresh()
            except Exception as e:safe_error(d,'Não foi possível salvar a conversão',e)
        RoundedActionButton(form,'Adicionar',add,width=110,height=34,fill='#F28C28',hover='#BA5200',fg='#FFFFFF',bg=bg_col).grid(row=1,column=4,padx=6)
        load();refresh()
        actions=tk.Frame(d,bg=bg_col,padx=16,pady=10);actions.pack(fill='x')
        RoundedActionButton(actions,'Cancelar',d.destroy,width=110,height=36,fill='#6B7280',hover='#4B5563',fg='#FFFFFF',bg=bg_col).pack(side='right')
        RoundedActionButton(actions,'Salvar',lambda:(self.notify('Unidades configuráveis salvas.'),d.destroy()),width=110,height=36,fill='#F28C28',hover='#BA5200',fg='#FFFFFF',bg=bg_col).pack(side='right',padx=8)

    def audit_database_dialog(self):
        d=Modal(self,'Auditoria do banco de dados','1040x620')
        bg_col = d.cget('bg')
        ttk.Label(d,text='Últimas operações registradas pelo SQLite. Clique duas vezes em uma linha para ver antes/depois.',padding=12).pack(anchor='w')
        tree=ttk.Treeview(d,columns=('date','action','table','id','reason'),show='headings')
        for k,t,w in [('date','Data/hora',150),('action','Ação',90),('table','Tabela',150),('id','ID',70),('reason','Motivo da edição',430)]:
            tree.heading(k,text=t);tree.column(k,width=w)
        tree.pack(fill='both',expand=True,padx=12,pady=8)
        with db() as c:
            rows=c.execute('SELECT id,action,table_name,record_id,changed_at FROM audit_log ORDER BY id DESC LIMIT 100').fetchall()
            for r in rows:
                reason=''
                if r['action']=='UPDATE':
                    eh=c.execute('''SELECT reason FROM edit_history WHERE entity_id=? ORDER BY ABS(strftime('%s',edited_at)-strftime('%s',?)) LIMIT 1''',(r['record_id'],r['changed_at'])).fetchone()
                    reason=eh['reason'] if eh else ''
                tree.insert('', 'end', iid=str(r['id']), values=(r['changed_at'],r['action'],r['table_name'],r['record_id'] or '-',reason))
        def details(_=None):
            sel=tree.selection()
            if not sel:return
            aid=int(sel[0])
            with db() as c:r=c.execute('SELECT * FROM audit_log WHERE id=?',(aid,)).fetchone()
            if not r:return
            detail=Modal(d,'Detalhes da operação','900x560')
            ttk.Label(detail,text=f"{r['action']} — {r['table_name']} — registro ID {r['record_id']}",font=('Segoe UI',12,'bold')).pack(anchor='w',padx=16,pady=(16,8))
            ttk.Label(detail,text=f"Data/hora: {r['changed_at']}").pack(anchor='w',padx=16)
            reason=''
            if r['action']=='UPDATE':
                with db() as c:
                    eh=c.execute('SELECT reason FROM edit_history WHERE entity_id=? ORDER BY id DESC LIMIT 1',(r['record_id'],)).fetchone()
                reason=eh['reason'] if eh else ''
            ttk.Label(detail,text=f"Motivo: {reason or '—'}").pack(anchor='w',padx=16,pady=(2,10))
            txt=tk.Text(detail,wrap='word',height=22)
            txt.pack(fill='both',expand=True,padx=16,pady=8)
            txt.insert('1.0', 'ANTES\n'+(r['before_json'] or '—')+'\n\nDEPOIS\n'+(r['after_json'] or '—'))
            txt.configure(state='disabled')
            RoundedActionButton(detail,'Fechar',detail.destroy,width=110,height=36,fill='#F28C28',hover='#BA5200',fg='#FFFFFF',bg=detail.cget('bg')).pack(pady=(0,12))
        tree.bind('<Double-1>',details)
        RoundedActionButton(d,'Fechar',d.destroy,width=110,height=36,fill='#F28C28',hover='#BA5200',fg='#FFFFFF',bg=bg_col).pack(pady=(0,12))

    def choose_db_file(self):
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.db',filetypes=[('SQLite','*.db'),('Todos os arquivos','*.*')],initialfile=paths.get_db_path().name)
        if path:self.db_path_var.set(path)

    def apply_db_file(self):
        new_path=Path(self.db_path_var.get().strip())
        if not new_path:
            messagebox.showerror('Banco de dados','Informe um caminho para o banco SQLite.',parent=self);return
        try:
            paths.set_db_path(new_path);new_path.parent.mkdir(parents=True,exist_ok=True);save_file_config();init_db();self._update_db_status();self.refresh_all();messagebox.showinfo('Banco de dados','Banco SQLite aplicado. O Nexo continuará usando este arquivo nas próximas execuções.',parent=self)
        except Exception as e:safe_error(self,'Não foi possível aplicar o banco',e)

    def refresh_settings(self):
        if hasattr(self,'header_title'):
            name=get_setting('company_name','Nexo') or 'Nexo'
            if getattr(self,'current_page',None) == 'Geral':
                self.header_title.config(text='Início')
                self.header_subtitle.config(text='Visão geral do seu negócio')
            self.company_label.config(text='')
            if hasattr(self, 'sidebar_nav'):
                self.sidebar_nav.set_brand(name)
            logo=get_setting('company_logo','').strip()
            if not logo or not Path(logo).exists():
                self.header_logo.configure(image='',text='')
                self.header_logo_img=None
                return
            source=Path(logo)
            try:
                from PIL import Image, ImageTk
                img=Image.open(source).convert('RGBA')
                max_w,max_h=54,54
                scale=min(max_w/img.width,max_h/img.height,1.0)
                if scale < 1.0:
                    img=img.resize((max(1,int(img.width*scale)),max(1,int(img.height*scale))), Image.Resampling.LANCZOS)
                img2=Image.open(source).convert('RGBA')
                max_w2,max_h2=38,38
                scale2=min(max_w2/img2.width,max_h2/img2.height,1.0)
                if scale2 < 1.0:
                    img2=img2.resize((max(1,int(img2.width*scale2)),max(1,int(img2.height*scale2))), Image.Resampling.LANCZOS)
                self.header_logo_img=ImageTk.PhotoImage(img2)
                self.header_logo.configure(image=self.header_logo_img,text='')
            except Exception:
                try:
                    self.header_logo_img=tk.PhotoImage(file=str(source)); self.header_logo.configure(image=self.header_logo_img,text='')
                except Exception:
                    self.header_logo.configure(image='',text='')

    def select_logo(self,var):
        path=filedialog.askopenfilename(parent=self,filetypes=[('Imagens','*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp;*.tif;*.tiff;*.ico'),('PNG','*.png'),('JPEG','*.jpg;*.jpeg'),('GIF','*.gif'),('BMP','*.bmp'),('WebP','*.webp'),('TIFF','*.tif;*.tiff'),('Ícone','*.ico'),('Todos os arquivos','*.*')])
        if path:
            try:
                from PIL import Image
                with Image.open(path) as im:
                    if min(im.size) < 500:
                        messagebox.showwarning('Logo','A imagem selecionada tem menos de 500 px no menor lado. Ela pode perder qualidade ao ser exibida maior. O Nexo não irá corrigir a imagem.',parent=self)
            except Exception:
                pass
            var.set(path)

    def save_company_settings(self):
        name=normalize_text(self.settings_vars['company'].get().strip()) or 'Nexo'
        logo=self.settings_vars['logo'].get().strip()
        set_setting('company_name',name);set_setting('company_logo',logo);self.refresh_settings();self.notify('Identidade da empresa salva.')

    def save_cost_settings(self):
        try:
            vals={n:to_float(v.get(),n) for n,v in self.cost_vars.items()}
            for n,v in vals.items():
                if v<0:raise ValueError(f'O percentual de {n} não pode ser negativo.')
            with db() as c:
                for n,v in vals.items():c.execute('UPDATE cost_settings SET percentage=? WHERE name=?',(v,n))
                c.commit()
            snapshot_costs();self.refresh_all();self.notify('Custos operacionais salvos.')
        except Exception as e:safe_error(self,'Não foi possível salvar os custos operacionais',e)

    def save_base_units(self):
        try:
            desired={k:v.get() for k,v in self.base_vars.items()}
            old={k:get_setting(k,BASE_UNITS_DEFAULT[dimension_of_unit({'mass_base_unit':'mg','volume_base_unit':'ml','count_base_unit':'un'}[k])]) for k in desired}
            with db() as c:
                for key,new_unit in desired.items():
                    old_unit=old[key]
                    if old_unit==new_unit: continue
                    old_factor=unit_factor_to_default_base(old_unit);new_factor=unit_factor_to_default_base(new_unit)
                    for row in c.execute('SELECT id,base_unit,factor_to_base FROM custom_units').fetchall():
                        if row['base_unit']==old_unit:
                            factor_new=row['factor_to_base']*old_factor/new_factor
                            c.execute('UPDATE custom_units SET base_unit=?,factor_to_base=? WHERE id=?',(new_unit,factor_new,row['id']))
                    c.execute('UPDATE system_settings SET value=? WHERE key=?',(new_unit,key))
                c.commit()
            snapshot_costs();self.notify('Unidades internas salvas e conversões ajustadas.')
        except Exception as e:safe_error(self,'Não foi possível salvar as unidades internas',e)

