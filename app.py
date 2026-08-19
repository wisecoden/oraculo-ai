import os
from dataclasses import dataclass
from dotenv import load_dotenv
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

@dataclass
class Settings:
    openai_api_key: str
    model_name: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    retriever_k: int
    max_history_pairs: int  # max (human, ai) pairs kept in context


try:
    _ = st.secrets  
    _ST_AVAILABLE = True
except FileNotFoundError:
    _ST_AVAILABLE = False


def _get_secret(key: str, default: str = "") -> str:
    """
    Read a secret/config value with this priority:
      1. st.secrets (Streamlit Cloud dashboard)
      2. os.environ / .env file
      3. default
    """
    if _ST_AVAILABLE:
        try:
            return str(st.secrets[key])
        except (KeyError, FileNotFoundError):
            pass
    return os.getenv(key, default)


def load_settings() -> Settings:
    """Load and validate all settings (works on local .env and Streamlit Cloud)."""
    api_key = _get_secret("OPENAI_API_KEY").strip()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. "
            "Set it in .env locally, or in the Streamlit Cloud Secrets dashboard."
        )
    return Settings(
        openai_api_key=api_key,
        model_name=_get_secret("MODEL_NAME", "gpt-5-mini-2025-08-07"),
        embedding_model=_get_secret("EMBEDDING_MODEL", "text-embedding-3-small"),
        chunk_size=int(_get_secret("CHUNK_SIZE", "800")),
        chunk_overlap=int(_get_secret("CHUNK_OVERLAP", "120")),
        retriever_k=int(_get_secret("RETRIEVER_K", "4")),
        max_history_pairs=int(_get_secret("MAX_HISTORY_PAIRS", "5")),
    )


def load_and_split_pdf(path: str, settings: Settings) -> list:
    """
    Load a PDF from `path`, split it into overlapping chunks.
    Returns a list of LangChain Document objects.
    """
    loader = PyPDFLoader(path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(pages)
    return chunks


def build_vector_store(chunks: list, settings: Settings) -> FAISS:
    """
    Generate embeddings for `chunks` and store them in an in-memory FAISS index.
    Returns the FAISS vector store.
    """
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )
    vector_store = FAISS.from_documents(chunks, embeddings)
    return vector_store


_SYSTEM_PROMPT = """Você é um assistente prestativo e preciso. \
Responda APENAS com base no contexto do documento fornecido abaixo. \
Se a resposta não estiver no contexto, diga que não encontrou a informação no documento.

Sempre que houver $ na sua saída, substitua por S.

Contexto do documento:
---------------------
{context}
---------------------"""

def build_rag_chain(vector_store: FAISS, settings: Settings):
    """
    Build the RAG chain: retriever + prompt + LLM.
    Returns a tuple (chain, retriever) so the caller can run retrieval separately.
    """
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.retriever_k},
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
    ])

    llm = ChatOpenAI(
        model=settings.model_name,
        api_key=settings.openai_api_key,
        temperature=0.2,
        streaming=True,
        max_retries=2
    )

    chain = prompt | llm
    return chain, retriever



def trim_history(history: list[dict], max_pairs: int) -> list[dict]:
    """
    Keep only the last `max_pairs` (human + assistant) exchange pairs.
    Prevents token overflow on long conversations.
    Always returns an even-length list (full pairs only).
    """

    pairs: list[tuple[dict, dict]] = []
    buf = None
    for msg in history:
        if msg["role"] == "user":
            buf = msg
        elif msg["role"] == "assistant" and buf is not None:
            pairs.append((buf, msg))
            buf = None
    # Take the last max_pairs pairs and flatten
    trimmed_pairs = pairs[-max_pairs:]
    return [m for pair in trimmed_pairs for m in pair]


def answer(
    chain,
    retriever,
    question: str,
    history: list[dict],
    max_history_pairs: int = 5,
) -> tuple[str, list[dict]]:
    """
    Retrieve relevant chunks for `question`, build chat history messages,
    invoke the chain, and return (response_text, sources).

    `sources` is a list of dicts with keys:
      - 'page'    : int  (1-indexed page number from the PDF)
      - 'snippet' : str  (first 200 chars of the chunk)

    `history` is a list of dicts with keys 'role' ('user'|'assistant') and 'content'.
    The current user message should NOT be included in history.
    """

    trimmed = trim_history(history, max_history_pairs)

    docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)

    seen_pages: set[int] = set()
    sources: list[dict] = []
    for doc in docs:
        page = int(doc.metadata.get("page", 0)) + 1  # PyPDFLoader is 0-indexed
        if page not in seen_pages:
            seen_pages.add(page)
            sources.append({
                "page": page,
                "snippet": doc.page_content[:200].strip(),
            })
    sources.sort(key=lambda s: s["page"])

    chat_history = []
    for msg in trimmed:
        if msg["role"] == "user":
            chat_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            chat_history.append(AIMessage(content=msg["content"]))

    response = chain.invoke({
        "context": context,
        "chat_history": chat_history,
        "input": question,
    })

    content = getattr(response, "content", response)
    if isinstance(content, list):
        text = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )
    elif isinstance(content, dict):
        text = str(content.get("text", ""))
    else:
        text = str(content)

    return text, sources