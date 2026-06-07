from langchain_ollama import ChatOllama  # Imports the Ollama chat wrapper used to talk to the local LLM.


def ask_question(question, mode="general"):  # Exposes one reusable function for asking the chatbot a question.

    llm = ChatOllama(model="llama3.2:latest", temperature=0.3)  # Creates a local Llama model client with mild creativity.

    response = llm.invoke(question)  # Sends the user's question to the local model and waits for the generated answer.

    return {  # Returns a standard dictionary shape expected by the evaluation pipeline.
        "answer": response.content,  # Stores the model's text answer under a predictable key.
        "contexts": []  # Uses an empty context list because this simple engine does not retrieve documents yet.
    }  # Ends the response dictionary returned to callers.
