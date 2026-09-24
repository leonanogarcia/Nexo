import ast

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_redraw = '''        def redraw_mat_header(_event=None):
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
            
            # Use displaycolumns for mapping
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
                
            # LEFT fixed cover
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
                
                txt_chk = '☑' if is_all_checked else '☐'
                color_chk = '#2B3D55' if is_all_checked else '#A0ABB9'
                if getattr(self, '_dark', False): color_chk = '#FFFFFF' if is_all_checked else '#60769D'
                
                chk_id = c.create_text(cw0/2, h/2, text=txt_chk, fill=color_chk, font=('Segoe UI', 13), anchor='center', tags=('header_chk',))
                hitbox_id = c.create_rectangle(0, 0, cw0-2, h, fill='', outline='', tags=('header_chk',))
                c.tag_bind('header_chk', '<Button-1>', lambda e: self._toggle_all_checkboxes(self.mat_tree))
                
            # RIGHT fixed cover (Edit/Delete/Options)
            # Find the actual displayed indices of these fixed cols
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
                            img = Image.new('RGBA', (64, 64), (0,0,0,0))
                            draw = ImageDraw.Draw(img)
                            gcx, gcy = 32, 32
                            r_out, r_in = 28, 9
                            pts = []
                            for i in range(16):
                                angle = i * (math.pi / 8)
                                r = r_out if i % 2 == 0 else r_out - 8
                                pts.extend([gcx + r * math.cos(angle), gcy + r * math.sin(angle)])
                            draw.polygon(pts, fill=color)
                            draw.ellipse([gcx-r_in, gcy-r_in, gcx+r_in, gcy+r_in], fill='#EEF4FB')
                            return ImageTk.PhotoImage(img.resize((16, 16), Image.Resampling.LANCZOS))
                        
                        self._mat_header_imgs['gear_normal'] = make_gear('#60769D')
                        self._mat_header_imgs['gear_hover'] = make_gear('#F28C28')

                    c.create_image(cx + cw13/2, h/2, image=self._mat_header_imgs['gear_normal'], anchor='center', tags=('mat_gear', 'mat_gear_img'))
                    c.create_rectangle(cx, 0, cx+cw13, h, fill='', outline='', tags=('mat_gear',))
                    
                    c.tag_bind('mat_gear', '<Enter>', lambda e, c=c: (c.itemconfig('mat_gear_img', image=self._mat_header_imgs['gear_hover']), c.config(cursor='hand2')))
                    c.tag_bind('mat_gear', '<Leave>', lambda e, c=c: (c.itemconfig('mat_gear_img', image=self._mat_header_imgs['gear_normal']), c.config(cursor='')))
                    c.tag_bind('mat_gear', '<Button-1>', lambda e: self._show_mat_col_menu(e))'''

extractor = ast.parse(text)
methods = [n for n in ast.walk(extractor) if isinstance(n, ast.FunctionDef) and n.name == 'cadastro']
m_cad = methods[0]
cad_lines = text.split('\n')[m_cad.lineno-1:m_cad.end_lineno]
cad_text = '\n'.join(cad_lines)

ext2 = ast.parse(cad_text)
methods2 = [n for n in ast.walk(ext2) if isinstance(n, ast.FunctionDef) and n.name == 'redraw_mat_header']
m_redraw = methods2[0]

lines_before = cad_lines[:m_redraw.lineno-1]
lines_after = cad_lines[m_redraw.end_lineno:]

new_cad_text = '\n'.join(lines_before) + '\n' + new_redraw + '\n' + '\n'.join(lines_after)

lines = text.split('\n')
lines_before_all = lines[:m_cad.lineno-1]
lines_after_all = lines[m_cad.end_lineno:]

final_text = '\n'.join(lines_before_all) + '\n' + new_cad_text + '\n' + '\n'.join(lines_after_all)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(final_text)

print('Patched redraw_mat_header logic.')
