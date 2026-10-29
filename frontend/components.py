import json
import re
import shutil
import sqlite3
from pathlib import Path
from datetime import date, datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

from backend import (
    paths,
    BASE_DIR, RESOURCE_DIR, USER_DATA_DIR, DATA_DIR, BACKUPS_DIR,
    CONFIG_PATH, DEFAULT_DB_PATH, DB_PATH, DOCS_DIR,
    ICON_PNG, LOGO_PNG, ICON_ICO, UI_ASSETS,
    load_file_config, save_file_config, get_db_path, set_db_path,
    db, now_iso, init_db, next_code, get_setting, set_setting,
    get_cost_settings, record_edit, list_names,
    UNITS_MASS, UNITS_VOLUME, UNITS_COUNT, UNITS, BASE_UNITS_DEFAULT,
    to_float, optional_float, money_to_float, fmt, fmt_num, normalize_text,
    dimension_of_unit, base_unit, unit_factor_to_default_base,
    configured_base_unit, unit_factor_to_internal,
    custom_units_for_material, conversion_to_base, convert_generic, conversion_between,
    material_cost, recipe_cost, item_cost, operational_cost,
    product_unit_cost, product_direct_cost, snapshot_costs,
    save_uploaded_document, latest_document,
    extract_docx_text, extract_pdf_text, parse_recipe_lines,
)

def _field_palette(parent):
    try:
        app=parent.winfo_toplevel()
        colors=getattr(app,'colors',{})
        return colors.get('field','#FFFFFF'), colors.get('line','#DDE5F2'), colors.get('panel','#FFFFFF')
    except Exception:
        return '#FFFFFF','#DDE5F2',parent.cget('bg')


def rounded_entry(parent, variable, **kwargs):
    field, line, panel = _field_palette(parent)
    try: parent_bg = parent.cget('bg')
    except: parent_bg = panel
    w = kwargs.pop('width', 28)
    # Estimate pixel width (tk.Entry width is in characters, roughly 8px per char)
    px_w = w * 9 + 32
    wrap=RoundedPanel(parent, fill=field, border='#B0C0D6', radius=16, bg=parent_bg)
    wrap.config(width=px_w, height=32); wrap.pack_propagate(False)
    entry_kwargs=dict(bg=field, fg=getattr(parent.winfo_toplevel(),'colors',{}).get('text','#1F2A44'),
                      insertbackground=getattr(parent.winfo_toplevel(),'colors',{}).get('text','#1F2A44'),
                      relief='flat', bd=0, highlightthickness=0, font=('Segoe UI',10), **kwargs)
    entry=tk.Entry(wrap, textvariable=variable, **entry_kwargs)
    entry.pack(fill='both', expand=True, padx=(16,16), pady=4)
    return wrap, entry


def numeric_entry(parent, variable, **kwargs):
    """Campo numérico arredondado; bloqueia qualquer entrada não numérica."""
    wrap, entry = rounded_entry(parent, variable, **kwargs)
    vcmd=(entry.register(lambda proposed: bool(re.fullmatch(r'[0-9]*([.,][0-9]*)?',proposed))),'%P')
    entry.configure(validate='key',validatecommand=vcmd)
    return wrap


def masked_money_entry(parent, variable, **kwargs):
    """Campo monetário: aceita somente dígitos; separadores digitados são ignorados."""
    wrap, entry = rounded_entry(parent, variable, **kwargs)
    state = {'digits': ''}

    def format_digits(digits):
        digits = ''.join(ch for ch in str(digits) if ch.isdigit()) or '0'
        digits = digits.lstrip('0') or '0'
        state['digits'] = digits
        variable.set(fmt(int(digits) / 100.0))
        entry.icursor(tk.END)

    def sync_from_display():
        digits = ''.join(ch for ch in variable.get() if ch.isdigit())
        # O display sempre tem R$ e duas casas. Não deixamos o campo vazio.
        format_digits(digits[-18:] if digits else '0')

    def keypress(event):
        if event.char and event.char.isdigit():
            format_digits(state['digits'] + event.char)
            return 'break'
        if event.char in (',', '.'):
            # Separadores são apenas ignorados. A máscara já fornece a vírgula.
            entry.icursor(tk.END)
            return 'break'
        if event.keysym in ('BackSpace', 'Delete'):
            digits = state['digits'][:-1] if state['digits'] else '0'
            format_digits(digits)
            return 'break'
        if event.keysym in ('Tab','Return','Escape','Left','Right','Home','End','Shift_L','Shift_R','Control_L','Control_R'):
            return
        return 'break'

    entry.bind('<KeyPress>', keypress)
    entry.bind('<FocusIn>', lambda e: sync_from_display())
    if not variable.get():
        variable.set('R$ 0,00')
    else:
        sync_from_display()
    return wrap


def safe_error(parent, title, exc):
    message = str(exc)
    if 'obrigat' in message.lower():
        action = 'finalizar' if any(word in title.lower() for word in ('finalizar','concluir')) else 'salvar'
        message = f'Não foi possível {action}. Existem campos obrigatórios que precisam ser preenchidos.'
    messagebox.showerror(title, message, parent=parent)


def bind_text_capitalization(widget):
    if isinstance(widget, (ttk.Entry, ttk.Combobox)):
        def normalize(_event=None, w=widget):
            try:
                if str(w.cget('state')) == 'disabled':
                    return
                value = w.get()
                normalized = normalize_text(value)
                if normalized != value:
                    w.delete(0, tk.END)
                    w.insert(0, normalized)
            except Exception:
                pass
        widget.bind('<FocusOut>', normalize, add='+')
        widget.bind('<Return>', normalize, add='+')
        widget.bind('<KeyRelease>', normalize, add='+')
    for child in widget.winfo_children():
        bind_text_capitalization(child)


def FlatEmojiButton(master, text, command):
    try: bg_col = master.cget('bg')
    except: bg_col = '#FFFFFF'
    btn = tk.Label(master, text=text, font=('Segoe UI', 12), cursor='hand2', bg=bg_col, fg='#687796')
    btn.bind('<Enter>', lambda e: btn.config(fg='#1D3557', bg='#E3EBF6'))
    btn.bind('<Leave>', lambda e: btn.config(fg='#687796', bg=bg_col))
    btn.bind('<Button-1>', lambda e: command())
    return btn


