import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_tooltip = """    def _show_tooltip(self, key):
        self._hide_tooltip()
        if not key or key not in self._labels: return
        text = self._labels[key]
        try:
            W=max(self.winfo_width(),150); H=max(self.winfo_height(),650)
            side_w=min(84, max(78, int(W*0.064))); sx=(W-side_w)/2 if W<=150 else (29 if W>=600 else 8)
            y0=145 if H>=700 else 130
            bottom=max(y0+530, H-32)
            h=max(300,bottom-y0)
            if h > 540:
                spacing = (h - 130) / 4
                centers = [y0 + 65 + i * spacing for i in range(5)]
            else:
                centers = [y0+65, y0+170, y0+275, y0+380, y0+485]
            idx = list(self._asset_slug.keys()).index(key)
            cy = centers[idx]
            
            # Use Canvas on main window to guarantee perfect camouflage
            tx = int(sx + side_w + 2)
            ty = int(cy - 18)
            
            root = self.winfo_toplevel()
            tip = tk.Canvas(root, bd=0, highlightthickness=0)
            
            import tkinter.font as tkfont
            font = tkfont.Font(family='Segoe UI', size=10, weight='bold')
            text_w = font.measure(text)
            tip_w = text_w + 28
            tip_h = 36
            
            tip.place(x=tx, y=ty, width=tip_w, height=tip_h)
            
            # The boundary where ReferenceSidebar ends is at x=150 on the root window
            boundary = 150 - tx
            
            app_bg = getattr(root, 'colors', {}).get('bg', '#F4F7FC')
            panel_bg = getattr(root, 'colors', {}).get('panel', '#FFFFFF')
            
            if boundary > 0:
                tip.create_rectangle(0, 0, boundary, tip_h, fill=app_bg, outline='')
                tip.create_rectangle(boundary, 0, tip_w, tip_h, fill=panel_bg, outline='')
            else:
                tip.create_rectangle(0, 0, tip_w, tip_h, fill=panel_bg, outline='')
                
            try:
                from PIL import Image, ImageDraw, ImageTk
                scale = 4
                im = Image.new('RGBA', (tip_w*scale, tip_h*scale), (0,0,0,0))
                d = ImageDraw.Draw(im)
                d.rounded_rectangle((0, 0, tip_w*scale-1, tip_h*scale-1), radius=16*scale, fill='#1F2633')
                im = im.resize((tip_w, tip_h), Image.Resampling.LANCZOS)
                tip._bg_img = ImageTk.PhotoImage(im)
                tip.create_image(0, 0, image=tip._bg_img, anchor='nw')
            except Exception:
                tip.create_oval(0, 0, tip_h, tip_h, fill='#1F2633', outline='')
                tip.create_rectangle(tip_h/2, 0, tip_w - tip_h/2, tip_h, fill='#1F2633', outline='')
                tip.create_oval(tip_w - tip_h, 0, tip_w, tip_h, fill='#1F2633', outline='')
            
            tip.create_text(tip_w/2, tip_h/2, text=text, fill='#FFFFFF', font=('Segoe UI', 10, 'bold'), anchor='center')
            self._tooltip_win = tip
        except Exception: pass"""

new_hide = """    def _hide_tooltip(self):
        if self._tooltip_win:
            try:
                if isinstance(self._tooltip_win, tk.Toplevel):
                    self._tooltip_win.destroy()
                else:
                    self._tooltip_win.place_forget()
                    self._tooltip_win.destroy()
            except Exception: pass
            self._tooltip_win=None"""

# We'll use regex to replace everything from "def _show_tooltip" to "except Exception: pass" inside ReferenceSidebar.
# Note: we have two _show_tooltips (one in NavItem). We only want the second one.
parts = code.split('def _show_tooltip(self, key):')
if len(parts) == 2:
    prefix = parts[0]
    rest = parts[1]
    
    # find end of _show_tooltip
    end_idx = rest.find('    def _hide_tooltip(self):')
    if end_idx != -1:
        rest2 = rest[end_idx:]
        end_idx2 = rest2.find('        self._hover=None')
        
        final_code = prefix + new_tooltip + "\n\n" + new_hide + "\n" + rest2[end_idx2:]
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(final_code)
        print("Success")
    else:
        print("Could not find _hide_tooltip")
else:
    print("Could not split properly")
