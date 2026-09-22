import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix mat_tree columns
old_mat = "self.mat_tree.column(k,width=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date','status') else 'w',stretch=(k=='name'))"
new_mat = "self.mat_tree.column(k,width=w,minwidth=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date','status') else 'w',stretch=(k=='name'))"
code = code.replace(old_mat, new_mat)

# Fix rec_tree columns
old_rec = "self.rec_tree.column(k,width=w,anchor='center' if k in ('yield','unit','cost') else 'w',stretch=(k=='name'))"
new_rec = "self.rec_tree.column(k,width=w,minwidth=w,anchor='center' if k in ('yield','unit','cost') else 'w',stretch=(k=='name'))"
code = code.replace(old_rec, new_rec)

# Fix prod_tree columns
old_prod = "self.prod_tree.column(k,width=w,anchor='center' if k in ('weight','cost','price','margin') else 'w',stretch=(k=='name'))"
new_prod = "self.prod_tree.column(k,width=w,minwidth=w,anchor='center' if k in ('weight','cost','price','margin') else 'w',stretch=(k=='name'))"
code = code.replace(old_prod, new_prod)

# Also fix the vertical scrollbar issue for treeviews. If vertical scrollbar is needed, it's ttk.Scrollbar(..., orient='vertical').
# The user said "todos os campos tem q ser visivel para qualquer tamanho de janela". That's achieved by minwidth.

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
