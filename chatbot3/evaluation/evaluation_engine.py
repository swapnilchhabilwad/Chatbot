# Imports the RAGAS metric runner.
from evaluation.ragas_metrics import evaluate_ragas_metrics
# Imports the DeepEval metric runner.
from evaluation.deepeval_metrics import evaluate_deepeval_metrics

# =====================================================
# COMBINED EVALUATION
# =====================================================


# Runs every configured evaluator and combines their scores into one dictionary.
def evaluate_all_metrics(
    # The original question from Excel.
    question,
    # The chatbot-generated answer.
    answer,
    # Context returned by the chatbot or fallback marker.
    contexts,
    # Expected answer from Excel.
    expected,
):
    # Initializes default RAGAS scores so the pipeline can continue if RAGAS fails.
    ragas_scores = {
        # Default faithfulness score.
        "Faithfulness": 0.0,
        # Default answer relevancy score.
        "Answer Relevancy": 0.0,
        # Default context precision score.
        "Context Precision": 0.0,
    }
    
    # Attempts RAGAS evaluation without stopping the whole Excel pipeline on one bad row.
    try:
        # Runs the configured RAGAS metrics for this question-answer pair.
        ragas_scores = evaluate_ragas_metrics(
            # Sends the original question.
            question,
            # Sends the chatbot answer.
            answer,
            # Sends the context list.
            contexts,
            # Sends the expected output.
            expected,
        )
    # Catches any RAGAS error so later rows and DeepEval can still run.
    except Exception as e:
        # Prints the RAGAS warning while keeping the pipeline alive.
        print(f"[WARNING] RAGAS evaluation failed for this question: {e}")

    # Initializes default DeepEval scores so the pipeline can continue if DeepEval fails.
    deepeval_scores = {
        # Default hallucination score.
        "Hallucination": 0.0,
    }
    
    # Attempts DeepEval evaluation without stopping the whole Excel pipeline on one bad row.
    try:
        # Runs the configured DeepEval metrics for this question-answer pair.
        deepeval_scores = evaluate_deepeval_metrics(
            # Sends the original question.
            question,
            # Sends the chatbot answer.
            answer,
            # Sends the context list.
            contexts,
            # Sends the expected output.
            expected,
        )
    # Catches any DeepEval error so the pipeline can still write output.
    except Exception as e:
        # Prints the DeepEval warning while keeping the pipeline alive.
        print(f"[WARNING] DeepEval evaluation failed for this question: {e}")

    # Merges RAGAS and DeepEval scores into one output dictionary.
    final_scores = {
        # Adds all RAGAS score keys.
        **ragas_scores,
        # Adds all DeepEval score keys.
        **deepeval_scores,
    }

    # Returns the combined metrics to the pipeline.
    return final_scores

# =====================================================
# OVERALL SCORE
# =====================================================


# Imports math for safe NaN checks during overall score calculation.
import math

# Calculates one weighted overall score from the metric dictionary.
def calculate_overall_score(metrics):

    # Defines how much each metric contributes to the final score.
    weights={
        # Rewards answer relevancy.
        "Answer Relevancy": 0.3,
        # Rewards faithfulness to context.
        "Faithfulness": 0.3,
        # Rewards precise/useful context.
        "Context Precision": 0.2,
        # Penalizes hallucination because lower hallucination is better.
        "Hallucination": -0.2,
    }

    # Starts the weighted total at zero.
    score=0

    # Loops over each metric weight to build the final weighted score.
    for metric, weight in weights.items():
        # Reads the metric value, using 0 when it is missing.
        val = metrics.get(metric, 0)
        # Handle nan or None values due to timeouts/exceptions safely
        # Replaces None or NaN values with zero before math operations.
        if val is None or (isinstance(val, float) and math.isnan(val)):
            # Uses zero when the evaluator could not produce a usable score.
            val = 0

        # Adds this metric's weighted contribution to the final score.
        score += val * weight

    # Prevents negative final scores and rounds the result for Excel readability.
    return round(max(score, 0), 2)
