import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# 1. Fix the buttons in main.py
# Old buttons: RoundedActionButton(bar, '🗑️ Excluir', ..., width=120, height=40, fill='#FCE8E8', hover='#F9D1D1', fg='#D93838')
text = re.sub(
    r"RoundedActionButton\(bar,\s*['\"][\w\W]*?Excluir['\"],\s*(lambda: self\._run_normal_action\([^)]+\)),\s*width=120,\s*height=40,\s*fill='#[A-Fa-f0-9]+',\s*hover='#[A-Fa-f0-9]+',\s*fg='#[A-Fa-f0-9]+'\)",
    r"RoundedActionButton(bar, '<delete> Excluir', \1, width=110, height=40, fill='#FEF2F2', hover='#FEE2E2', fg='#991B1B')",
    text
)

# 2. Add 'delete' to _detect_icon and _clean_text (Wait, they already have it! Let's check)
# My _clean_text already had <delete>.
# But we need to add the drawing code for 'delete' in _make.
old_convert = """                elif icon=='convert':
                    line([cx-8*scale, c_y-3*scale, cx+6*scale, c_y-3*scale])
                    line([cx+3*scale, c_y-6*scale, cx+6*scale, c_y-3*scale, cx+3*scale, c_y])
                    line([cx+8*scale, c_y+3*scale, cx-6*scale, c_y+3*scale])
                    line([cx-3*scale, c_y, cx-6*scale, c_y+3*scale, cx-3*scale, c_y+6*scale])"""

new_delete = """                elif icon=='convert':
                    line([cx-8*scale, c_y-3*scale, cx+6*scale, c_y-3*scale])
                    line([cx+3*scale, c_y-6*scale, cx+6*scale, c_y-3*scale, cx+3*scale, c_y])
                    line([cx+8*scale, c_y+3*scale, cx-6*scale, c_y+3*scale])
                    line([cx-3*scale, c_y, cx-6*scale, c_y+3*scale, cx-3*scale, c_y+6*scale])
                elif icon=='delete':
                    # Lid
                    line([cx-5*scale, c_y-5*scale, cx+5*scale, c_y-5*scale])
                    # Handle
                    line([cx-2*scale, c_y-7*scale, cx+2*scale, c_y-7*scale])
                    # Body (using lines to make a U shape with slight taper)
                    line([cx-4*scale, c_y-4*scale, cx-3*scale, c_y+6*scale])
                    line([cx+4*scale, c_y-4*scale, cx+3*scale, c_y+6*scale])
                    line([cx-3*scale, c_y+6*scale, cx+3*scale, c_y+6*scale])
                    # Vertical slits
                    line([cx-1*scale, c_y-2*scale, cx-0.5*scale, c_y+4*scale])
                    line([cx+1*scale, c_y-2*scale, cx+0.5*scale, c_y+4*scale])"""

if old_convert in text:
    text = text.replace(old_convert, new_delete)
    
with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched delete icon and styling")
