import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Materials
text = re.sub(
    r"self\.mat_bulk_delete_btn=RoundedActionButton\(bar,\s*'.*?Excluir',",
    r"self.mat_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir',",
    text
)
text = text.replace("self.delete_selected_materials), width=120, height=40, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')", "self.delete_selected_materials), width=105, height=40, fill='#FEF2F2', hover='#FEE2E2', fg='#991B1B')")

# Recipes
text = re.sub(
    r"self\.rec_bulk_delete_btn=RoundedActionButton\(bar,\s*'.*?Excluir',",
    r"self.rec_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir',",
    text
)
text = text.replace("self.delete_selected_recipes), width=120, height=40, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')", "self.delete_selected_recipes), width=105, height=40, fill='#FEF2F2', hover='#FEE2E2', fg='#991B1B')")

# Products
text = re.sub(
    r"self\.prod_bulk_delete_btn=RoundedActionButton\(bar,\s*'.*?Excluir',",
    r"self.prod_bulk_delete_btn=RoundedActionButton(bar, '<delete> Excluir',",
    text
)
text = text.replace("self.delete_selected_products), width=120, height=40, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')", "self.delete_selected_products), width=105, height=40, fill='#FEF2F2', hover='#FEE2E2', fg='#991B1B')")

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Buttons fully replaced!")
