import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_delete = """        if refs:
            if messagebox.askyesno('Insumo vinculado','Este Insumo possui histrico ou vnculos. Excluir apagar seu histrico de compras. Deseja apenas INATIV-LO para preservar os dados?',parent=self):
                with db() as c:c.execute('UPDATE materials SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Insumo inativado com sucesso.')
                return
            elif not messagebox.askyesno('Excluir Definitivamente', 'Tem certeza que deseja EXCLUIR o item e perder todo o histrico relacionado a ele?', parent=self):
                return"""

new_delete = """        if refs:
            if messagebox.askyesno('Insumo vinculado','Este Insumo possui histrico ou vnculos. Excluir apagar seu histrico de compras. Deseja apenas INATIV-LO para preservar os dados? Se escolher No, a operao ser cancelada.',parent=self):
                with db() as c:c.execute('UPDATE materials SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))
                self.refresh_all();self.notify('Insumo inativado com sucesso.')
            return"""

code = code.replace(old_delete, new_delete)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
