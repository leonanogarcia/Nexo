import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

setup_canvas_func = """    def _setup_canvas_header_drag(self, canvas, tree, fixed_cols, redraw_cmd, state_key):
        canvas._drag_col = None
        canvas._drag_start_x = 0
        canvas._drag_start_w = 0
        def get_col_edge(x):
            cx = 0; cols = ['#0'] + list(tree['columns'])
            for col in cols:
                cw = int(tree.column(col, 'width'))
                cx += cw
                if abs(x - cx) < 8: return col
            return None
        def on_press(e):
            col = get_col_edge(e.x)
            if col and col not in fixed_cols:
                canvas._drag_col = col; canvas._drag_start_x = e.x
                canvas._drag_start_w = int(tree.column(col, 'width'))
                setattr(self, f'_{state_key}_user_resized', True)
        def on_drag(e):
            if canvas._drag_col:
                delta = e.x - canvas._drag_start_x
                new_w = max(40, canvas._drag_start_w + delta)
                tree.column(canvas._drag_col, width=new_w)
                redraw_cmd()
        def on_motion(e):
            canvas.config(cursor='sb_h_double_arrow' if get_col_edge(e.x) and get_col_edge(e.x) not in fixed_cols else 'arrow')
        def on_double_click(e):
            col = get_col_edge(e.x)
            if col and col not in fixed_cols:
                setattr(self, f'_{state_key}_user_resized', False)
                self.winfo_toplevel().event_generate('<Configure>')
        canvas.bind('<Button-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<Motion>', on_motion)
        canvas.bind('<Double-Button-1>', on_double_click)

    def cadastro(self, f):"""

code = code.replace("    def cadastro(self, f):", setup_canvas_func)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
