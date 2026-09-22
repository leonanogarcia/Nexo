import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Restore ReferenceSidebar to the exact original from temp_extract
new_sidebar = """class ReferenceSidebar(tk.Canvas):
    \"\"\"Sidebar flutuante em formato de cápsula, reproduzindo a referência visual.\"\"\"
    def __init__(self, parent, command, app_bg='#F4F7FC', dark_theme=False, **kwargs):
        super().__init__(parent, bg=app_bg, bd=0, highlightthickness=0, cursor='arrow', **kwargs)
        self._command=command; self._app_bg=app_bg; self._dark=dark_theme; self._active='Geral'; self._hover=None
        self._image_refs={}; self._button_items={}; self._tooltip_win=None
        self._asset_slug={'Geral':'home','Cadastro':'cadastro','Receitas':'receitas','Produtos':'produtos','Configurações':'settings'}
        self._labels={'Geral':'Início','Cadastro':'Cadastro','Receitas':'Receitas','Produtos':'Produtos','Configurações':'Configurações'}
        self.bind('<Configure>', lambda e:self._redraw())
        self.bind('<Motion>', self._on_motion); self.bind('<Leave>', self._on_leave); self.bind('<Button-1>', self._on_click)
        self._load_assets()

    def _load_photo(self, filename):
        import pathlib
        UI_ASSETS = pathlib.Path(__file__).parent / 'ui_assets'
        p=UI_ASSETS/filename
        try:
            from PIL import Image, ImageTk
            im=Image.open(p).convert('RGBA')
            if filename in ('home.png','cadastro.png','receitas.png','produtos.png','settings.png'):
                max_side=42
                scale=min(max_side/im.width,max_side/im.height,1.0)
                if scale < 1.0:
                    im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.Resampling.LANCZOS)
            img=ImageTk.PhotoImage(im); self._image_refs[filename]=img; return img
        except Exception:
            return None

    def _load_assets(self):
        self._buttons={k:self._load_photo(f'{slug}.png') for k,slug in self._asset_slug.items()}

    def _rounded(self, x,y,w,h,r,fill,outline='',width=0,tag='shape'):
        self.create_rectangle(x+r,y,x+w-r,y+h,fill=fill,outline='',tags=tag)
        self.create_rectangle(x,y+r,x+w,y+h-r,fill=fill,outline='',tags=tag)
        for bx,by,start in ((x,y,90),(x+w-2*r,y,0),(x,y+h-2*r,180),(x+w-2*r,y+h-2*r,270)):
            self.create_arc(bx,by,bx+2*r,by+2*r,start=start,extent=90,fill=fill,outline=fill,tags=tag)
        if outline:
            self.create_line(x+r,y,x+w-r,y,fill=outline,width=width,tags=tag)
            self.create_line(x+r,y+h,x+w-r,y+h,fill=outline,width=width,tags=tag)
            self.create_line(x,y+r,x,y+h-r,fill=outline,width=width,tags=tag)
            self.create_line(x+w,y+r,x+w,y+h-r,fill=outline,width=width,tags=tag)

    def _redraw(self):
        self.delete('all')
        W=self.winfo_width(); H=self.winfo_height()
        if W<10 or H<10: return
        side_w=min(84, max(78, int(W*0.064))); x=(W-side_w)/2 if W<=150 else (29 if W>=600 else 8)
        y=145 if H>=700 else 130
        bottom=min(H-42, y+580)
        h=max(300,bottom-y); r=side_w/2
        sidebar='#111C30' if not self._dark else '#F28C28'
        shadow='#D8E1EE' if not self._dark else '#0A0A0A'
        outline='#A9BFE0' if not self._dark else '#F6A24B'
        self._rounded(x+2,y+4,side_w,h,r,shadow,tag='shadow')
        self._rounded(x,y,side_w,h,r,sidebar,outline=outline,width=1,tag='sidebar')
        centers=[y+70,y+180,y+290,y+400,y+510]
        if h > 540:
            spacing = (h - 130) / 4
            centers = [y+65 + i*spacing for i in range(5)]
            
        for key,cy in zip(self._asset_slug.keys(),centers):
            if key==self._active:
                self._rounded(x+14,cy-30,side_w-28,60,20,'#304763' if not self._dark else '#F6A45A',tag='selection')
            elif key==self._hover:
                self._rounded(x+14,cy-30,side_w-28,60,20,'#1E2E4A' if not self._dark else '#DF7D1D',tag='hover')
            img=self._buttons.get(key)
            if img:
                item=self.create_image(x+side_w/2,cy,image=img,anchor='center',tags=('nav',key))
                self._button_items[key]=item

    def _on_motion(self, event):
        W=self.winfo_width(); side_w=min(84, max(78, int(W*0.064))); x=(W-side_w)/2 if W<=150 else (29 if W>=600 else 8)
        hover_key = None
        for key in self._asset_slug.keys():
            items = self.find_withtag(key)
            if items:
                bbox = self.bbox(items[0])
                if bbox and bbox[0]-15 <= event.x <= bbox[2]+15 and bbox[1]-15 <= event.y <= bbox[3]+15:
                    hover_key = key
                    break
        if hover_key != self._hover:
            self._hover = hover_key
            self._redraw()
            self.config(cursor='hand2' if self._hover else 'arrow')

    def _on_leave(self, event):
        if self._hover:
            self._hover = None
            self._redraw()
            self.config(cursor='arrow')

    def _on_click(self, event):
        if self._hover and self._hover != self._active:
            self._active = self._hover
            self._redraw()
            if self._command: self._command(self._hover)

    def set_active(self, key):
        if key in self._asset_slug and key != self._active:
            self._active = key
            self._redraw()

    def set_brand(self, text): pass
    def set_theme(self, dark, bg): pass"""

