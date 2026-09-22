with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_rec = False
in_prod = False

for i, l in enumerate(lines):
    if "self.rec_tree=ttk.Treeview" in l:
        in_rec = True
    elif "self.prod_tree=ttk.Treeview" in l:
        in_prod = True
        in_rec = False
        
    if in_rec and "for k,w in [('code',100),('name',220)," in l:
        lines[i] = "        for k, w in [('code',95),('name',280),('yield',120),('unit',65),('cost',120)]:\n"
        in_rec = False
        
    if in_prod and "for k,w in [('code',100),('name',220)," in l:
        lines[i] = "        for k, w in [('code',95),('name',280),('weight',140),('cost',120),('price',120),('margin',100)]:\n"
        in_prod = False

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
