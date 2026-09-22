import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Fix RoundedActionButton _clean_text
old_clean = """    def _clean_text(self,text):
        for token in ('+','?','?','?',' '):
            text=text.replace(token,'')
        return ' '.join(text.split())"""
new_clean = """    def _clean_text(self,text):
        for token in ('+', '🕒', '🗑', '🔄', '🗑️', '➕', '⏳', '⌚'):
            text=text.replace(token,'')
        return ' '.join(text.split())"""
code = code.replace(old_clean, new_clean)

# 2. Add PillScrollbar class
pill_scrollbar_class = """class PillScrollbar(tk.Canvas):
    def __init__(self, parent, tree, **kwargs):
        super().__init__(parent, height=8, bg=parent.cget('bg'), bd=0, highlightthickness=0, **kwargs)
        self.tree = tree
        self.tree.configure(xscrollcommand=self.set_scroll)
        self.bind('<Configure>', self._redraw)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self._pos = (0.0, 1.0)
        self._drag_data = {'x': 0, 'start_pos': 0.0}

    def set_scroll(self, first, last):
        first, last = float(first), float(last)
        self._pos = (first, last)
        if first == 0.0 and last == 1.0:
            self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side='bottom', fill='x', pady=(0, 4), padx=12)
        self._redraw()

    def _redraw(self, e=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10: return
        self.delete('all')
        first, last = self._pos
        x1 = first * w
        x2 = last * w
        r = h / 2
        fill = '#333333'
        self.create_arc(x1, 0, x1+2*r, h, start=90, extent=180, fill=fill, outline='')
        self.create_arc(x2-2*r, 0, x2, h, start=-90, extent=180, fill=fill, outline='')
        self.create_rectangle(x1+r, 0, x2-r, h, fill=fill, outline='')

    def _on_press(self, e):
        w = self.winfo_width()
        first, last = self._pos
        x1 = first * w
        x2 = last * w
        if x1 <= e.x <= x2:
            self._drag_data['x'] = e.x
            self._drag_data['start_pos'] = first
        else:
            new_first = max(0.0, min(1.0 - (last-first), (e.x / w) - (last-first)/2))
            self.tree.xview_moveto(new_first)

    def _on_drag(self, e):
        w = self.winfo_width()
        dx = e.x - self._drag_data['x']
        first, last = self._pos
        delta_pos = dx / w
        new_first = max(0.0, min(1.0 - (last-first), self._drag_data['start_pos'] + delta_pos))
        self.tree.xview_moveto(new_first)

"""
if "class PillScrollbar" not in code:
    code = code.replace("class RoundedActionButton", pill_scrollbar_class + "class RoundedActionButton")

# 3. Replace horizontal ttk.Scrollbar with PillScrollbar in pages
code = code.replace("self.mat_hsb = ttk.Scrollbar(table_host, orient='horizontal', command=self.mat_tree.xview, style='Horizontal.TScrollbar')", "self.mat_hsb = PillScrollbar(table_host, self.mat_tree)")
code = code.replace("self.mat_tree.configure(xscrollcommand=self.mat_hsb.set)\n        self.mat_hsb.pack(side='bottom', fill='x', pady=(2,0))", "")

code = code.replace("self.rec_hsb = ttk.Scrollbar(table_host, orient='horizontal', command=self.rec_tree.xview, style='Horizontal.TScrollbar')", "self.rec_hsb = PillScrollbar(table_host, self.rec_tree)")
code = code.replace("self.rec_tree.configure(xscrollcommand=self.rec_hsb.set)\n        self.rec_hsb.pack(side='bottom', fill='x', pady=(2,0))", "")

code = code.replace("self.prod_hsb = ttk.Scrollbar(table_host, orient='horizontal', command=self.prod_tree.xview, style='Horizontal.TScrollbar')", "self.prod_hsb = PillScrollbar(table_host, self.prod_tree)")
code = code.replace("self.prod_tree.configure(xscrollcommand=self.prod_hsb.set)\n        self.prod_hsb.pack(side='bottom', fill='x', pady=(2,0))", "")

# 4. Fix stretch in treeviews so overlay icons don't break when maximized
# In cadastro:
old_mat_col = """        for k,w in [('code',100),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135),('status',90),('edit',40),('delete',40),('options',40)]:
            self.mat_tree.column(k,width=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date','status') else 'w',stretch=False)"""
new_mat_col = """        for k,w in [('code',100),('name',220),('brand',150),('qty',110),('unit',65),('value',100),('category',130),('date',135),('mod_date',135),('status',90),('edit',40),('delete',40),('options',40)]:
            self.mat_tree.column(k,width=w,anchor='center' if k in ('qty','unit','value','category','date','mod_date','status') else 'w',stretch=(k=='name'))"""
code = code.replace(old_mat_col, new_mat_col)

# In recipes:
old_rec_col = """        for k, w in [('code',95),('name',280),('yield',120),('unit',65),('cost',120)]:
            self.rec_tree.column(k,width=w,anchor='center' if k in ('yield','unit','cost') else 'w',stretch=False)"""
new_rec_col = """        for k, w in [('code',95),('name',280),('yield',120),('unit',65),('cost',120)]:
            self.rec_tree.column(k,width=w,anchor='center' if k in ('yield','unit','cost') else 'w',stretch=(k=='name'))"""
code = code.replace(old_rec_col, new_rec_col)

# In products:
old_prod_col = """        for k, w in [('code',95),('name',280),('weight',140),('cost',120),('price',120),('margin',100)]:
            self.prod_tree.column(k,width=w,anchor='center' if k in ('weight','cost','price','margin') else 'w',stretch=False)"""
new_prod_col = """        for k, w in [('code',95),('name',280),('weight',140),('cost',120),('price',120),('margin',100)]:
            self.prod_tree.column(k,width=w,anchor='center' if k in ('weight','cost','price','margin') else 'w',stretch=(k=='name'))"""
code = code.replace(old_prod_col, new_prod_col)


# 5. Fix button widths in cadastro
code = code.replace("width=177, height=49", "width=130, height=49")
code = code.replace("width=148, height=49", "width=120, height=49")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