code = re.sub(r"class ReferenceSidebar\(tk\.Canvas\):.*?    def set_theme\(self, dark, bg\):.*?        pass", new_sidebar, code, flags=re.DOTALL)

# 2. Fix RoundedEntry placeholder bug
code = re.sub(
    r"show=\(not self\._var\.get\(\)\) and not self\.entry\.focus_get\(\)",
    r"show = (not self._var.get()) and (self.focus_get() != self.entry)",
    code
)

# 3. Fix PillScrollbar to be thin and gray, and not show if 0 to 1
new_scrollbar = """class PillScrollbar(tk.Canvas):
    def __init__(self, parent, tree, **kwargs):
        super().__init__(parent, height=10, bg=parent.cget('bg'), bd=0, highlightthickness=0, **kwargs)
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
                self.pack(side='bottom', fill='x', pady=(2, 6), padx=20)
        self._redraw()

    def _redraw(self, e=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10: return
        self.delete('all')
        first, last = self._pos
        if first <= 0.0 and last >= 1.0: return
        
        # Track line
        self.create_line(0, h/2, w, h/2, fill='#E5ECF5', width=4, capstyle='round')
        
        # Pill
        x1 = max(0, first * w)
        x2 = min(w, last * w)
        if x2 - x1 < 20:
            mid = (x1 + x2)/2
            x1, x2 = mid - 10, mid + 10
        self.create_line(x1+4, h/2, x2-4, h/2, fill='#A0ABB9', width=6, capstyle='round')

    def _on_press(self, e):
        w = self.winfo_width()
        first, last = self._pos
        x1 = first * w; x2 = last * w
        if x1 <= e.x <= x2:
            self._drag_data['x'] = e.x
            self._drag_data['start_pos'] = first
        else:
            new_first = max(0.0, min(1.0 - (last-first), (e.x / w) - (last-first)/2))
            self.tree.xview_moveto(new_first)

    def _on_drag(self, e):
        w = self.winfo_width(); dx = e.x - self._drag_data['x']; first, last = self._pos
        delta_pos = dx / w
        new_first = max(0.0, min(1.0 - (last-first), self._drag_data['start_pos'] + delta_pos))
        self.tree.xview_moveto(new_first)"""

code = re.sub(r"class PillScrollbar\(tk\.Canvas\):.*?        self\.tree\.xview_moveto\(new_first\)", new_scrollbar, code, flags=re.DOTALL)


# 4. Fix _styled_search_entry
new_styled_search = """    def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)
        # Search is fixed on the right, but we give it a min size by NOT propagating
        wrap.pack(side='right',padx=(14,0),fill='none',expand=False)
        return wrap"""

code = re.sub(r"    def _styled_search_entry\(self, parent, textvariable, width=28\):.*?return wrap", new_styled_search, code, flags=re.DOTALL)


with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
