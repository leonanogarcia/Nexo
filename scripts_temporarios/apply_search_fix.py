import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update _styled_search_entry
old_search_func = """def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)"""
new_search_func = """def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=32)"""
text = text.replace(old_search_func, new_search_func)

# 2. Update RoundedEntry __init__ defaults
old_init = "def __init__(self,parent,textvariable,width=280,height=40,placeholder='Pesquisar',**kwargs):"
new_init = "def __init__(self,parent,textvariable,width=280,height=32,placeholder='Pesquisar',**kwargs):"
text = text.replace(old_init, new_init)

# 3. Update RoundedEntry _redraw (Magnifying Glass math)
old_redraw_glass = """self._canvas.create_oval(14, 12, 24, 22, outline='#9AA9BF', width=2)
        self._canvas.create_line(22, 20, 27, 25, fill='#9AA9BF', width=2, capstyle='round')"""
new_redraw_glass = """cx, cy_icon = 19, h / 2 - 3
        self._canvas.create_oval(cx-5, cy_icon-5, cx+5, cy_icon+5, outline='#9AA9BF', width=2)
        self._canvas.create_line(cx+3, cy_icon+3, cx+8, cy_icon+8, fill='#9AA9BF', width=2, capstyle='round')"""
text = text.replace(old_redraw_glass, new_redraw_glass)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Barra de pesquisa afinada com sucesso (Lupa matemática aplicada)!")
