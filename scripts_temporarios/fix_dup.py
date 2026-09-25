with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace(", anchor='center', tags=('header_chk',)), anchor='center', tags=('header_chk',))", ", anchor='center', tags=('header_chk',))")
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
