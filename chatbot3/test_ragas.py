# Imports OS helpers so the script can read environment variables.
import os

# Imports dotenv loader so Azure settings can come from the .env file.
from dotenv import load_dotenv

# Imports Dataset because RAGAS evaluates Hugging Face Dataset objects.
from datasets import Dataset

# Imports the RAGAS evaluate function.
from ragas import evaluate

# Imports SecretStr so the Azure API key is passed in the format expected by LangChain.
from pydantic.v1 import SecretStr

# Imports Azure OpenAI chat and embedding model wrappers.
from langchain_openai import (
    # Chat model used as the RAGAS judge LLM.
    AzureChatOpenAI,
    # Embedding model used by RAGAS embedding-based metrics.
    AzureOpenAIEmbeddings,
)
# Imports the RAGAS metrics used in this standalone test script.
from ragas.metrics import (
    # Measures whether the answer is grounded in context.
    faithfulness,
    # Measures whether the answer addresses the question.
    answer_relevancy,
    # Measures whether the provided context is precise/useful.
    context_precision,
)

# Imports the same Azure wrappers again; this is duplicate but left unchanged to avoid code behavior changes.
from langchain_openai import (
    # Duplicate chat model import kept as-is.
    AzureChatOpenAI,
    # Duplicate embeddings import kept as-is.
    AzureOpenAIEmbeddings,
)

# =====================================================
# LOAD ENV
# =====================================================

# Loads variables from .env into the process environment.
load_dotenv()

# =====================================================
# ENV VARIABLES
# =====================================================

# Reads the Azure OpenAI API key from the environment.
AZURE_API_KEY = os.getenv(
    # Environment variable name for the Azure OpenAI API key.
    "AZURE_OPENAI_API_KEY"
)

# Reads the Azure OpenAI endpoint URL from the environment.
AZURE_ENDPOINT = os.getenv(
    # Environment variable name for the Azure OpenAI endpoint.
    "AZURE_OPENAI_ENDPOINT"
)

# Reads the Azure OpenAI API version from the environment.
AZURE_API_VERSION = os.getenv(
    # Environment variable name for the Azure OpenAI API version.
    "AZURE_OPENAI_API_VERSION"
)

# Reads the Azure chat deployment name from the environment.
AZURE_DEPLOYMENT = os.getenv(
    # Environment variable name for the Azure chat model deployment.
    "AZURE_OPENAI_DEPLOYMENT"
)

# Reads the Azure embeddings deployment name from the environment.
AZURE_EMBEDDING_DEPLOYMENT = os.getenv(
    # Environment variable name for the Azure embedding model deployment.
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"
)

# =====================================================
# SAFETY CHECKS
# =====================================================

# Stops the script if the Azure API key is missing.
if not AZURE_API_KEY:
    # Raises a clear error message naming the missing variable.
    raise ValueError(
        # Error text shown in the terminal.
        "Missing AZURE_OPENAI_API_KEY"
    )

# Stops the script if the Azure endpoint is missing.
if not AZURE_ENDPOINT:
    # Raises a clear error message naming the missing variable.
    raise ValueError(
        # Error text shown in the terminal.
        "Missing AZURE_OPENAI_ENDPOINT"
    )

# Stops the script if the Azure API version is missing.
if not AZURE_API_VERSION:
    # Raises a clear error message naming the missing variable.
    raise ValueError(
        # Error text shown in the terminal.
        "Missing AZURE_OPENAI_API_VERSION"
    )

# Stops the script if the Azure chat deployment name is missing.
if not AZURE_DEPLOYMENT:
    # Raises a clear error message naming the missing variable.
    raise ValueError(
        # Error text shown in the terminal.
        "Missing AZURE_OPENAI_DEPLOYMENT"
    )

# Stops the script if the Azure embedding deployment name is missing.
if not AZURE_EMBEDDING_DEPLOYMENT:
    # Raises a clear error message naming the missing variable.
    raise ValueError(
        # Error text shown in the terminal.
        "Missing AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"
    )

# =====================================================
# AZURE LLM
# =====================================================

# Creates the Azure chat model that RAGAS will use for judge prompts.
azure_llm = AzureChatOpenAI(
    # Uses the configured Azure OpenAI endpoint.
    azure_endpoint=AZURE_ENDPOINT,

    # Passes the API key as a secret value.
    api_key=SecretStr(AZURE_API_KEY),

    # Uses the configured Azure OpenAI API version.
    api_version=AZURE_API_VERSION,

    # Uses the configured Azure chat deployment.
    azure_deployment=AZURE_DEPLOYMENT,

    # Keeps judge output deterministic.
    temperature=0,
)

# =====================================================
# AZURE EMBEDDINGS
# =====================================================

# Creates the Azure embeddings model that RAGAS uses for retrieval metrics.
azure_embeddings = AzureOpenAIEmbeddings(
    # Uses the configured Azure OpenAI endpoint.
    azure_endpoint=AZURE_ENDPOINT,

    # Passes the API key as a secret value.
    api_key=SecretStr(AZURE_API_KEY),

    # Uses the configured Azure OpenAI API version.
    api_version=AZURE_API_VERSION,

    # Uses the configured Azure embedding deployment.
    azure_deployment=AZURE_EMBEDDING_DEPLOYMENT,
)

# =====================================================
# TEST DATA
# =====================================================

# Defines one sample record so RAGAS can be tested without the Excel pipeline.
data = {
    # RAGAS question column.
    "question": [
        # Sample user question.
        "What is AI?"
    ],

    # RAGAS answer column.
    "answer": [
        # Sample chatbot answer.
        "AI is the simulation of human intelligence by machines."
    ],

    # RAGAS contexts column; each row must contain a list of context strings.
    "contexts": [[
        # Sample context used to judge the answer.
        (
            # First part of the sample context string.
            "Artificial Intelligence is the "
            # Second part of the sample context string.
            "simulation of human intelligence "
            # Third part of the sample context string.
            "processes by machines."
        )
    ]],

    # RAGAS ground truth column.
    "ground_truth": [
        # Sample expected answer.
        (
            # First part of the expected answer string.
            "AI refers to machine systems capable "
            # Second part of the expected answer string.
            "of performing tasks requiring "
            # Third part of the expected answer string.
            "human intelligence."
        )
    ],
}

# =====================================================
# CREATE DATASET
# =====================================================

# Converts the sample dictionary into a Hugging Face Dataset for RAGAS.
dataset = Dataset.from_dict(data)

# =====================================================
# RUN RAGAS EVALUATION
# =====================================================

# Runs RAGAS against the sample dataset using Azure OpenAI.
result = evaluate(
    # Supplies the dataset to evaluate.
    dataset=dataset,

    # Selects the metrics to calculate.
    metrics=[
        # Calculates faithfulness.
        faithfulness,
        # Calculates answer relevancy.
        answer_relevancy,
        # Calculates context precision.
        context_precision,
    ],

    # Supplies the Azure chat judge model.
    llm=azure_llm,

    # Supplies the Azure embeddings model.
    embeddings=azure_embeddings,
)

# =====================================================
# PRINT RESULTS
# =====================================================

# Prints a readable section header before the result object.
print("\n===== RAGAS RESULTS =====\n")

# Prints the full RAGAS result returned by the library.
print(result)
