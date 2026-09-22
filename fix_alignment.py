import re

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix the X alignment to match the logo (which is at x=29)
code = code.replace("x = 22 if W >= 600 else 8", "x = 29 if W >= 600 else 8")
code = code.replace("x=22 if W>=600 else 8", "x = 29 if W >= 600 else 8")

# Let's also make sure the logo is resized with LANCZOS
# In `_place_nexo_brand`:
# img=img.resize((max(1,int(img.width*scale)),max(1,int(img.height*scale))),Image.Resampling.LANCZOS)
# It is already using LANCZOS! Why did the user say "logo sem qualidade"?
# Maybe the original image is bad? Or maybe they meant the sidebar icons were bad.

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
