import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_make_row_icon = """    def _make_row_icon(self, kind):
        try:
            from PIL import Image, ImageTk
            import pathlib
            UI_ASSETS = pathlib.Path(__file__).parent / 'ui_assets'
            if kind == 'edit':
                im = Image.open(UI_ASSETS / 'action_edit_reference_exact.png').convert('RGBA')
            elif kind == 'delete':
                im = Image.open(UI_ASSETS / 'action_delete_reference_exact.png').convert('RGBA')
            else:
                return None
            im = im.resize((24, 24), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(im)
        except Exception: return None"""

code = re.sub(r"    def _make_row_icon\(self, kind\):.*?        return ImageTk\.PhotoImage\(im\)", new_make_row_icon, code, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
