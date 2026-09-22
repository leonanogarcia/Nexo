import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(
    r"try:\n\s*b\.configure\(state='normal'\)\n\s*if not b\.winfo_ismapped\(\): b\.pack\(side='left', padx=6\)",
    "try:\n                        if not b.winfo_ismapped(): b.pack(side='left', padx=6)",
    code
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
