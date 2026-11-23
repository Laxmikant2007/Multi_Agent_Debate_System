
import argparse
import csv
import json
import re
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATASET_FILE = BASE_DIR / "dataset" / "agent_questions.csv"
ANSWER_FILE = BASE_DIR / "dataset" / "reasoning_questions.csv"

PROMPTS_DIR = BASE_DIR / "prompts"
RESULTS_DIR = BASE_DIR / "results"

RESULTS_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = RESULTS_DIR / "experiment_results_gpu_test.csv"

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_NAME = "qwen2.5:3b"
TEMPERATURE = 0
MAX_TOKENS = 1000
TIMEOUT = 600

PROMPT_FILES = {
    "A": "config_A_direct_answer.txt",
    "B": "config_B_reasoning.txt",
    "C_SOLVER": "config_C_solver.txt",
    "C_CRITIC": "config_C_critic.txt",
    "C_REVISION": "config_C_revision.txt",
    "D_JUDGE": "config_D_judge.txt",
}

CONFIGURATIONS = ["A", "B", "C", "D"]

FIELDNAMES = [
    "configuration",
    "model",
    "question_id",
    "dataset_name",
    "answer_type",
    "initial_prediction",
    "result_status",
    "final_prediction",
    "reference_answer",
    "initial_correct",
    "final_correct",
    "revision_transition",
    "model_calls",
    "time_seconds",
    "prompt_tokens",
    "generated_tokens",
    "done_reasons",
    "complete",
    "error",
    "stage_responses",
]


# ============================================================
# LOAD DATA
# ============================================================

def load_csv(path):

    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def prepare_options(options):

    if not options:
        return ""

    try:
        choices = json.loads(options)
    except (json.JSONDecodeError, TypeError):
        return str(options)

    if not isinstance(choices, list):
        return str(choices)

    return "\n".join(
        f"{chr(65 + i)}. {str(choice).split(')', 1)[-1].strip()}"
        for i, choice in enumerate(choices)
    )


def load_prompts():

    prompts = {}

    for key, filename in PROMPT_FILES.items():

        path = PROMPTS_DIR / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Missing prompt template: {path}"
            )

        prompts[key] = path.read_text(encoding="utf-8-sig")

    print("All six prompt templates loaded successfully.")

    return prompts


# ============================================================
# PROMPT GENERATION
# ============================================================

def common_values(item):

    return {
        "question": item.get("question", ""),
        "context": item.get("context", ""),
        "options": prepare_options(item.get("options", "")),
    }


def render_prompt(template, values):

    try:
        return template.format(**values)

    except KeyError as error:
        raise ValueError(
            f"Missing prompt variable: {error}"
        ) from error


# ============================================================
# OLLAMA MODEL CALL
# ============================================================

def call_model(prompt):

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
            "num_predict": MAX_TOKENS,
        },
    }

    start = time.perf_counter()

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    elapsed = time.perf_counter() - start

    done_reason = data.get("done_reason", "unknown")

    return {
        "response": data.get("response", "").strip(),
        "time_seconds": round(elapsed, 3),
        "prompt_tokens": data.get("prompt_eval_count", 0) or 0,
        "generated_tokens": data.get("eval_count", 0) or 0,
        "done_reason": done_reason,
        "complete": (
            data.get("done", False)
            and done_reason != "length"
            and bool(data.get("response", "").strip())
        ),
    }


# ============================================================
# ANSWER EXTRACTION
# ============================================================


def extract_prediction(response, answer_type):

    if answer_type == "numeric":

        # 1. Extract an explicitly labelled numeric final answer.
        matches = re.findall(
            r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?\s*"
            r"(?:FINAL(?:\s+ANSWER)?|ANSWER)\s*(?:\*\*)?\s*:\s*"
            r"(?:\*\*)?\s*\$?\s*(-?\d[\d,]*(?:\.\d+)?)",
            response,
        )

        if matches:
            return matches[-1].replace(",", "")

        # 2. Extract a boxed numeric answer, e.g. \boxed{5}.
        boxed = re.findall(
            r"\\boxed\s*\{\s*(-?\d[\d,]*(?:\.\d+)?)\s*\}",
            response,
            re.IGNORECASE,
        )

        if boxed:
            return boxed[-1].replace(",", "")

        # 3. Accept a response containing exactly one number.
        numbers = re.findall(
            r"-?\d[\d,]*(?:\.\d+)?",
            response,
        )

        if len(numbers) == 1:
            return numbers[0].replace(",", "")

        # Multiple numbers without a clear final answer: do not guess.
        return ""

    # Multiple-choice answer extraction

    matches = re.findall(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?\s*FINAL\s*"
        r"(?:\*\*)?\s*:\s*(?:\*\*)?\s*\[?\s*([A-E])\s*\]?",
        response,
    )

    if matches:
        return matches[-1].upper()

    # Extract a boxed multiple-choice answer, e.g. \boxed{A}.
    boxed = re.findall(
        r"\\boxed\s*\{\s*([A-E])\s*\}",
        response,
        re.IGNORECASE,
    )

    if boxed:
        return boxed[-1].upper()

    return ""



