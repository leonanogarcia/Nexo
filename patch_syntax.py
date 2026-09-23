with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

bad_rec = "self.rec_empty_overlay = tk.Label(table_host, text='Nenhuma receita cadastrada.\\nClique em + Nova Receita para adicionar a primeira receita.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"
good_rec = "self.rec_empty_overlay = tk.Label(table_host, text='Nenhuma receita cadastrada.\\nClique em + Nova Receita para adicionar a primeira receita.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"

bad_prod = "self.prod_empty_overlay = tk.Label(table_host, text='Nenhum produto cadastrado.\\nClique em + Novo Produto para adicionar o primeiro produto.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"
good_prod = "self.prod_empty_overlay = tk.Label(table_host, text='Nenhum produto cadastrado.\\nClique em + Novo Produto para adicionar o primeiro produto.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"

# I need to fix the actual file content, which currently has a real newline character!
text = text.replace("text='Nenhuma receita cadastrada.\nClique em", "text='Nenhuma receita cadastrada.\\nClique em")
text = text.replace("text='Nenhum produto cadastrado.\nClique em", "text='Nenhum produto cadastrado.\\nClique em")

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Fixed syntax error!")
