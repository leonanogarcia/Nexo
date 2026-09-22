import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 3. Add 'inactive' tags and update overlay logic
old_mat_insert = r"self\.mat_tree\.insert\('', 'end', iid=str\(mat_id\), text='\?', values=tuple\(r_list\)\+\(status_str, '',''\)\)"
new_mat_insert = r"self.mat_tree.insert('', 'end', iid=str(mat_id), text='?', values=tuple(r_list)+(status_str, '','',''), tags=() if is_active else ('inactive',))"
code = re.sub(old_mat_insert, new_mat_insert, code)

# Let's do the same for recipes
code = re.sub(
    r"query = '%'\+self\.rec_search\.get\(\)\.strip\(\)\+'%' if hasattr\(self,'rec_search'\) else '%'\s*\n\s*with db\(\) as c:\s*\n\s*rows = c\.execute\('''SELECT\s*code,name,yield_qty,yield_unit,\s*substr\(created_at,1,10\), substr\(COALESCE\(updated_at,created_at\),1,10\), id\s*FROM base_recipes WHERE name LIKE \? OR code LIKE \? ORDER BY name''', \(query,query\)\)\.fetchall\(\)",
    r"query = '%'+self.rec_search.get().strip()+'%' if hasattr(self,'rec_search') else '%'\n        with db() as c:\n            rows = c.execute('''SELECT code,name,yield_qty,yield_unit, substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10), id, COALESCE(active,1) FROM base_recipes WHERE name LIKE ? OR code LIKE ? ORDER BY name''', (query,query)).fetchall()",
    code
)
code = re.sub(
    r"rec_id = r_list\.pop\(6\)\s*\n\s*self\.rec_tree\.insert\('', 'end', iid=str\(rec_id\), text='\?', values=tuple\(r_list\)\+\('',''\)\)",
    r"is_active = r_list.pop(7)\n            rec_id = r_list.pop(6)\n            self.rec_tree.insert('', 'end', iid=str(rec_id), text='?', values=tuple(r_list)+('','',''), tags=() if is_active else ('inactive',))",
    code
)

# And products
code = re.sub(
    r"query = '%'\+self\.prod_search\.get\(\)\.strip\(\)\+'%' if hasattr\(self,'prod_search'\) else '%'\s*\n\s*with db\(\) as c:\s*\n\s*rows = c\.execute\('''SELECT\s*code,name,weight_qty,weight_unit,sale_price,\s*substr\(created_at,1,10\), substr\(COALESCE\(updated_at,created_at\),1,10\), id\s*FROM products WHERE name LIKE \? OR code LIKE \? ORDER BY name''', \(query,query\)\)\.fetchall\(\)",
    r"query = '%'+self.prod_search.get().strip()+'%' if hasattr(self,'prod_search') else '%'\n        with db() as c:\n            rows = c.execute('''SELECT code,name,weight_qty,weight_unit,sale_price, substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10), id, COALESCE(active,1) FROM products WHERE name LIKE ? OR code LIKE ? ORDER BY name''', (query,query)).fetchall()",
    code
)
code = re.sub(
    r"prod_id = r_list\.pop\(7\)\s*\n\s*self\.prod_tree\.insert\('', 'end', iid=str\(prod_id\), text='\?', values=tuple\(r_list\)\+\('',''\)\)",
    r"is_active = r_list.pop(8)\n            prod_id = r_list.pop(7)\n            self.prod_tree.insert('', 'end', iid=str(prod_id), text='?', values=tuple(r_list)+('','',''), tags=() if is_active else ('inactive',))",
    code
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
