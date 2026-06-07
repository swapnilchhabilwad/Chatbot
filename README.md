# 🤖 Chatbot Project — Complete Multi-Version Guide

> **Repository**: [github.com/swapnilchhabilwad/Chatbot](https://github.com/swapnilchhabilwad/Chatbot)  
> **Python Version**: 3.12+  
> **Package Manager**: uv

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Chatbot1 — Hybrid PDF Chatbot](#2-chatbot1--hybrid-pdf-chatbot)
3. [Chatbot2 — Evaluation Pipeline (Azure-backed)](#3-chatbot2--evaluation-pipeline-azure-backed)
4. [Chatbot3 — Evaluation Pipeline (RAGAS + DeepEval)](#4-chatbot3--evaluation-pipeline-ragas--deepeval)
5. [Comparison Across Versions](#5-comparison-across-versions)
6. [Shared Technical Concepts](#6-shared-technical-concepts)
7. [Common Setup Steps](#7-common-setup-steps)
8. [Quick Start Commands](#8-quick-start-commands)

---

## 1. Project Overview

This repository contains **three independent chatbot projects**, each evolving in complexity and evaluation methodology:

| Version | Focus | LLM Used | Evaluation | Output |
|---------|-------|----------|------------|--------|
| **Chatbot1** | Interactive web-based chatbot with PDF RAG | Ollama (local) | None (user judges) | Real-time UI |
| **Chatbot2** | Batch evaluation pipeline with Azure judge | Ollama (answer) + Azure (evaluate) | 5 custom Azure-scored metrics | Excel report |
| **Chatbot3** | Batch evaluation pipeline with RAGAS + DeepEval | Ollama (answer) + Azure (evaluate) | RAGAS (3 metrics) + DeepEval (1 metric) | Excel report |

Each version lives in its own directory with its own `pyproject.toml`, dependencies, and virtual environment.

---

## 2. Chatbot1 — Hybrid PDF Chatbot

> **Directory**: `Chatbot1/`  
> **Entry Point**: `app.py`  
> **Interface**: Streamlit Web UI

### 2.1 What It Does

Chatbot1 is a **hybrid chatbot web application** offering two modes:

| Mode | Description |
|------|-------------|
| **Direct Chat** | User types a question → AI answers directly using local Ollama `llama3.2` |
| **PDF Chat** | User uploads PDFs → app extracts text → chunks → embeds → stores in FAISS → answers questions using **only** PDF content via RAG |

### 2.2 Architecture

```
                    ┌─────────────────────────┐
                    │   User Uploads PDFs      │
                    └──────────┬──────────────┘
                               ▼
                    ┌─────────────────────────┐
                    │  Extract Text (PyPDF2)   │
                    └──────────┬──────────────┘
                               ▼
                    ┌─────────────────────────┐
                    │  Split into Chunks       │
                    │  (1000 chars, 200 overlap)│
                    └──────────┬──────────────┘
                               ▼
                    ┌─────────────────────────┐
                    │  Embed Chunks (vectors)  │
                    │  using nomic-embed-text  │
                    └──────────┬──────────────┘
                               ▼
                    ┌─────────────────────────┐
                    │  Store in FAISS Index    │
                    │  (saved to disk)         │
                    └─────────────────────────┘
                                      │
                    User asks question │
                    ───────────────────┘
                                      ▼
                    ┌─────────────────────────┐
                    │  FAISS finds top 4       │
                    │  most similar chunks     │
                    └──────────┬──────────────┘
                               ▼
                    ┌─────────────────────────┐
                    │  LLM (llama3.2)          │
                    │  answers using context   │
                    └──────────┬──────────────┘
                               ▼
                    ┌─────────────────────────┐
                    │  Display Answer in UI    │
                    └─────────────────────────┘
```

### 2.3 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Web UI** | Streamlit |
| **Chat Model** | Ollama `llama3.2` (temperature=0.3) |
| **Embedding Model** | Ollama `nomic-embed-text` |
| **Orchestration** | LangChain (prompts, chains, RunnablePassthrough) |
| **PDF Extraction** | PyPDF2 |
| **Vector Search** | FAISS (CPU) |
| **Dependencies** | uv + pyproject.toml |

### 2.4 Key Code Components (`app.py`)

| Function | Purpose |
|----------|---------|
| `get_llm()` | Creates ChatOllama client (`llama3.2`, temperature=0.3) |
| `get_embeddings()` | Creates OllamaEmbeddings client (`nomic-embed-text`) |
| `get_pdf_text(pdf_docs)` | Extracts text from uploaded PDFs using PyPDF2 |
| `get_text_chunks(text)` | Splits text into 1000-char chunks with 200-char overlap |
| `get_vector_store(text_chunks)` | Embeds chunks and saves FAISS index to disk |
| `get_conversational_chain()` | Builds RAG pipeline: context extraction → prompt → LLM → output parser |
| `ask_pdf_question(question)` | Loads FAISS index, retrieves top-4 chunks, runs RAG chain |
| `ask_direct_question(question)` | Sends question directly to LLM without context |
| `main()` | Sets up Streamlit UI with sidebar mode selector, file upload, and chat input |

### 2.5 RAG (Retrieval-Augmented Generation) Explained

**The Problem**: AI models don't know your specific PDFs. If asked about them, they may:
- Not know the content (not in training data)
- Hallucinate (make up convincing-looking false information)
- Give generic answers instead of document-specific ones

**The RAG Solution**:
1. **Indexing**: Split PDFs into chunks → convert each chunk to a vector (embedding) → store in FAISS
2. **Retrieval**: When a question is asked, find chunks whose vectors are most similar to the question's vector
3. **Generation**: Send those chunks + the question to the LLM with instructions to answer using only that context

**Why This Works**:
- **Chunking** (1000 chars + 200 overlap): Fits within LLM context windows, preserves boundary-spanning ideas
- **Embeddings** (`nomic-embed-text`): Convert meaning into numbers for semantic (not keyword) search
- **FAISS**: Optimized for fast similarity search across millions of vectors

### 2.6 How to Run

```powershell
cd Chatbot1
uv sync                                      # Install dependencies
ollama pull llama3.2                          # Pull chat model
ollama pull nomic-embed-text                  # Pull embedding model
uv run python -m streamlit run app.py         # Start the app
# Open http://localhost:8501
```

### 2.7 Key Files

| File | Purpose |
|------|---------|
| `app.py` | ★★ Main application — the real chatbot (375 lines) |
| `main.py` | ★ Placeholder — prints "Hello from..." |
| `test_gemini.py` | ★ Standalone Google Gemini test (not part of main app) |
| `pyproject.toml` | ★★ Dependencies and project metadata |
| `run.bat` | ★ Windows launcher (needs fixing — points to wrong venv name) |

### 2.8 Limitations & Troubleshooting

| Issue | Solution |
|-------|----------|
| Streamlit not found | Use `uv run python -m streamlit run app.py` |
| Ollama model not found | Run `ollama pull llama3.2` and `ollama pull nomic-embed-text` |
| "Upload PDFs first" | Process PDFs in sidebar before asking questions |
| No readable text in PDF | PDF is scanned (image-based) — use OCR first |
| Wrong/irrelevant answers | Adjust chunk_size/chunk_overlap or use better embedding model |
| `run.bat` doesn't work | Use uv command or update .bat to use `.venv` instead of `ragenv` |

---

## 3. Chatbot2 — Evaluation Pipeline (Azure-backed)

> **Directory**: `chatbot2/`  
> **Entry Point**: `run_pipeline.py`  
> **Interface**: Command-line batch processor → Excel output

### 3.1 What It Does

Chatbot2 is a **batch evaluation pipeline** that:
1. Reads questions from `data/input.xlsx` (columns: Question, Expected Output, Mode)
2. Sends each question to local Ollama `llama3.2:latest`
3. Evaluates answers using **Azure OpenAI GPT-4o-mini** across 5 quality metrics
4. Calculates a **weighted overall score** with hallucination penalty
5. Generates **human-readable remarks** and **improvement suggestions**
6. Writes results to `results/output.xlsx`

### 3.2 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         data/input.xlsx                                 │
│  ┌───────────┬──────────────────────┬────────┐                         │
│  │ Question  │   Expected Output     │  Mode  │                         │
│  └───────────┴──────────────────────┴────────┘                         │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         run_pipeline.py                                 │
│                                                                         │
│  For each row:                                                          │
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
```

### 3.3 Module-by-Module Breakdown

#### `chatbot_engine.py` (13 lines)
- Creates `ChatOllama(model="llama3.2:latest", temperature=0.3)`
- Returns `{"answer": response.content, "contexts": []}`
- **Known issue**: `mode` parameter accepted but never used

#### `real_metrics.py` (184 lines)
- Reads 4 Azure environment variables from `.env`
- Builds a strict JSON-only evaluation prompt
- Uses `temperature=0` for deterministic scoring
- Returns 5 metrics (0.0–1.0):
  - Answer Relevancy, Correctness, Hallucination, Faithfulness, Context Precision
- **Fallback on failure**: All zeros (hallucination defaults to 1.0)

#### `evaluation_engine.py` (46 lines)
Three helper functions:

| Function | Purpose |
|----------|---------|
| `calculate_overall_score(metrics)` | Weighted sum: Relevancy (+0.20) + Correctness (+0.25) + Faithfulness (+0.25) + Context Precision (+0.15) + Hallucination (**-0.15**) |
| `generate_remarks(score)` | Converts score to qualitative label: ≥0.85 Excellent, ≥0.70 Good, ≥0.50 Needs Improvement, <0.50 Poor |
| `generate_improvements(metrics)` | Suggests fixes based on threshold triggers (hallucination > 0.3 → "Reduce hallucination") |

#### `run_pipeline.py` (145 lines)
- The main orchestrator
- Validates input columns
- Loops through rows with progress bar
- Assembles and saves results to Excel

### 3.4 Scoring System

| Metric | Weight | Purpose |
|--------|--------|---------|
| Answer Relevancy | +0.20 | Rewards on-topic answers |
| Correctness | +0.25 | Matches expected output |
| Faithfulness | +0.25 | Grounded in context |
| Context Precision | +0.15 | Useful retrieval |
| Hallucination | **-0.15** | Penalty for unsupported info |

Score is clamped to minimum 0.0 and rounded to 2 decimal places.

### 3.5 Azure Configuration (.env)

```env
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### 3.6 How to Run

```bash
cd chatbot2
uv sync                                        # Install dependencies
ollama pull llama3.2:latest                     # Pull the LLM model
# Create .env with Azure credentials
# Prepare data/input.xlsx
uv run python run_pipeline.py                   # Run the pipeline
# Check results/output.xlsx
```

### 3.7 Known Limitations

| # | Limitation | Impact |
|---|------------|--------|
| 1 | `mode` parameter never used | Mode has no effect on behavior |
| 2 | Contexts always empty list | Faithfulness & Context Precision metrics are meaningless |
| 3 | FAISS index exists but unused | No document retrieval |
| 4 | No unit tests | Changes risk regression |
| 5 | JSON parsing from Azure fragile | Malformed JSON triggers fallback scores |
| 6 | Sequential processing only | Slow for 100+ questions |

---

## 4. Chatbot3 — Evaluation Pipeline (RAGAS + DeepEval)

> **Directory**: `chatbot3/`  
> **Entry Point**: `run_pipeline.py`  
> **Interface**: Command-line batch processor → Excel output

### 4.1 What It Does

Chatbot3 is the **most advanced evaluation pipeline**, using two dedicated evaluation frameworks:
1. Reads questions from `data/input.xlsx`
2. Sends each question to local Ollama `llama3.2`
3. Evaluates answers using **RAGAS** (3 metrics) + **DeepEval** (1 metric)
4. Calculates a weighted overall score
5. Saves results to `results/output.xlsx`

### 4.2 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         .env File                                     │
│  AZURE_OPENAI_API_KEY=...    AZURE_OPENAI_EMBEDDING_DEPLOYMENT=...  │
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
│          │chatbot_    │ │evaluation│ │evaluation  │                │
│          │engine.py   │ │_engine   │ │_engine     │                │
│          │            │ │(RAGAS)   │ │(DeepEval)  │                │
│          │ Ollama     │ │          │ │            │                │
│          │ LLM        │ │ Azure    │ │ Azure      │                │
│          │            │ │ GPT-4o   │ │ GPT-4o     │                │
│          └────────────┘ └──────────┘ └────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Project Structure

```
chatbot3/
├── .env                             # Azure OpenAI credentials
├── pyproject.toml                   # uv project config
├── run_pipeline.py                  # ★★ MAIN ENTRY POINT
├── chatbot_engine.py                # Ollama chatbot wrapper
├── test_ragas.py                    # Standalone RAGAS demo
├── test_deepeval.py                 # Standalone DeepEval demo
├── config/
│   ├── settings.py                  # Pydantic model for .env
│   └── azure_clients.py             # Azure client factories
├── evaluation/
│   ├── evaluation_engine.py         # Orchestrator (RAGAS + DeepEval + scoring)
│   ├── ragas_metrics.py             # RAGAS metric runner
│   ├── ragas_config.py              # LEGACY (import-time clients)
│   ├── deepeval_metrics.py          # DeepEval hallucination scoring
│   └── deepeval_config.py           # Azure wrapper for DeepEval
├── data/input.xlsx                  # Input questions
└── results/output.xlsx              # Output scores
```

### 4.4 Module Walkthrough

#### `config/settings.py` — Configuration Hub
- Pydantic `BaseModel` with all 5 Azure settings from `.env`
- Singleton `settings` object shared across all modules
- `load_dotenv()` called here (also redundantly in `run_pipeline.py`)

#### `config/azure_clients.py` — Client Factories
- `_required_setting(name)`: Validates and returns non-empty setting, raises `ValueError` with clear message
- `get_azure_llm()`: Creates `AzureChatOpenAI` with `temperature=0` for deterministic scoring
- `get_azure_embeddings()`: Creates `AzureOpenAIEmbeddings` for RAGAS embedding metrics
- Both use `SecretStr` for API key security

#### `evaluation/ragas_metrics.py` — RAGAS Integration
- **Data normalization pipeline**: `_to_text()` → `_to_context_list()` → `Dataset.from_dict()` → `ragas.evaluate()` → `_ragas_result_to_record()` → `_score()`
- **`_to_text(value, fallback)`**: Universal sanitizer handling None, NaN, empty strings, and type errors
- **`_to_context_list(contexts, expected)`**: Normalizes contexts to list, falls back to expected output when contexts are empty or contain the placeholder `"No retrieval context used"`
- **`_score(result_dict, key)`**: Safe metric extraction handling NaN, None, and conversion errors
- **Metrics evaluated**: Faithfulness, Answer Relevancy, Context Precision

#### `evaluation/deepeval_config.py` — Azure Wrapper for DeepEval
- `AzureOpenAIModel(DeepEvalBaseLLM)`: Adapts Azure OpenAI to DeepEval's interface
  - `load_model()`: Lazy-loads Azure client (cached after first call)
  - `generate(prompt)`: Synchronous LLM call
  - `a_generate(prompt)`: Async LLM call
  - `get_model_name()`: Returns `"Azure OpenAI"`
- Module-level singleton `azure_model` reused across all metric calls

#### `evaluation/deepeval_metrics.py` — DeepEval Hallucination
- Context fallback: If contexts are None/empty/placeholder → uses expected output as context
- Builds `LLMTestCase` with question, answer, expected output, context, and retrieval context
- Runs `HallucinationMetric(model=azure_model).measure(test_case)`

#### `evaluation/evaluation_engine.py` — Combined Orchestrator
- `evaluate_all_metrics()`: Calls RAGAS (3 metrics) + DeepEval (1 metric), wraps each in try/except
- `calculate_overall_score()`: Weighted formula with hallucination penalty
  - Answer Relevancy: **+0.3**
  - Faithfulness: **+0.3**
  - Context Precision: **+0.2**
  - Hallucination: **-0.2**

### 4.5 Azure Configuration

```env
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002
```

### 4.6 How to Run

```bash
cd chatbot3
uv sync
ollama pull llama3.2
# Create .env with Azure credentials
# Prepare data/input.xlsx
uv run python run_pipeline.py
# Check results/output.xlsx
```

### 4.7 Evaluation Metrics Explained

#### RAGAS Metrics

| Metric | What It Measures | Score Range | How It Works |
|--------|-----------------|-------------|--------------|
| **Faithfulness** | Is the answer supported by context? | 0–1 (higher=better) | Breaks answer into claims, checks each against context |
| **Answer Relevancy** | Does the answer address the question? | 0–1 (higher=better) | Generates hypothetical questions from answer, checks similarity to original |
| **Context Precision** | Is the context useful/precise? | 0–1 (higher=better) | Checks if relevant information appears early in context list |

#### DeepEval Metric

| Metric | What It Measures | Score Range | How It Works |
|--------|-----------------|-------------|--------------|
| **Hallucination** | Does answer contain fabricated info? | 0–1 (**lower=better**) | Compares claims against context, counts unsupported ones |

#### Scoring Formula

```
Overall = (Answer_Relevancy × 0.3) + (Faithfulness × 0.3) + (Context_Precision × 0.2) + (Hallucination × -0.2)
Final   = max(Overall, 0), rounded to 2 decimal places
```

### 4.8 Error Handling (5-Layer Defense)

| Layer | What It Protects Against |
|-------|-------------------------|
| 1: File Validation | Missing `data/input.xlsx` → graceful exit |
| 2: Row Validation | Empty/NaN questions → skip row with warning |
| 3: Data Normalization | None, NaN, empty strings → safe defaults |
| 4: Evaluation Failure | RAGAS/DeepEval network errors → 0.0 fallback scores |
| 5: Score Safety | NaN/None metrics → treated as 0.0 |

### 4.9 Known Limitations

| Issue | Impact |
|-------|--------|
| No document retrieval | Contexts are placeholder text; Faithfulness/Context Precision operate on meaningless context |
| FAISS index exists but unused | Artifacts from previous RAG-enabled version |
| Sequential processing | No parallelism for multiple rows |
| RAGAS clients created per row | Unnecessary overhead (could be cached) |
| Test files make real API calls | Cannot be used with pytest |

---

## 5. Comparison Across Versions

### Feature Matrix

| Feature | Chatbot1 | Chatbot2 | Chatbot3 |
|---------|:--------:|:--------:|:--------:|
| **Interface** | Streamlit Web UI | CLI + Excel | CLI + Excel |
| **Chatbot LLM** | Ollama `llama3.2` | Ollama `llama3.2:latest` | Ollama `llama3.2` |
| **Chatbot Temperature** | 0.3 | 0.3 | 0.3 |
| **PDF Support** | ✅ Yes (RAG with FAISS) | ❌ No | ❌ No |
| **Evaluation** | ❌ None (user judges) | ✅ Azure GPT-4o-mini | ✅ RAGAS + DeepEval on Azure |
| **Evaluation LLM Temp** | N/A | 0.0 (deterministic) | 0.0 (deterministic) |
| **Number of Metrics** | 0 | 5 | 4 (3 RAGAS + 1 DeepEval) |
| **Hallucination Check** | ❌ No | ✅ Yes (metric) | ✅ Yes (DeepEval) |
| **Output Format** | Real-time UI | `results/output.xlsx` | `results/output.xlsx` |
| **Batch Processing** | ❌ No (single session) | ✅ Yes (multi-row) | ✅ Yes (multi-row) |
| **Azure Required** | ❌ No | ✅ Yes | ✅ Yes |
| **Config Layer** | Hardcoded in app.py | Direct `os.getenv` | Pydantic + factories |
| **Embeddings** | Ollama `nomic-embed-text` | N/A | Azure `text-embedding-ada-002` |
| **Weights System** | N/A | Manual weights | Cleaner weighted formula |
| **Error Handling** | Basic | Basic | 5-layer defense |

### Output Columns Comparison

| Chatbot1 (Streamlit UI) | Chatbot2 (Excel) | Chatbot3 (Excel) |
|:-----------------------:|:----------------:|:----------------:|
| Question (chat input) | Question | Question |
| Answer (displayed) | Expected Output | Expected Output |
| Context type indicator | Actual Output | Actual Output |
| | Retrieved Context | Faithfulness |
| | Answer Relevancy | Answer Relevancy |
| | Correctness | Context Precision |
| | Hallucination | Hallucination |
| | Faithfulness | Overall Score |
| | Context Precision | |
| | Overall Score | |
| | Remarks | |
| | Improvements Needed | |

### Code Complexity

| Metric | Chatbot1 | Chatbot2 | Chatbot3 |
|--------|:--------:|:--------:|:--------:|
| Python Files | 5 | 6 | 10 |
| Total Lines (app) | ~375 | ~388 | ~450+ |
| Dependencies | ~10 | ~30 | ~30+ |
| External Services | Ollama only | Ollama + Azure | Ollama + Azure |
| Config Management | Hardcoded | `.env` direct | `.env` + Pydantic |
| Evaluation Frameworks | None | Custom prompts | RAGAS + DeepEval |

---

## 6. Shared Technical Concepts

### 6.1 Ollama — Local LLM Runner

[Ollama](https://ollama.com) is used across all three versions to run AI models **locally** on your machine. It:
- Runs as a background service
- Downloads models on demand
- Supports GPU acceleration when available
- Requires no internet after initial model download

**Models Used**:
- `llama3.2` / `llama3.2:latest` — For generating answers (ChatBot)
- `nomic-embed-text` — For generating text embeddings (Chatbot1 only)

### 6.2 Azure OpenAI — Evaluation Judge

Chatbot2 and Chatbot3 use Azure OpenAI as the evaluation/judge LLM:
- **GPT-4o-mini**: Acts as the evaluator (temperature=0 for deterministic results)
- **text-embedding-ada-002**: Provides embeddings for RAGAS metrics (Chatbot3 only)
- **API Version**: `2024-12-01-preview`

### 6.3 uv — Python Package Manager

All three versions use [uv](https://github.com/astral-sh/uv) as their package manager:
- 10x faster than pip
- Locks exact dependency versions (`uv.lock`)
- Provides `uv sync`, `uv run`, `uv add`, `uv lock` commands
- Creates isolated virtual environments

### 6.4 RAG (Retrieval-Augmented Generation)

Only Chatbot1 implements full RAG. The concept involves:
1. **Chunking**: Breaking documents into manageable pieces
2. **Embedding**: Converting text to numerical vectors
3. **Indexing**: Storing vectors in a searchable database (FAISS)
4. **Retrieval**: Finding relevant chunks based on semantic similarity
5. **Generation**: Having the LLM answer using only retrieved context

### 6.5 FAISS (Facebook AI Similarity Search)

Used in Chatbot1 (and present but unused in Chatbot2/Chatbot3):
- CPU-optimized vector database
- Stores embeddings as searchable indices
- Enables fast similarity search across thousands of documents
- Index saved to `faiss_index/` directory

### 6.6 Evaluation Metrics & Scoring

Chatbot2 and Chatbot3 share similar scoring philosophies:
- **Answer Relevancy**: Is the answer on-topic?
- **Correctness/Faithfulness**: Does the answer match expected or grounded truth?
- **Hallucination**: Does the answer fabricate information? (penalized)
- **Context Precision**: Is the retrieved context relevant? (when retrieval is available)
- Weighted scoring with hallucination penalty

---

## 7. Common Setup Steps

### Step 1: Install Python 3.12+

```bash
python --version
# Must show Python 3.12.x
```

### Step 2: Install uv

```bash
pip install uv
uv --version
```

### Step 3: Install Ollama

Download from [ollama.com](https://ollama.com) and install.

Pull required models:
```bash
ollama pull llama3.2
ollama pull nomic-embed-text   # Only needed for Chatbot1
```

Make sure Ollama is **running** (check system tray / background service).

### Step 4: Azure OpenAI (Chatbot2 & Chatbot3 Only)

You need an Azure OpenAI resource with:
- A deployed chat model (e.g., `gpt-4o-mini`)
- (Chatbot3 only) A deployed embedding model (e.g., `text-embedding-ada-002`)

Create a `.env` file with:
```env
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
# Chatbot3 only:
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002
```

---

## 8. Quick Start Commands

### Chatbot1 — PDF Web Chatbot

```powershell
cd Chatbot1
uv sync
ollama pull llama3.2
ollama pull nomic-embed-text
uv run python -m streamlit run app.py
# Open http://localhost:8501
```

### Chatbot2 — Azure-backed Evaluation Pipeline

```bash
cd chatbot2
uv sync
ollama pull llama3.2:latest
# Create .env with Azure credentials
# Prepare data/input.xlsx
uv run python run_pipeline.py
# Open results/output.xlsx
```

### Chatbot3 — RAGAS + DeepEval Evaluation Pipeline

```bash
cd chatbot3
uv sync
ollama pull llama3.2
# Create .env with Azure credentials
# Prepare data/input.xlsx
uv run python run_pipeline.py
# Open results/output.xlsx
```

---

> **End of Multi-Version Project Guide**  
> This document summarizes all three chatbot versions in this repository. Each version has its own detailed guide in its respective directory:
> - `Chatbot1/COMPLETE_PROJECT_GUIDE.md` — Full Chatbot1 documentation (697 lines)
> - `chatbot2/COMPLETE_PROJECT_GUIDE.md` — Full Chatbot2 documentation (635 lines)
> - `chatbot3/COMPREHENSIVE_PROJECT_GUIDE.md` — Full Chatbot3 documentation (1613 lines)