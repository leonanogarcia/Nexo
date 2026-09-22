import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix button texts in cadastro
code = code.replace("'+  Novo item'", "'+ Novo item'")
code = code.replace("'   Histórico'", "'🕒 Histórico'")
code = code.replace("'Excluir'", "'🗑 Excluir'")

# Fix placeholder color in RoundedEntry so it's not "so light it almost disappears"
code = code.replace("fg='#9AA9BF',font=('Segoe UI',10)", "fg='#60769D',font=('Segoe UI',10)")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
