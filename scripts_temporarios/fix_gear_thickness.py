import ast
import math

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_gear = '''                        def make_gear(color):
                            img = Image.new('RGBA', (128, 128), (0,0,0,0))
                            draw = ImageDraw.Draw(img)
                            gcx, gcy = 64, 64
                            
                            # 1. Dentes compridos e finos cruzando a imagem (4 linhas = 8 dentes)
                            # Deixando bastante "espaço vazio" para não virar rosquinha no anti-aliasing
                            for i in range(4):
                                angle = i * (math.pi / 4)
                                x1 = gcx + 58 * math.cos(angle)
                                y1 = gcy + 58 * math.sin(angle)
                                x2 = gcx - 58 * math.cos(angle)
                                y2 = gcy - 58 * math.sin(angle)
                                draw.line([x1, y1, x2, y2], fill=color, width=18)
                            
                            # 2. Anel central mais fino (menos massa)
                            draw.ellipse([gcx-32, gcy-32, gcx+32, gcy+32], fill=color)
                            
                            # 3. Furo bem maior
                            draw.ellipse([gcx-18, gcy-18, gcx+18, gcy+18], fill='#EEF4FB')
                            
                            return ImageTk.PhotoImage(img.resize((16, 16), Image.Resampling.LANCZOS))'''

new_gear = '''                        def make_gear(color):
                            img = Image.new('RGBA', (128, 128), (0,0,0,0))
                            draw = ImageDraw.Draw(img)
                            gcx, gcy = 64, 64
                            
                            for i in range(4):
                                angle = i * (math.pi / 4)
                                x1 = gcx + 52 * math.cos(angle)
                                y1 = gcy + 52 * math.sin(angle)
                                x2 = gcx - 52 * math.cos(angle)
                                y2 = gcy - 52 * math.sin(angle)
                                draw.line([x1, y1, x2, y2], fill=color, width=22)
                            
                            draw.ellipse([gcx-36, gcy-36, gcx+36, gcy+36], fill=color)
                            
                            draw.ellipse([gcx-14, gcy-14, gcx+14, gcy+14], fill='#EEF4FB')
                            
                            return ImageTk.PhotoImage(img.resize((16, 16), Image.Resampling.LANCZOS))'''

if old_gear in text:
    text = text.replace(old_gear, new_gear)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Gear fixed')
else:
    print('Failed to find gear')
