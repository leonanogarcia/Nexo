import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(
    r"self\.mat_icon_ov=self\._attach_row_icon_overlay\(\s*self\.mat_tree, table_host, 9, 10,",
    r"self.mat_icon_ov=self._attach_row_icon_overlay(\n            self.mat_tree, table_host, 10, 11,",
    code
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
