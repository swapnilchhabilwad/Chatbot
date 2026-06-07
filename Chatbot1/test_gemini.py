# Imports the Gemini chat wrapper so LangChain can call Google's generative AI chat model.
from langchain_google_genai import ChatGoogleGenerativeAI
# Imports load_dotenv so API keys and other secrets can be loaded from the local .env file.
from dotenv import load_dotenv

# Loads environment variables from .env, which is where GOOGLE_API_KEY is usually stored for this client.
load_dotenv()


# Creates a Gemini chat model object that can receive prompts through LangChain's standard invoke method.
llm = ChatGoogleGenerativeAI(
    # Selects the Gemini model variant used for this quick connectivity test.
    model="gemini-2.0-flash"
)

# Sends a tiny prompt to Gemini to confirm the model and API key are working.
response = llm.invoke("Say hello")

# Prints only the text content of the model response so the terminal output is easy to read.
print(response.content)
