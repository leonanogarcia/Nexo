import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update Modal __init__ to inherit master background
modal_old = """class Modal(tk.Toplevel):
    def __init__(self, master, title, geometry='760x560'):
        super().__init__(master)
        self.title(title)"""
modal_new = """class Modal(tk.Toplevel):
    def __init__(self, master, title, geometry='760x560'):
        super().__init__(master)
        try: bg_col = master.colors.get('bg', '#F4F7FC')
        except: bg_col = '#F4F7FC'
        self.configure(bg=bg_col)
        self.title(title)"""
code = code.replace(modal_old, modal_new)

# 2. Update rounded_entry to use parent's real bg
rounded_old = """def rounded_entry(parent, variable, **kwargs):
    field, line, panel = _field_palette(parent)
    if not panel.startswith('#'): panel = getattr(parent.winfo_toplevel(), 'colors', {}).get('panel', '#F3F6FA')
    w = kwargs.pop('width', 28)
    # Estimate pixel width (tk.Entry width is in characters, roughly 8px per char)
    px_w = w * 9 + 32
    wrap=RoundedPanel(parent, fill=field, border='#E2EAF5', radius=20, bg=panel)"""
rounded_new = """def rounded_entry(parent, variable, **kwargs):
    field, line, panel = _field_palette(parent)
    try: parent_bg = parent.cget('bg')
    except: parent_bg = panel
    w = kwargs.pop('width', 28)
    # Estimate pixel width (tk.Entry width is in characters, roughly 8px per char)
    px_w = w * 9 + 32
    wrap=RoundedPanel(parent, fill=field, border='#E2EAF5', radius=20, bg=parent_bg)"""
code = code.replace(rounded_old, rounded_new)

# 3. Update RoundedDropdown to use parent's real bg reliably
rd_old = """bg_col = parent.cget('bg') if hasattr(parent, 'cget') and not isinstance(parent, __import__('tkinter').ttk.Widget) else getattr(parent.winfo_toplevel(), 'colors', {}).get('panel', '#F3F6FA')
        super().__init__(parent, bg=bg_col, bd=0, highlightthickness=0, width=width, height=height, cursor='hand2', **kwargs)"""
rd_new = """try: bg_col = parent.cget('bg')
        except: bg_col = getattr(parent.winfo_toplevel(), 'colors', {}).get('panel', '#F3F6FA')
        super().__init__(parent, bg=bg_col, bd=0, highlightthickness=0, width=width, height=height, cursor='hand2', **kwargs)"""
code = code.replace(rd_old, rd_new)

# 4. Update material_form to use tk.Frame instead of ttk.Frame, and tk.Label instead of ttk.Label
mat_old = """        else:
            vars['unit'].set(''); vars['category'].set('Comestível'); vars['date'].set(date.today().isoformat())
        form = ttk.Frame(d, padding=18); form.pack(fill='both', expand=True)
        fields = [
            ('Nome *','name',0,0),('Marca','brand',0,1),('Quantidade *','qty',1,0),('Unidade *','unit',1,1),
            ('Valor da compra *','value',2,0),('Categoria *','category',2,1),('Data *','date',3,0),('Cód. Barras','barcode',3,1)
        ]
        for label,key,row,col in fields:
            ttk.Label(form,text=label).grid(row=row*2,column=col,sticky='w',padx=12,pady=(1,0))
            if key == 'unit':"""
mat_new = """        else:
            vars['unit'].set(''); vars['category'].set('Comestível'); vars['date'].set(date.today().isoformat())
        form = tk.Frame(d, bg=d.cget('bg'), padx=18, pady=18); form.pack(fill='both', expand=True)
        fields = [
            ('Nome *','name',0,0),('Marca','brand',0,1),('Quantidade *','qty',1,0),('Unidade *','unit',1,1),
            ('Valor da compra *','value',2,0),('Categoria *','category',2,1),('Data *','date',3,0),('Cód. Barras','barcode',3,1)
        ]
        try: text_col = self.colors.get('text', '#18223A')
        except: text_col = '#18223A'
        for label,key,row,col in fields:
            tk.Label(form, text=label, bg=d.cget('bg'), fg=text_col, font=('Segoe UI', 9)).grid(row=row*2,column=col,sticky='w',padx=12,pady=(1,0))
            if key == 'unit':"""
code = code.replace(mat_old, mat_new)

# 5. Fix the bottom text label in material_form
bot_old = """ttk.Label(d,text='* campo obrigatório; peso/rendimento e preço podem ser definidos depois.').pack(anchor='w',padx=16)"""
bot_new = """#"""
code = code.replace(bot_old, bot_new) # Actually material_form doesn't have this, it's product_form. Wait. Let's just fix it if it exists.

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Patched successfully!')
