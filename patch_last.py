import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# 1. FIX RoundedEntry placeholder
old_rounded_init = """        self.entry.place(x=42,rely=.5,anchor='w',relwidth=1,width=-56,relheight=.56)
        self._var=textvariable
        self._var.trace_add('write',lambda *a:self._update_placeholder())"""

new_rounded_init = """        self.entry.place(x=42,rely=.5,anchor='w',relwidth=1,width=-56,relheight=.56)
        self._placeholder_label = tk.Label(self, text=placeholder, bg=self._bg, fg='#A0ABB9', font=('Segoe UI', 10), cursor='xterm')
        self._placeholder_label.bind('<Button-1>', lambda e: self.entry.focus_set())
        self._var=textvariable
        self._var.trace_add('write',lambda *a:self._update_placeholder())"""
text = text.replace(old_rounded_init, new_rounded_init)

# 2. FIX _attach_row_icon_overlay (complete regex replace of the method up to `ov_left.place`)
# The problem is that y_off was 36 if is_mat else 0. Now it MUST ALWAYS BE 36 for all custom headers!
attach_pattern = r"    def _attach_row_icon_overlay\(self, tree, table_host, edit_col_idx, delete_col_idx, edit_cmd, delete_cmd\):.*?ov_left\.place\(relx=0, x=0, y=y_off, width=cw0, relheight=1\.0, height=-y_off, anchor='nw'\)"

new_attach = """    def _attach_row_icon_overlay(self, tree, table_host, edit_col_idx, delete_col_idx, edit_cmd, delete_cmd):
        ov = tk.Canvas(table_host, bd=0, highlightthickness=0, cursor='arrow', bg=self.colors['field'])
        ov.place(relx=1.0, x=0, y=36, width=90, relheight=1.0, height=-36, anchor='ne')
        ov._icon_refs = []
        
        is_mat = tree == getattr(self, 'mat_tree', None)
        try: cw0 = int(tree.column('#0', 'width'))
        except: cw0 = 60
        y_off = 36
        ov_left = tk.Canvas(table_host, bd=0, highlightthickness=0, cursor='arrow', bg=self.colors['field'])
        ov_left.place(relx=0, x=0, y=y_off, width=cw0, relheight=1.0, height=-y_off, anchor='nw')"""

text = re.sub(attach_pattern, new_attach, text, flags=re.DOTALL)

# 3. FIX the `not is_mat` block inside `_redraw_overlay` that draws over the header!
not_mat_pattern = r"            if not is_mat:\s*header_bg.*?outline=''\)"
new_not_mat = """            pass"""
text = re.sub(not_mat_pattern, new_not_mat, text, flags=re.DOTALL)


with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched RoundedEntry and _attach_row_icon_overlay!")
