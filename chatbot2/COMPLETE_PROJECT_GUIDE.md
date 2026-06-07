# 🧠 Chatbot Evaluation Pipeline — Complete Project Guide

A complete, production-ready pipeline that:

1. Reads questions from an **Excel file**
2. Sends them to a **local Ollama LLM** (`llama3.2:latest`)
3. Evaluates each answer using **Azure OpenAI** against 5 quality metrics
4. Calculates a **weighted overall score**
5. Generates **human-readable remarks** and **improvement suggestions**
6. Writes everything into a **results Excel file**

---

## 📁 Project Structure

```
chatbot2/
│
├── 📂 data/
│   └── input.xlsx                    # Input file: questions + expected answers + modes
│
├── 📂 results/
│   └── output.xlsx                   # Generated evaluation report
│
├── 📂 faiss_index/
│   ├── index.faiss                   # FAISS vector index (unused currently)
│   └── index.pkl                     # FAISS metadata (unused currently)
│
├── 🐍 chatbot_engine.py              # Calls local Ollama model to generate answers
├── 🐍 evaluation_engine.py           # Calculates scores, remarks, and suggestions
├── 🐍 real_metrics.py                # Uses Azure OpenAI to score answers
├── 🐍 run_pipeline.py                # Main orchestrator — runs the full pipeline
├── 🐍 main.py                        # Placeholder entry point (not the real workflow)
│
├── 📄 pyproject.toml                 # UV project metadata + 30 dependencies
├── 📄 uv.lock                        # Locked dependency versions
├── 📄 requirements.txt               # Legacy pip-style deps (redundant)
├── 📄 .python-version                # Python 3.12
├── 📄 .env                           # Azure OpenAI secrets (DO NOT COMMIT)
├── 📄 run.bat                        # Stale Streamlit launcher (doesn't work currently)
├── 📄 README.md                      # Short run command
└── 📄 PROJECT_GUIDE.md               # Original project documentation
```

> **Note:** The project started as a Streamlit PDF chat app (`run.bat` + `app.py`), but has been refactored into a batch evaluation pipeline. Some legacy artifacts (`faiss_index/`, `run.bat`) remain but are not used by the current workflow.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         data/input.xlsx                                 │
│  ┌───────────┬──────────────────────┬────────┐                         │
│  │ Question  │   Expected Output     │  Mode  │                         │
│  ├───────────┼──────────────────────┼────────┤                         │
│  │ What is…  │   The answer is…     │ general│                         │
│  └───────────┴──────────────────────┴────────┘                         │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         run_pipeline.py                                 │
│                                                                         │
│  For each row (with tqdm progress bar):                                │
│    1. Extract Question, Expected Output, Mode                           │
│    2. Call chatbot_engine.ask_question()                                │
│    3. Call real_metrics.evaluate_all_metrics()                         │
│    4. Call evaluation_engine helpers                                    │
│    5. Collect row data                                                  │
│                                                                         │
│  Finally: Save all rows to results/output.xlsx                          │
└─────────────────────────────────────────────────────────────────────────┘
          │                    │                       │
          ▼                    ▼                       ▼
┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│ chatbot_engine   │  │  real_metrics    │  │  evaluation_engine   │
│                  │  │                  │  │                      │
│  Ollama LLM      │  │  Azure OpenAI    │  │  calculate_overall   │
│  llama3.2:latest │  │  GPT-4o-mini     │  │  generate_remarks    │
│  temperature=0.3 │  │  temperature=0   │  │  generate_improvements│
│  returns:        │  │  returns:        │  │                      │
│   • answer       │  │   • 5 metrics    │  │  transforms metrics  │
│   • contexts=[]  │  │   • JSON format  │  │  → report fields     │
└─────────────────┘  └──────────────────┘  └──────────────────────┘
          │                    │                       │
          └────────────────────┼───────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         results/output.xlsx                             │
