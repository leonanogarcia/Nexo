import ast

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# -------------------------------------------------------------
# 1. FIX THE MENU (DYNAMIC HEIGHT)
# -------------------------------------------------------------

new_menu = '''    def _show_mat_col_menu(self, e):
        if hasattr(self, '_mat_col_popup') and self._mat_col_popup.winfo_exists():
            self._mat_col_popup.destroy()
            
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        bg_color = '#000001'
        top.attributes('-transparentcolor', bg_color)
        top.config(bg=bg_color)
        self._mat_col_popup = top
        
        canvas = tk.Canvas(top, bg=bg_color, highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        
        panel = tk.Frame(canvas, bg='#FFFFFF')
        
        lbl_title = tk.Label(panel, text='EXIBIR COLUNAS', bg='#FFFFFF', fg='#A0ABB9', font=('Segoe UI', 8, 'bold'))
        lbl_title.pack(anchor='w', padx=12, pady=(8, 4))
        
        for idx, (key, txt, default_w) in enumerate(self._mat_header_specs, 1):
            if key in ('dummy', 'edit', 'delete', 'options', 'barcode'): continue
            
            row = tk.Frame(panel, bg='#FFFFFF', cursor='hand2')
            row.pack(fill='x', pady=1)
            
            is_vis = key not in self._mat_hidden_cols
            chk_char = '☑' if is_vis else '☐'
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
                is_vis_now = k not in self._mat_hidden_cols
                lt.config(bg='#FFFFFF', fg='#18223A' if is_vis_now else '#687796')
                
            for w in (row, lbl_chk, lbl_txt):
                w.bind('<Enter>', on_enter)
                w.bind('<Leave>', on_leave)
            
            def toggle(ev, k=key, lc=lbl_chk, lt=lbl_txt):
                if k in self._mat_hidden_cols:
                    self._mat_hidden_cols.remove(k)
                    lc.config(text='☑', fg='#F28C28')
                    lt.config(fg='#18223A')
                else:
                    self._mat_hidden_cols.append(k)
                    lc.config(text='☐', fg='#C0C9D8')
                    lt.config(fg='#687796')
                
                set_setting('mat_hidden_cols', self._mat_hidden_cols)
                
                valid_keys = [spec[0] for spec in self._mat_header_specs]
                disp = [c for c in valid_keys if c not in self._mat_hidden_cols and c != 'dummy']
                self.mat_tree['displaycolumns'] = disp
                self.after_idle(self._redraw_mat_header)
                
            for w in (row, lbl_chk, lbl_txt):
                w.bind('<Button-1>', toggle)
                
        # DYNAMIC HEIGHT CALCULATION
        top.update_idletasks()
        w_menu = 180
        h_menu = panel.winfo_reqheight() + 8
        
        canvas.config(width=w_menu, height=h_menu)
        
        def create_round_rect(c, x1, y1, x2, y2, r, **kwargs):
            points = (x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1)
            return c.create_polygon(points, smooth=True, **kwargs)
            
        create_round_rect(canvas, 1, 1, w_menu-1, h_menu-1, 12, fill='#FFFFFF', outline='#E5ECF5', width=1)
        
        # Place panel OVER the drawn rounded background
        canvas.create_window(w_menu/2, h_menu/2, window=panel, anchor='center', width=w_menu-6, height=h_menu-6)
        
        x_pos = max(0, e.x_root - w_menu - 10)
        y_pos = e.y_root + 15
        top.geometry(f"{w_menu}x{h_menu}+{x_pos}+{y_pos}")
        
        def close_popup(ev):
            if hasattr(self, '_mat_col_popup') and self._mat_col_popup.winfo_exists():
                self._mat_col_popup.destroy()
        
        top.focus_set()
        top.bind('<FocusOut>', lambda ev: top.destroy() if str(ev.widget) == str(top) else None)
        self.mat_tree.bind('<Button-1>', lambda ev: close_popup(ev), add='+')'''


# Parse and replace _show_mat_col_menu
extractor = ast.parse(text)
m_menu = [n for n in ast.walk(extractor) if isinstance(n, ast.FunctionDef) and n.name == '_show_mat_col_menu'][0]
lines = text.split('\n')
lines_before = lines[:m_menu.lineno-1]
lines_after = lines[m_menu.end_lineno:]

text = '\n'.join(lines_before) + '\n' + new_menu + '\n' + '\n'.join(lines_after)


# -------------------------------------------------------------
# 2. FIX THE GEAR ICON (FLAT TEETH / BLOCK ABSTRACTION)
# -------------------------------------------------------------
# Find the make_gear block inside _redraw_mat_header

old_gear_block = '''                        def make_gear(color):
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
                            return ImageTk.PhotoImage(img.resize((16, 16), Image.Resampling.LANCZOS))'''

new_gear_block = '''                        def make_gear(color):
                            img = Image.new('RGBA', (128, 128), (0,0,0,0))
                            draw = ImageDraw.Draw(img)
                            gcx, gcy = 64, 64
                            
                            # 1. Anel principal robusto
                            draw.ellipse([gcx-32, gcy-32, gcx+32, gcy+32], fill=color)
                            
                            # 2. Oito "dentes" chatos usando blocos/linhas grossas
                            for i in range(8):
                                angle = i * (math.pi / 4)
                                x1 = gcx + 50 * math.cos(angle)
                                y1 = gcy + 50 * math.sin(angle)
                                x2 = gcx - 50 * math.cos(angle)
                                y2 = gcy - 50 * math.sin(angle)
                                draw.line([x1, y1, x2, y2], fill=color, width=28)
                                
                            # 3. Furo central maciço
                            draw.ellipse([gcx-16, gcy-16, gcx+16, gcy+16], fill='#EEF4FB')
                            
                            return ImageTk.PhotoImage(img.resize((16, 16), Image.Resampling.LANCZOS))'''

if old_gear_block in text:
    text = text.replace(old_gear_block, new_gear_block)
else:
    print("WARNING: Could not find old gear block.")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Dynamic menu height and flat-tooth PIL gear applied successfully!")
