import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace("key = self._get_hover_key(event.y)", "key = self._hit_key(event.x, event.y)")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