│                                                                         │
│  ┌──────────┬──────────┬────────┬───────────┬──────┬──────┬──────┐    │
│  │ Question │ Expected │ Actual │ Retrieved │ Ans. │ Corr.│ Hal. │    │
│  │          │ Output   │ Output │ Context   │ Rel. │      │      │    │
│  ├──────────┼──────────┼────────┼───────────┼──────┼──────┼──────┤    │
│  │ ...      │ ...      │ ...    │ ...       │ ...  │ ...  │ ...  │    │
│  └──────────┴──────────┴────────┴───────────┴──────┴──────┴──────┘    │
│                                                                         │
│  Additional columns: Faithfulness, Context Precision, Overall Score,    │
│                      Remarks, Improvements Needed                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Prerequisites

### 1. Python 3.12
```bash
python --version
# Expected: Python 3.12.x
```

### 2. UV (Dependency Manager)
```bash
uv --version
# If not installed:
pip install uv
```

### 3. Ollama (Local LLM)
```bash
ollama --version
# If not installed: download from https://ollama.com

# Pull the required model
ollama pull llama3.2:latest

# Make sure Ollama is RUNNING before executing the pipeline
# (Ollama runs as a background service on your machine)
```

### 4. Azure OpenAI Resource
You need access to an Azure OpenAI resource with a deployed model. The project uses:
- Model: `gpt-4o-mini` (or any chat model)
- API version: `2024-12-01-preview`

---

## 🔐 Environment Setup (.env)

Create a `.env` file in the project root with these exact variable names:

```env
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

The code performs a **safety check** on startup. If any variable is missing, the pipeline stops immediately with a clear error:

```
Missing AZURE_OPENAI_API_KEY in .env
```

> ⚠️ **Never commit or share your `.env` file** — it contains API secrets.

---

## 📊 Input File Format

The pipeline reads from `data/input.xlsx`. This file **must** contain three columns:

| Column Name       | Purpose                                              | Example                          |
|-------------------|------------------------------------------------------|----------------------------------|
| `Question`        | The question sent to the chatbot                     | "What is the capital of France?" |
| `Expected Output` | The reference answer used to judge correctness       | "Paris"                          |
| `Mode`            | A mode value passed into the chatbot function        | "general"                        |

If any column is missing, the pipeline raises:
```
Missing column: Question
```

---

## 🐍 Module-by-Module Deep Dive

### 1. `chatbot_engine.py` (13 lines) — Answer Generator

```python
from langchain_ollama import ChatOllama

def ask_question(question, mode="general"):
    llm = ChatOllama(model="llama3.2:latest", temperature=0.3)
    response = llm.invoke(question)
    return {"answer": response.content, "contexts": []}
```

**What it does:**
- Creates an Ollama client pointed at the locally running `llama3.2:latest` model
- Uses `temperature=0.3` for mild creativity in responses
- Returns a dictionary with the generated answer and an **empty contexts list** (no document retrieval)

**Key observation:** The `mode` parameter is accepted but **never used** internally. This is a known limitation.

---

### 2. `real_metrics.py` (184 lines) — Azure-backed Evaluator

```python
from openai import AzureOpenAI

# Reads 4 values from .env
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or ""
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT") or ""
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION") or ""
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT") or ""

client = AzureOpenAI(
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
)

def _call_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[{"role": "system", "content": "You are a strict AI evaluator. Always return valid JSON only."},
                  {"role": "user", "content": prompt}],
        temperature=0,
    )
    ...

def evaluate_all_metrics(question, answer, contexts, expected):
    # Builds a prompt with question, expected answer, actual answer, and context
    # Asks Azure to return JSON with 5 metrics
    # Falls back to worst-case scores if anything fails
    ...
```

**What it does:**
- Loads Azure OpenAI configuration from `.env` with validation
- Builds a strict evaluation prompt that demands **valid JSON only**
- Uses `temperature=0` for **deterministic, reproducible** scoring
- Returns 5 normalized metric values (0.0 to 1.0)

**The evaluation prompt sent to Azure:**
```
Evaluate the chatbot response.

Return ONLY valid JSON.

FORMAT:
{
    "Answer Relevancy": 0.0,
    "Correctness": 0.0,
    "Hallucination": 0.0,
    "Faithfulness": 0.0,
    "Context Precision": 0.0
}

SCORING RULES:
- All scores must be between 0 and 1
- Higher is better except Hallucination
...

