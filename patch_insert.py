import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Fix refresh_recipes insert values
old_rec_ins = "values=(r['code'],name_disp,fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'','')"
new_rec_ins = "values=(r['code'],name_disp,fmt_num(r['yield_qty']),r['yield_unit'] or '-',fmt(cost),'','','')"
text = text.replace(old_rec_ins, new_rec_ins)

old_rec_ins2 = "values=('',f'↳ {comp_name}',fmt_num(comp['qty']),comp['unit'],'-','','')"
new_rec_ins2 = "values=('',f'↳ {comp_name}',fmt_num(comp['qty']),comp['unit'],'-','','','')"
text = text.replace(old_rec_ins2, new_rec_ins2)

# Fix refresh_products insert values
old_prod_ins = "values=(r['code'],name_disp,w_disp,fmt(cost),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-','','')"
new_prod_ins = "values=(r['code'],name_disp,w_disp,fmt(cost),fmt(r['sale_price']),f'{margin:.1f}%' if margin is not None else '-','','','')"
text = text.replace(old_prod_ins, new_prod_ins)

old_prod_ins2 = "values=('',f'↳ {n}',fmt_num(comp['qty']),comp['unit'],'-','-','','')"
new_prod_ins2 = "values=('',f'↳ {n}',fmt_num(comp['qty']),comp['unit'],'-','-','','','')"
text = text.replace(old_prod_ins2, new_prod_ins2)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched insert values for the extra dummy column shift!")
