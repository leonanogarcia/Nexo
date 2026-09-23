import re

with open('main.py', 'rb') as f:
    content = f.read().decode('utf-8')

match = re.search(r'    def refresh_recipes\(self\):.*?self\._reset_checked\(self\.rec_tree\)', content, re.DOTALL)
if match:
    old = match.group(0)
    new_code = """    def refresh_recipes(self):
        if not hasattr(self,'rec_tree'):return
        for x in self.rec_tree.get_children():self.rec_tree.delete(x)
        with db() as c:rows=c.execute('SELECT id,code,name,yield_qty,yield_unit FROM base_recipes WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0 ORDER BY name').fetchall()
        for r in rows:
            try:cost=recipe_cost(r['id'])
            except Exception:cost=0
            
            with db() as c:
                comps=c.execute('SELECT m.name,bri.qty,bri.unit,COALESCE(m.archived,0) as arc FROM base_recipe_items bri JOIN materials m ON m.id=bri.material_id WHERE bri.recipe_id=? ORDER BY bri.id',(r['id'],)).fetchall()
            
            has_arc = any(comp['arc'] for comp in comps)
            name_disp = f"⚠️ {r['name']}" if has_arc else r['name']
            
            iid=self.rec_tree.insert('','end',text='☐',values=(r['code'],name_disp,fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'✏️','🗑️'))
            for comp in comps:
                comp_name = f"{comp['name']} (⚠️ Excluído)" if comp['arc'] else comp['name']
                self.rec_tree.insert(iid,'end',text='  ',values=('',f'↳ {comp_name}',fmt_num(comp['qty']),comp['unit'],'-','',''))
        self._reset_checked(self.rec_tree)"""
    content = content.replace(old, new_code)
    with open('main.py', 'wb') as f:
        f.write(content.encode('utf-8'))
    print('Success recipe')
else:
    print('Regex failed')

match2 = re.search(r'    def refresh_products\(self\):.*?self\._reset_checked\(self\.prod_tree\)', content, re.DOTALL)
if match2:
    old2 = match2.group(0)
    new_code2 = """    def refresh_products(self):
        if not hasattr(self,'prod_tree'):return
        for x in self.prod_tree.get_children():self.prod_tree.delete(x)
        with db() as c:rows=c.execute('SELECT id,code,name,weight_qty,weight_unit,sale_price FROM products WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0 ORDER BY name').fetchall()
        for r in rows:
            try:cost=product_unit_cost(r['id'])
            except Exception:cost=0
            margin=((r['sale_price']-cost)/r['sale_price']*100) if r['sale_price'] else None
            
            with db() as c:
                comps=c.execute('SELECT item_type,ref_id,qty_per_unit AS qty,unit FROM product_items WHERE product_id=? ORDER BY id',(r['id'],)).fetchall()
                
                has_arc = False
                disp_comps = []
                for comp in comps:
                    if comp['item_type'] == 'MATERIAL':
                        m = c.execute('SELECT name, COALESCE(archived,0) as arc FROM materials WHERE id=?',(comp['ref_id'],)).fetchone()
                        if m:
                            n = m['name']
                            if m['arc']:
                                has_arc = True
                                n += " (⚠️ Excluído)"
                            disp_comps.append((n, comp['qty'], comp['unit']))
                    else:
                        m = c.execute('SELECT name, COALESCE(archived,0) as arc FROM base_recipes WHERE id=?',(comp['ref_id'],)).fetchone()
                        if m:
                            n = m['name']
                            if m['arc']:
                                has_arc = True
                                n += " (⚠️ Excluído)"
                            disp_comps.append((f"[Receita] {n}", comp['qty'], comp['unit']))

            name_disp = f"⚠️ {r['name']}" if has_arc else r['name']
            
            iid=self.prod_tree.insert('','end',text='☐',values=(r['code'],name_disp,(fmt_num(r['weight_qty'])+' '+str(r['weight_unit'] or '')).strip() or '-',fmt(cost),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-','✏️','🗑️'))
            for n, q, u in disp_comps:
                self.prod_tree.insert(iid,'end',text='  ',values=('',f'↳ {n}',fmt_num(q),u,'-','-','',''))
        self._reset_checked(self.prod_tree)"""
    content = content.replace(old2, new_code2)
    with open('main.py', 'wb') as f:
        f.write(content.encode('utf-8'))
    print('Success products')
