import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

missing_methods = """
    def _on_motion(self, event):
        key = self._get_hover_key(event.y)
        if key != self._hover:
            self._hover = key
            if key:
                self.configure(cursor='hand2')
                self._show_tooltip(key)
            else:
                self.configure(cursor='arrow')
                self._hide_tooltip()
            self._redraw()

    def _on_leave(self, event):
        self._hover = None
        self.configure(cursor='arrow')
        self._hide_tooltip()
        self._redraw()

    def _on_click(self, event):
        key = self._get_hover_key(event.y)
        if key:
            self._command(key)
            self.set_active(key)

    def set_active(self, key):
        self._active = key
        self._redraw()
"""

# Append missing methods after _hide_tooltip
code = code.replace("self._tooltip_win=None", "self._tooltip_win=None\n" + missing_methods)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
