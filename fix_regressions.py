import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. FIX THE "WEIRD LINE" AROUND THE TOOLBAR AND TABLE
# The RoundedPanel in _build_page_toolbar and _build_page_table_panel was drawing a thick border '#E5ECF5'
# The user HATES this line. "e essa linha nada haver em todo a tela?"
code = re.sub(
    r"shell=RoundedPanel\(parent, fill=self\.colors\['panel'\], border='#E2EAF5', radius=22, bg=self\.colors\['bg'\], height=84\)",
    r"shell=RoundedPanel(parent, fill=self.colors['panel'], border=self.colors['bg'], radius=22, bg=self.colors['bg'], height=84)",
    code
)
code = re.sub(
    r"shell=RoundedPanel\(parent, fill=self\.colors\['panel'\], border='#E5ECF5', radius=22, bg=self\.colors\['bg'\]\)",
    r"shell=RoundedPanel(parent, fill=self.colors['panel'], border=self.colors['bg'], radius=22, bg=self.colors['bg'])",
    code
)


# 2. FIX PILL SCROLLBAR (REMOVE TRACK LINE)
new_scrollbar = """class PillScrollbar(tk.Canvas):
    def __init__(self, parent, tree, **kwargs):
        super().__init__(parent, height=8, bg=parent.cget('bg'), bd=0, highlightthickness=0, **kwargs)
        self.tree = tree
        self.tree.configure(xscrollcommand=self.set_scroll)
        self.bind('<Configure>', self._redraw)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self._pos = (0.0, 1.0)
        self._drag_data = {'x': 0, 'start_pos': 0.0}

    def set_scroll(self, first, last):
        first, last = float(first), float(last)
        self._pos = (first, last)
        if first <= 0.0 and last >= 1.0:
            self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side='bottom', fill='x', pady=(0, 12), padx=20)
        self._redraw()

    def _redraw(self, e=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10: return
        self.delete('all')
        first, last = self._pos
        if first <= 0.0 and last >= 1.0: return
        
        x1 = max(0, first * w)
        x2 = min(w, last * w)
        if x2 - x1 < 20:
            mid = (x1 + x2)/2
            x1, x2 = mid - 10, mid + 10
        self.create_line(x1+4, h/2, x2-4, h/2, fill='#A0ABB9', width=6, capstyle='round')

    def _on_press(self, e):
        w = self.winfo_width(); first, last = self._pos; x1 = first * w; x2 = last * w
        if x1 <= e.x <= x2:
            self._drag_data['x'] = e.x; self._drag_data['start_pos'] = first
        else:
            new_first = max(0.0, min(1.0 - (last-first), (e.x / w) - (last-first)/2))
            self.tree.xview_moveto(new_first)

    def _on_drag(self, e):
        w = self.winfo_width(); dx = e.x - self._drag_data['x']; first, last = self._pos
        self.tree.xview_moveto(max(0.0, min(1.0 - (last-first), self._drag_data['start_pos'] + dx/w)))"""

code = re.sub(r"class PillScrollbar\(tk\.Canvas\):.*?        self\.tree\.xview_moveto\(max\(0\.0, min\(1\.0 - \(last-first\), self\._drag_data\['start_pos'\] \+ dx/w\)\)\)", new_scrollbar, code, flags=re.DOTALL)


