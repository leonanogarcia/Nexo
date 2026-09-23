import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Change _attach_row_icon_overlay so it assumes y_off=36 for everything
old_attach = """        is_mat = tree == getattr(self, 'mat_tree', None)
        cw0 = int(tree.column('#0', 'width'))
        y_off = 36 if is_mat else 0
        ov_left = tk.Canvas(table_host, bd=0, highlightthickness=0, cursor='arrow', bg=self.colors['field'])"""
new_attach = """        cw0 = int(tree.column('#0', 'width'))
        y_off = 36
        ov_left = tk.Canvas(table_host, bd=0, highlightthickness=0, cursor='arrow', bg=self.colors['field'])"""
text = text.replace(old_attach, new_attach)

old_not_mat = """            if not is_mat:
                header_bg = '#142544' if getattr(self, '_dark', False) else '#E8EEF8'
                ov_left.create_rectangle(0, 0, cw0, 38, fill=header_bg, outline='')"""
new_not_mat = """            pass"""
text = text.replace(old_not_mat, new_not_mat)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched _attach_row_icon_overlay")
