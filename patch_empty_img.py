import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Recipe Empty Overlay
old_rec_empty = "        self.rec_empty_overlay = tk.Label(table_host, text='Nenhuma receita cadastrada.\\nClique em + Nova Receita para adicionar a primeira receita.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"

new_rec_empty = """        try:
            from PIL import Image, ImageTk
            import pathlib
            UI_ASSETS = pathlib.Path(__file__).parent / 'assets'
            img_path = UI_ASSETS / 'empty_state_reference_exact.png'
            self._rec_empty_img = ImageTk.PhotoImage(Image.open(img_path))
            
            self.rec_empty_overlay = tk.Frame(table_host, bg=self.colors['field'])
            inner = tk.Frame(self.rec_empty_overlay, bg=self.colors['field'])
            inner.place(relx=0.5, rely=0.5, anchor='center')
            
            l_img = tk.Label(inner, image=self._rec_empty_img, bg=self.colors['field'])
            l_img.pack(pady=(0, 10))
            
            l_title = tk.Label(inner, text='Nenhuma receita cadastrada.', bg=self.colors['field'], fg='#687796', font=('Segoe UI', 11, 'bold'))
            l_title.pack(pady=(0, 4))
            
            l_sub = tk.Label(inner, text='Clique em + Nova Receita para adicionar a primeira receita.', bg=self.colors['field'], fg='#8A99B5', font=('Segoe UI', 9))
            l_sub.pack()
        except Exception:
            self.rec_empty_overlay = tk.Label(table_host, text='Nenhuma receita cadastrada.\\nClique em + Nova Receita para adicionar a primeira receita.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"""

text = text.replace(old_rec_empty, new_rec_empty)


# Product Empty Overlay
old_prod_empty = "        self.prod_empty_overlay = tk.Label(table_host, text='Nenhum produto cadastrado.\\nClique em + Novo Produto para adicionar o primeiro produto.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"

new_prod_empty = """        try:
            from PIL import Image, ImageTk
            import pathlib
            UI_ASSETS = pathlib.Path(__file__).parent / 'assets'
            img_path = UI_ASSETS / 'empty_state_reference_exact.png'
            self._prod_empty_img = ImageTk.PhotoImage(Image.open(img_path))
            
            self.prod_empty_overlay = tk.Frame(table_host, bg=self.colors['field'])
            inner = tk.Frame(self.prod_empty_overlay, bg=self.colors['field'])
            inner.place(relx=0.5, rely=0.5, anchor='center')
            
            l_img = tk.Label(inner, image=self._prod_empty_img, bg=self.colors['field'])
            l_img.pack(pady=(0, 10))
            
            l_title = tk.Label(inner, text='Nenhum produto cadastrado.', bg=self.colors['field'], fg='#687796', font=('Segoe UI', 11, 'bold'))
            l_title.pack(pady=(0, 4))
            
            l_sub = tk.Label(inner, text='Clique em + Novo Produto para adicionar o primeiro produto.', bg=self.colors['field'], fg='#8A99B5', font=('Segoe UI', 9))
            l_sub.pack()
        except Exception:
            self.prod_empty_overlay = tk.Label(table_host, text='Nenhum produto cadastrado.\\nClique em + Novo Produto para adicionar o primeiro produto.', bg=self.colors['field'], fg=self.colors['muted'], font=('Segoe UI', 10))"""

text = text.replace(old_prod_empty, new_prod_empty)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Upgraded empty overlays to match Cadastro with PIL Image!")
