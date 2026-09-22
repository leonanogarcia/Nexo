import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add horizontal scrollbar style
style_code = """        self.style.configure('Vertical.TScrollbar', background=btn_bg, troughcolor=bg, bordercolor=bg, arrowcolor=('#91A5CC' if dark else '#7B879A'))
        self.style.configure('Horizontal.TScrollbar', background=btn_bg, troughcolor=bg, bordercolor=bg, arrowcolor=('#91A5CC' if dark else '#7B879A'), arrowsize=8, width=8)"""
code = code.replace("        self.style.configure('Vertical.TScrollbar', background=btn_bg, troughcolor=bg, bordercolor=bg, arrowcolor=('#91A5CC' if dark else '#7B879A'))", style_code)

# 2. Add separator lines in cadastro's redraw_mat_header
old_redraw_mat = """                elif col=='#13':
                    pass
                else:
                    align = 'w' if col in ('#1', '#2', '#3') else 'center'
                    anchor_x = x0+12 if align == 'w' else x0+cw/2
                    c.create_text(anchor_x,h/2,text=txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor=align)
                x0+=cw"""
new_redraw_mat = """                elif col=='#13':
                    pass
                else:
                    align = 'w' if col in ('#1', '#2', '#3') else 'center'
                    anchor_x = x0+12 if align == 'w' else x0+cw/2
                    c.create_text(anchor_x,h/2,text=txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor=align)
                
                # Add separator line
                if col not in ('#0', '#11', '#12', '#13'):
                    c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                x0+=cw"""
code = code.replace(old_redraw_mat, new_redraw_mat)

# 3. Add horizontal scrollbar to cadastro
old_mat_pack = """        self.mat_tree=ttk.Treeview(table_host,columns=('code','name','brand','qty','unit','value','category','date','mod_date','status','edit','delete','options'),show='tree')
        self.mat_tree.tag_configure('inactive', foreground='#9AA9BF')
        self.mat_tree.column('#0',width=60,minwidth=60,stretch=False)
        
        for k,w in [('code',100),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135),('status',90),('edit',40),('delete',40),('options',40)]:
            self.mat_tree.column(k,width=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date','status') else 'w',stretch=False)
            
        self.mat_tree.pack(fill='both',expand=True)"""
new_mat_pack = """        self.mat_tree=ttk.Treeview(table_host,columns=('code','name','brand','qty','unit','value','category','date','mod_date','status','edit','delete','options'),show='tree')
        self.mat_tree.tag_configure('inactive', foreground='#9AA9BF')
        self.mat_tree.column('#0',width=60,minwidth=60,stretch=False)
        
        for k,w in [('code',100),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135),('status',90),('edit',40),('delete',40),('options',40)]:
            self.mat_tree.column(k,width=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date','status') else 'w',stretch=False)
            
        self.mat_hsb = ttk.Scrollbar(table_host, orient='horizontal', command=self.mat_tree.xview, style='Horizontal.TScrollbar')
        self.mat_tree.configure(xscrollcommand=self.mat_hsb.set)
        self.mat_hsb.pack(side='bottom', fill='x', pady=(2,0))
        self.mat_tree.pack(fill='both',expand=True)"""
code = code.replace(old_mat_pack, new_mat_pack)

# 4. Add horizontal scrollbar to recipes_page
old_rec_pack = """        for k in ('edit','delete','options'):
            self.rec_tree.column(k,width=40,anchor='center',stretch=False)
        self.rec_tree.pack(fill='both',expand=True)"""
new_rec_pack = """        for k in ('edit','delete','options'):
            self.rec_tree.column(k,width=40,anchor='center',stretch=False)
        self.rec_hsb = ttk.Scrollbar(table_host, orient='horizontal', command=self.rec_tree.xview, style='Horizontal.TScrollbar')
        self.rec_tree.configure(xscrollcommand=self.rec_hsb.set)
        self.rec_hsb.pack(side='bottom', fill='x', pady=(2,0))
        self.rec_tree.pack(fill='both',expand=True)"""
code = code.replace(old_rec_pack, new_rec_pack)

# 5. Add horizontal scrollbar to products_page
old_prod_pack = """        for k in ('edit','delete','options'):
            self.prod_tree.column(k,width=40,anchor='center',stretch=False)
        self.prod_tree.pack(fill='both',expand=True)"""
new_prod_pack = """        for k in ('edit','delete','options'):
            self.prod_tree.column(k,width=40,anchor='center',stretch=False)
        self.prod_hsb = ttk.Scrollbar(table_host, orient='horizontal', command=self.prod_tree.xview, style='Horizontal.TScrollbar')
        self.prod_tree.configure(xscrollcommand=self.prod_hsb.set)
        self.prod_hsb.pack(side='bottom', fill='x', pady=(2,0))
        self.prod_tree.pack(fill='both',expand=True)"""
code = code.replace(old_prod_pack, new_prod_pack)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