# 3. FIX SEARCH BOX
new_entry = """class RoundedEntry(tk.Frame):
    def __init__(self,parent,textvariable,width=280,height=40,placeholder='Pesquisar',**kwargs):
        super().__init__(parent,bg=parent.cget('bg'),bd=0,highlightthickness=0,width=width,height=height,**kwargs)
        self.pack_propagate(False); self.grid_propagate(False)
        self.config(width=width, height=height)
        self._bg='#FFFFFF'; self._line='#E2EAF5'; self._placeholder=placeholder
        self._canvas=tk.Canvas(self,bg=self.cget('bg'),bd=0,highlightthickness=0); self._canvas.place(relwidth=1,relheight=1)
        self.entry=tk.Entry(self,textvariable=textvariable,bg=self._bg,fg='#18223A',insertbackground='#18223A',relief='flat',bd=0,highlightthickness=0,font=('Segoe UI',10))
        self.entry.place(x=42,rely=.5,anchor='w',relwidth=1,width=-56,relheight=.56)
        self._var=textvariable
        self._var.trace_add('write',lambda *a:self._update_placeholder())
        self.entry.bind('<FocusIn>',lambda e:self._update_placeholder())
        self.entry.bind('<FocusOut>',lambda e:self._update_placeholder())
        self.bind('<Button-1>',lambda e:self.entry.focus_set())
        self._canvas.bind('<Button-1>',lambda e:self.entry.focus_set())
        self.bind('<Configure>',lambda e:self._redraw())
        self.after_idle(self._redraw)

    def _update_placeholder(self):
        if not hasattr(self,'_placeholder_label'): return
        show = (not self._var.get()) and (self.focus_get() != self.entry)
        self._placeholder_label.place_forget() if not show else self._placeholder_label.place(x=42,rely=.5,anchor='w')

    def _redraw(self):
        w=self.winfo_width(); h=self.winfo_height(); r=h/2
        if w < 10: return
        self._canvas.delete('all')
        try:
            from PIL import Image,ImageDraw,ImageTk
            scale=4; im=Image.new('RGBA',(w*scale,h*scale),(0,0,0,0)); d=ImageDraw.Draw(im)
            d.rounded_rectangle((scale,scale,w*scale-scale,h*scale-scale),radius=r*scale,fill=self._bg,outline=self._line,width=scale)
            im=im.resize((w,h),Image.Resampling.LANCZOS); self._img=ImageTk.PhotoImage(im); self._canvas.create_image(0,0,image=self._img,anchor='nw')
        except Exception:
            pass
        self._canvas.create_oval(14, 12, 24, 22, outline='#9AA9BF', width=2)
        self._canvas.create_line(22, 20, 27, 25, fill='#9AA9BF', width=2, capstyle='round')
        if not hasattr(self,'_placeholder_label'):
            self._placeholder_label=tk.Label(self,text=self._placeholder,bg=self._bg,fg='#9AA9BF',font=('Segoe UI',10))
            self._update_placeholder()"""

code = re.sub(r"class RoundedEntry\(tk\.Frame\):.*?        self\._update_placeholder\(\)", new_entry, code, flags=re.DOTALL)


