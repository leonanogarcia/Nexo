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

class ProductsPageMixin:
    def products_page(self,f):
        _, bar=self._build_page_toolbar(f)
        
        prod_add=RoundedActionButton(bar, '+ Novo Produto', lambda: self._run_normal_action(self.prod_tree, self.new_product), width=135, height=42, fill='#F28C28', hover='#BA5200')
        prod_add.pack(side='left')
        
        self.prod_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self.delete_selected_products(), width=95, height=40, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030')
        
        prod_history=RoundedActionButton(bar, '<clock> Histórico', lambda: self._run_normal_action(self.prod_tree, self.product_history_dialog), width=120, height=42, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        prod_history.pack(side='left', padx=(8, 0))

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
        
        self.prod_tree=ttk.Treeview(table_host,columns=('code','name','weight','cost','price','margin','date','mod_date','status','dummy','edit','delete','options'),show='tree')
        self.prod_tree.tag_configure('inactive', foreground='#9AA9BF')
        self.prod_tree.column('#0',width=60,minwidth=60,stretch=False)
        
        for k,w in [('code',100),('name',380),('weight',120),('cost',110),('price',110),('margin',90),('date',130),('mod_date',130),('status',80),('edit',30),('delete',30),('options',30)]:
            self.prod_tree.column(k,width=w,minwidth=w,anchor='center' if k in ('weight','cost','price','margin','date','mod_date','status') else 'w',stretch=False)
        self.prod_tree.column('dummy', width=0, minwidth=0, stretch=True)
        
        self.prod_hsb = PillScrollbar(table_host, self.prod_tree)
        original_scroll_prod = self.prod_hsb._on_scroll
        def hsb_scroll_prod(first, last):
            original_scroll_prod(first, last)
            self.after_idle(self._redraw_prod_header) if hasattr(self, '_redraw_prod_header') else None
        self.prod_tree.configure(xscrollcommand=hsb_scroll_prod)
        self.prod_tree.pack(fill='both',expand=True)
        
        self._prod_header_specs=[('code','Código',100),('name','Produto',380),('weight','Peso/Rendimento',120),('cost','Custo total',110),('price','Preço',110),('margin','Margem',90),('date','Data de criação',130),('mod_date','Última modificação',130),('status','Status',80),('dummy','',0),('edit','',30),('delete','',30),('options','',30)]
        self._prod_header_imgs={}
        
        valid_keys = [spec[0] for spec in self._prod_header_specs]
        disp = [c for c in valid_keys if c not in self._prod_hidden_cols]
        self.prod_tree['displaycolumns'] = disp
        
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
                total_w = sum(int(self.prod_tree.column(col, 'width')) for col in ['#0'] + list(self.prod_tree['displaycolumns']))
                x_offset = float(self.prod_tree.xview()[0]) * total_w
            except Exception: x_offset = 0
            x0 = -x_offset
            
            disp = self.prod_tree['displaycolumns']
            if disp == ('#all',): disp = self.prod_tree['columns']
            spec_dict = {key: txt for key, txt, _ in self._prod_header_specs}
            
            cols = [('#0', '', 'dummy')]
            for i, col_id in enumerate(disp, 1):
                cols.append((f'#{i}', spec_dict.get(col_id, ''), col_id))
                
            for idx,(col,txt,key) in enumerate(cols):
                try: cw=int(self.prod_tree.column(col,'width'))
                except Exception: cw=0
                if col == '#0': cw = 60
                if key in ('dummy', 'edit', 'delete'):
                    x0+=cw; continue
                align = 'w' if key in ('code', 'name') else 'center'
                anchor_x = x0+12 if align == 'w' else x0+cw/2
                
                arrow_txt = ''
                if getattr(self, '_prod_order_by', 'name') == key:
                    arrow_txt = ' ↑' if getattr(self, '_prod_order_dir', 'ASC') == 'ASC' else ' ↓'
                full_txt = txt + arrow_txt if align == 'w' else arrow_txt + txt
                
                tag = f'hdr_{key}'
                tid = c.create_text(anchor_x,h/2,text=full_txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor=align, tags=(tag,))
                c.create_rectangle(x0, 0, x0+cw, h, fill='', outline='', tags=(tag,))
                c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                
                c.tag_bind(tag, '<Enter>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#BA5200'))
                c.tag_bind(tag, '<Leave>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#60769D'))
                c.tag_bind(tag, '<Button-1>', lambda e, k=key: self._sort_prod_col(k))
                
                x0+=cw
            cw0 = 60
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
                c.create_image(cw0/2, h/2, image=self._img_chk_on if is_all_checked else self._img_chk_off, anchor='center', tags=('header_chk',))
                c.create_rectangle(0, 0, cw0-2, h, fill='', outline='', tags=('header_chk',))
                c.tag_bind('header_chk', '<Button-1>', lambda e: self._toggle_all_checkboxes(self.prod_tree))
            
            # RIGHT side cover
            start_x = w - 90
            c.create_rectangle(start_x, 0, w-r, h, fill=fill, outline='')
            c.create_rectangle(start_x, r, w, h-r, fill=fill, outline='')
            c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=fill, outline=fill)
            c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=fill, outline=fill)
            c.create_line(start_x, 6, start_x, h-6, fill=self.colors.get('line', '#E5ECF5'))
            if hasattr(self, '_img_gear'):
                c.create_image(w - 20, h/2, image=self._img_gear, anchor='center', tags=('gear_icon',))
                c.tag_bind('gear_icon', '<Enter>', lambda e: c.config(cursor='hand2'))
                c.tag_bind('gear_icon', '<Leave>', lambda e: c.config(cursor='arrow'))
                c.tag_bind('gear_icon', '<Button-1>', lambda e: self._show_generic_col_menu(e, '_prod_col_popup', self.prod_tree, self._prod_header_specs, self._prod_hidden_cols, 'prod_hidden_cols', '_redraw_prod_header'))
        
        self._redraw_prod_header=redraw_prod_header
        self.prod_header.bind('<Configure>', redraw_prod_header)
        self.prod_tree.bind('<Configure>', lambda e: self.prod_tree.after_idle(redraw_prod_header))
        self.after_idle(redraw_prod_header)
        
        self._setup_canvas_header_drag(self.prod_header, self.prod_tree, ['edit','delete'], redraw_prod_header, 'prod')

        self.prod_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.prod_tree,'product'))
        self.prod_tree.bind('<Double-1>',lambda e: (self.edit_selected_product(), 'break')[1])
        
        self.prod_icon_ov=self._attach_row_icon_overlay(self.prod_tree, table_host, 7, 8, self.edit_selected_product, self.delete_selected_product)
        try:
            from PIL import Image, ImageTk
            img_path = UI_ASSETS / 'empty_state_reference_exact.png'
            self._prod_empty_img = ImageTk.PhotoImage(Image.open(img_path))
            
            self.prod_empty_overlay = tk.Frame(table_host, bg=self.colors['field'])
            inner = tk.Frame(self.prod_empty_overlay, bg=self.colors['field'])
            inner.place(relx=0.5, rely=0.5, anchor='center')
            
            l_img = tk.Label(inner, image=self._prod_empty_img, bg=self.colors['field'])
            l_img.pack(pady=(0, 10))
            
            l_title = tk.Label(inner, text='Nenhum produto cadastrado.', bg=self.colors['field'], fg='#687796', font=('Segoe UI', 11, 'bold'))
            l_title.pack(pady=(0, 4))
            
            l_sub = tk.Label(inner, text='Clique em + Novo Produto para adicionar o primeiro produto.', bg=self.colors['field'], fg='#8A99B5', font=('Segoe UI', 9))
            l_sub.pack()
        except Exception:
            self.prod_empty_overlay = tk.Label(table_host, text='Nenhum produto cadastrado.\nClique em + Novo Produto para adicionar o primeiro produto.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))
        self._action_buttons[self.prod_tree]={'normal':[prod_add,prod_history],'bulk':[self.prod_bulk_delete_btn]}
        self._update_action_states()

    def product_form(self, edit_id=None):
        is_edit=edit_id is not None
        with db() as c:
            existing=c.execute('SELECT * FROM products WHERE id=?',(edit_id,)).fetchone() if is_edit else None
            current=c.execute('SELECT * FROM product_items WHERE product_id=?',(edit_id,)).fetchall() if is_edit else []
        d=Modal(self,'Editar Produto' if is_edit else 'Novo Produto','1000x580')
        name=tk.StringVar(value=existing['name'] if existing else '')
        weight=tk.StringVar(value=fmt_num(existing['weight_qty']) if existing and existing['weight_qty'] is not None else '')
        weight_unit=tk.StringVar(value=existing['weight_unit'] if existing and existing['weight_unit'] else 'g')
        price=tk.StringVar(value=fmt(existing['sale_price']) if existing and existing['sale_price'] is not None else '')
        notes=tk.StringVar(value=existing['notes'] or '' if existing else '')
        
        try: text_col = self.colors.get('text', '#18223A')
        except: text_col = '#18223A'
        
        def make_field(parent, label, var, w_chars, w_pixels=None, is_dropdown=False, opts=None, bg=None, is_num=False, is_money=False):
            bg = bg or parent.cget('bg')
            wrap = tk.Frame(parent, bg=bg)
            tk.Label(wrap, text=label, bg=bg, fg=text_col, font=('Segoe UI', 9)).pack(anchor='w', padx=4, pady=(1,0))
            if is_dropdown:
                wd = RoundedDropdown(wrap, var, opts or [], width=w_pixels or 140, align='left')
            elif is_money:
                wd = masked_money_entry(wrap, var, width=w_chars)
            elif is_num:
                wd = numeric_entry(wrap, var, width=w_chars)
            else:
                wd, _ = rounded_entry(wrap, var, width=w_chars)
            wd.pack(fill='x', expand=True, padx=4, pady=(0,8))
            return wrap, wd

        top = tk.Frame(d, bg=d.cget('bg'), padx=24, pady=16); top.pack(fill='x')
        make_field(top, 'Nome *', name, 30)[0].pack(side='left', fill='x', expand=True)
        make_field(top, 'Peso/Rend.', weight, 12, is_num=True)[0].pack(side='left')
        make_field(top, 'Unidade', weight_unit, 10, is_dropdown=True, opts=UNITS)[0].pack(side='left')
        make_field(top, 'Preço Venda', price, 16, is_money=True)[0].pack(side='left')
        make_field(top, 'Observações', notes, 24)[0].pack(side='left', fill='x', expand=True)
        
        box_outer = tk.Frame(d, bg=d.cget('bg'), padx=16, pady=4); box_outer.pack(fill='both', expand=True)
        tk.Label(box_outer, text='Composição por unidade vendida', bg=d.cget('bg'), fg=self.colors.get('text', '#18223A'), font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 4))
        
        box_top = RoundedPanel(box_outer, fill='#FFFFFF', radius=12, bg=d.cget('bg'))
        box_top.pack(fill='x', pady=(0, 8))
        
        typ=tk.StringVar(value='INSUMO');ref=tk.StringVar();qty=tk.StringVar();unit=tk.StringVar(value='g');items=[]
        
        _, typ_wd = make_field(box_top, 'Origem', typ, 16, w_pixels=140, is_dropdown=True, opts=('INSUMO','RECEITA','PRODUTO'), bg='#FFFFFF')
        typ_wd.master.pack(side='left', pady=4, padx=(4,0))
        _, cb = make_field(box_top, 'Item', ref, 40, w_pixels=320, is_dropdown=True, bg='#FFFFFF')
        cb.master.pack(side='left', fill='x', expand=True, pady=4)
        make_field(box_top, 'Quantidade', qty, 12, is_num=True, bg='#FFFFFF')[0].pack(side='left', pady=4)
        _, unit_cb = make_field(box_top, 'Unidade', unit, 10, w_pixels=100, is_dropdown=True, opts=UNITS, bg='#FFFFFF')
        unit_cb.master.pack(side='left', pady=4)
        
        for r in current:
            with db() as c:
                table={'MATERIAL':'materials','RECIPE_BASE':'base_recipes','PRODUCT':'products'}.get(r['item_type'])
                rr=c.execute(f'SELECT id,name FROM {table} WHERE id=?',(r['ref_id'],)).fetchone() if table else None
            if rr: items.append((r['item_type'],r['ref_id'],rr['name'],r['qty_per_unit'],r['unit']))
            
        _, table_host = self._build_page_table_panel(box_outer)
        
        header_canvas = tk.Canvas(table_host, bg=self.colors['panel'], bd=0, highlightthickness=0, height=36)
        header_canvas.pack(fill='x', padx=2, pady=(0,0))
        
        tree=ttk.Treeview(table_host, columns=('type','item','qty','unit','cost','dummy','edit','delete'), show='tree')
        tree.column('#0', width=60, minwidth=60, stretch=False)
        for k, w, a in [('type', 120, 'w'), ('item', 330, 'w'), ('qty', 90, 'center'), ('unit', 70, 'center'), ('cost', 100, 'center'), ('dummy', 0, 'w'), ('edit', 30, 'center'), ('delete', 30, 'center')]:
            tree.column(k, width=w, minwidth=w, anchor=a, stretch=(k=='dummy'))
        tree.pack(fill='both', expand=True)
        
        header_specs = [('type', 'Origem', 120), ('item', 'Componente', 330), ('qty', 'Qtd.', 90), ('unit', 'Un.', 70), ('cost', 'Custo', 100), ('dummy', '', 0), ('edit', '', 30), ('delete', '', 30)]
        
        def redraw_header(_event=None):
            c = header_canvas; c.delete('all')
            w = max(c.winfo_width(), 2); h = max(c.winfo_height(), 2)
            r = min(h/2, 18); fill = '#EEF4FB'
            c.create_rectangle(r, 0, w-r, h, fill=fill, outline=''); c.create_rectangle(0, r, w, h-r, fill=fill, outline='')
            c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=fill, outline=fill); c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=fill, outline=fill)
            c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=fill, outline=fill); c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=fill, outline=fill)
            x0 = 0
            for idx, (key, txt, cw) in enumerate(header_specs):
                if key == 'dummy': cw = int(tree.column('dummy', 'width'))
                if key in ('edit', 'delete'): x0 += cw; continue
                align = 'w' if key in ('type', 'item') else 'center'
                anchor_x = x0 + 12 if align == 'w' else x0 + cw/2
                if idx == 0: x0 += 60 
                
                arrow_txt = ''
                if sort_state['by'] == key:
                    arrow_txt = ' ↑' if sort_state['dir'] == 'ASC' else ' ↓'
                full_txt = txt + arrow_txt if align == 'w' else arrow_txt + txt
                
                tag = f'hdr_{key}'
                tid = c.create_text(anchor_x + (60 if idx==0 else 0), h/2, text=full_txt, fill='#60769D', font=('Segoe UI', 9, 'bold'), anchor=align, tags=(tag,))
                c.create_rectangle(x0 - (60 if idx==0 else 0), 0, x0+cw, h, fill='', outline='', tags=(tag,))
                if key in ('type', 'item', 'qty', 'cost'):
                    c.tag_bind(tag, '<Enter>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#BA5200'))
                    c.tag_bind(tag, '<Leave>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#60769D'))
                    c.tag_bind(tag, '<Button-1>', lambda e, k=key: sort_items(k))
                    
                x0 += cw
            all_checked = len(self._checked_rows.get(str(tree), set())) == len(tree.get_children()) and tree.get_children()
            c.create_image(30, h/2, image=self._img_chk_on if all_checked else self._img_chk_off, anchor='center', tags=('master_chk',))
            c.tag_bind('master_chk', '<Button-1>', lambda e: toggle_master_chk())
            c.tag_bind('master_chk', '<Enter>', lambda e: c.config(cursor='hand2'))
            c.tag_bind('master_chk', '<Leave>', lambda e: c.config(cursor='arrow'))
            
        def toggle_master_chk():
            cset = self._checked_rows.get(str(tree), set())
            children = tree.get_children()
            if len(cset) == len(children) and children: cset.clear()
            else: cset.update(children)
            self._checked_rows[str(tree)] = cset
            redraw_header(); _redraw_overlay()
            
        header_canvas.bind('<Configure>', redraw_header)
        
        ov = tk.Canvas(table_host, bd=0, highlightthickness=0, cursor='arrow', bg=self.colors['field'])
        ov.place(relx=1.0, x=0, y=36, width=60, relheight=1.0, height=-36, anchor='ne')
        ov._icon_refs = []
        ov_left = tk.Canvas(table_host, bd=0, highlightthickness=0, cursor='arrow', bg=self.colors['field'])
        ov_left.place(relx=0, x=0, y=36, width=60, relheight=1.0, height=-36, anchor='nw')
        
        def _redraw_overlay(*_):
            ov.delete('all'); ov_left.delete('all')
            ov._icon_refs.clear()
            img_e = self._make_row_icon('edit')
            img_d = self._make_row_icon('delete')
            if img_e: ov._icon_refs.append(img_e)
            if img_d: ov._icon_refs.append(img_d)
            ex, dx = 15, 45
            selected = set(tree.selection())
            for iid in tree.get_children():
                bb = tree.bbox(iid)
                if not bb: continue
                _, ry, _, rh = bb
                bg_color = self.colors['accent_soft'] if iid in selected else self.colors['field']
                
                ov_left.create_rectangle(0, ry, 60, ry + rh, fill=bg_color, outline='', tags=(f'c_{iid}',))
                is_checked = iid in self._checked_rows.get(str(tree), set())
                cy = ry + rh // 2
                ov_left.create_image(30, cy, image=self._img_chk_on if is_checked else self._img_chk_off, anchor='center', tags=(f'c_{iid}',))
                ov_left.tag_bind(f'c_{iid}', '<Button-1>', lambda ev, i=iid: (self._toggle_checkbox(tree, i), redraw_header(), _redraw_overlay()))
                ov_left.tag_bind(f'c_{iid}', '<Enter>', lambda ev, i=iid: ov_left.config(cursor='hand2'))
                ov_left.tag_bind(f'c_{iid}', '<Leave>', lambda ev, i=iid: ov_left.config(cursor='arrow'))
                
                ov.create_rectangle(0, ry, 60, ry + rh, fill=bg_color, outline='')
                if img_e:
                    ov.create_image(ex, cy, image=img_e, anchor='center', tags=(f'e_{iid}',))
                    ov.tag_bind(f'e_{iid}', '<Button-1>', lambda ev, i=iid: (tree.selection_set(i), edit_item()))
                    ov.tag_bind(f'e_{iid}', '<Enter>', lambda ev, i=iid: ov.config(cursor='hand2'))
                    ov.tag_bind(f'e_{iid}', '<Leave>', lambda ev, i=iid: ov.config(cursor='arrow'))
                if img_d:
                    ov.create_image(dx, cy, image=img_d, anchor='center', tags=(f'd_{iid}',))
                    ov.tag_bind(f'd_{iid}', '<Button-1>', lambda ev, i=iid: (tree.selection_set(i), delete_item()))
                    ov.tag_bind(f'd_{iid}', '<Enter>', lambda ev, i=iid: ov.config(cursor='hand2'))
                    ov.tag_bind(f'd_{iid}', '<Leave>', lambda ev, i=iid: ov.config(cursor='arrow'))

        tree.bind('<Configure>', lambda e: (redraw_header(), _redraw_overlay()), add='+')
        tree.bind('<<TreeviewSelect>>', _redraw_overlay, add='+')
        
        def load_ref(*_):
            if not typ.get(): return
            typemap={'INSUMO':'materials','RECEITA':'base_recipes','PRODUTO':'products'}
            table=typemap[typ.get()];vals=[]
            current_pid=edit_id
            for r in list_names(table):
                if table=='products' and current_pid and r['id']==current_pid:continue
                vals.append(f'{r["id"]} — {r["name"]}')
            cb._opts = vals; ref.set(''); unit_cb._opts = UNITS
            
        typ.trace_add('write',load_ref)
        
        sort_state = {'by': 'item', 'dir': 'ASC'}
        def sort_items(key):
            if sort_state['by'] == key: sort_state['dir'] = 'DESC' if sort_state['dir'] == 'ASC' else 'ASC'
            else: sort_state['by'] = key; sort_state['dir'] = 'ASC'
            refresh_items()
            
        def refresh_items():
            for x in tree.get_children():tree.delete(x)
            dec = []
            for i, it in enumerate(items):
                t,r,n,qv,uv=it
                try:cst=item_cost(t,r,qv,uv)
                except Exception:cst=0
                dec.append({'i': i, 't': t, 'n': n, 'q': qv, 'u': uv, 'cst': cst})
                
            k = sort_state['by']
            rev = (sort_state['dir'] == 'DESC')
            if k == 'type': dec.sort(key=lambda x: {'MATERIAL':'INSUMO','RECIPE_BASE':'RECEITA','PRODUCT':'PRODUTO'}.get(x['t'],x['t']).lower(), reverse=rev)
            elif k == 'item': dec.sort(key=lambda x: x['n'].lower(), reverse=rev)
            elif k == 'qty': dec.sort(key=lambda x: float(x['q']), reverse=rev)
            elif k == 'cost': dec.sort(key=lambda x: x['cst'] if isinstance(x['cst'], (int, float)) else 0, reverse=rev)
            
            for item in dec:
                cst = item['cst']
                t = item['t']
                tree.insert('','end',iid=str(item['i']),values=({'MATERIAL':'INSUMO','RECIPE_BASE':'RECEITA','PRODUCT':'PRODUTO'}.get(t,t),item['n'],item['q'],item['u'],fmt(cst)))
            redraw_header(); _redraw_overlay()
                
        def add():
            try:
                if '—' not in ref.get():raise ValueError('Selecione um componente relacionado ao Cadastro, Receita ou Produto.')
                qv=to_float(qty.get(),'Quantidade');uv=unit.get().strip();rid=int(ref.get().split(' — ')[0])
                if qv<=0:raise ValueError('A Quantidade deve ser maior que zero.')
                table={'INSUMO':'materials','RECEITA':'base_recipes','PRODUTO':'products'}[typ.get()]
                with db() as c:rr=c.execute(f'SELECT name FROM {table} WHERE id=?',(rid,)).fetchone()
                if not rr: raise ValueError('O componente selecionado não foi encontrado.')
                internal={'INSUMO':'MATERIAL','RECEITA':'RECIPE_BASE','PRODUTO':'PRODUCT'}[typ.get()]
                items.append((internal,rid,rr['name'],qv,uv));refresh_items();qty.set('')
            except Exception as e:safe_error(d,'Não foi possível adicionar o componente',e)
            
        RoundedActionButton(box_top, 'Adicionar', add, width=100, height=32, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557', bg='#FFFFFF').pack(side='left', padx=12, pady=(16,4))
        
        def edit_item():
            sel=tree.selection()
            if not sel:
                messagebox.showwarning('Produto','Selecione um componente para editar.',parent=d); return
            idx=int(sel[0]); t,r,n,qv,uv=items[idx]
            display={'MATERIAL':'INSUMO','RECIPE_BASE':'RECEITA','PRODUCT':'PRODUTO'}[t]
            typ.set(display); load_ref()
            ref.set(f'{r} — {n}'); qty.set(fmt_num(qv)); unit.set(uv)
            items.pop(idx); refresh_items()
            
        def delete_item():
            sel=tree.selection()
            if not sel:
                messagebox.showwarning('Produto','Selecione um componente para excluir.',parent=d); return
            items.pop(int(sel[0])); refresh_items()
            
        def bulk_delete_items():
            cset = self._checked_rows.get(str(tree), set())
            if not cset: return
            if not messagebox.askyesno('Produto', f'Excluir {len(cset)} itens marcados da composição?', parent=d): return
            indices = sorted([int(i) for i in cset], reverse=True)
            for idx in indices: items.pop(idx)
            cset.clear()
            refresh_items()
            
        tree.bind('<Double-1>',lambda e: edit_item())
        
        def save():
            try:
                n=name.get().strip()
                if not n:raise ValueError('O campo "Nome" é obrigatório.')
                w=optional_float(weight.get())
                if w is not None and w<=0:raise ValueError('O Peso/Rendimento deve ser maior que zero.')
                pv=money_to_float(price.get(),'Preço de venda') if price.get().strip() else None
                if pv is not None and pv<0:raise ValueError('O Preço de venda não pode ser negativo.')
                if not items:raise ValueError('Adicione pelo menos um componente ao Produto.')
                if is_edit:
                    with db() as c: before=dict(c.execute('SELECT * FROM products WHERE id=?',(edit_id,)).fetchone())
                    self.ask_edit_reason('PRODUTO',edit_id,before,{'name':n,'weight_qty':w,'weight_unit':weight_unit.get(),'sale_price':pv,'notes':notes.get().strip(),'items':[(i[0],i[1],i[3],i[4]) for i in items]})
                with db() as c:
                    if is_edit:
                        pid=edit_id
                        c.execute('UPDATE products SET name=?,weight_qty=?,weight_unit=?,sale_price=?,notes=?,updated_at=? WHERE id=?',(n,w,weight_unit.get() if w is not None else None,pv,notes.get().strip(),now_iso(),edit_id))
                        c.execute('DELETE FROM product_items WHERE product_id=?',(pid,))
                    else:
                        code=next_code('products','PROD');cur=c.execute('INSERT INTO products(code,name,weight_qty,weight_unit,sale_price,notes,updated_at) VALUES(?,?,?,?,?,?,?)',(code,n,w,weight_unit.get() if w is not None else None,pv,notes.get().strip(),now_iso()));pid=cur.lastrowid
                    for t,r,qv,uv in [(i[0],i[1],i[3],i[4]) for i in items]:c.execute('INSERT INTO product_items(product_id,item_type,ref_id,qty_per_unit,unit) VALUES(?,?,?,?,?)',(pid,t,r,qv,uv))
                snapshot_costs();d.destroy();self.refresh_all();self.notify('Produto salvo com sucesso.')
            except Exception as e:safe_error(d,'Não foi possível salvar o Produto',e)
            
        ttk.Label(d,text='* campo obrigatório; Peso/Rendimento pode ser definido depois.').pack(anchor='w',padx=16,pady=(0,4))
        
        act=d.action_host
        left=tk.Frame(act,bg=d.cget('bg'));left.pack(side='left',fill='y')
        RoundedActionButton(left, '<delete> Excluir Selecionados', bulk_delete_items, width=160, height=38, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030').pack(side='left', pady=7)
        
        right=tk.Frame(act,bg=d.cget('bg'));right.pack(side='right',fill='y')
        RoundedActionButton(right,'Salvar',save,width=92,height=38,fill='#F28C28',hover='#BA5200').pack(side='left',padx=(6,0),pady=7)
        RoundedActionButton(right,'Cancelar',d.destroy,width=92,height=38,fill='#6B7280',hover='#4B5563').pack(side='left',padx=(6,0),pady=7)
        
        load_ref();refresh_items()

    def new_product(self): self.product_form()

    def edit_selected_product(self):
        s=self.prod_tree.selection()
        if not s:return
        code=self.prod_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id FROM products WHERE code=?',(code,)).fetchone()
        if r:self.product_form(r['id'])

    def delete_selected_product(self):
        self._bulk_delete_list(self.prod_tree, 'product', use_selection_only=True)

    def delete_selected_products(self):
        tree=self.prod_tree
        checked=getattr(self,'_checked_rows',{}).get(str(tree),set())
        parents=[iid for iid in checked if not tree.parent(iid)]
        if len(parents)<2:
            return
        rows=[]
        with db() as c:
            for iid in parents:
                vals=tree.item(iid,'values'); code=vals[0] if vals else ''
                r=c.execute('SELECT id,name FROM products WHERE code=?',(code,)).fetchone()
                if r: rows.append(r)
        if not rows:return
        linked=[]
        with db() as c:
            for r in rows:
                refs=c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='PRODUCT' AND ref_id=?",(r['id'],)).fetchone()['n']
                if refs: linked.append(r['name'])
        if linked:
            msg='Alguns produtos selecionados possuem vínculos/histórico e não podem ser excluídos sem quebrar referências:\n\n'+'\n'.join('• '+n for n in linked)+'\n\nDeseja inativá-los? Se escolher Não, toda a operação será cancelada.'
            if not messagebox.askyesno('Itens vinculados',msg,parent=self):
                return
            with db() as c:
                c.execute('CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY)') if False else None
                cols={x['name'] for x in c.execute('PRAGMA table_info(products)').fetchall()}
                if 'active' in cols:
                    for r in rows:
                        if r['name'] in linked:c.execute('UPDATE products SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                else:
                    messagebox.showwarning('Inativação','Esta base ainda não possui o campo de inativação. A operação foi cancelada para preservar os vínculos.',parent=self);return
            self.refresh_all();self.notify('Produtos vinculados foram inativados.');return
        if not messagebox.askyesno('Excluir produtos',f'Excluir {len(rows)} produtos selecionados? Esta ação remove suas composições.',parent=self):
            return
        with db() as c:
            for r in rows:c.execute('DELETE FROM products WHERE id=?',(r['id'],))
        self.refresh_all();self.notify(f'{len(rows)} produtos excluídos com sucesso.')

    def _sort_prod_col(self, key):
        if getattr(self, '_prod_order_by', 'name') == key:
            self._prod_order_dir = 'DESC' if getattr(self, '_prod_order_dir', 'ASC') == 'ASC' else 'ASC'
        else:
            self._prod_order_by = key
            self._prod_order_dir = 'ASC'
        self.refresh_products()
        self.after_idle(self._redraw_prod_header)

    def refresh_products(self):
        if not hasattr(self,'prod_tree'):return
        for x in self.prod_tree.get_children():self.prod_tree.delete(x)
        
        query = '%'+self.prod_search.get().strip()+'%' if hasattr(self,'prod_search') else '%'
        status_filter = self.prod_status.get() if hasattr(self, 'prod_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        
        ob = getattr(self, '_prod_order_by', 'name')
        od = getattr(self, '_prod_order_dir', 'ASC')
        
        with db() as c:rows=c.execute(f'SELECT id,code,name,weight_qty,weight_unit,sale_price,COALESCE(active,1) as active, substr(created_at,1,10) as cdate, substr(COALESCE(updated_at,created_at),1,10) as udate FROM products WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()
        
        items = []
        for r in rows:
            try:cost=product_unit_cost(r['id'])
            except Exception:cost=0
            margin=((r['sale_price']-cost)/r['sale_price']*100) if r['sale_price'] else None
            with db() as c:comps=c.execute('SELECT item_type,ref_id,qty_per_unit AS qty,unit FROM product_items WHERE product_id=?',(r['id'],)).fetchall()
            
            has_arc = False
            comp_details = []
            for comp in comps:
                if comp['item_type'] == 'MATERIAL':
                    with db() as cd: m = cd.execute('SELECT name, COALESCE(archived,0) as arc FROM materials WHERE id=?',(comp['ref_id'],)).fetchone()
                else:
                    with db() as cd: m = cd.execute('SELECT name, COALESCE(archived,0) as arc FROM base_recipes WHERE id=?',(comp['ref_id'],)).fetchone()
                if m:
                    if m['arc']: has_arc = True
                    comp_details.append({'name': m['name'], 'arc': m['arc'], 'qty': comp['qty'], 'unit': comp['unit']})
            
            comp_details.sort(key=lambda x: x['name'].lower())
            name_disp = f"⚠️ {r['name']}" if has_arc else r['name']
            is_active = r['active']
            items.append({'r': r, 'cost': cost, 'margin': margin, 'name_disp': name_disp, 'is_active': is_active, 'comps': comp_details})
            
        if ob == 'name': items.sort(key=lambda x: x['r']['name'].lower(), reverse=(od=='DESC'))
        elif ob == 'code': items.sort(key=lambda x: str(x['r']['code']).lower() if x['r']['code'] else '', reverse=(od=='DESC'))
        elif ob == 'weight': items.sort(key=lambda x: x['r']['weight_qty'] or 0, reverse=(od=='DESC'))
        elif ob == 'cost': items.sort(key=lambda x: x['cost'], reverse=(od=='DESC'))
        elif ob == 'price': items.sort(key=lambda x: x['r']['sale_price'] or 0, reverse=(od=='DESC'))
        elif ob == 'margin': items.sort(key=lambda x: x['margin'] if x['margin'] is not None else -9999, reverse=(od=='DESC'))
        elif ob == 'date': items.sort(key=lambda x: x['r']['cdate'] or '', reverse=(od=='DESC'))
        elif ob == 'mod_date': items.sort(key=lambda x: x['r']['udate'] or '', reverse=(od=='DESC'))
        elif ob == 'status': items.sort(key=lambda x: x['is_active'], reverse=(od=='DESC'))
            
        for item in items:
            r = item['r']
            is_active = item['is_active']
            w_disp = (fmt_num(r['weight_qty'])+' '+str(r['weight_unit'] or '')).strip() or '-'
            margin = item['margin']
            iid=self.prod_tree.insert('','end',text='',values=(r['code'],item['name_disp'],w_disp,fmt(item['cost']),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-',r['cdate'] or '-',r['udate'] or '-','Ativo' if is_active else 'Inativo','','',''), tags=() if is_active else ('inactive',))
            for comp in item['comps']:
                n = f"{comp['name']} (⚠️ Excluído)" if comp['arc'] else comp['name']
                self.prod_tree.insert(iid,'end',text='',values=('',f'↳ {n}',fmt_num(comp['qty']),comp['unit'],'-','-','-','-','-','','',''))
        self._reset_checked(self.prod_tree)
        if hasattr(self, 'prod_icon_ov'): self.prod_icon_ov._redraw()
        if hasattr(self, '_redraw_prod_header'): self._redraw_prod_header()
        if hasattr(self, 'prod_empty_overlay'):
            if rows: self.prod_empty_overlay.place_forget()
            else: self.prod_empty_overlay.place(x=0, y=36, relwidth=1, relheight=1, height=-36)

    def product_history_dialog(self):
        s=self.prod_tree.selection()
        if not s:return
        code=self.prod_tree.item(s[0])['values'][0]
        with db() as c:p=c.execute('SELECT id FROM products WHERE code=?',(code,)).fetchone()
        if not p:return
        with db() as c:rows=c.execute('SELECT substr(recorded_at,1,7),cost,recorded_at FROM cost_history WHERE entity_type=\'PRODUCT\' AND entity_id=? ORDER BY id DESC',(p['id'],)).fetchall()
        v = self.prod_tree.item(s[0])['values']
        curr_row = (v[4],) if len(v) > 4 else ('-')
        CustomHistoryModal(self, f"Histórico: {v[1]}", (('registro', 'Data/Hora', 165), ('custo', 'Custo', 120)), [(r[2], r[1]) for r in rows], current_row_data=curr_row)

    # ---------- Configurações ----------

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
                    hover_fill = '#FEF3E9' if not getattr(self.app, '_dark', False) else '#2A1D11'
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
                fill = '#FEF3E9' if not getattr(self.app, '_dark', False) else '#2A1D11'
                fg = '#F28C28' if not getattr(self.app, '_dark', False) else '#F6A45A'
                font = ('Segoe UI', 10, 'bold')
            else:
                fill = bg
                fg = self.app.colors['muted']
                font = ('Segoe UI', 10, 'normal')
                
            self.panel.set_style(fill=fill, bg=bg)
            self.lbl.config(bg=fill, fg=fg, font=font)