DATA:
Question: ...
Expected Answer: ...
Actual Answer: ...
Retrieved Context: ...
```

**Fallback scores on failure:**
```json
{
  "Answer Relevancy": 0,
  "Correctness": 0,
  "Hallucination": 1,
  "Faithfulness": 0,
  "Context Precision": 0
}
```

---

### 3. `evaluation_engine.py` (46 lines) — Score Processing

Contains three helper functions:

#### `calculate_overall_score(metrics)`
Computes a weighted sum of all 5 metrics:

| Metric              | Weight  | Why                                     |
|---------------------|---------|-----------------------------------------|
| Answer Relevancy    | +0.20   | Rewards on-topic answers                |
| Correctness         | +0.25   | Strong importance for matching expected |
| Faithfulness        | +0.25   | Strong importance for context grounding |
| Context Precision   | +0.15   | Rewards useful retrieval                |
| Hallucination       | **-0.15** | Penalty for unsupported information   |

The score is clamped to minimum 0.0 and rounded to 2 decimal places.

#### `generate_remarks(score)`
Converts the numeric score into a qualitative label:

| Score Range   | Remark                       |
|:-------------:|:-----------------------------|
| ≥ 0.85        | Excellent response quality   |
| ≥ 0.70        | Good but minor issues exist  |
| ≥ 0.50        | Needs improvement            |
| < 0.50        | Poor performance             |

#### `generate_improvements(metrics)`
Creates targeted suggestions based on weak metrics:

| Condition                     | Suggestion                   |
|:------------------------------|:-----------------------------|
| Hallucination > 0.3           | Reduce hallucination         |
| Faithfulness < 0.7            | Improve grounding in context |
| Context Precision < 0.7       | Improve retrieval quality    |
| No issues found               | System is performing well    |

---

### 4. `run_pipeline.py` (145 lines) — The Orchestrator

This is the **main entry point** that wires everything together.

**Flow:**
1. Load `.env` variables
2. Read `data/input.xlsx` with `pandas`
3. Validate required columns: `Question`, `Expected Output`, `Mode`
4. For each row (with `tqdm` progress bar):
   - Call `chatbot_engine.ask_question(question, mode)` → get answer
   - Call `real_metrics.evaluate_all_metrics(question, answer, contexts, expected)` → get metric scores
   - Call `evaluation_engine.calculate_overall_score(metrics)` → get weighted score
   - Call `evaluation_engine.generate_remarks(score)` → get remark
   - Call `evaluation_engine.generate_improvements(metrics)` → get suggestions
   - Assemble row data dictionary
5. Save all rows to `results/output.xlsx`

**Output columns:**
| Column               | Source                                 |
|----------------------|----------------------------------------|
| Question             | From input                             |
| Expected Output      | From input                             |
| Actual Output        | From chatbot_engine                    |
| Retrieved Context    | From chatbot_engine                    |
| Answer Relevancy     | From real_metrics                      |
| Correctness          | From real_metrics                      |
| Hallucination        | From real_metrics                      |
| Faithfulness         | From real_metrics                      |
| Context Precision    | From real_metrics                      |
| Overall Score        | From evaluation_engine                 |
| Remarks              | From evaluation_engine                 |
| Improvements Needed  | From evaluation_engine                 |

---

### 5. `main.py` (6 lines) — Placeholder

```python
def main():
    print("Hello from chat-with-multiple-pdf-documents!")

if __name__ == "__main__":
    main()
```

This file is **not the real workflow**. It exists from an earlier project template and is not used.

---

## ⚙️ Complete Setup & Run Instructions

### Step 1: Install Python 3.12
```bash
python --version
# Ensure you see Python 3.12.x
```

### Step 2: Install UV
```bash
pip install uv
uv --version
```

### Step 3: Sync Project Dependencies
```bash
uv sync
```
This reads `pyproject.toml` + `uv.lock` and installs all 30+ dependencies into a virtual environment.

### Step 4: Install & Start Ollama
```bash
# Download from https://ollama.com if not installed

# Pull the required model
ollama pull llama3.2:latest

# Verify Ollama is running (it runs as a background service)
ollama list
```

### Step 5: Configure Azure OpenAI (.env)
Create a `.env` file in the project root:
```env
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### Step 6: Prepare Input Data
Create/update `data/input.xlsx` with these columns:

