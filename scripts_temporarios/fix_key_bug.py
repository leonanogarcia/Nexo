import re

with open('main.py', 'r', encoding='utf-8') as f: text = f.read()

old_loop = """            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.mat_tree.column(col,'width'))
                except Exception: cw=0"""
new_loop = """            for idx,(col,txt) in enumerate(cols):
                key = 'dummy' if idx == 0 else self._mat_header_specs[idx-1][0]
                try: cw=int(self.mat_tree.column(col,'width'))
                except Exception: cw=0"""

text = text.replace(old_loop, new_loop)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Fixed UnboundLocalError!')
