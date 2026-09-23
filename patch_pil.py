import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Fix rec_empty_overlay
old_rec_try = """        try:
            from PIL import Image, ImageTk
            import pathlib
            UI_ASSETS = pathlib.Path(__file__).parent / 'assets'
            img_path = UI_ASSETS / 'empty_state_reference_exact.png'
            self._rec_empty_img = ImageTk.PhotoImage(Image.open(img_path))"""

new_rec_try = """        try:
            from PIL import Image, ImageTk
            img_path = UI_ASSETS / 'empty_state_reference_exact.png'
            self._rec_empty_img = ImageTk.PhotoImage(Image.open(img_path))"""
text = text.replace(old_rec_try, new_rec_try)

# Fix prod_empty_overlay
old_prod_try = """        try:
            from PIL import Image, ImageTk
            import pathlib
            UI_ASSETS = pathlib.Path(__file__).parent / 'assets'
            img_path = UI_ASSETS / 'empty_state_reference_exact.png'
            self._prod_empty_img = ImageTk.PhotoImage(Image.open(img_path))"""

new_prod_try = """        try:
            from PIL import Image, ImageTk
            img_path = UI_ASSETS / 'empty_state_reference_exact.png'
            self._prod_empty_img = ImageTk.PhotoImage(Image.open(img_path))"""
text = text.replace(old_prod_try, new_prod_try)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Fixed PIL image pathing!")
