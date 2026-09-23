import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_logic = """    def _bulk_delete_list(self, tree, kind):
        checked=getattr(self,'_checked_rows',{}).get(str(tree),set())
        if len(checked)<2: return
        table={'material':'materials','recipe':'base_recipes','product':'products'}[kind]
        rows=[]
        with db() as c:
            for iid in checked:
                vals=tree.item(iid,'values'); code=vals[0] if vals else ''
                r=c.execute(f'SELECT id,name FROM {table} WHERE code=?',(code,)).fetchone()
                if r: rows.append(r)
        if not rows:return
        
        linked = []
        unlinked = []
        with db() as c:
            for r in rows:
                if kind == 'material':
                    refs = c.execute('SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?',(r['id'],)).fetchone()['n']
                    refs += c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",(r['id'],)).fetchone()['n']
                elif kind == 'recipe':
                    refs = c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='RECIPE_BASE' AND ref_id=?",(r['id'],)).fetchone()['n']
                elif kind == 'product':
                    refs = 0
                if refs > 0: linked.append(r)
                else: unlinked.append(r)
        
        msg = f'Você selecionou {len(rows)} itens.\\n'
        if linked:
            msg += f'\\n{len(linked)} itens possuem vínculos/dependências e serão INATIVADOS:\\n'
            msg += '\\n'.join('  - ' + r['name'] for r in linked) + '\\n'
        if unlinked:
            msg += f'\\nOs outros {len(unlinked)} itens (sem vínculos) serão EXCLUÍDOS permanentemente.\\n'
            
        msg += '\\nDeseja prosseguir? (Se escolher Não, toda a operação será cancelada).'
            
        if not messagebox.askyesno('Confirmar exclusão em lote', msg, parent=self): return
        
        with db() as c:
            for r in unlinked:
                if kind == 'material':
                    c.execute('DELETE FROM purchases WHERE material_id=?', (r['id'],))
                    c.execute("DELETE FROM cost_history WHERE entity_type='MATERIAL' AND entity_id=?", (r['id'],))
                    c.execute('DELETE FROM custom_units WHERE material_id=?', (r['id'],))
                elif kind == 'recipe':
                    c.execute("DELETE FROM cost_history WHERE entity_type='RECIPE_BASE' AND entity_id=?", (r['id'],))
                elif kind == 'product':
                    c.execute("DELETE FROM cost_history WHERE entity_type='PRODUCT' AND entity_id=?", (r['id'],))
                c.execute(f'DELETE FROM {table} WHERE id=?',(r['id'],))
            
            for r in linked:
                c.execute(f'UPDATE {table} SET active=0, updated_at=? WHERE id=?', (now_iso(), r['id']))
                
        self.refresh_all()
        self.notify(f'{len(unlinked)} excluídos, {len(linked)} inativados.')"""

