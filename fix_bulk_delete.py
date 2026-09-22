import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_bulk = """        if linked:
            unlinked=[r for r in rows if r['id'] not in {x['id'] for x in linked}]
            msg = 'Alguns itens possuem vinculos/historico:\\n\\n' + '\\n'.join(' '+r['name'] for r in linked)
            msg += '\\n\\nEstes itens nao podem ser excluidos, apenas inativados.'
            if unlinked:
                msg += f'\\nOs outros {len(unlinked)} itens sem vinculos serao excluidos.'
            msg += '\\n\\nDeseja prosseguir com a operacao conjunta? Se escolher Nao, TUDO sera cancelado.'
            if not messagebox.askyesno('Itens vinculados', msg, parent=self): return
            try:
                with db() as c:
                    for r in linked: c.execute(f'UPDATE {table} SET active=0,updated_at=? WHERE id=?', (now_iso(), r['id']))
                    for r in unlinked: c.execute(f'DELETE FROM {table} WHERE id=?', (r['id'],))
                self.refresh_all()
                self.notify('Operacao concluida com sucesso.')
            except Exception as e:
                messagebox.showerror('Erro', f'Falha ao processar: {e}', parent=self)
            return
        if not messagebox.askyesno('Excluir itens',f'Excluir {len(rows)} itens selecionados?',parent=self):return
        with db() as c:
            for r in rows:c.execute(f'DELETE FROM {table} WHERE id=?',(r['id'],))
        self.refresh_all();self.notify(f'{len(rows)} itens excluidos com sucesso.')

    def edit_selected_material(self):"""

code = re.sub(
    r"        if linked:.*?    def edit_selected_material\(self\):",
    new_bulk,
    code,
    flags=re.DOTALL
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
