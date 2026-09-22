import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

def replace_detect_icon(m):
    return m.group(0).replace("return None", "if 'Excluir' in text or 'delete' in text.lower(): return 'delete'\n        return None")

code = re.sub(r'def _detect_icon.*?return None', replace_detect_icon, code, flags=re.DOTALL)

def replace_make(m):
    return m.group(0).replace("elif icon == 'convert':", "elif icon == 'delete':\n                    d.line([(sx-6*scale,sy-6*scale),(sx+6*scale,sy-6*scale)],fill=col,width=lw)\n                    d.line([(sx-3*scale,sy-8*scale),(sx+3*scale,sy-8*scale)],fill=col,width=lw)\n                    d.line([(sx-5*scale,sy-6*scale),(sx-4*scale,sy+7*scale)],fill=col,width=lw)\n                    d.line([(sx+5*scale,sy-6*scale),(sx+4*scale,sy+7*scale)],fill=col,width=lw)\n                    d.line([(sx-4*scale,sy+7*scale),(sx+4*scale,sy+7*scale)],fill=col,width=lw)\n                elif icon == 'convert':")

code = re.sub(r'elif icon == \'clock\':.*?elif icon == \'convert\':', replace_make, code, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
