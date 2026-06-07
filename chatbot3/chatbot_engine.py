# Imports the Ollama chat wrapper from LangChain so the project can call a local LLM.
from langchain_ollama import ChatOllama

# =====================================================
# LOCAL CHATBOT
# =====================================================


# This function receives one question from the Excel pipeline and returns the chatbot answer.
# The mode argument is kept for future workflows, even though the current local model call does not use it.
def ask_question(question, mode="general"):

    # Creates the local Ollama chat model that will answer the question.
    llm = ChatOllama(
        # Uses the locally installed llama3.2 model.
        model="llama3.2",
        # Keeps responses slightly creative but still stable.
        temperature=0.3,
    )

    # Sends the user question to the local model and waits for its response.
    response = llm.invoke(question)

    # Returns a dictionary because the pipeline expects both answer text and retrieval contexts.
    return {
        # Stores the model's actual answer text.
        "answer": response.content,

        # No document retrieval is currently used, so this placeholder keeps evaluation code consistent.
        "contexts": [
            # This marker tells the evaluation layer to use safe fallback context handling.
            "No retrieval context used"
        ]
    }