def extract_field(response, field_name):

    pattern = (
        rf"(?ims)^\s*{re.escape(field_name)}\s*:\s*"
        rf"(.*?)(?=^\s*[A-Za-z][A-Za-z ]*\s*:|\Z)"
    )

    match = re.search(pattern, response)

    if match:
        return match.group(1).strip()

    return ""


def normalize_answer(value, answer_type):

    value = str(value).strip()

    if answer_type == "numeric":

        try:
            number = Decimal(value.replace(",", ""))

            if number == number.to_integral_value():
                return str(int(number))

            return format(number.normalize(), "f")

        except (InvalidOperation, ValueError):
            return value

    return value.upper()


def is_correct(prediction, reference, answer_type):

    predicted = normalize_answer(prediction, answer_type)
    expected = normalize_answer(reference, answer_type)

    return bool(predicted) and predicted == expected


# ============================================================
# RUN ONE MODEL STAGE
# ============================================================
def run_stage(name, template, values, stages):

    prompt = render_prompt(template, values)

    print(f"  Running: {name}")

    try:
        result = call_model(prompt)

    except Exception as exception:
        exception.stages = stages
        raise

    stages[name] = result

    print(
        f"  Completed: {name} | "
        f"{result['time_seconds']} sec | "
        f"{result['generated_tokens']} tokens"
    )

    return result["response"]

# ============================================================
# CONFIGURATION A - DIRECT ANSWER
# ============================================================

def run_A(item, prompts):

    stages = {}

    values = common_values(item)

    response = run_stage(
        "direct_answer",
        prompts["A"],
        values,
        stages,
    )

    prediction = extract_prediction(
        response,
        item["answer_type"],
    )

    return {
        "initial_prediction": "",
        "final_prediction": prediction,
        "stages": stages,
    }


# ============================================================
# CONFIGURATION B - REASONING PROMPT
# ============================================================

def run_B(item, prompts):

    stages = {}

    values = common_values(item)

    response = run_stage(
        "reasoning",
        prompts["B"],
        values,
        stages,
    )

    prediction = extract_prediction(
        response,
        item["answer_type"],
    )

    return {
        "initial_prediction": "",
        "final_prediction": prediction,
        "stages": stages,
    }


# ============================================================
# SHARED SOLVER-CRITIC-REVISION PIPELINE
# Used by both C and D
# ============================================================


def run_debate_pipeline(item, prompts):

    stages = {}

    values = common_values(item)

    # STEP 1: SOLVER

    solver_response = run_stage(
        "solver",
        prompts["C_SOLVER"],
        values,
        stages,
    )

    solver_answer = extract_prediction(
        solver_response,
        item["answer_type"],
    )

    solver_explanation = extract_field(
        solver_response,
        "Explanation",
    )

    # STEP 2: CRITIC

    critic_values = {
        **values,
        "solver_response": solver_response,
    }

    critic_response = run_stage(
        "critic",
        prompts["C_CRITIC"],
        critic_values,
        stages,
    )

    critic_assessment = extract_field(
        critic_response,
        "Assessment",
    )

    critic_issues = extract_field(
        critic_response,
        "Issues identified",
    )

    critic_suggestion = extract_field(
        critic_response,
        "Suggested correction",
    )

    # STEP 3: SOLVER REVISION

    revision_values = {
        **values,
        "solver_response": solver_response,
        "critic_response": critic_response,
    }

    revision_response = run_stage(
        "revision",
        prompts["C_REVISION"],
        revision_values,
        stages,
    )

    revision_answer = extract_prediction(
        revision_response,
        item["answer_type"],
    )

    revision_explanation = extract_field(
        revision_response,
        "Explanation",
    )

    return {
        "initial_prediction": solver_answer,
        "revision_prediction": revision_answer,
        "solver_explanation": solver_explanation,
        "solver_answer": solver_answer,
        "critic_assessment": critic_assessment,
        "critic_issues": critic_issues,
        "critic_suggestion": critic_suggestion,
        "revision_explanation": revision_explanation,
        "solver_response": solver_response,
        "critic_response": critic_response,
        "revision_response": revision_response,
        "stages": stages,
    }


