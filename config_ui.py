with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update `_detect_icon` to support delete
detect_icon_old = """    def _detect_icon(self,text):
        if '+' in text or text.lstrip().startswith('+'): return 'plus'
        if '🕰' in text or '🕒' in text or 'clock' in text.lower(): return 'clock'
        if '🔄' in text or '🔀' in text: return 'convert'
        return None"""
detect_icon_new = """    def _detect_icon(self,text):
        if '+' in text or text.lstrip().startswith('+'): return 'plus'
        if '🕰' in text or '🕒' in text or 'clock' in text.lower(): return 'clock'
        if '🔄' in text or '🔀' in text: return 'convert'
        if '🗑' in text or 'Excluir' in text: return 'delete'
        return None"""
code = code.replace(detect_icon_old, detect_icon_new)
if detect_icon_new not in code:
    print("Warning: _detect_icon not updated")

# 2. Update `_make` to draw trash can
make_old = """                elif icon == 'clock':
                    d.ellipse([(sx-7*scale,sy-7*scale),(sx+7*scale,sy+7*scale)],outline=col,width=lw)
                    d.line([(sx,sy-4*scale),(sx,sy),(sx+3*scale,sy+3*scale)],fill=col,width=lw)
                elif icon == 'convert':"""
make_new = """                elif icon == 'clock':
                    d.ellipse([(sx-7*scale,sy-7*scale),(sx+7*scale,sy+7*scale)],outline=col,width=lw)
                    d.line([(sx,sy-4*scale),(sx,sy),(sx+3*scale,sy+3*scale)],fill=col,width=lw)
                elif icon == 'delete':
                    d.line([(sx-6*scale,sy-6*scale),(sx+6*scale,sy-6*scale)],fill=col,width=lw)
                    d.line([(sx-3*scale,sy-8*scale),(sx+3*scale,sy-8*scale)],fill=col,width=lw)
                    d.line([(sx-5*scale,sy-6*scale),(sx-4*scale,sy+7*scale)],fill=col,width=lw)
                    d.line([(sx+5*scale,sy-6*scale),(sx+4*scale,sy+7*scale)],fill=col,width=lw)
                    d.line([(sx-4*scale,sy+7*scale),(sx+4*scale,sy+7*scale)],fill=col,width=lw)
                elif icon == 'convert':"""
code = code.replace(make_old, make_new)
if make_new not in code:
    print("Warning: _make not updated")

# 3. Replace bulk delete buttons
code = code.replace(
    "self.mat_bulk_delete_btn=ttk.Button(bar, text='🗑️ Excluir', style='Soft.TButton', command=self.delete_selected_materials, state='disabled')",
    "self.mat_bulk_delete_btn=RoundedActionButton(bar, '🗑️ Excluir', self.delete_selected_materials, width=120, height=40, fill='#FEE2E2', hover='#FECACA', fg='#DC2626')"
)
code = code.replace(
    "self.rec_bulk_delete_btn=ttk.Button(bar,text='🗑️ Excluir',command=self.delete_selected_recipes,state='disabled',style='Soft.TButton')",
    "self.rec_bulk_delete_btn=RoundedActionButton(bar, '🗑️ Excluir', self.delete_selected_recipes, width=120, height=40, fill='#FEE2E2', hover='#FECACA', fg='#DC2626')"
)
code = code.replace(
    "self.prod_bulk_delete_btn=ttk.Button(bar,text='🗑️ Excluir',command=self.delete_selected_products,state='disabled',style='Soft.TButton')",
    "self.prod_bulk_delete_btn=RoundedActionButton(bar, '🗑️ Excluir', self.delete_selected_products, width=120, height=40, fill='#FEE2E2', hover='#FECACA', fg='#DC2626')"
)

# 4. Fix Tooltip background
code = code.replace(
    "trans_color = '#FF00FF'\n            try: tip.attributes('-transparentcolor', trans_color)\n            except Exception: pass\n            \n            tip.configure(bg=trans_color)\n            tip.geometry(f'+{tx}+{ty}')\n            \n            panel = RoundedPanel(tip, fill='#1F2633', border='', radius=16, bg=trans_color)",
    "trans_color = getattr(self.winfo_toplevel(), 'colors', {}).get('bg', '#F7F9FC')\n            tip.configure(bg=trans_color)\n            tip.geometry(f'+{tx}+{ty}')\n            \n            panel = RoundedPanel(tip, fill='#1F2633', border='', radius=16, bg=trans_color)"
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
