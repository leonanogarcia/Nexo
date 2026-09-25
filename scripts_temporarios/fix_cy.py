with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("ov_left.create_image(cw0/2, ry + rh // 2, image=self._img_chk_on if is_checked else self._img_chk_off, anchor='center', tags=(f'c_{iid}',))",
                    "cy = ry + rh // 2\n                ov_left.create_image(cw0/2, cy, image=self._img_chk_on if is_checked else self._img_chk_off, anchor='center', tags=(f'c_{iid}',))")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