| Question                    | Expected Output                          | Mode    |
|-----------------------------|------------------------------------------|---------|
| What is the capital of France? | The capital of France is Paris.       | general |
| Explain quantum computing   | Quantum computing uses qubits...        | expert  |
| ...                         | ...                                      | ...     |

### Step 7: Run the Pipeline
```bash
uv run python run_pipeline.py
```

**What you'll see:**
```
-> Processing Question 1: What is the capital of France?
Evaluation Error: ...
OK Completed Question 1

-> Processing Question 2: Explain quantum computing
OK Completed Question 2
...

Evaluation Pipeline Completed Successfully!
```

### Step 8: View Results
Open `results/output.xlsx` in Excel.

---

## 📈 Metric Interpretation Guide

| Metric              | What It Measures                          | High Score Means                       |
|---------------------|-------------------------------------------|----------------------------------------|
| Answer Relevancy    | Is the answer on-topic?                   | Answer directly addresses the question |
| Correctness         | Does the answer match the expected output?| Factually aligned with reference       |
| Faithfulness        | Is the answer grounded in context?        | Answer is supported by retrieved docs  |
| Context Precision   | Is the retrieved context useful?          | Context is focused and relevant        |
| Hallucination       | Does the answer contain unsupported info? | **Low is good** — keep below 0.3       |

### Remarks Scale
| Score        | Label                           | Action                             |
|:------------:|:--------------------------------|:-----------------------------------|
| ≥ 0.85       | Excellent response quality      | No changes needed                  |
| ≥ 0.70       | Good but minor issues exist     | Review weak metrics                |
| ≥ 0.50       | Needs improvement               | Investigate and retrain            |
| < 0.50       | Poor performance                | Major overhaul required            |

### Improvement Suggestions
| Triggered When                     | Suggestion                    |
|:-----------------------------------|:------------------------------|
| Hallucination > 0.3                | Reduce hallucination          |
| Faithfulness < 0.7                 | Improve grounding in context  |
| Context Precision < 0.7            | Improve retrieval quality     |
| None of the above                  | System is performing well     |

---

## 🚫 Known Limitations

| # | Limitation | Impact | Potential Fix |
|---|------------|--------|---------------|
| 1 | `mode` parameter is accepted but **never used** in `chatbot_engine.py` | Mode has no effect on chatbot behavior | Implement mode-based routing or prompt customization |
| 2 | Contexts always returned as **empty list** | Faithfulness & Context Precision metrics are meaningless without context | Connect `faiss_index/` to the chatbot flow for RAG |
| 3 | `faiss_index/` directory exists but is **never loaded or queried** | No document retrieval possible | Implement FAISS vector search in `chatbot_engine.py` |
| 4 | `main.py` is a **6-line placeholder** | Misleading for new developers | Either remove or wire it to `run_pipeline()` |
| 5 | `run.bat` references nonexistent `app.py` and `ragenv` | Confusing; suggests dead code | Remove or update the batch file |
| 6 | **No unit tests** | Changes risk regression | Add `pytest` tests for scoring logic, Excel I/O, and metric parsing |
| 7 | JSON parsing from Azure is fragile | Malformed JSON triggers fallback scores | Use Azure OpenAI structured output API |
| 8 | Sequential processing only | Slow for 100+ questions | Add concurrent/parallel question processing |

---

## 🧪 Future Enhancement Opportunities

### 🔄 Add RAG (Retrieval-Augmented Generation)
```python
# In chatbot_engine.py — load FAISS index and retrieve relevant chunks
from langchain_community.vectorstores import FAISS
vectorstore = FAISS.load_local("faiss_index", embeddings)
docs = vectorstore.similarity_search(question, k=3)
context = "\n".join([doc.page_content for doc in docs])
prompt = f"Context:\n{context}\n\nQuestion:\n{question}"
```

### 🎯 Use the `mode` Parameter
```python
def ask_question(question, mode="general"):
    if mode == "expert":
        prompt = f"You are an expert. Answer in detail: {question}"
    elif mode == "simple":
        prompt = f"Answer in one sentence: {question}"
    else:
        prompt = question
    ...
```

### 📋 Add Tests
```python
# test_evaluation.py
def test_calculate_overall_score():
    metrics = {"Answer Relevancy": 1, "Correctness": 1, "Faithfulness": 1,
               "Context Precision": 1, "Hallucination": 0}
    assert calculate_overall_score(metrics) == 0.85
```

