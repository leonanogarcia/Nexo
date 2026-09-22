import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Fix single material delete
old_delete_mat = """    def delete_selected_material(self):
        s=self.mat_tree.selection()
        if not s or self._selection_count(self.mat_tree)!=1:return
        code=self.mat_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM materials WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:
            refs=(c.execute('SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?',(r['id'],)).fetchone()['n']
                  + c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",(r['id'],)).fetchone()['n']
                  + c.execute('SELECT COUNT(*) n FROM custom_units WHERE material_id=?',(r['id'],)).fetchone()['n'])
        if refs:
            if messagebox.askyesno('Insumo vinculado','Este Insumo possui vínculos e não pode ser excluído sem quebrar relações. Deseja inativá-lo?',parent=self):
                with db() as c:c.execute('UPDATE materials SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Insumo inativado com sucesso.')
            return
        if not messagebox.askyesno('Excluir Insumo',f'Excluir "{r["name"]}"? O histórico de compras também será removido.',parent=self):return
        with db() as c:c.execute('DELETE FROM materials WHERE id=?',(r['id'],))
        self.refresh_all();self.notify('Insumo excluído com sucesso.')"""

# Using regex because of encoding differences
new_delete_mat = """    def delete_selected_material(self):
        s=self.mat_tree.selection()
        if not s or self._selection_count(self.mat_tree)!=1:return
        code=self.mat_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM materials WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:
            refs=(c.execute('SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?',(r['id'],)).fetchone()['n']
                  + c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",(r['id'],)).fetchone()['n'])
        if refs:
            if messagebox.askyesno('Insumo vinculado', 'Este Insumo possui vínculos em receitas/produtos. Deseja inativá-lo em vez de excluir?', parent=self):
                with db() as c:c.execute('UPDATE materials SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Insumo inativado com sucesso.')
            return
        if not messagebox.askyesno('Excluir Insumo', f'Excluir "{r["name"]}"? O histórico de compras e custos também será removido.', parent=self):return
        with db() as c:
            c.execute('DELETE FROM purchases WHERE material_id=?', (r['id'],))
            c.execute("DELETE FROM cost_history WHERE entity_type='MATERIAL' AND entity_id=?", (r['id'],))
            c.execute('DELETE FROM custom_units WHERE material_id=?', (r['id'],))
            c.execute('DELETE FROM materials WHERE id=?', (r['id'],))
        self.refresh_all();self.notify('Insumo excluído com sucesso.')"""

code = re.sub(r"    def delete_selected_material\(self\):.*?self\.notify\('Insumo exclu..?do com sucesso\.'\)", new_delete_mat, code, flags=re.DOTALL)


# 2. Fix bulk delete
new_bulk_delete = """    def _bulk_delete_list(self, tree, kind):
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
        
        msg = f'Você selecionou {len(rows)} itens.\n'
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

code = re.sub(r"    def _bulk_delete_list\(self, tree, kind\):.*?self\.notify\(f'\{len\(unlinked\)\} excluidos, \{len\(linked\)\} inativados\.'\)", new_bulk_delete, code, flags=re.DOTALL)


# Also ensure single recipe and product deletes are safe from cost_history blocks!
old_del_rec = """    def delete_selected_recipe(self):
        s=self.rec_tree.selection()
        if not s or self._selection_count(self.rec_tree)!=1:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM base_recipes WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:refs=c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='RECIPE_BASE' AND ref_id=?",(r['id'],)).fetchone()['n']
        if refs:
            if messagebox.askyesno('Receita vinculada','Esta Receita Base  usada em Produtos. Deseja inativ-la em vez de excluir?',parent=self):
                with db() as c:c.execute('UPDATE base_recipes SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Receita inativada com sucesso.')
            return
        if not messagebox.askyesno('Excluir Receita',f'Excluir permanentemente "{r["name"]}"?',parent=self):return
        with db() as c:c.execute('DELETE FROM base_recipes WHERE id=?',(r['id'],))
        self.refresh_all();self.notify('Receita excluda com sucesso.')"""

new_del_rec = """    def delete_selected_recipe(self):
        s=self.rec_tree.selection()
        if not s or self._selection_count(self.rec_tree)!=1:return
        code=self.rec_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM base_recipes WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:refs=c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='RECIPE_BASE' AND ref_id=?",(r['id'],)).fetchone()['n']
        if refs:
            if messagebox.askyesno('Receita vinculada','Esta Receita Base é usada em Produtos. Deseja inativá-la em vez de excluir?',parent=self):
                with db() as c:c.execute('UPDATE base_recipes SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Receita inativada com sucesso.')
            return
        if not messagebox.askyesno('Excluir Receita',f'Excluir permanentemente "{r["name"]}"?',parent=self):return
        with db() as c:
            c.execute("DELETE FROM cost_history WHERE entity_type='RECIPE_BASE' AND entity_id=?", (r['id'],))
            c.execute('DELETE FROM base_recipes WHERE id=?',(r['id'],))
        self.refresh_all();self.notify('Receita excluída com sucesso.')"""

code = re.sub(r"    def delete_selected_recipe\(self\):.*?self\.notify\('Receita exclu..?da com sucesso\.'\)", new_del_rec, code, flags=re.DOTALL)


old_del_prod = """    def delete_selected_product(self):
        s=self.prod_tree.selection()
        if not s or self._selection_count(self.prod_tree)!=1:return
        code=self.prod_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM products WHERE code=?',(code,)).fetchone()
        if not r:return
        if not messagebox.askyesno('Excluir Produto',f'Excluir permanentemente "{r["name"]}"?',parent=self):return
        with db() as c:c.execute('DELETE FROM products WHERE id=?',(r['id'],))
        self.refresh_all();self.notify('Produto excludo com sucesso.')"""

new_del_prod = """    def delete_selected_product(self):
        s=self.prod_tree.selection()
        if not s or self._selection_count(self.prod_tree)!=1:return
        code=self.prod_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM products WHERE code=?',(code,)).fetchone()
        if not r:return
        if not messagebox.askyesno('Excluir Produto',f'Excluir permanentemente "{r["name"]}"?',parent=self):return
        with db() as c:
            c.execute("DELETE FROM cost_history WHERE entity_type='PRODUCT' AND entity_id=?", (r['id'],))
            c.execute('DELETE FROM products WHERE id=?',(r['id'],))
        self.refresh_all();self.notify('Produto excluído com sucesso.')"""

code = re.sub(r"    def delete_selected_product\(self\):.*?self\.notify\('Produto exclu..?do com sucesso\.'\)", new_del_prod, code, flags=re.DOTALL)


with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
