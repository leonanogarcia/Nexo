import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

def inject_double_click(m):
    return m.group(0) + """
        def on_double(e):
            col = get_col_edge(e.x)
            if col and col not in fixed_cols:
                setattr(self, f'_{state_key}_user_resized', False)
                redraw_cmd()
        canvas.bind('<Double-Button-1>', on_double)
"""

code = re.sub(
    r"canvas\.bind\('<Motion>', on_motion\)",
    inject_double_click,
    code
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
