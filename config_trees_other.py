with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()
import re
# Rec tree
code = re.sub(
    r"self\.rec_tree\.column\(k,width=w,anchor='w',stretch=False\)",
    "self.rec_tree.column(k,width=w,anchor='center' if k in ('yield','unit','cost') else 'w',stretch=False)",
    code
)
# Prod tree
code = re.sub(
    r"self\.prod_tree\.column\(k,width=w,anchor='w',stretch=False\)",
    "self.prod_tree.column(k,width=w,anchor='center' if k in ('weight','cost','price','margin') else 'w',stretch=False)",
    code
)
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
