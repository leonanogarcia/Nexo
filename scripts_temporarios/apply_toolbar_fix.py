import re

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix RoundedActionButton bug
old_rab_init = """self.pack_propagate(False); self._fill=fill; self._hover=hover; self._fg=fg; self._text=text; self._command=command; self._font=font
        self._canvas=tk.Canvas(self,bg=self.cget('bg'),bd=0,highlightthickness=0); self._canvas.pack(fill='both',expand=True)"""
new_rab_init = """self.pack_propagate(False); self._base_fill=fill; self._hover_fill=hover; self._current_fill=fill; self._fg=fg; self._text=text; self._command=command; self._font=font
        self._canvas=tk.Canvas(self,bg=self.cget('bg'),bd=0,highlightthickness=0); self._canvas.pack(fill='both',expand=True)"""
text = text.replace(old_rab_init, new_rab_init)

old_rab_make = """img=self._make(self._fill, icon=self._icon, start_x=start+icon_w/2, cy=cy)"""
new_rab_make = """img=self._make(self._current_fill, icon=self._icon, start_x=start+icon_w/2, cy=cy)"""
text = text.replace(old_rab_make, new_rab_make)

old_rab_events = """def _on_enter(self,e): self._fill0=self._fill; self._fill=self._hover; self._redraw()
    def _on_leave(self,e): self._fill=getattr(self,'_fill0',self._fill); self._redraw()
    def _click(self,e=None): self._command()"""
new_rab_events = """def _on_enter(self,e): self._current_fill=self._hover_fill; self._redraw()
    def _on_leave(self,e): self._current_fill=self._base_fill; self._redraw()
    def _click(self,e=None): 
        self._current_fill=self._base_fill; self._redraw()
        self.after(10, self._command)"""
text = text.replace(old_rab_events, new_rab_events)

# 2. Fix Toolbar Height & Padding (_build_page_toolbar)
old_toolbar = """shell=RoundedPanel(parent, fill=self.colors['panel'], border='', radius=22, bg=self.colors['bg'], height=84)
        shell.pack(fill='x', padx=0, pady=(0,14)); shell.pack_propagate(False)
        inner=tk.Frame(shell,bg=self.colors['panel'])
        inner.pack(fill='both', expand=True, padx=24, pady=17)"""
new_toolbar = """shell=RoundedPanel(parent, fill=self.colors['panel'], border='', radius=22, bg=self.colors['bg'], height=64)
        shell.pack(fill='x', padx=0, pady=(0,8)); shell.pack_propagate(False)
        inner=tk.Frame(shell,bg=self.colors['panel'])
        inner.pack(fill='both', expand=True, padx=24, pady=11)"""
text = text.replace(old_toolbar, new_toolbar)

# 3. Change height=49 to height=42
text = text.replace("height=49", "height=42")

# 4. Change hover color #D96F0B to #BA5200 (darker, stronger orange)
text = text.replace("#D96F0B", "#BA5200")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Hover fix e Toolbar Ajustes aplicados!")
