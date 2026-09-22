import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    "'Este Insumo possui historico ou vinculos.\nDeseja inativa-lo? (Se escolher Nao, a operacao e cancelada)'",
    "'Este Insumo possui historico ou vinculos.\\nDeseja inativa-lo? (Se escolher Nao, a operacao e cancelada)'"
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
