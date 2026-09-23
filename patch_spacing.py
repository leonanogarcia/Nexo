import re

with open('main.py', 'rb') as f:
    text = f.read().decode('utf-8')

# Fix header padding
text = text.replace("head.pack(fill='x',padx=18,pady=(58,14))", "head.pack(fill='x',padx=18,pady=(32,14))")

# Fix logo position
text = text.replace("self.nexo_brand_label.place(x=10,y=54,width=135,height=105)", "self.nexo_brand_label.place(x=10,y=26,width=135,height=105)")

with open('main.py', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Patched header spacing")
