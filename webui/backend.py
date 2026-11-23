import sys
import time
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Import existing experiment engine
from experiment_runner import (  # noqa: E402
    load_prompts,
    run_A,
    run_B,
    run_C,
    run_D,
)

# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Multi-Agent Debate API",
    description="API for running multi-agent reasoning experiments",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Load existing prompt templates
PROMPTS = load_prompts()

# Configuration mapping
CONFIG_RUNNERS = {
    "A": run_A,
    "B": run_B,
    "C": run_C,
    "D": run_D,
}

CONFIG_NAMES = {
    "A": "Direct Answer",
    "B": "Reasoning Prompt",
    "C": "Two-Agent Debate",
    "D": "Solver-Critic-Judge",
}


# =========================================================
# REQUEST SCHEMA
# =========================================================

class ExperimentRequest(BaseModel):
    question: str
    configuration: str


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Multi-Agent Debate API",
        "model": "qwen2.5:3b",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "qwen2.5:3b",
    }


# =========================================================
# RUN EXPERIMENT
# =========================================================

@app.post("/run")
def run_experiment(request: ExperimentRequest):

    question = request.question.strip()
    configuration = request.configuration.upper().strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    if configuration not in CONFIG_RUNNERS:
        raise HTTPException(
            status_code=400,
            detail="Configuration must be A, B, C, or D.",
        )

    # Construct a custom question compatible with the existing engine.
    item = {
        "question_id": "WEBUI_CUSTOM",
        "dataset_name": "Custom",
        "question": question,
        "context": "",
        "options": "",
        "answer_type": "multiple_choice",
    }

    runner = CONFIG_RUNNERS[configuration]

    start_time = time.perf_counter()

    try:
        result = runner(item, PROMPTS)

    except Exception as exc:
        stage_data = getattr(exc, "stages", {})

        raise HTTPException(
            status_code=500,
            detail={
                "error": str(exc),
                "completed_stages": stage_data,
            },
        )

    total_time = round(time.perf_counter() - start_time, 3)

    stages = result.get("stages", {})

           # Get the final raw model response.
    if configuration in ("A", "B"):
        final_stage = next(iter(stages.values()), {})
    elif configuration == "C":
        final_stage = stages.get("revision", {})
    else:
        final_stage = stages.get("judge", {})

    raw_final_response = final_stage.get("response", "")
    final_answer = result.get("final_prediction", "")

    # Extract a concise final answer.
    if not final_answer:
        match = re.search(
            r"(?im)^\s*(?:\*\*)?\s*(?:FINAL ANSWER|FINAL)\s*:?\s*(?:\*\*)?\s*(.+)$",
            raw_final_response,
        )

        if match:
            final_answer = match.group(1).strip()
        else:
            # Check for a final answer label on a separate line.
            match = re.search(
                r"(?im)^\s*(?:\*\*)?\s*(?:FINAL ANSWER|FINAL)\s*:?\s*(?:\*\*)?\s*$"
                r"\s*\n\s*([^\n]+)",
                raw_final_response,
            )

            if match:
                final_answer = match.group(1).strip()
            else:
                final_answer = raw_final_response

    # Calculate actual number of model calls and timing.
    model_calls = len(stages)

    total_stage_time = round(
        sum(
            stage.get("time_seconds", 0)
            for stage in stages.values()
        ),
        3,
    )

    # Prepare stage information for the frontend.
    formatted_stages = {}

    for stage_name, stage_result in stages.items():
        formatted_stages[stage_name] = {
            "response": stage_result.get("response", ""),
            "time_seconds": stage_result.get("time_seconds", 0),
            "prompt_tokens": stage_result.get("prompt_tokens", 0),
            "generated_tokens": stage_result.get("generated_tokens", 0),
            "complete": stage_result.get("complete", False),
            "done_reason": stage_result.get("done_reason", ""),
        }

    return {
        "success": True,
        "question": question,
        "configuration": configuration,
        "configuration_name": CONFIG_NAMES[configuration],
        "model": "qwen2.5:3b",
        "final_answer": final_answer,
        "extracted_prediction": result.get("final_prediction", ""),
        "initial_prediction": result.get("initial_prediction", ""),
        "result_status": result.get("result_status", "ANSWERED"),
        "model_calls": model_calls,
        "execution_time": total_time,
        "stage_execution_time": total_stage_time,
        "stages": formatted_stages,
    }

# =========================================================
# FINAL EXPERIMENT RESULTS API
# =========================================================

import csv
from pathlib import Path

FINAL_RESULTS_CSV = (
    Path(__file__).resolve().parent.parent
    / "results"
    / "final_28_common_questions_comparison.csv"
)


def load_final_results():
    if not FINAL_RESULTS_CSV.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Final results CSV not found: {FINAL_RESULTS_CSV}",
        )

    with open(FINAL_RESULTS_CSV, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def to_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes")


def to_float(value):
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0


def to_int(value):
    try:
        return int(float(value or 0))
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

@app.get("/results/summary")
def get_results_summary():

    rows = load_final_results()

    configurations = ["A", "B", "C", "D"]
    summary = {}

    for config in configurations:

        config_rows = [
            row for row in rows
            if row.get("configuration", "").upper() == config
        ]

        total = len(config_rows)

        initial_correct = sum(
            to_bool(row.get("initial_correct"))
            for row in config_rows
        )

        final_correct = sum(
            to_bool(row.get("final_correct"))
            for row in config_rows
        )

        total_time = sum(
            to_float(row.get("time_seconds"))
            for row in config_rows
        )

        total_calls = sum(
            to_int(row.get("model_calls"))
            for row in config_rows
        )

        summary[config] = {
            "configuration": config,
            "name": CONFIG_NAMES.get(config, config),
            "total_questions": total,
            "initial_correct": initial_correct,
            "final_correct": final_correct,
            "initial_accuracy": round(
                initial_correct / total * 100, 2
            ) if total else 0,
            "final_accuracy": round(
                final_correct / total * 100, 2
            ) if total else 0,
            "average_time": round(
                total_time / total, 3
            ) if total else 0,
            "total_time": round(total_time, 3),
            "average_model_calls": round(
                total_calls / total, 2
            ) if total else 0,
        }

    return {
        "success": True,
        "total_records": len(rows),
        "total_questions": len(set(
            row.get("question_id", "") for row in rows
        )),
        "configurations": summary,
    }


# ---------------------------------------------------------
# FULL DATASET
# ---------------------------------------------------------

@app.get("/results/data")
def get_results_data():

    rows = load_final_results()

    # Return useful fields only; keep large stage_responses out.
    clean_rows = []

    for row in rows:
        clean_rows.append({
            "configuration": row.get("configuration"),
            "model": row.get("model"),
            "question_id": row.get("question_id"),
            "dataset_name": row.get("dataset_name"),
            "answer_type": row.get("answer_type"),
            "initial_prediction": row.get("initial_prediction"),
            "final_prediction": row.get("final_prediction"),
            "reference_answer": row.get("reference_answer"),
            "initial_correct": to_bool(row.get("initial_correct")),
            "final_correct": to_bool(row.get("final_correct")),
            "revision_transition": row.get("revision_transition"),
            "model_calls": to_int(row.get("model_calls")),
            "time_seconds": to_float(row.get("time_seconds")),
            "prompt_tokens": to_int(row.get("prompt_tokens")),
            "generated_tokens": to_int(row.get("generated_tokens")),
            "complete": to_bool(row.get("complete")),
            "error": row.get("error"),
        })

    return {
        "success": True,
        "total_records": len(clean_rows),
        "data": clean_rows,
    }