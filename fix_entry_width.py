import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Make sure RoundedEntry enforces its width and height properly
new_init = """    def __init__(self,parent,textvariable,width=28,height=40,placeholder='Pesquisar',**kwargs):
        super().__init__(parent,bg=parent.cget('bg'),bd=0,highlightthickness=0,width=width*8,height=height,**kwargs)
        self.pack_propagate(False); self.grid_propagate(False)
        self.config(width=width*8, height=height)
        self._bg='#FFFFFF'; self._line='#DCE5F1'; self._placeholder=placeholder
        self._canvas=tk.Canvas(self,bg=self.cget('bg'),bd=0,highlightthickness=0); self._canvas.place(relwidth=1,relheight=1)
        self.entry=tk.Entry(self,textvariable=textvariable,bg=self._bg,fg='#18223A',insertbackground='#18223A',relief='flat',bd=0,highlightthickness=0,font=('Segoe UI',10))
        self.entry.place(relx=.115,rely=.5,anchor='w',relwidth=.82,relheight=.56)"""

code = re.sub(r"    def __init__\(self,parent,textvariable.*?relheight=\.56\)", new_init, code, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
