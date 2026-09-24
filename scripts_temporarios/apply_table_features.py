import re
import ast

with open('main.py', 'r', encoding='utf-8') as f: text = f.read()

# 1. Update refresh_materials
old_refresh = '''def refresh_materials(self):
        if not hasattr(self,'mat_tree'): return
        for x in self.mat_tree.get_children(): self.mat_tree.delete(x)
        query = '%'+self.mat_search.get().strip()+'%' if hasattr(self,'mat_search') else '%'
        status_filter = self.mat_status.get() if hasattr(self, 'mat_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        with db() as c:
            rows = c.execute(f\'\'\'SELECT code,COALESCE(barcode,''),name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,
                                       substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10), COALESCE(active,1), id
                                FROM materials WHERE {status_cond} AND (name LIKE ? OR COALESCE(brand,'') LIKE ? OR code LIKE ?) ORDER BY name\'\'\', (query,query,query)).fetchall()'''

new_refresh = '''def refresh_materials(self):
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
            rows = c.execute(f\'\'\'SELECT code,COALESCE(barcode,''),name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,
                                       substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10), COALESCE(active,1), id
                                FROM materials WHERE {status_cond} AND (name LIKE ? OR COALESCE(brand,'') LIKE ? OR code LIKE ?) 
                                ORDER BY {sql_order} COLLATE NOCASE {od}\'\'\', (query,query,query)).fetchall()'''

if old_refresh in text:
    text = text.replace(old_refresh, new_refresh)
else:
    print('Failed to replace refresh_materials!')

# 2. Inject sorting and menu methods into the App class
new_methods = '''
    def _show_mat_col_menu(self, e):
        menu = tk.Menu(self, tearoff=0, bg='#FFFFFF', fg='#18223A', font=('Segoe UI', 9))
        for idx, (key, txt, default_w) in enumerate(self._mat_header_specs, 1):
            if key in ('dummy', 'edit', 'delete', 'options', 'barcode'): continue
            
            var = tk.BooleanVar(value=key not in self._mat_hidden_cols)
            def toggle(k=key, v=var, dw=default_w, i=idx):
                if v.get():
                    if k in self._mat_hidden_cols: self._mat_hidden_cols.remove(k)
                    self.mat_tree.column(f'#{i}', width=dw, minwidth=dw, stretch=False)
                else:
                    if k not in self._mat_hidden_cols: self._mat_hidden_cols.append(k)
                    self.mat_tree.column(f'#{i}', width=0, minwidth=0, stretch=False)
                set_setting('mat_hidden_cols', self._mat_hidden_cols)
                self.after_idle(self._redraw_mat_header)
                
            menu.add_checkbutton(label=txt, variable=var, command=toggle)
        menu.tk_popup(e.x_root, e.y_root)

    def _sort_mat_col(self, key):
        if getattr(self, '_mat_order_by', 'name') == key:
            self._mat_order_dir = 'DESC' if getattr(self, '_mat_order_dir', 'ASC') == 'ASC' else 'ASC'
        else:
            self._mat_order_by = key
            self._mat_order_dir = 'ASC'
        self.refresh_materials()
        self.after_idle(self._redraw_mat_header)

    def refresh_materials(self):'''
text = text.replace('    def refresh_materials(self):', new_methods)


# 3. Update cadastro initial hidden cols
old_cadastro_start = '''    def cadastro(self, f):
        _, bar = self._build_page_toolbar(f)'''
new_cadastro_start = '''    def cadastro(self, f):
        self._mat_hidden_cols = get_setting('mat_hidden_cols')
        if self._mat_hidden_cols is None:
            self._mat_hidden_cols = ['code']
            set_setting('mat_hidden_cols', self._mat_hidden_cols)
        
        _, bar = self._build_page_toolbar(f)'''
text = text.replace(old_cadastro_start, new_cadastro_start)


# 4. Update redraw_mat_header for clickables and gear
# Find the exact lines in _redraw_mat_header that draw text and inject arrow logic + gear
old_header_text = '''                align = 'w' if col in ('#1', '#2', '#3') else 'center'
                anchor_x = x0+12 if align == 'w' else x0+cw/2
                c.create_text(anchor_x,h/2,text=txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor=align)
                c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                x0+=cw'''

