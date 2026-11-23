
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"


def generate_response(prompt, max_tokens=500):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0,
            "num_predict": max_tokens
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )

        response.raise_for_status()
        data = response.json()

        return {
            "answer": data.get("response", "").strip(),
            "time_seconds": round(
                data.get("total_duration", 0) / 1_000_000_000, 3
            ),
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "generated_tokens": data.get("eval_count", 0),
            "done_reason": data.get("done_reason", "unknown"),
            "complete": data.get("done_reason") != "length"
        }

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Could not connect to Ollama: {error}"
        ) from error
