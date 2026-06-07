import os  # Provides filesystem helpers, used here to create the results folder.
import pandas as pd  # Provides Excel reading/writing and table handling for the evaluation data.
from tqdm import tqdm  # Adds a progress bar so long batches show visible progress.
from dotenv import load_dotenv  # Loads environment variables from a .env file for local configuration.

from chatbot_engine import ask_question  # Imports the local chatbot call used to generate actual answers.
from real_metrics import evaluate_all_metrics  # Imports the Azure-backed evaluator that scores each answer.
from evaluation_engine import (
    calculate_overall_score,  # Converts individual metrics into one weighted score.
    generate_remarks,  # Converts the score into a short quality remark.
    generate_improvements,  # Converts weak metrics into improvement suggestions.
)  # Ends the grouped import from the local evaluation helper module.

load_dotenv()  # Reads .env so any required API settings are available before the pipeline runs.

INPUT_FILE = "data/input.xlsx"  # Centralizes the input Excel path so it is easy to change later.
OUTPUT_FILE = "results/output.xlsx"  # Centralizes the output Excel path used after evaluation completes.


def run_pipeline():  # Orchestrates the full workflow: read questions, answer them, score them, and save results.

    df = pd.read_excel(INPUT_FILE)  # Loads the spreadsheet containing questions and expected answers.

    required = [  # Lists the columns the rest of the pipeline depends on.
        "Question",  # Holds the user question that will be sent to the chatbot.
        "Expected Output",  # Holds the reference answer used by the evaluator.
        "Mode",  # Holds the chatbot mode so the pipeline can pass behavior settings forward.
    ]  # Ends the required-column list.

    for col in required:  # Checks every required column before processing any row.
        if col not in df.columns:  # Detects a malformed input file early.
            raise Exception(f"Missing column: {col}")  # Stops with a clear message instead of failing later.

    results = []  # Collects one output dictionary per question before writing the final spreadsheet.

    # ==================================================
    # PROCESS QUESTIONS
    # ==================================================

    for idx, (_, row) in enumerate(  # Loops through each spreadsheet row while also creating a human-friendly count.
        tqdm(df.iterrows(), total=len(df)),  # Wraps row iteration in a progress bar with the known total row count.
        start=1  # Starts numbering at 1 because that is easier for users to read than zero-based indexes.
    ):  # Ends the loop header that provides both question number and row data.

        question = str(row["Question"])  # Normalizes the question value to text before sending it to the chatbot.
        expected = str(row["Expected Output"])  # Normalizes the reference answer to text for evaluation.
        mode = str(row["Mode"])  # Normalizes the mode value to text before passing it into the chatbot layer.

        print(f"\n-> Processing Question {idx}: {question}")  # Logs which question is currently being processed.

        # ----------------------------------------------
        # LOCAL LLM RESPONSE
        # ----------------------------------------------

        result = ask_question(question, mode)  # Calls the chatbot and expects answer/context data back.

        answer = str(result.get("answer", ""))  # Extracts the chatbot answer, defaulting to empty text if missing.

        contexts = result.get("contexts", [])  # Extracts retrieved context so the evaluator can judge grounding.

        if not isinstance(contexts, list):  # Handles engines that return a single context instead of a list.
            contexts = [str(contexts)]  # Converts the single context into a list so later code has one shape.

        contexts = [str(c) for c in contexts]  # Ensures every context item is text before joining or scoring.

        context_text = "\n".join(contexts)  # Combines all contexts into one readable block for Excel output.

        # ----------------------------------------------
        # AZURE EVALUATION
        # ----------------------------------------------

        metrics = evaluate_all_metrics(  # Sends the full answer package to the Azure evaluator.
            question=question,  # Provides the original user question for relevancy scoring.
            answer=answer,  # Provides the chatbot's actual response for quality scoring.
            contexts=contexts,  # Provides retrieved context for faithfulness and precision scoring.
            expected=expected,  # Provides the reference answer for correctness scoring.
        )  # Receives a dictionary of metric names and numeric scores.

        # ----------------------------------------------
        # OVERALL SCORE
        # ----------------------------------------------

        overall_score = calculate_overall_score(metrics)  # Produces one weighted summary score from all metrics.

        remarks = generate_remarks(overall_score)  # Converts the numeric score into a readable quality label.

        improvements = generate_improvements(metrics)  # Creates guidance based on whichever metrics are weak.

        # ----------------------------------------------
        # FINAL EXCEL ROW
        # ----------------------------------------------

        row_data = {  # Builds the exact output row that will become one row in the results Excel file.
            "Question": question,  # Preserves the original question for traceability.
            "Expected Output": expected,  # Preserves the reference answer beside the actual answer.
            "Actual Output": answer,  # Stores the chatbot's generated answer.
            "Retrieved Context": context_text,  # Stores the context used or retrieved for this answer.

            "Answer Relevancy":  # Names the column for the relevancy score.
                metrics.get("Answer Relevancy", 0),  # Stores relevancy, defaulting to 0 if omitted.

            "Correctness":  # Names the column for expected-answer matching.
                metrics.get("Correctness", 0),  # Stores correctness, defaulting to 0 if missing.

            "Hallucination":  # Names the column for unsupported information.
                metrics.get("Hallucination", 0),  # Stores hallucination, defaulting to 0 if missing.

            "Faithfulness":  # Names the column for context grounding.
                metrics.get("Faithfulness", 0),  # Stores faithfulness, defaulting to 0 if missing.

            "Context Precision":  # Names the column for retrieval quality.
                metrics.get("Context Precision", 0),  # Stores context precision, defaulting to 0 if missing.

            "Overall Score":  # Names the summary score column.
                overall_score,  # Stores the weighted score calculated from the metric dictionary.

            "Remarks":  # Names the human-readable assessment column.
                remarks,  # Stores the short quality remark.

            "Improvements Needed":  # Names the improvement guidance column.
                improvements,  # Stores the generated improvement suggestions.
        }  # Ends the output row dictionary.

        results.append(row_data)  # Adds this evaluated question to the full output collection.

        print(f"OK Completed Question {idx}")  # Logs completion for this specific row.

    # ==================================================
    # SAVE OUTPUT
    # ==================================================

    os.makedirs("results", exist_ok=True)  # Ensures the output folder exists before writing the Excel file.

    output_df = pd.DataFrame(results)  # Converts the list of row dictionaries into a table.

    output_df.to_excel(  # Writes the final evaluation table to an Excel workbook.
        OUTPUT_FILE,  # Uses the configured output file path.
        index=False  # Omits pandas row numbers because they are not meaningful report data.
    )  # Finishes the Excel export call.

    print("\nEvaluation Pipeline Completed Successfully!")  # Prints a final success message after saving output.


if __name__ == "__main__":  # Runs the pipeline only when this file is executed directly.
    run_pipeline()  # Starts the complete evaluation workflow.
