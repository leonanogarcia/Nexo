import re

with open('main.py', 'rb') as f:
    content = f.read().decode('utf-8')

# Fix _styled_search_entry
old_styled = """    def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)
        # Search is fixed on the right, but we give it a min size by NOT propagating
        wrap.pack(side='right',padx=(14,0),fill='none',expand=False)
        return wrap"""

new_styled = """    def _styled_search_entry(self, parent, textvariable, width=280):
        # We enforce a minimum width in pixels, not characters, so width must be large
        w = width if width > 100 else 280
        wrap=RoundedEntry(parent,textvariable,width=w,height=40)
        wrap.pack(side='right',padx=(14,0),fill='none',expand=False)
        return wrap"""

content = content.replace(old_styled, new_styled)

# Also fix the usages in cadastro, recipes_page, products_page
content = content.replace("self._styled_search_entry(bar,self.mat_search,22)", "self._styled_search_entry(bar,self.mat_search,280)")
content = content.replace("self._styled_search_entry(bar,self.rec_search,22)", "self._styled_search_entry(bar,self.rec_search,280)")
content = content.replace("self._styled_search_entry(bar,self.prod_search,22)", "self._styled_search_entry(bar,self.prod_search,280)")

with open('main.py', 'wb') as f:
    f.write(content.encode('utf-8'))
print('Fixed search bar')
