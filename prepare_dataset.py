
import json
import csv
import random
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR / "dataset"
OUTPUT_FILE = DATASET_DIR / "reasoning_questions.csv"

# Experiment settings
SAMPLE_SIZE = 30
RANDOM_SEED = 42

random.seed(RANDOM_SEED)


def load_jsonl(file_path):
    records = []

    with open(file_path, encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    return records


def select_questions(records, dataset_name):
    if len(records) < SAMPLE_SIZE:
        raise ValueError(
            f"{dataset_name} has fewer than {SAMPLE_SIZE} records"
        )

    selected = random.sample(
        list(enumerate(records, start=1)),
        SAMPLE_SIZE
    )

    # Preserve original source order
    selected.sort(key=lambda item: item[0])

    return selected


def main():
    all_questions = []

    # 1. GSM8K
    gsm8k = load_jsonl(
        DATASET_DIR / "gsm8k" / "test.jsonl"
    )

    for source_id, record in select_questions(gsm8k, "GSM8K"):
        answer = record["answer"]

        if "####" not in answer:
            raise ValueError(
                f"GSM8K answer missing #### at record {source_id}"
            )

        reference_answer = answer.split("####", 1)[1].strip()

        all_questions.append({
            "question_id": f"GSM8K_{source_id:04d}",
            "dataset_name": "GSM8K",
            "question": record["question"],
            "context": "",
            "options": "",
            "reference_answer": reference_answer,
            "answer_type": "numeric",
            "source_id": source_id,
            "source_split": "test"
        })

    # 2. AQuA-RAT
    aqua = load_jsonl(
        DATASET_DIR / "aqua_rat" / "test.json"
    )

    for source_id, record in select_questions(aqua, "AQuA-RAT"):
        all_questions.append({
            "question_id": f"AQUA_{source_id:04d}",
            "dataset_name": "AQuA-RAT",
            "question": record["question"],
            "context": "",
            "options": json.dumps(record["options"], ensure_ascii=False),
            "reference_answer": record["correct"].strip().upper(),
            "answer_type": "multiple_choice",
            "source_id": source_id,
            "source_split": "test"
        })

    # 3. LogiQA 2.0
    logiqa = load_jsonl(
        DATASET_DIR / "logiqa" / "test.txt"
    )

    for source_id, record in select_questions(logiqa, "LogiQA"):
        answer_index = int(record["answer"])

        if not 0 <= answer_index < len(record["options"]):
            raise ValueError(
                f"Invalid LogiQA answer at record {source_id}"
            )

        reference_answer = chr(ord("A") + answer_index)

        all_questions.append({
            "question_id": f"LOGIQA_{source_id:04d}",
            "dataset_name": "LogiQA",
            "question": record["question"],
            "context": record["text"],
            "options": json.dumps(record["options"], ensure_ascii=False),
            "reference_answer": reference_answer,
            "answer_type": "multiple_choice",
            "source_id": source_id,
            "source_split": "test"
        })

    # Save unified CSV
    fieldnames = [
        "question_id",
        "dataset_name",
        "question",
        "context",
        "options",
        "reference_answer",
        "answer_type",
        "source_id",
        "source_split"
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_questions)

    print("\nDATASET PREPARATION COMPLETED")
    print("-" * 40)
    print("GSM8K: 30 questions")
    print("AQuA-RAT: 30 questions")
    print("LogiQA: 30 questions")
    print("-" * 40)
    print("Total questions:", len(all_questions))
    print("Random seed:", RANDOM_SEED)
    print("Output file:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
