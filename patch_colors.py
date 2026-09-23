import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# 1. Change primary action buttons from Blue to Nexo Orange
text = text.replace(
    "width=130, height=49, fill='#2F67B1', hover='#255894'",
    "width=130, height=49, fill='#F28C28', hover='#D96F0B'"
)
text = text.replace(
    "width=150,height=40,fill='#2F67B1',hover='#255894'",
    "width=150,height=40,fill='#F28C28',hover='#D96F0B'"
)

# 2. Change the sidebar selection highlight from blue to a soft orange
# Current code in _redraw: sel_fill = '#304763' if not self._dark else '#F6A45A'
text = text.replace(
    "sel_fill = '#304763' if not self._dark else '#F6A45A'",
    "sel_fill = '#693A16' if not self._dark else '#F6A45A'" # Soft burnt orange glow
)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched colors")
