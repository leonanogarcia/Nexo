import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

start_idx = text.find('class RoundedActionButton(tk.Frame):')
end_idx = text.find('class RoundedEntry(tk.Frame):', start_idx)

if start_idx != -1 and end_idx != -1:
    old = text[start_idx:end_idx]
    
    new_class = """class RoundedActionButton(tk.Frame):
    \"\"\"Botão cápsula com renderização antialias perfeita e ícones desenhados com supersampling.\"\"\"
    def __init__(self,parent,text,command,width=150,height=42,fill='#2F67B1',hover='#255894',fg='#FFFFFF',font=('Segoe UI',10,'bold'),**kwargs):
        super().__init__(parent,bg=parent.cget('bg'),bd=0,highlightthickness=0,width=width,height=height,cursor='hand2',**kwargs)
        self.pack_propagate(False); self._fill=fill; self._hover=hover; self._fg=fg; self._text=text; self._command=command; self._font=font
        self._canvas=tk.Canvas(self,bg=self.cget('bg'),bd=0,highlightthickness=0); self._canvas.pack(fill='both',expand=True)
        self._img_ref=None; self._icon=self._detect_icon(text); self._label=self._clean_text(text)
        self.bind('<Configure>',lambda e:self._redraw())
        for w in (self,self._canvas):
            w.bind('<Enter>',self._on_enter); w.bind('<Leave>',self._on_leave); w.bind('<Button-1>',self._click)
        self.after_idle(self._redraw)

    def _detect_icon(self,text):
        if '+' in text: return 'plus'
        if '<clock>' in text: return 'clock'
        if '<convert>' in text: return 'convert'
        if '<delete>' in text: return 'delete'
        return None

    def _clean_text(self,text):
        for token in ('+', '<clock>', '<convert>', '<delete>'):
            text = text.replace(token, '')
        return ' '.join(text.split())

    def _make(self,fill, icon=None, start_x=0, cy=0):
        try:
            from PIL import Image,ImageDraw,ImageTk
            w=max(2,self.winfo_width()); h=max(2,self.winfo_height()); scale=8
            
            # Draw on a solid background matching the parent to avoid dark alpha halos
            parent_bg = self.cget('bg')
            im=Image.new('RGB',(w*scale,h*scale), parent_bg); d=ImageDraw.Draw(im)
            d.rounded_rectangle((0,0,w*scale-1,h*scale-1),radius=(h*scale)//2,fill=fill)
            
            if icon:
                col = self._fg
                cx = start_x * scale
                c_y = cy * scale
                cw = max(2, int(1.8 * scale))
                
                def line(pts):
                    d.line(pts, fill=col, width=cw)
                    for i in range(0, len(pts), 2):
                        x, y = pts[i], pts[i+1]
                        d.ellipse((x-cw/2, y-cw/2, x+cw/2, y+cw/2), fill=col)
                        
                if icon=='plus':
                    line([cx-7*scale, c_y, cx+7*scale, c_y])
                    line([cx, c_y-7*scale, cx, c_y+7*scale])
                elif icon=='clock':
                    outer = 7 * scale
                    inner = outer - cw
                    d.ellipse((cx-outer, c_y-outer, cx+outer, c_y+outer), fill=col)
                    d.ellipse((cx-inner, c_y-inner, cx+inner, c_y+inner), fill=fill)
                    line([cx, c_y, cx, c_y-4.5*scale])
                    line([cx, c_y, cx+4*scale, c_y+2.5*scale])
                elif icon=='convert':
                    line([cx-8*scale, c_y-3*scale, cx+6*scale, c_y-3*scale])
                    line([cx+3*scale, c_y-6*scale, cx+6*scale, c_y-3*scale, cx+3*scale, c_y])
                    line([cx+8*scale, c_y+3*scale, cx-6*scale, c_y+3*scale])
                    line([cx-3*scale, c_y, cx-6*scale, c_y+3*scale, cx-3*scale, c_y+6*scale])
                    
            im=im.resize((w,h),Image.Resampling.LANCZOS); return ImageTk.PhotoImage(im)
        except Exception:return None

    def _on_enter(self,e): self._fill0=self._fill; self._fill=self._hover; self._redraw()
    def _on_leave(self,e): self._fill=getattr(self,'_fill0',self._fill); self._redraw()
    def _click(self,e=None): self._command()

    def _redraw(self):
        self._canvas.delete('all')
        w=max(2,self.winfo_width()); h=max(2,self.winfo_height()); cy=h/2
        
        start = 0
        icon_w = 16
        gap = 10
        if self._icon:
            try: text_w=self._font.measure(self._label)
            except Exception: text_w=max(40,len(self._label)*7)
            group_w=icon_w+gap+text_w
            start=max(0,(w-group_w)/2)
        
        img=self._make(self._fill, icon=self._icon, start_x=start+icon_w/2, cy=cy)
        self._img_ref=img
        
        if img:self._canvas.create_image(0,0,image=img,anchor='nw')
        
        if self._icon:
            self._canvas.create_text(start+icon_w+gap,cy,text=self._label,fill=self._fg,font=self._font,anchor='w')
        else:
            self._canvas.create_text(w/2,cy,text=self._label,fill=self._fg,font=self._font,anchor='center')

"""
    text = text[:start_idx] + new_class + text[end_idx:]
    with open('main.py', 'wb') as f:
        f.write(text.encode('utf-8'))
    print("Patched correctly!")
else:
    print("Failed")
