import re

with open('main.py', 'rb') as f:
    content = f.read().decode('utf-8')

# Let's define RoundedDropdown component at the top
dropdown_class = """
class RoundedDropdown(tk.Frame):
    def __init__(self, parent, textvariable, options, width=120, height=40, **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), bd=0, highlightthickness=0, width=width, height=height, cursor='hand2', **kwargs)
        self.pack_propagate(False); self.grid_propagate(False)
        self.config(width=width, height=height)
        self._var = textvariable
        self._options = options
        self._bg = '#FFFFFF'
        self._hover = '#F8FAFC'
        self._line = '#E2EAF5'
        self._fg = '#18223A'
        self._canvas = tk.Canvas(self, bg=self.cget('bg'), bd=0, highlightthickness=0)
        self._canvas.place(relwidth=1, relheight=1)
        self._is_hover = False
        self._canvas.bind('<Enter>', lambda e: self._on_enter())
        self._canvas.bind('<Leave>', lambda e: self._on_leave())
        self._canvas.bind('<Button-1>', lambda e: self._open_dropdown())
        self._var.trace_add('write', lambda *a: self._redraw())
        self.bind('<Configure>', lambda e: self._redraw())
        self.after_idle(self._redraw)

    def _on_enter(self): self._is_hover = True; self._redraw()
    def _on_leave(self): self._is_hover = False; self._redraw()

    def _redraw(self):
        w = max(2, self.winfo_width()); h = max(2, self.winfo_height()); r = h/2
        if w < 10: return
        self._canvas.delete('all')
        try:
            from PIL import Image, ImageDraw, ImageTk
            scale = 4; im = Image.new('RGBA', (w*scale, h*scale), (0,0,0,0)); d = ImageDraw.Draw(im)
            fill_col = self._hover if self._is_hover else self._bg
            d.rounded_rectangle((scale, scale, w*scale-scale, h*scale-scale), radius=r*scale, fill=fill_col, outline=self._line, width=scale)
            im = im.resize((w, h), Image.Resampling.LANCZOS); self._img = ImageTk.PhotoImage(im)
            self._canvas.create_image(0, 0, image=self._img, anchor='nw')
        except Exception: pass
        
        txt = self._var.get()
        self._canvas.create_text(w/2 - 6, h/2, text=txt, fill=self._fg, font=('Segoe UI', 10, 'bold'), anchor='center')
        # Draw chevron
        cx = w - 18; cy = h/2 - 2
        self._canvas.create_line(cx-4, cy, cx, cy+4, cx+4, cy, fill='#687796', width=2, capstyle='round', joinstyle='round')

    def _open_dropdown(self):
        w = self.winfo_width()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        top.geometry(f'{w}x{len(self._options)*36}+{x}+{y}')
        top.configure(bg='#000001')
        top.attributes('-transparentcolor', '#000001')
        
        c = tk.Canvas(top, bg='#000001', bd=0, highlightthickness=0)
        c.pack(fill='both', expand=True)
        
        try:
            from PIL import Image, ImageDraw, ImageTk
            scale = 4; tw = w*scale; th = len(self._options)*36*scale
            im = Image.new('RGBA', (tw, th), (0,0,0,0)); d = ImageDraw.Draw(im)
            d.rounded_rectangle((0, 0, tw-1, th-1), radius=12*scale, fill='#FFFFFF', outline='#E2EAF5', width=scale)
            im = im.resize((w, len(self._options)*36), Image.Resampling.LANCZOS)
            self._menu_bg = ImageTk.PhotoImage(im)
            c.create_image(0, 0, image=self._menu_bg, anchor='nw')
        except Exception:
            c.create_rectangle(0,0,w,len(self._options)*36, fill='#FFFFFF', outline='#E2EAF5')

        # Add hitboxes and text
        for i, opt in enumerate(self._options):
            oy = i*36
            # Hitbox filled with #FFFFFF so it's opaque to clicks
            hb = c.create_rectangle(2, oy+2, w-2, oy+34, fill='#FFFFFF', outline='', tags=f'opt_{i}')
            col = '#2F67B1' if opt == self._var.get() else '#18223A'
            fnt = ('Segoe UI', 10, 'bold') if opt == self._var.get() else ('Segoe UI', 10)
            txt = c.create_text(w/2, oy+18, text=opt, fill=col, font=fnt, anchor='center', tags=f'opt_{i}')
            
            def on_enter(e, idx=i, hb_id=hb): c.itemconfig(hb_id, fill='#F8FAFC')
            def on_leave(e, idx=i, hb_id=hb): c.itemconfig(hb_id, fill='#FFFFFF')
            def on_click(e, o=opt):
                self._var.set(o)
                top.destroy()
                
            c.tag_bind(f'opt_{i}', '<Enter>', on_enter)
            c.tag_bind(f'opt_{i}', '<Leave>', on_leave)
            c.tag_bind(f'opt_{i}', '<Button-1>', on_click)
            
        def close_menu(e):
            if e.widget != top and e.widget != c: top.destroy()
            
        top.bind('<FocusOut>', close_menu)
        top.focus_set()
"""

