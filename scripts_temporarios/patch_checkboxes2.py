import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Tree items
text = text.replace("tree.item(item, text='☑' if item==iid else '☐')", "tree.item(item, text='', image=self._img_chk_on if item==iid else self._img_chk_off)")
text = text.replace("tree.item(item, text='☑' if item in checked else '☐')", "tree.item(item, text='', image=self._img_chk_on if item in checked else self._img_chk_off)")
text = text.replace("tree.item(iid,text='☐')", "tree.item(iid, text='', image=self._img_chk_off)")

# Headings
text = text.replace("tree.heading('#0', text='☑' if is_all_checked else '☐')", "tree.heading('#0', text='', image=self._img_chk_on if is_all_checked else self._img_chk_off)")
text = text.replace("tree.heading('#0', text='☐')", "tree.heading('#0', text='', image=self._img_chk_off)")

# Inserts
text = text.replace("text='☐', values=tuple(r_list)+(status_str, '','','')", "text='', image=self._img_chk_off, values=tuple(r_list)+(status_str, '','','')")
text = text.replace("text='☐', values=(r['code'],name_disp,fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'','','')", "text='', image=self._img_chk_off, values=(r['code'],name_disp,fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'','','')")
text = text.replace("text='☐', values=(r['code'],name_disp,w_disp,fmt(cost),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-','','','')", "text='', image=self._img_chk_off, values=(r['code'],name_disp,w_disp,fmt(cost),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-','','','')")


# Headers
text = re.sub(
    r"txt = '☑' if is_checked else '☐'\n\s*ov_left\.create_text\(cw_chk/2, h/2, text=txt, fill=chk_color, font=\('Segoe UI', 13\), tags=\('header_chk',\)\)",
    r"ov_left.create_image(cw_chk/2, h/2, image=self._img_chk_on if is_checked else self._img_chk_off, tags=('header_chk',))",
    text
)
text = re.sub(
    r"txt_chk = '☑' if is_all_checked else '☐'\n\s*c\.create_text\(cw_chk/2, h/2, text=txt_chk, fill=chk_color, font=\('Segoe UI', 13\), tags=\('header_chk',\)\)",
    r"c.create_image(cw_chk/2, h/2, image=self._img_chk_on if is_all_checked else self._img_chk_off, tags=('header_chk',))",
    text
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
