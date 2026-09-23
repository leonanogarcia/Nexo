import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Dropdown active color
text = text.replace(
    "col = '#2F67B1' if opt == self._var.get() else '#18223A'",
    "col = '#D96F0B' if opt == self._var.get() else '#18223A'"
)

# Checkbox checked color
text = text.replace(
    "color = '#2B3D55' if is_checked else '#A0ABB9'",
    "color = '#D96F0B' if is_checked else '#A0ABB9'"
)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched additional blue elements")
