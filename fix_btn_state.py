import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

def inject_configure(m):
    return m.group(0) + """
    def configure(self, **kwargs):
        if 'state' in kwargs:
            kwargs.pop('state')
        super().configure(**kwargs)
    config = configure
"""

code = re.sub(r'def _on_leave\(self, e\):\s*self\._active = False\s*self\._redraw\(\)', inject_configure, code)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