### ⚡ Parallel Processing
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_row, row) for _, row in df.iterrows()]
    for future in tqdm(futures, total=len(df)):
        results.append(future.result())
```

---

## 🛠️ Useful Commands Reference

| Command | Purpose |
|---------|---------|
| `uv sync` | Install/sync all project dependencies |
| `uv run python run_pipeline.py` | Run the full evaluation pipeline |
| `uv run python main.py` | Run the placeholder main (not useful) |
| `ollama pull llama3.2:latest` | Download the required Ollama model |
| `ollama list` | List downloaded Ollama models |
| `uv run python -B -m py_compile chatbot_engine.py evaluation_engine.py main.py real_metrics.py run_pipeline.py` | Syntax-check all Python files without generating `__pycache__` |

---

## 🔄 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        .env File                                     │
│  AZURE_OPENAI_API_KEY=...                                           │
│  AZURE_OPENAI_ENDPOINT=...                                          │
│  AZURE_OPENAI_API_VERSION=...                                       │
│  AZURE_OPENAI_DEPLOYMENT=...                                        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ┌───────────────┐     ┌───────────────────┐     ┌───────────────┐ │
│  │ input.xlsx   │────▶│  run_pipeline.py   │────▶│ output.xlsx  │ │
│  │ (Questions)  │     │                    │     │ (Results)    │ │
│  └───────────────┘     └───────┬───────────┘     └───────────────┘ │
│                                │                                    │
│                    ┌───────────┼───────────┐                        │
│                    ▼           ▼           ▼                        │
│          ┌────────────┐ ┌──────────┐ ┌────────────┐                │
│          │chatbot_    │ │real_     │ │evaluation_ │                │
│          │engine.py   │ │metrics.py│ │engine.py   │                │
│          │            │ │          │ │            │                │
│          │ Ollama     │ │ Azure    │ │ Score      │                │
│          │ LLM        │ │ OpenAI   │ │ Remarks    │                │
│          │            │ │          │ │ Suggestions│                │
│          └────────────┘ └──────────┘ └────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 💡 Quick Start Summary

```bash
# 1. Prerequisites check
python --version          # Must be 3.12.x
uv --version              # Must be installed
ollama --version          # Must be installed

# 2. Setup
uv sync                   # Install dependencies
ollama pull llama3.2:latest  # Download LLM model

# 3. Configure
# Edit .env with your Azure OpenAI credentials

# 4. Prepare input
# Edit data/input.xlsx with questions and expected answers

# 5. Run
uv run python run_pipeline.py

# 6. Review
# Open results/output.xlsx
```

---

## 📚 Key Technical Concepts

### Why UV instead of pip?
UV is a fast Python package manager that:
- Creates isolated virtual environments
- Locks exact dependency versions (`uv.lock`)
- Installs dependencies ~10x faster than pip

### Why Ollama + Azure instead of one LLM?
- **Ollama** runs locally — free, private, no API costs for generation
- **Azure OpenAI** handles evaluation — deterministic scoring with temperature=0
- This separation means you can swap the chatbot without changing the evaluator

### Why weighted scores?
Not all quality dimensions are equally important. The pipeline:
- Prioritizes **Correctness** and **Faithfulness** (both 0.25 weight)
- **Penalizes Hallucination** (-0.15) because unsupported info is harmful
- Treats **Context Precision** as secondary (0.15) since retrieval quality feeds into other metrics

---

## 🎯 Summary

This project is a **reusable chatbot benchmarking framework** that:

| Capability | How It Works |
|------------|--------------|
| 🗣️ **Generates answers** | Local Ollama LLM (free, private) |
| 📏 **Measures quality** | 5 Azure-scored metrics (deterministic) |
| 📊 **Calculates overall score** | Weighted formula with hallucination penalty |
| 📝 **Generates human feedback** | Remarks + improvement suggestions |
| 📋 **Batch processes** | Reads Excel, loops through rows |
| 📁 **Exports results** | Clean Excel report with all data |

It's designed to be **extensible** — you can swap the chatbot model, add document retrieval, change scoring weights, or connect a different evaluation service without rewriting the pipeline.