# Imports the operating-system helper module so the app can check whether the FAISS index files already exist.
import os

# Imports Streamlit because this project is a web app built with Streamlit widgets, pages, sidebars, and messages.
import streamlit as st
# Imports PdfReader so uploaded PDF files can be opened and their text can be extracted page by page.
from PyPDF2 import PdfReader

# Imports the Ollama chat wrapper so LangChain can talk to a locally running Llama model.
from langchain_ollama import ChatOllama
# Imports the Ollama embeddings wrapper so text chunks can be converted into searchable numeric vectors.
from langchain_ollama import OllamaEmbeddings

# Imports a recursive splitter because long PDF text must be broken into smaller pieces before embedding.
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Imports FAISS because it stores embeddings locally and performs fast similarity search over PDF chunks.
from langchain_community.vectorstores import FAISS

# Imports PromptTemplate so the app can consistently format context and questions before sending them to the LLM.
from langchain_core.prompts import PromptTemplate
# Imports RunnablePassthrough so the LangChain pipeline can keep the original inputs while adding formatted context.
from langchain_core.runnables import RunnablePassthrough
# Imports StrOutputParser so the final LLM message is converted into a plain string for Streamlit output.
from langchain_core.output_parsers import StrOutputParser


# Stores the embedding model name in one place so it is easy to change without hunting through the code.
EMBED_MODEL = "nomic-embed-text"
# Stores the chat model name in one place so every direct and PDF answer uses the same local LLM.
LLM_MODEL = "llama3.2"
# Stores the folder name where FAISS saves and reloads the PDF vector index.
FAISS_PATH = "faiss_index"


# Defines a helper function so every part of the app creates the chat model in the same way.
def get_llm():
    # Returns a ChatOllama object, which is the LangChain interface to the local Ollama chat model.
    return ChatOllama(
        # Selects which local Ollama model will generate the chatbot answers.
        model=LLM_MODEL,
        # Uses a low temperature so answers are more focused and less random.
        temperature=0.3,
    )


# Defines a helper function so embedding setup is centralized and reusable.
def get_embeddings():
    # Returns an OllamaEmbeddings object, which converts text into vectors for semantic search.
    return OllamaEmbeddings(
        # Selects which local Ollama embedding model will turn PDF chunks and questions into vectors.
        model=EMBED_MODEL
    )


# Defines a helper function that receives uploaded PDFs and extracts all readable text from them.
def get_pdf_text(pdf_docs):
    # Starts with an empty string because the app will append text from every page of every uploaded PDF.
    text = ""

    # Loops through each uploaded PDF because users can upload multiple files at once.
    for pdf in pdf_docs:
        # Creates a PDF reader for the current uploaded file so its pages can be inspected.
        pdf_reader = PdfReader(pdf)

        # Loops through each page because PDF text extraction happens one page at a time.
        for page in pdf_reader.pages:
            # Extracts text from the current page; PyPDF2 may return None if no readable text exists.
            page_text = page.extract_text()

            # Checks that text was actually extracted before adding it, avoiding errors from None values.
            if page_text:
                # Appends the current page text to the full text that will later be split and embedded.
                text += page_text

    # Returns the combined text from all uploaded PDF pages to the caller.
    return text


# Defines a helper function that splits long PDF text into smaller chunks suitable for embeddings and retrieval.
def get_text_chunks(text):
    # Creates a splitter that tries to keep meaningful text together while respecting the target chunk size.
    text_splitter = RecursiveCharacterTextSplitter(
        # Sets each chunk to about 1000 characters so chunks are large enough for context but not too large.
        chunk_size=1000,
        # Keeps 200 characters of overlap so ideas near chunk boundaries are not lost during retrieval.
        chunk_overlap=200,
    )

    # Runs the splitter on the extracted PDF text and receives a list of text chunks.
    chunks = text_splitter.split_text(text)

    # Returns the chunk list so it can be embedded and stored in FAISS.
    return chunks


# Defines a helper function that creates a searchable FAISS vector store from PDF text chunks.
def get_vector_store(text_chunks):
    # Gets the embedding model because FAISS needs vectors, not raw text, to perform similarity search.
    embeddings = get_embeddings()

    # Creates a FAISS index from the text chunks by embedding each chunk and storing the result.
    vector_store = FAISS.from_texts(
        # Provides the list of PDF chunks that should become searchable documents.
        text_chunks,
        # Provides the embedding model used to convert each chunk into a numeric vector.
        embedding=embeddings,
    )

    # Saves the FAISS index locally so later questions can reuse it without reprocessing the PDFs.
    vector_store.save_local(FAISS_PATH)


