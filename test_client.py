from src.ollama_client import generate_response

prompt = "What is 200 divided by 800, multiplied by 100? Give only the numerical answer."

result = generate_response(prompt, max_tokens=500)

print("\nANSWER:")
print(result["answer"])

print("\nPERFORMANCE:")
print("Execution time:", result["time_seconds"], "seconds")
print("Prompt tokens:", result["prompt_tokens"])
print("Generated tokens:", result["generated_tokens"])
print("Done reason:", result["done_reason"])
print("Complete:", result["complete"])