import re

with open('main.py', 'rb') as f:
    content = f.read().decode('utf-8')

old_dropdown_open = """    def _open_dropdown(self):
        w = self.winfo_width()
        h_menu = len(self._opts)*36
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        top.geometry(f'{w}x{h_menu}+{x}+{y}')
        
        try:
            top.configure(bg='#000001')
            top.wm_attributes('-transparentcolor', '#000001')
            transparent_bg = '#000001'
        except Exception:
            transparent_bg = '#FFFFFF'
            top.configure(bg='#FFFFFF')
        
        c = tk.Canvas(top, bg=transparent_bg, bd=0, highlightthickness=0)
        c.pack(fill='both', expand=True)
        
        r = 8
        bg = '#FFFFFF'
        border = '#E2EAF5'
        
        # Draw native Tkinter rounded corners (hard aliasing prevents black halo with transparentcolor)
        c.create_rectangle(r, 0, w-r, h_menu, fill=bg, outline='')
        c.create_rectangle(0, r, w, h_menu-r, fill=bg, outline='')
        c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=bg, outline='')
        c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=bg, outline='')
        c.create_arc(0, h_menu-2*r, 2*r, h_menu, start=180, extent=90, fill=bg, outline='')
        c.create_arc(w-2*r, h_menu-2*r, w, h_menu, start=270, extent=90, fill=bg, outline='')
        
        c.create_line(r, 0, w-r, 0, fill=border)
        c.create_line(r, h_menu-1, w-r, h_menu-1, fill=border)
        c.create_line(0, r, 0, h_menu-r, fill=border)
        c.create_line(w-1, r, w-1, h_menu-r, fill=border)
        c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, style='arc', outline=border)
        c.create_arc(w-2*r-1, 0, w-1, 2*r, start=0, extent=90, style='arc', outline=border)
        c.create_arc(0, h_menu-2*r-1, 2*r, h_menu-1, start=180, extent=90, style='arc', outline=border)
        c.create_arc(w-2*r-1, h_menu-2*r-1, w-1, h_menu-1, start=270, extent=90, style='arc', outline=border)

        for i, opt in enumerate(self._opts):
            oy = i*36
            # Hitbox slightly padded so it doesn't overlap the border
            hb = c.create_rectangle(1, oy, w-1, oy+36, fill='#FFFFFF', outline='', tags=f'opt_{i}')"""

new_dropdown_open = """    def _open_dropdown(self):
        w = self.winfo_width()
        h_menu = len(self._opts)*36
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        top.geometry(f'{w}x{h_menu}+{x}+{y}')
        top.configure(bg='#E2EAF5') # Border color as background
        
        # Inner frame to create a 1px border effect
        inner = tk.Frame(top, bg='#FFFFFF')
        inner.pack(fill='both', expand=True, padx=1, pady=1)
        
        c = tk.Canvas(inner, bg='#FFFFFF', bd=0, highlightthickness=0)
        c.pack(fill='both', expand=True)
        
        for i, opt in enumerate(self._opts):
            oy = i*36
            hb = c.create_rectangle(0, oy, w, oy+36, fill='#FFFFFF', outline='', tags=f'opt_{i}')"""

content = content.replace(old_dropdown_open, new_dropdown_open)

with open('main.py', 'wb') as f:
    f.write(content.encode('utf-8'))
print('Patched dropdown to square')
