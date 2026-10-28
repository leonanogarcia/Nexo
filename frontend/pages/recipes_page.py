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

class RecipesPageMixin:
    def recipes_page(self, f):
        _, bar=self._build_page_toolbar(f)
        
        rec_add=RoundedActionButton(bar, '+ Nova Receita', lambda: self._run_normal_action(self.rec_tree, self.new_recipe), width=130, height=42, fill='#F28C28', hover='#BA5200')
        rec_add.pack(side='left')
        
        self.rec_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir', lambda: self.delete_selected_recipes(), width=95, height=40, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030')
        
        rec_history=RoundedActionButton(bar, '<clock> Histórico', lambda: self._run_normal_action(self.rec_tree, self.recipe_history_dialog), width=120, height=42, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        rec_history.pack(side='left', padx=(8, 0))
        
        rec_conv=RoundedActionButton(bar, '<convert> Conversões', lambda: self.material_conversion_dialog(), width=135, height=42, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        rec_conv.pack(side='left', padx=(8, 0))
        

        
        def show_rec_more_menu():
            if hasattr(self, '_current_menu') and self._current_menu.winfo_exists():
                self._current_menu.destroy()
                
            menu = tk.Toplevel(self)
            menu.overrideredirect(True)
            menu.attributes('-topmost', True)
            self._current_menu = menu
            
            bg = self.colors['panel']
            border = self.colors['line']
            try:
                menu.configure(bg='#000001')
                menu.wm_attributes('-transparentcolor', '#000001')
                transparent_bg = '#000001'
            except Exception:
                transparent_bg = bg
                menu.configure(bg=bg)
                
            w, h = 180, 115
            x = rec_more.winfo_rootx()
            y = rec_more.winfo_rooty() + rec_more.winfo_height() + 4
            menu.geometry(f'{w}x{h}+{x}+{y}')
            
            c = tk.Canvas(menu, bg=transparent_bg, bd=0, highlightthickness=0)
            c.pack(fill='both', expand=True)
            
            r = 8
            c.create_rectangle(r, 0, w-r, h, fill=bg, outline='')
            c.create_rectangle(0, r, w, h-r, fill=bg, outline='')
            c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=bg, outline='')
            c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=bg, outline='')
            c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=bg, outline='')
            c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=bg, outline='')
            
            c.create_line(r, 0, w-r, 0, fill=border)
            c.create_line(r, h-1, w-r, h-1, fill=border)
            c.create_line(0, r, 0, h-r, fill=border)
            c.create_line(w-1, r, w-1, h-r, fill=border)
            c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, style='arc', outline=border)
            c.create_arc(w-2*r-1, 0, w-1, 2*r, start=0, extent=90, style='arc', outline=border)
            c.create_arc(0, h-2*r-1, 2*r, h-1, start=180, extent=90, style='arc', outline=border)
            c.create_arc(w-2*r-1, h-2*r-1, w-1, h-1, start=270, extent=90, style='arc', outline=border)
            
            ai_active = int(get_setting('ai_enabled', '0'))
            import_txt = '✨ Importar' if ai_active else 'Anexar'
            icon_t = 'ai' if ai_active else 'import'
            
            items = [
                (import_txt, icon_t, lambda: self._run_normal_action(self.rec_tree, self.ai_import_dialog)),
                ('Download', 'download', lambda: self._run_normal_action(self.rec_tree, self.download_attached_document)),
                ('View', 'eye', lambda: self._run_normal_action(self.rec_tree, self.view_attached_document))
            ]
            
            for i, (label, icon_type, cmd) in enumerate(items):
                oy = 5 + i * 35
                hitbox = c.create_rectangle(1, oy, w-1, oy+35, fill=bg, outline='', tags=f'opt_{i}')
                
                ix, iy = 24, oy + 17
                col = '#687796'
                text_col = self.colors['text']
                
                is_disabled = False
                if not self.rec_tree.selection() and label != '✨ Importar':
                    is_disabled = True
                    col = '#9BA5B7'
                    text_col = '#9BA5B7'
                
                if icon_type == 'import':
                    if not hasattr(c, 'clip_img'):
                        try:
                            from PIL import Image, ImageTk
                            c.clip_img = ImageTk.PhotoImage(Image.open('assets/icons/clip.png'))
                        except Exception:
                            c.clip_img = None
                    if getattr(c, 'clip_img', None):
                        c.create_image(ix, iy, image=c.clip_img)
                elif icon_type == 'download':
                    c.create_line(ix, iy-4, ix, iy+4, fill=col, width=2)
                    c.create_line(ix-3, iy+1, ix, iy+4, ix+3, iy+1, fill=col, width=2)
                    c.create_line(ix-5, iy+6, ix+5, iy+6, fill=col, width=2)
                elif icon_type == 'eye':
                    c.create_oval(ix-6, iy-4, ix+6, iy+4, outline=col, width=2)
                    c.create_oval(ix-2, iy-2, ix+2, iy+2, fill=col, outline='')
                    
                if label.startswith('✨ '):
                    c.create_text(24, oy+17, text='✨', fill=col, font=('Segoe UI', 10), anchor='center', tags=f'opt_{i}')
                    c.create_text(42, oy+17, text=label[2:], fill=text_col, font=('Segoe UI', 10), anchor='w', tags=f'opt_{i}')
                else:
                    c.create_text(42, oy+17, text=label, fill=text_col, font=('Segoe UI', 10), anchor='w', tags=f'opt_{i}')
                
                if not is_disabled:
                    def on_click(e, c_cmd=cmd):
                        menu.destroy()
                        c_cmd()
                    hover = '#20375F' if getattr(self, '_dark', False) else '#F4F7FC'
                    c.tag_bind(f'opt_{i}', '<Enter>', lambda e, hb=hitbox: c.itemconfig(hb, fill=hover))
                    c.tag_bind(f'opt_{i}', '<Leave>', lambda e, hb=hitbox: c.itemconfig(hb, fill=bg))
                    c.tag_bind(f'opt_{i}', '<Button-1>', on_click)
                    c.tag_bind(f'opt_{i}', '<Enter>', lambda e: c.config(cursor='hand2'), add='+')
                    c.tag_bind(f'opt_{i}', '<Leave>', lambda e: c.config(cursor='arrow'), add='+')
            
            root = self.winfo_toplevel()
            def close_on_click(e):
                if menu.winfo_exists():
                    mx, my = menu.winfo_rootx(), menu.winfo_rooty()
                    mw, mh = menu.winfo_width(), menu.winfo_height()
                    if not (mx <= e.x_root <= mx+mw and my <= e.y_root <= my+mh):
                        menu.destroy()
                try: root.unbind('<Button-1>', bind_id)
                except Exception: pass
            bind_id = root.bind('<Button-1>', close_on_click, add='+')
              
            menu.focus_set()
            def on_focus_out(e):
                if menu.winfo_exists():
                    menu.destroy()
            menu.bind('<FocusOut>', on_focus_out)
            
        rec_more=RoundedActionButton(bar, 'Mais ▾', show_rec_more_menu, width=80, height=42, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557')
        rec_more.pack(side='left', padx=(8, 0))

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
        
        self.rec_tree=ttk.Treeview(table_host,columns=('code','name','yield','unit','cost','date','mod_date','status','dummy','edit','delete','options'),show='tree')
        self.rec_tree.tag_configure('inactive', foreground='#9AA9BF')
        self.rec_tree.column('#0',width=60,minwidth=60,stretch=False)
        
        for k,w in [('code',100),('name',380),('yield',120),('unit',65),('cost',120),('date',130),('mod_date',130),('status',80),('edit',30),('delete',30),('options',30)]:
            self.rec_tree.column(k,width=w,minwidth=w,anchor='center' if k in ('yield','unit','cost','date','mod_date','status') else 'w',stretch=False)
        self.rec_tree.column('dummy', width=0, minwidth=0, stretch=True)
        
        self.rec_hsb = PillScrollbar(table_host, self.rec_tree)
        original_scroll_rec = self.rec_hsb._on_scroll
        def hsb_scroll_rec(first, last):
            original_scroll_rec(first, last)
            self.after_idle(self._redraw_rec_header) if hasattr(self, '_redraw_rec_header') else None
        self.rec_tree.configure(xscrollcommand=hsb_scroll_rec)
        self.rec_tree.pack(fill='both',expand=True)
        
        self._rec_header_specs=[('code','Código',100),('name','Receita',380),('yield','Rendimento',120),('unit','Un.',65),('cost','Custo total',120),('date','Data de criação',130),('mod_date','Última modificação',130),('status','Status',80),('dummy','',0),('edit','',30),('delete','',30),('options','',30)]
        self._rec_header_imgs={}
        
        valid_keys = [spec[0] for spec in self._rec_header_specs]
        disp = [c for c in valid_keys if c not in self._rec_hidden_cols]
        self.rec_tree['displaycolumns'] = disp
        
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
                total_w = sum(int(self.rec_tree.column(col, 'width')) for col in ['#0'] + list(self.rec_tree['displaycolumns']))
                x_offset = float(self.rec_tree.xview()[0]) * total_w
            except Exception: x_offset = 0
            x0 = -x_offset
            
            disp = self.rec_tree['displaycolumns']
            if disp == ('#all',): disp = self.rec_tree['columns']
            spec_dict = {key: txt for key, txt, _ in self._rec_header_specs}
            
            cols = [('#0', '', 'dummy')]
            for i, col_id in enumerate(disp, 1):
                cols.append((f'#{i}', spec_dict.get(col_id, ''), col_id))
                
            for idx,(col,txt,key) in enumerate(cols):
                try: cw=int(self.rec_tree.column(col,'width'))
                except Exception: cw=0
                if col == '#0': cw = 60
                if key in ('dummy', 'edit', 'delete'):
                    x0+=cw; continue
                align = 'w' if key in ('code', 'name') else 'center'
                anchor_x = x0+12 if align == 'w' else x0+cw/2
                
                arrow_txt = ''
                if getattr(self, '_rec_order_by', 'name') == key:
                    arrow_txt = ' ↑' if getattr(self, '_rec_order_dir', 'ASC') == 'ASC' else ' ↓'
                full_txt = txt + arrow_txt if align == 'w' else arrow_txt + txt
                
                tag = f'hdr_{key}'
                tid = c.create_text(anchor_x,h/2,text=full_txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor=align, tags=(tag,))
                c.create_rectangle(x0, 0, x0+cw, h, fill='', outline='', tags=(tag,))
                c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                
                c.tag_bind(tag, '<Enter>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#BA5200'))
                c.tag_bind(tag, '<Leave>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#60769D'))
                c.tag_bind(tag, '<Button-1>', lambda e, k=key: self._sort_rec_col(k))
                
                x0+=cw
            cw0 = 60
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
                c.create_image(cw0/2, h/2, image=self._img_chk_on if is_all_checked else self._img_chk_off, anchor='center', tags=('header_chk',))
                c.create_rectangle(0, 0, cw0-2, h, fill='', outline='', tags=('header_chk',))
                c.tag_bind('header_chk', '<Button-1>', lambda e: self._toggle_all_checkboxes(self.rec_tree))
            
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
                c.tag_bind('gear_icon', '<Button-1>', lambda e: self._show_generic_col_menu(e, '_rec_col_popup', self.rec_tree, self._rec_header_specs, self._rec_hidden_cols, 'rec_hidden_cols', '_redraw_rec_header'))
        
        self._redraw_rec_header=redraw_rec_header
        self.rec_header.bind('<Configure>', redraw_rec_header)
        self.rec_tree.bind('<Configure>', lambda e: self.rec_tree.after_idle(redraw_rec_header))
        self.after_idle(redraw_rec_header)
        
        self._setup_canvas_header_drag(self.rec_header, self.rec_tree, ['edit','delete'], redraw_rec_header, 'rec')

        self.rec_tree.bind('<Button-1>',lambda e:self._tree_click(e,self.rec_tree,'recipe'))
        self.rec_tree.bind('<Double-1>',lambda e: (self.edit_selected_recipe(), 'break')[1])
        
        self.rec_icon_ov=self._attach_row_icon_overlay(self.rec_tree, table_host, 6, 7, self.edit_selected_recipe, self.delete_selected_recipe)
        try:
            from PIL import Image, ImageTk
            img_path = UI_ASSETS / 'empty_state_reference_exact.png'
            self._rec_empty_img = ImageTk.PhotoImage(Image.open(img_path))
            
            self.rec_empty_overlay = tk.Frame(table_host, bg=self.colors['field'])
            inner = tk.Frame(self.rec_empty_overlay, bg=self.colors['field'])
            inner.place(relx=0.5, rely=0.5, anchor='center')
            
            l_img = tk.Label(inner, image=self._rec_empty_img, bg=self.colors['field'])
            l_img.pack(pady=(0, 10))
            
            l_title = tk.Label(inner, text='Nenhuma receita cadastrada.', bg=self.colors['field'], fg='#687796', font=('Segoe UI', 11, 'bold'))
            l_title.pack(pady=(0, 4))
            
            l_sub = tk.Label(inner, text='Clique em + Nova Receita para adicionar a primeira receita.', bg=self.colors['field'], fg='#8A99B5', font=('Segoe UI', 9))
            l_sub.pack()
        except Exception:
            self.rec_empty_overlay = tk.Label(table_host, text='Nenhuma receita cadastrada.\nClique em + Nova Receita para adicionar a primeira receita.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))
        self._action_buttons[self.rec_tree]={'normal':[rec_add,rec_history,rec_conv,rec_more],'bulk':[self.rec_bulk_delete_btn]}
        self._update_action_states()

    def recipe_form(self, edit_id=None, imported_recipe=None, imported_source=None):
        is_edit=edit_id is not None
        with db() as c:
            existing=c.execute('SELECT * FROM base_recipes WHERE id=?',(edit_id,)).fetchone() if is_edit else None
            current_items=c.execute('SELECT material_id,qty,unit FROM base_recipe_items WHERE recipe_id=?',(edit_id,)).fetchall() if is_edit else []
        d=Modal(self,'Editar Receita' if is_edit else 'Nova Receita','920x580')
        name=tk.StringVar(value=existing['name'] if existing else '')
        yield_qty=tk.StringVar(value=fmt_num(existing['yield_qty']) if existing and existing['yield_qty'] is not None else '')
        yield_unit=tk.StringVar(value=existing['yield_unit'] if existing and existing['yield_unit'] else 'g')
        notes=tk.StringVar(value=existing['notes'] or '' if existing else '')
        
        try: text_col = self.colors.get('text', '#18223A')
        except: text_col = '#18223A'
        
        def make_field(parent, label, var, w_chars, w_pixels=None, is_dropdown=False, opts=None, bg=None, is_num=False):
            bg = bg or parent.cget('bg')
            wrap = tk.Frame(parent, bg=bg)
            tk.Label(wrap, text=label, bg=bg, fg=text_col, font=('Segoe UI', 9)).pack(anchor='w', padx=4, pady=(1,0))
            if is_dropdown:
                wd = RoundedDropdown(wrap, var, opts or [], width=w_pixels or 140, align='left')
            elif is_num:
                wd = numeric_entry(wrap, var, width=w_chars)
            else:
                wd, _ = rounded_entry(wrap, var, width=w_chars)
            wd.pack(fill='x', expand=True, padx=4, pady=(0,8))
            return wrap, wd

        top = tk.Frame(d, bg=d.cget('bg'), padx=24, pady=16); top.pack(fill='x')
        make_field(top, 'Nome *', name, 30)[0].pack(side='left', fill='x', expand=True)
        make_field(top, 'Rendimento', yield_qty, 12, is_num=True)[0].pack(side='left')
        make_field(top, 'Unidade', yield_unit, 10, is_dropdown=True, opts=UNITS)[0].pack(side='left')
        make_field(top, 'Observações', notes, 24)[0].pack(side='left', fill='x', expand=True)
        
        box_outer = tk.Frame(d, bg=d.cget('bg'), padx=16, pady=4); box_outer.pack(fill='both', expand=True)
        tk.Label(box_outer, text='Composição — somente itens do Cadastro', bg=d.cget('bg'), fg=self.colors.get('text', '#18223A'), font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 4))
        
        box_top = RoundedPanel(box_outer, fill='#FFFFFF', radius=12, bg=d.cget('bg'))
        box_top.pack(fill='x', pady=(0, 8))
        
        material_var=tk.StringVar();qty_var=tk.StringVar();unit_var=tk.StringVar(value='g')
        
        _, material_wd = make_field(box_top, 'Insumo', material_var, 30, w_pixels=300, is_dropdown=True, bg='#FFFFFF')
        material_wd.master.pack(side='left', fill='x', expand=True, padx=(4,0), pady=4)
        make_field(box_top, 'Quantidade', qty_var, 12, is_num=True, bg='#FFFFFF')[0].pack(side='left', pady=4)
        _, unit_wd = make_field(box_top, 'Unidade', unit_var, 10, w_pixels=120, is_dropdown=True, opts=UNITS, bg='#FFFFFF')
        unit_wd.master.pack(side='left', pady=4)
        
        items=[]
        if current_items:
            for r in current_items:
                with db() as c: m=c.execute('SELECT id,code,name FROM materials WHERE id=?',(r['material_id'],)).fetchone()
                if m: items.append((m['id'],m['name'],r['qty'],r['unit']))
        if imported_recipe and 'items' in imported_recipe:
            items.extend(imported_recipe['items'])
            
        _, table_host = self._build_page_table_panel(box_outer)
        
        header_canvas = tk.Canvas(table_host, bg=self.colors['panel'], bd=0, highlightthickness=0, height=36)
        header_canvas.pack(fill='x', padx=2, pady=(0,0))
        
        tree=ttk.Treeview(table_host, columns=('item','qty','unit','cost','dummy','edit','delete'), show='tree')
        tree.column('#0', width=60, minwidth=60, stretch=False)
        for k, w, a in [('item', 360, 'w'), ('qty', 100, 'center'), ('unit', 70, 'center'), ('cost', 110, 'center'), ('dummy', 0, 'w'), ('edit', 30, 'center'), ('delete', 30, 'center')]:
            tree.column(k, width=w, minwidth=w, anchor=a, stretch=(k=='dummy'))
        tree.pack(fill='both', expand=True)
        
        header_specs = [('item', 'Item', 360), ('qty', 'Quantidade', 100), ('unit', 'Un.', 70), ('cost', 'Custo', 110), ('dummy', '', 0), ('edit', '', 30), ('delete', '', 30)]
        
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
                align = 'w' if key == 'item' else 'center'
                anchor_x = x0 + 12 if align == 'w' else x0 + cw/2
                if idx == 0: x0 += 60 
                
                arrow_txt = ''
                if sort_state['by'] == key:
                    arrow_txt = ' ↑' if sort_state['dir'] == 'ASC' else ' ↓'
                full_txt = txt + arrow_txt if align == 'w' else arrow_txt + txt
                
                tag = f'hdr_{key}'
                tid = c.create_text(anchor_x + (60 if idx==0 else 0), h/2, text=full_txt, fill='#60769D', font=('Segoe UI', 9, 'bold'), anchor=align, tags=(tag,))
                c.create_rectangle(x0 - (60 if idx==0 else 0), 0, x0+cw, h, fill='', outline='', tags=(tag,))
                if key in ('item', 'qty', 'cost'):
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
        
        def load_materials(*_):
            vals=[f'{r["id"]} — {r["name"]} ({r["code"]})' for r in list_names('materials')]
            material_wd._opts = vals
        def load_units(*_):
            if '—' not in material_var.get(): unit_wd._opts = UNITS; return
            mid=int(material_var.get().split(' — ')[0]); custom=[r['name'] for r in custom_units_for_material(mid)]; unit_wd._opts = UNITS+tuple(custom)
            
        material_var.trace_add('write', load_units)
        
        sort_state = {'by': 'item', 'dir': 'ASC'}
        def sort_items(key):
            if sort_state['by'] == key: sort_state['dir'] = 'DESC' if sort_state['dir'] == 'ASC' else 'ASC'
            else: sort_state['by'] = key; sort_state['dir'] = 'ASC'
            refresh_items()
            
        def refresh_items():
            for x in tree.get_children():tree.delete(x)
            dec = []
            for i, (mid,n,q,u) in enumerate(items):
                try: cst=material_cost(mid,q,u)
                except Exception as e: cst=f'Erro'
                dec.append({'i': i, 'n': n, 'q': q, 'u': u, 'cst': cst})
                
            k = sort_state['by']
            rev = (sort_state['dir'] == 'DESC')
            if k == 'item': dec.sort(key=lambda x: x['n'].lower(), reverse=rev)
            elif k == 'qty': dec.sort(key=lambda x: float(x['q']), reverse=rev)
            elif k == 'cost': dec.sort(key=lambda x: x['cst'] if isinstance(x['cst'], (int, float)) else 0, reverse=rev)
            
            for item in dec:
                cst = item['cst']
                tree.insert('','end',iid=str(item['i']),values=(item['n'],item['q'],item['u'],fmt(cst) if isinstance(cst,(int,float)) else cst))
            redraw_header(); _redraw_overlay()
                
        def add_item():
            try:
                if ' — ' not in material_var.get(): raise ValueError('Selecione um Insumo do Cadastro.')
                mid=int(material_var.get().split(' — ')[0]);q=to_float(qty_var.get(),'Quantidade');u=unit_var.get().strip()
                if q<=0:raise ValueError('A Quantidade deve ser maior que zero.')
                items.append((mid,material_var.get().split(' — ')[1].split(' (')[0],q,u));material_var.set('');qty_var.set('');refresh_items()
            except Exception as e:safe_error(d,'Não foi possível adicionar o item',e)
            
        RoundedActionButton(box_top, 'Adicionar', add_item, width=100, height=32, fill='#EFF4FB', hover='#E3EBF6', fg='#1D3557', bg='#FFFFFF').pack(side='left', padx=12, pady=(16,4))
        
        def edit_item():
            sel=tree.selection()
            if not sel:
                messagebox.showwarning('Receita','Selecione um item da composição para editar.',parent=d); return
            idx=int(sel[0]); mid,n,q,u=items[idx]
            material_var.set(f'{mid} — {n}')
            load_units()
            qty_var.set(fmt_num(q)); unit_var.set(u)
            items.pop(idx); refresh_items()

        def delete_item():
            sel=tree.selection()
            if not sel:
                messagebox.showwarning('Receita','Selecione um item da composição para excluir.',parent=d); return
            idx=int(sel[0]); items.pop(idx); refresh_items()

        def bulk_delete_items():
            cset = self._checked_rows.get(str(tree), set())
            if not cset: return
            if not messagebox.askyesno('Receita', f'Excluir {len(cset)} itens marcados da composição?', parent=d): return
            indices = sorted([int(i) for i in cset], reverse=True)
            for idx in indices: items.pop(idx)
            cset.clear()
            refresh_items()

        tree.bind('<Double-1>',lambda e: edit_item())
        
        def save():
            try:
                n=name.get().strip()
                if not n: raise ValueError('O campo "Nome" é obrigatório.')
                y=optional_float(yield_qty.get()); yu=yield_unit.get().strip() if y is not None else None
                if y is not None and y<=0: raise ValueError('O Rendimento deve ser maior que zero.')
                if not items: raise ValueError('Adicione pelo menos um Insumo à receita.')
                if is_edit:
                    with db() as c: before=dict(c.execute('SELECT * FROM base_recipes WHERE id=?',(edit_id,)).fetchone())
                    self.ask_edit_reason('RECEITA_BASE',edit_id,before,{'name':n,'yield_qty':y,'yield_unit':yu,'notes':notes.get().strip(),'items':[(m,q,u) for m,_,q,u in items]})
                with db() as c:
                    if is_edit:
                        rid=edit_id
                        c.execute('UPDATE base_recipes SET name=?,yield_qty=?,yield_unit=?,notes=?,updated_at=? WHERE id=?',(n,y,yu,notes.get().strip(),now_iso(),edit_id))
                        c.execute('DELETE FROM base_recipe_items WHERE recipe_id=?',(rid,))
                    else:
                        code=next_code('base_recipes','RB');cur=c.execute('INSERT INTO base_recipes(code,name,yield_qty,yield_unit,notes,updated_at) VALUES(?,?,?,?,?,?)',(code,n,y,yu,notes.get().strip(),now_iso()));rid=cur.lastrowid
                    for mid,_,q,u in items:c.execute('INSERT INTO base_recipe_items(recipe_id,material_id,qty,unit) VALUES(?,?,?,?)',(rid,mid,q,u))
                if imported_source:
                    save_uploaded_document('RECIPE_BASE', rid, imported_source)
                snapshot_costs();d.destroy();self.refresh_all();self.notify('Receita salva com sucesso.')
            except Exception as e:safe_error(d,'Não foi possível salvar a Receita',e)
            
        ttk.Label(d,text='* campo obrigatório; Rendimento pode ser definido depois.').pack(anchor='w',padx=16,pady=(0,4))
        
        act=d.action_host
        left=tk.Frame(act,bg=d.cget('bg'));left.pack(side='left',fill='y')
        RoundedActionButton(left, '<delete> Excluir Selecionados', bulk_delete_items, width=160, height=38, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030').pack(side='left', pady=7)
        
        right=tk.Frame(act,bg=d.cget('bg'));right.pack(side='right',fill='y')
        RoundedActionButton(right,'Salvar',save,width=92,height=38,fill='#F28C28',hover='#BA5200').pack(side='left',padx=(6,0),pady=7)
        RoundedActionButton(right,'Cancelar',d.destroy,width=92,height=38,fill='#6B7280',hover='#4B5563').pack(side='left',padx=(6,0),pady=7)
        
        load_materials();refresh_items()

    def new_recipe(self): self.recipe_form()

    def edit_selected_recipe(self):
        s=self.rec_tree.selection()
        if not s:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id FROM base_recipes WHERE code=?',(code,)).fetchone()
        if r:self.recipe_form(r['id'])

    def delete_selected_recipe(self):
        self._bulk_delete_list(self.rec_tree, 'recipe', use_selection_only=True)

    def _sort_rec_col(self, key):
        if getattr(self, '_rec_order_by', 'name') == key:
            self._rec_order_dir = 'DESC' if getattr(self, '_rec_order_dir', 'ASC') == 'ASC' else 'ASC'
        else:
            self._rec_order_by = key
            self._rec_order_dir = 'ASC'
        self.refresh_recipes()
        self.after_idle(self._redraw_rec_header)

    def ai_import_dialog(self):
        from tkinter import filedialog
        import datetime
        import json
        import threading
        
        filepath = filedialog.askopenfilename(title="Selecionar Receita", filetypes=[("Imagens e PDFs", "*.png;*.jpg;*.jpeg;*.pdf")])
        if not filepath:
            return
            
        ai_enabled = int(get_setting('ai_enabled', '0'))
        if not ai_enabled:
            # Comportamento Anexar: salva o arquivo na receita selecionada
            sel = self.rec_tree.selection()
            if sel:
                code = self.rec_tree.item(sel[0])['values'][0]
                with db() as c:
                    r = c.execute('SELECT id FROM base_recipes WHERE code=?', (code,)).fetchone()
                if r:
                    save_uploaded_document('RECIPE_BASE', r['id'], filepath)
                    self.show_toast("Item anexado com sucesso!")
                    return
            self.recipe_form(imported_source=filepath)
            return
            
        # Comportamento Smart
        limit = int(get_setting('ai_daily_limit', '50'))
        today = datetime.date.today().isoformat()
        
        with db() as c:
            row = c.execute('SELECT request_count FROM ai_usage_logs WHERE date_str=?', (today,)).fetchone()
            count = row['request_count'] if row else 0
            
        if count >= limit:
            messagebox.showwarning("Atenção", f"Limite de segurança de {limit} leituras diárias atingido. O Nexo salvou o documento apenas como anexo. Para importar automaticamente, aguarde a renovação no dia seguinte (tempo de recarga 24H) ou altere seu limite nas Configurações da IA.", parent=self.winfo_toplevel())
            sel = self.rec_tree.selection()
            if sel:
                code = self.rec_tree.item(sel[0])['values'][0]
                with db() as c:
                    r = c.execute('SELECT id FROM base_recipes WHERE code=?', (code,)).fetchone()
                if r:
                    save_uploaded_document('RECIPE_BASE', r['id'], filepath)
                    self.show_toast("Item anexado com sucesso!")
                    return
            self.recipe_form(imported_source=filepath)
            return
            
        api_key = get_setting('ai_api_key', '')
        if not api_key:
            messagebox.showerror("Atenção", "Chave de API não configurada. Vá em Configurações para inserir a chave do Google Gemini.", parent=self.winfo_toplevel())
            self.recipe_form(imported_source=filepath)
            return
            
        # Abre tela de "Processando"
        d = tk.Toplevel(self)
        d.overrideredirect(True)
        d.attributes('-topmost', True)
        d.geometry(f"400x150+{self.winfo_screenwidth()//2 - 200}+{self.winfo_screenheight()//2 - 75}")
        bg = self.colors['panel']
        d.configure(bg='#000001'); d.wm_attributes('-transparentcolor', '#000001')
        p = RoundedPanel(d, fill=bg, radius=16, border=self.colors['line'], bg='#000001')
        p.pack(fill='both', expand=True, padx=4, pady=4)
        tk.Label(p, text="✨ Lendo receita com Inteligência Artificial...", bg=bg, fg=self.colors['text'], font=('Segoe UI', 12, 'bold')).pack(pady=(40, 5))
        tk.Label(p, text="Isso pode levar alguns segundos.", bg=bg, fg=self.colors['muted'], font=('Segoe UI', 9)).pack()
        d.update()
        
        def run_ai():
            try:
                import requests
                import base64
                import mimetypes
                
                with open(filepath, "rb") as f:
                    file_data = f.read()
                
                mime_type = mimetypes.guess_type(filepath)[0] or 'image/jpeg'
                if mime_type == 'application/pdf':
                    pass # Gemini 1.5 suporta PDF nativamente
                
                b64_data = base64.b64encode(file_data).decode('utf-8')
                
                prompt = """
                Atue como um extrator de receitas culinárias para um sistema ERP de restaurante.
                Extraia a receita do arquivo fornecido.
                Retorne ESTRITAMENTE e APENAS um JSON válido, sem markdown, sem explicações adicionais, com o seguinte formato:
                {
                    "nome": "Nome da Receita",
                    "rendimento_qtde": 1,
                    "rendimento_unidade": "un",
                    "ingredientes": [
                        {"nome": "Nome do Ingrediente 1", "qtde": 200, "unidade": "g"},
                        {"nome": "Nome do Ingrediente 2", "qtde": 1, "unidade": "un"}
                    ]
                }
                Se a unidade ou o rendimento não estiverem claros, deixe em branco ou use "un". Tente inferir a quantidade como número.
                """
                
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": mime_type, "data": b64_data}}
                        ]
                    }],
                    "generationConfig": {"temperature": 0.1}
                }
                
                modelos_fallback = ['gemini-flash-latest', 'gemini-flash-lite-latest', 'gemini-3.6-flash']
                data = None
                ultimo_erro = "Erro desconhecido ao contatar a IA."
                import time
                
                for modelo in modelos_fallback:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
                    sucesso = False
                    for tentativa in range(3):
                        res = requests.post(url, json=payload, timeout=30)
                        if res.status_code == 200:
                            data = res.json()
                            sucesso = True
                            break
                        else:
                            try:
                                erro_json = res.json()
                                erro_msg = erro_json.get('error', {}).get('message', res.text)
                                if "high demand" in erro_msg.lower():
                                    ultimo_erro = "Servidores do Google estão sobrecarregados no momento."
                                else:
                                    ultimo_erro = erro_msg
                            except:
                                ultimo_erro = f"Erro {res.status_code}: {res.text}"
                            time.sleep(1)
                    if sucesso:
                        break
                        
                if not data:
                    raise Exception(f"{ultimo_erro}\nTodos os modelos de IA falharam após múltiplas tentativas.")
                
                text_result = data['candidates'][0]['content']['parts'][0]['text']
                # Clean markdown blocks if present
                text_result = text_result.strip()
                if text_result.startswith('```json'): text_result = text_result[7:]
                elif text_result.startswith('```'): text_result = text_result[3:]
                if text_result.endswith('```'): text_result = text_result[:-3]
                text_result = text_result.strip()
                
                recipe_data = json.loads(text_result)
                
                # Increment usage count
                with db() as c:
                    if count == 0:
                        c.execute("INSERT INTO ai_usage_logs(date_str, request_count) VALUES(?, 1)", (today,))
                    else:
                        c.execute("UPDATE ai_usage_logs SET request_count = request_count + 1 WHERE date_str=?", (today,))
                        
                self.after(0, lambda: [d.destroy(), self.ai_review_dialog(recipe_data, filepath)])
                
            except Exception as e:
                self.after(0, lambda err=str(e): [d.destroy(), safe_error(self.winfo_toplevel(), "Falha na Extração", f"Erro ao contatar a IA: {err}\\nAbrindo modo manual."), self.recipe_form(imported_source=filepath)])
                
        threading.Thread(target=run_ai, daemon=True).start()
    def ai_review_dialog(self, recipe_data, filepath):
        import difflib
        d = tk.Toplevel(self)
        d.title("Revisão da Inteligência Artificial")
        d.geometry("900x700")
        d.configure(bg=self.colors['bg'])
        d.transient(self)
        d.grab_set()
        
        top = tk.Frame(d, bg=self.colors['bg'], padx=16, pady=16)
        top.pack(fill='x')
        tk.Label(top, text="✨ Eis o que a IA entendeu da sua receita:", bg=self.colors['bg'], fg=self.colors['text'], font=('Segoe UI', 14, 'bold')).pack(anchor='w', pady=(0, 16))
        
        info = tk.Frame(top, bg=self.colors['bg'])
        info.pack(fill='x')
        tk.Label(info, text="Nome da Receita:", bg=self.colors['bg']).grid(row=0, column=0, sticky='w')
        name_var = tk.StringVar(value=recipe_data.get('nome', ''))
        ttk.Entry(info, textvariable=name_var, width=40).grid(row=0, column=1, padx=8, sticky='w')
        
        tk.Label(info, text="Rendimento:", bg=self.colors['bg']).grid(row=0, column=2, sticky='w', padx=(16,0))
        qty_var = tk.StringVar(value=str(recipe_data.get('rendimento_qtde', '1')))
        ttk.Entry(info, textvariable=qty_var, width=10).grid(row=0, column=3, padx=8, sticky='w')
        
        tk.Label(info, text="Unidade:", bg=self.colors['bg']).grid(row=0, column=4, sticky='w')
        unit_var = tk.StringVar(value=recipe_data.get('rendimento_unidade', 'un'))
        ttk.Entry(info, textvariable=unit_var, width=10).grid(row=0, column=5, padx=8, sticky='w')
        
        tk.Label(d, text="Composição (Mapeamento de Insumos):", bg=self.colors['bg'], fg=self.colors['text'], font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=16, pady=(8,4))
        tk.Label(d, text="Os itens em laranja não foram encontrados perfeitamente no seu estoque e precisam ser mapeados.", bg=self.colors['bg'], fg=self.colors['muted'], font=('Segoe UI', 9)).pack(anchor='w', padx=16, pady=(0,8))
        
        canvas = tk.Canvas(d, bg=self.colors['bg'], highlightthickness=0, bd=0)
        canvas.pack(side='top', fill='both', expand=True, padx=16)
        sb = ttk.Scrollbar(d, orient='vertical', command=canvas.yview)
        sb.place(in_=canvas, relx=1.0, rely=0, relheight=1.0, anchor='ne')
        canvas.configure(yscrollcommand=sb.set)
        
        pad = tk.Frame(canvas, bg=self.colors['bg'])
        win = canvas.create_window((0,0), window=pad, anchor='nw')
        
        def _sync(_=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.itemconfigure(win, width=canvas.winfo_width())
        pad.bind('<Configure>', _sync)
        canvas.bind('<Configure>', _sync)
        
        with db() as c:
            mats = c.execute("SELECT id, name, purchase_unit FROM materials ORDER BY name").fetchall()
            
        mat_options = [f"{m['id']} - {m['name']} ({m['purchase_unit']})" for m in mats]
        mat_names = [m['name'] for m in mats]
        name_to_opt = {m['name']: f"{m['id']} - {m['name']} ({m['purchase_unit']})" for m in mats}
        
        item_vars = []
        
        headers = tk.Frame(pad, bg=self.colors['panel'])
        headers.pack(fill='x', pady=2)
        tk.Label(headers, text="Lido na Receita (IA)", width=35, anchor='w', bg=self.colors['panel'], font=('Segoe UI', 9, 'bold')).pack(side='left', padx=4)
        tk.Label(headers, text="Insumo no Nexo", width=40, anchor='w', bg=self.colors['panel'], font=('Segoe UI', 9, 'bold')).pack(side='left', padx=4)
        tk.Label(headers, text="Qtde", width=10, anchor='w', bg=self.colors['panel'], font=('Segoe UI', 9, 'bold')).pack(side='left', padx=4)
        tk.Label(headers, text="Unidade", width=10, anchor='w', bg=self.colors['panel'], font=('Segoe UI', 9, 'bold')).pack(side='left', padx=4)
        
        for ing in recipe_data.get('ingredientes', []):
            row = tk.Frame(pad, bg=self.colors['bg'])
            row.pack(fill='x', pady=4)
            
            raw_name = ing.get('nome', '')
            lbl = tk.Label(row, text=raw_name, width=35, anchor='w', bg=self.colors['bg'])
            lbl.pack(side='left', padx=4)
            
            cbox_var = tk.StringVar()
            cbox = ttk.Combobox(row, textvariable=cbox_var, values=mat_options, state='readonly', width=38)
            cbox.pack(side='left', padx=4)
            
            q_var = tk.StringVar(value=str(ing.get('qtde', '0')))
            ttk.Entry(row, textvariable=q_var, width=10).pack(side='left', padx=4)
            
            u_var = tk.StringVar(value=ing.get('unidade', 'g'))
            ttk.Entry(row, textvariable=u_var, width=10).pack(side='left', padx=4)
            
            match = difflib.get_close_matches(raw_name, mat_names, n=1, cutoff=0.5)
            if match:
                cbox_var.set(name_to_opt[match[0]])
            else:
                lbl.configure(fg='#C53030', font=('Segoe UI', 9, 'bold')) # Orange/Red indicator
                cbox_var.set('')
                
            item_vars.append({'cbox': cbox_var, 'q': q_var, 'u': u_var})
            
        bot = tk.Frame(d, bg=self.colors['bg'])
        bot.pack(fill='x', padx=16, pady=16)
        
        def confirm():
            final_items = []
            for v in item_vars:
                sel = v['cbox'].get()
                if not sel:
                    messagebox.showwarning("Atenção", "Por favor, mapeie todos os insumos antes de confirmar (selecione no dropdown os itens em branco).", parent=d)
                    return
                try:
                    q = float(v['q'].get().replace(',', '.'))
                except:
                    messagebox.showwarning("Atenção", "Quantidade inválida encontrada.", parent=d)
                    return
                u = v['u'].get().strip()
                mid = int(sel.split(' - ')[0])
                mname = sel.split(' - ')[1].split(' (')[0]
                final_items.append((mid, mname, q, u))
                
            recipe_obj = {
                'name': name_var.get().strip(),
                'yield_qty': qty_var.get().strip(),
                'yield_unit': unit_var.get().strip(),
                'items': final_items
            }
            d.destroy()
            self.recipe_form(imported_recipe=recipe_obj, imported_source=filepath)
            
        RoundedActionButton(bot, 'Cancelar', d.destroy, width=120, height=42, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030').pack(side='left')
        RoundedActionButton(bot, 'Confirmar e Preencher', confirm, width=220, height=42, fill='#F28C28', hover='#BA5200').pack(side='right')



    def refresh_recipes(self):
        if not hasattr(self,'rec_tree'):return
        for x in self.rec_tree.get_children():self.rec_tree.delete(x)
        
        query = '%'+self.rec_search.get().strip()+'%' if hasattr(self,'rec_search') else '%'
        status_filter = self.rec_status.get() if hasattr(self, 'rec_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        
        ob = getattr(self, '_rec_order_by', 'name')
        od = getattr(self, '_rec_order_dir', 'ASC')
        
        with db() as c:rows=c.execute(f'SELECT id,code,name,yield_qty,yield_unit,COALESCE(active,1) as active, substr(created_at,1,10) as cdate, substr(COALESCE(updated_at,created_at),1,10) as udate FROM base_recipes WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()
        
        items = []
        for r in rows:
            try:cost=recipe_cost(r['id'])
            except Exception:cost=0
            with db() as c:comps=c.execute('SELECT m.name,bri.qty,bri.unit,COALESCE(m.archived,0) as arc FROM base_recipe_items bri JOIN materials m ON m.id=bri.material_id WHERE bri.recipe_id=? ORDER BY m.name COLLATE NOCASE ASC',(r['id'],)).fetchall()
            has_arc = any(comp['arc'] for comp in comps)
            name_disp = f"⚠️ {r['name']}" if has_arc else r['name']
            
            is_active = r['active']
            items.append({'r': r, 'cost': cost, 'name_disp': name_disp, 'is_active': is_active, 'comps': comps})
            
        if ob == 'name': items.sort(key=lambda x: x['r']['name'].lower(), reverse=(od=='DESC'))
        elif ob == 'code': items.sort(key=lambda x: str(x['r']['code']).lower() if x['r']['code'] else '', reverse=(od=='DESC'))
        elif ob == 'yield': items.sort(key=lambda x: x['r']['yield_qty'] or 0, reverse=(od=='DESC'))
        elif ob == 'cost': items.sort(key=lambda x: x['cost'], reverse=(od=='DESC'))
        elif ob == 'date': items.sort(key=lambda x: x['r']['cdate'] or '', reverse=(od=='DESC'))
        elif ob == 'mod_date': items.sort(key=lambda x: x['r']['udate'] or '', reverse=(od=='DESC'))
        elif ob == 'status': items.sort(key=lambda x: x['is_active'], reverse=(od=='DESC'))
            
        for item in items:
            r = item['r']
            is_active = item['is_active']
            iid=self.rec_tree.insert('','end',text='',values=(r['code'],item['name_disp'],fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(item['cost']),r['cdate'] or '-',r['udate'] or '-','Ativo' if is_active else 'Inativo','','',''), tags=() if is_active else ('inactive',))
            for comp in item['comps']:
                comp_name = f"{comp['name']} (⚠️ Excluído)" if comp['arc'] else comp['name']
                self.rec_tree.insert(iid,'end',text='',values=('',f'↳ {comp_name}',fmt_num(comp['qty']),comp['unit'],'-','-','-','-','','',''))
        self._reset_checked(self.rec_tree)
        if hasattr(self, 'rec_icon_ov'): self.rec_icon_ov._redraw()
        if hasattr(self, '_redraw_rec_header'): self._redraw_rec_header()
        if hasattr(self, 'rec_empty_overlay'):
            if rows: self.rec_empty_overlay.place_forget()
            else: self.rec_empty_overlay.place(x=0, y=36, relwidth=1, relheight=1, height=-36)

    def export_selected_recipe(self):
        s=self.rec_tree.selection()
        if not s:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name,yield_qty,yield_unit,notes FROM base_recipes WHERE code=?',(code,)).fetchone()
        if not r:return
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.txt',filetypes=[('Documento de texto','*.txt'),('Word','*.docx'),('PDF','*.pdf')],initialfile=f'{r["name"]}.txt')
        if not path:return
        text=self.recipe_export_text(r['id'])
        try:
            if path.lower().endswith('.txt'):
                Path(path).write_text(text,encoding='utf-8')
            elif path.lower().endswith('.docx'):
                try:
                    from docx import Document
                except ImportError: raise RuntimeError('Para exportar Word, instale "python-docx".')
                doc=Document();doc.add_heading(r['name'],0)
                for line in text.splitlines():doc.add_paragraph(line)
                doc.save(path)
            else:
                try:
                    from reportlab.pdfgen import canvas
                except ImportError: raise RuntimeError('Para exportar PDF, instale "reportlab".')
                c=canvas.Canvas(path);y=800
                for line in text.splitlines():
                    c.drawString(40,y,line[:110]);y-=16
                    if y<50:c.showPage();y=800
                c.save()
            messagebox.showinfo('Exportação','Receita exportada com sucesso.',parent=self)
        except Exception as e:safe_error(self,'Não foi possível exportar a receita',e)

    def recipe_export_text(self,rid):
        with db() as c:
            r=c.execute('SELECT * FROM base_recipes WHERE id=?',(rid,)).fetchone()
            rows=c.execute('''SELECT m.id,m.name,bri.qty,bri.unit FROM base_recipe_items bri JOIN materials m ON m.id=bri.material_id WHERE bri.recipe_id=?''',(rid,)).fetchall()
        lines=[r['name'],'',f'Rendimento: {fmt_num(r["yield_qty"])} {r["yield_unit"] or ""}'.strip(),'','Composição:']
        for x in rows:
            try:cst=material_cost(x['id'],x['qty'],x['unit'])
            except Exception:cst=0
            lines.append(f'- {x["name"]}: {fmt_num(x["qty"])} {x["unit"]} — {fmt(cst)}')
        lines += ['',f'Custo total: {fmt(recipe_cost(rid))}']
        return '\n'.join(lines)

    def _material_id_by_name(self,name):
        with db() as c:return c.execute('SELECT id FROM materials WHERE name=?',(name,)).fetchone()['id']

    def recipe_history_dialog(self):
        s=self.rec_tree.selection()
        if not s:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id FROM base_recipes WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:rows=c.execute("SELECT substr(recorded_at,1,7),cost,recorded_at FROM cost_history WHERE entity_type='RECIPE_BASE' AND entity_id=? ORDER BY id DESC",(r['id'],)).fetchall()
        v = self.rec_tree.item(s[0])['values']
        curr_row = (v[4],) if len(v) > 4 else ('-')
        CustomHistoryModal(self, f"Histórico: {v[1]}", (('registro', 'Data/Hora', 165), ('custo', 'Custo', 120)), [(r[2], r[1]) for r in rows], current_row_data=curr_row)

    def download_attached_document(self):
        s=self.rec_tree.selection()
        if not s:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM base_recipes WHERE code=?',(code,)).fetchone()
        doc=latest_document('RECIPE_BASE',r['id']) if r else None
        if not doc or not Path(doc['stored_path']).exists():
            messagebox.showinfo('Documento','Esta Receita não possui documento original armazenado.',parent=self)
            return
        src_path = Path(doc['stored_path'])
        dest_path = filedialog.asksaveasfilename(
            title="Salvar Cópia do Documento",
            defaultextension=src_path.suffix,
            initialfile=f"Receita_{code}{src_path.suffix}",
            parent=self.winfo_toplevel()
        )
        if dest_path:
            import shutil
            shutil.copy2(src_path, dest_path)
            messagebox.showinfo("Download Concluído", f"Cópia salva em:\n{dest_path}", parent=self.winfo_toplevel())

    def view_attached_document(self):
        s=self.rec_tree.selection()
        if not s:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM base_recipes WHERE code=?',(code,)).fetchone()
        doc=latest_document('RECIPE_BASE',r['id']) if r else None
        if not doc or not Path(doc['stored_path']).exists():
            messagebox.showinfo('Documento','Esta Receita não possui documento original armazenado.',parent=self)
            return
            
        src_path = Path(doc['stored_path'])
        ext = src_path.suffix.lower()
        if ext == '.pdf':
            import os; os.startfile(src_path)
        elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
            v = tk.Toplevel(self)
            v.title("Visualizador do Anexo")
            v.geometry("600x700")
            v.transient(self.winfo_toplevel())
            v.configure(bg=self.colors['bg'])
            from PIL import Image, ImageTk
            try:
                img = Image.open(src_path)
                img.thumbnail((580, 680), Image.LANCZOS)
                ph = ImageTk.PhotoImage(img)
                lbl = tk.Label(v, image=ph, bg=self.colors['bg'])
                lbl.image = ph
                lbl.pack(expand=True, fill='both')
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exibir imagem: {e}", parent=self.winfo_toplevel())
        else:
            messagebox.showinfo("Formato", "Formato não suportado para visualização interna. Por favor, faça o Download.", parent=self.winfo_toplevel())

    # ---------- Produtos ----------
