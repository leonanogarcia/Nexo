import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(
    r"txt = '☑' if is_checked else '☐'\n\s*color = [^\n]+\n\s*(?:if [^\n]+\n\s*)?cy = ry \+ rh // 2\n\s*ov_left\.create_text\(cw0/2, cy, text=txt, [^\)]+\)",
    r"ov_left.create_image(cw0/2, ry + rh // 2, image=self._img_chk_on if is_checked else self._img_chk_off, anchor='center', tags=(f'c_{iid}',))",
    text
)

text = re.sub(
    r"txt_chk = '☑' if is_all_checked else '☐'\n\s*chk_color = [^\n]+\n\s*(?:if [^\n]+\n\s*)?c\.create_text\(cw_chk/2, h/2, text=txt_chk, [^\)]+\)",
    r"c.create_image(cw_chk/2, h/2, image=self._img_chk_on if is_all_checked else self._img_chk_off, anchor='center', tags=('header_chk',))",
    text
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Canvas patched successfully")
