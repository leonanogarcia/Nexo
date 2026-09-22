import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_draw = """        def _draw_status(text):
            self.mat_status_wrap.delete('all')
            self.mat_status_wrap.create_polygon(20, 1, 90, 1, 109, 1, 109, 20, 109, 39, 90, 39, 20, 39, 1, 39, 1, 20, 1, 1, smooth=True, fill=self.colors['field'], outline='#E2EAF5')
            self.mat_status_wrap.create_text(45, 20, text=text, fill=self.colors['text'], font=('Segoe UI', 10, 'bold'), anchor='center')
            self.mat_status_wrap.create_text(90, 20, text='▼', fill=self.colors['muted'], font=('Segoe UI', 8), anchor='center')"""

new_draw = """        def _draw_status(text):
            self.mat_status_wrap.delete('all')
            w = 110; h = 40
            # Draw a perfect capsule
            self.mat_status_wrap.create_arc(2, 2, 38, 38, start=90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='pieslice')
            self.mat_status_wrap.create_arc(2, 2, 38, 38, start=90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='arc')
            self.mat_status_wrap.create_arc(w-38, 2, w-2, 38, start=-90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='pieslice')
            self.mat_status_wrap.create_arc(w-38, 2, w-2, 38, start=-90, extent=180, fill='#FFFFFF', outline='#E2EAF5', style='arc')
            self.mat_status_wrap.create_rectangle(20, 2, w-20, 38, fill='#FFFFFF', outline='')
            self.mat_status_wrap.create_line(20, 2, w-20, 2, fill='#E2EAF5')
            self.mat_status_wrap.create_line(20, 38, w-20, 38, fill='#E2EAF5')
            # Text and icon
            self.mat_status_wrap.create_text(45, 20, text=text, fill=self.colors['text'], font=('Segoe UI', 10, 'bold'), anchor='center')
            self.mat_status_wrap.create_text(90, 20, text='▼', fill=self.colors['muted'], font=('Segoe UI', 8), anchor='center')"""

code = code.replace(old_draw, new_draw)

# The search bar in the screenshot looks very faded. Let's make sure the text isn't light gray when typing!
# RoundedEntry handles that, but I'm just making sure.

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
