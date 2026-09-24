import ast

with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_gear_block = '''                        def make_gear(color):
                            img = Image.new('RGBA', (128, 128), (0,0,0,0))
                            draw = ImageDraw.Draw(img)
                            gcx, gcy = 64, 64
                            
                            # 1. Anel principal robusto
                            draw.ellipse([gcx-32, gcy-32, gcx+32, gcy+32], fill=color)
                            
                            # 2. Oito "dentes" chatos usando blocos/linhas grossas
                            for i in range(8):
                                angle = i * (math.pi / 4)
                                x1 = gcx + 50 * math.cos(angle)
                                y1 = gcy + 50 * math.sin(angle)
                                x2 = gcx - 50 * math.cos(angle)
                                y2 = gcy - 50 * math.sin(angle)
                                draw.line([x1, y1, x2, y2], fill=color, width=28)
                                
                            # 3. Furo central maciço
                            draw.ellipse([gcx-16, gcy-16, gcx+16, gcy+16], fill='#EEF4FB')
                            
                            return ImageTk.PhotoImage(img.resize((16, 16), Image.Resampling.LANCZOS))'''

new_gear_block = '''                        def make_gear(color):
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

if old_gear_block in text:
    text = text.replace(old_gear_block, new_gear_block)
else:
    print("WARNING: Could not find old donut block.")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Donut eliminated. Gear proportions fixed.")
