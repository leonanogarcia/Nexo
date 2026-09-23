import re

with open('main.py', 'rb') as f:
    content = f.read().decode('utf-8')

old_refresh_all = """    def refresh_all(self):
        self.refresh_materials()
        self.refresh_recipes()
        self.refresh_products()
        if hasattr(self,'refresh_general'): self.after_idle(self.refresh_general)"""

new_refresh_all = """    def refresh_all(self):
        self._garbage_collect()
        self.refresh_materials()
        self.refresh_recipes()
        self.refresh_products()
        if hasattr(self,'refresh_general'): self.after_idle(self.refresh_general)
        
    def _garbage_collect(self):
        with db() as c:
            # Delete materials that are archived AND not used anywhere
            c.execute('''DELETE FROM materials WHERE archived=1 AND id NOT IN (SELECT material_id FROM base_recipe_items) AND id NOT IN (SELECT ref_id FROM product_items WHERE item_type='MATERIAL')''')
            # Delete recipes that are archived AND not used anywhere
            c.execute('''DELETE FROM base_recipes WHERE archived=1 AND id NOT IN (SELECT ref_id FROM product_items WHERE item_type='RECIPE_BASE')''')
            # Products don't have dependents yet, so if archived=1, just delete
            c.execute('''DELETE FROM products WHERE archived=1''')
"""

content = content.replace(old_refresh_all, new_refresh_all)

with open('main.py', 'wb') as f:
    f.write(content.encode('utf-8'))
print('Patched garbage collection')
