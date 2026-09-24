import os

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_str = "Modal(self, 'Editar item' if is_edit else 'Novo item', '620x360')"
new_str = "Modal(self, 'Editar item' if is_edit else 'Novo item', '620x310')"

content = content.replace(old_str, new_str)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Altura reduzida com sucesso!")