# 4. FIX THE SIDEBAR
new_sidebar = """class ReferenceSidebar(tk.Canvas):
    \"\"\"Sidebar HD com shadow perfeito via PIL\"\"\"
    def __init__(self, parent, command, app_bg='#F4F7FC', dark_theme=False, **kwargs):
        super().__init__(parent, bg=app_bg, bd=0, highlightthickness=0, cursor='arrow', **kwargs)
        self._command=command; self._app_bg=app_bg; self._dark=dark_theme; self._active='Geral'; self._hover=None
        self._image_refs={}; self._button_items={}; self._tooltip_win=None
        self._asset_slug={'Geral':'home','Cadastro':'cadastro','Receitas':'receitas','Produtos':'produtos','Configurações':'settings'}
        self.bind('<Configure>', lambda e:self._redraw())
        self.bind('<Motion>', self._on_motion); self.bind('<Leave>', self._on_leave); self.bind('<Button-1>', self._on_click)
        self._load_assets()

    def _load_photo(self, filename):
        import pathlib
        p = pathlib.Path(__file__).parent / 'ui_assets' / filename
        try:
            from PIL import Image, ImageTk
            im = Image.open(p).convert('RGBA')
            if filename in ('home.png','cadastro.png','receitas.png','produtos.png','settings.png'):
                scale = min(36/im.width, 36/im.height, 1.0)
                if scale < 1.0:
                    im = im.resize((int(im.width*scale), int(im.height*scale)), Image.Resampling.LANCZOS)
            img = ImageTk.PhotoImage(im); self._image_refs[filename] = img; return img
        except Exception: return None

    def _load_assets(self):
        self._buttons={k:self._load_photo(f'{slug}.png') for k,slug in self._asset_slug.items()}

    def _redraw(self):
        self.delete('all')
        W=self.winfo_width(); H=self.winfo_height()
        if W<10 or H<10: return
        side_w = 84
        x = 22 if W >= 600 else 8
        y = 145 if H >= 700 else 130
        bottom = min(H-42, y+580)
        h = max(300, bottom-y)
        
        try:
            from PIL import Image, ImageDraw, ImageTk, ImageFilter
            scale = 2
            im = Image.new('RGBA', ((side_w + 40)*scale, (h + 40)*scale), (0,0,0,0))
            d = ImageDraw.Draw(im)
            
            # Shadow
            if not self._dark:
                d.rounded_rectangle((16*scale, 20*scale, (side_w+16)*scale, (h+20)*scale), radius=(side_w/2)*scale, fill='#D4DCE8')
                im = im.filter(ImageFilter.GaussianBlur(6))
                d = ImageDraw.Draw(im)
            
            # Main capsule
            d.rounded_rectangle((16*scale, 16*scale, (side_w+16)*scale, (h+16)*scale), radius=(side_w/2)*scale, fill='#111C30' if not self._dark else '#F28C28')
            
            im = im.resize((side_w + 40, h + 40), Image.Resampling.LANCZOS)
            self._bg_img = ImageTk.PhotoImage(im)
            self.create_image(x-16, y-16, image=self._bg_img, anchor='nw')
        except Exception:
            self.create_rectangle(x, y, x+side_w, y+h, fill='#111C30', outline='')

        centers=[y+70,y+180,y+290,y+400,y+510]
        if h > 540:
            spacing = (h - 130) / 4
            centers = [y+65 + i*spacing for i in range(5)]
            
        for key, cy in zip(self._asset_slug.keys(), centers):
            if key == self._active or key == self._hover:
                try:
                    from PIL import Image, ImageDraw, ImageTk
                    scale = 2
                    tile = Image.new('RGBA', (56*scale, 56*scale), (0,0,0,0))
                    td = ImageDraw.Draw(tile)
                    fill_c = '#304763' if key == self._active else '#1E2E4A'
                    td.rounded_rectangle((0,0,56*scale-1,56*scale-1), radius=16*scale, fill=fill_c)
                    tile = tile.resize((56, 56), Image.Resampling.LANCZOS)
                    self._tile_cache = getattr(self, '_tile_cache', {})
                    self._tile_cache[key] = ImageTk.PhotoImage(tile)
                    self.create_image(x+side_w/2, cy, image=self._tile_cache[key], anchor='center')
                except Exception:
                    self.create_rectangle(x+14, cy-28, x+side_w-14, cy+28, fill='#304763')
                    
            img = self._buttons.get(key)
            if img:
                self.create_image(x+side_w/2, cy, image=img, anchor='center', tags=('nav', key))

    def _on_motion(self, event):
        W=self.winfo_width(); side_w=84; x=22 if W>=600 else 8
        hover_key = None
        for key in self._asset_slug.keys():
            items = self.find_withtag(key)
            if items:
                bbox = self.bbox(items[0])
                if bbox and bbox[0]-20 <= event.x <= bbox[2]+20 and bbox[1]-20 <= event.y <= bbox[3]+20:
                    hover_key = key; break
        if hover_key != self._hover:
            self._hover = hover_key; self._redraw(); self.config(cursor='hand2' if self._hover else 'arrow')

    def _on_leave(self, event):
        if self._hover: self._hover = None; self._redraw(); self.config(cursor='arrow')

    def _on_click(self, event):
        if self._hover and self._hover != self._active:
            self._active = self._hover; self._redraw()
            if self._command: self._command(self._hover)

    def set_active(self, key):
        if key in self._asset_slug and key != self._active:
            self._active = key; self._redraw()

    def set_brand(self, text): pass
    def set_theme(self, dark, bg): pass"""

code = re.sub(r"class ReferenceSidebar\(tk\.Canvas\):.*?    def set_theme\(self, dark, bg\):.*?        pass", new_sidebar, code, flags=re.DOTALL)


# 5. Fix _styled_search_entry
# The user wants it to look proper and expand, NOT just be fixed width without expanding.
# The user: "não falei q pesquisar é fixo no canto direito? lista suspesa de ativo tinha q estar em uma capsula cade o toolbar para eu arrumar a dimensão da coluna?"
# If they said "fixed on the right", we pack side='right'. But let's set width=280!
new_styled_search = """    def _styled_search_entry(self, parent, textvariable, width=280):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)
        wrap.pack(side='right',padx=(14,0),fill='none',expand=False)
        return wrap"""

code = re.sub(r"    def _styled_search_entry\(self, parent, textvariable, width=280\):.*?return wrap", new_styled_search, code, flags=re.DOTALL)


with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
