import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# 1. FIX CADASTRO
old_mat_cols = "columns=('code','name','brand','qty','unit','value','category','date','mod_date','status','edit','delete','options','dummy')"
new_mat_cols = "columns=('code','name','brand','qty','unit','value','category','date','mod_date','status','dummy','edit','delete','options')"
text = text.replace(old_mat_cols, new_mat_cols)

old_mat_specs = "self._mat_header_specs=[('code','Código',100),('name','Item',220),('brand','Marca',150),('qty','Quantidade',110),('unit','Un.',65),('value','Valor',100),('category','Categoria',130),('date','Data de criação',135),('mod_date','Última modificação',135),('status','Status',90),('edit','',30),('delete','',30),('options','',30)]"
new_mat_specs = "self._mat_header_specs=[('code','Código',100),('name','Item',220),('brand','Marca',150),('qty','Quantidade',110),('unit','Un.',65),('value','Valor',100),('category','Categoria',130),('date','Data de criação',135),('mod_date','Última modificação',135),('status','Status',90),('dummy','',0),('edit','',30),('delete','',30),('options','',30)]"
text = text.replace(old_mat_specs, new_mat_specs)

old_mat_skip = "if col in ('#0', '#11', '#12', '#13'):"
new_mat_skip = "if col == '#0': cw = 60\n                if col in ('#0', '#12', '#13', '#14'):"
text = text.replace(old_mat_skip, new_mat_skip)

old_mat_right = """            try:
                cw11 = int(self.mat_tree.column('#11','width'))
                cw12 = int(self.mat_tree.column('#12','width'))
                cw13 = int(self.mat_tree.column('#13','width'))
                fixed_right_w = cw11 + cw12 + cw13"""
new_mat_right = """            try:
                cw12 = int(self.mat_tree.column('#12','width'))
                cw13 = int(self.mat_tree.column('#13','width'))
                cw14 = int(self.mat_tree.column('#14','width'))
                fixed_right_w = cw12 + cw13 + cw14"""
text = text.replace(old_mat_right, new_mat_right)

old_mat_cw11_cw12 = """                cx = start_x
                if cw11 > 0:
                    img=self._mat_header_imgs.get('edit')
                    if img: c.create_image(cx+cw11/2, h/2, image=img, anchor='center')
                    cx += cw11
                if cw12 > 0:
                    img=self._mat_header_imgs.get('delete')
                    if img: c.create_image(cx+cw12/2, h/2, image=img, anchor='center')"""
new_mat_cw11_cw12 = """                cx = start_x
                if cw12 > 0:
                    img=self._mat_header_imgs.get('edit')
                    if img: c.create_image(cx+cw12/2, h/2, image=img, anchor='center')
                    cx += cw12
                if cw13 > 0:
                    img=self._mat_header_imgs.get('delete')
                    if img: c.create_image(cx+cw13/2, h/2, image=img, anchor='center')"""
text = text.replace(old_mat_cw11_cw12, new_mat_cw11_cw12)


# 2. FIX RECEITAS
old_rec_cols = "columns=('code','name','yield','unit','cost','edit','delete','dummy')"
new_rec_cols = "columns=('code','name','yield','unit','cost','dummy','edit','delete')"
text = text.replace(old_rec_cols, new_rec_cols)

old_rec_specs = "self._rec_header_specs=[('code','Código',100),('name','Receita',380),('yield','Rendimento',120),('unit','Un.',65),('cost','Custo total',120),('edit','',30),('delete','',30)]"
new_rec_specs = "self._rec_header_specs=[('code','Código',100),('name','Receita',380),('yield','Rendimento',120),('unit','Un.',65),('cost','Custo total',120),('dummy','',0),('edit','',30),('delete','',30)]"
text = text.replace(old_rec_specs, new_rec_specs)

old_rec_skip = "if col in ('#0', '#6', '#7'):"
new_rec_skip = "if col in ('#0', '#7', '#8'):"
text = text.replace(old_rec_skip, new_rec_skip)

old_rec_right = """            try: cw6=int(self.rec_tree.column('#6','width'))
            except: cw6=0
            try: cw7=int(self.rec_tree.column('#7','width'))
            except: cw7=0
            total_r = cw6 + cw7"""
new_rec_right = """            try: cw7=int(self.rec_tree.column('#7','width'))
            except: cw7=0
            try: cw8=int(self.rec_tree.column('#8','width'))
            except: cw8=0
            total_r = cw7 + cw8"""
text = text.replace(old_rec_right, new_rec_right)


# 3. FIX PRODUTOS
old_prod_cols = "columns=('code','name','weight','cost','price','margin','edit','delete','dummy')"
new_prod_cols = "columns=('code','name','weight','cost','price','margin','dummy','edit','delete')"
text = text.replace(old_prod_cols, new_prod_cols)

old_prod_specs = "self._prod_header_specs=[('code','Código',100),('name','Produto',380),('weight','Peso/Rendimento',120),('cost','Custo total',110),('price','Preço',110),('margin','Margem',90),('edit','',30),('delete','',30)]"
new_prod_specs = "self._prod_header_specs=[('code','Código',100),('name','Produto',380),('weight','Peso/Rendimento',120),('cost','Custo total',110),('price','Preço',110),('margin','Margem',90),('dummy','',0),('edit','',30),('delete','',30)]"
text = text.replace(old_prod_specs, new_prod_specs)

old_prod_skip = "if col in ('#0', '#7', '#8'):"
new_prod_skip = "if col in ('#0', '#8', '#9'):"
text = text.replace(old_prod_skip, new_prod_skip)

old_prod_right = """            try: cw7=int(self.prod_tree.column('#7','width'))
            except: cw7=0
            try: cw8=int(self.prod_tree.column('#8','width'))
            except: cw8=0
            total_r = cw7 + cw8"""
new_prod_right = """            try: cw8=int(self.prod_tree.column('#8','width'))
            except: cw8=0
            try: cw9=int(self.prod_tree.column('#9','width'))
            except: cw9=0
            total_r = cw8 + cw9"""
text = text.replace(old_prod_right, new_prod_right)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched column layout to put dummy before actions!")
