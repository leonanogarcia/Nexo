import re

with open('main.py', 'rb') as f:
    content = f.read().decode('utf-8')

old_dropdown_open = """    def _open_dropdown(self):
        w = self.winfo_width()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        top.geometry(f'{w}x{len(self._opts)*36}+{x}+{y}')
        top.configure(bg='#000001')
        top.attributes('-transparentcolor', '#000001')
        
        c = tk.Canvas(top, bg='#000001', bd=0, highlightthickness=0)
        c.pack(fill='both', expand=True)
        
        try:
            from PIL import Image, ImageDraw, ImageTk
            scale = 4; tw = w*scale; th = len(self._opts)*36*scale
            im = Image.new('RGBA', (tw, th), (0,0,0,0)); d = ImageDraw.Draw(im)
            d.rounded_rectangle((0, 0, tw-1, th-1), radius=12*scale, fill='#FFFFFF', outline='#E2EAF5', width=scale)
            im = im.resize((w, len(self._opts)*36), Image.Resampling.LANCZOS)
            self._menu_bg = ImageTk.PhotoImage(im)
            c.create_image(0, 0, image=self._menu_bg, anchor='nw')
        except Exception:
            c.create_rectangle(0,0,w,len(self._opts)*36, fill='#FFFFFF', outline='#E2EAF5')

        for i, opt in enumerate(self._opts):
            oy = i*36
            hb = c.create_rectangle(2, oy+2, w-2, oy+34, fill='#FFFFFF', outline='', tags=f'opt_{i}')"""

new_dropdown_open = """    def _open_dropdown(self):
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

content = content.replace(old_dropdown_open, new_dropdown_open)

with open('main.py', 'wb') as f:
    f.write(content.encode('utf-8'))
print('Patched menu background')
