# Multi-Agent Debate System

## Overview

The **Multi-Agent Debate System** is a mini-project focused on improving the accuracy of Large Language Model (LLM) responses through prompt engineering and multi-agent reasoning strategies.

The project evaluates four different prompting configurations using a locally hosted language model and compares their accuracy, execution time, and number of model calls.

The system explores whether reasoning prompts, agent debate, answer revision, and independent judging can improve the reliability of answers to reasoning-based questions.

---

## Problem Statement

Large Language Models can generate incorrect answers when solving logical, mathematical, and reasoning-based problems. A direct prompting approach may fail to produce accurate answers.

This project investigates whether structured reasoning and multi-agent interaction can improve answer accuracy compared with a direct answer approach.

---

## Objectives

- Evaluate different prompt engineering strategies.
- Compare direct answering with reasoning-based prompting.
- Implement multi-agent debate and answer revision.
- Evaluate a Solver–Critic–Judge architecture.
- Compare accuracy, execution time, and model calls.
- Investigate whether additional agent interactions improve reasoning performance.

---

## Configurations

Four prompting configurations were implemented and evaluated.

| Configuration | Approach | Model Calls |
|---|---|---:|
| A | Direct Answer | 1 |
| B | Reasoning Prompt | 1 |
| C | Two-Agent Debate | 3 |
| D | Solver–Critic–Judge | 4 |

### Configuration A — Direct Answer

The model receives a question and generates an answer directly without an explicit reasoning prompt.

### Configuration B — Reasoning Prompt

The model is instructed to reason through the problem before producing its final answer.

### Configuration C — Two-Agent Debate

A Solver generates an initial answer, a Critic evaluates it, and the Solver revises the answer based on the criticism.

### Configuration D — Solver–Critic–Judge

This configuration introduces an additional Judge stage to evaluate the revised answer and produce the final response.

---

## Technology Stack

- **Programming Language:** Python
- **LLM Runtime:** Ollama
- **Language Model:** Qwen 2.5 3B
- **Backend:** FastAPI
- **Frontend:** HTML, CSS, JavaScript
- **API Communication:** REST API
- **Data Storage:** CSV
- **Experiment Evaluation:** Python

---

## System Architecture

The project consists of the following major components:

- **Experiment Runner:** Executes the different prompting configurations and manages experiments.
- **Ollama Client:** Communicates with the locally hosted LLM.
- **Prompt Modules:** Contains the prompts used for each configuration and agent.
- **Baseline Module:** Implements the single-LLM baseline.
- **Evaluation Module:** Measures accuracy, answer transitions, error correction, model calls, and execution time.
- **Web Interface:** Provides an interface for interacting with the system and viewing experiment comparisons.
- **Results Module:** Stores experiment outputs and evaluation metrics in CSV files.

---

## Datasets

The project uses reasoning-oriented datasets for evaluating model performance:

- GSM8K
- AQuA-RAT
- LogiQA

The experiments use a common set of 28 questions for the final comparison across all four configurations.

---

## Experimental Results

All four configurations were evaluated using the same 28-question benchmark.

| Configuration | Correct | Incorrect | Accuracy | Avg. Runtime (s) | Model Calls |
|---|---:|---:|---:|---:|
| A – Direct Answer | 4 | 24 | 14.29% | 0.2764 | 1 |
| B – Reasoning Prompt | 26 | 2 | **92.86%** | 4.2685 | 1 |
| C – Two-Agent Debate | 25 | 3 | 89.29% | 15.3611 | 3 |
| D – Solver–Critic–Judge | 25 | 3 | 89.29% | 15.0068 | 4 |

### Key Findings

- Direct answering achieved 14.29% accuracy.
- Reasoning prompting achieved the highest accuracy of **92.86%**.
- Two-Agent Debate achieved 89.29% accuracy.
- Solver–Critic–Judge achieved 89.29% accuracy.
- Multi-agent configurations required more model calls and execution time.
- Additional agent interactions did not outperform the single-call reasoning prompt in this experiment.

The results demonstrate that structured reasoning prompts can significantly improve performance compared with direct answering. However, additional multi-agent interactions do not necessarily guarantee higher accuracy.

---

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Laxmikant2007/Multi_Agent_Debate_System.git
```

Navigate into the project directory:

```bash
cd Multi_Agent_Debate_System
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama

Download and install Ollama:

https://ollama.com/

### 5. Download the model

```bash
ollama pull qwen2.5:3b
```

Ensure Ollama is running before executing experiments.

---

## Running the Project

### Run the experiment

Execute the experiment runner from the project root:

```bash
python -m src.experiment_runner
```

The experiment runner is responsible for executing the supported configurations and recording results.

### Run the web backend

Navigate to the web interface directory:

```bash
cd webui
```

Start the FastAPI backend:

```bash
python -m uvicorn backend:app --host 127.0.0.1 --port 8000 --reload
```

### Run the frontend

Open another terminal, navigate to the `webui` directory, and run:

```bash
python -m http.server 5500
```

Open the frontend in your browser:

http://localhost:5500

---

## Evaluation Metrics

The project evaluates performance using the following metrics:

- **Accuracy:** Percentage of questions answered correctly.
- **Average Runtime:** Average execution time per question in seconds.
- **Model Calls:** Number of LLM calls required by each configuration.
- **Error Correction:** Measures incorrect answers corrected during revision.
- **Revision Transition:** Tracks changes from initial predictions to final predictions.

---

## Limitations

- The final comparison uses a relatively small benchmark of 28 questions.
- Experiments use a single local language model.
- Results may vary across runs.
- The multi-agent configurations increase computational time and model calls.
- The experiments do not establish that multi-agent systems outperform reasoning prompts across all tasks or models.

---

## Future Improvements

- Evaluate using larger benchmark datasets.
- Test multiple LLMs of different sizes and architectures.
- Perform repeated experiments and report average performance.
- Improve the debate and critic prompting strategies.
- Evaluate token usage, computational cost, and scalability.
- Explore adaptive debate mechanisms that invoke additional agents only when necessary.

---

## Conclusion

The Multi-Agent Debate System investigates the effectiveness of prompt engineering and multi-agent reasoning for improving LLM answer accuracy.

In the final experiment, the Reasoning Prompt configuration achieved the highest accuracy of 92.86%, outperforming the two multi-agent configurations on the evaluated benchmark. The findings suggest that effective prompting can improve reasoning performance without necessarily requiring additional agents.

The project highlights the importance of experimentally evaluating reasoning strategies rather than assuming that increased model interaction always leads to better results.



