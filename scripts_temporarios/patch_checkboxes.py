import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace tree.item
text = text.replace("tree.item(item, text='\\u2611' if item==iid else '\\u2610')", "tree.item(item, text='', image=self._img_chk_on if item==iid else self._img_chk_off)")
text = text.replace("tree.item(item, text='\\u2611' if item in checked else '\\u2610')", "tree.item(item, text='', image=self._img_chk_on if item in checked else self._img_chk_off)")
text = text.replace("tree.item(iid,text='\\u2610')", "tree.item(iid, text='', image=self._img_chk_off)")

# Replace tree.heading
text = text.replace("tree.heading('#0', text='\\u2611' if is_all_checked else '\\u2610')", "tree.heading('#0', text='', image=self._img_chk_on if is_all_checked else self._img_chk_off)")
text = text.replace("tree.heading('#0', text='\\u2610')", "tree.heading('#0', text='', image=self._img_chk_off)")

# Replace tree.insert for all modules
text = text.replace("text='\\u2610', values=tuple(r_list)+(status_str, '','',''), tags=() if is_active else ('inactive',)", "text='', image=self._img_chk_off, values=tuple(r_list)+(status_str, '','',''), tags=() if is_active else ('inactive',)")
text = text.replace("text='\\u2610', values=(r['code'],name_disp,fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'','',''), tags=() if is_active else ('inactive',)", "text='', image=self._img_chk_off, values=(r['code'],name_disp,fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'','',''), tags=() if is_active else ('inactive',)")
text = text.replace("text='\\u2610', values=(r['code'],name_disp,w_disp,fmt(cost),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-','','',''), tags=() if is_active else ('inactive',)", "text='', image=self._img_chk_off, values=(r['code'],name_disp,w_disp,fmt(cost),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-','','',''), tags=() if is_active else ('inactive',)")


# Fix canvas header text checkmarks!
# We don't have self._img_chk_on directly in the canvas redraw function without passing it, but it's a method so we have `self`.
# ov_left.create_text(cw_chk/2, h/2, text=txt, fill=chk_color, font=('Segoe UI', 13), tags=('header_chk',))
# ov_left.create_image(cw_chk/2, h/2, image=self._img_chk_on if is_checked else self._img_chk_off, tags=('header_chk',))

text = re.sub(
    r"txt = '\\u2611' if is_checked else '\\u2610'\n\s*ov_left\.create_text\(cw_chk/2, h/2, text=txt, fill=chk_color, font=\('Segoe UI', 13\), tags=\('header_chk', \)\)",
    r"ov_left.create_image(cw_chk/2, h/2, image=self._img_chk_on if is_checked else self._img_chk_off, tags=('header_chk', ))",
    text
)
text = re.sub(
    r"txt = '\\u2611' if is_checked else '\\u2610'\n\s*ov_left\.create_text\(cw_chk/2, h/2, text=txt, fill=chk_color, font=\('Segoe UI', 13\), tags=\('header_chk',\)\)",
    r"ov_left.create_image(cw_chk/2, h/2, image=self._img_chk_on if is_checked else self._img_chk_off, tags=('header_chk',))",
    text
)
text = re.sub(
    r"txt_chk = '\\u2611' if is_all_checked else '\\u2610'\n\s*c\.create_text\(cw_chk/2, h/2, text=txt_chk, fill=chk_color, font=\('Segoe UI', 13\), tags=\('header_chk',\)\)",
    r"c.create_image(cw_chk/2, h/2, image=self._img_chk_on if is_all_checked else self._img_chk_off, tags=('header_chk',))",
    text
)


with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
