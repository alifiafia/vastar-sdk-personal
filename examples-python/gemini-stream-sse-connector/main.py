
# main.py
from connector import handle

result = handle({
    "prompt": "Explain quantum computing simply",
    "max_tokens": 120
})

print("\n=== CONNECTOR OUTPUT ===")
print(result["text"])
