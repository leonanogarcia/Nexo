import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace("outline=self.colors['border']", "outline='#E2EAF5'")
# While we're at it, fill should be self.colors['field'] to match the search bar's interior, but panel is fine.
# Let's match the search bar!
code = code.replace("fill=self.colors['panel'], outline='#E2EAF5'", "fill=self.colors['field'], outline='#E2EAF5'")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
