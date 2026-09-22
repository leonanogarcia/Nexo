import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(
    r"trans_color = getattr\(self\.winfo_toplevel\(\), 'colors', \{\}\)\.get\('bg', '#F7F9FC'\)",
    "trans_color = getattr(self.winfo_toplevel(), 'colors', {}).get('panel', '#FFFFFF')",
    code
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
