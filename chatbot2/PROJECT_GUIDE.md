# Chatbot Evaluation Project Guide

This project runs a local chatbot against questions stored in an Excel file, evaluates each answer with Azure OpenAI, calculates summary scores, and writes a final Excel report.

The main workflow is:

```text
data/input.xlsx
    -> run_pipeline.py
    -> chatbot_engine.py
    -> real_metrics.py
    -> evaluation_engine.py
    -> results/output.xlsx
```

## 1. Project Purpose

The project is designed to measure chatbot answer quality in a repeatable way.

For each row in the input Excel file, the system:

1. Reads a question, expected answer, and mode.
2. Sends the question to a local Ollama LLM.
3. Collects the chatbot answer.
4. Sends the question, expected answer, actual answer, and retrieved context to Azure OpenAI for evaluation.
5. Receives metric scores as JSON.
6. Calculates an overall weighted score.
7. Adds remarks and improvement suggestions.
8. Saves everything into `results/output.xlsx`.

## 2. Current Project Structure

```text
chatbot2/
  data/
    input.xlsx              # Input questions, expected outputs, and mode values.

  results/
    output.xlsx             # Generated evaluation report.

  faiss_index/
    index.faiss             # Existing vector index artifact.
    index.pkl               # Existing metadata/index artifact.

  chatbot_engine.py         # Calls the local Ollama chatbot model.
  evaluation_engine.py      # Calculates overall score, remarks, and suggestions.
  main.py                   # Minimal placeholder entry file.
  real_metrics.py           # Uses Azure OpenAI to score chatbot answers.
  run_pipeline.py           # Main end-to-end evaluation pipeline.

  pyproject.toml            # UV/Python project metadata and dependencies.
  uv.lock                   # Locked dependency versions for reproducible installs.
  requirements.txt          # Older pip-style dependency list.
  README.md                 # Short existing run note.
  run.bat                   # Older Streamlit launcher; does not match current files.
  .python-version           # Python version marker: 3.12.
  .env                      # Local secrets/configuration file. Do not commit/share.
```

## 3. Important Files

### `run_pipeline.py`

This is the main file for the current project workflow.

It performs the complete batch evaluation:

- Loads `data/input.xlsx`.
- Verifies required columns exist.
- Loops through every question.
- Calls `ask_question()` from `chatbot_engine.py`.
- Calls `evaluate_all_metrics()` from `real_metrics.py`.
- Calls helper functions from `evaluation_engine.py`.
- Writes the final report to `results/output.xlsx`.

Run this file when you want the complete evaluation output.

### `chatbot_engine.py`

This file contains the local chatbot call.

Current behavior:

- Uses `ChatOllama`.
- Calls the model `llama3.2:latest`.
- Uses `temperature=0.3`.
- Returns a dictionary with:
  - `answer`
  - `contexts`

At present, `contexts` is returned as an empty list. That means this version does not actively retrieve document chunks during the current pipeline, even though `faiss_index/` exists in the project.

### `real_metrics.py`

This file evaluates answer quality using Azure OpenAI.

It:

- Loads Azure settings from `.env`.
- Creates an `AzureOpenAI` client.
- Builds a strict evaluation prompt.
- Requests JSON-only metric output.
- Parses the JSON response.
- Returns normalized metric values.

The expected metrics are:

- `Answer Relevancy`
- `Correctness`
- `Hallucination`
- `Faithfulness`
- `Context Precision`

If Azure evaluation fails, it returns conservative fallback scores:

```json
{
  "Answer Relevancy": 0,
  "Correctness": 0,
  "Hallucination": 1,
  "Faithfulness": 0,
  "Context Precision": 0
}
```

### `evaluation_engine.py`

This file converts raw metrics into human-readable evaluation output.

It contains:

- `calculate_overall_score(metrics)`
- `generate_remarks(score)`
- `generate_improvements(metrics)`

The overall score uses these weights:

| Metric | Weight |
|---|---:|
| Answer Relevancy | 0.20 |
| Correctness | 0.25 |
| Faithfulness | 0.25 |
| Context Precision | 0.15 |
| Hallucination | -0.15 |

