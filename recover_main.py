import json

log_path = r"C:\Users\lgarcia\.gemini\antigravity\brain\38dcee48-7484-4ae3-bcff-47f541e2c844\.system_generated\logs\transcript_full.jsonl"
largest_code = ""

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            # check if it's a tool response
            if 'tool_calls' in data:
                continue # this is a call, not a response
            
            # Check content for python code
            content = data.get('content', '')
            if 'class App(tk.Tk):' in content and 'def cadastro(self' in content:
                if len(content) > len(largest_code):
                    largest_code = content
        except:
            pass

print(f"Found code of length {len(largest_code)}")
if largest_code:
    with open('recovered_main.py', 'w', encoding='utf-8') as out:
        out.write(largest_code)
