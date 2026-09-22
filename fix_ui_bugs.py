import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Fix placeholder check in RoundedEntry
code = re.sub(
    r"show=\(not self\._var\.get\(\)\) and not self\.entry\.focus_get\(\)",
    r"show = (not self._var.get()) and (self.focus_get() != self.entry)",
    code
)

# 2. Fix the Pill Capsule border
code = re.sub(
    r"self\.mat_status_wrap\.create_polygon\(20, 0, 90, 0, 110, 0, 110, 20, 110, 40, 90, 40, 20, 40, 0, 40, 0, 20, 0, 0, smooth=True, fill=self\.colors\['field'\], outline=''\)",
    r"self.mat_status_wrap.create_polygon(20, 1, 90, 1, 109, 1, 109, 20, 109, 39, 90, 39, 20, 39, 1, 39, 1, 20, 1, 1, smooth=True, fill=self.colors['panel'], outline=self.colors['border'])",
    code
)

# 3. Fix the overlay 3-dots code by replacing the entire method
new_overlay = """    def _attach_row_icon_overlay(self, tree, table_host, edit_col_idx, delete_col_idx,
                                  edit_cmd, delete_cmd):
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
                    ov.create_image(ex, cy, image=img_e, anchor='center', tags=(f'e_{iid}',))
                    if is_active:
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
            if tree.yview() != ov.yview():
                ov.yview_moveto(tree.yview()[0])
            _redraw_overlay()

        tree.bind('<Configure>', _redraw_overlay, add='+')
        tree.bind('<MouseWheel>', _sync_scroll, add='+')
        tree.bind('<<TreeviewSelect>>', _redraw_overlay, add='+')
        tree.bind('<<TreeviewOpen>>', _redraw_overlay, add='+')
        tree.bind('<<TreeviewClose>>', _redraw_overlay, add='+')
        
        def _on_right_click(ev):
            iid = tree.identify_row(ev.y)
            if iid:
                self._show_row_menu(tree, kind, iid, ev.x_root, ev.y_root, edit_cmd, delete_cmd)
        
        tree.bind('<Button-3>', _on_right_click)

        ov._redraw = _redraw_overlay
        return ov

    def edit_selected_material(self):"""

code = re.sub(
    r"    def _attach_row_icon_overlay\(self.*?def edit_selected_material\(self\):",
    new_overlay,
    code,
    flags=re.DOTALL
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
