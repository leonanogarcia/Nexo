import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Ajustar RoundedDropdown (altura)
text = text.replace("height=40, align='center'", "height=32, align='center'")

# 2. Ajustar rounded_entry (altura, raio e padding)
text = text.replace("wrap.config(width=px_w, height=40)", "wrap.config(width=px_w, height=32)")
text = text.replace("radius=20, bg=parent_bg)", "radius=16, bg=parent_bg)")
text = text.replace("padx=(16,16), pady=9)", "padx=(16,16), pady=4)")

# 3. Remover altura fixa e pack_propagate do Modal
text = text.replace("self.action_host=tk.Frame(self,bg=self.cget('bg'),height=58)", "self.action_host=tk.Frame(self,bg=self.cget('bg'))")
text = text.replace("self.action_host.pack_propagate(False)", "# self.action_host.pack_propagate(False)")

# 4. Injetar a marca d'água no material_form e ajustar a altura para 290
text = text.replace("Modal(self, 'Editar item' if is_edit else 'Novo item', '620x360')", "Modal(self, 'Editar item' if is_edit else 'Novo item', '620x290')")
text = text.replace("Modal(self, 'Editar item' if is_edit else 'Novo item', '620x310')", "Modal(self, 'Editar item' if is_edit else 'Novo item', '620x290')")

# Procurar o bloco de botões do material_form para injetar a marca d'água
form_buttons = """        act=d.action_host
        right=tk.Frame(act,bg=d.cget('bg'));right.pack(side='right',fill='y')
        RoundedActionButton(right,'Salvar',save,width=92,height=38,fill='#F28C28',hover='#D96F0B').pack(side='left',padx=(6,0),pady=7)
        RoundedActionButton(right,'Cancelar',d.destroy,width=92,height=38,fill='#6B7280',hover='#4B5563').pack(side='left',padx=(6,0),pady=7)"""

form_buttons_new = """        act=d.action_host
        left=tk.Frame(act,bg=d.cget('bg'));left.pack(side='left',fill='y')
        try: muted_col = self.colors.get('muted', '#687796')
        except: muted_col = '#687796'
        tk.Label(left, text='* campo obrigatório', bg=d.cget('bg'), fg=muted_col, font=('Segoe UI', 9, 'italic')).pack(side='left', padx=16, pady=7)
        
        right=tk.Frame(act,bg=d.cget('bg'));right.pack(side='right',fill='y')
        RoundedActionButton(right,'Salvar',save,width=92,height=38,fill='#F28C28',hover='#D96F0B').pack(side='left',padx=(6,0),pady=7)
        RoundedActionButton(right,'Cancelar',d.destroy,width=92,height=38,fill='#6B7280',hover='#4B5563').pack(side='left',padx=(6,0),pady=7)"""

text = text.replace(form_buttons, form_buttons_new)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Ajustes 100% aplicados!")
