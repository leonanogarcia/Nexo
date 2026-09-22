import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the specific lines inside delete_selected_material
code = re.sub(
    r"(if refs:\s*\n\s*if messagebox\.askyesno\('Insumo vinculado',.*?:\s*\n\s*with db\(\) as c:c\.execute\('UPDATE materials SET active=0.*?:\s*\n\s*return\s*\n\s*elif not messagebox\.askyesno\('Excluir Definitivamente'.*?:\s*\n\s*return)",
    r"if refs:\n            if messagebox.askyesno('Insumo vinculado','Este Insumo possui historico ou vinculos. Excluir quebra o banco. Deseja INATIVA-LO? (Se escolher Nao, a operacao e cancelada)',parent=self):\n                with db() as c:c.execute('UPDATE materials SET active=0,updated_at=? WHERE id=?',(now_iso(),r['id']))\n                self.refresh_all();self.notify('Insumo inativado com sucesso.')\n            return",
    code,
    flags=re.DOTALL
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
