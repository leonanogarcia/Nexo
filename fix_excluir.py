with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    "RoundedActionButton(bar, '🗑️ Excluir',",
    "RoundedActionButton(bar, 'Excluir',",
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
