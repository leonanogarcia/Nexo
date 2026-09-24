import re

with open('main.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Fix encoding corruption in recipe validations
text = text.replace("if '' not in material_var.get():", "if ' — ' not in material_var.get():")
text = text.replace("if '' not in material.get():", "if ' — ' not in material.get():")

text = text.replace("if '?' not in material_var.get():", "if ' — ' not in material_var.get():")
text = text.replace("if '?' not in material.get():", "if ' — ' not in material.get():")

text = text.replace("if '?\"' not in material_var.get():", "if ' — ' not in material_var.get():")

# Generic regex for this specific line since it got mangled differently
text = re.sub(r"if '[^']*' not in material_var\.get\(\): raise ValueError\('Selecione um Insumo", 
              r"if ' — ' not in material_var.get(): raise ValueError('Selecione um Insumo", text)
text = re.sub(r"if '[^']*' not in material\.get\(\):raise ValueError\('Selecione um Insumo", 
              r"if ' — ' not in material.get():raise ValueError('Selecione um Insumo", text)

# Fix emojis
text = re.sub(r"FlatEmojiButton\(left,'[^']*',edit_item\)", "FlatEmojiButton(left,'✏️',edit_item)", text)
text = re.sub(r"FlatEmojiButton\(left,'[^']*',delete_item\)", "FlatEmojiButton(left,'🗑️',delete_item)", text)

text = re.sub(r"edit_item_btn=ttk\.Button\(box,text='[^']*',", "edit_item_btn=ttk.Button(box,text='✏️',", text)
text = re.sub(r"delete_item_btn=ttk\.Button\(box,text='[^']*',", "delete_item_btn=ttk.Button(box,text='🗑️',", text)

# Fix title version
text = text.replace('v0.7.20', 'v0.7.22')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed encodings and version string.')
