with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace("c.create_text(x0+12, h/2, text=txt, fill=text_col, font=('Segoe UI',9,'bold'), anchor='w')",
                    "c.create_text(x0+cw/2, h/2, text=txt, fill=text_col, font=('Segoe UI',9,'bold'), anchor='center')")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
