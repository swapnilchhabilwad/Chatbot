# Imports DeepEval metric classes.
from deepeval.metrics import (
    # Measures whether the answer contains unsupported or hallucinated claims.
    HallucinationMetric,
)

# Imports DeepEval's test case structure.
from deepeval.test_case import LLMTestCase

# Imports the custom Azure OpenAI-backed DeepEval model.
from evaluation.deepeval_config import (
    # Reusable model wrapper passed into DeepEval metrics.
    azure_model,
)

# =====================================================
# DEEPEVAL METRICS
# =====================================================


# Evaluates one question-answer pair with DeepEval hallucination scoring.
def evaluate_deepeval_metrics(
    # The original question from Excel.
    question,
    # The chatbot-generated answer.
    answer,
    # Retrieval context from the chatbot, or a fallback marker.
    contexts,
    # Expected output from Excel used as reference when context is missing.
    expected,
):

    # Handle context fallbacks. If no real retrieval context is provided,
    # use the expected output (ground truth) as reference to avoid deepeval crash.
    # Starts with the contexts returned by the chatbot.
    eval_context = contexts
    # Replaces missing or placeholder contexts with expected output so DeepEval has reference material.
    if not eval_context or eval_context == ["No retrieval context used"] or not any(eval_context):
        # Uses expected output when present; otherwise uses a readable fallback string.
        eval_context = [expected] if expected else ["No reference context available"]

    # Creates the DeepEval test case object for one evaluated answer.
    test_case = LLMTestCase(
        # Stores the user question.
        input=question,
        # Stores the chatbot's actual answer.
        actual_output=answer,
        # Stores the expected answer/reference text.
        expected_output=expected,
        # Provides context for metrics that use normal context.
        context=eval_context,
        # Provides context for metrics that specifically use retrieval context.
        retrieval_context=eval_context,
    )

    # Creates the hallucination metric using the Azure-backed DeepEval model.
    hallucination_metric = (
        HallucinationMetric(
            # Tells DeepEval to score using Azure OpenAI.
            model=azure_model
        )
    )

    # Runs the hallucination metric for this test case.
    hallucination_score = (
        hallucination_metric.measure(
            # Supplies the prepared question-answer-context object.
            test_case
        )
    )

    # Returns the score in the same dictionary shape used by the pipeline output.
    return {
        # Converts the hallucination score to a plain float for Excel output.
        "Hallucination": float(
            # Uses the score returned by DeepEval.
            hallucination_score
        )
    }
