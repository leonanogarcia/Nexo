import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace("            self.mat_tree.tag_configure", "        self.mat_tree.tag_configure")
code = code.replace("            self.rec_tree.tag_configure", "        self.rec_tree.tag_configure")
code = code.replace("            self.prod_tree.tag_configure", "        self.prod_tree.tag_configure")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
