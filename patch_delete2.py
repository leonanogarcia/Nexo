import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Change button colors
text = text.replace("width=105, height=40, fill='#FEF2F2', hover='#FEE2E2', fg='#991B1B')", "width=105, height=40, fill='#FFF5F5', hover='#FFEBEB', fg='#C53030')")

# Change RoundedActionButton delete icon to use the PNG
old_delete = """                elif icon=='delete':
                    line([cx-5*scale, c_y-5*scale, cx+5*scale, c_y-5*scale])
                    line([cx-2*scale, c_y-7*scale, cx+2*scale, c_y-7*scale])
                    line([cx-4*scale, c_y-4*scale, cx-3*scale, c_y+6*scale])
                    line([cx+4*scale, c_y-4*scale, cx+3*scale, c_y+6*scale])
                    line([cx-3*scale, c_y+6*scale, cx+3*scale, c_y+6*scale])
                    line([cx-1*scale, c_y-2*scale, cx-0.5*scale, c_y+4*scale])
                    line([cx+1*scale, c_y-2*scale, cx+0.5*scale, c_y+4*scale])"""

new_delete = """                elif icon=='delete':
                    import pathlib
                    UI_ASSETS = pathlib.Path(__file__).parent / 'ui_assets'
                    try:
                        icon_img = Image.open(UI_ASSETS / 'action_delete_reference_exact.png').convert('RGBA')
                        # Resize to fit nicely (about 14x16 at 1x)
                        icon_img = icon_img.resize((int(14*scale), int(16*scale)), Image.Resampling.LANCZOS)
                        
                        # Recolor the icon to match self._fg exactly
                        r_c, g_c, b_c = self.winfo_rgb(col)
                        r_c, g_c, b_c = r_c//256, g_c//256, b_c//256
                        data = icon_img.getdata()
                        new_data = [(r_c, g_c, b_c, item[3]) for item in data]
                        icon_img.putdata(new_data)
                        
                        # Paste centered
                        im.paste(icon_img, (int(cx - 7*scale), int(c_y - 8*scale)), icon_img)
                    except Exception:
                        line([cx-5*scale, c_y-5*scale, cx+5*scale, c_y-5*scale])"""

if old_delete in text:
    text = text.replace(old_delete, new_delete)

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched delete icon and colors")
