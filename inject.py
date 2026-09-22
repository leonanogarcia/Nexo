import sys

with open('main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

with open('reconstructed_block.py', 'r', encoding='utf-8') as f:
    block_code = f.read()

# Make sure it's not already injected (to avoid doubling up)
if "def cadastro(self, f):" not in main_code:
    main_code = main_code.replace("    def edit_selected_material(self):", block_code + "\n    def edit_selected_material(self):")
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(main_code)
    print("Injected successfully!")
else:
    print("Already there!")
