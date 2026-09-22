import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Fix _detect_icon and _clean_text using regex so we don't depend on garbled characters
detect_icon_new = """    def _detect_icon(self,text):
        if '+' in text: return 'plus'
        if '🕒' in text or 'clock' in text.lower(): return 'clock'
        if '🔄' in text: return 'convert'
        if '🗑' in text or 'delete' in text.lower(): return 'delete'
        return None

    def _clean_text(self,text):
        for token in ('+', '🕒', '🔄', '🗑'):
            text = text.replace(token, '')
        return ' '.join(text.split())"""

# Replace the two functions. We find from `def _detect_icon` up to the line before `def _make`
code = re.sub(r"    def _detect_icon\(self,text\):.*?return ' '\.join\(text\.split\(\)\)", detect_icon_new, code, flags=re.DOTALL)

# 2. Add self._action_buttons for mat_tree in cadastro
# We will insert it at the end of the cadastro method, right before `def material_form`
action_btn_code = """        self._action_buttons[self.mat_tree]={'normal':[mat_add,mat_history],'bulk':[self.mat_bulk_delete_btn]}
        self.mat_empty_overlay = tk.Label(table_host, text='Nenhum insumo encontrado.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"""

# Search for the end of cadastro (where mat_empty_overlay is defined)
code = code.replace("        self.mat_empty_overlay = tk.Label(table_host, text='Nenhum insumo encontrado.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))", action_btn_code)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
