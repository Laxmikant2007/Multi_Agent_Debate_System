
import csv
import json
import re
import time
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parents[1]

PILOT_FILE = BASE_DIR / "dataset" / "pilot_questions.csv"
ANSWER_FILE = BASE_DIR / "dataset" / "reasoning_questions.csv"

RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = RESULTS_DIR / "pilot_model_comparison.csv"

OLLAMA_URL = "http://localhost:11434/api/generate"

MODELS = [
    "qwen2.5:3b",
    "qwen2.5:7b",
    "qwen3:4b",
    "deepseek-r1:7b"
]


def load_csv(path):
    with open(path, "r", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def prepare_options(options):
    if not options:
        return ""

    try:
        choices = json.loads(options)
    except json.JSONDecodeError:
        return options

    if not isinstance(choices, list):
        return str(choices)

    return "\n".join(
        f"{chr(65 + i)}. {str(choice).split(')', 1)[-1].strip()}"
        for i, choice in enumerate(choices)
    )


def build_prompt(item):

    question = item["question"]
    context = item["context"]
    options = prepare_options(item["options"])

    if item["answer_type"] == "numeric":
        instruction = (
            "Solve the numerical reasoning problem. "
            "Put your final numerical answer on the last line "
            "in this format: FINAL: 123"
        )
    else:
        instruction = (
            "Solve the multiple-choice reasoning problem. "
            "Select exactly one option. "
            "Put your final option letter on the last line "
            "in this format: FINAL: A"
        )

    return f"""
{instruction}

Context:
{context}

Question:
{question}

Options:
{options}

Do not guess. Provide your answer clearly.
"""


def extract_prediction(response, answer_type):

    if answer_type == "numeric":

        final_match = re.findall(
            r"FINAL\s*:\s*(-?\d[\d,]*(?:\.\d+)?)",
            response,
            re.IGNORECASE
        )

        if final_match:
            return final_match[-1].replace(",", "")

        numbers = re.findall(
            r"-?\d[\d,]*(?:\.\d+)?",
            response
        )

        if numbers:
            return numbers[-1].replace(",", "")

        return ""

    boxed = re.findall(
        r"\\boxed\{\s*([A-E])\s*\}",
        response,
        re.IGNORECASE
    )

    if boxed:
        return boxed[-1].upper()

    final_match = re.findall(
    r"(?im)^\s*(?:\*\*)?\s*FINAL"
    r"(?:\*\*)?\s*:\s*(?:\*\*)?\s*([A-E])\b",
    response
    )
    if final_match:
        return final_match[-1].upper()

    answer_match = re.findall(
        r"(?:final answer|correct option|answer)\s*(?:is|:)?\s*"
        r"\(?([A-E])\)?\b",
        response,
        re.IGNORECASE
    )

    if answer_match:
        return answer_match[-1].upper()

    return ""


def normalize_answer(value, answer_type):

    value = str(value).strip()

    if answer_type == "numeric":
        try:
            return str(float(value))
        except ValueError:
            return value

    return value.upper()


def run_model(model, item):

    prompt = build_prompt(item)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 6000
        }
    }

    start = time.perf_counter()

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=600
    )

    response.raise_for_status()

    data = response.json()

    elapsed = time.perf_counter() - start

    answer = data.get("response", "").strip()

    prediction = extract_prediction(
        answer,
        item["answer_type"]
    )

    return {
        "answer": answer,
        "prediction": prediction,
        "time_seconds": round(elapsed, 3),
        "prompt_tokens": data.get("prompt_eval_count", 0),
        "generated_tokens": data.get("eval_count", 0),
        "done_reason": data.get("done_reason", "unknown"),
        "complete": (
        data.get("done_reason") == "stop"
        and bool(prediction)
)
    }



def main():

    questions = load_csv(PILOT_FILE)
    answer_rows = load_csv(ANSWER_FILE)

    answer_key = {
        row["question_id"]: row["reference_answer"]
        for row in answer_rows
    }

    # Load existing results so completed work is preserved.
    existing_results = {}

    if OUTPUT_FILE.exists():
        for row in load_csv(OUTPUT_FILE):
            key = (row["model"], row["question_id"])
            existing_results[key] = row

    print("=" * 65)
    print("FOUR-MODEL PILOT EVALUATION")
    print("=" * 65)

    print("Questions:", len(questions))
    print("Models:", len(MODELS))
    print("Expected model calls:", len(questions) * len(MODELS))

    fieldnames = [
        "model",
        "question_id",
        "dataset_name",
        "answer_type",
        "predicted_answer",
        "reference_answer",
        "correct",
        "time_seconds",
        "prompt_tokens",
        "generated_tokens",
        "done_reason",
        "complete",
        "full_response"
    ]

    for model in MODELS:

        print("\n" + "=" * 65)
        print("MODEL:", model)
        print("=" * 65)

        for index, item in enumerate(questions, start=1):

            question_id = item["question_id"]
            key = (model, question_id)

            old_row = existing_results.get(key)

            # Skip only genuinely completed results.
            if old_row and (
                str(old_row.get("complete", "")).lower() == "true"
                and old_row.get("done_reason") == "stop"
                and old_row.get("predicted_answer", "").strip()
            ):
                print(
                    f"SKIPPED: {model} | "
                    f"{question_id} | Already completed"
                )
                continue

            print(
                f"\n{model} | "
                f"Question {index}/{len(questions)}: "
                f"{question_id}"
            )

            try:

                result = run_model(model, item)

                reference = answer_key[question_id]

                predicted = normalize_answer(
                    result["prediction"],
                    item["answer_type"]
                )

                expected = normalize_answer(
                    reference,
                    item["answer_type"]
                )

                correct = (
                    predicted == expected
                    if predicted else False
                )

                row = {
                    "model": model,
                    "question_id": question_id,
                    "dataset_name": item["dataset_name"],
                    "answer_type": item["answer_type"],
                    "predicted_answer": predicted,
                    "reference_answer": reference,
                    "correct": correct,
                    "time_seconds": result["time_seconds"],
                    "prompt_tokens": result["prompt_tokens"],
                    "generated_tokens": result["generated_tokens"],
                    "done_reason": result["done_reason"],
                    "complete": result["complete"],
                    "full_response": result["answer"]
                }

                print("Prediction:", predicted)
                print("Expected:", expected)
                print("Correct:", correct)
                print("Done reason:", result["done_reason"])
                print("Complete:", result["complete"])

            except Exception as error:

                print("ERROR:", error)

                row = {
                    "model": model,
                    "question_id": question_id,
                    "dataset_name": item["dataset_name"],
                    "answer_type": item["answer_type"],
                    "predicted_answer": "",
                    "reference_answer": answer_key[question_id],
                    "correct": False,
                    "time_seconds": "",
                    "prompt_tokens": "",
                    "generated_tokens": "",
                    "done_reason": "error",
                    "complete": False,
                    "full_response": str(error)
                }

            # Insert or replace the result for this model-question pair.
            existing_results[key] = row

            # Save all results after every question.
            with open(
                OUTPUT_FILE,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=fieldnames
                )

                writer.writeheader()
                writer.writerows(existing_results.values())

    print("\n" + "=" * 65)
    print("PILOT EVALUATION COMPLETED")
    print("=" * 65)

    print("Total unique results:", len(existing_results))
    print("Saved to:", OUTPUT_FILE)

if __name__ == "__main__":
    main()
