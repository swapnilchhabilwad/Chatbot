# Imports Any because DeepEval's base model interface can return different model client types.
from typing import Any
# Imports the DeepEval base class required for custom evaluator models.
from deepeval.models.base_model import DeepEvalBaseLLM
# Imports the Azure chat model factory shared with the rest of the project.
from config.azure_clients import get_azure_llm


# Custom DeepEval model wrapper that lets DeepEval use Azure OpenAI instead of default OpenAI.
class AzureOpenAIModel(DeepEvalBaseLLM):

    # Initializes the wrapper without creating a network client immediately.
    def __init__(self):
        # Keeps the Azure model unset until the first evaluation call needs it.
        self.model = None

    # Loads and caches the Azure model client for DeepEval.
    def load_model(self) -> Any:
        # Creates the Azure client only once.
        if self.model is None:
            # Builds the Azure chat model using settings from .env.
            self.model = get_azure_llm()
        # Returns the cached model client to DeepEval.
        return self.model

    # Synchronous generation method required by DeepEval metrics.
    def generate(self, prompt: str) -> str:
        # Sends the DeepEval judge prompt to Azure OpenAI.
        response = self.load_model().invoke(prompt)
        # Returns only the response text because DeepEval expects a string.
        return str(response.content)

    # Asynchronous generation method required by DeepEval metrics.
    async def a_generate(self, prompt: str) -> str:
        # Sends the DeepEval judge prompt to Azure OpenAI asynchronously.
        response = await self.load_model().ainvoke(prompt)
        # Returns only the response text because DeepEval expects a string.
        return str(response.content)

    # Gives DeepEval a readable name for logs and reports.
    def get_model_name(self) -> str:
        # Identifies this evaluator as Azure OpenAI-backed.
        return "Azure OpenAI"


# Creates one reusable custom model object for DeepEval metrics.
azure_model = AzureOpenAIModel()
