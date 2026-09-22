import tkinter as tk
import tkinter.ttk as ttk

root = tk.Tk()
root.geometry("600x400")

canvas = tk.Canvas(root, height=40, bg='red')
canvas.pack(fill='x')

tree = ttk.Treeview(root, columns=('a', 'b', 'c'), show='tree')
tree.column('#0', width=60)
tree.column('a', width=100)
tree.column('b', width=100)
tree.column('c', width=100)
tree.pack(fill='both', expand=True)

def _setup_canvas_header_drag(canvas, tree, fixed_cols):
    canvas._drag_col = None
    canvas._drag_start_x = 0
    canvas._drag_start_w = 0
    def get_col_edge(x):
        cx = 0; cols = ['#0'] + list(tree['columns'])
        for col in cols:
            cw = tree.column(col, 'width')
            cx += cw
            if abs(x - cx) < 6: return col
        return None
    def on_press(e):
        col = get_col_edge(e.x)
        if col and col not in fixed_cols:
            canvas._drag_col = col; canvas._drag_start_x = e.x
            canvas._drag_start_w = tree.column(col, 'width')
            print("Pressed", col, canvas._drag_start_w)
    def on_drag(e):
        if canvas._drag_col:
            delta = e.x - canvas._drag_start_x
            new_w = max(40, canvas._drag_start_w + delta)
            tree.column(canvas._drag_col, width=new_w)
            # redraw_cmd()
            print("Drag", canvas._drag_col, new_w)
    def on_release(e): canvas._drag_col = None
    def on_motion(e):
        col = get_col_edge(e.x)
        canvas.config(cursor='sb_h_double_arrow' if (col and col not in fixed_cols) else '')
    canvas.bind('<ButtonPress-1>', on_press)
    canvas.bind('<B1-Motion>', on_drag)
    canvas.bind('<ButtonRelease-1>', on_release)
    canvas.bind('<Motion>', on_motion)

_setup_canvas_header_drag(canvas, tree, [])

def redraw():
    canvas.delete('all')
    cx = 0
    for col in ['#0'] + list(tree['columns']):
        cw = tree.column(col, 'width')
        cx += cw
        canvas.create_line(cx, 0, cx, 40, fill='black', width=2)
    canvas.after(100, redraw)
redraw()

root.mainloop()
