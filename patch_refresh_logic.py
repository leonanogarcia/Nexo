import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Fix refresh_recipes
text = re.sub(
    r"with db\(\) as c:rows=c\.execute\('SELECT id,code,name,yield_qty,yield_unit FROM base_recipes WHERE COALESCE\(active,1\)=1 AND COALESCE\(archived,0\)=0 ORDER BY name'\)\.fetchall\(\)\n\s*for r in rows:",
    r"""query = '%'+self.rec_search.get().strip()+'%' if hasattr(self,'rec_search') else '%'
        status_filter = self.rec_status.get() if hasattr(self, 'rec_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        
        with db() as c:rows=c.execute(f'SELECT id,code,name,yield_qty,yield_unit,COALESCE(active,1) as active FROM base_recipes WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()
        for r in rows:
            is_active = r['active']""",
    text
)

# Add overlay redraw to refresh_recipes
text = re.sub(
    r"(self\._reset_checked\(self\.rec_tree\))",
    r"\1\n        if hasattr(self, 'rec_icon_ov'): self.rec_icon_ov._redraw()",
    text
)

# Fix refresh_products
text = re.sub(
    r"with db\(\) as c:rows=c\.execute\('SELECT id,code,name,weight,price FROM products WHERE COALESCE\(active,1\)=1 AND COALESCE\(archived,0\)=0 ORDER BY name'\)\.fetchall\(\)\n\s*for r in rows:",
    r"""query = '%'+self.prod_search.get().strip()+'%' if hasattr(self,'prod_search') else '%'
        status_filter = self.prod_status.get() if hasattr(self, 'prod_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        
        with db() as c:rows=c.execute(f'SELECT id,code,name,weight,price,COALESCE(active,1) as active FROM products WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()
        for r in rows:
            is_active = r['active']""",
    text
)

# Add overlay redraw to refresh_products
text = re.sub(
    r"(self\._reset_checked\(self\.prod_tree\))",
    r"\1\n        if hasattr(self, 'prod_icon_ov'): self.prod_icon_ov._redraw()",
    text
)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched methods!")
