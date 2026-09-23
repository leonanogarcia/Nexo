import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# We need to find the lines where mat_status is packed, and where mat_search_wrap is created.
# Current code in main.py looks like:
'''
        self.mat_search=tk.StringVar(); self.mat_search.trace_add('write',lambda *a:self.refresh_materials())
        
        self.mat_status = tk.StringVar(value='Ativos')
        self.mat_status.trace_add('write', lambda *a: self.refresh_materials())
        self.mat_status_wrap = RoundedDropdown(bar, self.mat_status, ['Ativos', 'Inativos', 'Todos'], width=110)
        self.mat_status_wrap.pack(side='right', padx=14)
        
        self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,280)
'''

match = re.search(r'        self\.mat_status = tk\.StringVar\(value=\'Ativos\'\)\s*self\.mat_status\.trace_add\(\'write\', lambda \*a: self\.refresh_materials\(\)\)\s*self\.mat_status_wrap = RoundedDropdown\(bar, self\.mat_status, \[\'Ativos\', \'Inativos\', \'Todos\'\], width=110\)\s*self\.mat_status_wrap\.pack\(side=\'right\', padx=14\)\s*self\.mat_search_wrap=self\._styled_search_entry\(bar,self\.mat_search,280\)', text)

if match:
    old = match.group(0)
    new_code = """        self.mat_search_wrap=self._styled_search_entry(bar,self.mat_search,280)
        
        self.mat_status = tk.StringVar(value='Ativos')
        self.mat_status.trace_add('write', lambda *a: self.refresh_materials())
        self.mat_status_wrap = RoundedDropdown(bar, self.mat_status, ['Ativos', 'Inativos', 'Todos'], width=110)
        self.mat_status_wrap.pack(side='right', padx=14)"""
        
    text = text.replace(old, new_code)
    with open('main.py', 'wb') as f:
        f.write(text.encode('utf-8'))
    print('Patched order successfully')
else:
    print('Failed to patch order')
