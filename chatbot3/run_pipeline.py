# Imports OS helpers for checking files and creating folders.
import os
# Imports pandas for reading the Excel input and writing the Excel output.
import pandas as pd
# Imports dotenv loader so the pipeline can read API/model settings from .env.
from dotenv import load_dotenv

# Imports the chatbot function that answers each question from Excel.
from chatbot_engine import ask_question
# Imports the evaluation functions that calculate RAGAS, DeepEval, and overall scores.
from evaluation.evaluation_engine import (
    # Runs all configured metric evaluators for one question-answer pair.
    evaluate_all_metrics,
    # Combines individual metric scores into one final score.
    calculate_overall_score,
)

# =====================================================
# LOAD ENV
# =====================================================
# Loads .env values before Azure/RAGAS/DeepEval code needs them.
load_dotenv()

# Defines the Excel file that contains the input questions.
INPUT_FILE = "data/input.xlsx"
# Defines the Excel file where final responses and metrics will be saved.
OUTPUT_FILE = "results/output.xlsx"

# =====================================================
# MAIN PIPELINE WORKFLOW
# =====================================================


# Runs the full non-UI workflow: read Excel, answer questions, evaluate, and write Excel.
def run_pipeline():
    # Prints a start message so the terminal user knows the batch job has begun.
    print("[START] Starting Chatbot Evaluation Pipeline...")

    # Load input file
    # Stops early if the expected input Excel file is not present.
    if not os.path.exists(INPUT_FILE):
        # Tells the user exactly which file path is missing.
        print(f"[ERROR] Input file not found at {INPUT_FILE}")
        # Exits the function because there is nothing to process.
        return

    # Reads all questions and expected outputs from the Excel file into a DataFrame.
    df = pd.read_excel(INPUT_FILE)
    # Creates an empty list that will collect one result dictionary per processed row.
    results = []

    # Shows how many rows were loaded from the input file.
    print(f"[INFO] Loaded {len(df)} questions from {INPUT_FILE}.\n")

    # =====================================================
    # SAFE LOOP (NO TYPE ERRORS)
    # =====================================================
    # Loops through each Excel row while keeping a numeric row index for progress messages.
    for idx, row in enumerate(df.itertuples(index=False)):

        # Reads the Question column if it exists; otherwise returns None.
        question = getattr(row, "Question", None)
        # Reads the Expected Output column if it exists; otherwise returns None.
        expected = getattr(row, "Expected Output", None)
        # Reads the Mode column if it exists; otherwise uses the default general mode.
        mode = getattr(row, "Mode", "general")

        # --------------------------
        # Validate question
        # --------------------------
        # Skips rows where the question is missing, NaN, or only whitespace.
        if question is None or pd.isna(question) or not str(question).strip():
            # Logs which row was skipped so the input file can be corrected later.
            print(f"[WARNING] Skipping row {idx}: Empty Question")
            # Moves to the next Excel row without calling the chatbot or evaluators.
            continue

        # Converts the question to clean text before sending it to the chatbot.
        question = str(question).strip()

        # --------------------------
        # Expected output cleanup
        # --------------------------
        # Uses a safe fallback when the expected answer is missing.
        if expected is None or pd.isna(expected):
            # This fallback prevents evaluator validation errors caused by blank ground truth.
            expected = "No expected output provided."
        else:
            # Converts the expected output to clean text.
            expected = str(expected).strip()

        # --------------------------
        # Mode cleanup
        # --------------------------
        # Uses the general mode when the Excel row does not specify a valid mode.
        if mode is None or pd.isna(mode):
            # Keeps the chatbot call stable even when the Mode column is blank.
            mode = "general"
        else:
            # Converts the mode value to clean text.
            mode = str(mode).strip()

        # =====================================================
        # CHATBOT CALL
        # =====================================================
        # Prints row progress and the current question.
        print(f"\nQuestion {idx + 1}/{len(df)}: {question}")

        # Sends the question to the chatbot and receives the answer plus context list.
        chatbot_result = ask_question(question, mode=mode)

        # Safely reads the answer from the chatbot response dictionary.
        answer = chatbot_result.get("answer", "")
        # Safely reads retrieval contexts from the chatbot response dictionary.
        contexts = chatbot_result.get("contexts", [])

        # Prints the generated answer so the terminal log is useful during long runs.
        print(f"Chatbot Answer: {answer}")

        # =====================================================
        # EVALUATION
        # =====================================================
        # Announces that metric calculation is starting for this row.
        print("Running RAGAS and DeepEval metrics...")

        # Runs RAGAS and DeepEval metrics using the question, answer, contexts, and expected output.
        metrics = evaluate_all_metrics(
            # Sends the cleaned question text to the evaluators.
            question=question,
            # Sends the chatbot answer to the evaluators.
            answer=answer,
            # Sends retrieval context or fallback context to the evaluators.
            contexts=contexts,
            # Sends the expected output as ground truth/reference text.
            expected=expected,
        )

        # Calculates the final weighted score from the individual metric scores.
        overall_score = calculate_overall_score(metrics)

        # =====================================================
        # STORE RESULT
        # =====================================================
        # Adds one complete output row to the results list.
        results.append({
            # Stores the original cleaned question.
            "Question": question,
            # Stores the cleaned expected output.
            "Expected Output": expected,
            # Stores the chatbot's generated answer.
            "Actual Output": answer,
            # Stores the RAGAS faithfulness score, or 0 if unavailable.
            "Faithfulness": metrics.get("Faithfulness", 0),
            # Stores the RAGAS answer relevancy score, or 0 if unavailable.
            "Answer Relevancy": metrics.get("Answer Relevancy", 0),
            # Stores the RAGAS context precision score, or 0 if unavailable.
            "Context Precision": metrics.get("Context Precision", 0),
            # Stores the DeepEval hallucination score, or 0 if unavailable.
            "Hallucination": metrics.get("Hallucination", 0),
            # Stores the final weighted overall score.
            "Overall Score": overall_score,
        })

        # Prints completion status for the current row.
        print(
            # Includes the row number and final score in the terminal log.
            f"Completed Question {idx + 1}. Overall Score: {overall_score}\n")

    # =====================================================
    # SAVE OUTPUT
    # =====================================================
    # Creates the results folder if it does not already exist.
    os.makedirs("results", exist_ok=True)

    # Converts the collected result dictionaries into a DataFrame.
    output_df = pd.DataFrame(results)
    # Writes the DataFrame to an Excel file without adding a pandas index column.
    output_df.to_excel(OUTPUT_FILE, index=False)

    # Prints the final output path after the pipeline finishes.
    print(f"[SUCCESS] Pipeline Completed. Results saved to {OUTPUT_FILE}")


# =====================================================
# ENTRY POINT
# =====================================================

# Runs the pipeline only when this file is executed directly.
if __name__ == "__main__":
    # Starts the Excel processing workflow.
    run_pipeline()
