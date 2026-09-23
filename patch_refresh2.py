import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Fix refresh_recipes
old_rr = "with db() as c:rows=c.execute('SELECT id,code,name,yield_qty,yield_unit FROM base_recipes WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0 ORDER BY name').fetchall()"
new_rr = """query = '%'+self.rec_search.get().strip()+'%' if hasattr(self,'rec_search') else '%'
        status_filter = self.rec_status.get() if hasattr(self, 'rec_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        with db() as c:rows=c.execute(f'SELECT id,code,name,yield_qty,yield_unit,COALESCE(active,1) as active FROM base_recipes WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()"""
text = text.replace(old_rr, new_rr)

# Add is_active to recipes
text = text.replace(
    "name_disp = f\"⚠️ {r['name']}\" if has_arc else r['name']",
    "name_disp = f\"⚠️ {r['name']}\" if has_arc else r['name']\n            is_active = r['active']"
)


# Fix refresh_products
old_rp = "with db() as c:rows=c.execute('SELECT id,code,name,weight_qty,weight_unit,sale_price FROM products WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0 ORDER BY name').fetchall()"
new_rp = """query = '%'+self.prod_search.get().strip()+'%' if hasattr(self,'prod_search') else '%'
        status_filter = self.prod_status.get() if hasattr(self, 'prod_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1 AND COALESCE(archived,0)=0" if status_filter == 'Ativos' else ("COALESCE(active,1)=0 AND COALESCE(archived,0)=0" if status_filter == 'Inativos' else "COALESCE(archived,0)=0")
        with db() as c:rows=c.execute(f'SELECT id,code,name,weight_qty,weight_unit,sale_price,COALESCE(active,1) as active FROM products WHERE {status_cond} AND (name LIKE ? OR code LIKE ?) ORDER BY name', (query, query)).fetchall()"""
text = text.replace(old_rp, new_rp)

# Add is_active to products
text = text.replace(
    "margin=((r['sale_price']-cost)/r['sale_price']*100) if r['sale_price'] else None",
    "margin=((r['sale_price']-cost)/r['sale_price']*100) if r['sale_price'] else None\n            is_active = r['active']"
)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Fixed refresh DB queries")
