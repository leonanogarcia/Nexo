with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

import re

for i, l in enumerate(lines):
    if "self.mat_tree=ttk.Treeview" in l:
        lines[i] = l.replace("'date','edit','delete'", "'date','mod_date','edit','delete'")
    if "for k,t,w in [('code'" in l:
        lines[i] = "        for k,w in [('code',100),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135)]:\n"
    if "self.mat_tree.column(k,width=w,anchor='w',stretch=False)" in l:
        lines[i] = "            self.mat_tree.column(k,width=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date') else 'w',stretch=False)\n"

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
