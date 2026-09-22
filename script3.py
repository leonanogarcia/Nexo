import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 4. Add tag configure to Treeviews
code = re.sub(
    r"self\.mat_tree=ttk\.Treeview.*?show='tree'\)",
    r"\g<0>\n            self.mat_tree.tag_configure('inactive', foreground='#9AA9BF')",
    code
)
code = re.sub(
    r"self\.rec_tree=ttk\.Treeview.*?show='tree'\)",
    r"\g<0>\n            self.rec_tree.tag_configure('inactive', foreground='#9AA9BF')",
    code
)
code = re.sub(
    r"self\.prod_tree=ttk\.Treeview.*?show='tree'\)",
    r"\g<0>\n            self.prod_tree.tag_configure('inactive', foreground='#9AA9BF')",
    code
)

# 5. Context menu function and toggle function
new_methods = """    def _toggle_active(self, kind, iid, current_active):
        table={'material':'materials','recipe':'base_recipes','product':'products'}[kind]
        new_val = 0 if current_active else 1
        with db() as c:
            c.execute(f'UPDATE {table} SET active=?, updated_at=? WHERE id=?', (new_val, now_iso(), iid))
        self.refresh_all()
        self.notify(f"Item {'desativado' if current_active else 'ativado'} com sucesso.")

    def _show_row_menu(self, tree, kind, iid, x, y, edit_cmd, delete_cmd):
        tree.selection_set(iid)
        is_active = 'inactive' not in tree.item(iid, 'tags')
        
        m = tk.Menu(self.winfo_toplevel(), tearoff=0, bg=self.colors['panel'], fg=self.colors['text'], font=('Segoe UI', 10), bd=1)
        
        if is_active:
            m.add_command(label='✏️ Editar', command=lambda: edit_cmd())
        else:
            m.add_command(label='✏️ Editar (Desabilitado)', state='disabled')
            
        m.add_command(label='🗑️ Excluir', command=lambda: delete_cmd())
        m.add_separator()
        
        if is_active:
            m.add_command(label='❌ Desativar', command=lambda: self._toggle_active(kind, iid, True))
        else:
            m.add_command(label='✅ Ativar', command=lambda: self._toggle_active(kind, iid, False))
            
        m.post(x, y)

    def _attach_row_icon_overlay(self, tree, table_host, edit_col_idx, delete_col_idx,
                                  edit_cmd, delete_cmd):"""

code = re.sub(
    r"    def _attach_row_icon_overlay\(self, tree, table_host, edit_col_idx, delete_col_idx,\s*\n\s*edit_cmd, delete_cmd\):",
    new_methods,
    code
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
