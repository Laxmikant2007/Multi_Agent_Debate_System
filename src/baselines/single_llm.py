
import csv
import json
from pathlib import Path

from src.ollama_client import generate_response


BASE_DIR = Path(__file__).resolve().parents[2]
DATASET_FILE = BASE_DIR / "dataset" / "agent_questions.csv"
RESULTS_DIR = BASE_DIR / "results"

RESULTS_DIR.mkdir(exist_ok=True)


def run_single_llm(question, context="", options=""):
    """
    Configuration A:
    Single LLM generates an answer directly,
    without a special reasoning or debate prompt.
    """

    prompt = f"""
Solve this question. Be concise.

Show at most 3 calculation steps.
Do not repeat the question.
Do not explain basic concepts.
Do not include lengthy reasoning.

Context:
{context}

Question:
{question}

Options:
{options}

Answer:
"""

    result = generate_response(prompt, max_tokens=300)

    return {
        "answer": result["answer"],
        "time_seconds": result["time_seconds"],
        "prompt_tokens": result["prompt_tokens"],
        "generated_tokens": result["generated_tokens"],
        "done_reason": result["done_reason"],
        "complete": result["complete"]
    }


def main():

    with open(DATASET_FILE, "r", encoding="utf-8-sig") as file:
        questions = list(csv.DictReader(file))

    output_file = RESULTS_DIR / "configuration_A_results.csv"

    results = []

    print("CONFIGURATION A: SINGLE LLM")
    print("-" * 50)
    print("Total questions:", len(questions))

    for index, item in enumerate(questions[:1], start=1):

        print(
            f"\nProcessing {index}/{len(questions)}: "
            f"{item['question_id']}"
        )

        result = run_single_llm(
            question=item["question"],
            context=item["context"] if item["context"] else "",
            options=item["options"] if item["options"] else ""
        )

        results.append({
            "question_id": item["question_id"],
            "dataset_name": item["dataset_name"],
            "answer": result["answer"],
            "time_seconds": result["time_seconds"],
            "prompt_tokens": result["prompt_tokens"],
            "generated_tokens": result["generated_tokens"],
            "done_reason": result["done_reason"],
            "complete": result["complete"]
        })

        print("Time:", result["time_seconds"], "seconds")
        print("Generated tokens:", result["generated_tokens"])
        print("Generation complete:", result["complete"])

    fieldnames = list(results[0].keys())

    with open(output_file, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "-" * 50)
    print("CONFIGURATION A COMPLETED")
    print("Questions processed:", len(results))
    print("Results saved to:", output_file)


if __name__ == "__main__":
    main()
