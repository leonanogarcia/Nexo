    def _tree_click(self, event, tree, kind):
        iid=tree.identify_row(event.y); col=tree.identify_column(event.x)
        if not iid or tree.parent(iid): return
        # Action columns are identified by their fixed position, so image-only
        # headers remain clickable even when the heading text is intentionally blank.
        action_cols={
            'material':('#9','#10'),
            'recipe':('#6','#7'),
            'product':('#6','#7'),
        }
        edit_col,delete_col=action_cols.get(kind,('', ''))
        if col==edit_col:
            self._set_single_checked(tree,iid)
            {'material':self.edit_selected_material,'recipe':self.edit_selected_recipe,'product':self.edit_selected_product}[kind]()
            return 'break'
        if col==delete_col:
            self._set_single_checked(tree,iid)
            {'material':self.delete_selected_material,'recipe':self.delete_selected_recipe,'product':self.delete_selected_product}[kind]()
            return 'break'
        # Expand/collapse indicator always wins and never changes selection.
        if col=='#0':
            try: element=tree.identify_element(event.x,event.y)
            except Exception: element=''
            if 'indicator' in element:
                tree.item(iid, open=not bool(tree.item(iid,'open')))
                return 'break'
            bbox=tree.bbox(iid,'#0')
            checkbox_zone=(bbox[0], bbox[0]+58) if bbox else (0,58)
            if checkbox_zone[0] <= event.x <= checkbox_zone[1]:
                self._toggle_checkbox(tree,iid)
                return 'break'
        # Any other click in the row always becomes a single selection.
        self._set_single_checked(tree,iid)
        return 'break'

    # ---------- Cadastro ----------
    def _build_page_toolbar(self, parent):
        # Barra em cápsula única, sem molduras extras nos campos.
        shell=RoundedPanel(parent, fill=self.colors['panel'], border='#E2EAF5', radius=22, bg=self.colors['bg'], height=84)
        shell.pack(fill='x', padx=0, pady=(0,14)); shell.pack_propagate(False)
        inner=tk.Frame(shell,bg=self.colors['panel'])
        inner.pack(fill='both', expand=True, padx=24, pady=17)
        return shell, inner

    def _build_page_table_panel(self, parent):
        shell=RoundedPanel(parent, fill=self.colors['panel'], border='#E5ECF5', radius=22, bg=self.colors['bg'])
        shell.pack(fill='both', expand=True, padx=0, pady=(0,12))
        inner=tk.Frame(shell,bg=self.colors['panel'])
        inner.pack(fill='both', expand=True, padx=12, pady=12)
        return shell, inner

    def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)
        wrap.pack(side='left',padx=(14,0))
        return wrap.entry


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

    def cadastro(self, f):
        _, bar = self._build_page_toolbar(f)
        mat_add=RoundedActionButton(bar, '＋  Novo item', lambda: self._run_normal_action(self.mat_tree, self.new_material), width=177, height=49, fill='#2F67B1', hover='#255894'); mat_add.pack(side='left')
        mat_history=RoundedActionButton(bar, '◷  Histórico', lambda: self._run_normal_action(self.mat_tree, self.material_history_dialog), width=148, height=49, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557'); mat_history.pack(side='left', padx=10)
        mat_conv=RoundedActionButton(bar, '⇄  Conversões do item', lambda: self._run_normal_action(self.mat_tree, self.material_conversion_dialog), width=217, height=49, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557'); mat_conv.pack(side='left')
        self.mat_bulk_delete_btn=ttk.Button(bar, text='🗑 Excluir', style='Soft.TButton', command=self.delete_selected_materials, state='disabled')
        tk.Label(bar,text='',bg=self.colors['panel'],width=1).pack(side='left')
        self.mat_search=tk.StringVar(); self.mat_search.trace_add('write',lambda *a:self.refresh_materials())
        # A pesquisa ocupa todo o espaço restante da toolbar, permitindo que a tela
        # acompanhe o redimensionamento da janela sem deixar uma faixa vazia fixa.
        self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,58)
        self.mat_search_wrap.pack_configure(side='left',padx=(14,0),fill='x',expand=True)

        _,table_host=self._build_page_table_panel(f)
        # Cabeçalho em cápsula: mais fino e com extremidades semicirculares,
        # seguindo a referência e redimensionando junto com a tabela.
        self.mat_header=tk.Canvas(table_host,bg=self.colors['panel'],bd=0,highlightthickness=0,height=36)
        self.mat_header.pack(fill='x',padx=2,pady=(0,0))
        self.mat_tree=ttk.Treeview(table_host,columns=('code','name','brand','qty','unit','value','category','date','mod_date','status','edit','delete','options'),show='tree')
        self.mat_tree.tag_configure('inactive', foreground='#9AA9BF')
        self.mat_tree.column('#0',width=18,minwidth=18,stretch=False)
        for k,t,w in [('code','Código',100),('name','Item',190),('brand','Marca',150),('qty','Quantidade',120),('unit','Un.',70),('value','Valor',100),('category','Categoria',130),('date','Último cadastro',135),('edit','',46),('delete','',46)]:
            self.mat_tree.column(k,width=w,anchor='w',stretch=True)
        self.mat_tree.pack(fill='both',expand=True)

        self._mat_header_specs=[('code','Código'),('name','Item'),('brand','Marca'),('qty','Quantidade'),('unit','Un.'),('value','Valor'),('category','Categoria'),('date','Último cadastro'),('edit',''),('delete','')]
        self._mat_header_imgs={
            'edit': self._action_photo('action_edit_reference_exact.png'),
            'delete': self._action_photo('action_delete_reference_exact.png'),
        }
        def redraw_mat_header(_event=None):
            c=self.mat_header; c.delete('all')
            w=max(c.winfo_width(),2); h=max(c.winfo_height(),2)
            # Smooth rounded heading background matching the reference.
            r=min(h/2,18); fill='#EEF4FB'
            c.create_rectangle(r,0,w-r,h,fill=fill,outline='')
            c.create_rectangle(0,r,w,h-r,fill=fill,outline='')
            c.create_arc(0,0,2*r,2*r,start=90,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,0,w,2*r,start=0,extent=90,fill=fill,outline=fill)
            c.create_arc(0,h-2*r,2*r,h,start=180,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,h-2*r,w,h,start=270,extent=90,fill=fill,outline=fill)
            x0=0
            # Use the actual configured tree column widths so the header remains aligned on resize.
            cols=[('#0','')]+[(f'#{i}',txt) for i,(key,txt) in enumerate(self._mat_header_specs,1)]
            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.mat_tree.column(col,'width'))
                except Exception: cw=0
                if col=='#0':
                    x0+=cw; continue
                if col=='#9':
                    img=self._mat_header_imgs.get('edit')
                    if img: c.create_image(x0+cw/2,h/2,image=img,anchor='center')
                elif col=='#10':
                    img=self._mat_header_imgs.get('delete')
                    if img: c.create_image(x0+cw/2,h/2,image=img,anchor='center')
                else:
                    c.create_text(x0+cw/2,h/2,text=txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor='center')
                x0+=cw
        self._redraw_mat_header=redraw_mat_header
        self.mat_header.bind('<Configure>',redraw_mat_header)
        self.mat_tree.bind('<Configure>',lambda e:redraw_mat_header())
        self.after_idle(redraw_mat_header)

        # Estado vazio: ícone extraído/reconstruído a partir da referência, sem substituir por um símbolo genérico.
        self.mat_empty_overlay=tk.Frame(table_host,bg=self.colors['panel'],bd=0,highlightthickness=0)
        self.mat_empty_overlay.place(x=0,y=36,relwidth=1,relheight=1,height=-36)
        # Conteúdo do estado vazio centralizado de forma responsiva, em vez de
        # usar um deslocamento vertical fixo que fica errado ao redimensionar.
        self.mat_empty_content=tk.Frame(self.mat_empty_overlay,bg=self.colors['panel'],bd=0,highlightthickness=0)
        self.mat_empty_content.place(relx=.5,rely=.5,anchor='center')
        try:
            from PIL import Image,ImageTk
            self._empty_state_img=ImageTk.PhotoImage(Image.open(UI_ASSETS/'empty_state_reference_exact.png').convert('RGBA'))
            tk.Label(self.mat_empty_content,image=self._empty_state_img,bg=self.colors['panel'],bd=0,highlightthickness=0).pack(pady=(0,5))
        except Exception:
            tk.Label(self.mat_empty_content,text='',bg=self.colors['panel']).pack(pady=(0,5))
        tk.Label(self.mat_empty_content,text='Ainda não há registros cadastrados.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',11,'bold')).pack()
        tk.Label(self.mat_empty_content,text='Clique em + Novo item para adicionar o primeiro item.',bg=self.colors['panel'],fg=self.colors['muted'],font=('Segoe UI',9)).pack(pady=(4,0))
        self._action_buttons[self.mat_tree]={'normal':[mat_add,mat_history,mat_conv],'bulk':[self.mat_bulk_delete_btn]}
        self.mat_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.mat_tree,'material'))
        self.mat_tree.bind('<Double-1>',lambda e:self.edit_selected_material())
        self._update_action_states()

    def material_form(self, edit_id=None):
        is_edit = edit_id is not None
        with db() as c:
            existing = c.execute('SELECT * FROM materials WHERE id=?', (edit_id,)).fetchone() if is_edit else None
        d = Modal(self, 'Editar item' if is_edit else 'Novo item', '720x500')
        vars = {k: tk.StringVar() for k in ('name','brand','qty','unit','value','category','date')}
        if existing:
            for k in vars:
                if k == 'date': vars[k].set(date.today().isoformat())
                elif k == 'qty': vars[k].set(fmt_num(existing['purchase_qty']))
                elif k == 'value': vars[k].set(fmt(existing['purchase_value']))
                elif k == 'unit': vars[k].set(existing['purchase_unit'])
                elif k == 'category': vars[k].set(existing['category'] or 'Comestível')
                elif k == 'name': vars[k].set(existing['name'])
                elif k == 'brand': vars[k].set(existing['brand'] or '')
        else:
            vars['unit'].set(''); vars['category'].set('Comestível'); vars['date'].set(date.today().isoformat())
        form = ttk.Frame(d, padding=18); form.pack(fill='both', expand=True)
        fields = [
            ('Nome *','name',0,0),('Marca','brand',0,1),('Quantidade *','qty',1,0),('Unidade *','unit',1,1),
            ('Valor da compra *','value',2,0),('Categoria *','category',2,1),('Data *','date',3,0)
        ]
        for label,key,row,col in fields:
            ttk.Label(form,text=label).grid(row=row*2,column=col,sticky='w',padx=6,pady=(4,0))
            if key == 'unit':
                w=ttk.Combobox(form,textvariable=vars[key],values=UNITS,state='readonly',width=20)
            elif key == 'category':
                w=ttk.Combobox(form,textvariable=vars[key],values=('Comestível','Não comestível','Doação'),state='readonly',width=20)
            elif key == 'value':
                w=masked_money_entry(form, vars[key], width=28)
            elif key == 'qty':
                w=numeric_entry(form, vars[key], width=28)
            else:
                w,_entry=rounded_entry(form, vars[key], width=28)
            w.grid(row=row*2+1,column=col,sticky='ew',padx=6,pady=(0,8))
        form.columnconfigure(0,weight=1); form.columnconfigure(1,weight=1)
        ttk.Label(form,text='* campo obrigatório').grid(row=8,column=0,columnspan=2,sticky='w',padx=6,pady=8)
        def save():
            try:
                name = vars['name'].get().strip(); brand = vars['brand'].get().strip(); unit = vars['unit'].get().strip(); category = vars['category'].get().strip()
                if not name: raise ValueError('O campo "Nome" é obrigatório.')
                if not unit: raise ValueError('O campo "Unidade" é obrigatório.')
                if not category: raise ValueError('O campo "Categoria" é obrigatório.')
                qty = to_float(vars['qty'].get(),'Quantidade')
                value = money_to_float(vars['value'].get(),'Valor da compra')
                if qty <= 0: raise ValueError('A Quantidade deve ser maior que zero.')
                if value < 0: raise ValueError('O Valor da compra não pode ser negativo.')
                if value == 0 and category != 'Doação': raise ValueError('Valor zero só é permitido para itens da categoria Doação.')
                purchase_date = vars['date'].get().strip()
                if not purchase_date: raise ValueError('O campo "Data" é obrigatório.')
                if is_edit:
                    with db() as c: before = dict(c.execute('SELECT * FROM materials WHERE id=?', (edit_id,)).fetchone())
                    self.ask_edit_reason('INSUMO', edit_id, before, {'name':name,'purchase_qty':qty,'purchase_unit':unit,'purchase_value':value,'brand':brand,'category':category})
                with db() as c:
                    if is_edit:
                        mid = edit_id
                        c.execute('UPDATE materials SET name=?,purchase_qty=?,purchase_unit=?,purchase_value=?,brand=?,category=?,updated_at=? WHERE id=?',
                                  (name,qty,unit,value,brand,category,now_iso(),edit_id))
                    else:
                        code = next_code('materials','INS')
                        cur = c.execute('INSERT INTO materials(code,name,purchase_qty,purchase_unit,purchase_value,brand,category,updated_at) VALUES(?,?,?,?,?,?,?,?)',
                                         (code,name,qty,unit,value,brand,category,now_iso()))
                        mid = cur.lastrowid
                        c.execute('INSERT INTO purchases(material_id,qty,unit,value,brand,purchase_date) VALUES(?,?,?,?,?,?)', (mid,qty,unit,value,brand,purchase_date))
                snapshot_costs(); d.destroy(); self.refresh_all(); self.notify('Insumo salvo com sucesso.')
            except Exception as e: safe_error(d,'Não foi possível salvar o item',e)
        act=d.action_host
        right=tk.Frame(act,bg=d.cget('bg'));right.pack(side='right',fill='y')
        RoundedActionButton(right,'Salvar',save,width=92,height=38,fill='#F28C28',hover='#D96F0B').pack(side='left',padx=(6,0),pady=7)
        RoundedActionButton(right,'Cancelar',d.destroy,width=92,height=38,fill='#6B7280',hover='#4B5563').pack(side='left',padx=(6,0),pady=7)

    def new_material(self): self.material_form()

    def delete_selected_material(self):
        s=self.mat_tree.selection()
        if not s or self._selection_count(self.mat_tree)!=1:return
        code=self.mat_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM materials WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:
            refs=(c.execute('SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?',(r['id'],)).fetchone()['n']
                  + c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",(r['id'],)).fetchone()['n']
                  + c.execute('SELECT COUNT(*) n FROM custom_units WHERE material_id=?',(r['id'],)).fetchone()['n'])
        if refs:
            if messagebox.askyesno('Insumo vinculado','Este Insumo possui vínculos e não pode ser excluído sem quebrar relações. Deseja inativá-lo?',parent=self):
                with db() as c:c.execute('UPDATE materials SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Insumo inativado com sucesso.')
            return
        if not messagebox.askyesno('Excluir Insumo',f'Excluir "{r["name"]}"? O histórico de compras também será removido.',parent=self):return
        with db() as c:c.execute('DELETE FROM materials WHERE id=?',(r['id'],))
        self.refresh_all();self.notify('Insumo excluído com sucesso.')

    def delete_selected_materials(self):
        self._bulk_delete_list(self.mat_tree,'material')

    def delete_selected_recipes(self):
        self._bulk_delete_list(self.rec_tree,'recipe')

    def _bulk_delete_list(self, tree, kind):
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
        linked=[]
        with db() as c:
            for r in rows:
                if kind=='material':
                    refs=(c.execute('SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?',(r['id'],)).fetchone()['n'] + c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",(r['id'],)).fetchone()['n'] + c.execute('SELECT COUNT(*) n FROM custom_units WHERE material_id=?',(r['id'],)).fetchone()['n'])
                elif kind=='recipe':
                    refs=c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='RECIPE_BASE' AND ref_id=?",(r['id'],)).fetchone()['n']
                else:
                    refs=(c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='PRODUCT' AND ref_id=?",(r['id'],)).fetchone()['n'])
                if refs: linked.append(r)
        if linked:
            msg=('Os seguintes itens possuem vínculos/histórico:\n\n'
                 + '\n'.join('• '+r['name'] for r in linked)
                 + '\n\nDeseja inativá-los? Se escolher Não, toda a operação será cancelada.')
            if not messagebox.askyesno('Itens vinculados',msg,parent=self): return
            with db() as c:
                for r in linked:c.execute(f'UPDATE {table} SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
            # Unlinked selected items are still deleted only if all are explicitly confirmed below.
            unlinked=[r for r in rows if r['id'] not in {x['id'] for x in linked}]
            if unlinked and not messagebox.askyesno('Excluir itens',f'Excluir também os {len(unlinked)} itens sem vínculos selecionados?',parent=self):
                self.refresh_all(); return
            with db() as c:
                for r in unlinked:c.execute(f'DELETE FROM {table} WHERE id=?',(r['id'],))
            self.refresh_all();self.notify('Seleção processada com sucesso.');return
        
        
        
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
        
        msg = f'Voce selecionou {len(rows)} itens.\n'
        if linked:
            msg += f'\n{len(linked)} itens possuem vinculos/historico e serao apenas INATIVADOS.\n'
        if unlinked:
            msg += f'\nOs outros {len(unlinked)} itens sem vinculos serao EXCLUIDOS.\n'
            
        msg += '\nDeseja prosseguir com a operacao conjunta? Se escolher Nao, TUDO sera cancelado.'
            
        if not messagebox.askyesno('Confirmar operacao em lote', msg, parent=self): return
        
        with db() as c:
            for r in unlinked:
                c.execute(f'DELETE FROM {table} WHERE id=?',(r['id'],))
            for r in linked:
                c.execute(f'UPDATE {table} SET active=0, updated_at=? WHERE id=?', (now_iso(), r['id']))
                
        self.refresh_all()
        self.notify(f'{len(unlinked)} excluidos, {len(linked)} inativados.')