new_logic = """    def _bulk_delete_list(self, tree, kind):
        checked=getattr(self,'_checked_rows',{}).get(str(tree),set())
        if not checked:
            s = tree.selection()
            if s: checked = {s[0]}
            else: return
            
        table={'material':'materials','recipe':'base_recipes','product':'products'}[kind]
        rows=[]
        with db() as c:
            for iid in checked:
                vals=tree.item(iid,'values'); code=vals[0] if vals else ''
                r=c.execute(f'SELECT id,name,COALESCE(active,1) as active FROM {table} WHERE code=?',(code,)).fetchone()
                if r: rows.append(r)
        if not rows:return
        
        linked = []
        unlinked = []
        with db() as c:
            for r in rows:
                if kind == 'material':
                    refs = c.execute('SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?',(r['id'],)).fetchone()['n']
                    refs += c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",(r['id'],)).fetchone()['n']
                elif kind == 'recipe':
                    refs = c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='RECIPE_BASE' AND ref_id=?",(r['id'],)).fetchone()['n']
                elif kind == 'product':
                    refs = 0
                if refs > 0: linked.append(r)
                else: unlinked.append(r)
        
        if len(rows) == 1:
            r = rows[0]
            if unlinked:
                if not messagebox.askyesno('Confirmar exclusão', f"Tem certeza que deseja excluir permanentemente '{r['name']}'?", parent=self): return
                with db() as c:
                    if kind == 'material':
                        c.execute('DELETE FROM purchases WHERE material_id=?', (r['id'],))
                        c.execute("DELETE FROM cost_history WHERE entity_type='MATERIAL' AND entity_id=?", (r['id'],))
                        c.execute('DELETE FROM custom_units WHERE material_id=?', (r['id'],))
                    elif kind == 'recipe':
                        c.execute("DELETE FROM cost_history WHERE entity_type='RECIPE_BASE' AND entity_id=?", (r['id'],))
                    elif kind == 'product':
                        c.execute("DELETE FROM cost_history WHERE entity_type='PRODUCT' AND entity_id=?", (r['id'],))
                    c.execute(f'DELETE FROM {table} WHERE id=?',(r['id'],))
                self.refresh_all()
                self.notify(f"Item '{r['name']}' excluído permanentemente.")
                return
            else:
                if r['active'] == 1:
                    if not messagebox.askyesno('Confirmar inativação', f"O item '{r['name']}' possui vínculos/dependências em receitas ou produtos e não pode ser apagado sem quebrar os custos.\\n\\nDeseja INATIVAR este item em vez disso?", parent=self): return
                    with db() as c: c.execute(f'UPDATE {table} SET active=0, updated_at=? WHERE id=?', (now_iso(), r['id']))
                    self.refresh_all()
                    self.notify(f"Item '{r['name']}' inativado.")
                    return
                else:
                    if not messagebox.askyesno('Exclusão Fantasma', f"O item '{r['name']}' já está inativo, mas ainda possui vínculos com receitas/produtos.\\n\\nDeseja OCULTÁ-LO definitivamente do sistema?\\n\\nEle desaparecerá das listas, mas aparecerá com um alerta ⚠️ nas receitas até ser substituído.", parent=self): return
                    with db() as c: c.execute(f'UPDATE {table} SET archived=1, updated_at=? WHERE id=?', (now_iso(), r['id']))
                    self.refresh_all()
                    self.notify(f"Item '{r['name']}' ocultado definitivamente.")
                    return
        
        msg = f'Você selecionou {len(rows)} itens.\\n'
        if linked:
            msg += f'\\n{len(linked)} itens possuem vínculos/dependências e serão INATIVADOS/OCULTADOS:\\n'
            msg += '\\n'.join('  - ' + r['name'] for r in linked) + '\\n'
        if unlinked:
            msg += f'\\nOs outros {len(unlinked)} itens (sem vínculos) serão EXCLUÍDOS permanentemente.\\n'
            
        msg += '\\nDeseja prosseguir? (Se escolher Não, toda a operação será cancelada).'
            
        if not messagebox.askyesno('Confirmar exclusão em lote', msg, parent=self): return
        
        with db() as c:
            for r in unlinked:
                if kind == 'material':
                    c.execute('DELETE FROM purchases WHERE material_id=?', (r['id'],))
                    c.execute("DELETE FROM cost_history WHERE entity_type='MATERIAL' AND entity_id=?", (r['id'],))
                    c.execute('DELETE FROM custom_units WHERE material_id=?', (r['id'],))
                elif kind == 'recipe':
                    c.execute("DELETE FROM cost_history WHERE entity_type='RECIPE_BASE' AND entity_id=?", (r['id'],))
                elif kind == 'product':
                    c.execute("DELETE FROM cost_history WHERE entity_type='PRODUCT' AND entity_id=?", (r['id'],))
                c.execute(f'DELETE FROM {table} WHERE id=?',(r['id'],))
            
            for r in linked:
                if r['active'] == 1:
                    c.execute(f'UPDATE {table} SET active=0, updated_at=? WHERE id=?', (now_iso(), r['id']))
                else:
                    c.execute(f'UPDATE {table} SET archived=1, updated_at=? WHERE id=?', (now_iso(), r['id']))
                
        self.refresh_all()
        self.notify(f'{len(unlinked)} excluídos, {len(linked)} inativados/ocultados.')"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Successfully patched _bulk_delete_list!')
else:
    print('Failed to find old_logic in main.py.')
