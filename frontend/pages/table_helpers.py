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

class TableHelpersMixin:
    def _selection_count(self, tree):
        return len(getattr(self, '_checked_rows', {}).get(str(tree), set()))

    def _set_single_checked(self, tree, iid):
        key=str(tree); self._checked_rows[key]={iid}
        for item in tree.get_children():
            tree.item(item, text='', image=self._img_chk_on if item==iid else self._img_chk_off)
        tree.selection_set(iid)
        self._update_action_states()
        
        children = tree.get_children()
        is_all_checked = len(self._checked_rows[key]) == len(children) and len(children) > 0
        if tree == getattr(self, 'mat_tree', None) and hasattr(self, '_redraw_mat_header'):
            self._redraw_mat_header()
        else:
            tree.heading('#0', text='', image=self._img_chk_on if is_all_checked else self._img_chk_off)
            
        tree.event_generate('<<TreeviewSelect>>')

    def _toggle_checkbox(self, tree, iid):
        key=str(tree); checked=self._checked_rows.setdefault(key,set())
        if iid in checked:
            checked.remove(iid)
        else:
            checked.add(iid)
        for item in tree.get_children():
            tree.item(item, text='', image=self._img_chk_on if item in checked else self._img_chk_off)
        if checked:
            tree.selection_set(iid if len(checked)==1 else tuple(checked))
        else:
            tree.selection_remove(tree.selection())
        self._update_action_states()
        
        children = tree.get_children()
        is_all_checked = len(checked) == len(children) and len(children) > 0
        if tree == getattr(self, 'mat_tree', None) and hasattr(self, '_redraw_mat_header'):
            self._redraw_mat_header()
        else:
            tree.heading('#0', text='', image=self._img_chk_on if is_all_checked else self._img_chk_off)
            
        tree.event_generate('<<TreeviewSelect>>')

    def _toggle_all_checkboxes(self, tree):
        key = str(tree)
        checked = self._checked_rows.setdefault(key, set())
        children = tree.get_children()
        if not children: return
        
        if len(checked) == len(children):
            checked.clear()
            tree.selection_remove(tree.selection())
        else:
            checked.update(children)
            tree.selection_set(children)
            
        for item in children:
            tree.item(item, text='', image=self._img_chk_on if item in checked else self._img_chk_off)
            
        self._update_action_states()
        tree.event_generate('<<TreeviewSelect>>')
        
        if tree == getattr(self, 'mat_tree', None) and hasattr(self, '_redraw_mat_header'):
            self._redraw_mat_header()
        else:
            is_all_checked = len(checked) == len(children)
            tree.heading('#0', text='', image=self._img_chk_on if is_all_checked else self._img_chk_off)

    def _update_action_states(self):
        for tree, cfg in getattr(self, '_action_buttons', {}).items():
            count=self._selection_count(tree)
            normal=cfg.get('normal', []) if isinstance(cfg, dict) else []
            bulk=cfg.get('bulk', []) if isinstance(cfg, dict) else []
            if count >= 2:
                for b in normal:
                    try: b.pack_forget()
                    except Exception: pass
                for b in bulk:
                    try: b.configure(state='normal')
                    except Exception: pass
                    try:
                        if not b.winfo_ismapped(): b.pack(side='left', padx=6)
                    except Exception: pass
            else:
                for b in bulk:
                    try: b.pack_forget()
                    except Exception: pass
                for b in normal:
                    try:
                        if not b.winfo_ismapped(): b.pack(side='left', padx=6)
                    except Exception: pass

    def _cancel_multiselection_for(self, tree):
        self._reset_checked(tree)
        try: tree.selection_remove(tree.selection())
        except Exception: pass

    def _run_normal_action(self, tree, func):
        if self._selection_count(tree) >= 2:
            self._cancel_multiselection_for(tree)
        func()

    def _reset_checked(self, tree):
        self._checked_rows[str(tree)] = set()
        for iid in tree.get_children(): tree.item(iid, text='', image=self._img_chk_off)
        if tree == getattr(self, 'mat_tree', None) and hasattr(self, '_redraw_mat_header'):
            self._redraw_mat_header()
        else:
            tree.heading('#0', text='', image=self._img_chk_off)
        self._update_action_states()

    def _action_photo(self, slug):
        if not hasattr(self, '_action_photo_refs'):
            self._action_photo_refs={}
        if slug not in self._action_photo_refs:
            try:self._action_photo_refs[slug]=tk.PhotoImage(file=str(UI_ASSETS/slug))
            except Exception:self._action_photo_refs[slug]=None
        return self._action_photo_refs[slug]

    def _tree_click(self, event, tree, kind):
        region = tree.identify_region(event.x, event.y)
        col = tree.identify_column(event.x)
        if region == 'heading' and col == '#0':
            self._toggle_all_checkboxes(tree)
            return 'break'
            
        iid=tree.identify_row(event.y)
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
            {'material':self.delete_selected_materials,'recipe':self.delete_selected_recipes,'product':self.delete_selected_products}[kind]()
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
        shell=RoundedPanel(parent, fill=self.colors['panel'], border='', radius=22, bg=self.colors['bg'], height=64)
        shell.pack(fill='x', padx=0, pady=(0,8)); shell.pack_propagate(False)
        inner=tk.Frame(shell,bg=self.colors['panel'])
        inner.pack(fill='both', expand=True, padx=24, pady=11)
        return shell, inner

    def _build_page_table_panel(self, parent):
        shell=RoundedPanel(parent, fill=self.colors['panel'], border='', radius=22, bg=self.colors['bg'])
        shell.pack(fill='both', expand=True, padx=0, pady=(0,12))
        inner=tk.Frame(shell,bg=self.colors['panel'])
        inner.pack(fill='both', expand=True, padx=12, pady=12)
        return shell, inner

    def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=32)
        # Search is fixed on the right, but we give it a min size by NOT propagating
        wrap.pack(side='right',padx=(14,0),fill='none',expand=False)
        return wrap

    def _auto_size_tree_column(self, tree, col):
        import tkinter.font as tkfont
        f = tkfont.Font(family='Segoe UI', size=10)
        max_w = 40
        txt = tree.heading(col, 'text')
        if txt: max_w = max(max_w, f.measure(txt) + 24)
        
        if tree == getattr(self, 'mat_tree', None) and hasattr(self, '_mat_header_specs'):
            if str(col).startswith('#'):
                try:
                    idx = int(col[1:])
                    if idx > 0:
                        txt = self._mat_header_specs[idx-1][1]
                        if txt: max_w = max(max_w, f.measure(txt) + 24)
                except Exception: pass

        c_idx = -1
        if str(col).startswith('#'):
            try: c_idx = int(col[1:]) - 1
            except Exception: pass
        else:
            cols = list(tree['columns'])
            if col in cols: c_idx = cols.index(col)
        
        for iid in tree.get_children():
            if col == '#0' or c_idx == -1:
                v = tree.item(iid, 'text')
            else:
                vals = tree.item(iid, 'values')
                v = str(vals[c_idx]) if c_idx < len(vals) else ''
            max_w = max(max_w, f.measure(v) + 24)
            
        tree.column(col, width=min(max_w, 600))

    def _on_native_tree_double_click(self, e, tree, default_action):
        if tree.identify_region(e.x, e.y) == 'separator':
            col = tree.identify_column(e.x)
            if col and col != 'dummy' and 'edit' not in col and 'delete' not in col:
                self._auto_size_tree_column(tree, col)
            return 'break'
        if default_action: default_action()

    def _setup_canvas_header_drag(self, canvas, tree, fixed_cols, redraw_cmd, state_key):
        canvas._drag_col = None
        canvas._drag_start_x = 0
        canvas._drag_start_w = 0
        def get_col_edge(x):
            total_w = sum(int(tree.column(c, 'width')) for c in ['#0'] + list(tree['columns']))
            try: x_offset = float(tree.xview()[0]) * total_w
            except Exception: x_offset = 0
            
            cx = -x_offset
            cols = ['#0'] + list(tree['columns'])
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
                canvas.after_idle(redraw_cmd)
        def on_motion(e):
            canvas.config(cursor='sb_h_double_arrow' if get_col_edge(e.x) and get_col_edge(e.x) not in fixed_cols else 'arrow')
        def on_double_click(e):
            col = get_col_edge(e.x)
            if col and col not in fixed_cols and col != 'dummy':
                setattr(self, f'_{state_key}_user_resized', False)
                self._auto_size_tree_column(tree, col)
                canvas.after_idle(redraw_cmd)
        
        canvas.bind('<Button-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<Motion>', on_motion)
        canvas.bind('<Double-1>', on_double_click)

    def _make_row_icon(self, kind):
        try:
            from PIL import Image, ImageTk
            if kind == 'edit':
                im = Image.open(UI_ASSETS / 'action_edit_reference_exact.png').convert('RGBA')
            elif kind == 'delete':
                im = Image.open(UI_ASSETS / 'action_delete_reference_exact.png').convert('RGBA')
            else:
                return None
            im = im.resize((16, 16), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(im)
        except Exception: return None

    def _toggle_active(self, kind, iid, current_active):
        table = {'material': 'materials', 'recipe': 'base_recipes', 'product': 'products'}[kind]
        new_val = 0 if current_active else 1
        with db() as c:
            c.execute(f'UPDATE {table} SET active=?, updated_at=? WHERE id=?', (new_val, now_iso(), iid))
        self.refresh_all()
        self.notify(f"Item {'desativado' if current_active else 'ativado'} com sucesso.")

    def _show_row_menu(self, tree, kind, iid, x, y, edit_cmd, delete_cmd):
        self._set_single_checked(tree, iid)
        is_active = 'inactive' not in tree.item(iid, 'tags')
        
        dark = getattr(self, '_dark', False)
        bg = self.colors['panel']
        fg = self.colors['text']
        hover = '#20375F' if dark else '#F4F7FC'
        border = self.colors['line']
        
        if hasattr(self, '_current_menu') and self._current_menu.winfo_exists():
            self._current_menu.destroy()

        menu = tk.Toplevel(self)
        menu.overrideredirect(True)
        menu.attributes('-topmost', True)
        self._current_menu = menu
        
        try:
            menu.configure(bg='#000001')
            menu.wm_attributes('-transparentcolor', '#000001')
            transparent_bg = '#000001'
        except Exception:
            transparent_bg = bg
            menu.configure(bg=bg)
        
        w, h = 180, 145
        menu.geometry(f'{w}x{h}+{x-w+10}+{y+5}')
        
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
        
        c.create_line(16, 72, w-16, 72, fill=border)
        
        try:
            from PIL import Image, ImageDraw, ImageTk
            im_e = Image.open(UI_ASSETS / 'action_edit_reference_exact.png').convert('RGBA').resize((16, 16), Image.Resampling.LANCZOS)
            im_d = Image.open(UI_ASSETS / 'action_delete_reference_exact.png').convert('RGBA').resize((16, 16), Image.Resampling.LANCZOS)
            
            icon_color = '#AFC0E2' if dark else '#687796'
            dis_color = '#4A5568' if dark else '#C5CEDB'
            
            def make_pause(color):
                im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
                d = ImageDraw.Draw(im)
                d.rectangle([4, 2, 6, 14], fill=color)
                d.rectangle([10, 2, 12, 14], fill=color)
                return im
                
            def make_play(color):
                im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
                ImageDraw.Draw(im).polygon([5, 2, 5, 14, 13, 8], fill=color)
                return im
                
            def make_disabled_img(im):
                im_dis = im.copy()
                alpha = im_dis.getchannel('A')
                alpha = alpha.point(lambda p: int(p * 0.35))
                im_dis.putalpha(alpha)
                return im_dis
            
            if not hasattr(self, '_menu_icons'):
                self._menu_icons = {}
            self._menu_icons['edit'] = ImageTk.PhotoImage(im_e)
            self._menu_icons['edit_dis'] = ImageTk.PhotoImage(make_disabled_img(im_e))
            self._menu_icons['delete'] = ImageTk.PhotoImage(im_d)
            self._menu_icons['pause'] = ImageTk.PhotoImage(make_pause(icon_color))
            self._menu_icons['pause_dis'] = ImageTk.PhotoImage(make_pause(dis_color))
            self._menu_icons['play'] = ImageTk.PhotoImage(make_play(icon_color))
            self._menu_icons['play_dis'] = ImageTk.PhotoImage(make_play(dis_color))
            
            img_e = self._menu_icons['edit'] if is_active else self._menu_icons['edit_dis']
            img_d = self._menu_icons['delete']
            img_p = self._menu_icons['pause'] if is_active else self._menu_icons['pause_dis']
            img_pl = self._menu_icons['play'] if not is_active else self._menu_icons['play_dis']
        except Exception:
            img_e = img_d = img_p = img_pl = None

        def add_item(oy, text, img, cmd, active=True):
            text_col = fg if active else ('#4A5568' if dark else '#C5CEDB')
            hitbox = c.create_rectangle(1, oy, w-1, oy+35, fill=bg, outline='', tags=(f'item_{oy}',))
            if img:
                c.create_image(24, oy+17, image=img, anchor='center', tags=(f'item_{oy}',))
            c.create_text(42, oy+17, text=text, fill=text_col, font=('Segoe UI', 10), anchor='w', tags=(f'item_{oy}',))
            
            if active:
                def on_click(e, c_cmd=cmd):
                    menu.destroy()
                    c_cmd()
                c.tag_bind(f'item_{oy}', '<Enter>', lambda e: c.itemconfig(hitbox, fill=hover))
                c.tag_bind(f'item_{oy}', '<Leave>', lambda e: c.itemconfig(hitbox, fill=bg))
                c.tag_bind(f'item_{oy}', '<Button-1>', on_click)
                c.tag_bind(f'item_{oy}', '<Enter>', lambda e: c.config(cursor='hand2'), add='+')
                c.tag_bind(f'item_{oy}', '<Leave>', lambda e: c.config(cursor='arrow'), add='+')

        add_item(5, 'Editar' if is_active else 'Editar (Desativado)', img_e, edit_cmd, is_active)
        add_item(35, 'Excluir', img_d, delete_cmd)
        add_item(75, 'Ativar', img_pl, lambda: self._toggle_active(kind, iid, False), not is_active)
        add_item(105, 'Desativar', img_p, lambda: self._toggle_active(kind, iid, True), is_active)
            
        menu.grab_set()
        def on_click_anywhere(e):
            x_root, y_root = e.x_root, e.y_root
            rx, ry, rw, rh = menu.winfo_rootx(), menu.winfo_rooty(), menu.winfo_width(), menu.winfo_height()
            if not (rx <= x_root <= rx+rw and ry <= y_root <= ry+rh):
                menu.destroy()
        menu.bind('<Button-1>', on_click_anywhere, add='+')

    def _attach_row_icon_overlay(self, tree, table_host, edit_col_idx, delete_col_idx, edit_cmd, delete_cmd):
        ov = tk.Canvas(table_host, bd=0, highlightthickness=0, cursor='arrow', bg=self.colors['field'])
        ov.place(relx=1.0, x=0, y=36, width=90, relheight=1.0, height=-36, anchor='ne')
        ov._icon_refs = []
        
        is_mat = tree == getattr(self, 'mat_tree', None)
        cw0 = 60
        y_off = 36
        ov_left = tk.Canvas(table_host, bd=0, highlightthickness=0, cursor='arrow', bg=self.colors['field'])
        ov_left.place(relx=0, x=0, y=y_off, width=cw0, relheight=1.0, height=-y_off, anchor='nw')
        
        if tree == getattr(self, 'mat_tree', None):
            kind = 'material'
        elif tree == getattr(self, 'rec_tree', None):
            kind = 'recipe'
        else:
            kind = 'product'

        def _redraw_overlay(*_):
            ov.delete('all')
            ov_left.delete('all')
            ov._icon_refs.clear()
            
            pass
                
            img_e = self._make_row_icon('edit')
            img_d = self._make_row_icon('delete')
            ex, dx, ox = 15, 45, 75
            selected = set(tree.selection())
            
            from tkinter.font import Font
            f_chk = Font(family='Segoe UI', size=13)
            
            for iid in tree.get_children():
                bb = tree.bbox(iid)
                if not bb: continue
                _, ry, _, rh = bb
                
                # Checkbox Overlay Drawing (Left)
                bg_color = self.colors['accent_soft'] if iid in selected else self.colors['field']
                
                ov_left.create_rectangle(0, ry, cw0, ry + rh, fill=bg_color, outline='', tags=(f'c_{iid}',))
                
                tags = tree.item(iid, 'tags')
                is_active = 'inactive' not in tags
                is_checked = iid in self._checked_rows.get(str(tree), set())
                cy = ry + rh // 2
                
                ov_left.create_image(35, cy, image=self._img_chk_on if is_checked else self._img_chk_off, anchor='center', tags=(f'c_{iid}',))
                ov_left.tag_bind(f'c_{iid}', '<Button-1>', lambda ev, i=iid: self._toggle_checkbox(tree, i))
                ov_left.tag_bind(f'c_{iid}', '<Enter>', lambda ev, i=iid: ov_left.config(cursor='hand2'))
                ov_left.tag_bind(f'c_{iid}', '<Leave>', lambda ev, i=iid: ov_left.config(cursor='arrow'))

                if len(tree.get_children(iid)) > 0:
                    cx = 15
                    is_open = tree.item(iid, 'open')
                    chev_color = '#687796'
                    
                    if is_open:
                        ov_left.create_line(cx-4, cy-2, cx, cy+3, cx+4, cy-2, fill=chev_color, width=2, capstyle='round', joinstyle='round', tags=(f'chev_{iid}',))
                    else:
                        ov_left.create_line(cx-2, cy-4, cx+3, cy, cx-2, cy+4, fill=chev_color, width=2, capstyle='round', joinstyle='round', tags=(f'chev_{iid}',))
                    
                    ov_left.create_rectangle(cx-10, cy-10, cx+10, cy+10, fill='', outline='', tags=(f'chev_{iid}',))
                    ov_left.tag_bind(f'chev_{iid}', '<Button-1>', lambda ev, i=iid: (tree.item(i, open=not tree.item(i, 'open')), _redraw_overlay()))
                    ov_left.tag_bind(f'chev_{iid}', '<Enter>', lambda ev, i=iid: ov_left.config(cursor='hand2'))
                    ov_left.tag_bind(f'chev_{iid}', '<Leave>', lambda ev, i=iid: ov_left.config(cursor='arrow'))
                
                # Action Buttons Overlay Drawing (Right)
                ov.create_rectangle(0, ry, 90, ry + rh, fill=bg_color, outline='')
                
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
                ov.create_oval(ox-1, cy-5, ox+1, cy-3, fill=dot_c, outline='', tags=(f'o_{iid}',))
                ov.create_oval(ox-1, cy-1, ox+1, cy+1, fill=dot_c, outline='', tags=(f'o_{iid}',))
                ov.create_oval(ox-1, cy+3, ox+1, cy+5, fill=dot_c, outline='', tags=(f'o_{iid}',))
                ov.create_rectangle(ox-8, cy-10, ox+8, cy+10, fill='', outline='', tags=(f'o_{iid}',))
                
                ov.tag_bind(f'o_{iid}', '<Button-1>', lambda ev, i=iid: self._show_row_menu(tree, kind, i, ev.x_root, ev.y_root, edit_cmd, delete_cmd))
                ov.tag_bind(f'o_{iid}', '<Enter>', lambda ev, i=iid: ov.config(cursor='hand2'))
                ov.tag_bind(f'o_{iid}', '<Leave>', lambda ev, i=iid: ov.config(cursor='arrow'))

        tree.bind('<Configure>', _redraw_overlay, add='+')
        tree.bind('<<TreeviewSelect>>', _redraw_overlay, add='+')
        
        orig_yscroll = tree.cget('yscrollcommand')
        def _on_yscroll(first, last):
            if orig_yscroll: tree.tk.call(orig_yscroll, first, last)
            tree.after_idle(_redraw_overlay)
        tree.configure(yscrollcommand=_on_yscroll)
        
        ov._redraw = _redraw_overlay
        tree._ov_left = ov_left
        return ov

