# rag_app.py
from pathlib import Path

from langchain_community.document_loaders import TextLoader, PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import OllamaLLM as Ollama
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
import json

DATA_DIR = Path("data")
DB_DIR = "./chroma_db"

# 1) Load documents (add more loaders to taste)
def load_docs():
    docs = []
    # Local text/markdown
    for p in DATA_DIR.glob("**/*"):
        if p.suffix.lower() in {".md", ".txt","json"}:
            docs.extend(TextLoader(str(p), autodetect_encoding=True).load())
        elif p.suffix.lower() == ".pdf":
            docs.extend(PyPDFLoader(str(p)).load())
        elif p.suffix.lower() == ".json":
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert JSON to readable text
            json_text = json.dumps(data, indent=2, ensure_ascii=False)

            docs.append(
                Document(
                    page_content=json_text,
                    metadata={"source": str(p)}
                )
            )
    # Example: Load a web page
    try:
        web_docs = WebBaseLoader("https://python.langchain.com/").load()
        docs.extend(web_docs)
    except Exception:
        pass

    return docs

# 2) Split
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=100, add_start_index=True
)

# 3) Embeddings via Ollama
# Choose your pulled embedding model name
EMBED_MODEL = "nomic-embed-text"  # or "mxbai-embed-large"
embeddings = OllamaEmbeddings(model=EMBED_MODEL)

# 4) Vector store (Chroma)
vectorstore = Chroma(collection_name="local_rag", embedding_function=embeddings, persist_directory=DB_DIR)

# 5) Indexing function

def build_or_load_index():
    # If DB exists, you can skip re-index; here we rebuild for demo
    docs = load_docs()
    splits = text_splitter.split_documents(docs)

    # Recreate collection for a fresh demo
    vectorstore.reset_collection()
    vectorstore.add_documents(splits)

# 6) Retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# 7) LLM via Ollama
CHAT_MODEL = "llama3.1:8b"  # tune to your device
llm = Ollama(model=CHAT_MODEL)

# 8) Prompt
prompt = ChatPromptTemplate.from_template(
    """
    You are a helpful assistant. Answer the user question using the provided context.
    If the answer is not in the context, say you don't know.

    Context:
    {context}

    Question: {question}
    """
)

# 9) Chain: retrieve -> prompt -> llm -> parse
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

if __name__ == "__main__":
    # First time: build the index
    if not Path(DB_DIR).exists():
        Path(DB_DIR).mkdir(parents=True, exist_ok=True)
    build_or_load_index()

    # Simple CLI
    print("RAG ready. Ask a question (Ctrl+C to exit).")
    while True:
        try:
            q = input("\nYou: ")
            if not q.strip():
                continue
            answer = rag_chain.invoke(q)
            print("\nAssistant:\n", answer)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
