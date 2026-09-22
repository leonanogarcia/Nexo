import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_sidebar = """class ReferenceSidebar(tk.Canvas):
    \"\"\"Sidebar utilizando os assets de botão perfeitamente renderizados pelo usuário.\"\"\"
    def __init__(self, parent, command, app_bg='#F4F7FC', dark_theme=False, **kwargs):
        super().__init__(parent, bg=app_bg, bd=0, highlightthickness=0, cursor='arrow', **kwargs)
        self._command=command; self._app_bg=app_bg; self._dark=dark_theme; self._active='Geral'; self._hover=None
        self._image_refs={}; self._button_items={}
        self._asset_slug={'Geral':'home','Cadastro':'cadastro','Receitas':'receitas','Produtos':'produtos','Configurações':'settings'}
        self.bind('<Configure>', lambda e:self._redraw())
        self.bind('<Motion>', self._on_motion); self.bind('<Leave>', self._on_leave); self.bind('<Button-1>', self._on_click)
        self._load_assets()

    def _load_photo(self, filename):
        p = UI_ASSETS / filename
        try:
            from PIL import Image, ImageTk
            im = Image.open(p).convert('RGBA')
            img = ImageTk.PhotoImage(im); self._image_refs[filename] = img; return img
        except Exception: return None

    def _load_assets(self):
        self._states = {}
        for k, slug in self._asset_slug.items():
            self._states[k] = {
                'normal': self._load_photo(f'btn_{slug}_normal.png'),
                'hover': self._load_photo(f'btn_{slug}_hover.png'),
                'active': self._load_photo(f'btn_{slug}_active.png')
            }

    def _redraw(self):
        self.delete('all')
        W=self.winfo_width(); H=self.winfo_height()
        if W<10 or H<10: return
        side_w=min(84, max(78, int(W*0.064))); x=(W-side_w)/2 if W<=150 else (29 if W>=600 else 8)
        y=145 if H>=700 else 130; bottom=min(H-42, y+580)
        h=max(300,bottom-y); r=side_w/2
        
        # Draw background capsule
        self.create_polygon(
            x+r, y, x+side_w-r, y,
            x+side_w, y+r, x+side_w, y+h-r,
            x+side_w-r, y+h, x+r, y+h,
            x, y+h-r, x, y+r,
            smooth=True, fill='#111C30', outline='#111C30', tag='sidebar'
        )

        centers=[y+70,y+180,y+290,y+400,y+510]
        if h > 540:
            spacing = (h - 130) / 4
            centers = [y+65 + i*spacing for i in range(5)]
            
        for key, cy in zip(self._asset_slug.keys(), centers):
            state = 'active' if key == self._active else ('hover' if key == self._hover else 'normal')
            img = self._states.get(key, {}).get(state)
            if img:
                self.create_image(x+side_w/2, cy, image=img, anchor='center', tags=('nav', key))

    def _on_motion(self, event):
        W = self.winfo_width(); side_w=min(84, max(78, int(W*0.064))); x=(W-side_w)/2 if W<=150 else (29 if W>=600 else 8)
        hover_key = None
        for key in self._asset_slug.keys():
            items = self.find_withtag(key)
            if items:
                bbox = self.bbox(items[0])
                if bbox and bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]:
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
    def set_theme(self, dark, bg): pass
"""

code = re.sub(r"class ReferenceSidebar\(tk\.Canvas\):.*?    def set_theme\(self, dark, bg\):.*?        pass", new_sidebar, code, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
