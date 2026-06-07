def calculate_overall_score(metrics: dict):  # Combines individual metric scores into one summary score for reporting.

    weights = {  # Defines how much each quality metric should influence the final score.
        "Answer Relevancy": 0.2,  # Rewards answers that directly address the user's question.
        "Correctness": 0.25,  # Gives strong importance to matching the expected answer.
        "Faithfulness": 0.25,  # Gives strong importance to being grounded in the provided context.
        "Context Precision": 0.15,  # Rewards retrieval/context that is useful and focused.
        "Hallucination": -0.15,  # Penalizes unsupported or invented information.
    }  # Ends the weight mapping used by the scoring loop.

    score = 0  # Starts the total score at zero before adding weighted metric values.

    for k, w in weights.items():  # Loops through every metric weight so the formula stays easy to change.
        score += metrics.get(k, 0) * w  # Adds each metric's weighted contribution, using 0 if a metric is missing.

    return round(max(score, 0), 2)  # Prevents negative totals and rounds the score for readable Excel output.


def generate_remarks(score):  # Converts the numeric overall score into a human-readable quality label.

    if score >= 0.85:  # Treats very high scores as excellent quality.
        return "Excellent response quality"  # Reports the strongest positive evaluation label.
    elif score >= 0.7:  # Handles solid scores that still may have small weaknesses.
        return "Good but minor issues exist"  # Reports a good-but-not-perfect label.
    elif score >= 0.5:  # Handles middle scores where quality is acceptable but clearly weak.
        return "Needs improvement"  # Reports that the chatbot should be improved.
    return "Poor performance"  # Covers all scores below 0.5 as poor quality.


def generate_improvements(metrics):  # Builds targeted improvement suggestions from the metric values.

    suggestions = []  # Starts with no suggestions and adds only the ones supported by the metrics.

    if metrics.get("Hallucination", 0) > 0.3:  # Checks whether unsupported information is too high.
        suggestions.append("Reduce hallucination")  # Suggests reducing invented claims when hallucination is high.

    if metrics.get("Faithfulness", 1) < 0.7:  # Checks whether the answer is insufficiently based on the context.
        suggestions.append("Improve grounding in context")  # Suggests better context grounding when faithfulness is low.

    if metrics.get("Context Precision", 1) < 0.7:  # Checks whether retrieved context is too noisy or irrelevant.
        suggestions.append("Improve retrieval quality")  # Suggests improving retrieval when context precision is low.

    if not suggestions:  # Detects when no metric crossed a problem threshold.
        suggestions.append("System is performing well")  # Adds a positive default so the output column is never empty.

    return " | ".join(suggestions)  # Joins all suggestions into one Excel-friendly text cell.
