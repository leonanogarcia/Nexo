import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Fix rec_header `#0` width
old_rec_cw0 = """            try: cw0=int(self.rec_tree.column('#0','width'))
            except Exception: cw0=60"""
new_rec_cw0 = """            cw0 = 60"""
text = text.replace(old_rec_cw0, new_rec_cw0)

old_rec_cw = """            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.rec_tree.column(col,'width'))
                except Exception: cw=0
                if col in ('#0', '#6', '#7'):"""
new_rec_cw = """            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.rec_tree.column(col,'width'))
                except Exception: cw=0
                if col == '#0': cw = 60
                if col in ('#0', '#6', '#7'):"""
text = text.replace(old_rec_cw, new_rec_cw)


# Fix prod_header `#0` width
old_prod_cw0 = """            try: cw0=int(self.prod_tree.column('#0','width'))
            except Exception: cw0=60"""
new_prod_cw0 = """            cw0 = 60"""
text = text.replace(old_prod_cw0, new_prod_cw0)

old_prod_cw = """            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.prod_tree.column(col,'width'))
                except Exception: cw=0
                if col in ('#0', '#7', '#8'):"""
new_prod_cw = """            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.prod_tree.column(col,'width'))
                except Exception: cw=0
                if col == '#0': cw = 60
                if col in ('#0', '#7', '#8'):"""
text = text.replace(old_prod_cw, new_prod_cw)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched cw0 to 60")
