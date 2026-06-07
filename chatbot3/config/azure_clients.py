# Imports SecretStr from Pydantic v1 because LangChain OpenAI models expect this secret type.
from pydantic.v1 import SecretStr
# Imports Azure model wrappers used for chat evaluation and embedding-based metrics.
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
# Imports the centralized environment configuration.
from config.settings import settings


# Reads one required setting and raises a clear error if it is missing.
def _required_setting(name: str) -> str:
    # Gets the setting by name from the shared settings object.
    value = getattr(settings, name, "")
    # Converts the value to a trimmed string while safely handling None.
    value = str(value).strip() if value is not None else ""
    # Stops early if the required environment variable was not provided.
    if not value:
        # Raises a simple message that names the missing setting.
        raise ValueError(f"Missing {name}")
    # Returns the validated non-empty value to the caller.
    return value


# Creates the Azure chat LLM used by RAGAS and DeepEval evaluators.
def get_azure_llm():
    # Reads the API key once so it can be wrapped as a secret.
    api_key = _required_setting("AZURE_API_KEY")

    # Builds and returns the LangChain Azure chat model client.
    return AzureChatOpenAI(
        # Provides the Azure OpenAI resource endpoint.
        azure_endpoint=_required_setting("AZURE_ENDPOINT"),
        # Passes the API key as a secret to avoid plain-text handling by the model wrapper.
        api_key=SecretStr(api_key),
        # Selects the Azure OpenAI API version configured in .env.
        api_version=_required_setting("AZURE_API_VERSION"),
        # Selects the deployed chat model name.
        azure_deployment=_required_setting("AZURE_DEPLOYMENT"),
        # Uses deterministic evaluator responses.
        temperature=0,
    )


# Creates the Azure embeddings client used by RAGAS context metrics.
def get_azure_embeddings():
    # Reads the same Azure API key used by the embeddings deployment.
    api_key = _required_setting("AZURE_API_KEY")

    # Builds and returns the LangChain Azure embeddings client.
    return AzureOpenAIEmbeddings(
        # Provides the Azure OpenAI resource endpoint.
        azure_endpoint=_required_setting("AZURE_ENDPOINT"),
        # Passes the API key as a secret value.
        api_key=SecretStr(api_key),
        # Selects the configured Azure OpenAI API version.
        api_version=_required_setting("AZURE_API_VERSION"),
        # Selects the deployed embedding model name.
        azure_deployment=_required_setting("AZURE_EMBEDDING_DEPLOYMENT"),
    )
