import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

bad_init = """        self._command=command; self._app_bg=app_bg; self._dark=dark_theme; self._active='Geral'; self._hover=None
        self._image_refs={}; self._button_items={}; self._tooltip_win=None

    def _on_motion(self, event):"""

good_init = """        self._command=command; self._app_bg=app_bg; self._dark=dark_theme; self._active='Geral'; self._hover=None
        self._image_refs={}; self._button_items={}; self._tooltip_win=None
        self._asset_slug={'Geral':'home','Cadastro':'cadastro','Receitas':'receitas','Produtos':'produtos','Configurações':'settings'}
        self._labels={'Geral':'Início','Cadastro':'Cadastro','Receitas':'Receitas','Produtos':'Produtos','Configurações':'Configurações'}
        self.bind('<Configure>', lambda e:self._redraw())
        self.bind('<Motion>', self._on_motion); self.bind('<Leave>', self._on_leave); self.bind('<Button-1>', self._on_click)
        self._load_assets()

    def _on_motion(self, event):"""

code = code.replace(bad_init, good_init)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
