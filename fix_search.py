import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_search = """    def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)
        wrap.pack(side='left',padx=(14,0))
        return wrap.entry"""

new_search = """    def _styled_search_entry(self, parent, textvariable, width=28):
        wrap=RoundedEntry(parent,textvariable,width=width,height=40)
        wrap.pack(side='right',padx=(14,0),fill='none',expand=False)
        return wrap"""

code = code.replace(old_search, new_search)

# Also fix the reference in cadastro since it now returns wrap
code = code.replace(
    "self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,22)\n        self.mat_search_wrap.pack_configure(side='right',padx=(14,0),fill='none',expand=False)",
    "self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,22)"
)

# And in recipes_page, products_page, etc. if they use _styled_search_entry:
# Let's check if they were using wrap.entry or wrap.
# Since I reverted to old main.py for missing_block, recipes and products were NOT reverted.
# They might be expecting `wrap` instead of `wrap.entry`. We will see.

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
