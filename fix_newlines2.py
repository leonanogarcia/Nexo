import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    "f'Nao foi possivel excluir o Insumo:\n{e}'",
    "f'Nao foi possivel excluir o Insumo:\\n{e}'"
)
code = code.replace(
    "'Alguns itens possuem vinculos/historico:\n\n'",
    "'Alguns itens possuem vinculos/historico:\\n\\n'"
)
code = code.replace(
    "'\n'.join",
    "'\\n'.join"
)
code = code.replace(
    "'\n\nEstes itens nao podem ser excluidos, apenas inativados.'",
    "'\\n\\nEstes itens nao podem ser excluidos, apenas inativados.'"
)
code = code.replace(
    "f'\nOs outros {len(unlinked)} itens sem vinculos serao excluidos.'",
    "f'\\nOs outros {len(unlinked)} itens sem vinculos serao excluidos.'"
)
code = code.replace(
    "'\n\nDeseja prosseguir com a operacao conjunta? Se escolher Nao, TUDO sera cancelado.'",
    "'\\n\\nDeseja prosseguir com a operacao conjunta? Se escolher Nao, TUDO sera cancelado.'"
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
