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

class MaterialsPageMixin:
    def cadastro(self, f):
        hidden = get_setting('mat_hidden_cols')
        if isinstance(hidden, str):
            try:
                import ast
                hidden = ast.literal_eval(hidden)
            except:
                pass
        if isinstance(hidden, str):
            hidden = [hidden] if hidden else ['code']
        elif not isinstance(hidden, list):
            hidden = ['code']
        self._mat_hidden_cols = hidden
        
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
        
        for k,w in [('code',100),('barcode',130),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135),('status',90),('edit',30),('delete',30),('options',30)]:
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
        
        valid_keys = [spec[0] for spec in self._mat_header_specs]
        disp = [c for c in valid_keys if c not in self._mat_hidden_cols]
        self.mat_tree['displaycolumns'] = disp
        
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
                total_w = sum(int(self.mat_tree.column(col, 'width')) for col in ['#0'] + list(self.mat_tree['displaycolumns']))
                x_offset = float(self.mat_tree.xview()[0]) * total_w
            except Exception:
                x_offset = 0
            
            x0 = -x_offset
            
            disp = self.mat_tree['displaycolumns']
            if disp == ('#all',):
                disp = self.mat_tree['columns']
                
            spec_dict = {key: txt for key, txt, _ in self._mat_header_specs}
            
            cols = [('#0', '', 'dummy')]
            for i, col_id in enumerate(disp, 1):
                cols.append((f'#{i}', spec_dict.get(col_id, ''), col_id))
            
            for idx,(col,txt,key) in enumerate(cols):
                try: cw=int(self.mat_tree.column(col,'width'))
                except Exception: cw=0
                
                if col == '#0': cw = 60
                if key in ('dummy', 'edit', 'delete', 'options'):
                    x0+=cw; continue
                
                align = 'w' if key in ('barcode', 'name', 'brand') else 'center'
                anchor_x = x0+12 if align == 'w' else x0+cw/2
                tag = f'hdr_{key}'
                
                arrow_txt = ''
                if getattr(self, '_mat_order_by', 'name') == key:
                    arrow_txt = ' ↑' if getattr(self, '_mat_order_dir', 'ASC') == 'ASC' else ' ↓'
                
                full_txt = txt + arrow_txt if align == 'w' else arrow_txt + txt
                tid = c.create_text(anchor_x, h/2, text=full_txt, fill='#60769D', font=('Segoe UI',9,'bold'), anchor=align, tags=(tag,))
                
                c.create_rectangle(x0, 0, x0+cw, h, fill='', outline='', tags=(tag,))
                
                c.tag_bind(tag, '<Enter>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#BA5200'))
                c.tag_bind(tag, '<Leave>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#60769D'))
                c.tag_bind(tag, '<Button-1>', lambda e, k=key: self._sort_mat_col(k))
                c.tag_bind(tag, '<Enter>', lambda e: c.config(cursor='hand2'), add='+')
                c.tag_bind(tag, '<Leave>', lambda e: c.config(cursor=''), add='+')
                
                c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                x0+=cw
                
            try: cw0=int(self.mat_tree.column('#0','width'))
            except Exception: cw0=60
            if cw0 > 0:
                c.create_rectangle(r, 0, cw0, h, fill=fill, outline='')
                c.create_rectangle(0, r, cw0, h-r, fill=fill, outline='')
                c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=fill, outline=fill)
                c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=fill, outline=fill)
                c.create_line(cw0, 6, cw0, h-6, fill=self.colors.get('line', '#E5ECF5'))
                
                key_tree = str(self.mat_tree)
                checked = self._checked_rows.get(key_tree, set())
                children = self.mat_tree.get_children()
                is_all_checked = len(checked) == len(children) and len(children) > 0
                
                chk_id = c.create_image(cw0/2, h/2, image=self._img_chk_on if is_all_checked else self._img_chk_off, anchor='center', tags=('header_chk',))
                hitbox_id = c.create_rectangle(0, 0, cw0-2, h, fill='', outline='', tags=('header_chk',))
                c.tag_bind('header_chk', '<Button-1>', lambda e: self._toggle_all_checkboxes(self.mat_tree))
                
            try:
                disp_list = list(disp)
                idx_edit = f"#{disp_list.index('edit') + 1}" if 'edit' in disp_list else None
                idx_del = f"#{disp_list.index('delete') + 1}" if 'delete' in disp_list else None
                idx_opt = f"#{disp_list.index('options') + 1}" if 'options' in disp_list else None
                
                cw11 = int(self.mat_tree.column(idx_edit, 'width')) if idx_edit else 0
                cw12 = int(self.mat_tree.column(idx_del, 'width')) if idx_del else 0
                cw13 = int(self.mat_tree.column(idx_opt, 'width')) if idx_opt else 0
            except Exception:
                cw11, cw12, cw13 = 30, 30, 30
                
            fixed_right_w = cw11 + cw12 + cw13
            
            if fixed_right_w > 0:
                start_x = w - fixed_right_w
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
                    cx += cw12
                
                if cw13 > 0:
                    import math
                    from PIL import Image, ImageDraw, ImageTk
                    
                    if 'gear_normal' not in self._mat_header_imgs:
                        def make_gear(color):
                            img = Image.new('RGBA', (128, 128), (0,0,0,0))
                            draw = ImageDraw.Draw(img)
                            gcx, gcy = 64, 64
                            
                            for i in range(3):
                                angle = i * (math.pi / 3)
                                x1 = gcx + 48 * math.cos(angle)
                                y1 = gcy + 48 * math.sin(angle)
                                x2 = gcx - 48 * math.cos(angle)
                                y2 = gcy - 48 * math.sin(angle)
                                draw.line([x1, y1, x2, y2], fill=color, width=22)
                            
                            draw.ellipse([gcx-36, gcy-36, gcx+36, gcy+36], fill=color)
                            
                            draw.ellipse([gcx-14, gcy-14, gcx+14, gcy+14], fill='#EEF4FB')
                            
                            return ImageTk.PhotoImage(img.resize((16, 16), Image.Resampling.LANCZOS))
                        
                        self._mat_header_imgs['gear_normal'] = make_gear('#60769D')
                        self._mat_header_imgs['gear_hover'] = make_gear('#F28C28')

                    c.create_image(cx + cw13/2, h/2, image=self._mat_header_imgs['gear_normal'], anchor='center', tags=('mat_gear', 'mat_gear_img'))
                    c.create_rectangle(cx, 0, cx+cw13, h, fill='', outline='', tags=('mat_gear',))
                    
                    c.tag_bind('mat_gear', '<Enter>', lambda e, c=c: (c.itemconfig('mat_gear_img', image=self._mat_header_imgs['gear_hover']), c.config(cursor='hand2')))
                    c.tag_bind('mat_gear', '<Leave>', lambda e, c=c: (c.itemconfig('mat_gear_img', image=self._mat_header_imgs['gear_normal']), c.config(cursor='')))
                    c.tag_bind('mat_gear', '<Button-1>', lambda e: self._show_mat_col_menu(e))

        self._redraw_mat_header=redraw_mat_header
        self.mat_header.bind('<Configure>', redraw_mat_header)
        self.mat_tree.bind('<Configure>', lambda e: self.mat_tree.after_idle(redraw_mat_header))
        self.after_idle(redraw_mat_header)
        
        self._setup_canvas_header_drag(self.mat_header, self.mat_tree, ['edit','delete','options'], redraw_mat_header, 'mat')

        self.mat_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.mat_tree,'material'))
        self.mat_tree.bind('<Double-1>',lambda e: (self.edit_selected_material(), 'break')[1])
        
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

    def material_form(self, edit_id=None):
        is_edit = edit_id is not None
        with db() as c:
            existing = c.execute('SELECT * FROM materials WHERE id=?', (edit_id,)).fetchone() if is_edit else None
        d = Modal(self, 'Editar item' if is_edit else 'Novo item', '620x330')
        vars = {k: tk.StringVar() for k in ('name','brand','qty','unit','value','category','date','barcode')}
        if existing:
            for k in vars:
                if k == 'date': vars[k].set(date.today().isoformat())
                elif k == 'qty': vars[k].set(fmt_num(existing['purchase_qty']))
                elif k == 'value': vars[k].set(fmt(existing['purchase_value']))
                elif k == 'unit': vars[k].set(existing['purchase_unit'])
                elif k == 'category': vars[k].set(existing['category'] or 'Comestível')
                elif k == 'name': vars[k].set(existing['name'])
                elif k == 'brand': vars[k].set(existing['brand'] or '')
                elif k == 'barcode': vars[k].set(existing['barcode'] or '')
        else:
            vars['unit'].set(''); vars['category'].set('Comestível'); vars['date'].set(date.today().isoformat())
        form = tk.Frame(d, bg=d.cget('bg'), padx=24, pady=20); form.pack(fill='both', expand=True)
        try: text_col = self.colors.get('text', '#18223A')
        except: text_col = '#18223A'
        
        def make_field(parent, label, key, w_chars, w_pixels=None):
            wrap = tk.Frame(parent, bg=d.cget('bg'))
            tk.Label(wrap, text=label, bg=d.cget('bg'), fg=text_col, font=('Segoe UI', 9)).pack(anchor='w', padx=4, pady=(1,0))
            if key == 'unit':
                wd = RoundedDropdown(wrap, vars[key], UNITS, width=w_pixels or 140, align='left')
            elif key == 'category':
                wd = RoundedDropdown(wrap, vars[key], ['Comestível','Não comestível','Doação'], width=w_pixels or 180, align='left')
            elif key == 'value':
                wd = masked_money_entry(wrap, vars[key], width=w_chars)
            elif key == 'qty':
                wd = numeric_entry(wrap, vars[key], width=w_chars)
            else:
                wd, _ = rounded_entry(wrap, vars[key], width=w_chars)
            wd.pack(fill='x', expand=True, padx=4, pady=(0,8))
            return wrap

        r1 = tk.Frame(form, bg=d.cget('bg')); r1.pack(fill='x', pady=4)
        make_field(r1, 'Nome *', 'name', 38).pack(side='left', fill='x', expand=True)
        make_field(r1, 'Marca', 'brand', 18).pack(side='left', fill='x')

        r2 = tk.Frame(form, bg=d.cget('bg')); r2.pack(fill='x', pady=4)
        make_field(r2, 'Quantidade *', 'qty', 12).pack(side='left')
        make_field(r2, 'Unidade *', 'unit', 10, w_pixels=140).pack(side='left')
        make_field(r2, 'Valor da compra *', 'value', 16).pack(side='left', fill='x', expand=True)

        r3 = tk.Frame(form, bg=d.cget('bg')); r3.pack(fill='x', pady=4)
        make_field(r3, 'Categoria *', 'category', 14, w_pixels=180).pack(side='left')
        make_field(r3, 'Cód. Barras', 'barcode', 16).pack(side='left', fill='x', expand=True)
        make_field(r3, 'Data *', 'date', 14).pack(side='left')
        
        def save():
            try:
                name = vars['name'].get().strip(); brand = vars['brand'].get().strip(); unit = vars['unit'].get().strip(); category = vars['category'].get().strip(); barcode = vars['barcode'].get().strip()
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
                    self.ask_edit_reason('INSUMO', edit_id, before, {'name':name,'purchase_qty':qty,'purchase_unit':unit,'purchase_value':value,'brand':brand,'category':category,'barcode':barcode})
                with db() as c:
                    if is_edit:
                        mid = edit_id
                        c.execute('UPDATE materials SET name=?,purchase_qty=?,purchase_unit=?,purchase_value=?,brand=?,category=?,barcode=?,updated_at=? WHERE id=?',
                                  (name,qty,unit,value,brand,category,barcode,now_iso(),edit_id))
                    else:
                        code = next_code('materials','INS')
                        cur = c.execute('INSERT INTO materials(code,name,purchase_qty,purchase_unit,purchase_value,brand,category,barcode,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',
                                         (code,name,qty,unit,value,brand,category,barcode,now_iso()))
                        mid = cur.lastrowid
                        c.execute('INSERT INTO purchases(material_id,qty,unit,value,brand,purchase_date) VALUES(?,?,?,?,?,?)', (mid,qty,unit,value,brand,purchase_date))
                snapshot_costs(); d.destroy(); self.refresh_all(); self.notify('Insumo salvo com sucesso.')
            except Exception as e: safe_error(d,'Não foi possível salvar o item',e)
        act=d.action_host
        left=tk.Frame(act,bg=d.cget('bg'));left.pack(side='left',fill='y')
        try: muted_col = self.colors.get('muted', '#687796')
        except: muted_col = '#687796'
        tk.Label(left, text='* campo obrigatório', bg=d.cget('bg'), fg=muted_col, font=('Segoe UI', 9, 'italic')).pack(side='left', padx=16, pady=7)
        
        right=tk.Frame(act,bg=d.cget('bg'));right.pack(side='right',fill='y')
        RoundedActionButton(right,'Salvar',save,width=92,height=38,fill='#F28C28',hover='#BA5200').pack(side='left',padx=(6,0),pady=7)
        RoundedActionButton(right,'Cancelar',d.destroy,width=92,height=38,fill='#6B7280',hover='#4B5563').pack(side='left',padx=(6,0),pady=7)

    def new_material(self): self.material_form()

    def delete_selected_material(self):
        self._bulk_delete_list(self.mat_tree, 'material', use_selection_only=True)

    def delete_selected_materials(self):
        self._bulk_delete_list(self.mat_tree, 'material')

    def delete_selected_recipes(self):
        self._bulk_delete_list(self.rec_tree, 'recipe')

    def _bulk_delete_list(self, tree, kind, use_selection_only=False):
        if use_selection_only:
            s = tree.selection()
            if s: checked = {s[0]}
            else: return
        else:
            checked=getattr(self,'_checked_rows',{}).get(str(tree),set())
            if not checked:
                s = tree.selection()
                if s: checked = {s[0]}
                else: return
            
        table={'material':'materials','recipe':'base_recipes','product':'products'}[kind]
        rows=[]
        with db() as c:
            for iid in checked:
                vals=tree.item(iid,'values'); code=vals[0] if vals else ''
                r=c.execute(f'SELECT id,name,COALESCE(active,1) as active FROM {table} WHERE code=?',(code,)).fetchone()
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
                    refs = c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='PRODUCT' AND ref_id=?",(r['id'],)).fetchone()['n']
                if refs > 0: linked.append(r)
                else: unlinked.append(r)
        
        # Custom UI Modal
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        top.geometry(f"540x380+{self.winfo_screenwidth()//2 - 270}+{self.winfo_screenheight()//2 - 190}")
        bg_color = '#000001'
        top.attributes('-transparentcolor', bg_color)
        top.config(bg=bg_color)
        
        result = {'confirm': False}
        
        panel = RoundedPanel(top, fill='#FFFFFF', radius=18, bg=bg_color, border=self.colors.get('line', '#E2EAF5'))
        panel.pack(fill='both', expand=True, padx=4, pady=4)
        
        title_lbl = 'Excluir Item' if len(rows) == 1 else 'Exclusão em Lote'
        tk.Label(panel, text=title_lbl, bg='#FFFFFF', fg=self.colors.get('text', '#18223A'), font=('Segoe UI', 14, 'bold')).pack(pady=(20, 8))
        
        desc = tk.Frame(panel, bg='#FFFFFF')
        desc.pack(fill='both', expand=True, padx=24)
        
        if len(rows) == 1:
            r = rows[0]
            if unlinked:
                tk.Label(desc, text=f"Tem certeza que deseja excluir permanentemente o item:\n\n{r['name']}?", bg='#FFFFFF', fg=self.colors.get('text', '#18223A'), font=('Segoe UI', 11)).pack(pady=20)
                btn_txt, btn_color, btn_hover, btn_fg = 'Excluir Permanentemente', '#C53030', '#9B2C2C', '#FFFFFF'
            else:
                if r['active'] == 1:
                    tk.Label(desc, text=f"O item '{r['name']}' possui vínculos em receitas ou produtos e NÃO pode ser excluído permanentemente para não corromper o histórico.", bg='#FFFFFF', fg=self.colors.get('text', '#18223A'), font=('Segoe UI', 10), wraplength=480).pack(pady=(10,5))
                    tk.Label(desc, text="Deseja INATIVAR este item?\nEle não aparecerá mais nas listas, mas será preservado.", bg='#FFFFFF', fg='#9B2C2C', font=('Segoe UI', 10, 'bold')).pack(pady=(5,10))
                    btn_txt, btn_color, btn_hover, btn_fg = 'Inativar / Ocultar', '#DD6B20', '#C05621', '#FFFFFF'
                else:
                    tk.Label(desc, text=f"O item '{r['name']}' já está inativo, mas ainda possui vínculos com receitas/produtos.", bg='#FFFFFF', fg=self.colors.get('text', '#18223A'), font=('Segoe UI', 10), wraplength=480).pack(pady=(10,5))
                    tk.Label(desc, text="Deseja OCULTÁ-LO definitivamente do sistema?\nEle aparecerá com um alerta ⚠️ nas receitas até ser substituído.", bg='#FFFFFF', fg='#9B2C2C', font=('Segoe UI', 10, 'bold')).pack(pady=(5,10))
                    btn_txt, btn_color, btn_hover, btn_fg = 'Ocultar Definitivamente', '#DD6B20', '#C05621', '#FFFFFF'
        else:
            tk.Label(desc, text=f"Você selecionou {len(rows)} itens.", bg='#FFFFFF', fg=self.colors.get('text', '#18223A'), font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 10))
            if linked:
                l_frame = tk.Frame(desc, bg='#FFFaf0', bd=1, relief='solid', highlightthickness=0)
                l_frame.pack(fill='x', pady=4)
                tk.Label(l_frame, text=f"⚠️ {len(linked)} itens possuem vínculos e serão apenas INATIVADOS:", bg='#FFFaf0', fg='#C05621', font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=8, pady=4)
            if unlinked:
                u_frame = tk.Frame(desc, bg='#FFF5F5', bd=1, relief='solid', highlightthickness=0)
                u_frame.pack(fill='x', pady=4)
                tk.Label(u_frame, text=f"🔴 {len(unlinked)} itens livres serão EXCLUÍDOS permanentemente:", bg='#FFF5F5', fg='#C53030', font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=8, pady=4)
            
            btn_txt = 'Executar Operação Mista' if (linked and unlinked) else ('Inativar Itens' if linked else 'Excluir Itens')
            btn_color, btn_hover, btn_fg = ('#C53030', '#9B2C2C', '#FFFFFF') if unlinked else ('#DD6B20', '#C05621', '#FFFFFF')
            
        def do_confirm():
            result['confirm'] = True
            top.destroy()
            
        act_frame = tk.Frame(panel, bg='#FFFFFF')
        act_frame.pack(fill='x', padx=32, pady=(16, 24))
        RoundedActionButton(act_frame, 'Cancelar', top.destroy, width=120, height=40, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557').pack(side='left')
        RoundedActionButton(act_frame, btn_txt, do_confirm, width=280, height=40, fill=btn_color, hover=btn_hover, fg=btn_fg).pack(side='right')
        
        top.grab_set()
        self.wait_window(top)
        
        if not result['confirm']:
            return
            
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
                if r['active'] == 1:
                    c.execute(f'UPDATE {table} SET active=0, updated_at=? WHERE id=?', (now_iso(), r['id']))
                else:
                    c.execute(f'UPDATE {table} SET archived=1, updated_at=? WHERE id=?', (now_iso(), r['id']))
                    
        self.refresh_all()
        if len(rows) == 1:
            self.notify(f"Item '{rows[0]['name']}' alterado com sucesso.")
        else:
            self.notify(f'{len(unlinked)} excluídos, {len(linked)} inativados/ocultados.')

    def edit_selected_material(self):
        s = self.mat_tree.selection()
        if not s:
            messagebox.showwarning('Cadastro','Selecione um item para editar.', parent=self); return
        code = self.mat_tree.item(s[0])['values'][0]
        with db() as c: r = c.execute('SELECT id FROM materials WHERE code=?',(code,)).fetchone()
        if r: self.material_form(r['id'])

    def ask_edit_reason(self, entity_type, entity_id, before, after):
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        top.geometry(f"520x340+{self.winfo_screenwidth()//2 - 260}+{self.winfo_screenheight()//2 - 170}")
        bg_color = '#000001'
        top.attributes('-transparentcolor', bg_color)
        top.config(bg=bg_color)
        
        result = {'value': None}
        
        panel = RoundedPanel(top, fill='#FFFFFF', radius=18, bg=bg_color, border=self.colors.get('line', '#E2EAF5'))
        panel.pack(fill='both', expand=True, padx=4, pady=4)
        
        tk.Label(panel, text='Motivo da Edição', bg='#FFFFFF', fg=self.colors.get('text', '#18223A'), font=('Segoe UI', 14, 'bold')).pack(pady=(24, 8))
        tk.Label(panel, text='Escolha como registrar esta alteração no sistema:', bg='#FFFFFF', fg=self.colors.get('muted', '#687796'), font=('Segoe UI', 10)).pack(pady=(0, 20))
        
        btn_frame = tk.Frame(panel, bg='#FFFFFF')
        btn_frame.pack(fill='x', padx=32)
        
        def do_correction():
            result['value'] = 'correction'
            top.destroy()
            
        def do_update():
            for w in btn_frame.winfo_children(): w.destroy()
            tk.Label(btn_frame, text='Justificativa da atualização:', bg='#FFFFFF', fg=self.colors.get('text', '#18223A'), font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0,8))
            txt = tk.Text(btn_frame, height=4, font=('Segoe UI', 10), bg='#F9FBFC', bd=1, relief='solid', highlightthickness=0)
            txt.pack(fill='x', expand=True)
            
            diffs = []
            key_names = {
                'name': 'Nome', 'purchase_qty': 'Quantidade de Compra', 'purchase_unit': 'Unidade de Compra',
                'purchase_value': 'Valor de Compra', 'brand': 'Marca', 'category': 'Categoria', 'barcode': 'Cód. Barras',
                'yield_qty': 'Rendimento', 'yield_unit': 'Unid. Rendimento', 'sale_price': 'Preço de Venda',
                'weight_qty': 'Peso', 'weight_unit': 'Unid. Peso', 'notes': 'Observações'
            }
            for k, va in after.items():
                if k == 'items': continue
                vb = before.get(k) if isinstance(before, dict) else None
                str_va = str(float(va)) if isinstance(va, (int, float)) and not isinstance(va, bool) else str(va).strip() if va is not None else ""
                str_vb = str(float(vb)) if isinstance(vb, (int, float)) and not isinstance(vb, bool) else str(vb).strip() if vb is not None else ""
                if str_va != str_vb:
                    friendly_k = key_names.get(k, k)
                    diffs.append(f"{friendly_k} (de '{str_vb}' para '{str_va}')")
                    
            if not diffs:
                if 'items' in after:
                    diffs.append("Alterou a Composição")
                else:
                    diffs.append("Nenhuma alteração detectada")
            
            txt.insert('1.0', ", ".join(diffs))
            
            def save_reason():
                r = txt.get('1.0', 'end').strip()
                if not r:
                    messagebox.showwarning("Atenção", "A justificativa não pode ficar vazia.", parent=top)
                    return
                result['value'] = r
                top.destroy()
                
            act_frame = tk.Frame(btn_frame, bg='#FFFFFF')
            act_frame.pack(fill='x', pady=(16,0))
            RoundedActionButton(act_frame, 'Cancelar', top.destroy, width=100, height=36, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557').pack(side='left')
            RoundedActionButton(act_frame, 'Salvar Atualização', save_reason, width=160, height=36, fill='#F28C28', hover='#693A16', fg='#FFFFFF').pack(side='right')
            txt.focus_set()

        RoundedActionButton(btn_frame, 'Correção de Erro (Não gera histórico)', do_correction, width=450, height=42, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557').pack(pady=(0, 12))
        RoundedActionButton(btn_frame, 'Atualização de Valores (Gravar no histórico)', do_update, width=450, height=42, fill='#F28C28', hover='#693A16', fg='#FFFFFF').pack(pady=(0, 12))
        RoundedActionButton(btn_frame, 'Cancelar', top.destroy, width=450, height=42, fill='#FFFFFF', hover='#F3F6FA', fg='#687796').pack()
        
        top.grab_set()
        self.wait_window(top)
        
        if result['value'] is None:
            raise ValueError('A edição foi cancelada pelo usuário.')
        if result['value'] != 'correction':
            record_edit(entity_type, entity_id, result['value'], {'antes': before, 'depois': after})


    def _show_generic_col_menu(self, e, popup_attr, tree, header_specs, hidden_cols, setting_key, redraw_callback):
        if hasattr(self, popup_attr) and getattr(self, popup_attr).winfo_exists():
            getattr(self, popup_attr).destroy()
            
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        bg_color = '#000001'
        top.attributes('-transparentcolor', bg_color)
        top.config(bg=bg_color)
        setattr(self, popup_attr, top)
        
        panel = RoundedPanel(top, fill='#FFFFFF', radius=12, bg=bg_color)
        panel.pack(fill='both', expand=True, padx=4, pady=4)
        
        lbl_title = tk.Label(panel, text='EXIBIR COLUNAS', bg='#FFFFFF', fg='#A0ABB9', font=('Segoe UI', 8, 'bold'))
        lbl_title.pack(anchor='w', padx=12, pady=(12, 4))
        
        for idx, (key, txt, default_w) in enumerate(header_specs, 1):
            if key in ('dummy', 'edit', 'delete', 'options', 'barcode'): continue
            
            row = tk.Frame(panel, bg='#FFFFFF', cursor='hand2')
            row.pack(fill='x', pady=1)
            
            is_vis = key not in hidden_cols
            chk_char = '\u2611' if is_vis else '\u2610'
            chk_color = '#F28C28' if is_vis else '#C0C9D8'
            
            lbl_chk = tk.Label(row, text=chk_char, fg=chk_color, bg='#FFFFFF', font=('Segoe UI', 13), cursor='hand2')
            lbl_chk.pack(side='left', padx=(12, 6), pady=2)
            
            lbl_txt = tk.Label(row, text=txt, fg='#18223A' if is_vis else '#687796', bg='#FFFFFF', font=('Segoe UI', 9), cursor='hand2')
            lbl_txt.pack(side='left', padx=(0, 16), pady=2)
            
            def on_enter(ev, r=row, lc=lbl_chk, lt=lbl_txt):
                r.config(bg='#EEF4FB')
                lc.config(bg='#EEF4FB')
                lt.config(bg='#EEF4FB', fg='#18223A')
                
            def on_leave(ev, r=row, lc=lbl_chk, lt=lbl_txt, k=key):
                r.config(bg='#FFFFFF')
                lc.config(bg='#FFFFFF')
                is_vis_now = k not in hidden_cols
                lt.config(bg='#FFFFFF', fg='#18223A' if is_vis_now else '#687796')
                
            for w in (row, lbl_chk, lbl_txt):
                w.bind('<Enter>', on_enter)
                w.bind('<Leave>', on_leave)
                
            def toggle(ev, k=key, lc=lbl_chk, lt=lbl_txt):
                if k in hidden_cols:
                    hidden_cols.remove(k)
                    lc.config(text='\u2611', fg='#F28C28')
                    lt.config(fg='#18223A')
                else:
                    hidden_cols.append(k)
                    lc.config(text='\u2610', fg='#C0C9D8')
                    lt.config(fg='#687796')
                    
                set_setting(setting_key, hidden_cols)
                
                valid_keys = [spec[0] for spec in header_specs]
                disp = [c for c in valid_keys if c not in hidden_cols]
                tree['displaycolumns'] = disp
                if hasattr(self, redraw_callback):
                    self.after_idle(getattr(self, redraw_callback))
                    
            for w in (row, lbl_chk, lbl_txt):
                w.bind('<Button-1>', toggle)
                
        panel.update_idletasks()
        req_width = max(panel.winfo_reqwidth(), 160)
        req_height = panel.winfo_reqheight() + 12
        
        # force minimum width layout
        panel.config(width=req_width)
        
        x = e.x_root - req_width + 15
        y = e.y_root + 15
        top.geometry(f'{req_width}x{req_height}+{x}+{y}')
        top.bind('<FocusOut>', lambda ev: top.destroy())
        top.focus_set()

    def _show_mat_col_menu(self, e):
        self._show_generic_col_menu(e, '_mat_col_popup', self.mat_tree, self._mat_header_specs, self._mat_hidden_cols, 'mat_hidden_cols', '_redraw_mat_header')

    def _sort_mat_col(self, key):
        if getattr(self, '_mat_order_by', 'name') == key:
            self._mat_order_dir = 'DESC' if getattr(self, '_mat_order_dir', 'ASC') == 'ASC' else 'ASC'
        else:
            self._mat_order_by = key
            self._mat_order_dir = 'ASC'
        self.refresh_materials()
        self.after_idle(self._redraw_mat_header)

    def refresh_materials(self):
        if not hasattr(self,'mat_tree'): return
        for x in self.mat_tree.get_children(): self.mat_tree.delete(x)
        query = '%'+self.mat_search.get().strip()+'%' if hasattr(self,'mat_search') else '%'
        status_filter = self.mat_status.get() if hasattr(self, 'mat_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        
        ob = getattr(self, '_mat_order_by', 'name')
        od = getattr(self, '_mat_order_dir', 'ASC')
        valid_cols = {'code':'code', 'name':'name', 'brand':'brand', 'qty':'purchase_qty', 'value':'purchase_value', 'category':'category', 'date':'created_at'}
        sql_order = valid_cols.get(ob, 'name')
        
        with db() as c:
            rows = c.execute(f'''SELECT code,COALESCE(barcode,''),name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,
                                       substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10), COALESCE(active,1), id
                                FROM materials WHERE {status_cond} AND (name LIKE ? OR COALESCE(brand,'') LIKE ? OR code LIKE ?) 
                                ORDER BY {sql_order} COLLATE NOCASE {od}''', (query,query,query)).fetchall()
        for r in rows:
            r_list = list(r)
            val = r_list[6]
            val_str = f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            r_list[6] = val_str
            is_active = r_list.pop(10)
            mat_id = r_list.pop(10)
            status_str = 'Ativo' if is_active else 'Inativo'
            self.mat_tree.insert('', 'end', iid=str(mat_id), text='', image=self._img_chk_off, values=tuple(r_list)+(status_str, '','',''), tags=() if is_active else ('inactive',))
        self._reset_checked(self.mat_tree)
        if hasattr(self, 'mat_icon_ov'): self.mat_icon_ov._redraw()
        if hasattr(self,'mat_empty_overlay'):
            if rows:
                self.mat_empty_overlay.place_forget()
            else:
                self.mat_empty_overlay.place(x=0,y=43,relwidth=1,relheight=1,height=-43)

    def material_history_dialog(self):
        s=self.mat_tree.selection()
        if not s: return
        code=self.mat_tree.item(s[0])['values'][0]
        with db() as c:
            mid=c.execute('SELECT id FROM materials WHERE code=?',(code,)).fetchone()['id']
            rows=c.execute('SELECT purchase_date,qty,unit,value,COALESCE(brand,\'\') FROM purchases WHERE material_id=? ORDER BY id DESC',(mid,)).fetchall()
        v = self.mat_tree.item(s[0])['values']
        curr_row = (v[4], v[5], v[6], v[3]) if len(v) > 6 else ('-', '-', '-', '-')
        CustomHistoryModal(self, f"Histórico: {v[2]}", (('data', 'Data/Hora', 165), ('qtd', 'Qtd.', 90), ('un', 'Un.', 65), ('valor', 'Custo', 100), ('marca', 'Marca', 140)), rows, current_row_data=curr_row)

    def material_conversion_dialog(self):
        d = Modal(self, 'Conversões de Insumos', '600x520')
        
        # Subtitle
        tk.Label(d, text='Selecione o insumo para configurar suas unidades (Ex: xícara, colher).', 
                 bg=self.colors.get('bg', '#F4F7FC'), fg=self.colors.get('muted', '#60769D')).pack(anchor='w', padx=24, pady=(24, 12))
        
        # Insumo Combobox Area
        sel_frame = tk.Frame(d, bg=self.colors.get('bg', '#F4F7FC'))
        sel_frame.pack(fill='x', padx=24, pady=(0, 16))
        
        tk.Label(sel_frame, text='Insumo: ', bg=self.colors.get('bg', '#F4F7FC'), fg=self.colors.get('text', '#18223A'), font=('Segoe UI', 9, 'bold')).pack(side='left')
        mat_var = tk.StringVar()
        mat_cb = RoundedDropdown(sel_frame, mat_var, [], width=480, height=36, align='left')
        mat_cb.pack(side='left', padx=12)
        
        mats = []
        with db() as c:
            for r in c.execute('SELECT id, code, name FROM materials ORDER BY name').fetchall():
                mats.append(f"{r['id']} - {r['name']} ({r['code']})")
        mat_cb._opts = mats; mat_cb.after_idle(mat_cb._redraw)

        # Form Area
        form = tk.Frame(d, bg=self.colors.get('bg', '#F4F7FC'))
        form.pack(fill='x', padx=24)
        
        name = tk.StringVar(); base = tk.StringVar(value='g'); factor = tk.StringVar()
        
        lbl_cfg = tk.Label(form, text='Unidade configurável *', bg=self.colors.get('bg', '#F4F7FC'), fg=self.colors.get('text', '#18223A'))
        lbl_cfg.grid(row=0, column=0, padx=(0, 12), sticky='w', pady=(0, 4))
        RoundedEntry(form, name, width=200, height=36, placeholder='Ex: Xícara', icon=False).grid(row=1, column=0, padx=(0, 12))
        
        lbl_int = tk.Label(form, text='Un. Interna *', bg=self.colors.get('bg', '#F4F7FC'), fg=self.colors.get('text', '#18223A'))
        lbl_int.grid(row=0, column=1, padx=(0, 12), sticky='w', pady=(0, 4))
        RoundedDropdown(form, base, ('mg','g','kg','ml','l','un'), width=90, height=36).grid(row=1, column=1, padx=(0, 12))
        
        lbl_eq = tk.Label(form, text='Equivale a *', bg=self.colors.get('bg', '#F4F7FC'), fg=self.colors.get('text', '#18223A'))
        lbl_eq.grid(row=0, column=2, padx=(0, 12), sticky='w', pady=(0, 4))
        RoundedEntry(form, factor, width=120, height=36, placeholder='Ex: 200', icon=False).grid(row=1, column=2, padx=(0, 12))
        
        def refresh(*_):
            for x in tree.get_children(): tree.delete(x)
            if not mat_var.get(): return
            mid = int(mat_var.get().split(' - ')[0])
            for r in custom_units_for_material(mid):
                tree.insert('','end',values=(r['name'],r['base_unit'],r['factor_to_base']))
                
        mat_var.trace_add('write', lambda *_: refresh())
        
        def add():
            try:
                if not mat_var.get(): raise ValueError('Selecione um insumo primeiro.')
                mid = int(mat_var.get().split(' - ')[0])
                n=name.get().strip(); b=base.get().strip(); f=to_float(factor.get(),'Quantidade')
                if not n: raise ValueError('O nome da unidade configurável é obrigatório.')
                if not b: raise ValueError('A unidade interna é obrigatória.')
                if f<=0: raise ValueError('A quantidade deve ser maior que zero.')
                with db() as c:
                    exist = c.execute('SELECT id FROM custom_units WHERE material_id=? AND name=?', (mid, n)).fetchone()
                    if exist:
                        c.execute('UPDATE custom_units SET base_unit=?, factor_to_base=? WHERE id=?', (b, f, exist['id']))
                    else:
                        c.execute('INSERT INTO custom_units(material_id,name,base_unit,factor_to_base) VALUES(?,?,?,?)',(mid,n,b,f))
                name.set('');factor.set('');refresh()
                self.notify('Conversão salva com sucesso!')
            except Exception as e:
                safe_error(d,'Não foi possível salvar a conversão',e)
                
        RoundedActionButton(form, 'Salvar', add, width=100, height=36, fill='#F28C28', hover='#F6A45A', fg='#FFFFFF').grid(row=1, column=3, sticky='s', pady=0)
        
        # Table Area
        table_frame = tk.Frame(d, bg=self.colors.get('bg', '#F4F7FC'))
        table_frame.pack(fill='both', expand=True, padx=24, pady=(24, 24))
        
        header_canvas = tk.Canvas(table_frame, height=36, bg=self.colors.get('bg', '#F4F7FC'), highlightthickness=0)
        header_canvas.pack(side='top', fill='x')
        
        tree_container = tk.Frame(table_frame, bg=self.colors.get('bg', '#F4F7FC'))
        tree_container.pack(side='top', fill='both', expand=True)
        
        tree = ttk.Treeview(tree_container, columns=('name','base','factor'), show='tree')
        tree.column('#0', width=0, stretch=False)
        tree.pack(side='left', fill='both', expand=True)
        
        vsb = VerticalPillScrollbar(tree_container, tree)
        
        columns = [('name', 'Unidade Configurável', 240), ('base', 'Un. Interna', 140), ('factor', 'Equivale a', 160)]
        for k, t, w in columns:
            tree.column(k, width=w, anchor='center')
            
        def draw_header(e=None):
            c = header_canvas
            c.delete('all')
            w = max(c.winfo_width(), 2)
            h = max(c.winfo_height(), 2)
            r = min(h/2, 18)
            fill = '#EEF4FB'
            
            c.create_rectangle(r, 0, w-r, h, fill=fill, outline='')
            c.create_rectangle(0, r, w, h-r, fill=fill, outline='')
            c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=fill, outline=fill)
            c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=fill, outline=fill)
            c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=fill, outline=fill)
            c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=fill, outline=fill)
            
            try: x_offset = float(tree.xview()[0]) * sum(int(tree.column(col[0], 'width')) for col in columns)
            except Exception: x_offset = 0
            
            x0 = -x_offset
            for idx, (key, txt, width) in enumerate(columns):
                try: cw = int(tree.column(key, 'width'))
                except Exception: cw = width
                
                align = 'w' if key == 'name' else 'center'
                anchor_x = x0 + 12 if align == 'w' else x0 + cw/2
                
                c.create_text(anchor_x, h/2, text=txt, fill='#60769D', font=('Segoe UI', 9, 'bold'), anchor=align)
                if idx < len(columns) - 1:
                    c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                x0 += cw
                
        header_canvas.bind('<Configure>', draw_header)
        tree.bind('<Configure>', lambda e: tree.after_idle(draw_header))
        d.after_idle(draw_header)

    # ---------- Receitas ----------
