import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_detect = """    def _detect_icon(self,text):
        if '+' in text: return 'plus'
        if '<clock>' in text: return 'clock'
        if '<convert>' in text: return 'convert'
        if '<delete>' in text: return 'delete'
        return None

    def _clean_text(self,text):
        for token in ('+', '<clock>', '<convert>', '<delete>'):
            text = text.replace(token, '')
        return ' '.join(text.split())"""

code = re.sub(r"    def _detect_icon\(self,text\):.*?return ' '\.join\(text\.split\(\)\)", new_detect, code, flags=re.DOTALL)

# Fix the texts in cadastro
code = code.replace("🕒 Histórico", "<clock> Histórico")
code = code.replace("🗑 Excluir", "<delete> Excluir")

# Make sure to fix `mat_conv` if it exists. (Wait, the user's UI didn't have mat_conv! The user's image shows Novo Item, Histórico, Ativos filter).
# What about 'Excluir'? It's a bulk delete button, it should say '<delete> Excluir'.

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
