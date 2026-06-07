import os  # Reads API configuration values from environment variables.
import json  # Parses the evaluator model's JSON text into a Python dictionary.

from dotenv import load_dotenv  # Loads local .env settings so secrets do not need to be hard-coded.
from openai import AzureOpenAI  # Provides the Azure OpenAI client used for metric evaluation.

load_dotenv()  # Makes .env values available through os.getenv before configuration is read.

# ======================================================
# ENV VARIABLES
# ======================================================

AZURE_API_KEY: str = os.getenv(  # Reads the Azure API key needed to authenticate evaluator requests.
    "AZURE_OPENAI_API_KEY"  # Names the environment variable expected in the .env file.
) or ""  # Falls back to an empty string so the safety check can produce a clear error.

AZURE_ENDPOINT: str = os.getenv(  # Reads the Azure endpoint URL for the OpenAI resource.
    "AZURE_OPENAI_ENDPOINT"  # Names the environment variable that stores the Azure resource endpoint.
) or ""  # Falls back to empty text so missing configuration is easy to validate.

AZURE_API_VERSION: str = os.getenv(  # Reads the Azure OpenAI API version used by this client.
    "AZURE_OPENAI_API_VERSION"  # Names the environment variable that stores the API version.
) or ""  # Falls back to empty text so the later check can stop with a friendly message.

AZURE_DEPLOYMENT: str = os.getenv(  # Reads the Azure model deployment name that should score answers.
    "AZURE_OPENAI_DEPLOYMENT"  # Names the environment variable that points to the deployment.
) or ""  # Falls back to empty text so missing deployment configuration is caught early.

# ======================================================
# SAFETY CHECKS
# ======================================================

if not AZURE_API_KEY:  # Stops early if authentication is not configured.
    raise Exception(  # Raises a clear setup error instead of letting the API call fail later.
        "Missing AZURE_OPENAI_API_KEY in .env"  # Explains exactly which .env value is missing.
    )  # Ends the exception construction.

if not AZURE_ENDPOINT:  # Stops early if the Azure resource URL is not configured.
    raise Exception(  # Raises a clear setup error for the missing endpoint.
        "Missing AZURE_OPENAI_ENDPOINT in .env"  # Explains exactly which .env value is missing.
    )  # Ends the exception construction.

if not AZURE_API_VERSION:  # Stops early if the API version is not configured.
    raise Exception(  # Raises a clear setup error for the missing API version.
        "Missing AZURE_OPENAI_API_VERSION in .env"  # Explains exactly which .env value is missing.
    )  # Ends the exception construction.

if not AZURE_DEPLOYMENT:  # Stops early if the target model deployment is not configured.
    raise Exception(  # Raises a clear setup error for the missing deployment.
        "Missing AZURE_OPENAI_DEPLOYMENT in .env"  # Explains exactly which .env value is missing.
    )  # Ends the exception construction.

# ======================================================
# AZURE CLIENT
# ======================================================

client = AzureOpenAI(  # Creates one reusable Azure OpenAI client for all evaluation calls.
    api_key=AZURE_API_KEY,  # Supplies the credential required to call Azure OpenAI.
    api_version=AZURE_API_VERSION,  # Pins the API contract expected by this project.
    azure_endpoint=AZURE_ENDPOINT,  # Points the client at the correct Azure OpenAI resource.
)  # Ends the client setup.

# ======================================================
# INTERNAL LLM CALL
# ======================================================


def _call_llm(prompt: str) -> str:  # Sends an evaluator prompt to Azure OpenAI and returns raw text.

    response = client.chat.completions.create(  # Calls the chat completion endpoint to score the answer.
        model=AZURE_DEPLOYMENT,  # Selects the configured Azure deployment rather than a hard-coded model name.
        messages=[  # Provides the conversation messages that instruct the evaluator model.
            {  # Starts the system message that controls evaluator behavior.
                "role": "system",  # Marks this message as high-priority behavior guidance.
                "content": (  # Starts a multi-part string so the instruction stays readable.
                    "You are a strict AI evaluator. "  # Tells the model to behave as an evaluator.
                    "Always return valid JSON only."  # Forces machine-readable output for json.loads.
                ),  # Ends the system instruction string.
            },  # Ends the system message dictionary.
            {  # Starts the user message containing the actual scoring prompt.
                "role": "user",  # Marks this message as the prompt content to evaluate.
                "content": prompt,  # Sends the formatted scoring prompt built by evaluate_all_metrics.
            },  # Ends the user message dictionary.
        ],  # Ends the messages list.
        temperature=0,  # Makes evaluation deterministic by reducing randomness.
    )  # Ends the Azure chat completion request.

    content = response.choices[0].message.content  # Extracts the model's text from the first completion choice.

    if content is None:  # Handles the rare case where Azure returns no message text.
        return "{}"  # Returns empty JSON so the caller can parse a safe fallback object.

    return str(content)  # Ensures the caller always receives a string for JSON parsing.

