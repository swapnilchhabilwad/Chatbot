# Imports OS helpers so the script can read environment variables.
import os

# Imports Any for the custom DeepEval model's load_model return type.
from typing import Any

# Imports dotenv loader so Azure settings can come from the .env file.
from dotenv import load_dotenv

# Imports the Azure chat model wrapper used by the custom DeepEval model.
from langchain_openai import AzureChatOpenAI

# Imports DeepEval's base class for custom LLM integrations.
from deepeval.models.base_model import DeepEvalBaseLLM

# Imports DeepEval metric classes.
from deepeval.metrics import (
    # Measures whether the answer includes unsupported claims.
    HallucinationMetric,
)

# Imports DeepEval's test case object.
from deepeval.test_case import LLMTestCase

# Imports SecretStr so the Azure API key is passed in the expected secret type.
from pydantic.v1 import SecretStr

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
    # Environment variable name for the Azure chat deployment.
    "AZURE_OPENAI_DEPLOYMENT"
)

# =====================================================
# SAFETY CHECKS
# =====================================================

# Stops the script if the Azure API key is missing.
if not AZURE_API_KEY:
    # Raises a clear error naming the missing variable.
    raise ValueError(
        # Error text shown in the terminal.
        "Missing AZURE_OPENAI_API_KEY"
    )

# Stops the script if the Azure endpoint is missing.
if not AZURE_ENDPOINT:
    # Raises a clear error naming the missing variable.
    raise ValueError(
        # Error text shown in the terminal.
        "Missing AZURE_OPENAI_ENDPOINT"
    )

# Stops the script if the Azure API version is missing.
if not AZURE_API_VERSION:
    # Raises a clear error naming the missing variable.
    raise ValueError(
        # Error text shown in the terminal.
        "Missing AZURE_OPENAI_API_VERSION"
    )

# Stops the script if the Azure deployment name is missing.
if not AZURE_DEPLOYMENT:
    # Raises a clear error naming the missing variable.
    raise ValueError(
        # Error text shown in the terminal.
        "Missing AZURE_OPENAI_DEPLOYMENT"
    )


# This duplicate check is left unchanged so the script behavior stays exactly as it was.
if not AZURE_DEPLOYMENT:
    # Raises the same clear error if the deployment value is missing.
    raise ValueError(
        # Error text shown in the terminal.
        "Missing AZURE_OPENAI_DEPLOYMENT"
    )

# =====================================================
# TYPE FIXES
# =====================================================

# Converts the API key to a plain string after the missing-value checks.
AZURE_API_KEY = str(AZURE_API_KEY)

# Converts the endpoint to a plain string after the missing-value checks.
AZURE_ENDPOINT = str(AZURE_ENDPOINT)

# Converts the API version to a plain string after the missing-value checks.
AZURE_API_VERSION = str(AZURE_API_VERSION)

# Converts the deployment name to a plain string after the missing-value checks.
AZURE_DEPLOYMENT = str(AZURE_DEPLOYMENT)

# =====================================================
# CUSTOM AZURE MODEL
# =====================================================


# Custom model wrapper that lets DeepEval use Azure OpenAI.
class AzureOpenAIModel(DeepEvalBaseLLM):

    # Creates the Azure OpenAI chat client for DeepEval.
    def __init__(self):

        # Builds the Azure chat model used by hallucination scoring.
        self.model = AzureChatOpenAI(
            # Uses the configured Azure OpenAI endpoint.
            azure_endpoint=AZURE_ENDPOINT,

            # Passes the API key as a secret value.
            api_key=SecretStr(str(AZURE_API_KEY)),

            # Uses the configured Azure OpenAI API version.
            api_version=str(AZURE_API_VERSION),

            # Uses the configured Azure chat deployment.
            azure_deployment=AZURE_DEPLOYMENT,

            # Keeps evaluator responses deterministic.
            temperature=0,
        )

    # Returns the model client to DeepEval.
    def load_model(self) -> Any:
        # Provides the Azure chat model created during initialization.
        return self.model

    # Generates one synchronous response for a DeepEval judge prompt.
    def generate(self, prompt: str) -> str:

        # Sends the judge prompt to Azure OpenAI.
        response = self.model.invoke(prompt)

        # Returns only the text content expected by DeepEval.
        return str(response.content)

    # Generates one asynchronous response for a DeepEval judge prompt.
    async def a_generate(
        # Receives the model wrapper instance.
        self,
        # Receives the DeepEval judge prompt.
        prompt: str
    ) -> str:

        # Sends the judge prompt to Azure OpenAI asynchronously.
        response = await self.model.ainvoke(prompt)

        # Returns only the text content expected by DeepEval.
        return str(response.content)

    # Gives DeepEval a readable model name for logs and reports.
    def get_model_name(self) -> str:
        # Identifies this custom model as Azure OpenAI-backed.
        return "Azure OpenAI"

# =====================================================
# CREATE MODEL
# =====================================================


# Creates the custom Azure-backed model used by the metric below.
azure_model = AzureOpenAIModel()

# =====================================================
# TEST CASE
# =====================================================

# Creates a sample DeepEval test case for hallucination scoring.
test_case = LLMTestCase(
    # Sample user question.
    input="What is AI?",

    # Sample chatbot answer.
    actual_output=(
        # First part of the sample actual answer.
        "AI is the simulation of "
        # Second part of the sample actual answer.
        "human intelligence."
    ),

    # Sample expected/reference answer.
    expected_output=(
        # First part of the expected answer.
        "AI refers to systems capable "
        # Second part of the expected answer.
        "of performing intelligent tasks."
    ),

    # Context used by DeepEval metrics that read context.
    context=[
        # Sample context string.
        (
            # First part of the context string.
            "Artificial Intelligence enables "
            # Second part of the context string.
            "machines to simulate human intelligence."
        )
    ],

    # Retrieval context used by DeepEval retrieval-aware metrics.
    retrieval_context=[
        # Sample retrieval context string.
        (
            # First part of the retrieval context string.
            "Artificial Intelligence enables "
            # Second part of the retrieval context string.
            "machines to simulate human intelligence."
        )
    ]
)

# =====================================================
# HALLUCINATION METRIC
# =====================================================

# Creates the hallucination metric using the Azure-backed model.
metric = HallucinationMetric(
    # Tells DeepEval to use the custom Azure model.
    model=azure_model
)

# Runs the hallucination metric against the sample test case.
score = metric.measure(test_case)

# =====================================================
# PRINT RESULT
# =====================================================

# Prints a readable section header before the score.
print("\n===== DEEPEVAL RESULT =====\n")

# Prints the hallucination score returned by DeepEval.
print("Hallucination Score:", score)
