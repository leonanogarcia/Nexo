import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_logic = """        with db() as c:rows=c.execute('SELECT id,code,name,yield_qty,yield_unit FROM base_recipes WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0 ORDER BY name').fetchall()
        for r in rows:
            try:cost=recipe_cost(r['id'])
            except Exception:cost=0
            
            iid=self.rec_tree.insert('','end',text='☐',values=(r['code'],r['name'],fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'✏️','🗑️'))
            with db() as c:
                comps=c.execute('SELECT m.name,bri.qty,bri.unit FROM base_recipe_items bri JOIN materials m ON m.id=bri.material_id WHERE bri.recipe_id=? ORDER BY bri.id',(r['id'],)).fetchall()
            for comp in comps:
                self.rec_tree.insert(iid,'end',text='  ',values=('',f'↳ {comp[0]}',fmt_num(comp[1]),comp[2],'-','',''))"""

new_logic = """        with db() as c:rows=c.execute('SELECT id,code,name,yield_qty,yield_unit FROM base_recipes WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0 ORDER BY name').fetchall()
        for r in rows:
            try:cost=recipe_cost(r['id'])
            except Exception:cost=0
            
            with db() as c:
                comps=c.execute('SELECT m.name,bri.qty,bri.unit,COALESCE(m.archived,0) as arc FROM base_recipe_items bri JOIN materials m ON m.id=bri.material_id WHERE bri.recipe_id=? ORDER BY bri.id',(r['id'],)).fetchall()
            
            has_arc = any(comp['arc'] for comp in comps)
            name_disp = f"⚠️ {r['name']}" if has_arc else r['name']
            
            iid=self.rec_tree.insert('','end',text='☐',values=(r['code'],name_disp,fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'✏️','🗑️'))
            for comp in comps:
                comp_name = f"{comp['name']} (Excluído)" if comp['arc'] else comp['name']
                self.rec_tree.insert(iid,'end',text='  ',values=('',f'↳ {comp_name}',fmt_num(comp['qty']),comp['unit'],'-','',''))"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Patched refresh_recipes!')
else:
    print('Failed to find old_logic in refresh_recipes.')
