
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:4b"

question = """
A shopkeeper buys an item for Rs. 800
and sells it for Rs. 1000.
Calculate the profit percentage step by step.
"""

payload = {
    "model": MODEL,
    "prompt": question,
    "stream": False,
    "think": False,
    "options": {
        "temperature": 0
    }
}

response = requests.post(OLLAMA_URL, json=payload, timeout=180)
response.raise_for_status()

result = response.json()

print("\nMODEL ANSWER:\n")
print(result["response"])

print("\nEXECUTION TIME:")
print(result.get("total_duration", 0) / 1_000_000_000, "seconds")

print("\nPROMPT TOKENS:", result.get("prompt_eval_count", 0))
print("GENERATED TOKENS:", result.get("eval_count", 0))
