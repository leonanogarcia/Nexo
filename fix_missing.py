import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

missing_functions = """    def _make_row_icon(self, kind):
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

    def _setup_canvas_header_drag"""

code = code.replace("    def _setup_canvas_header_drag", missing_functions)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
