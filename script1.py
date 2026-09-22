import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Capsule Dropdown for Status Filter
new_status_cb = """        # Custom Capsule Filter Dropdown
        self.mat_status_wrap = tk.Canvas(bar, bg=self.colors['panel'], bd=0, highlightthickness=0, width=110, height=40, cursor='hand2')
        self.mat_status_wrap.pack(side='right', padx=14)
        def _draw_status(text):
            self.mat_status_wrap.delete('all')
            self.mat_status_wrap.create_polygon(20, 0, 90, 0, 110, 0, 110, 20, 110, 40, 90, 40, 20, 40, 0, 40, 0, 20, 0, 0, smooth=True, fill=self.colors['field'], outline='')
            self.mat_status_wrap.create_text(45, 20, text=text, fill=self.colors['text'], font=('Segoe UI', 10, 'bold'), anchor='center')
            self.mat_status_wrap.create_text(90, 20, text='▼', fill=self.colors['muted'], font=('Segoe UI', 8), anchor='center')
        
        _draw_status(self.mat_status.get())
        
        def _open_status_menu(e):
            m = tk.Menu(self.winfo_toplevel(), tearoff=0, bg=self.colors['panel'], fg=self.colors['text'], font=('Segoe UI', 10), activebackground=self.colors['accent_soft'], activeforeground=self.colors['accent'], bd=1)
            for opt in ['Ativos', 'Inativos', 'Todos']:
                m.add_command(label=opt, command=lambda o=opt: (self.mat_status.set(o), _draw_status(o)))
            m.post(e.x_root, e.y_root)
            
        self.mat_status_wrap.bind('<Button-1>', _open_status_menu)"""

code = re.sub(
    r"self\.mat_status_cb=ttk\.Combobox\(bar,textvariable=self\.mat_status,values=\['Ativos','Inativos','Todos'\],state='readonly',width=10\)\s*\n\s*self\.mat_status_cb\.pack\(side='right',padx=14\)",
    new_status_cb,
    code
)

# 2. Add 'options' column and tags to trees
def update_tree_cols(match):
    original = match.group(0)
    # Add 'options' after 'delete'
    original = original.replace("'delete')", "'delete','options')")
    original = original.replace("('delete','',46)", "('delete','',40),('options','',40)")
    original = original.replace("('edit','',46)", "('edit','',40)")
    original = original.replace("('edit','delete')", "('edit','delete','options')")
    return original

# For materials
code = re.sub(r"self\.mat_tree=ttk\.Treeview.*?\('delete','',46\)\]", update_tree_cols, code, flags=re.DOTALL)
# For recipes
code = re.sub(r"self\.rec_tree=ttk\.Treeview.*?\('delete','',46\)\]", update_tree_cols, code, flags=re.DOTALL)
# For products
code = re.sub(r"self\.prod_tree=ttk\.Treeview.*?\('delete','',46\)\]", update_tree_cols, code, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