# ============================================================
# CONFIGURATION C - TWO-AGENT DEBATE
# ============================================================

def run_C(item, prompts):

    result = run_debate_pipeline(item, prompts)

    decision = extract_field(
        result["revision_response"],
        "Revision decision",
    ).strip().lower()

    if result["revision_prediction"]:
        result_status = "ANSWERED"

    elif decision == "uncertain":
        result_status = "UNCERTAIN"

    else:
        result_status = "INCOMPLETE"

    return {
        "initial_prediction": result["initial_prediction"],
        "final_prediction": result["revision_prediction"],
        "result_status": result_status,
        "stages": result["stages"],
    }
# ============================================================
# CONFIGURATION D - SOLVER-CRITIC-JUDGE
# ============================================================
def run_D(item, prompts):

    result = run_debate_pipeline(item, prompts)

    judge_values = {
        **common_values(item),
        "solver_response": result["solver_response"],
        "critic_response": result["critic_response"],
        "revision_response": result["revision_response"],
    }

    judge_response = run_stage(
        "judge",
        prompts["D_JUDGE"],
        judge_values,
        result["stages"],
    )

    selection_match = re.search(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:[-*+]\s*)?"
        r"(?:\*\*|__)?\s*(?:Selected answer|Selection)\s*(?:\*\*|__)?\s*:?\s*"
        r"(?:[-*+]\s*)?(?:\*\*|__)?\s*(initial|revised|uncertain)\s*(?:\*\*|__)?\s*$",
        judge_response,
    )

    if not selection_match:
        selection_match = re.search(
            r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*|__)?\s*Final\s*(?:\*\*|__)?\s*:?\s*"
            r"(initial|revised|uncertain)\s*(?:\*\*|__)?\s*$",
            judge_response,
        )

    selected_answer = (
        selection_match.group(1).lower()
        if selection_match
        else ""
    )

    if selected_answer == "initial":
        judge_prediction = result["initial_prediction"]
        result_status = "ANSWERED"

    elif selected_answer == "revised":
        judge_prediction = result["revision_prediction"]
        result_status = "ANSWERED"

    elif selected_answer == "uncertain":
        judge_prediction = ""
        result_status = "UNCERTAIN"

    else:
        judge_prediction = ""
        result_status = "INVALID_SELECTION"

        print(
            f"WARNING: Invalid Judge selection: {selected_answer!r}"
        )

    return {
        "initial_prediction": result["initial_prediction"],
        "final_prediction": judge_prediction,
        "result_status": result_status,
        "stages": result["stages"],
    }

# ============================================================
# RESULT CALCULATIONS
# ============================================================
def build_result(configuration, item, reference, output, error=""):

    stages = output.get("stages", {})

    final_prediction = output.get("final_prediction", "")
    initial_prediction = output.get("initial_prediction", "")

    result_status = output.get(
        "result_status",
        "ANSWERED" if final_prediction else "INCOMPLETE"
    )

    final_correct = is_correct(
        final_prediction,
        reference,
        item["answer_type"],
    )

    if configuration in ("C", "D"):

        initial_correct = is_correct(
            initial_prediction,
            reference,
            item["answer_type"],
        )

        if initial_correct and not final_correct:
            transition = "Correct_to_Incorrect"

        elif not initial_correct and final_correct:
            transition = "Incorrect_to_Correct"

        elif final_correct:
            transition = "Correct_Retained"

        else:
            transition = "Incorrect_Retained"

    else:
        initial_correct = ""
        transition = "Not_Applicable"

    if error:
        result_status = "INCOMPLETE"

    complete = (
        bool(stages)
        and all(s["complete"] for s in stages.values())
        and result_status in ("ANSWERED", "UNCERTAIN")
        and not error
    )

    return {
        "configuration": configuration,
        "model": MODEL_NAME,
        "question_id": item["question_id"],
        "dataset_name": item["dataset_name"],
        "answer_type": item["answer_type"],
        "initial_prediction": initial_prediction,
        "final_prediction": final_prediction,
        "result_status": result_status,
        "reference_answer": reference,
        "initial_correct": initial_correct,
        "final_correct": final_correct,
        "revision_transition": transition,
        "model_calls": len(stages),
        "time_seconds": round(
            sum(s["time_seconds"] for s in stages.values()), 3
        ),
        "prompt_tokens": sum(
            s["prompt_tokens"] for s in stages.values()
        ),
        "generated_tokens": sum(
            s["generated_tokens"] for s in stages.values()
        ),
        "done_reasons": "|".join(
            s["done_reason"] for s in stages.values()
        ),
        "complete": complete,
        "error": error,
        "stage_responses": json.dumps(
            {
                name: stage["response"]
                for name, stage in stages.items()
            },
            ensure_ascii=False,
        ),
    }
