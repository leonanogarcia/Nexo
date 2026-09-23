import re

with open('main.py', 'rb') as f:
    content = f.read().decode('utf-8')

old_class = """    def _make(self,fill):
        try:
            from PIL import Image,ImageDraw,ImageTk
            w=max(2,self.winfo_width()); h=max(2,self.winfo_height()); scale=4
            im=Image.new('RGBA',(w*scale,h*scale),(0,0,0,0)); d=ImageDraw.Draw(im)
            d.rounded_rectangle((scale,scale,w*scale-scale-1,h*scale-scale-1),radius=(h*scale)//2,fill=fill)
            im=im.resize((w,h),Image.Resampling.LANCZOS); return ImageTk.PhotoImage(im)
        except Exception:return None

    def _draw_icon(self,kind,cx,cy,col):
        w=1.8
        if kind=='plus':
            self._canvas.create_line(cx-7,cy,cx+7,cy,fill=col,width=w,capstyle='round')
            self._canvas.create_line(cx,cy-7,cx,cy+7,fill=col,width=w,capstyle='round')
        elif kind=='clock':
            self._canvas.create_oval(cx-7,cy-7,cx+7,cy+7,outline=col,width=w)
            self._canvas.create_line(cx,cy,cx,cy-4.5,fill=col,width=w,capstyle='round')
            self._canvas.create_line(cx,cy,cx+4,cy+2.5,fill=col,width=w,capstyle='round')
        elif kind=='convert':
            self._canvas.create_line(cx-8,cy-3,cx+6,cy-3,fill=col,width=w,capstyle='round')
            self._canvas.create_line(cx+3,cy-6,cx+6,cy-3,cx+3,cy,fill=col,width=w,capstyle='round',joinstyle='round')
            self._canvas.create_line(cx+8,cy+3,cx-6,cy+3,fill=col,width=w,capstyle='round')
            self._canvas.create_line(cx-3,cy,cx-6,cy+3,cx-3,cy+6,fill=col,width=w,capstyle='round',joinstyle='round')

    def _redraw(self):
        self._canvas.delete('all')
        img=self._make(self._fill); self._img_ref=img
        if img:self._canvas.create_image(0,0,image=img,anchor='nw')
        w=max(2,self.winfo_width()); h=max(2,self.winfo_height()); cy=h/2
        # Centraliza o conjunto ícone + texto como um único bloco.
        # Isso evita a sobreposição que ocorria especialmente em
        # "Conversões do item", mantendo o visual da referência.
        if self._icon:
            try:
                text_w=self._font.measure(self._label)
            except Exception:
                text_w=max(40,len(self._label)*7)
            icon_w=16
            gap=10
            group_w=icon_w+gap+text_w
            start=max(0,(w-group_w)/2)
            self._draw_icon(self._icon,start+icon_w/2,cy,self._fg)
            self._canvas.create_text(start+icon_w+gap,cy,text=self._label,fill=self._fg,font=self._font,anchor='w')
        else:
            self._canvas.create_text(w/2,cy,text=self._label,fill=self._fg,font=self._font,anchor='center')"""

new_class = """    def _make(self,fill, icon=None, start_x=0, cy=0):
        try:
            from PIL import Image,ImageDraw,ImageTk
            w=max(2,self.winfo_width()); h=max(2,self.winfo_height()); scale=4
            im=Image.new('RGBA',(w*scale,h*scale),(0,0,0,0)); d=ImageDraw.Draw(im)
            d.rounded_rectangle((scale,scale,w*scale-scale-1,h*scale-scale-1),radius=(h*scale)//2,fill=fill)
            
            if icon:
                col = self._fg
                cx = start_x * scale
                c_y = cy * scale
                cw = max(2, int(1.8 * scale))
                
                # Draw circles at endpoints for round caps
                def line(pts, **kwargs):
                    d.line(pts, fill=col, width=cw, joint='curve')
                    for i in range(0, len(pts), 2):
                        x, y = pts[i], pts[i+1]
                        d.ellipse((x-cw/2, y-cw/2, x+cw/2, y+cw/2), fill=col)
                        
                if icon=='plus':
                    line([cx-7*scale, c_y, cx+7*scale, c_y])
                    line([cx, c_y-7*scale, cx, c_y+7*scale])
                elif icon=='clock':
                    d.ellipse((cx-7*scale, c_y-7*scale, cx+7*scale, c_y+7*scale), outline=col, width=cw)
                    line([cx, c_y, cx, c_y-4.5*scale])
                    line([cx, c_y, cx+4*scale, c_y+2.5*scale])
                elif icon=='convert':
                    line([cx-8*scale, c_y-3*scale, cx+6*scale, c_y-3*scale])
                    line([cx+3*scale, c_y-6*scale, cx+6*scale, c_y-3*scale, cx+3*scale, c_y])
                    line([cx+8*scale, c_y+3*scale, cx-6*scale, c_y+3*scale])
                    line([cx-3*scale, c_y, cx-6*scale, c_y+3*scale, cx-3*scale, c_y+6*scale])
                    
            im=im.resize((w,h),Image.Resampling.LANCZOS); return ImageTk.PhotoImage(im)
        except Exception:return None

    def _draw_icon(self,kind,cx,cy,col):
        pass

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
            self._canvas.create_text(w/2,cy,text=self._label,fill=self._fg,font=self._font,anchor='center')"""

content = content.replace(old_class, new_class)

with open('main.py', 'wb') as f:
    f.write(content.encode('utf-8'))
print('Patched button icons')
