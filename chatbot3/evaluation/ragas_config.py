# Imports Azure client factories used by RAGAS.
from config.azure_clients import get_azure_llm, get_azure_embeddings

# =====================================================
# AZURE LLM (for RAGAS evaluation)
# =====================================================
# Creates the Azure chat model for RAGAS evaluator prompts.
azure_llm = get_azure_llm()

# =====================================================
# AZURE EMBEDDINGS (for retrieval metrics)
# =====================================================
# Creates the Azure embeddings model for RAGAS retrieval/context metrics.
azure_embeddings = get_azure_embeddings()
