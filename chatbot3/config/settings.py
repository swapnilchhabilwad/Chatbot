# Imports Python's operating system helpers so environment variables can be read.
import os
# Imports Pydantic's BaseModel so settings are stored in a structured object.
from pydantic import BaseModel
# Imports dotenv loader so values from the local .env file become environment variables.
from dotenv import load_dotenv

# Loads variables from .env before the Settings class reads them.
load_dotenv()


# This class centralizes all Azure OpenAI settings used by RAGAS and DeepEval.
class Settings(BaseModel):
    # Reads the Azure OpenAI API key; an empty string means the value is missing.
    AZURE_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    # Reads the Azure OpenAI endpoint URL.
    AZURE_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    # Reads the Azure OpenAI API version.
    AZURE_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "")
    # Reads the Azure chat model deployment name.
    AZURE_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    # Reads the Azure embeddings deployment name used by RAGAS retrieval metrics.
    AZURE_EMBEDDING_DEPLOYMENT: str = os.getenv(
        # This environment variable should contain the embedding model deployment name.
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", ""
    )


# Creates one shared settings object that other modules import.
settings = Settings()