class Modal(tk.Toplevel):
    def __init__(self, master, title, geometry='760x560'):
        super().__init__(master)
        try: bg_col = master.colors.get('bg', '#F4F7FC')
        except: bg_col = '#F4F7FC'
        self.configure(bg=bg_col)
        self.title(title)
        self.transient(master)
        self.resizable(True, True)
        self.minsize(520, 320)
        self._place_over_master(geometry)
        self.action_host=tk.Frame(self,bg=self.cget('bg'))
        self.action_host.pack(side='bottom',fill='x',padx=12,pady=(4,10))
        # self.action_host.pack_propagate(False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.bind('<Map>', lambda e: (self.lift(), self.focus_force()))
        self.after(50, lambda: (self.lift(), self.focus_force(), bind_text_capitalization(self)))

    def _work_area(self, x, y):
        # No Windows, usa a área útil do monitor onde a janela principal está.
        try:
            import ctypes
            from ctypes import wintypes
            class RECT(ctypes.Structure):
                _fields_=[('left',wintypes.LONG),('top',wintypes.LONG),('right',wintypes.LONG),('bottom',wintypes.LONG)]
            class MONITORINFO(ctypes.Structure):
                _fields_=[('cbSize',wintypes.DWORD),('rcMonitor',RECT),('rcWork',RECT),('dwFlags',wintypes.DWORD)]
            MONITOR_DEFAULTTONEAREST=2
            hmon=ctypes.windll.user32.MonitorFromPoint(wintypes.POINT(x,y), MONITOR_DEFAULTTONEAREST)
            mi=MONITORINFO(); mi.cbSize=ctypes.sizeof(MONITORINFO)
            if hmon and ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
                r=mi.rcWork
                return r.left,r.top,r.right,r.bottom
        except Exception:
            pass
        return 0,0,self.winfo_screenwidth(),self.winfo_screenheight()

    def _place_over_master(self, geometry):
        m=re.match(r'^(\d+)x(\d+)', str(geometry))
        req_w,req_h=(int(m.group(1)),int(m.group(2))) if m else (760,560)
        self.update_idletasks()
        mx=self.master.winfo_rootx(); my=self.master.winfo_rooty()
        mw=max(self.master.winfo_width(),1); mh=max(self.master.winfo_height(),1)
        left,top,right,bottom=self._work_area(mx+mw//2,my+mh//2)
        max_w=max(520,right-left-24); max_h=max(320,bottom-top-24)
        w=min(req_w,max_w); h=min(req_h,max_h)
        x=mx+(mw-w)//2; y=my+(mh-h)//2
        x=max(left+12,min(x,right-w-12)); y=max(top+12,min(y,bottom-h-12))
        self.geometry(f'{w}x{h}+{x}+{y}')


class RoundedPanel(tk.Frame):
    """Painel visual com fundo arredondado, com suporte a cor sólida ou degradê vertical."""
    def __init__(self, parent, fill='#FFFFFF', border='#E8DED0', radius=22, padding=0, **kwargs):
        bg = kwargs.pop('bg', None)
        if bg is None:
            try: bg = parent.cget('bg')
            except Exception:
                try: bg = parent.cget('background')
                except Exception: bg = '#FFFFFF'
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0, **kwargs)
        self._fill = fill
        self._border = border
        self._radius = radius
        self._canvas = tk.Canvas(self, bg=self.cget('bg'), highlightthickness=0, bd=0)
        self._canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._canvas.lower('all')
        self.bind('<Configure>', self._redraw)
        if padding:
            self.configure(padx=padding, pady=padding)

    def set_style(self, fill=None, border=None, bg=None):
        if fill is not None:
            self._fill = fill
        if border is not None:
            self._border = border
        if bg is not None:
            self.configure(bg=bg)
            self._canvas.configure(bg=bg)
        self._redraw()

    def _hex_to_rgb(self, color):
        color = str(color).strip()
        if color.startswith('#') and len(color) == 7:
            return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        return (255, 255, 255)

    def _rgb_to_hex(self, rgb):
        return '#%02x%02x%02x' % tuple(max(0, min(255, int(v))) for v in rgb)

    def _interpolate(self, c1, c2, t):
        a = self._hex_to_rgb(c1)
        b = self._hex_to_rgb(c2)
        return self._rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))

    def _draw_gradient(self, c, w, h, r):
        import math
        top, bottom = self._fill
        denom = max(h - 1, 1)
        for y in range(h):
            t = y / denom
            color = self._interpolate(top, bottom, t)
            if y < r:
                dy = r - y
                dx = r - math.sqrt(max(r*r - dy*dy, 0))
            elif y >= h - r:
                dy = y - (h - r - 1)
                dx = r - math.sqrt(max(r*r - dy*dy, 0))
            else:
                dx = 0
            x1 = dx
            x2 = w - dx
            c.create_line(x1, y, x2, y, fill=color)

    def _draw_solid(self, c, w, h, r, fill):
        c.create_rectangle(r,0,w-r,h,fill=fill,outline='')
        c.create_rectangle(0,r,w,h-r,fill=fill,outline='')
        c.create_arc(0,0,2*r,2*r,start=90,extent=90,fill=fill,outline=fill)
        c.create_arc(w-2*r,0,w,2*r,start=0,extent=90,fill=fill,outline=fill)
        c.create_arc(0,h-2*r,2*r,h,start=180,extent=90,fill=fill,outline=fill)
        c.create_arc(w-2*r,h-2*r,w,h,start=270,extent=90,fill=fill,outline=fill)

    def _redraw(self, _event=None):
        c=self._canvas; c.delete('all')
        w=max(self.winfo_width(),2); h=max(self.winfo_height(),2); r=min(self._radius, w//2, h//2)
        try:
            from PIL import Image, ImageDraw, ImageTk
            scale=4
            sw,sh=w*scale,h*scale
            im=Image.new('RGBA',(sw,sh),(0,0,0,0))
            d=ImageDraw.Draw(im)
            if isinstance(self._fill,(tuple,list)) and len(self._fill)>=2:
                top,bottom=self._fill
                def rgb(v):
                    v=str(v).lstrip('#'); return tuple(int(v[i:i+2],16) for i in (0,2,4))
                a,b=rgb(top),rgb(bottom)
                for yy in range(sh):
                    t=yy/max(sh-1,1)
                    col=tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))+(255,)
                    d.line((0,yy,sw,yy),fill=col)
                # Mask to rounded silhouette.
                mask=Image.new('L',(sw,sh),0); md=ImageDraw.Draw(mask)
                md.rounded_rectangle((0,0,sw-1,sh-1),radius=r*scale,fill=255)
                im.putalpha(mask)
            else:
                d.rounded_rectangle((0,0,sw-1,sh-1),radius=r*scale,fill=self._fill)
            if self._border:
                d.rounded_rectangle((scale,scale,sw-scale-1,sh-scale-1),radius=max(1,r*scale-scale),outline=self._border,width=scale)
            im=im.resize((w,h),Image.Resampling.LANCZOS)
            self._img_ref=ImageTk.PhotoImage(im)
            c.create_image(0,0,image=self._img_ref,anchor='nw')
        except Exception:
            if isinstance(self._fill,(tuple,list)):
                self._draw_solid(c,w,h,r,self._fill[0])
            else:
                self._draw_solid(c,w,h,r,self._fill)
            if self._border:
                c.create_rectangle(0,0,w-1,h-1,outline=self._border,width=1)


