import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(
    r"trans_color = getattr\(self\.winfo_toplevel\(\), 'colors', \{\}\)\.get\('panel', '#FFFFFF'\)",
    "trans_color = '#FF00FF'\n            try: tip.attributes('-transparentcolor', trans_color)\n            except: pass",
    code
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
