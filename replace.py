with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '_mat_header_specs=' in l:
        lines[i] = "        self._mat_header_specs=[('code','Código',100),('name','Item',220),('brand','Marca',150),('qty','Quantidade',110),('unit','Un.',65),('value','Valor',100),('category','Categoria',130),('date','Data de criação',135),('mod_date','Última modificação',135),('edit','',46),('delete','',46)]\n"
        break

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
