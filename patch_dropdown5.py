import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

match = re.search(r'    def _open_dropdown\(self\):.*?top\.focus_set\(\)\n', text, re.DOTALL)
if match:
    old = match.group(0)
    
    new_code = """    def _open_dropdown(self):
        w = self.winfo_width()
        h_menu = len(self._opts)*36
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        
        top = tk.Toplevel(self)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        top.geometry(f'{w}x{h_menu}+{x}+{y}')
        
        # Use the app's background color as the transparent key to prevent halos!
        try: bg_color = self.winfo_toplevel().cget('bg')
        except: bg_color = '#F4F7FC'
        
        try:
            top.configure(bg=bg_color)
            top.wm_attributes('-transparentcolor', bg_color)
        except Exception: pass
        
        c = tk.Canvas(top, bg=bg_color, bd=0, highlightthickness=0)
        c.pack(fill='both', expand=True)
        
        # Draw perfectly anti-aliased rounded rectangle in PIL matching the background
        try:
            from PIL import Image, ImageDraw, ImageTk
            scale = 4; tw = w*scale; th = h_menu*scale
            # Background matches the transparent key so resizing blends beautifully
            im = Image.new('RGB', (tw, th), bg_color)
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((0, 0, tw-1, th-1), radius=10*scale, fill='#FFFFFF', outline='#E2EAF5', width=scale)
            im = im.resize((w, h_menu), Image.Resampling.LANCZOS)
            self._menu_bg = ImageTk.PhotoImage(im)
            c.create_image(0, 0, image=self._menu_bg, anchor='nw')
        except Exception:
            c.create_rectangle(0,0,w,h_menu, fill='#FFFFFF', outline='#E2EAF5')

        for i, opt in enumerate(self._opts):
            oy = i*36
            # Use a slightly inset hitbox so we don't cover the rounded corners
            hb = c.create_rectangle(2, oy+2 if i==0 else oy, w-2, oy+34 if i==len(self._opts)-1 else oy+36, fill='#FFFFFF', outline='', tags=f'opt_{i}')
            col = '#2F67B1' if opt == self._var.get() else '#18223A'
            fnt = ('Segoe UI', 10, 'bold') if opt == self._var.get() else ('Segoe UI', 10)
            c.create_text(w/2, oy+18, text=opt, fill=col, font=fnt, anchor='center', tags=f'opt_{i}')
            
            def on_enter(e, idx=i, hb_id=hb): c.itemconfig(hb_id, fill='#F8FAFC')
            def on_leave(e, idx=i, hb_id=hb): c.itemconfig(hb_id, fill='#FFFFFF')
            def on_click(e, o=opt):
                self._var.set(o)
                root.unbind('<Button-1>', bind_id)
                top.destroy()
                
            c.tag_bind(f'opt_{i}', '<Enter>', on_enter)
            c.tag_bind(f'opt_{i}', '<Leave>', on_leave)
            c.tag_bind(f'opt_{i}', '<Button-1>', on_click)
            
        root = self.winfo_toplevel()
        def check_click(e):
            if not top.winfo_exists(): return
            rx, ry = top.winfo_pointerxy()
            tx = top.winfo_rootx(); ty = top.winfo_rooty()
            tw = top.winfo_width(); th = top.winfo_height()
            
            if (tx <= rx <= tx+tw and ty <= ry <= ty+th):
                pass
            else:
                try:
                    root.unbind('<Button-1>', bind_id)
                    top.destroy()
                except Exception: pass

        bind_id = root.bind('<Button-1>', check_click, add='+')
        
        def on_focus_out(e):
            if e.widget == top:
                try:
                    root.unbind('<Button-1>', bind_id)
                    top.destroy()
                except Exception: pass
                
        top.bind('<FocusOut>', on_focus_out)
        top.focus_set()
"""
    text = text.replace(old, new_code)
    
    with open('main.py', 'wb') as f:
        f.write(text.encode('utf-8'))
    print("SUCCESS")
else:
    print("Regex failed")
