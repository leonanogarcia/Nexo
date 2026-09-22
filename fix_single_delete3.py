import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_func = """    def delete_selected_material(self):
        checked=list(getattr(self,'_checked_rows',{}).get(str(self.mat_tree),set()))
        s=checked if checked else list(self.mat_tree.selection())
        if not s:return
        s=s[:1]
        code=self.mat_tree.item(s[0])['values'][0]
        with db() as c:r=c.execute('SELECT id,name FROM materials WHERE code=?',(code,)).fetchone()
        if not r:return
        with db() as c:
            refs=(c.execute('SELECT COUNT(*) n FROM base_recipe_items WHERE material_id=?',(r['id'],)).fetchone()['n']
                  + c.execute("SELECT COUNT(*) n FROM product_items WHERE item_type='MATERIAL' AND ref_id=?",(r['id'],)).fetchone()['n']
                  + c.execute('SELECT COUNT(*) n FROM custom_units WHERE material_id=?',(r['id'],)).fetchone()['n']
                  + c.execute('SELECT COUNT(*) n FROM purchases WHERE material_id=?',(r['id'],)).fetchone()['n'])
        if refs:
            if messagebox.askyesno('Insumo vinculado','Este Insumo possui historico ou vinculos.\\nDeseja inativa-lo? (Se escolher Nao, a operacao e cancelada)',parent=self):
                with db() as c:c.execute('UPDATE materials SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Insumo inativado com sucesso.')
            return
        if not messagebox.askyesno('Excluir Insumo',f'Excluir "{r["name"]}"?',parent=self):return
        try:
            with db() as c:
                c.execute('DELETE FROM purchases WHERE material_id=?',(r['id'],))
                c.execute('DELETE FROM materials WHERE id=?',(r['id'],))
            self.refresh_all();self.notify('Insumo excluido com sucesso.')
        except Exception as e:
            messagebox.showerror('Erro',f'Nao foi possivel excluir o Insumo:\\n{e}',parent=self)"""

code = re.sub(
    r"    def delete_selected_material\(self\):.*?def delete_selected_materials\(self\):",
    new_func + "\n\n    def delete_selected_materials(self):",
    code,
    flags=re.DOTALL
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
