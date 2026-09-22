import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_refresh = """    def refresh_materials(self):
        if not hasattr(self,'mat_tree'): return
        for x in self.mat_tree.get_children(): self.mat_tree.delete(x)
        query = '%'+self.mat_search.get().strip()+'%' if hasattr(self,'mat_search') else '%'
        with db() as c:
            rows = c.execute('''SELECT code,name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,
                                       substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10)
                                FROM materials WHERE COALESCE(active,1)=1 AND (name LIKE ? OR COALESCE(brand,'') LIKE ? OR code LIKE ?) ORDER BY name''', (query,query,query)).fetchall()
        for r in rows:
            r_list = list(r)
            val = r_list[5]
            val_str = f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            r_list[5] = val_str
            self.mat_tree.insert('', 'end', text='?', values=tuple(r_list)+('',''))"""

new_refresh = """    def refresh_materials(self):
        if not hasattr(self,'mat_tree'): return
        for x in self.mat_tree.get_children(): self.mat_tree.delete(x)
        query = '%'+self.mat_search.get().strip()+'%' if hasattr(self,'mat_search') else '%'
        status_filter = self.mat_status.get() if hasattr(self, 'mat_status') else 'Ativos'
        status_cond = "COALESCE(active,1)=1" if status_filter == 'Ativos' else ("COALESCE(active,1)=0" if status_filter == 'Inativos' else "1=1")
        with db() as c:
            rows = c.execute(f'''SELECT code,name,COALESCE(brand,''),purchase_qty,purchase_unit,purchase_value,category,
                                       substr(created_at,1,10), substr(COALESCE(updated_at,created_at),1,10), COALESCE(active,1), id
                                FROM materials WHERE {status_cond} AND (name LIKE ? OR COALESCE(brand,'') LIKE ? OR code LIKE ?) ORDER BY name''', (query,query,query)).fetchall()
        for r in rows:
            r_list = list(r)
            val = r_list[5]
            val_str = f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            r_list[5] = val_str
            is_active = r_list.pop(9)
            mat_id = r_list.pop(9)
            status_str = 'Ativo' if is_active else 'Inativo'
            self.mat_tree.insert('', 'end', iid=str(mat_id), text='?', values=tuple(r_list)+(status_str, '','',''), tags=() if is_active else ('inactive',))"""

code = code.replace(old_refresh, new_refresh)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