class PillScrollbar(tk.Canvas):
    def __init__(self, parent, tree, **kwargs):
        super().__init__(parent, height=8, bg=parent.cget('bg'), bd=0, highlightthickness=0, **kwargs)
        self.tree = tree
        self.tree.configure(xscrollcommand=self._on_scroll)
        self.bind('<Configure>', self._redraw)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self._pos = (0.0, 1.0)
        self._drag_data = {'x': 0, 'start_pos': 0.0}
        # Start hidden — do NOT pack yet

    def _on_scroll(self, first, last):
        first, last = float(first), float(last)
        self._pos = (first, last)
        if first <= 0.001 and last >= 0.999:
            if self.winfo_ismapped():
                self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side='bottom', fill='x', pady=(0, 4), padx=20)
            self.tk.call('raise', self._w)
        self._redraw()

    def _redraw(self, e=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10: return
        self.delete('all')
        first, last = self._pos
        if first <= 0.001 and last >= 0.999: return
        r = h / 2
        x1 = max(r, first * w)
        x2 = min(w - r, last * w)
        if x2 - x1 < 20:
            mid = (x1 + x2) / 2
            x1, x2 = mid - 10, mid + 10
            x1 = max(r, x1)
            x2 = min(w - r, max(x1+20, x2))
        self.create_line(x1, h / 2, x2, h / 2, fill='#A0ABB9', width=h, capstyle='round')

    def _on_press(self, e):
        w = self.winfo_width()
        first, last = self._pos
        x1 = first * w; x2 = last * w
        if x1 <= e.x <= x2:
            self._drag_data['x'] = e.x
            self._drag_data['start_pos'] = first
        else:
            new_first = max(0.0, min(1.0 - (last-first), (e.x / w) - (last-first)/2))
            self.tree.xview_moveto(new_first)

    def _on_drag(self, e):
        w = self.winfo_width(); dx = e.x - self._drag_data['x']; first, last = self._pos
        delta_pos = dx / w
        new_first = max(0.0, min(1.0 - (last-first), self._drag_data['start_pos'] + delta_pos))
        self.tree.xview_moveto(new_first)

    def _on_drag(self, e):
        w = self.winfo_width()
        dx = e.x - self._drag_data['x']
        first, last = self._pos
        delta_pos = dx / w
        new_first = max(0.0, min(1.0 - (last-first), self._drag_data['start_pos'] + delta_pos))
        self.tree.xview_moveto(new_first)

class RoundedActionButton(tk.Frame):
    """Botão cápsula com renderização antialias perfeita e ícones desenhados com supersampling."""
    def __init__(self,parent,text,command,width=150,height=42,fill='#2F67B1',hover='#255894',fg='#FFFFFF',font=('Segoe UI',10,'bold'),**kwargs):
        import tkinter.font as tkfont
        f = tkfont.Font(family=font[0], size=font[1], weight=font[2] if len(font)>2 else 'normal')
        c_text = text
        for t in ('+', '<clock>', '<convert>', '<delete>'): c_text = c_text.replace(t, '')
        c_text = ' '.join(c_text.split())
        calc_w = f.measure(c_text) + (24 if c_text != text else 0) + 36
        if c_text.strip(): width = max(width, calc_w)
        bg_color = kwargs.pop('bg', parent.cget('bg'))
        super().__init__(parent,bg=bg_color,bd=0,highlightthickness=0,width=width,height=height,cursor='hand2',**kwargs)
        self.pack_propagate(False); self._base_fill=fill; self._hover_fill=hover; self._current_fill=fill; self._fg=fg; self._text=text; self._command=command; self._font=font; self._tkfont=f
        self._canvas=tk.Canvas(self,bg=self.cget('bg'),bd=0,highlightthickness=0); self._canvas.pack(fill='both',expand=True)
        self._img_ref=None; self._icon=self._detect_icon(text); self._label=self._clean_text(text)
        self.bind('<Configure>',lambda e:self._redraw())
        for w in (self,self._canvas):
            w.bind('<Enter>',self._on_enter); w.bind('<Leave>',self._on_leave); w.bind('<Button-1>',self._click)
        self.after_idle(self._redraw)

    def set_text(self, text):
        self._text = text
        self._icon = self._detect_icon(text)
        self._label = self._clean_text(text)
        self._redraw()

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
            if not parent_bg.startswith('#'): parent_bg = getattr(self.winfo_toplevel(), 'colors', {}).get('panel', '#F3F6FA')
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
                    d.arc((cx-7*scale, c_y-4*scale, cx+1*scale, c_y+4*scale), 180, 270, fill=col, width=cw)
                    d.ellipse((cx-7*scale-cw/2, c_y-cw/2, cx-7*scale+cw/2, c_y+cw/2), fill=col)
                    line([cx-3*scale, c_y-4*scale, cx+5*scale, c_y-4*scale])
                    line([cx+2*scale, c_y-7*scale, cx+5*scale, c_y-4*scale, cx+2*scale, c_y-1*scale])
                    d.arc((cx-1*scale, c_y-4*scale, cx+7*scale, c_y+4*scale), 0, 90, fill=col, width=cw)
                    d.ellipse((cx+7*scale-cw/2, c_y-cw/2, cx+7*scale+cw/2, c_y+cw/2), fill=col)
                    line([cx+3*scale, c_y+4*scale, cx-5*scale, c_y+4*scale])
                    line([cx-2*scale, c_y+1*scale, cx-5*scale, c_y+4*scale, cx-2*scale, c_y+7*scale])
                elif icon=='delete':
                    try:
                        icon_img = Image.open(UI_ASSETS / 'action_delete_reference_exact.png').convert('RGBA')
                        # Resize to fit nicely (about 14x16 at 1x)
                        icon_img = icon_img.resize((int(14*scale), int(16*scale)), Image.Resampling.LANCZOS)
                        
                        # Recolor the icon to match self._fg exactly
                        r_c, g_c, b_c = self.winfo_rgb(col)
                        r_c, g_c, b_c = r_c//256, g_c//256, b_c//256
                        data = icon_img.get_flattened_data() if hasattr(icon_img, 'get_flattened_data') else icon_img.getdata()
                        new_data = [(r_c, g_c, b_c, item[3]) for item in data]
                        icon_img.putdata(new_data)
                        
                        # Paste centered
                        im.paste(icon_img, (int(cx - 7*scale), int(c_y - 8*scale)), icon_img)
                    except Exception:
                        line([cx-5*scale, c_y-5*scale, cx+5*scale, c_y-5*scale])
                    
            im=im.resize((w,h),Image.Resampling.LANCZOS); return ImageTk.PhotoImage(im)
        except Exception:return None

    def _on_enter(self,e): self._current_fill=self._hover_fill; self._redraw()
    def _on_leave(self,e): self._current_fill=self._base_fill; self._redraw()
    def _click(self,e=None): 
        self._current_fill=self._base_fill; self._redraw()
        self.after(10, self._command)

    def _redraw(self):
        self._canvas.delete('all')
        w=max(2,self.winfo_width()); h=max(2,self.winfo_height()); cy=h/2
        
        start = 0
        icon_w = 16
        gap = 10
        if self._icon:
            text_w = self._tkfont.measure(self._label) if hasattr(self, '_tkfont') else max(40,len(self._label)*7)
            group_w=icon_w+gap+text_w
            start=max(0,(w-group_w)/2)
        
        img=self._make(self._current_fill, icon=self._icon, start_x=start+icon_w/2, cy=cy)
        self._img_ref=img
        
        if img:self._canvas.create_image(0,0,image=img,anchor='nw')
        
        if self._icon:
            self._canvas.create_text(start+icon_w+gap,cy,text=self._label,fill=self._fg,font=self._font,anchor='w')
        else:
            self._canvas.create_text(w/2,cy,text=self._label,fill=self._fg,font=self._font,anchor='center')

class RoundedEntry(tk.Frame):
    def __init__(self,parent,textvariable,width=280,height=32,placeholder='Pesquisar',icon=True,**kwargs):
        self._icon=icon
        super().__init__(parent,bg=parent.cget('bg'),bd=0,highlightthickness=0,width=width,height=height,**kwargs)
        self.pack_propagate(False); self.grid_propagate(False)
        self.config(width=width, height=height)
        self._bg='#FFFFFF'; self._line='#B0C0D6'; self._placeholder=placeholder
        self._canvas=tk.Canvas(self,bg=self.cget('bg'),bd=0,highlightthickness=0); self._canvas.place(relwidth=1,relheight=1)
        self.entry=tk.Entry(self,textvariable=textvariable,bg=self._bg,fg='#18223A',insertbackground='#18223A',relief='flat',bd=0,highlightthickness=0,font=('Segoe UI',10))
        self.entry.place(x=42 if self._icon else 16,rely=.5,anchor='w',relwidth=1,width=-56 if self._icon else -32,relheight=.56)
        self._var=textvariable
        self._var.trace_add('write',lambda *a:self._update_placeholder())
        self.entry.bind('<FocusIn>',lambda e:self._update_placeholder())
        self.entry.bind('<FocusOut>',lambda e:self._update_placeholder())
        self.bind('<Button-1>',lambda e:self.entry.focus_set())
        self._canvas.bind('<Button-1>',lambda e:self.entry.focus_set())
        self.bind('<Configure>',lambda e:self._redraw())
        self.after_idle(self._redraw)

    def _update_placeholder(self):
        if not hasattr(self,'_placeholder_label'): return
        show = (not self._var.get()) and (self.focus_get() != self.entry)
        self._placeholder_label.place_forget() if not show else self._placeholder_label.place(x=42 if self._icon else 16,rely=.5,anchor='w',relheight=.56)

    def _redraw(self):
        w=self.winfo_width(); h=self.winfo_height(); r=h/2
        if w < 10: return
        self._canvas.delete('all')
        try:
            from PIL import Image,ImageDraw,ImageTk
            scale=4; im=Image.new('RGBA',(w*scale,h*scale),(0,0,0,0)); d=ImageDraw.Draw(im)
            d.rounded_rectangle((scale,scale,w*scale-scale,h*scale-scale),radius=r*scale,fill=self._bg,outline=self._line,width=scale)
            im=im.resize((w,h),Image.Resampling.LANCZOS); self._img=ImageTk.PhotoImage(im); self._canvas.create_image(0,0,image=self._img,anchor='nw')
        except Exception:
            pass
        if self._icon:
            cx, cy_icon = 19, h / 2 - 3
            self._canvas.create_oval(cx-5, cy_icon-5, cx+5, cy_icon+5, outline='#9AA9BF', width=2)
            self._canvas.create_line(cx+3, cy_icon+3, cx+8, cy_icon+8, fill='#9AA9BF', width=2, capstyle='round')
        if not hasattr(self,'_placeholder_label'):
            self._placeholder_label=tk.Label(self,text=self._placeholder,bg=self._bg,fg='#9AA9BF',font=('Segoe UI',10))
            self._placeholder_label.bind('<Button-1>',lambda e:self.entry.focus_set())
            self._update_placeholder()


class SidebarIcon(tk.Canvas):
    """Ícones vetoriais desenhados para ficar mais próximos do layout de referência."""
    def __init__(self, parent, kind, color='#FFFFFF', bg='#17181C', size=42, **kwargs):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0, **kwargs)
        self.kind=kind; self.color=color; self.size=size
        self._draw()

    def set_style(self, color=None, bg=None):
        if color is not None:
            self.color=color
        if bg is not None:
            self.configure(bg=bg)
        self._draw()

    def _rounded_rect(self, x1, y1, x2, y2, r, outline, width=2.8):
        self.create_line(x1+r, y1, x2-r, y1, fill=outline, width=width, capstyle='round')
        self.create_line(x1+r, y2, x2-r, y2, fill=outline, width=width, capstyle='round')
        self.create_line(x1, y1+r, x1, y2-r, fill=outline, width=width, capstyle='round')
        self.create_line(x2, y1+r, x2, y2-r, fill=outline, width=width, capstyle='round')
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, style='arc', outline=outline, width=width)
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, style='arc', outline=outline, width=width)
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style='arc', outline=outline, width=width)
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style='arc', outline=outline, width=width)

    def _draw(self):
        import math
        c=self
        c.delete('all')
        col=self.color
        cx=self.size/2
        cy=self.size/2
        stroke=2.9
        line=dict(fill=col,width=stroke,capstyle='round',joinstyle='round')
        if self.kind=='home':
            c.create_line(cx-13, cy-2, cx, cy-14, cx+13, cy-2, **line)
            self._rounded_rect(cx-10, cy-3, cx+10, cy+13, 4, col, stroke)
            c.create_line(cx-3.5, cy+13, cx-3.5, cy+5, cx+3.5, cy+5, cx+3.5, cy+13, **line)
        elif self.kind=='cadastro':
            self._rounded_rect(cx-10, cy-13, cx+11, cy+13, 3.8, col, stroke)
            c.create_polygon(cx+4, cy-13, cx+11, cy-13, cx+11, cy-6, fill='', outline=col, width=stroke, joinstyle='round')
            c.create_line(cx-5, cy-6, cx+2, cy-6, **line)
            c.create_line(cx-5, cy, cx+2, cy, **line)
            c.create_line(cx-5, cy+6, cx+1, cy+6, **line)
            c.create_line(cx+4, cy+4, cx+7, cy+7, **line)
            c.create_line(cx+7, cy+7, cx+12, cy, **line)
        elif self.kind=='recipe':
            c.create_line(cx-10, cy-12, cx-10, cy-7, **line)
            c.create_line(cx, cy-12, cx, cy-7, **line)
            c.create_line(cx+10, cy-12, cx+10, cy-7, **line)
            c.create_line(cx-13, cy-7, cx+13, cy-7, **line)
            self._rounded_rect(cx-14, cy-7, cx+14, cy+9, 4, col, stroke)
            c.create_arc(cx-10, cy-3, cx-2, cy+5, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_arc(cx-4, cy-3, cx+4, cy+5, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_arc(cx+2, cy-3, cx+10, cy+5, start=180, extent=180, style='arc', outline=col, width=stroke)
        elif self.kind=='product':
            c.create_arc(cx-13, cy-10, cx+13, cy+6, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_arc(cx-9, cy-14, cx+1, cy-2, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_arc(cx-1, cy-14, cx+9, cy-2, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_arc(cx+7, cy-11, cx+15, cy-1, start=180, extent=180, style='arc', outline=col, width=stroke)
            c.create_line(cx-12, cy-2, cx+12, cy-2, **line)
            c.create_polygon(cx-10, cy-1, cx+10, cy-1, cx+7, cy+12, cx-7, cy+12, fill='', outline=col, width=stroke, joinstyle='round')
            c.create_line(cx-4, cy+1, cx-1, cy+11, **line)
            c.create_line(cx+4, cy+1, cx+1, cy+11, **line)
        elif self.kind=='settings':
            pts=[]
            for i in range(16):
                ang=math.radians(i*22.5 - 90)
                radius=14 if i % 2 == 0 else 10.5
                pts.extend((cx + radius*math.cos(ang), cy + radius*math.sin(ang)))
            c.create_polygon(pts, fill='', outline=col, width=stroke, joinstyle='round')
            c.create_oval(cx-6, cy-6, cx+6, cy+6, outline=col, width=stroke)
            c.create_oval(cx-1.6, cy-1.6, cx+1.6, cy+1.6, fill=col, outline=col)


class NavItem(tk.Frame):
    """Item de navegação com botão grande, arredondado e sombreamento discreto."""
    def __init__(self, parent, icon_kind, text, command, icon_color, sidebar_bg='#17181C', **kwargs):
        super().__init__(parent, bg=sidebar_bg, bd=0, highlightthickness=0, cursor='hand2', **kwargs)
        self._sidebar_bg=sidebar_bg
        self._tile_normal=('#435CFA', '#5139E8')
        self._tile_hover=('#556BFF', '#5B41EF')
        self._tile_active=('#8B75FF', '#725CF7')
        self._border_normal='#5C66FF'
        self._border_hover='#7482FF'
        self._border_active='#9C8CFF'
        self._shadow_normal='#18255A'
        self._shadow_active='#1A1956'
        self._icon_color=icon_color
        self._text=text
        self._command=command
        self._tooltip=None
        self._active=False
        self.configure(width=88,height=96)
        self.pack_propagate(False)
        self.shadow=RoundedPanel(self, fill=self._shadow_normal, border='', radius=19, bg=sidebar_bg)
        self.shadow.place(relx=.5, rely=.5, anchor='center', x=3, y=4, width=72, height=72)
        self.tile=RoundedPanel(self, fill=self._tile_normal, border=self._border_normal, radius=19, bg=sidebar_bg)
        self.tile.place(relx=.5, rely=.5, anchor='center', width=72, height=72)
        self.icon=SidebarIcon(self.tile, icon_kind, color='#FFFFFF', bg='#4F48EF', size=44)
        self.icon.place(relx=.5, rely=.5, anchor='center')
        for w in (self, self.tile, self.tile._canvas, self.icon):
            w.bind('<Button-1>', self._click)
            w.bind('<Enter>', self._enter)
            w.bind('<Leave>', self._leave)

    def _click(self,_event=None):
        self._command()

    def _fill_center(self, fill):
        if isinstance(fill, (tuple, list)) and fill:
            return fill[0]
        return fill

    def _apply_state(self, fill, border, shadow):
        self.configure(bg=self._sidebar_bg)
        self.shadow.set_style(fill=shadow, bg=self._sidebar_bg)
        self.tile.set_style(fill=fill, border=border, bg=self._sidebar_bg)
        self.icon.set_style(color='#FFFFFF', bg=self._fill_center(fill))

    def _enter(self,_event=None):
        if not self._active:
            self._apply_state(self._tile_hover, self._border_hover, self._shadow_normal)
        self.after(180,self._show_tooltip)

    def _leave(self,_event=None):
        try:
            x,y=self.winfo_pointerxy(); target=self.winfo_containing(x,y)
            if target in (self, self.tile, self.tile._canvas, self.icon):
                return
        except Exception:
            pass
        self._hide_tooltip()
        if not self._active:
            self.set_active(False)

    def _show_tooltip(self):
        if not self.winfo_exists() or self._tooltip is not None:
            return
        try:
            x,y=self.winfo_pointerxy(); w=self.winfo_containing(x,y)
            if w not in (self, self.tile, self.tile._canvas, self.icon):
                return
        except Exception:
            pass
        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.attributes('-topmost', True)
        try: tip.attributes('-transparentcolor', '#FF00FF')
        except: pass
        tip.configure(bg='#FF00FF')
        
        tx = int(self.winfo_rootx() + self.winfo_width() + 2)
        ty = int(self.winfo_rooty() + max(0, (self.winfo_height() - 32) // 2))
        
        tip_w = len(self._text) * 8 + 24
        tip_h = 32
        tip.geometry(f'{tip_w}x{tip_h}+{tx}+{ty}')
        
        from PIL import Image, ImageDraw, ImageTk, ImageFont
        
        mask = Image.new('1', (tip_w, tip_h), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, 0, tip_w-1, tip_h-1), radius=14, fill=1)
        
        capsule = Image.new('RGBA', (tip_w, tip_h), '#101A33')
        cd = ImageDraw.Draw(capsule)
        
        try:
            fnt = ImageFont.truetype('segoeuib.ttf', 12)
        except Exception:
            try:
                fnt = ImageFont.truetype('arialbd.ttf', 12)
            except Exception:
                fnt = ImageFont.load_default()
                
        cd.text((tip_w/2, tip_h/2 - 1), self._text, fill='#FFFFFF', font=fnt, anchor='mm')
        
        im = Image.new('RGBA', (tip_w, tip_h), '#FF00FF')
        im.paste(capsule, (0, 0), mask)
        
        img_tk = ImageTk.PhotoImage(im)
        
        lbl = tk.Label(tip, image=img_tk, bg='#FF00FF', bd=0, highlightthickness=0)
        lbl.image = img_tk
        lbl.pack(fill='both', expand=True)
        self._tooltip = tip

    def _hide_tooltip(self, event=None):
        if getattr(self, '_tooltip', None):
            try:
                if isinstance(self._tooltip, tk.Toplevel):
                    self._tooltip.destroy()
                else:
                    self._tooltip.place_forget()
                    self._tooltip.destroy()
            except Exception: pass
            self._tooltip=None

    def set_active(self,active):
        self._active=active
        if active:
            self._apply_state(self._tile_active, self._border_active, self._shadow_active)
        else:
            self._apply_state(self._tile_normal, self._border_normal, self._shadow_normal)



class ReferenceSidebar(tk.Canvas):
    """Sidebar flutuante em formato de cápsula, reproduzindo a referência visual."""
    def __init__(self, parent, command, app_bg='#F4F7FC', dark_theme=False, **kwargs):
        super().__init__(parent, bg=app_bg, bd=0, highlightthickness=0, cursor='arrow', **kwargs)
        self._command=command; self._app_bg=app_bg; self._dark=dark_theme; self._active='Geral'; self._hover=None
        self._image_refs={}; self._button_items={}
        self._asset_slug={'Geral':'home','Cadastro':'cadastro','Receitas':'receitas','Produtos':'produtos','Configurações':'settings'}
        self._labels={'Geral':'Início','Cadastro':'Cadastro','Receitas':'Receitas','Produtos':'Produtos','Configurações':'Configurações'}
        self.bind('<Configure>', lambda e:self._redraw())
        self.bind('<Motion>', self._on_motion); self.bind('<Leave>', self._on_leave); self.bind('<Button-1>', self._on_click)
        self._load_assets()

    def _load_photo(self, filename):
        p=UI_ASSETS/filename
        try:
            from PIL import Image, ImageTk
            im=Image.open(p).convert('RGBA')
            if filename in ('home.png','cadastro.png','receitas.png','produtos.png','settings.png'):
                max_side=42
                scale=min(max_side/im.width,max_side/im.height,1.0)
                if scale < 1.0:
                    im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.Resampling.LANCZOS)
            img=ImageTk.PhotoImage(im); self._image_refs[filename]=img; return img
        except Exception:
            try:
                img=tk.PhotoImage(file=str(p)); self._image_refs[filename]=img; return img
            except Exception:
                return None

    def _load_assets(self):
        self._buttons={k:self._load_photo(f'{slug}.png') for k,slug in self._asset_slug.items()}

    def _draw_pil_shape(self, x, y, w, h, radius, fill, outline='', line_width=1, tag='', blur=0):
        from PIL import Image, ImageDraw, ImageTk, ImageFilter
        scale = 4
        
        if blur > 0:
            pad = blur * 2
            sw, sh = int((w + pad*2) * scale), int((h + pad*2) * scale)
            def hex_to_rgba(h_str, alpha=0):
                h_str = h_str.lstrip('#')
                return tuple(int(h_str[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)
            
            im = Image.new('RGBA', (sw, sh), hex_to_rgba(fill, 0))
            d = ImageDraw.Draw(im)
            r = int(radius * scale)
            d.rounded_rectangle((pad*scale, pad*scale, sw - pad*scale - 1, sh - pad*scale - 1), radius=r, fill=fill)
            im = im.filter(ImageFilter.GaussianBlur(blur * scale))
            im = im.resize((int(w + pad*2), int(h + pad*2)), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(im)
            self._image_refs[f"shape_{tag}_{x}_{y}_{w}_{h}_{fill}"] = img_tk
            self.create_image(x - pad, y - pad, image=img_tk, anchor='nw', tags=tag)
        else:
            sw, sh = int(w * scale), int(h * scale)
            im = Image.new('RGBA', (sw, sh), (0,0,0,0))
            d = ImageDraw.Draw(im)
            r = int(radius * scale)
            if outline:
                lw = int(line_width * scale)
                d.rounded_rectangle((lw/2, lw/2, sw - lw/2 - 1, sh - lw/2 - 1), radius=r, fill=fill, outline=outline, width=lw)
            else:
                d.rounded_rectangle((0, 0, sw - 1, sh - 1), radius=r, fill=fill)
            
            im = im.resize((int(w), int(h)), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(im)
            self._image_refs[f"shape_{tag}_{x}_{y}_{w}_{h}_{fill}"] = img_tk
            self.create_image(x, y, image=img_tk, anchor='nw', tags=tag)

    def _compute_geometry(self):
        H = max(self.winfo_height(), 600)
        y_min = 160
        bottom_max = H - 32
        available_h = max(380, bottom_max - y_min)
        
        target_h = 500
        if available_h >= target_h:
            h = target_h
            y = int(y_min + (available_h - target_h) / 2)
        else:
            h = available_h
            y = y_min
            
        top_c = y + 50
        bot_c = y + h - 50
        spacing = (bot_c - top_c) / 4
        centers = [top_c + i * spacing for i in range(5)]
        
        available_w = 150
        side_w = 68
        x = (available_w - side_w) // 2
        return x, y, side_w, h, centers

    def _get_centers(self):
        return self._compute_geometry()[4]

    def _redraw(self):
        self.delete('all'); self._button_items.clear()
        self._image_refs = {}
        
        x, y, side_w, h, centers = self._compute_geometry()
        r = side_w / 2
        sidebar = '#111C30' if not self._dark else '#F28C28'
        shadow = '#D8E1EE' if not self._dark else '#0A0A0A'
        outline = '#A9BFE0' if not self._dark else '#F6A24B'
        
        self._draw_pil_shape(x, y+4, side_w, h, r, shadow, tag='shadow', blur=6)
        self._draw_pil_shape(x, y, side_w, h, r, sidebar, outline=outline, line_width=1, tag='sidebar')
        
        for key, cy in zip(self._asset_slug.keys(), centers):
            if key == self._active:
                sel_w = side_w - 24
                sel_h = 60
                sel_r = 20
                sel_fill = '#693A16' if not self._dark else '#111C30'
                self._draw_pil_shape(x+12, cy-sel_h/2, sel_w, sel_h, sel_r, sel_fill, tag='selection')
            img = self._buttons.get(key)
            if img:
                item = self.create_image(x+side_w/2, cy, image=img, anchor='center', tags=('nav', key))
                self._button_items[key] = item

    def _hit_key(self, x, y):
        gx, gy, side_w, h, centers = self._compute_geometry()
        if not (gx <= x <= gx + side_w): return None
        for key, cy in zip(self._asset_slug.keys(), centers):
            if abs(y - cy) <= 36: return key
        return None

    def _on_click(self,event):
        key=self._hit_key(event.x,event.y)
        if key: self._command(key)

    def _on_motion(self,event):
        key=self._hit_key(event.x,event.y)
        if key != self._hover:
            self._hover=key
            self.configure(cursor='hand2' if key else 'arrow')
            if key:
                self._show_tooltip(key, event)
            else:
                self._hide_tooltip()

    def _on_leave(self,event):
        self._hover=None; self.configure(cursor='arrow')
        self._hide_tooltip()

    def _show_tooltip(self, key, event):
        self._hide_tooltip()
        labels={'Geral':'Início','Cadastro':'Cadastro','Receitas':'Receitas','Produtos':'Produtos','Configurações':'Configurações'}
        text = labels.get(key, key)
        
        gx, gy, side_w, h, centers = self._compute_geometry()
        centers_map = dict(zip(self._asset_slug.keys(), centers))
        cy = centers_map.get(key, event.y)

        tip = tk.Toplevel(self)
        tip.wm_overrideredirect(True)
        tip.attributes('-topmost', True)
        try: tip.attributes('-transparentcolor', '#FF00FF')
        except: pass
        tip.configure(bg='#FF00FF')
        
        tx = int(self.winfo_rootx() + gx + side_w + 2)
        ty = int(self.winfo_rooty() + cy - 16)
        
        tip_w = len(text) * 8 + 24
        tip_h = 32
        tip.geometry(f'{tip_w}x{tip_h}+{tx}+{ty}')
        
        from PIL import Image, ImageDraw, ImageTk, ImageFont
        
        mask = Image.new('1', (tip_w, tip_h), 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle((0, 0, tip_w-1, tip_h-1), radius=14, fill=1)
        
        fill_c = '#101A33' if not self._dark else '#2A3B5C'
        capsule = Image.new('RGBA', (tip_w, tip_h), fill_c)
        cd = ImageDraw.Draw(capsule)
        
        try:
            fnt = ImageFont.truetype('segoeuib.ttf', 12)
        except Exception:
            try:
                fnt = ImageFont.truetype('arialbd.ttf', 12)
            except Exception:
                fnt = ImageFont.load_default()
                
        cd.text((tip_w/2, tip_h/2 - 1), text, fill='#FFFFFF', font=fnt, anchor='mm')
        
        im = Image.new('RGBA', (tip_w, tip_h), '#FF00FF')
        im.paste(capsule, (0, 0), mask)
        
        img_tk = ImageTk.PhotoImage(im)
        
        lbl = tk.Label(tip, image=img_tk, bg='#FF00FF', bd=0, highlightthickness=0)
        lbl.image = img_tk
        lbl.pack(fill='both', expand=True)
        self._tooltip_win = tip

    def _hide_tooltip(self):
        if getattr(self, '_tooltip_win', None):
            try:
                if isinstance(self._tooltip_win, tk.Toplevel):
                    self._tooltip_win.destroy()
                else:
                    self._tooltip_win.place_forget()
                    self._tooltip_win.destroy()
            except Exception: pass
            self._tooltip_win=None

    def set_active(self,key):
        self._active=key; self._redraw()

    def set_theme(self,dark,app_bg):
        self._dark=dark; self._app_bg=app_bg; self.configure(bg=app_bg); self._redraw()

    def set_brand(self,name):
        pass



class RoundedDropdown(tk.Frame):
    def __init__(self, parent, textvariable, options, width=120, height=32, align='center', **kwargs):
        try: bg_col = parent.cget('bg')
        except: bg_col = getattr(parent.winfo_toplevel(), 'colors', {}).get('panel', '#F3F6FA')
        super().__init__(parent, bg=bg_col, bd=0, highlightthickness=0, width=width, height=height, cursor='hand2', **kwargs)
        self.pack_propagate(False); self.grid_propagate(False)
        self.config(width=width, height=height)
        self._var = textvariable
        self._opts = options
        self._align = align
        self._bg = '#FFFFFF'
        self._hover = '#F8FAFC'
        self._line = getattr(parent.winfo_toplevel(), 'colors', {}).get('line', '#B0C0D6')
        if self._line == '#E2EAF5' or self._line == '#DDE5F2':
            self._line = '#B0C0D6'
        self._fg = '#18223A'
        self._canvas = tk.Canvas(self, bg=self.cget('bg'), bd=0, highlightthickness=0)
        self._canvas.place(relwidth=1, relheight=1)
        self._is_hover = False
        self._canvas.bind('<Enter>', lambda e: self._on_enter())
        self._canvas.bind('<Leave>', lambda e: self._on_leave())
        self._canvas.bind('<Button-1>', lambda e: self._open_dropdown())
        self._var.trace_add('write', lambda *a: self._redraw())
        self.bind('<Configure>', lambda e: self._redraw())
        self.after_idle(self._redraw)

    def _on_enter(self): self._is_hover = True; self._redraw()
    def _on_leave(self): self._is_hover = False; self._redraw()

    def _redraw(self):
        w = max(2, self.winfo_width()); h = max(2, self.winfo_height()); r = h/2
        if w < 10: return
        self._canvas.delete('all')
        try:
            from PIL import Image, ImageDraw, ImageTk
            scale = 4; im = Image.new('RGBA', (w*scale, h*scale), (0,0,0,0)); d = ImageDraw.Draw(im)
            fill_col = self._hover if self._is_hover else self._bg
            d.rounded_rectangle((scale, scale, w*scale-scale, h*scale-scale), radius=r*scale, fill=fill_col, outline=self._line, width=scale)
            im = im.resize((w, h), Image.Resampling.LANCZOS); self._img = ImageTk.PhotoImage(im)
            self._canvas.create_image(0, 0, image=self._img, anchor='nw')
        except Exception: pass
        
        txt = self._var.get()
        if getattr(self, '_align', 'center') == 'left':
            self._canvas.create_text(16, h/2, text=txt, fill=self._fg, font=('Segoe UI', 10), anchor='w')
        else:
            self._canvas.create_text(w/2 - 6, h/2, text=txt, fill=self._fg, font=('Segoe UI', 10, 'bold'), anchor='center')
        # Draw chevron
        cx = w - 18; cy = h/2 - 2
        self._canvas.create_line(cx-4, cy, cx, cy+4, cx+4, cy, fill='#687796', width=2, capstyle='round', joinstyle='round')

    def _open_dropdown(self):
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
            col = '#BA5200' if opt == self._var.get() else '#18223A'
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
def get_work_area():
    try:
        import ctypes
        from ctypes import wintypes
        class RECT(ctypes.Structure):
            _fields_=[('left',wintypes.LONG),('top',wintypes.LONG),('right',wintypes.LONG),('bottom',wintypes.LONG)]
        rect = RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        pass
    return None

class VerticalPillScrollbar(tk.Canvas):
    def __init__(self, parent, tree, **kwargs):
        super().__init__(parent, width=8, bg=parent.cget('bg'), bd=0, highlightthickness=0, **kwargs)
        self.tree = tree
        self.tree.configure(yscrollcommand=self._on_scroll)
        self.bind('<Configure>', self._redraw)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self._pos = (0.0, 1.0)
        self._drag_data = {'y': 0, 'start_pos': 0.0}

    def _on_scroll(self, first, last):
        first, last = float(first), float(last)
        self._pos = (first, last)
        if first <= 0.001 and last >= 0.999:
            if self.winfo_ismapped():
                self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side='right', fill='y', pady=20, padx=(0, 4))
            self.tk.call('raise', self._w)
        self._redraw()

    def _redraw(self, e=None):
        w, h = self.winfo_width(), self.winfo_height()
        if h < 10: return
        self.delete('all')
        first, last = self._pos
        if first <= 0.001 and last >= 0.999: return
        r = w / 2
        y1 = max(r, first * h)
        y2 = min(h - r, last * h)
        if y2 - y1 < 20:
            mid = (y1 + y2) / 2
            y1, y2 = mid - 10, mid + 10
            y1 = max(r, y1)
            y2 = min(h - r, max(y1+20, y2))
        self.create_line(w / 2, y1, w / 2, y2, fill='#A0ABB9', width=w, capstyle='round')

    def _on_press(self, e):
        h = self.winfo_height()
        first, last = self._pos
        y1 = first * h; y2 = last * h
        if y1 <= e.y <= y2:
            self._drag_data['y'] = e.y
            self._drag_data['start_pos'] = first
        else:
            new_first = max(0.0, min(1.0 - (last-first), (e.y / h) - (last-first)/2))
            self.tree.yview_moveto(new_first)

    def _on_drag(self, e):
        h = self.winfo_height()
        dy = e.y - self._drag_data['y']
        first, last = self._pos
        delta_pos = dy / h
        new_first = max(0.0, min(1.0 - (last-first), self._drag_data['start_pos'] + delta_pos))
        self.tree.yview_moveto(new_first)

class CustomHistoryModal(Modal):
    def __init__(self, master, title, columns, rows, current_row_data=None):
        super().__init__(master, title, '760x520')
        
        self.colors = master.colors if hasattr(master, 'colors') else {'bg': '#F4F7FC', 'primary': '#0D6EFD', 'text': '#18223A', 'line': '#E2EAF5'}
        self.configure(bg=self.colors.get('bg', '#F4F7FC'))
        
        # Footer
        act_frame = tk.Frame(self, bg=self.colors.get('bg', '#F4F7FC'))
        act_frame.pack(side='bottom', fill='x', padx=24, pady=20)
        RoundedActionButton(act_frame, '📄 Exportar Relatório', self.export_csv, width=180, height=36, fill='#EAFaf1', hover='#D4E6DC', fg='#1E833F').pack(side='right')

        # Header Area
        top_bar = tk.Frame(self, bg=self.colors.get('bg', '#F4F7FC'))
        top_bar.pack(side='top', fill='x', padx=24, pady=(24, 16))
        
        # Big Title
        internal_title = title.replace("Histórico: ", "")
        tk.Label(top_bar, text=internal_title, bg=self.colors.get('bg', '#F4F7FC'), fg=self.colors.get('text', '#18223A'), font=('Segoe UI', 16, 'bold')).pack(side='left')
        
        # Search Box
        search_frame = tk.Frame(top_bar, bg=self.colors.get('bg', '#F4F7FC'))
        search_frame.pack(side='right')
        self.search_var = tk.StringVar()
        search_entry = RoundedEntry(search_frame, textvariable=self.search_var, width=180, height=32, placeholder="Filtrar...")
        search_entry.pack()
        self.search_var.trace_add('write', lambda *_: self._on_search())
        
        # Table Area
        table_frame = tk.Frame(self, bg=self.colors.get('bg', '#F4F7FC'))
        table_frame.pack(fill='both', expand=True, padx=24, pady=(0, 0))
        
        self.header_canvas = tk.Canvas(table_frame, height=36, bg=self.colors.get('bg', '#F4F7FC'), highlightthickness=0)
        self.header_canvas.pack(side='top', fill='x')
        
        tree_container = tk.Frame(table_frame, bg=self.colors.get('bg', '#F4F7FC'))
        tree_container.pack(side='top', fill='both', expand=True)
        
        self.tree = ttk.Treeview(tree_container, columns=[c[0] for c in columns], show='tree')
        self.tree.column('#0', width=0, stretch=False)
        self.tree.pack(side='left', fill='both', expand=True)
        
        # New Scrollbar
        self.vsb = VerticalPillScrollbar(tree_container, self.tree)
        
        # Formatting & Sorting setup
        self._sort_dirs = {}
        for k, t, w in columns:
            self.tree.column(k, width=w, anchor='center')
            
        self.raw_rows = rows
        self.columns = columns
        
        # Inject current value as first row if it's not already there
        self.display_rows = list(rows)
        if current_row_data is not None:
            from datetime import datetime
            now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + " (Hoje)"
            mock_row = [now_str]
            for v in current_row_data:
                mock_row.append(v)
            self.display_rows.insert(0, tuple(mock_row))

        self._populate_tree(self.display_rows)
        
        self.header_canvas.bind('<Configure>', self._draw_header)
        self.tree.bind('<Configure>', lambda e: self.tree.after_idle(self._draw_header))
        self.after_idle(self._draw_header)

    def _draw_header(self, e=None):
        c = self.header_canvas
        c.delete('all')
        w = max(c.winfo_width(), 2)
        h = max(c.winfo_height(), 2)
        r = min(h/2, 18)
        fill = '#EEF4FB'
        
        c.create_rectangle(r, 0, w-r, h, fill=fill, outline='')
        c.create_rectangle(0, r, w, h-r, fill=fill, outline='')
        c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=fill, outline=fill)
        c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=fill, outline=fill)
        c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=fill, outline=fill)
        c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=fill, outline=fill)
        
        try: x_offset = float(self.tree.xview()[0]) * sum(int(self.tree.column(c[0], 'width')) for c in self.columns)
        except Exception: x_offset = 0
        
        x0 = -x_offset
        for idx, (key, txt, width) in enumerate(self.columns):
            try: cw = int(self.tree.column(key, 'width'))
            except Exception: cw = width
            
            align = 'w' if key in ('data', 'registro', 'marca') else 'center'
            anchor_x = x0 + 12 if align == 'w' else x0 + cw/2
            
            arrow_txt = ''
            if key in self._sort_dirs:
                arrow_txt = ' ▼' if not self._sort_dirs[key] else ' ▲'
            
            full_txt = txt + arrow_txt if align == 'w' else arrow_txt + txt
            tid = c.create_text(anchor_x, h/2, text=full_txt, fill='#60769D', font=('Segoe UI', 9, 'bold'), anchor=align)
            
            hitbox = c.create_rectangle(x0, 0, x0+cw, h, fill='', outline='', tags=(f'hdr_{key}',))
            c.tag_bind(f'hdr_{key}', '<Enter>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#BA5200'))
            c.tag_bind(f'hdr_{key}', '<Leave>', lambda e, t=tid, c=c: c.itemconfig(t, fill='#60769D'))
            c.tag_bind(f'hdr_{key}', '<Button-1>', lambda e, k=key: self._sort_col(k))
            c.tag_bind(f'hdr_{key}', '<Enter>', lambda e: c.config(cursor='hand2'), add='+')
            c.tag_bind(f'hdr_{key}', '<Leave>', lambda e: c.config(cursor=''), add='+')
            
            if idx < len(self.columns) - 1:
                c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
            x0 += cw

    def _sort_col(self, col):
        rev = self._sort_dirs.get(col, False)
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try: l.sort(key=lambda t: float(t[0].replace('R$ ','').replace('.','').replace(',','.')), reverse=not rev)
        except: l.sort(reverse=not rev)
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
        self._sort_dirs = {col: not rev}
        self._draw_header()

    def _populate_tree(self, rows):
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            formatted = list(r)
            for i, val in enumerate(formatted):
                col_key = self.columns[i][0]
                if col_key in ('custo', 'valor'):
                    try:
                        v = float(str(val).replace('R$ ','').replace('.','').replace(',','.'))
                        formatted[i] = f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    except: pass
                if col_key in ('registro', 'data') and isinstance(val, str):
                    val_str = val
                    is_hoje = '(Hoje)' in val_str
                    val_str = val_str.replace(' (Hoje)', '')
                    if 'T' in val_str and len(val_str) >= 16:
                        dt, tm = val_str.split('T')
                        y,m,d = dt.split('-')
                        formatted[i] = f"{d}/{m}/{y} {tm[:5]}"
                    elif '-' in val_str and len(val_str) >= 10:
                        y,m,d = val_str[:10].split('-')
                        formatted[i] = f"{d}/{m}/{y} 00:00"
                    if is_hoje: formatted[i] += " (Hoje)"
            self.tree.insert('', 'end', values=tuple(formatted))
            
    def _on_search(self):
        q = self.search_var.get().strip().lower()
        if not q:
            self._populate_tree(self.display_rows)
            return
        filtered = []
        for r in self.display_rows:
            if any(q in str(v).lower() for v in r):
                filtered.append(r)
        self._populate_tree(filtered)
        
    def export_csv(self):
        import csv
        from tkinter import filedialog, messagebox
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if f:
            with open(f, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow([c[1] for c in self.columns])
                for k in self.tree.get_children(''):
                    writer.writerow(self.tree.item(k)['values'])
            messagebox.showinfo("Exportar", f"Relatório salvo com sucesso em:\n{f}", parent=self)
class ListDialog(Modal):
    def __init__(self,master,title,columns,rows):
        super().__init__(master,title,'820x460')
        tree=ttk.Treeview(self,columns=[c[0] for c in columns],show='headings')
        for k,t,w in columns:tree.heading(k,text=t);tree.column(k,width=w)
        for r in rows:tree.insert('','end',values=tuple(r))
        tree.pack(fill='both',expand=True,padx=12,pady=12)
        ttk.Button(self,text='Fechar',command=self.destroy).pack(pady=(0,12))