Hallucination has a negative weight because a higher hallucination score means worse answer quality.

### `main.py`

This is only a minimal placeholder entry point. It prints a simple message and is not the main evaluation workflow.

### `run.bat`

This appears to be from an older Streamlit version of the project. It references:

- `ragenv`
- `app.py`

Those do not match the current visible project workflow. For the current pipeline, use:

```bash
uv run python run_pipeline.py
```

## 4. Prerequisites

Before running the project, install these external tools:

### Python

The project is configured for Python 3.12.

Check your Python version:

```bash
python --version
```

### UV

UV is used for environment and dependency management.

Check whether UV is installed:

```bash
uv --version
```

If UV is not installed, install it from the official UV installation instructions:

```bash
pip install uv
```

### Ollama

The local chatbot uses Ollama through `langchain_ollama`.

Check whether Ollama is installed:

```bash
ollama --version
```

The current model name in code is:

```text
llama3.2:latest
```

Make sure it is available locally:

```bash
ollama pull llama3.2:latest
```

Ollama must be running before the pipeline asks questions.

### Azure OpenAI

The evaluator uses Azure OpenAI, so you need:

- Azure OpenAI API key
- Azure OpenAI endpoint
- Azure OpenAI API version
- Azure OpenAI deployment name

These values are read from `.env`.

## 5. Environment Setup Using UV

From the project root:

```bash
cd "C:\VS Code\Python Projects\Chatbot projects\chatbot2"
```

Create or sync the virtual environment from the locked dependency file:

```bash
uv sync
```

This reads:

- `pyproject.toml`
- `uv.lock`

and creates/updates the project virtual environment.

To run commands inside the UV environment, use:

```bash
uv run <command>
```

For example:

```bash
uv run python run_pipeline.py
```

## 6. `.env` Setup

Create a `.env` file in the project root if it does not already exist.

Required variables:

```env
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=your_api_version
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
```

The code will stop early with a clear error if any of these values are missing.

Do not share or commit `.env`, because it contains secrets.

## 7. Input Excel Format

The pipeline expects this file:

```text
data/input.xlsx
```

It must contain these columns:

| Column | Purpose |
|---|---|
| `Question` | The question that will be sent to the chatbot. |
| `Expected Output` | The reference answer used to judge correctness. |
| `Mode` | A mode value passed into the chatbot function. |

If any required column is missing, the pipeline raises an exception like:

```text
Missing column: Question
```

Current note: `Mode` is passed into `ask_question(question, mode)`, but the current implementation of `chatbot_engine.py` does not use it internally yet.

## 8. End-to-End Workflow

### Step 1: Prepare dependencies

```bash
uv sync
```

### Step 2: Make sure Ollama has the model

```bash
ollama pull llama3.2:latest
```

### Step 3: Prepare Azure OpenAI settings

Ensure `.env` contains:

```env
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_VERSION=...
AZURE_OPENAI_DEPLOYMENT=...
```

### Step 4: Prepare input data

Open `data/input.xlsx` and make sure every row has:

- `Question`
- `Expected Output`
- `Mode`

### Step 5: Run the pipeline

```bash
uv run python run_pipeline.py
```

### Step 6: Review output

Open:

```text
results/output.xlsx
```

The output report includes:

- Question
- Expected Output
- Actual Output
- Retrieved Context
- Answer Relevancy
- Correctness
- Hallucination
- Faithfulness
- Context Precision
- Overall Score
- Remarks
- Improvements Needed

## 9. Runtime Data Flow

```text
Excel row
  |
  |-- Question
  |-- Expected Output
  |-- Mode
  v
run_pipeline.py
  |
  v
chatbot_engine.ask_question(question, mode)
  |
  |-- Sends question to Ollama model
  |-- Receives answer
  |-- Returns answer and contexts
  v
real_metrics.evaluate_all_metrics(...)
  |
  |-- Builds evaluator prompt
  |-- Sends prompt to Azure OpenAI
  |-- Expects valid JSON
  |-- Parses metric scores
  v
evaluation_engine.py
  |
  |-- Calculates weighted score
  |-- Generates remarks
  |-- Generates improvement suggestions
  v
results/output.xlsx
```

