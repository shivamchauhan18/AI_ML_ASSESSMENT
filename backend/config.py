import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

EMBEDDING_MODEL = "embeddinggemma-2:440m"
LLM_MODEL = "gpt-6-luna"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_embeddings():
    from langchain_ollama import OllamaEmbeddings
    return OllamaEmbeddings(model=EMBEDDING_MODEL)


def get_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=LLM_MODEL,api_key=OPENAI_API_KEY)
