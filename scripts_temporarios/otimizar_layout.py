import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Find the material_form block
start_str = "    def material_form(self, edit_id=None):"
end_str = "        act=d.action_host"

start_idx = text.find(start_str)
end_idx = text.find(end_str, start_idx)

original_block = text[start_idx:end_idx]

new_block = """    def material_form(self, edit_id=None):
        is_edit = edit_id is not None
        with db() as c:
            existing = c.execute('SELECT * FROM materials WHERE id=?', (edit_id,)).fetchone() if is_edit else None
        d = Modal(self, 'Editar item' if is_edit else 'Novo item', '620x360')
        vars = {k: tk.StringVar() for k in ('name','brand','qty','unit','value','category','date','barcode')}
        if existing:
            for k in vars:
                if k == 'date': vars[k].set(date.today().isoformat())
                elif k == 'qty': vars[k].set(fmt_num(existing['purchase_qty']))
                elif k == 'value': vars[k].set(fmt(existing['purchase_value']))
                elif k == 'unit': vars[k].set(existing['purchase_unit'])
                elif k == 'category': vars[k].set(existing['category'] or 'Comestível')
                elif k == 'name': vars[k].set(existing['name'])
                elif k == 'brand': vars[k].set(existing['brand'] or '')
                elif k == 'barcode': vars[k].set(existing['barcode'] or '')
        else:
            vars['unit'].set(''); vars['category'].set('Comestível'); vars['date'].set(date.today().isoformat())
        form = tk.Frame(d, bg=d.cget('bg'), padx=24, pady=20); form.pack(fill='both', expand=True)
        try: text_col = self.colors.get('text', '#18223A')
        except: text_col = '#18223A'
        
        def make_field(parent, label, key, w_chars, w_pixels=None):
            wrap = tk.Frame(parent, bg=d.cget('bg'))
            tk.Label(wrap, text=label, bg=d.cget('bg'), fg=text_col, font=('Segoe UI', 9)).pack(anchor='w', padx=4, pady=(1,0))
            if key == 'unit':
                wd = RoundedDropdown(wrap, vars[key], UNITS, width=w_pixels or 140, align='left')
            elif key == 'category':
                wd = RoundedDropdown(wrap, vars[key], ['Comestível','Não comestível','Doação'], width=w_pixels or 180, align='left')
            elif key == 'value':
                wd = masked_money_entry(wrap, vars[key], width=w_chars)
            elif key == 'qty':
                wd = numeric_entry(wrap, vars[key], width=w_chars)
            else:
                wd, _ = rounded_entry(wrap, vars[key], width=w_chars)
            wd.pack(fill='x', expand=True, padx=4, pady=(0,8))
            return wrap

        r1 = tk.Frame(form, bg=d.cget('bg')); r1.pack(fill='x', pady=4)
        make_field(r1, 'Nome *', 'name', 38).pack(side='left', fill='x', expand=True)
        make_field(r1, 'Marca', 'brand', 18).pack(side='left', fill='x')

        r2 = tk.Frame(form, bg=d.cget('bg')); r2.pack(fill='x', pady=4)
        make_field(r2, 'Quantidade *', 'qty', 12).pack(side='left')
        make_field(r2, 'Unidade *', 'unit', 10, w_pixels=140).pack(side='left')
        make_field(r2, 'Valor da compra *', 'value', 16).pack(side='left', fill='x', expand=True)

        r3 = tk.Frame(form, bg=d.cget('bg')); r3.pack(fill='x', pady=4)
        make_field(r3, 'Categoria *', 'category', 14, w_pixels=180).pack(side='left')
        make_field(r3, 'Cód. Barras', 'barcode', 16).pack(side='left', fill='x', expand=True)
        make_field(r3, 'Data *', 'date', 14).pack(side='left')
        
        def save():
            try:
                name = vars['name'].get().strip(); brand = vars['brand'].get().strip(); unit = vars['unit'].get().strip(); category = vars['category'].get().strip(); barcode = vars['barcode'].get().strip()
                if not name: raise ValueError('O campo "Nome" é obrigatório.')
                if not unit: raise ValueError('O campo "Unidade" é obrigatório.')
                if not category: raise ValueError('O campo "Categoria" é obrigatório.')
                qty = to_float(vars['qty'].get(),'Quantidade')
                value = money_to_float(vars['value'].get(),'Valor da compra')
                if qty <= 0: raise ValueError('A Quantidade deve ser maior que zero.')
                if value < 0: raise ValueError('O Valor da compra não pode ser negativo.')
                if value == 0 and category != 'Doação': raise ValueError('Valor zero só é permitido para itens da categoria Doação.')
                purchase_date = vars['date'].get().strip()
                if not purchase_date: raise ValueError('O campo "Data" é obrigatório.')
                if is_edit:
                    with db() as c: before = dict(c.execute('SELECT * FROM materials WHERE id=?', (edit_id,)).fetchone())
                    self.ask_edit_reason('INSUMO', edit_id, before, {'name':name,'purchase_qty':qty,'purchase_unit':unit,'purchase_value':value,'brand':brand,'category':category,'barcode':barcode})
                with db() as c:
                    if is_edit:
                        mid = edit_id
                        c.execute('UPDATE materials SET name=?,purchase_qty=?,purchase_unit=?,purchase_value=?,brand=?,category=?,barcode=?,updated_at=? WHERE id=?',
                                  (name,qty,unit,value,brand,category,barcode,now_iso(),edit_id))
                    else:
                        code = next_code('materials','INS')
                        cur = c.execute('INSERT INTO materials(code,name,purchase_qty,purchase_unit,purchase_value,brand,category,barcode,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',
                                         (code,name,qty,unit,value,brand,category,barcode,now_iso()))
                        mid = cur.lastrowid
                        c.execute('INSERT INTO purchases(material_id,qty,unit,value,brand,purchase_date) VALUES(?,?,?,?,?,?)', (mid,qty,unit,value,brand,purchase_date))
                snapshot_costs(); d.destroy(); self.refresh_all(); self.notify('Insumo salvo com sucesso.')
            except Exception as e: safe_error(d,'Não foi possível salvar o item',e)
"""

text = text[:start_idx] + new_block + text[end_idx:]

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated material_form layout successfully!")