# Defines a helper function that builds the retrieval-augmented question-answering chain.
def get_conversational_chain():

    # Stores the full prompt instructions that tell the model how to answer using retrieved PDF context.
    prompt_template = """
Answer the question as detailed as possible using only the provided context.

If the answer is not available in the context, respond with:

"Answer is not available in the context."

Do not make up information.

Context:
{context}

Question:
{question}

Answer:
"""

    # Creates the chat model that will receive the prompt and produce the final answer.
    model = get_llm()

    # Builds a PromptTemplate so LangChain can inject the retrieved context and the user's question safely.
    prompt = PromptTemplate(
        # Supplies the template string that defines the model's instructions and answer format.
        template=prompt_template,
        # Declares the variable names that must be provided when the prompt is formatted.
        input_variables=["context", "question"],
    )

    # Builds a LangChain pipeline that prepares context, formats the prompt, calls the model, and parses output.
    chain = (
        # Keeps the original input dictionary while adding a new "context" field made from retrieved documents.
        RunnablePassthrough.assign(
            # Converts the retrieved document objects into one plain context string for the prompt.
            context=lambda x: "\n\n".join(
                # Takes the text content from each retrieved document because the model only needs readable text.
                doc.page_content
                # Iterates through the retrieved documents passed under "input_documents".
                for doc in x["input_documents"]
            )
        )
        # Sends the enriched input dictionary into the prompt template.
        | prompt
        # Sends the formatted prompt into the local chat model.
        | model
        # Converts the model response into a plain string for display.
        | StrOutputParser()
    )

    # Returns the reusable chain to the question-answering function.
    return chain


# Defines the PDF question flow, which answers using only uploaded and indexed PDF content.
def ask_pdf_question(user_question):

    # Checks whether the FAISS index exists because PDF questions require previously processed documents.
    if not os.path.exists(f"{FAISS_PATH}/index.faiss"):
        # Shows a clear Streamlit error if the user asks a PDF question before processing PDFs.
        st.error(
            # Explains the exact action the user must take before PDF chat can work.
            "Please upload PDF files and click 'Submit & Process' first."
        )
        # Stops this function early because there is no index to search yet.
        return

    # Gets the same embedding model used when saving the FAISS index so search vectors match stored vectors.
    embeddings = get_embeddings()

    # Starts an error-handled block because loading indexes, searching, and model calls can fail at runtime.
    try:
        # Loads the saved FAISS index from disk so the app can search the processed PDF chunks.
        new_db = FAISS.load_local(
            # Points FAISS to the local folder where the index was saved.
            FAISS_PATH,
            # Provides embeddings so FAISS can embed the user's question before searching.
            embeddings,
            # Allows FAISS/LangChain to deserialize its saved local index files.
            allow_dangerous_deserialization=True,
        )

        # Searches the vector store for chunks most semantically similar to the user's question.
        docs = new_db.similarity_search(
            # Uses the user's question as the search query.
            user_question,
            # Retrieves the top four chunks so the model has enough context without being overloaded.
            k=4
        )

        # Builds the question-answering chain that combines retrieved context with the LLM.
        chain = get_conversational_chain()

        # Runs the chain with retrieved documents and the user's question to generate an answer.
        response = chain.invoke(
            # Passes the exact input keys expected by the RunnablePassthrough and PromptTemplate pipeline.
            {
                # Supplies the retrieved PDF chunks that will become the prompt context.
                "input_documents": docs,
                # Supplies the user's question that the model must answer.
                "question": user_question,
            }
        )

        # Adds a reply heading in the Streamlit page so the answer is visually separated from the input.
        st.write("### Reply")
        # Displays the final answer returned by the LangChain pipeline.
        st.write(response)

    # Catches any runtime exception so the Streamlit app shows an error instead of crashing.
    except Exception as e:
        # Displays the exception message to help the user understand what failed.
        st.error(f"Error: {str(e)}")


# Defines the direct chat flow, which answers from the model without using PDF retrieval.
def ask_direct_question(user_question):

    # Starts an error-handled block because the local model call can fail if Ollama or the model is unavailable.
    try:
        # Creates the local chat model used for normal chatbot questions.
        model = get_llm()
        # Sends the user's question directly to the LLM without adding PDF context.
        response = model.invoke(user_question)

        # Adds a reply heading in the Streamlit page so the answer is easy to find.
        st.write("### Reply")
        # Displays the text content from the model response object.
        st.write(response.content)

    # Catches any runtime exception so the Streamlit app remains usable after an error.
    except Exception as e:
        # Displays the exception message in the web UI for easier debugging.
        st.error(f"Error: {str(e)}")


