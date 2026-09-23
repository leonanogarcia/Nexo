import re

with open('main.py', 'rb') as f:
    content = f.read().decode('utf-8')

# Fix _draw_status
old_draw_status = """        def _draw_status(text):
            self.mat_status_wrap.delete('all')
            w = 110; h = 40
            self.mat_status_wrap.create_arc(2, 2, 38, 38, start=90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='pieslice')
            self.mat_status_wrap.create_arc(2, 2, 38, 38, start=90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='arc')
            self.mat_status_wrap.create_arc(w-38, 2, w-2, 38, start=-90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='pieslice')
            self.mat_status_wrap.create_arc(w-38, 2, w-2, 38, start=-90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='arc')
            self.mat_status_wrap.create_rectangle(20, 2, w-20, 38, fill='#FFFFFF', outline='')
            self.mat_status_wrap.create_line(20, 2, w-20, 2, fill='#E2EAF5')
            self.mat_status_wrap.create_line(20, 38, w-20, 38, fill='#E2EAF5')
            self.mat_status_wrap.create_text(45, 20, text=text, fill=self.colors['text'], font=('Segoe UI', 10, 'bold'), anchor='center')
            self.mat_status_wrap.create_text(90, 20, text='▼', fill=self.colors['muted'], font=('Segoe UI', 8), anchor='center')"""

new_draw_status = """        def _draw_status(text):
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
            self.mat_status_wrap.create_text(90, 20, text='▼', fill=self.colors['muted'], font=('Segoe UI', 8), anchor='center')"""

content = content.replace(old_draw_status, new_draw_status)

# Now fix the packing order.
# The search bar should be packed FIRST so it goes to the rightmost edge, and then status_wrap is packed after.
# In `cadastro(self, f):`, `mat_search` is created, then `mat_status_wrap`, then `_open_status_menu`, then `self.mat_search_wrap=self._styled_search_entry(...)`

old_pack = """        self.mat_status_wrap.bind('<Button-1>', _open_status_menu)
        
        self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,280)"""

new_pack = """        self.mat_status_wrap.bind('<Button-1>', _open_status_menu)"""

content = content.replace(old_pack, new_pack)

# Now insert the search entry pack BEFORE mat_status_wrap
old_create_status = """        self.mat_status = tk.StringVar(value='Ativos')
        self.mat_status_wrap = tk.Canvas(bar, bg=self.colors['panel'], bd=0, highlightthickness=0, width=110, height=40, cursor='hand2')
        self.mat_status_wrap.pack(side='right', padx=14)"""

new_create_status = """        self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,280)
        self.mat_status = tk.StringVar(value='Ativos')
        self.mat_status_wrap = tk.Canvas(bar, bg=self.colors['panel'], bd=0, highlightthickness=0, width=110, height=40, cursor='hand2')
        self.mat_status_wrap.pack(side='right', padx=14)"""

content = content.replace(old_create_status, new_create_status)

with open('main.py', 'wb') as f:
    f.write(content.encode('utf-8'))
print('Patched search layout')
