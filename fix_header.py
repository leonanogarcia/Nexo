import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

bad_redraw = """        def redraw_mat_header(_event=None):
            self._draw_canvas_header(self.mat_header, self.mat_tree, self._mat_header_specs, self._mat_header_imgs, 'mat')
            
        self.mat_header.bind('<Configure>', redraw_mat_header)
        self.mat_tree.bind('<Configure>', redraw_mat_header)
        
        self._setup_canvas_header_drag(self.mat_header, self.mat_tree, ['edit','delete','options'], redraw_mat_header, 'mat')"""

good_redraw = """        def redraw_mat_header(_event=None):
            c=self.mat_header; c.delete('all')
            w=max(c.winfo_width(),2); h=max(c.winfo_height(),2)
            r=min(h/2,18); fill='#EEF4FB'
            c.create_rectangle(r,0,w-r,h,fill=fill,outline='')
            c.create_rectangle(0,r,w,h-r,fill=fill,outline='')
            c.create_arc(0,0,2*r,2*r,start=90,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,0,w,2*r,start=0,extent=90,fill=fill,outline=fill)
            c.create_arc(0,h-2*r,2*r,h,start=180,extent=90,fill=fill,outline=fill)
            c.create_arc(w-2*r,h-2*r,w,h,start=270,extent=90,fill=fill,outline=fill)
            x0=0
            cols=[('#0','')]+[(f'#{i}',txt) for i,(key,txt, _) in enumerate(self._mat_header_specs,1)]
            for idx,(col,txt) in enumerate(cols):
                try: cw=int(self.mat_tree.column(col,'width'))
                except Exception: cw=0
                if col=='#0':
                    x0+=cw; continue
                if col=='#11':
                    img=self._mat_header_imgs.get('edit')
                    if img: c.create_image(x0+cw/2,h/2,image=img,anchor='center')
                elif col=='#12':
                    img=self._mat_header_imgs.get('delete')
                    if img: c.create_image(x0+cw/2,h/2,image=img,anchor='center')
                elif col=='#13':
                    pass
                else:
                    align = 'w' if col in ('#1', '#2', '#3') else 'center'
                    anchor_x = x0+12 if align == 'w' else x0+cw/2
                    c.create_text(anchor_x,h/2,text=txt,fill='#60769D',font=('Segoe UI',9,'bold'),anchor=align)
                x0+=cw
        self._redraw_mat_header=redraw_mat_header
        self.mat_header.bind('<Configure>',redraw_mat_header)
        self.mat_tree.bind('<Configure>',lambda e:redraw_mat_header())
        self.after_idle(redraw_mat_header)
        
        self._setup_canvas_header_drag(self.mat_header, self.mat_tree, ['edit','delete','options'], redraw_mat_header, 'mat')"""

code = code.replace(bad_redraw, good_redraw)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