# Defines the main Streamlit application layout and user interaction flow.
def main():

    # Configures the browser tab title and icon before Streamlit renders the page.
    st.set_page_config(
        # Sets the page title shown in the browser tab.
        page_title="Hybrid Chatbot",
        # Sets the page icon shown in the browser tab.
        page_icon="bot",
    )

    # Displays the main title at the top of the Streamlit app.
    st.header("Hybrid Chatbot using Local Llama 3.2")

    # Creates a sidebar radio button so the user can choose between direct chat and PDF chat.
    mode = st.sidebar.radio(
        # Labels the radio group so the user understands what they are choosing.
        "Choose Mode",
        # Provides the two available chatbot modes.
        [
            # Lets the user talk directly to the model without document retrieval.
            "Direct Chat",
            # Lets the user ask questions about uploaded PDF documents.
            "PDF Chat",
        ],
    )

    # Opens a sidebar layout block for menu controls such as file upload and processing.
    with st.sidebar:

        # Displays a simple title above the sidebar controls.
        st.title("Menu")

        # Shows PDF upload and processing controls only when the user selected PDF Chat mode.
        if mode == "PDF Chat":
            # Creates a PDF uploader so users can provide one or more documents for indexing.
            pdf_docs = st.file_uploader(
                # Explains what the user should upload and which button to click afterward.
                "Upload PDF files and click 'Submit & Process'",
                # Allows multiple PDF files because the retrieval index can combine more than one document.
                accept_multiple_files=True,
                # Restricts uploads to PDF files so PdfReader receives the expected file type.
                type="pdf",
            )

            # Runs the PDF processing workflow only when the user clicks the button.
            if st.button("Submit & Process"):

                # Checks whether the user clicked the button without uploading files.
                if not pdf_docs:
                    # Warns the user that at least one PDF is required before processing can continue.
                    st.warning("Please upload at least one PDF file.")
                    # Stops the current Streamlit run early because there is nothing to process.
                    return

                # Shows a loading spinner while extraction, splitting, embedding, and saving are happening.
                with st.spinner("Processing PDFs..."):

                    # Starts an error-handled block because PDF parsing and vector-store creation can fail.
                    try:
                        # Extracts all readable text from the uploaded PDF files.
                        raw_text = get_pdf_text(pdf_docs)

                        # Checks whether extracted text is empty or only whitespace.
                        if not raw_text.strip():
                            # Shows an error when PDFs contain scans/images or otherwise unreadable text.
                            st.error(
                                # Explains why the app cannot build a useful index from these files.
                                "No readable text found in the uploaded PDFs."
                            )
                            # Stops processing because embedding empty text would be useless.
                            return

                        # Splits the extracted text into chunks that are practical for embeddings and retrieval.
                        text_chunks = get_text_chunks(raw_text)

                        # Builds and saves the FAISS vector index from the text chunks.
                        get_vector_store(text_chunks)

                        # Confirms that the PDF index was created and PDF questions can now be asked.
                        st.success(
                            # Gives the user the next step after successful processing.
                            "PDFs processed successfully! You can now ask questions."
                        )

                    # Catches processing failures so they appear in the Streamlit UI.
                    except Exception as e:
                        # Displays the specific processing error message to help diagnose the problem.
                        st.error(
                            # Converts the exception into readable text for the user.
                            f"Processing failed: {str(e)}"
                        )

    # Chooses the text-input label based on the selected mode so the UI matches the current workflow.
    input_label = (
        # Uses a general label when the model is answering directly.
        "Ask anything"
        # Checks the selected mode to decide which label should be shown.
        if mode == "Direct Chat"
        # Uses a document-specific label when the answer should come from uploaded PDFs.
        else "Ask a question from the PDF files"
    )

    # Creates the main text input where the user types their question.
    user_question = st.text_input(input_label)

    # Runs an answer workflow only after the user has typed a non-empty question.
    if user_question:
        # Shows a loading spinner while the model or retrieval chain generates the reply.
        with st.spinner("Generating response..."):
            # Routes the question to the PDF retrieval flow when PDF Chat mode is selected.
            if mode == "PDF Chat":
                # Answers by searching indexed PDF chunks and using them as context for the model.
                ask_pdf_question(user_question)
            # Routes the question to the direct model flow for normal chat mode.
            else:
                # Answers by sending the question directly to the local LLM.
                ask_direct_question(user_question)


# Checks whether this file is being run directly instead of imported by another Python file.
if __name__ == "__main__":
    # Starts the Streamlit application logic when the file is executed as the main script.
    main()
