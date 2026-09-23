import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Find the RoundedDropdown._open_dropdown block
match = re.search(r'    def _open_dropdown\(self\):.*?top\.focus_set\(\)\n', text, re.DOTALL)
if match:
    old = match.group(0)
    
    new_code = """    def _open_dropdown(self):
        w = self.winfo_width()
        h_menu = len(self._opts)*36
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        top.geometry(f'{w}x{h_menu}+{x}+{y}')
        top.configure(bg='#E2EAF5')
        
        inner = tk.Frame(top, bg='#FFFFFF')
        inner.pack(fill='both', expand=True, padx=1, pady=1)
        
        c = tk.Canvas(inner, bg='#FFFFFF', bd=0, highlightthickness=0)
        c.pack(fill='both', expand=True)
        
        for i, opt in enumerate(self._opts):
            oy = i*36
            hb = c.create_rectangle(0, oy, w, oy+36, fill='#FFFFFF', outline='', tags=f'opt_{i}')
            col = '#2F67B1' if opt == self._var.get() else '#18223A'
            fnt = ('Segoe UI', 10, 'bold') if opt == self._var.get() else ('Segoe UI', 10)
            c.create_text(w/2, oy+18, text=opt, fill=col, font=fnt, anchor='center', tags=f'opt_{i}')
            
            def on_enter(e, idx=i, hb_id=hb): c.itemconfig(hb_id, fill='#F8FAFC')
            def on_leave(e, idx=i, hb_id=hb): c.itemconfig(hb_id, fill='#FFFFFF')
            def on_click(e, o=opt):
                self._var.set(o)
                root.unbind('<Button-1>', bind_id)
                top.destroy()
                
            c.tag_bind(f'opt_{i}', '<Enter>', on_enter)
            c.tag_bind(f'opt_{i}', '<Leave>', on_leave)
            c.tag_bind(f'opt_{i}', '<Button-1>', on_click)
            
        # Global click to dismiss
        root = self.winfo_toplevel()
        def check_click(e):
            # Check if click is inside the Toplevel
            if not top.winfo_exists(): return
            rx, ry = top.winfo_pointerxy()
            tx = top.winfo_rootx()
            ty = top.winfo_rooty()
            tw = top.winfo_width()
            th = top.winfo_height()
            
            # Allow click if it is inside the dropdown widget itself to close it
            btn_x = self.winfo_rootx()
            btn_y = self.winfo_rooty()
            btn_w = self.winfo_width()
            btn_h = self.winfo_height()
            
            if (tx <= rx <= tx+tw and ty <= ry <= ty+th):
                # Inside menu, let the canvas handle it
                pass
            else:
                # Outside menu! 
                try:
                    root.unbind('<Button-1>', bind_id)
                    top.destroy()
                except Exception: pass

        bind_id = root.bind('<Button-1>', check_click, add='+')
        
        def on_focus_out(e):
            if e.widget == top:
                try:
                    root.unbind('<Button-1>', bind_id)
                    top.destroy()
                except Exception: pass
                
        top.bind('<FocusOut>', on_focus_out)
        top.focus_set()
"""
    text = text.replace(old, new_code)
    
    with open('main.py', 'wb') as f:
        f.write(text.encode('utf-8'))
    print("SUCCESS")
else:
    print("Regex failed to find _open_dropdown")
