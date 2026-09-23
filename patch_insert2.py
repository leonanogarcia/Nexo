import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

text = re.sub(
    r"(iid=self\.prod_tree\.insert\('','end',text='[^']+',values=\([^)]+\)(?: \S+ [^)]+\))?[^)]+\))(\))",
    r"\1, tags=() if is_active else ('inactive',)\2",
    text
)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched prod insert")