# ============================================================
# SAVE AND RESUME
# ============================================================

def load_completed_keys():
    completed = set()

    if not OUTPUT_FILE.exists():
        return completed

    with open(OUTPUT_FILE, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row.get("complete", "").strip().lower() != "true":
                continue

            if row.get("error", "").strip():
                continue

            if row.get("result_status", "").strip() not in (
                "ANSWERED",
                "UNCERTAIN",
            ):
                continue

            key = (
                row["configuration"],
                row["question_id"],
            )

            completed.add(key)

    return completed



def save_result(row):

    file_exists = OUTPUT_FILE.exists()

    with open(
        OUTPUT_FILE,
        "a",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        if not file_exists or OUTPUT_FILE.stat().st_size == 0:
            writer.writeheader()

        writer.writerow(row)


# ============================================================
# MAIN EXPERIMENT
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Run only the first N questions.",
    )

    parser.add_argument(
        "--question-id",
        type=str,
        default=None,
        help="Run a specific question ID.",
    )

    args = parser.parse_args()

    print("=" * 65)
    print("MULTI-AGENT REASONING EXPERIMENT")
    print("=" * 65)

    questions = load_csv(DATASET_FILE)
    answer_rows = load_csv(ANSWER_FILE)

    answer_key = {
        row["question_id"]: row["reference_answer"]
        for row in answer_rows
    }

    if not questions:
        raise ValueError("No questions found in agent dataset.")

    if not answer_key:
        raise ValueError("Reference answer key is empty.")

    for item in questions:

        if item["question_id"] not in answer_key:
            raise ValueError(
                f"Missing reference answer: {item['question_id']}"
            )

    prompts = load_prompts()

    if args.question_id:

        questions = [
            item for item in questions
            if item["question_id"] == args.question_id
        ]

        if not questions:
            raise ValueError(
                f"Question ID not found: {args.question_id}"
            )

    elif args.limit is not None:

        if args.limit < 1:
            raise ValueError("--limit must be at least 1.")

        questions = questions[:args.limit]

    completed = load_completed_keys()

    print("Model:", MODEL_NAME)
    print("Temperature:", TEMPERATURE)
    print("Maximum output tokens per call:", MAX_TOKENS)
    print("Questions selected:", len(questions))
    print("Configurations:", CONFIGURATIONS)
    print("Maximum expected calls:", len(questions) * 9)
    print("Existing completed results:", len(completed))
    print("Output:", OUTPUT_FILE)

    runners = {
        "A": run_A,
        "B": run_B,
        "C": run_C,
        "D": run_D,
    }

    for index, item in enumerate(questions, start=1):

        question_id = item["question_id"]
        reference = answer_key[question_id]

        print("\n" + "=" * 65)
        print(
            f"QUESTION {index}/{len(questions)}: {question_id}"
        )
        print("=" * 65)

        for configuration in CONFIGURATIONS:

            key = (configuration, question_id)

            if key in completed:

                print(
                    f"\nConfiguration {configuration}: "
                    "Already completed. Skipping."
                )
                continue

            print(
                f"\n--- Configuration {configuration} ---"
            )

            start = time.perf_counter()

            error = ""

            try:

                output = runners[configuration](
                    item,
                    prompts,
                )

            except Exception as exception:

                error = str(exception)

                print("ERROR:", error)

                output = {
                    "initial_prediction": "",
                    "final_prediction": "",
                    "result_status": "INCOMPLETE",
                    "stages": getattr(exception, "stages", {}),
                }
            row = build_result(
                configuration,
                item,
                reference,
                output,
                error,
            )

            row["time_seconds"] = round(
                time.perf_counter() - start, 3
            )

            save_result(row)

            completed.add(key)

            print("Initial prediction:", row["initial_prediction"])
            print("Final prediction:", row["final_prediction"])
            print("Expected answer:", reference)
            print("Correct:", row["final_correct"])
            print("Model calls:", row["model_calls"])
            print("Total time:", row["time_seconds"], "seconds")
            print("Prompt tokens:", row["prompt_tokens"])
            print("Generated tokens:", row["generated_tokens"])

    print("\n" + "=" * 65)
    print("EXPERIMENT RUN COMPLETED")
    print("=" * 65)

    print("Results saved to:", OUTPUT_FILE)
    print("Completed configuration-question pairs:", len(completed))

    print(
        "\nNote: Dollar API cost is not calculated because "
        "this experiment uses a local Ollama model."
    )


if __name__ == "__main__":
    main()
