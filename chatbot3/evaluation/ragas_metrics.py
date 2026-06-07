# Imports Any so helper functions can safely handle third-party return objects with imperfect type hints.
from typing import Any

# Imports Hugging Face Dataset because RAGAS expects evaluation data in this format.
from datasets import Dataset
# Imports the main RAGAS evaluate function.
from ragas import evaluate

# Imports the RAGAS metrics used by this project.
from ragas.metrics import (
    # Measures whether the answer is supported by the provided context.
    faithfulness,
    # Measures whether the answer directly responds to the question.
    answer_relevancy,
    # Measures whether the retrieved context is useful for the expected answer.
    context_precision,
)

# Imports Azure OpenAI client factories for the evaluator LLM and embeddings model.
from config.azure_clients import get_azure_llm, get_azure_embeddings

# =====================================================
# UTILITIES
# =====================================================


# Converts any input value into safe text for RAGAS.
def _to_text(value, fallback=""):
    # Uses the fallback when the value is missing.
    if value is None:
        # Returns the caller-provided fallback text.
        return fallback

    # Tries to detect NaN values without importing pandas or numpy here.
    try:
        # NaN is the only common value that is not equal to itself.
        if value != value:  # NaN check
            # Uses fallback text when the value is NaN.
            return fallback
    # Some custom objects may not support self-comparison cleanly.
    except TypeError:
        # If comparison is not supported, continue with string conversion.
        pass

    # Converts the value to a trimmed string.
    value = str(value).strip()
    # Returns the cleaned string, or fallback when the cleaned string is empty.
    return value if value else fallback


# Converts contexts into the list-of-strings format expected by RAGAS.
def _to_context_list(contexts, expected):
    # Treats a single context string as a one-item context list.
    if isinstance(contexts, str):
        # Wraps the string so later code can iterate over contexts safely.
        contexts = [contexts]

    # Uses an empty list when no context value is provided.
    if contexts is None:
        # Normalizes missing contexts before fallback handling.
        contexts = []

    # Wraps scalar non-list context values so they are not accidentally iterated character-by-character.
    if not isinstance(contexts, (list, tuple, set)):
        # Converts the scalar context into a one-item list.
        contexts = [contexts]

    # Builds a clean context list by dropping blank or invalid context entries.
    cleaned_contexts = [
        # Converts each context item to safe text.
        _to_text(c)
        # Iterates through every provided context item.
        for c in contexts
        # Keeps only context items that become non-empty text.
        if _to_text(c)
    ]

    # Uses expected output as fallback when there is no real retrieval context.
    if not cleaned_contexts or cleaned_contexts == ["No retrieval context used"]:
        # Creates a one-item fallback list so RAGAS always receives context text.
        cleaned_contexts = [
            # Uses expected answer when possible, otherwise a readable placeholder.
            _to_text(expected, "No reference context available")]

    # Returns the final context list for the RAGAS dataset.
    return cleaned_contexts


# Converts one metric value from the RAGAS result dictionary into a safe float.
def _score(result_dict, key):
    # Reads the metric value, defaulting to 0 when the key is missing.
    value = result_dict.get(key, 0)

    # Tries to convert the metric value into a number.
    try:
        # Converts strings, integers, and floats into a float score.
        value = float(value)
    # Handles missing, invalid, or non-numeric metric values.
    except (TypeError, ValueError):
        # Returns a safe zero score when conversion fails.
        return 0.0

    # Handles NaN values that can appear when metric calculation fails internally.
    if value != value:  # NaN check
        # Returns a safe zero score for NaN.
        return 0.0

    # Returns the valid numeric score.
    return value


# Converts the RAGAS evaluation object into the first result row as a dictionary.
def _ragas_result_to_record(result: Any) -> dict[str, Any]:
    # Converts the RAGAS result into its pandas representation.
    pandas_result: Any = result.to_pandas()

    # Handles RAGAS versions/type hints where to_pandas may expose an iterator of DataFrames.
    if not hasattr(pandas_result, "to_dict"):
        # Reads the first DataFrame from the iterator, or None if there is no result.
        pandas_result = next(iter(pandas_result), None)

    # Stops with a clear error if RAGAS returned no DataFrame.
    if pandas_result is None:
        # Raises a readable error for the evaluation wrapper to catch.
        raise ValueError("RAGAS evaluation returned empty result")

    # Converts the DataFrame rows into a list of dictionaries.
    records = pandas_result.to_dict(orient="records")

    # Stops if the DataFrame exists but contains no rows.
    if not records:
        # Raises a readable error for the evaluation wrapper to catch.
        raise ValueError("RAGAS evaluation returned empty result")

    # Returns the first and only row because this function evaluates one question at a time.
    return records[0]


# =====================================================
# MAIN RAGAS EVALUATION FUNCTION
# =====================================================

def evaluate_ragas_metrics(
    # The question asked by the user or loaded from Excel.
    question,
    # The chatbot-generated answer.
    answer,
    # The retrieval context list or fallback context marker.
    contexts,
    # The expected output from the Excel file.
    expected,
):

    # Normalizes the question into non-empty text for RAGAS.
    question = _to_text(question, "No question provided.")
    # Normalizes the chatbot answer into non-empty text for RAGAS.
    answer = _to_text(answer, "No answer provided.")
    # Normalizes the expected answer into non-empty ground truth text.
    expected = _to_text(expected, "No expected output provided.")
    # Normalizes contexts into the list format required by RAGAS.
    contexts = _to_context_list(contexts, expected)

    # Builds a one-row dataset because the pipeline evaluates one Excel row at a time.
    dataset = Dataset.from_dict(
        # Defines the RAGAS-required columns.
        {
            # Stores the user question.
            "question": [question],
            # Stores the chatbot answer.
            "answer": [answer],
            # Stores context as a list inside a one-row dataset.
            "contexts": [contexts],
            # Stores the expected output as ground truth.
            "ground_truth": [expected],
        }
    )

    # Creates the Azure chat evaluator model only when RAGAS is actually run.
    azure_llm = get_azure_llm()
    # Creates the Azure embeddings model used by context precision and relevancy metrics.
    azure_embeddings = get_azure_embeddings()

    # Runs RAGAS metrics on the one-row dataset.
    result = evaluate(
        # Supplies the prepared dataset.
        dataset=dataset,
        # Selects the configured RAGAS metrics.
        metrics=[
            # Checks whether the answer is grounded in the context.
            faithfulness,
            # Checks whether the answer is relevant to the question.
            answer_relevancy,
            # Checks whether the context is precise for the answer.
            context_precision,
        ],
        # Provides the Azure LLM used by RAGAS judge prompts.
        llm=azure_llm,
        # Provides Azure embeddings for embedding-based RAGAS metrics.
        embeddings=azure_embeddings,
    )

    # Extracts the first result row as a normal dictionary.
    result_dict = _ragas_result_to_record(result)

    # Returns only the metric names used by the final Excel output.
    return {
        # Converts faithfulness to a safe float.
        "Faithfulness": _score(result_dict, "faithfulness"),
        # Converts answer relevancy to a safe float.
        "Answer Relevancy": _score(result_dict, "answer_relevancy"),
        # Converts context precision to a safe float.
        "Context Precision": _score(result_dict, "context_precision"),
    }
