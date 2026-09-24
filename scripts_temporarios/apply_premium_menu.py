import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update the Gear Math to be solid
old_gear = '''                    import math
                    cx_gear = cx + cw13/2
                    cy = h/2
                    r_out = 7; r_in = 4
                    pts = []
                    for i in range(16):
                        angle = i * (math.pi / 8)
                        r = r_out if i % 2 == 0 else r_out - 2.5
                        pts.extend([cx_gear + r * math.cos(angle), cy + r * math.sin(angle)])
                    
                    c.create_polygon(pts, fill='#60769D', tags=('mat_gear',))
                    c.create_oval(cx_gear-r_in, cy-r_in, cx_gear+r_in, cy+r_in, fill=fill, outline='', tags=('mat_gear',))'''

new_gear = '''                    import math
                    cx_gear = cx + cw13/2
                    cy = h/2
                    r_out = 8; r_in = 2.5
                    pts = []
                    for i in range(16):
                        angle = i * (math.pi / 8)
                        r = r_out if i % 2 == 0 else r_out - 3
                        pts.extend([cx_gear + r * math.cos(angle), cy + r * math.sin(angle)])
                    
                    c.create_polygon(pts, fill='#60769D', outline='', tags=('mat_gear',))
                    c.create_oval(cx_gear-r_in, cy-r_in, cx_gear+r_in, cy+r_in, fill=fill, outline='', tags=('mat_gear',))'''

if old_gear in text:
    text = text.replace(old_gear, new_gear)
else:
    print("WARNING: Could not find old gear math to replace.")

# 2. Update the Menu Logic to use Custom Toplevel
old_menu = '''    def _show_mat_col_menu(self, e):
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
        menu.tk_popup(e.x_root, e.y_root)'''

new_menu = '''    def _show_mat_col_menu(self, e):
        if hasattr(self, '_mat_col_popup') and self._mat_col_popup.winfo_exists():
            self._mat_col_popup.destroy()
            
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        self._mat_col_popup = top
        
        panel = tk.Frame(top, bg='#FFFFFF', highlightbackground='#E5ECF5', highlightthickness=1)
        panel.pack(fill='both', expand=True)
        
        lbl_title = tk.Label(panel, text='EXIBIR COLUNAS', bg='#FFFFFF', fg='#A0ABB9', font=('Segoe UI', 8, 'bold'))
        lbl_title.pack(anchor='w', padx=12, pady=(10, 6))
        
        for idx, (key, txt, default_w) in enumerate(self._mat_header_specs, 1):
            if key in ('dummy', 'edit', 'delete', 'options', 'barcode'): continue
            
            row = tk.Frame(panel, bg='#FFFFFF', cursor='hand2')
            row.pack(fill='x', pady=0)
            
            is_vis = key not in self._mat_hidden_cols
            chk_char = '☑' if is_vis else '☐'
            chk_color = '#F28C28' if is_vis else '#C0C9D8'
            
            lbl_chk = tk.Label(row, text=chk_char, fg=chk_color, bg='#FFFFFF', font=('Segoe UI', 12), cursor='hand2')
            lbl_chk.pack(side='left', padx=(12, 6), pady=4)
            
            lbl_txt = tk.Label(row, text=txt, fg='#18223A' if is_vis else '#687796', bg='#FFFFFF', font=('Segoe UI', 9), cursor='hand2')
            lbl_txt.pack(side='left', padx=(0, 16), pady=4)
            
            def on_enter(ev, r=row, lc=lbl_chk, lt=lbl_txt, k=key):
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
            
            def toggle(ev, k=key, dw=default_w, i=idx, lc=lbl_chk, lt=lbl_txt):
                if k in self._mat_hidden_cols:
                    self._mat_hidden_cols.remove(k)
                    self.mat_tree.column(f'#{i}', width=dw, minwidth=dw, stretch=False)
                    lc.config(text='☑', fg='#F28C28')
                    lt.config(fg='#18223A')
                else:
                    self._mat_hidden_cols.append(k)
                    self.mat_tree.column(f'#{i}', width=0, minwidth=0, stretch=False)
                    lc.config(text='☐', fg='#C0C9D8')
                    lt.config(fg='#687796')
                set_setting('mat_hidden_cols', self._mat_hidden_cols)
                self.after_idle(self._redraw_mat_header)
                
            for w in (row, lbl_chk, lbl_txt):
                w.bind('<Button-1>', toggle)
                
        # Padding final
        tk.Frame(panel, bg='#FFFFFF', height=6).pack()
            
        top.update_idletasks()
        w = top.winfo_reqwidth()
        # Calcula a posição baseada no ponteiro do mouse, mas espelha para a esquerda
        # Subtrai toda a largura da janela + 5px de margem
        x_pos = max(0, e.x_root - w - 5)
        y_pos = e.y_root + 15
        top.geometry(f"+{x_pos}+{y_pos}")
        
        # Fecha a janela ao clicar fora dela
        def close_popup(ev):
            if hasattr(self, '_mat_col_popup') and self._mat_col_popup.winfo_exists():
                self._mat_col_popup.destroy()
        
        # Garante foco e captura clique fora
        top.focus_set()
        top.bind('<FocusOut>', lambda ev: top.destroy() if str(ev.widget) == str(top) else None)
        self.mat_tree.bind('<Button-1>', lambda ev: close_popup(ev), add='+')'''

if old_menu in text:
    text = text.replace(old_menu, new_menu)
else:
    print("WARNING: Could not find old menu logic to replace.")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Premium gear and Toplevel menu applied successfully!")
