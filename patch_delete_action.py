import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Fix lambda for materials
text = text.replace(
    "lambda: self._run_normal_action(self.mat_tree, self.delete_selected_materials)",
    "lambda: self.delete_selected_materials()"
)

# Fix lambda for recipes
text = text.replace(
    "lambda: self._run_normal_action(self.rec_tree, self.delete_selected_recipes)",
    "lambda: self.delete_selected_recipes()"
)

# Fix lambda for products
text = text.replace(
    "lambda: self._run_normal_action(self.prod_tree, self.delete_selected_products)",
    "lambda: self.delete_selected_products()"
)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched click action")