## 10. Metric Meaning

### Answer Relevancy

Measures whether the chatbot answer directly responds to the question.

High score means the answer is on-topic.

### Correctness

Measures whether the actual answer matches the expected answer.

High score means the answer is factually aligned with the reference output.

### Hallucination

Measures unsupported or invented information.

High score is bad for this metric.

### Faithfulness

Measures whether the answer is grounded in the provided context.

High score means the answer is supported by context.

### Context Precision

Measures the quality of retrieved context.

High score means the context is relevant and useful.

Current note: because `chatbot_engine.py` currently returns an empty context list, this metric may be limited unless retrieval is added back into the chatbot flow.

## 11. Output Interpretation

The overall score is rounded to two decimal places and cannot go below zero.

Remarks are based on this scale:

| Score Range | Remark |
|---:|---|
| `>= 0.85` | Excellent response quality |
| `>= 0.70` | Good but minor issues exist |
| `>= 0.50` | Needs improvement |
| `< 0.50` | Poor performance |

Improvement suggestions are generated when:

| Condition | Suggestion |
|---|---|
| `Hallucination > 0.3` | Reduce hallucination |
| `Faithfulness < 0.7` | Improve grounding in context |
| `Context Precision < 0.7` | Improve retrieval quality |
| No issues found | System is performing well |

## 12. Common Commands

Install/sync dependencies:

```bash
uv sync
```

Run the full pipeline:

```bash
uv run python run_pipeline.py
```

Run the placeholder main file:

```bash
uv run python main.py
```

Check Python syntax without writing cache files:

```bash
uv run python -B -m py_compile chatbot_engine.py evaluation_engine.py main.py real_metrics.py run_pipeline.py
```

## 13. Troubleshooting

### Missing Azure environment variable

Example:

```text
Missing AZURE_OPENAI_API_KEY in .env
```

Fix:

Add the missing key to `.env`.

### Ollama model not found

If the chatbot call fails because `llama3.2:latest` is unavailable, run:

```bash
ollama pull llama3.2:latest
```

### Input Excel column missing

Example:

```text
Missing column: Expected Output
```

Fix:

Update `data/input.xlsx` so it contains all required columns:

- `Question`
- `Expected Output`
- `Mode`

### Output file does not appear

Check:

- Did `uv run python run_pipeline.py` finish successfully?
- Does the `results/` folder exist?
- Is `results/output.xlsx` open in Excel? If it is open, Python may not be able to overwrite it.

### Azure returns invalid JSON

The evaluator prompt asks for JSON only, but LLMs can still occasionally return malformed text.

The current code catches this and writes fallback scores. If this happens often, improve the evaluator prompt or use a stricter structured-output API pattern.

## 14. Known Current Limitations

- The chatbot currently does not use the `mode` value internally.
- The chatbot currently returns no retrieved contexts.
- `faiss_index/` exists, but the current visible pipeline does not load or query it.
- `run.bat` references `app.py`, but `app.py` is not present in the current visible project.
- `requirements.txt` exists, but `pyproject.toml` and `uv.lock` are the better source for UV-based setup.
- `main.py` is only a placeholder and does not run the evaluation pipeline.

## 15. How A New Coder Should Approach The Project

Start with `run_pipeline.py` to understand the full workflow.

Then read:

1. `chatbot_engine.py` to understand how answers are generated.
2. `real_metrics.py` to understand how answers are evaluated.
3. `evaluation_engine.py` to understand how scores become report fields.

The most important extension points are:

- Add document retrieval in `chatbot_engine.py`.
- Use `mode` to change chatbot behavior.
- Connect `faiss_index/` to the answer-generation flow.
- Improve Azure evaluation reliability with structured outputs.
- Add automated tests for scoring and Excel processing.

## 16. Quick Start Summary

```bash
cd "C:\VS Code\Python Projects\Chatbot projects\chatbot2"
uv sync
ollama pull llama3.2:latest
uv run python run_pipeline.py
```

Then open:

```text
results/output.xlsx
```

That is the complete current project flow.