# Insert class before App
if "class App(tk.Tk):" in content:
    content = content.replace("class App(tk.Tk):", dropdown_class + "\nclass App(tk.Tk):")

# Now replace the usage in cadastro
old_status = """        self.mat_status = tk.StringVar(value='Ativos')
        self.mat_status_wrap = tk.Canvas(bar, bg=self.colors['panel'], bd=0, highlightthickness=0, width=110, height=40, cursor='hand2')
        self.mat_status_wrap.pack(side='right', padx=14)
        def _draw_status(text):
            self.mat_status_wrap.delete('all')
            w = 110; h = 40
            self.mat_status_wrap.create_arc(2, 2, 38, 38, start=90, extent=180, fill='#FFFFFF', outline='', style='chord')
            self.mat_status_wrap.create_arc(2, 2, 38, 38, start=90, extent=180, fill='', outline='#E2EAF5', style='arc')
            self.mat_status_wrap.create_arc(w-38, 2, w-2, 38, start=-90, extent=180, fill='#FFFFFF', outline='', style='chord')
            self.mat_status_wrap.create_arc(w-38, 2, w-2, 38, start=-90, extent=180, fill='', outline='#E2EAF5', style='arc')
            self.mat_status_wrap.create_rectangle(20, 2, w-20, 38, fill='#FFFFFF', outline='')
            self.mat_status_wrap.create_line(20, 2, w-20, 2, fill='#E2EAF5')
            self.mat_status_wrap.create_line(20, 38, w-20, 38, fill='#E2EAF5')
            self.mat_status_wrap.create_text(45, 20, text=text, fill=self.colors['text'], font=('Segoe UI', 10, 'bold'), anchor='center')
            self.mat_status_wrap.create_text(90, 20, text='▼', fill=self.colors['muted'], font=('Segoe UI', 8), anchor='center')
        
        _draw_status(self.mat_status.get())
        
        def _open_status_menu(e):
            m = tk.Menu(self.winfo_toplevel(), tearoff=0, bg=self.colors['panel'], fg=self.colors['text'], font=('Segoe UI', 10), activebackground=self.colors['accent_soft'], activeforeground=self.colors['accent'], bd=1)
            for opt in ['Ativos', 'Inativos', 'Todos']:
                m.add_command(label=opt, command=lambda o=opt: (self.mat_status.set(o), _draw_status(o), self.refresh_materials()))
            m.post(e.x_root, e.y_root)
            
        self.mat_status_wrap.bind('<Button-1>', _open_status_menu)"""

new_status = """        self.mat_status = tk.StringVar(value='Ativos')
        self.mat_status.trace_add('write', lambda *a: self.refresh_materials())
        self.mat_status_wrap = RoundedDropdown(bar, self.mat_status, ['Ativos', 'Inativos', 'Todos'], width=110)
        self.mat_status_wrap.pack(side='right', padx=14)"""

content = content.replace(old_status, new_status)

with open('main.py', 'wb') as f:
    f.write(content.encode('utf-8'))
print('Patched dropdown')