new_header_text = '''                align = 'w' if col in ('#1', '#2', '#3') else 'center'
                anchor_x = x0+12 if align == 'w' else x0+cw/2
                tag = f'hdr_{key}'
                
                # Seta de ordenação
                arrow_txt = ''
                if getattr(self, '_mat_order_by', 'name') == key:
                    arrow_txt = ' ↑' if getattr(self, '_mat_order_dir', 'ASC') == 'ASC' else ' ↓'
                
                full_txt = txt + arrow_txt if align == 'w' else arrow_txt + txt
                tid = c.create_text(anchor_x, h/2, text=full_txt, fill='#60769D', font=('Segoe UI',9,'bold'), anchor=align, tags=(tag,))
                
                # Hitbox clicável
                c.create_rectangle(x0, 0, x0+cw, h, fill='', outline='', tags=(tag,))
                
                # Bindings Hover & Click
                c.tag_bind(tag, '<Enter>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#BA5200'))
                c.tag_bind(tag, '<Leave>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#60769D'))
                c.tag_bind(tag, '<Button-1>', lambda e, k=key: self._sort_mat_col(k))
                c.tag_bind(tag, '<Enter>', lambda e: c.config(cursor='hand2'), add='+')
                c.tag_bind(tag, '<Leave>', lambda e: c.config(cursor=''), add='+')
                
                c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                x0+=cw'''
if old_header_text in text:
    text = text.replace(old_header_text, new_header_text)
else:
    print('Failed to patch header text!')


old_gear_block = '''                if cw12 > 0:
                    img=self._mat_header_imgs.get('delete')
                    if img: c.create_image(cx+cw12/2, h/2, image=img, anchor='center')'''
new_gear_block = '''                if cw12 > 0:
                    img=self._mat_header_imgs.get('delete')
                    if img: c.create_image(cx+cw12/2, h/2, image=img, anchor='center')
                    cx += cw12
                
                if cw13 > 0:
                    # Desenhar engrenagem (16-point math gear) na coluna Options
                    import math
                    cx_gear = cx + cw13/2
                    cy = h/2
                    r_out = 7; r_in = 4
                    pts = []
                    for i in range(16):
                        angle = i * (math.pi / 8)
                        r = r_out if i % 2 == 0 else r_out - 2.5
                        pts.extend([cx_gear + r * math.cos(angle), cy + r * math.sin(angle)])
                    
                    c.create_polygon(pts, fill='#60769D', tags=('mat_gear',))
                    c.create_oval(cx_gear-r_in, cy-r_in, cx_gear+r_in, cy+r_in, fill=fill, outline='', tags=('mat_gear',))
                    
                    # Hitbox para a engrenagem
                    c.create_rectangle(cx, 0, cx+cw13, h, fill='', outline='', tags=('mat_gear',))
                    
                    # Bindings Engrenagem
                    c.tag_bind('mat_gear', '<Enter>', lambda e, c=c: (c.itemconfig(c.find_withtag('mat_gear')[0], fill='#BA5200'), c.config(cursor='hand2')))
                    c.tag_bind('mat_gear', '<Leave>', lambda e, c=c: (c.itemconfig(c.find_withtag('mat_gear')[0], fill='#60769D'), c.config(cursor='')))
                    c.tag_bind('mat_gear', '<Button-1>', lambda e: self._show_mat_col_menu(e))
'''
text = text.replace(old_gear_block, new_gear_block)

# Also apply initial hidden columns after header specs are defined
old_specs = "self._mat_header_specs=[('code','Código',100),"
# wait, it might have weird encoding. Let's just do it directly on `self._mat_header_imgs={}`
old_imgs = "self._mat_header_imgs={}"
new_imgs = '''self._mat_header_imgs={}
        
        # Apply hidden columns to Treeview initially
        for idx, (key, txt, dw) in enumerate(self._mat_header_specs, 1):
            if key in self._mat_hidden_cols:
                self.mat_tree.column(f'#{idx}', width=0, minwidth=0, stretch=False)'''
text = text.replace(old_imgs, new_imgs)


with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Success applying patches!')
