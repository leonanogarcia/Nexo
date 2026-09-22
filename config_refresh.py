with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "rows = c.execute('''SELECT" in l and "FROM materials" in lines[i+2]:
        lines[i] = "            rows = c.execute('''SELECT code,name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,\n"
        lines[i+1] = "                                       substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10)\n"
    if "for r in rows: self.mat_tree.insert" in l:
        lines[i] = """        for r in rows:
            r_list = list(r)
            val = r_list[5]
            val_str = f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            r_list[5] = val_str
            self.mat_tree.insert('', 'end', text='?', values=tuple(r_list)+('',''))
"""
        break

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