# ======================================================
# MAIN METRICS FUNCTION
# ======================================================


def evaluate_all_metrics(
    question,  # Receives the original question so relevancy can be judged.
    answer,  # Receives the chatbot's response so quality can be judged.
    contexts,  # Receives retrieved context so grounding and retrieval precision can be judged.
    expected,  # Receives the reference answer so correctness can be judged.
):  # Defines the public metric-evaluation function used by the pipeline.

    context_text = "\n".join(contexts)  # Combines context chunks into one prompt section for the evaluator.

    # Builds one detailed evaluator prompt containing format rules, scoring rules, and data.
    prompt = f"""
Evaluate the chatbot response.

Return ONLY valid JSON.

FORMAT:

{{
    "Answer Relevancy": 0.0,
    "Correctness": 0.0,
    "Hallucination": 0.0,
    "Faithfulness": 0.0,
    "Context Precision": 0.0
}}

SCORING RULES:
- All scores must be between 0 and 1
- Higher is better except Hallucination
- Hallucination = unsupported information
- Faithfulness = grounded in context
- Correctness = matches expected answer
- Relevancy = answers the question
- Context Precision = retrieval quality

DATA:

Question:
{question}

Expected Answer:
{expected}

Actual Answer:
{answer}

Retrieved Context:
{context_text}
"""  # Ends the evaluator prompt string.

    try:  # Protects the pipeline from API errors, malformed JSON, or unexpected evaluator output.

        raw_response = _call_llm(prompt)  # Gets the raw JSON-like response text from the evaluator model.

        cleaned = raw_response.strip()  # Removes surrounding whitespace that could break or clutter JSON parsing.

        metrics = json.loads(cleaned)  # Converts the evaluator's JSON string into a Python dictionary.

        return {  # Returns normalized metric values in the exact keys expected by the rest of the pipeline.
            "Answer Relevancy":  # Keeps the metric name consistent with the Excel report and scoring engine.
                float(metrics.get("Answer Relevancy", 0)),  # Converts relevancy to a float, defaulting missing values to 0.

            "Correctness":  # Keeps the correctness metric name consistent across modules.
                float(metrics.get("Correctness", 0)),  # Converts correctness to a float, defaulting missing values to 0.

            "Hallucination":  # Keeps the hallucination metric name consistent across modules.
                float(metrics.get("Hallucination", 0)),  # Converts hallucination to a float, defaulting missing values to 0.

            "Faithfulness":  # Keeps the faithfulness metric name consistent across modules.
                float(metrics.get("Faithfulness", 0)),  # Converts faithfulness to a float, defaulting missing values to 0.

            "Context Precision":  # Keeps the context precision metric name consistent across modules.
                float(metrics.get("Context Precision", 0)),  # Converts context precision to a float, defaulting missing values to 0.
        }  # Ends the normalized metrics dictionary.

    except Exception as e:  # Catches any evaluator failure so one bad evaluation does not crash the whole batch.

        print(f"\nEvaluation Error: {e}")  # Logs the problem so the user can diagnose evaluator failures.

        return {  # Returns conservative fallback scores when real evaluation is unavailable.
            "Answer Relevancy": 0,  # Gives no relevancy credit because the evaluator failed.
            "Correctness": 0,  # Gives no correctness credit because the evaluator failed.
            "Hallucination": 1,  # Marks hallucination as worst-case because unsupported output could not be checked.
            "Faithfulness": 0,  # Gives no faithfulness credit because grounding could not be verified.
            "Context Precision": 0,  # Gives no retrieval credit because context quality could not be verified.
        }  # Ends the fallback metrics dictionary.
